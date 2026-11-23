#!/usr/bin/env python3
"""Monitor do feed RSS do CEIP Plurilingüe Xosé Fernández López (O Porriño,
www.edu.xunta.gal). O portal da Xunta devolve HTTP 500 para IPs fóra de
Europa (verificado: ES/DE/CH/IT/SE -> 200; US/BR/TR/UA -> 500). Este script
debe rodar, pois, nunha máquina con IP europea (por exemplo unha VM Always
Free de Oracle Cloud en Madrid, ou calquera VPS na UE). Se a conexión directa
fallase, usa como relevo o proxy de tradución de Google (devolve o mesmo RSS
byte a byte, só que tamén só para IPs europeas).

Novos artigos son impresos en stdout e, se se indica --topic, enviados por
push a ntfy.sh (sen rexistro; subscribirse en https://ntfy.sh/<topic>).

Uso:
  python3 monitor.py --state /camiño/do/directorio --topic nome-do-topic
Cron diario (crontab -e), p. ex. ás 06:30:
  30 6 * * * cd /opt/edu-monitor && /usr/bin/python3 monitor.py --state . >> cron.log 2>&1
"""
import argparse, json, os, sys, time, urllib.request
import xml.etree.ElementTree as ET

FEEDS = [
    # 1º directo (funciona desde calquera IP europea)
    "https://www.edu.xunta.gal/centros/ceipxosefernandez/rss.xml",
    # 2º relevo de Google (mesmo contido; só desde IP europea)
    "https://www-edu-xunta-gal.translate.goog/centros/ceipxosefernandez/rss.xml",
    # 3º formulario antigo de Google Translate
    "https://translate.google.com/translate?u=https://www.edu.xunta.gal/centros/ceipxosefernandez/rss.xml&sl=gl&tl=en",
]
UA = "Mozilla/5.0 (compatible; edu-monitor/1.0)"


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
        if link:
            out.append({"title": title, "link": link, "date": date.strip()})
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--state", default=os.path.dirname(os.path.abspath(__file__)),
                    help="directorio onde gardar estado.json")
    ap.add_argument("--topic", default=os.environ.get("NTFY_TOPIC", ""),
                    help="topic de ntfy.sh para notificacións push (opcional)")
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

    if novos and args.topic:
        for n in novos:
            msg = "Novidade no CEIP Xosé Fernández López:\n%s\n%s" % (n["title"], n["link"])
            r = urllib.request.Request(
                "https://ntfy.sh/" + args.topic,
                data=msg.encode("utf-8"),
                headers={"Title": "CEIP Xosé Fdz. López", "Priority": "default"},
            )
            urllib.request.urlopen(r, timeout=30)
    sys.exit(0)


if __name__ == "__main__":
    main()
