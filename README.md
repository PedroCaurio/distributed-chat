# distributed-chat

Chat multiusuário com **arquitetura cliente-servidor**, **sockets TCP nativos**, **threads** e interface **web** (zero instalação na demonstração).

## Arquitetura (enunciado)

```text
Navegador ──HTTP/SSE──► client/ (servidor HTTP embutido + thread recv TCP)
                              │
                              ▼ sockets
                         server/ (1 thread por conexão TCP)
                              │
                              ▼
                         Redis (histórico, sessões, pub/sub)
                              │
                    2 instâncias Fly (failover)
```

| Requisito | Implementação |
|-----------|----------------|
| Múltiplos usuários | Sala global; mensagens via servidor |
| Thread por conexão no servidor | `server/session.py` → `ClientSession(threading.Thread)` |
| Thread de recv no cliente | `client/socket_bridge.py` → `_recv_loop` por usuário |
| Navegador + HTTP embutido no cliente | `client/app.py` (FastAPI) + React em `frontend/` |
| Tolerância a falhas | `fly scale count 2` + Redis + reconexão SSE |
| Sockets (sem WebSocket) | NDJSON sobre TCP (`common/protocol.py`) |

## Demonstração em aula

1. Abra `https://SEU_APP.fly.dev` (após deploy).
2. Login com username → converse na sala global.
3. **Nada para instalar** nos PCs dos alunos.

## Deploy

Guia completo: **[docs/DEPLOY.md](docs/DEPLOY.md)**

```powershell
fly auth login
fly launch --no-deploy --copy-config --name distributed-chat-SEUNOME --region gru
fly secrets set REDIS_URL="rediss://..."
fly deploy
fly scale count 2
fly open
```

## Estrutura

```text
distributed-chat/
├── client/          # Cliente: HTTP para o browser + TCP para o servidor
├── server/          # Servidor de chat TCP + Redis
├── stack/           # Entrypoint produção (ambos os processos)
├── frontend/        # React (build → servido pelo client)
├── common/          # Protocolo NDJSON/TCP
├── docs/
├── Dockerfile
└── fly.toml
```

## Desenvolvimento local

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
# Edite REDIS_URL no .env

$env:PYTHONPATH = (Get-Location).Path
python -m stack
```

Outro terminal:

```bash
cd frontend && npm install && npm run dev
```

`frontend/.env`: `VITE_API_URL=/api`

## Testes

```powershell
$env:PYTHONPATH = (Get-Location).Path
python -m pytest -q
```

## Documentação

| Arquivo | Conteúdo |
| --- | --- |
| [docs/DEPLOY.md](docs/DEPLOY.md) | Deploy Fly.io |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Arquitetura detalhada |
| [docs/PAYLOADS.md](docs/PAYLOADS.md) | API HTTP do cliente + frames TCP |

## Entrega AVA

Inclua no `.zip`: código-fonte, `requirements.txt`, este `README.md` e o **relatório em PDF**.
