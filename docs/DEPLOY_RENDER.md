# Deploy no Render + balanceamento (Load Balancer)

> **Guia passo a passo completo (Fly + Render + teste com 2 usuários):** [DEPLOY_PRODUCTION.md](./DEPLOY_PRODUCTION.md)

Este documento descreve como encaixar o **MVP servidor+proxy** na infraestrutura **Render**, com foco no que é (e o que **não** é) suportado nativamente pela plataforma.

## 1) Redis (estado compartilhado)

O servidor usa Redis para:

- **Histórico**: lista `chat:history`
- **Presença global** (MVP): set `chat:online`
- **Replicação entre instâncias**: canal pub/sub configurável (`PUBSUB_CHANNEL`, default `chat:broadcast`)

### Opção recomendada no ecossistema Render

Crie um **Render Key Value** (Redis®-compatível) e use a URL fornecida no painel como `REDIS_URL`.

> A URL costuma funcionar com `redis://` ou `rediss://` (TLS). Use exatamente o que o painel indicar.

### Variáveis de ambiente (servidor)

Veja também `.env.example`. Mínimo:

- `REDIS_URL` (**obrigatório**)
- `CHAT_HOST` (tipicamente `0.0.0.0` dentro do container)
- `CHAT_PORT` (porta interna do processo; veja seção de TCP abaixo)

## 2) O serviço de chat (TCP) e a limitação importante da borda pública Render

Na prática, o produto **Web Service** do Render expõe **HTTP(S)** na internet para o hostname `*.onrender.com`.

Para este trabalho, o **proxy** precisa abrir um **socket TCP** “cru” até o servidor de chat. **Não assuma** que um listener TCP arbitrário ficará acessível publicamente como no `localhost` — isso depende do **tipo de serviço** e da configuração de rede.

Em alto nível:

- **Private Service** no Render aceita TCP na rede privada, mas **não** recebe tráfego direto da internet (útil se *toda* a carga vier de outro serviço Render no mesmo projeto/região).
- **Web Service** é o padrão para HTTP público, não para expor um protocolo TCP customizado de ponta a ponta.

### Como isso afeta o MVP

1. **Se você hospedar o servidor TCP como Private Service** no Render:
   - o **proxy local** (máquina do usuário) **não conseguirá conectar** a menos que exista algum mecanismo adicional (VPN, túnel, bastion, etc.).
   - isso continua válido para demonstrar **alta disponibilidade interna** (2 instâncias + Redis + load balancer interno, quando aplicável).

2. **Se você precisa cumprir o requisito de “servidor online acessível fora do localhost” com TCP nativo**:
   - normalmente será necessário um provedor que permita **porta TCP pública** (VM, Fly.io, Railway com TCP, etc.), **ou**
   - manter Redis no Render e rodar o processo de chat em outro host — a arquitetura do MVP já desacopla estado (`REDIS_URL`) do processo Python.

> Recomendação honesta para a banca: descreva no relatório **onde** o TCP fica exposto publicamente e **como** a instância se recupera via Redis quando há failover.

## 3) Load Balancer / múltiplas instâncias (documentação oficial)

O Render documenta escalonamento e distribuição de tráfego em **múltiplas instâncias** de um mesmo serviço (com health checks). Leia:

- [Scaling Render Services](https://render.com/docs/scaling)

Pontos úteis para o seu relatório:

- **Health checks** ajudam a retirar instâncias ruins do conjunto saudável.
- Em serviços com múltiplas instâncias, o provedor **pode balancear** novas conexões entre réplicas (estrategia e nuances dependem do tipo de serviço e plano).

### TCP atrás de múltiplas instâncias

Para protocolos **com estado por conexão** (TCP long-lived), balanceamento ingênuo pode:

- espalhar usuários em instâncias diferentes (ok para este MVP, graças ao Redis pub/sub),
- **mas** exige que reconexões tratem autenticação novamente (o proxy precisa suportar reconexão; hoje o MVP assume sessão de longa duração).

## 4) Build & run (Docker)

Na raiz do repositório existe `Dockerfile.server` para empacotar apenas `common/` + `server/`.

Exemplo de variáveis no painel Render:

- `REDIS_URL` definido como *secret*
- `CHAT_HOST=0.0.0.0`
- `CHAT_PORT` consistente com a porta que o serviço espera receber **na rede onde ele estiver exposto**

Comando:

- `python -m server`

> Lembre de definir `PYTHONPATH=/app` (já presente no Dockerfile proposto) ou equivalente.

## 5) Checklist operacional (MVP)

- [ ] Redis acessível a partir de todas as instâncias (`REDIS_URL`).
- [ ] Canal pub/sub igual em todas as instâncias (`PUBSUB_CHANNEL`).
- [ ] Duas instâncias publicando/consumindo o mesmo Redis.
- [ ] Estratégia clara de **exposição TCP** (interna vs pública) documentada no relatório.
- [ ] Timeouts/reconexão do proxy documentados como “trabalho futuro” se ainda não existirem.

## 6) Manutenção: presença presa no Redis

Se um processo morrer sem rodar o cleanup da sessão, `chat:online` pode reter um username.

Durante desenvolvimento, você pode limpar com `DEL chat:online` no Redis (cuidado em produção). O relatório pode mencionar TTL/ heartbeats como melhoria.
