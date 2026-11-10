# Monitor de Publicações da Escola CEIP Xosé Fernández López

Este repositório contém um script Python que monitora o feed RSS da escola **CEIP Plurilingüe Xosé Fernández López** (https://www.edu.xunta.gal/centros/ceipxosefernandez) e envia um e‑mail sempre que uma nova publicação for adicionada.

## Funcionalidades
- Usa o *feed RSS* oficial como fonte de dados (fonte única e limpa).
- Mantém um estado local (`state/seen.json`) com os últimos 500 IDs já processados.
- Envia um e‑mail (SMTP Gmail) contendo título, link, data e resumo das novas publicações. Se houver várias novidades, elas são enviadas em um único e‑mail.
- Suporta `--dry-run` para depuração (imprime o que seria enviado).
- Tenta 3 vezes com back‑off exponencial + 1 tentativa final sem User‑Agent custom.
- Em caso de falha total na coleta, envia um e‑mail de alerta imediatamente.
- Pode ser executado automaticamente via **GitHub Actions** todos os dias às 07:00 UTC.

## Configuração
1. Crie um **app password** para a conta Gmail que enviará os e‑mails.  
2. No repositório do GitHub, adicione os seguintes *secrets*:
   - `GMAIL_USER` – endereço de e‑mail da conta Gmail.
   - `GMAIL_APP_PASSWORD` – o app‑password gerado.
   - `TO_EMAIL` – endereço de destino (pode ser o mesmo ou outro).
3. Opcionalmente ajuste `config.yaml` se desejar mudar a URL do RSS ou o assunto do e‑mail.

## Como usar
- **Execução local** (para teste ou depuração):
  ```bash
  python -m venv .venv
  .venv\Scripts\activate  # Windows
  pip install -r requirements.txt
  python monitor.py --dry-run
  ```
- **GitHub Actions**: o workflow já está configurado (arquivo `.github/workflows/monitor.yml`).  
  O cron `0 7 * * *` executa o monitor diariamente às 07:00 UTC (08:00 em Vigo no inverno).  
  Também é possível disparar manualmente via `workflow_dispatch`.

## Estrutura do repositório
```
school_monitor/
├─ .github/
│  └─ workflows/monitor.yml   # GitHub Actions workflow
├─ state/
│  └─ seen.json               # IDs já vistos (gerado na primeira execução)
├─ tests/
│  ├─ fixtures/
│  │   └─ sample.rss         # RSS de exemplo
│  └─ test_monitor.py       # Testes com pytest
├─ config.yaml                # Configurações do monitor
├─ monitor.py                 # Script principal
├─ requirements.txt           # Dependências Python
└─ README.md                  # Este documento
```

## Próximos passos
1. Clone este repositório em sua conta GitHub.
2. Habilite **GitHub Actions** nas *Settings* → *Actions*.
3. Adicione os *secrets* listados acima.
4. Opcional: ajuste `config.yaml` se necessário.
5. Na primeira execução o script criará `state/seen.json` com o estado atual – nenhum e‑mail será enviado.
6. A partir da segunda execução, novas publicações gerarão e‑mail.

---

*Este projeto foi desenvolvido seguindo as restrições de custo zero e utiliza apenas bibliotecas Python de código aberto.*