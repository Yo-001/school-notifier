#!/usr/bin/env python3
"""Wrapper de arranque para o monitor como Cloud Run Job.

O monitor grava o estado (links xa vistos) nun directorio local, que nun job de
Cloud Run é efémero. Este wrapper sincroniza ese estado con un bucket de GCS
(API REST, só stdlib) para que persista entre execucións e non se re-notifiquen
artigos antigos.

Fluxo:
  1. Descarga estado.json do bucket (se existe) para /data.
  2. Executa monitor.py --state /data (que engade os novos e grava o estado).
  3. Sube estado.json de volta ao bucket.
"""
import os, subprocess, sys, urllib.request, urllib.error

BUCKET = os.environ.get("STATE_BUCKET", "edu-monitor-state-514315")
STATE_OBJ = "estado.json"
DATA_DIR = "/data"
STATE_LOCAL = os.path.join(DATA_DIR, STATE_OBJ)

META_TOKEN = "http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/token"


def get_token():
    req = urllib.request.Request(META_TOKEN, headers={"Metadata-Flavor": "Google"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.read().decode()


def download_state(token):
    url = "https://storage.googleapis.com/storage/v1/b/%s/o/%s?alt=media" % (BUCKET, STATE_OBJ)
    req = urllib.request.Request(url, headers={"Authorization": "Bearer " + token})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            body = r.read()
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return  # sen estado previo (primeira execución)
        print("AVISO: non se puido descargar o estado (%s)" % e.code)
        return
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(STATE_LOCAL, "wb") as f:
        f.write(body)
    print("Estado descargado de GCS.")


def upload_state(token):
    if not os.path.exists(STATE_LOCAL):
        return
    body = open(STATE_LOCAL, "rb").read()
    url = "https://storage.googleapis.com/upload/storage/v1/b/%s/o?uploadType=media&name=%s" % (BUCKET, STATE_OBJ)
    req = urllib.request.Request(
        url, data=body, method="POST",
        headers={"Authorization": "Bearer " + token, "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        r.read()
    print("Estado subido a GCS.")


def main():
    os.makedirs(DATA_DIR, exist_ok=True)
    try:
        token = get_token()
    except Exception as e:
        token = None
        print("AVISO: sen token metadata (%s); o estado non persistirá." % e)
    if token:
        download_state(token)
    rc = subprocess.call(["python", "/app/monitor.py", "--state", DATA_DIR])
    if token and rc == 0:
        try:
            upload_state(token)
        except Exception as e:
            print("AVISO: fallo ao subir o estado (%s)" % e)
    sys.exit(rc)


if __name__ == "__main__":
    main()