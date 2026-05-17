# ChatNet v2 — Chat distribuído (FURG)

Chat multiusuário em tempo real com **sockets TCP**, **threads** e interface **web** (HTML + SSE). Hospedagem de demonstração: [https://chatnet-v2.fly.dev/](https://chatnet-v2.fly.dev/)

## Requisitos do enunciado (resumo)

| Item | Onde está |
|------|-----------|
| Socket TCP cliente ↔ servidor | `src/chatnet/protocol.py`, `proxy.py`, `server.py` |
| Thread por conexão no servidor | `src/chatnet/server.py` → `ClientSession` |
| Thread de recepção no cliente | `src/chatnet/proxy.py` → `TCPSession._recv_loop` |
| HTTP embutido para o navegador | `src/chatnet/proxy.py` + `static/index.html` |
| Tolerância a falhas (2 instâncias) | Fly.io + Redis (Upstash) |
| Histórico e apelidos | `src/chatnet/redis_backend.py`, `index.html` |

Detalhes: [docs/MAPA_CODIGO.md](docs/MAPA_CODIGO.md) · Avaliação: [docs/AVALIACAO_ENUNCIADO.md](docs/AVALIACAO_ENUNCIADO.md)

## Instalação

```bash
pip install -r requirements.txt
```

Redis (Docker local):

```bash
docker run -d -p 6379:6379 redis:7-alpine
```

## Execução local

```powershell
copy .env.example .env
# Edite REDIS_URL
.\LOCAL_run.ps1
# ou: $env:PYTHONPATH="src"; python -m chatnet
```

Abra [http://localhost:8080](http://localhost:8080).

## Deploy Fly.io

```powershell
fly auth login
fly secrets set REDIS_URL="rediss://default:TOKEN@HOST.upstash.io:6379"
fly deploy
fly scale count 2
fly open
```

Guia completo: [docs/DEPLOY.md](docs/DEPLOY.md)

## Testes

```powershell
python -m pytest -q
```

## Documentação

- [docs/GLOSSARIO.md](docs/GLOSSARIO.md) — termos (SSE, NDJSON, failover…)
- [docs/ARQUITETURA.md](docs/ARQUITETURA.md) — diagrama e fluxo
- [docs/API.md](docs/API.md) — rotas HTTP e frames TCP
- [docs/APRESENTACAO.md](docs/APRESENTACAO.md) — roteiro da demo oral
- [docs/DEPLOY.md](docs/DEPLOY.md) — Fly.io e failover

## Estrutura do repositório

```
src/chatnet/           # Código Python do chat
  protocol.py          # NDJSON sobre TCP
  server.py            # Servidor TCP (thread por conexão)
  proxy.py             # Proxy HTTP → TCP (thread recv + SSE)
  redis_backend.py     # Histórico, sessões, pub/sub
  affinity.py          # Afinidade entre VMs no Fly
  stack.py             # Sobe server + proxy
  static/index.html    # Interface web (sem npm)
stack.py               # Atalho: python stack.py (raiz)
tests/                 # pytest
docs/                  # Documentação
```

## Relatório PDF

O relatório técnico (AVA) é entregue em PDF à parte; use os arquivos em `docs/` como base.
