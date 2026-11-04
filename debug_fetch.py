import requests, sys
url='https://www.edu.xunta.gal/centros/ceipxosefernandez/rss.xml'
headers={'User-Agent':'school-monitor/1.0 (contact: test@example.com)'}
try:
    resp=requests.get(url, headers=headers, timeout=20)
    print('status', resp.status_code)
    print('len', len(resp.text))
    print(resp.text[:200])
except Exception as e:
    print('error', e)
