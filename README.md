# distributed-chat

Chat multiusuário com **TCP nativo + threads**, **Redis** (estado e pub/sub), **proxy HTTP local** e **front-end React**.

## Estrutura do repositório

```text
distributed-chat/
├── common/          # Protocolo NDJSON compartilhado
├── server/          # Servidor de chat TCP (deploy remoto)
├── client/          # Proxy local (FastAPI + SSE + socket)
├── frontend/        # UI React (Vite)
├── docs/            # Arquitetura, payloads, deploy
├── requirements.txt # Dependências Python
└── Dockerfile.server
```

## Requisitos

- Python 3.11+
- Node.js 20+ (front-end)
- Redis (Upstash, Docker local, etc.)

## Instalação Python

```bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1   # Windows
pip install -r requirements.txt
Copy-Item .env.example .env    # edite REDIS_URL e hosts
```

## Instalação front-end

```bash
cd frontend
npm install
```

## Execução (desenvolvimento local)

**Terminal 1 — servidor**

```powershell
$env:PYTHONPATH = (Get-Location).Path
python -m server
```

**Terminal 2 — proxy**

```powershell
$env:PYTHONPATH = (Get-Location).Path
python -m client
```

**Terminal 3 — front-end**

```bash
cd frontend
npm run dev
```

Abra `http://localhost:5173`, faça login e converse na **Sala global**.

## Testes automatizados

```powershell
$env:PYTHONPATH = (Get-Location).Path
python -m pytest -q
```

## Documentação

| Arquivo | Conteúdo |
| --- | --- |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Fluxo React → proxy → servidor → Redis |
| [docs/PAYLOADS.md](docs/PAYLOADS.md) | Contratos JSON (TCP e HTTP) |
| [docs/DEPLOY_RENDER.md](docs/DEPLOY_RENDER.md) | Deploy servidor + load balancer |
| [frontend/README.md](frontend/README.md) | Detalhes do front-end |

## Fluxo de integração

1. O React chama `POST /login` e `POST /messages` no proxy.
2. O proxy traduz para frames TCP (`login`, `message`).
3. O servidor persiste histórico no Redis e publica eventos em pub/sub.
4. O proxy recebe eventos na thread de `recv` e repassa via `GET /events` (SSE).
5. O React atualiza a lista de mensagens em tempo real.
