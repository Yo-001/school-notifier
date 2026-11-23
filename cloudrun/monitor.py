#!/usr/bin/env python3
"""Monitor do feed RSS do CEIP Plurilingüe Xosé Fernández López (O Porriño,
www.edu.xunta.gal). O portal da Xunta devolve HTTP 500 para IPs fóra de
Europa (verificado: ES/DE/CH/IT/SE -> 200; US/BR/TR/UA -> 500). Este script
debe rodar, pois, nunha máquina con IP europea (por exemplo unha VM Always
Free de Oracle Cloud en Madrid, ou calquera VPS na UE). Se a conexión directa
fallase, usa como relevo o proxy de tradución de Google (devolve o mesmo RSS
byte a byte, só que tamén só para IPs europeas).

Novos artigos son impresos en stdout e, se existe a configuración de Gmail,
enviados por e-mail vía API de Gmail (FROM=TO=leo). A API de Gmail é accesible
por REST con urllib, polo que non require dependencias externas.

Credenciais OAuth do Gmail lidas de variábeis de ambiente (nunca hardcodeadas):
  EMAIL_REFRESH_TOKEN, EMAIL_CLIENT_ID, EMAIL_CLIENT_SECRET
Se non existen, non se notifica (fallback silencioso, só aviso en stdout).

Uso:
  python3 monitor.py --state /camiño/do/directorio
"""
import argparse, base64, html as _html, json, os, sys, time, urllib.parse, urllib.request
import xml.etree.ElementTree as ET
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formatdate, make_msgid

FEEDS = [
    # 1º directo (funciona desde calquera IP europea)
    "https://www.edu.xunta.gal/centros/ceipxosefernandez/rss.xml",
    # 2º relevo de Google (mesmo contido; só desde IP europea)
    "https://www-edu-xunta-gal.translate.goog/centros/ceipxosefernandez/rss.xml",
    # 3º formulario antigo de Google Translate
    "https://translate.google.com/translate?u=https://www.edu.xunta.gal/centros/ceipxosefernandez/rss.xml&sl=gl&tl=en",
]
UA = "Mozilla/5.0 (compatible; edu-monitor/1.0)"

EMAIL_FROM = "leonardo.r.correa43@gmail.com"
# Destinatários (varios separados por vírgula). Envía-se a todos.
EMAIL_TO = "leonardo.r.correa43@gmail.com, arquivos.alvarez@gmail.com"
ESCOLA = "CEIP Plurilingüe Xosé Fernández López"


def fetch(url, timeout=60):
    req = urllib.request.Request(url, headers={
        "User-Agent": UA,
        "Accept": "application/rss+xml, application/xml, */*",
    })
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read(2_000_000)


def parse_items(body):
    root = ET.fromstring(body)
    out = []
    for it in root.iter("item"):
        title = (it.findtext("title") or "").strip()
        link = (it.findtext("link") or "").strip()
        date = it.findtext("pubDate") or ""
        cat = it.findtext("category") or ""
        # Anexos (enclosure: pdf/docx/...). Pode haver vários.
        attach = []
        for e in it.findall("enclosure"):
            url = (e.get("url") or "").strip()
            if url:
                ftype = e.get("type", "")
                attach.append({"url": url, "type": ftype})
        if link:
            out.append({
                "title": title,
                "link": link,
                "date": date.strip(),
                "category": cat.strip(),
                "attachments": attach,
            })
    return out


def get_access_token():
    """Obtém um access_token de curta duração a partir do refresh_token."""
    data = urllib.parse.urlencode({
        "client_id": os.environ["EMAIL_CLIENT_ID"],
        "client_secret": os.environ["EMAIL_CLIENT_SECRET"],
        "refresh_token": os.environ["EMAIL_REFRESH_TOKEN"],
        "grant_type": "refresh_token",
    }).encode("utf-8")
    req = urllib.request.Request("https://oauth2.googleapis.com/token", data=data)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r).get("access_token")


