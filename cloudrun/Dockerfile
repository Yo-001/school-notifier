# Monitor RSS CEIP Xosé Fernández López — Cloud Run Job (execução diária)
# Imagem mínima. Zero dependências externas (só stdlib). IP europeu (região do job).
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

COPY monitor.py /app/monitor.py

# O estado (links vistos) persiste via volume Cloud Storage FUSE montado em /data.
ENTRYPOINT ["python", "/app/monitor.py", "--state", "/data"]