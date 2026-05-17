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

Caminho no repositório: pacote `src/chatnet/`.

## Papéis dos módulos

| Arquivo | Papel |
|---------|--------|
| `static/index.html` | Interface web |
| `proxy.py` | Servidor HTTP + ponte TCP (thread recv por usuário) |
| `server.py` | Servidor de chat TCP (thread por conexão) |
| `protocol.py` | NDJSON (JSON por linha) |
| `redis_backend.py` | Histórico, sessões, pub/sub |
| `affinity.py` | Cookie + `fly-replay` |
| `stack.py` | Sobe server + proxy (produção) |

## Caminho de uma mensagem

1. Usuário envia no navegador → `POST /message`.
2. Proxy encaminha pelo TCP ao servidor.
3. Servidor grava no Redis e publica no pub/sub.
4. Broadcast TCP + Redis → proxy → SSE (`GET /events`).

## Threads

| Local | Implementação |
|-------|----------------|
| Servidor | `ClientSession(threading.Thread)` |
| Proxy | `TCPSession._recv_thread` |
| Redis | Thread subscriber pub/sub |

## Como executar

| Situação | Comando |
|----------|---------|
| Produção / Fly | `python -m chatnet` |
| Local | `.\LOCAL_run.ps1` |

Mais: [DEPLOY.md](DEPLOY.md) · [API.md](API.md)
