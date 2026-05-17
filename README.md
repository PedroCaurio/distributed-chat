# distributed-chat

Chat multiusuário para a disciplina de redes: **sockets TCP**, **threads**, interface **web** e hospedagem **online** (Fly.io).

**App em produção:** [https://distributed-chat-teste.fly.dev/](https://distributed-chat-teste.fly.dev/)

## Comece por aqui (grupo)

| Documento | Conteúdo |
|-----------|----------|
| [docs/GLOSSARIO.md](docs/GLOSSARIO.md) | Explica socket, thread, HTTP, Redis, Docker, Fly… |
| [docs/ARQUITETURA.md](docs/ARQUITETURA.md) | Como as peças se conectam |
| [docs/MAPA_CODIGO.md](docs/MAPA_CODIGO.md) | Onde está cada requisito do enunciado |
| [docs/APRESENTACAO.md](docs/APRESENTACAO.md) | Roteiro da apresentação presencial |
| [docs/DEPLOY.md](docs/DEPLOY.md) | Publicar no Fly.io |
| [docs/API.md](docs/API.md) | Rotas HTTP e mensagens TCP |

## Demonstração em aula

1. Abra [https://distributed-chat-teste.fly.dev/](https://distributed-chat-teste.fly.dev/)
2. Cada pessoa escolhe um **username** e conversa na sala global.
3. Nada para instalar nos computadores — só o navegador.

Failover (opcional): pare uma máquina com `fly machine stop` — ver [docs/DEPLOY.md](docs/DEPLOY.md).

## Requisitos do enunciado × implementação

| Requisito | Onde no código |
|-----------|----------------|
| Vários usuários em tempo real | Sala global via servidor |
| Thread por conexão no servidor | `server/session.py` |
| Thread recv no cliente | `client/socket_bridge.py` |
| Navegador + HTTP embutido | `client/app.py` + `frontend/` |
| Tolerância a falhas | 2 VMs Fly + Redis Upstash |
| Sockets (sem WebSocket no transporte real) | TCP + NDJSON em `common/protocol.py` |

## Estrutura do repositório

```text
distributed-chat/
├── client/          # HTTP para o browser + TCP para o servidor
├── server/          # Servidor de chat TCP + Redis
├── stack/           # Produção: python -m stack
├── frontend/        # React
├── common/          # Protocolo das mensagens
├── docs/            # Documentação do grupo
├── LOCAL_run.ps1    # Só para testar no seu PC
├── LOCAL_front.ps1
├── Dockerfile
└── fly.toml
```

## Deploy resumido

```powershell
fly auth login
fly secrets set REDIS_URL="rediss://..."
fly deploy
fly scale count 2
fly open
```

O app deste repositório já está configurado como `distributed-chat-teste` no `fly.toml`.

Detalhes: [docs/DEPLOY.md](docs/DEPLOY.md).

## Logs para a apresentação

| Onde | Como ativar | O que ver |
|------|-------------|-----------|
| Navegador | `VITE_DEMO_LOGS=true` em `frontend/.env` | F12 → Console, prefixo `[DEMO][navegador]` |
| Python | `DEMO_LOGS=1` no `.env` ou `fly secrets set DEMO_LOGS=1` | Terminal / `fly logs` — blocos `[DEMO]` e `[TRACE]` em linhas curtas |

Detalhes: [docs/APRESENTACAO.md](docs/APRESENTACAO.md) (seção 3).

## Testar no seu computador

Arquivos **`LOCAL_*`** são apenas para desenvolvimento local:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
# Edite REDIS_URL

.\LOCAL_run.ps1
# Outro terminal:
.\LOCAL_front.ps1
```

Testes:

```powershell
$env:PYTHONPATH = (Get-Location).Path
python -m pytest -q
```

## Entrega AVA

Inclua no `.zip`: código-fonte, `requirements.txt`, este `README.md` e o **relatório em PDF** (estrutura no enunciado da disciplina).
