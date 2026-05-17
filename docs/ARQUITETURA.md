# Arquitetura do sistema

## Visão geral

```text
┌─────────────┐   HTTP/SSE    ┌──────────────────────────────────┐
│  Navegador  │ ────────────► │  Fly.io (máquina 1 ou 2)         │
│ index.html  │               │  ┌────────────┐   TCP    ┌──────┐ │
└─────────────┘               │  │  proxy.py  │ ───────► │server│ │
                              │  │  :8080     │  :9000   │ .py  │ │
                              │  └────────────┘          └──┬───┘ │
                              └───────────────────────────┼─────┘
                                                          │
                                                 ┌────────▼────────┐
                                                 │ Redis (Upstash) │
                                                 └─────────────────┘
```

O navegador **não** abre socket TCP com o servidor de chat. O **proxy** (`proxy.py`) faz isso — atendendo ao enunciado (cliente com thread de recepção + servidor com thread por conexão).

## Papéis dos módulos

| Arquivo | Papel |
|---------|--------|
| `index.html` | Interface web (login, sala, lista de online) |
| `proxy.py` | Servidor HTTP para o browser + ponte TCP (thread recv por usuário) |
| `server.py` | Servidor de chat TCP (thread por conexão) |
| `protocol.py` | Formato das mensagens (JSON por linha — NDJSON) |
| `redis_backend.py` | Histórico, sessões, pub/sub entre VMs |
| `affinity.py` | Cookie + `fly-replay` para manter HTTP na VM certa |
| `stack.py` | Sobe `server.py` e `proxy.py` no mesmo processo (produção) |

## Caminho de uma mensagem

1. Usuário digita e envia no navegador.
2. `POST /message` (HTTP) chega ao **proxy**.
3. Proxy envia `{"type":"message",...}` pelo **socket TCP** ao **servidor**.
4. Servidor valida, grava no **Redis** e publica no canal pub/sub.
5. Servidor faz broadcast TCP local; outras VMs recebem via Redis.
6. Proxy recebe o evento (TCP e/ou Redis) e encaminha ao navegador via **SSE** (`GET /events`).

Todas as mensagens passam pelo servidor antes de chegar aos demais — requisito do trabalho.

## Threads

| Local | Implementação |
|-------|----------------|
| Servidor | `ClientSession(threading.Thread)` — uma por conexão TCP |
| Proxy | `TCPSession._recv_thread` — uma por usuário logado |
| Servidor / Proxy | Thread daemon no subscriber Redis pub/sub |
| Proxy HTTP | `ThreadingHTTPServer` — uma thread por requisição HTTP |

## Failover (duas máquinas Fly)

- `fly scale count 2` — duas réplicas do container.
- Estado compartilhado no Redis (histórico, presença, pub/sub).
- Cookie `fly_machine_id` + `affinity.py` mantêm o HTTP do mesmo usuário na VM que detém a sessão TCP.
- Se uma VM cair: `POST /resume` na VM viva + histórico `since` + novo SSE.

## Como executar

| Situação | Comando |
|----------|---------|
| Produção / Fly / Docker | `python stack.py` |
| No seu PC | `.\LOCAL_run.ps1` |
| Só servidor TCP (debug) | `python server.py` |
| Só proxy (debug) | `python proxy.py` (servidor TCP já rodando) |

Mais: [DEPLOY.md](DEPLOY.md) · Contratos: [API.md](API.md)
