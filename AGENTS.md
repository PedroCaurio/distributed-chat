# Guia rápido do repositório (IA e integrantes)

## Enunciado

Chat multiusuário com sockets, cliente-servidor, threads, interface web e tolerância a falhas.

## Onde está cada requisito

| Requisito | Arquivo |
|-----------|---------|
| Sockets TCP | `common/protocol.py`, `server/session.py`, `client/socket_bridge.py` |
| Thread por conexão (servidor) | `ClientSession` em `server/session.py` |
| Thread recv (cliente) | `SocketBridge._recv_loop` em `client/socket_bridge.py` |
| HTTP embutido no cliente | `client/app.py` |
| Navegador sem instalar | React + deploy Fly.io |
| Failover | 2 VMs Fly + Upstash Redis + reconexão SSE/histórico |
| Sem WebSocket no transporte real | Browser: HTTP + SSE; backend: TCP |

## Documentação para humanos

- [docs/GLOSSARIO.md](docs/GLOSSARIO.md)
- [docs/ARQUITETURA.md](docs/ARQUITETURA.md)
- [docs/APRESENTACAO.md](docs/APRESENTACAO.md)
- [docs/MAPA_CODIGO.md](docs/MAPA_CODIGO.md)
- [docs/DEPLOY.md](docs/DEPLOY.md)
- [docs/API.md](docs/API.md)

## Produção vs local

| Modo | Comando |
|------|---------|
| Fly / Docker | `python -m stack` |
| PC do desenvolvedor | `LOCAL_run.ps1` + `LOCAL_front.ps1` |

## Checklist de avaliação

- [ ] URL pública Fly (não localhost na demo)
- [ ] Múltiplos usuários (2 abas)
- [ ] Username + histórico
- [ ] Explicar threads e sockets TCP
- [ ] Demo failover: `fly machine stop`
- [ ] `requirements.txt` + README + relatório PDF
