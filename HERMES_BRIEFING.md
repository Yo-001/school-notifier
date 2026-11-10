# Project Briefing: School Monitor (CEIP Xosé Fernández López)

## 1. O que é o Projeto

Um monitor automatizado em Python voltado a acompanhar comunicados e novidades publicados no portal escolar oficial do colégio **CEIP Plurilingüe Xosé Fernández López** (Galícia, Espanha: `https://www.edu.xunta.gal/centros/ceipxosefernandez`). O sistema detecta novas publicações e envia alertas por e-mail (via SMTP Gmail), com custo zero de infraestrutura e execução automática diária via GitHub Actions.

---

## 2. Objetivo Principal

Garantir que os pais nunca percam avisos críticos, prazos de matrículas, festividades ou convocações da escola da filha, superando problemas de oscilação do site institucional por meio de fallbacks resilientes de scraping e agregação.

---

## 3. O que Já Foi Feito

- **Extração via RSS (`monitor.py`):**
  - Ingestão via Feed RSS oficial (`/rss.xml`) como **fonte única e limpa** (removido o fallback HTML).
  - **Resiliência de Rede:** retries com back-off exponencial (3x) + 1 tentativa final sem User-Agent custom.
- **Gerenciamento de Estado (`state/seen.json`):**
  - Controle persistente com histórico dos últimos 500 IDs já processados para evitar e-mails duplicados.
- **Sistema de Envio de E-mail:**
  - Formatação e disparo unificado via SMTP seguro (Gmail com App Password).
  - Em caso de falha total na coleta, envia e-mail de alerta **imediatamente** (removido o contador de 3 falhas).
- **Modo Debug / Simulação:**
  - Flag `--dry-run` para testar localmente sem enviar e-mails reais.
- **Automação CI/CD:**
  - Workflow do GitHub Actions configurado (`.github/workflows/monitor.yml`) para rodar via cron às 07:00 UTC (08:00 horário local).
- **Testes Unitários:**
  - Testes com `pytest` cobrindo o parser RSS, o fluxo de e-mail e o alerta de falha (`tests/test_monitor.py`).

---

## 4. Etapa Atual

O pipeline base de coleta RSS, persistência de estado e envio de e-mails está concluído e validado com testes. Estágio de produção configurado.

1. Validação de credenciais e disparo real de homologação.
2. Os comunicados vêm em galego/espanhol formal e texto cru (nenhuma síntese automática).

---

## 5. Próximas Etapas para Operação Completa e Melhorias

> **Nota (2026-11):** A síntese automática com IA (`gerar_resumo_inteligente`, dependente do serviço OmniRoute) foi **removida** por falta de utilidade. O fallback de scraping HTML e o proxy público também foram removidos — o projeto opera agora exclusivamente via RSS, com custo zero e dependência mínima.

### Etapa 5.1: Ativação dos Secrets no GitHub

- Segredos configurados no repositório GitHub (3 Nov):
  - ✅ `GMAIL_USER`
  - ✅ `GMAIL_APP_PASSWORD`
  - ✅ `TO_EMAIL`

### Etapa 5.2: Execução de Bootstrapping

- ✅ Executada a primeira rodada (`python monitor.py`) popular do `state/seen.json` inicial sem disparar notificações em lote retroativas.
