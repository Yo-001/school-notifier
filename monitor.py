import argparse
import json
import os
import smtplib
import ssl
import sys
import time
from email.message import EmailMessage
from pathlib import Path

import feedparser
import requests
import yaml
from bs4 import BeautifulSoup

CONFIG_PATH = Path(__file__).with_name('config.yaml')
STATE_DIR = Path(__file__).parent / 'state'
SEEN_PATH = STATE_DIR / 'seen.json'
FAIL_COUNT_PATH = STATE_DIR / 'failure_count.json'

def load_config():
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

# Load configuration at import time for helper functions that may be called independently
config = load_config()

def load_seen():
    if SEEN_PATH.is_file():
        try:
            data = json.load(open(SEEN_PATH, 'r', encoding='utf-8'))
            return set(data.get('ids', []))
        except Exception:
            return set()
    return set()

def save_seen(ids):
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    json.dump({'ids': list(ids)}, open(SEEN_PATH, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)

def load_failure_count():
    if FAIL_COUNT_PATH.is_file():
        try:
            return json.load(open(FAIL_COUNT_PATH, 'r'))
        except Exception:
            return 0
    return 0

def save_failure_count(cnt):
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    json.dump(cnt, open(FAIL_COUNT_PATH, 'w'))


def fetch_url(url: str, user_agent: str, timeout: int = 60) -> str:
    """Fetch a URL with retries and progressive fallbacks.

    1️⃣  Try the original HTTPS URL with the configured User‑Agent.
    2️⃣  If all retries fail, try the same URL using plain HTTP.
    3️⃣  If that also fails, retry without a custom User‑Agent.
    4️⃣  As a last resort, request the page through the public
        proxy https://r.jina.ai (which mirrors the target page).

    Returns the raw response text or raises the final exception.
    """
    headers = {"User-Agent": user_agent}

    # ---------- 1️⃣ primary attempts (custom UA) ----------
    for attempt in range(config["retry_attempts"]):
        try:
            resp = requests.get(url, headers=headers, timeout=timeout)
            resp.raise_for_status()
            return resp.text
        except Exception as e:
            print(
                f"Attempt {attempt+1}/{config['retry_attempts']} failed for {url}: {e}"
            )
            if attempt < config["retry_attempts"] - 1:
                backoff = config["retry_backoff_factor"] ** attempt
                time.sleep(backoff)

    # ---------- 2️⃣ HTTP fallback ----------
    if url.startswith("https://"):
        http_url = "http://" + url[len("https://"):]
        try:
            print("Trying HTTP fallback")
            resp = requests.get(http_url, headers=headers, timeout=timeout)
            resp.raise_for_status()
            return resp.text
        except Exception as e2:
            print(f"HTTP fallback also failed: {e2}")

    # ---------- 3️⃣ generic UA ----------
    try:
        print("Falling back to generic User‑Agent")
        resp = requests.get(url, timeout=timeout)  # no custom UA
        resp.raise_for_status()
        return resp.text
    except Exception as e3:
        print(f"Generic UA fallback also failed: {e3}")

    # ---------- 4️⃣ public proxy (r.jina.ai) ----------
    proxy_url = f"https://r.jina.ai/http://{url.lstrip('https://')}"
    try:
        print("Trying public proxy (r.jina.ai)…")
        resp = requests.get(proxy_url, timeout=timeout)
        resp.raise_for_status()
        return resp.text
    except Exception as e4:
        print(f"Proxy fallback also failed: {e4}")
        raise e4


def parse_rss(content):
    feed = feedparser.parse(content)
    items = []
    for entry in feed.entries:
        # guid may be a full link; extract node id numeric part
        guid = entry.get('id') or entry.get('guid') or entry.get('link')
        if not guid:
            continue
        # assume node id is the last numeric component of the URL
        try:
            node_id = int(guid.rstrip('/').split('/')[-1])
        except Exception:
            continue
        items.append({
            'id': node_id,
            'title': entry.get('title', '').strip(),
            'link': entry.get('link', '').strip(),
            'date': entry.get('published', entry.get('updated', '')).strip(),
            'summary': entry.get('summary', '').strip()
        })
    return items

def parse_html(content):
    soup = BeautifulSoup(content, 'html.parser')
    items = []
    for a in soup.select(config['html_selector']['entry']):
        href = a.get('href')
        if not href:
            continue
        try:
            node_id = int(href.rstrip('/').split('/')[-1])
        except Exception:
            continue
        # date text is the sibling text after the link; crude extraction
        parent = a.parent
        date_text = ''
        if parent:
            # find the following text node that contains 'Enviado por'
            sibling = a.next_sibling
            if sibling and isinstance(sibling, str):
                date_text = sibling.strip()
            else:
                # fallback: look for <p> after h2
                p = parent.find_next('p')
                if p:
                    date_text = p.get_text(strip=True)
        items.append({
            'id': node_id,
            'title': a.get_text(strip=True),
            'link': f"https://www.edu.xunta.gal{href}" if href.startswith('/') else href,
            'date': date_text,
            'summary': ''
        })
    return items

def send_email(new_items, dry_run=False):
    if not new_items:
        return
    
    subject = f"{config['email_subject_prefix']} Novas publicações"
    body_lines = []
    for it in new_items:
        body_lines.append(f"Título: {it['title']}")
        body_lines.append(f"Link: {it['link']}")
        body_lines.append(f"Data: {it['date']}")
        if it.get('summary'):
            body_lines.append(f"Resumo: {it['summary']}")
        body_lines.append('')
    body = '\n'.join(body_lines)
    if dry_run:
        print('--- DRY RUN EMAIL ---')
        print('Subject:', subject)
        print(body)
        return
    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = os.getenv('GMAIL_USER')
    msg['To'] = os.getenv('TO_EMAIL')
    msg.set_content(body)
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as server:
        server.login(os.getenv('GMAIL_USER'), os.getenv('GMAIL_APP_PASSWORD'))
        server.send_message(msg)

def main():
    parser = argparse.ArgumentParser(description='Monitor school publications')
    parser.add_argument('--dry-run', action='store_true', help='Print actions instead of sending email')
    args = parser.parse_args()

    global config
    config = load_config()
    user_agent = config['user_agent'].format(to_email=os.getenv('TO_EMAIL', ''))

    # fetch data (RSS first)
    items = []
    try:
        rss_text = fetch_url(config['rss_url'], user_agent)
        items = parse_rss(rss_text)
        if not items:
            raise ValueError('RSS parsed zero items')
        source = 'RSS'
    except Exception as e:
        # fallback to HTML
        try:
            html_text = fetch_url(config['html_url'], user_agent)
            items = parse_html(html_text)
            source = 'HTML'
        except Exception as e2:
            # total failure
            fail_cnt = load_failure_count() + 1
            save_failure_count(fail_cnt)
            if fail_cnt >= 3:
                # send alert once
                alert_items = [{'title': f'Falha ao coletar dados ({source if "source" in locals() else "nenhum"})',
                                'link': '', 'date': '', 'summary': str(e2)}]
                send_email(alert_items, dry_run=args.dry_run)
                save_failure_count(0)
            sys.exit(1)
    # success – reset failure count
    save_failure_count(0)

    seen_ids = load_seen()
    new_items = [it for it in items if it['id'] not in seen_ids]
    if not seen_ids:
        # first run: baseline, do not send email
        new_items = []
    if new_items:
        send_email(new_items, dry_run=args.dry_run)
    # update seen list, keep latest max_seen_ids
    all_ids = {it['id'] for it in items}
    combined = list(all_ids | seen_ids)
    # Keep most recent up to max_seen_ids (by numeric order, higher = newer)
    combined_sorted = sorted(combined, reverse=True)[:config['max_seen_ids']]
    save_seen(set(combined_sorted))

if __name__ == '__main__':
    main()