def _fmt_date(iso):
    """Converte 'Sun, 26 Oct 2026 23:00:00 +0000' -> '26/10/2026' approx."""
    try:
        import email.utils as _eu
        t = _eu.parsedate(iso)
        return "%02d/%02d/%04d" % (t[2], t[1], t[0]) if t else iso
    except Exception:
        return iso


def _file_label(url, ftype=""):
    """Devolve un nome curto para o anexo (basename) e a etiqueta do botão."""
    import os as _os, urllib.parse as _up
    name = _os.path.basename(_up.unquote(url)).strip() or "anexo"
    ftype = (ftype or "").lower()
    if "pdf" in ftype:
        return "📄 Descargar PDF", name
    if "doc" in ftype:
        return "📄 Descargar documento", name
    if "image" in ftype or ("png" in name or "jpg" in name or "jpeg" in name or "gif" in name or "webp" in name):
        return "🖼️ Descargar imaxe", name
    return "📎 Descargar anexo", name


def _build_html(item):
    """Corpo HTML estruturado (modelo padrao de todos os e-mails). Inclúe
    botóns de descarga para anexos (PDF/doc/imaxe) cando o post os ten."""
    title = _html.escape(item["title"])
    link = _html.escape(item["link"])
    data = _fmt_date(item.get("date", ""))
    cat = _html.escape(item.get("category", "Información xeral"))
    attach = item.get("attachments") or []

    # Botões de anexos (acima do link da publicación)
    btns = []
    for a in attach:
        label, fname = _file_label(a.get("url", ""), a.get("type", ""))
        aurl = _html.escape(a["url"])
        btns.append(
            '<td><a href="%s" style="display:inline-block;background:#188038;color:#ffffff;'
            'padding:12px 20px;border-radius:8px;text-decoration:none;font-weight:600;font-size:14px;margin-right:8px">%s</a>'
            '<div style="font-size:12px;color:#5f6368;margin-top:4px">%s</div></td>'
            % (aurl, label, _html.escape(fname))
        )
    anexos_html = ""
    if btns:
        anexos_html = ('<table style="margin-top:16px;width:100%%"><tr>%s</tr></table>'
                       % "".join(btns))

    # Link principal sempre presente
    link_html = ('<table style="margin-top:20px;width:100%%"><tr>'
                 '<td><a href="%s" style="display:inline-block;background:#1a73e8;color:#ffffff;'
                 'padding:12px 22px;border-radius:8px;text-decoration:none;font-weight:600;font-size:14px">&#128279; Ver publicación</a></td>'
                 '</tr></table>' % link)

    return """<html><body style="font-family:Segoe UI,Arial,sans-serif;margin:0;padding:0;background:#f4f4f4">
<table width="100%%" cellpadding="0" cellspacing="0" style="background:#f4f4f4;padding:20px"><tr><td align="center">
<table width="640" cellpadding="0" cellspacing="0" style="background:#ffffff;border-radius:12px;overflow:hidden;border:1px solid #e3e3e3">
<tr><td style="background:#1a73e8;padding:20px 24px;color:#ffffff">
  <div style="font-size:13px;font-weight:600;text-transform:uppercase;letter-spacing:.5px;opacity:.85">%s</div>
  <div style="font-size:20px;font-weight:700;margin-top:4px">Nova publicación na web do centro</div>
</td></tr>
<tr><td style="padding:24px">
  <div style="font-size:22px;font-weight:700;color:#202124;line-height:1.3">%s</div>
  <div style="margin-top:8px;color:#5f6368;font-size:13px">&#128197; %s &nbsp;&bull;&nbsp; &#127943; %s</div>
  <table style="margin-top:16px;background:#f8f9fa;border-left:4px solid #1a73e8;padding:14px 16px;border-radius:6px;width:100%%"><tr><td style="font-size:14px;color:#202124;line-height:1.5">
    Publicouse unha nova entrada na web do CEIP Xosé Fernández López. Preme nas ligazóns de abaixo para acceder ás publicacións ou descargar os documentos.
  </td></tr></table>
  %s
  %s
</td></tr>
<tr><td style="background:#f8f9fa;padding:12px 24px;color:#80868b;font-size:12px;border-top:1px solid #e3e3e3">
  Monitor automático • %s
</td></tr>
</table></td></tr></table></body></html>""" % (ESCOLA, title, data, cat, anexos_html, link_html, ESCOLA)


