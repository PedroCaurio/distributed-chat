# Guia rápido do repositório (IA e integrantes)

## Enunciado

Chat multiusuário com sockets, cliente-servidor, threads, interface web e tolerância a falhas.

## Onde está cada requisito

| Requisito | Arquivo |
|-----------|---------|
| Sockets TCP | `protocol.py`, `server.py`, `proxy.py` |
| Thread por conexão (servidor) | `ClientSession` em `server.py` |
| Thread recv (cliente/proxy) | `TCPSession._recv_loop` em `proxy.py` |
| HTTP embutido no cliente | `proxy.py` + `index.html` |
| Navegador sem instalar | `index.html` servido pelo proxy |
| Failover | 2 VMs Fly + Upstash Redis + `affinity.py` |
| Sem WebSocket no transporte | Browser: HTTP + SSE; backend: TCP |

## Documentação

- [docs/GLOSSARIO.md](docs/GLOSSARIO.md)
- [docs/ARQUITETURA.md](docs/ARQUITETURA.md)
- [docs/APRESENTACAO.md](docs/APRESENTACAO.md)
- [docs/MAPA_CODIGO.md](docs/MAPA_CODIGO.md)
- [docs/DEPLOY.md](docs/DEPLOY.md)
- [docs/API.md](docs/API.md)
- [docs/AVALIACAO_ENUNCIADO.md](docs/AVALIACAO_ENUNCIADO.md)

## Produção vs local

| Modo | Comando |
|------|---------|
| Fly / Docker | `python stack.py` |
| PC do desenvolvedor | `LOCAL_run.ps1` |

## URL pública

https://chatnet-v2.fly.dev/
