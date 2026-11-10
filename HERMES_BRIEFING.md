# Project Briefing: School Monitor (CEIP Xosé Fernández López)

## 1. O que é o Projeto

Um monitor automatizado em Python voltado a acompanhar comunicados e novidades publicados no portal escolar oficial do colégio **CEIP Plurilingüe Xosé Fernández López** (Galícia, Espanha: `https://www.edu.xunta.gal/centros/ceipxosefernandez`). O sistema detecta novas publicações e envia alertas por e-mail (via SMTP Gmail), com custo zero de infraestrutura e execução automática diária via GitHub Actions.

---

## 2. Objetivo Principal

Garantir que os pais nunca percam avisos críticos, prazos de matrículas, festividades ou convocações da escola da filha, superando problemas de oscilação do site institucional por meio de fallbacks resilientes de scraping e agregação.

---

## 3. O que Já Foi Feito

- **Arquitetura de Extração Resiliente (`monitor.py`):**
  - **Estratégia 1:** Ingestão via Feed RSS oficial (`/rss.xml`).
  - **Estratégia 2:** Fallback para scraping HTML da listagem (`/node`) com BeautifulSoup caso o RSS falhe ou esteja vazio.
  - **Mecanismo de Resiliência de Rede:** Fallback progressivo de requisições (HTTPS -> HTTP -> Sem custom User-Agent -> Proxy público Jina Reader `https://r.jina.ai`).
- **Gerenciamento de Estado (`state/seen.json`):**
  - Controle persistente com histórico dos últimos 500 IDs/links já processados para evitar e-mails duplicados.
- **Sistema de Envio de E-mail:**
  - Formatação e disparo unificado via SMTP seguro (Gmail com App Password).
  - Contador de falhas consecutivas (`failure_count.json`) com e-mail de alerta em caso de 3 falhas consecutivas.
- **Modo Debug / Simulação:**
  - Flag `--dry-run` para testar localmente sem enviar e-mails reais.
- **Automação CI/CD:**
  - Workflow do GitHub Actions configurado (`.github/workflows/monitor.yml`) para rodar via cron às 07:00 UTC (08:00 horário local).
- **Testes Unitários:**
  - Testes com `pytest` cobrindo parsers de RSS e HTML (`tests/test_monitor.py` e fixtures).

---

## 4. Etapa Atual

O pipeline base de scraping, persistência de estado e envio de e-mails está concluído e validado com testes. Estágio de produção configurado.

1. Validação de credenciais e primeiro disparo real de homologação.
2. Os comunicados estão em galego/espanhol formal e texto cru (nenhuma síntese automática).

---

## 5. Próximas Etapas para Operação Completa e Melhorias

> **Nota (2026-11):** A síntese automática com IA (`gerar_resumo_inteligente`, dependente do serviço OmniRoute em `localhost:20128`) foi **removida** por falta de utilidade. O monitor voltou a operar sem dependência externa de IA, com custo zero garantido.

### Etapa 5.1: Ativação dos Secrets no GitHub

- Segredos configurados no repositório GitHub (3 Nov):
  - ✅ `GMAIL_USER`
  - ✅ `GMAIL_APP_PASSWORD`
  - ✅ `TO_EMAIL`

### Etapa 5.2: Execução de Bootstrapping

- ✅ Executada a primeira rodada (`python monitor.py`) popular do `state/seen.json` inicial sem disparar notificações em lote retroativas.
