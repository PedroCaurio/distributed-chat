# Guia rápido do repositório (IA e integrantes)

## Enunciado

Chat multiusuário com sockets, cliente-servidor, threads, interface web e tolerância a falhas.

## Onde está cada requisito

| Requisito | Arquivo |
|-----------|---------|
| Sockets TCP | `src/chatnet/protocol.py`, `server.py`, `proxy.py` |
| Thread por conexão (servidor) | `src/chatnet/server.py` → `ClientSession` |
| Thread recv (cliente/proxy) | `src/chatnet/proxy.py` → `TCPSession._recv_loop` |
| HTTP embutido no cliente | `src/chatnet/proxy.py` |
| Interface web | `src/chatnet/static/index.html` |
| Failover | 2 VMs Fly + Redis + `src/chatnet/affinity.py` |

## Documentação

- [docs/GLOSSARIO.md](docs/GLOSSARIO.md)
- [docs/ARQUITETURA.md](docs/ARQUITETURA.md)
- [docs/APRESENTACAO.md](docs/APRESENTACAO.md)
- [docs/MAPA_CODIGO.md](docs/MAPA_CODIGO.md)
- [docs/DEPLOY.md](docs/DEPLOY.md)
- [docs/API.md](docs/API.md)

## Produção vs local

| Modo | Comando |
|------|---------|
| Fly / Docker | `python -m chatnet` |
| PC do desenvolvedor | `.\LOCAL_run.ps1` ou `python stack.py` |

## URL pública

https://chatnet-v2.fly.dev/
