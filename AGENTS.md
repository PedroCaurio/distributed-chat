# Enunciado do Trabalho

Desenvolva um chat multiusuário usando sockets, com arquitetura cliente-servidor e uso de threads. O chat deve permitir que vários usuários conversem em tempo real, com todas as mensagens passando primeiro pelo servidor, que as envia aos demais usuários. O servidor deve ter alguma forma de tolerância a falhas (exemplo: servidor secundário ativado automaticamente).

## Implementação neste repositório

| Requisito | Onde |
|-----------|------|
| Sockets TCP nativos | `common/protocol.py`, `server/session.py`, `client/socket_bridge.py` |
| Thread por conexão (servidor) | `ClientSession` em `server/session.py` |
| Thread recv (cliente) | `SocketBridge._recv_loop` em `client/socket_bridge.py` |
| HTTP embutido no cliente | `client/app.py` (FastAPI + uvicorn) |
| Navegador sem instalar | React servido pelo cliente; deploy Fly.io |
| Failover | 2 VMs Fly + Upstash Redis + `GET /history` + reconexão SSE |
| **Sem WebSocket** | Browser usa HTTP + SSE; transporte real é TCP |

## Arquitetura

```text
Browser → HTTPS → client/ (8080) → TCP → server/ (9000) → Redis
                      ↑                      ↑
              thread recv/user        thread/conn
```

Produção: `python -m stack` (servidor TCP + cliente HTTP no mesmo container).

## Stack

- **Python:** FastAPI (cliente), threading, socket, Redis
- **Front:** React, Vite
- **Infra:** Fly.io, Upstash

## Documentação

- `docs/ARCHITECTURE.md`
- `docs/PAYLOADS.md`
- `docs/DEPLOY.md`

## Checklist de avaliação

- [ ] URL pública Fly (sem instalar nada)
- [ ] Múltiplos usuários (2 abas / navegadores)
- [ ] Username + histórico
- [ ] Explicar threads (servidor + cliente) e sockets TCP
- [ ] Demo failover: `fly machine stop` → reconexão
- [ ] `requirements.txt` + README + relatório PDF
