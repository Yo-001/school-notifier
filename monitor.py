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

CONFIG_PATH = Path(__file__).with_name('config.yaml')
STATE_DIR = Path(__file__).parent / 'state'
SEEN_PATH = STATE_DIR / 'seen.json'


def load_config():
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


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


def fetch_url(url: str, user_agent: str, timeout: int = 60) -> str:
    """Fetch a URL with retries (exponential backoff) and one final attempt
    without a custom User-Agent. Returns the raw response text or raises."""
    headers = {"User-Agent": user_agent}
    for attempt in range(config["retry_attempts"]):
        try:
            resp = requests.get(url, headers=headers, timeout=timeout)
            resp.raise_for_status()
            return resp.text
        except Exception as e:
            print(f"Attempt {attempt+1}/{config['retry_attempts']} failed for {url}: {e}")
            if attempt < config["retry_attempts"] - 1:
                backoff = config["retry_backoff_factor"] ** attempt
                time.sleep(backoff)

    # Final fallback: try once more without a custom User-Agent
    print("Falling back to generic User-Agent")
    resp = requests.get(url, timeout=timeout)
    resp.raise_for_status()
    return resp.text


def parse_rss(content):
    """Parse the school RSS feed. The feed's <guid> looks like
    '481 at https://.../ceipxosefernandez', so the numeric node id is
    taken from <link> (.../node/481)."""
    feed = feedparser.parse(content)
    items = []
    for entry in feed.entries:
        link = entry.get('link', '').strip()
        try:
            node_id = int(link.rstrip('/').split('/')[-1])
        except Exception:
            continue
        items.append({
            'id': node_id,
            'title': entry.get('title', '').strip(),
            'link': link,
            'date': entry.get('published', entry.get('updated', '')).strip(),
            'summary': entry.get('summary', '').strip()
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
    parser = argparse.ArgumentParser(description='Monitor school publications (RSS)')
    parser.add_argument('--dry-run', action='store_true', help='Print actions instead of sending email')
    args = parser.parse_args()

    global config
    config = load_config()
    user_agent = config['user_agent'].format(to_email=os.getenv('TO_EMAIL', ''))

    # Fetch RSS (the only data source)
    try:
        rss_text = fetch_url(config['rss_url'], user_agent)
        items = parse_rss(rss_text)
        if not items:
            raise ValueError('RSS parsed no items')
    except Exception as e:
        # Total failure -> alert immediately
        alert_items = [{
            'title': 'Falha ao coletar dados do feed RSS',
            'link': '',
            'date': '',
            'summary': str(e),
        }]
        send_email(alert_items, dry_run=args.dry_run)
        sys.exit(1)

    seen_ids = load_seen()
    new_items = [it for it in items if it['id'] not in seen_ids]
    if not seen_ids:
        # First run: establish baseline, do not send email
        new_items = []
    if new_items:
        send_email(new_items, dry_run=args.dry_run)

    # Update seen list, keep latest max_seen_ids (higher id = newer)
    all_ids = {it['id'] for it in items}
    combined_sorted = sorted(all_ids | seen_ids, reverse=True)[:config['max_seen_ids']]
    save_seen(set(combined_sorted))


if __name__ == '__main__':
    main()