def _build_plain(item):
    txt = ("Nova publicación no CEIP Xosé Fernández López:\n\n"
           "Título: %s\nData: %s\nCategoría: %s\n\nLigazón: %s"
           % (item["title"], _fmt_date(item.get("date", "")),
              item.get("category", "Información xeral"), item["link"]))
    for a in (item.get("attachments") or []):
        if a.get("url"):
            txt += "\nAnexo: %s" % a["url"]
    return txt


def send_email(item):
    """Envia um e-mail HTML estruturado para todos os destinatários via API Gmail v1."""
    msg = MIMEMultipart("alternative")
    msg["Subject"] = "📢 Nova publicación: " + item["title"][:80]
    msg["From"] = EMAIL_FROM
    msg["To"] = EMAIL_TO
    msg["Date"] = formatdate(localtime=True)
    msg["Message-ID"] = make_msgid()
    msg.attach(MIMEText(_build_plain(item), "plain", "utf-8"))
    msg.attach(MIMEText(_build_html(item), "html", "utf-8"))
    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode("ascii")

    token = get_access_token()
    req = urllib.request.Request(
        "https://gmail.googleapis.com/gmail/v1/users/me/messages/send",
        data=json.dumps({"raw": raw}).encode("utf-8"),
        headers={
            "Authorization": "Bearer " + token,
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        resp = json.load(r)
        print("Email enviado: HTTP %d (%s) msg_id=%s para [%s]"
              % (r.status, r.reason, resp.get("id"), EMAIL_TO))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--state", default=os.path.dirname(os.path.abspath(__file__)),
                    help="directorio onde gardar estado.json")
    args = ap.parse_args()
    os.makedirs(args.state, exist_ok=True)
    state_path = os.path.join(args.state, "estado.json")

    first_run = not os.path.exists(state_path)
    visto = set()
    if os.path.exists(state_path):
        try:
            visto = set(json.load(open(state_path)).get("vistos", []))
        except Exception:
            pass

    body, itens, erros = None, [], []
    for u in FEEDS:
        try:
            b = fetch(u)
            it = parse_items(b)
            if it:
                body, itens = b, it
                break
            erros.append(u + " (baleiro)")
        except Exception as e:
            erros.append(u + " -> " + str(e))

    if body is None:
        print("FALLOU obter o feed:")
        for e in erros:
            print("  " + e)
        sys.exit(1)

    novos = [i for i in itens if i["link"] not in visto]
    json.dump({
        "vistos": sorted({i["link"] for i in itens} | visto),
        "ultima": time.strftime("%Y-%m-%d %H:%M"),
    }, open(state_path, "w"), ensure_ascii=False, indent=1)

    if first_run:
        # primeira execução: grava o estado actual sem notificar
        print("Primeira execução: %d artigos gravados como vistos (sen notificacións)." % len(itens))
        sys.exit(0)

    print("Feed OK: %d artigos totais, %d novos" % (len(itens), len(novos)))
    for n in novos:
        print("NOVO: %s | %s | %s" % (n["title"], n["link"], n["date"]))

    env_ok = all(os.environ.get(k) for k in
                 ("EMAIL_REFRESH_TOKEN", "EMAIL_CLIENT_ID", "EMAIL_CLIENT_SECRET"))
    if novos:
        if not env_ok:
            print("AVISO: variáveis EMAIL_REFRESH_TOKEN/EMAIL_CLIENT_ID/EMAIL_CLIENT_SECRET "
                  "não definidas; notificação por e-mail desativada.")
        else:
            for n in novos:
                try:
                    send_email(n)
                except Exception as e:
                    print("ERRO ao enviar e-mail: %s" % e)
    sys.exit(0)


if __name__ == "__main__":
    main()
