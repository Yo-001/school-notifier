# Monitor diário do CEIP Xosé Fernández López (edu.xunta.gal)

Solução recomendada (a mais simples com custo zero e confiável, verificada):

> **Uma VM sempre-grátis do Oracle Cloud na região Madrid (eu-madrid-1) + cron + `monitor.py`.**
> IP espanhol -> o portal responde 200 diretamente. Custo: €0 para sempre.

## Porquê

Verificado em 2026-11-10 (testes reais, via check-host.net e curl):

- O portal **bloqueia por geografia, não por "IP de datacenter"**: de nós na UE
  (ES, DE, CH, IT, SE) o RSS responde **200**; de for a UE (US, BR, TR, UA) devolve **500**.
- Proxies grátis "universais" não servem: r.jina.ai -> 500 do alvo; allorigins e
  codetabs -> 522 (infra deles fora); corsproxy -> 401 (agora é pago); thingsproxy -> morto;
  textise -> bloqueado pelo próprio Cloudflare; wsrv.nl -> só imagens.
- O proxy de tradução do Google (translate.goog) devolve o RSS **byte a byte idêntico**
  (sha256 igual), **mas também só responde 200 para IPs europeus** (testado: IP US -> 400).
  Logo não resolve o GitHub Actions (runners nos EUA -> 500/400).

Conclusão: o agendador tem de estar **na Europa**. Oracle Madrid é a opção grátis
mais simples e robusta. (Fontes de apoio: a própria Xunta declara que o seu entorno
EVA "non é viable" desde fóra de España — espazoabalar.edu.xunta.gal.)

## Passos (≈15 min, €0)

1. **Criar conta Oracle Cloud**: https://www.oracle.com/cloud/free/ — pede cartão
   (só para verificação, não cobra nada no plano Always Free).
2. **Criar a VM**: Console -> Compute -> Instances -> Create instance.
   - *Region*: **Spain (Madrid), eu-madrid-1**  ← obrigatório
   - *Image*: Ubuntu 24.04 (ou 22.04). *Shape*: VM.Standard.A1.Flex (ARM, grátis) ou
     VM.Standard.E2.1.Micro (x86, grátis). 4 OCPU/24GB ARM bastam de sobra.
   - Guarde a chave SSH (ou use a opção cloud-shell).
3. **Ligar por SSH** e rodar uma vez:
   ```bash
   mkdir -p /opt/edu-monitor && cd /opt/edu-monitor
   # copie monitor.py para este diretório (scp ou colar)
   sudo apt update && sudo apt install -y python3
   python3 monitor.py --state .          # 1ª execução: grava o estado atual (sem alertas)
   crontab -e                            # adicione a linha:
   ```
   ```cron
   30 6 * * * cd /opt/edu-monitor && /usr/bin/python3 monitor.py --state . --topic nome-do-teu-topic >> cron.log 2>&1
   ```
4. **Receber avisos**: no telemóvel, instale/abra https://ntfy.sh/nome-do-teu-topic
   (push grátis, sem registo). A cada novo artigo no RSS recebe uma notificação.
   Alternativa: Troque por email com um bloco `smtplib` no script (instruções se necessário).

Testar já: `python3 monitor.py --state . --topic teste` -> deve imprimir "0 novos".
Para confirmar um alerta, apague uma linha do `estado.json` e rode de novo.

## Alternativas (com pragas)

| Opção | Prós | Contras / praga | Testabilidade |
|---|---|---|---|
| **Oracle VM Madrid (RECOMENDADA)** | Grátis para sempre, IP ES, cron+python completo | ~15 min de setup; Oracle pode recolher ARM idle em raro excesso de capacidade (use E2.1.Micro x86 se quiser eliminar esse risco) | 100% comprovado: IP UE -> 200 direto |
| VPS pago minúsculo na UE (Hetzner CX22, ~€3,7/mês) | Mesmo que acima, sem risco de recolha | Tem custo | idem |
| Deno Deploy grátis, região eu-west, cron | Sem cartão (login GitHub), script curto | Egress UE não verificado aqui; notificação precisa de webhook externo; docs mudam | Não testado — precisa teste real |
| cron-job.org (Suíça) | Grátis, 1 clique, IP suíço -> 200 | Plano grátis só vigia status HTTP; **não lê RSS** (não detecta artigos novos) | Não serve para o objetivo |
| Visualping / Distill / Feedrabbit (alertas de mudança) | Zero código | Egress provavelmente fora da UE -> 500; planos grátis limitados | Não testado |
| **RSS do município oporrino.org** (https://oporrino.org/feed/) | Funciona de qualquer lugar (sem geo-bloqueio), site normal | Só republica parte das notícias do colégio; não é completo | Funciona, mas incompleto |
| GitHub Actions com relay do Google | Sem conta nova | Runner EUA -> 400/500; **falha** | Falhou nos testes |

## O que foi verificado (11/11/2026, hora local)

- r.jina.ai → `500` (o alvo devolve 500 ao próprio Jina) · allorigins/codetabs → `522`
  (proxy do serviço fora) · corsproxy → `401` (virou pago) · thingsproxy → `000` (morto)
  · textise → bloqueio Cloudflare do próprio textise · wsrv.nl → `404` (só imagens).
- check-host.net (nós em datacenters): ES, DE, CH, IT, SE → `200`; US, BR, TR, UA → `500`.
- Google translate.goog relay: sha256 idêntico ao RSS original (28725 bytes); IP US → `400`.
- RSS direto: 200, 10 itens atuais (ex.: "Convocatoria de eleccións ao Consello escolar").
