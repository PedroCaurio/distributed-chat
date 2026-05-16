# distributed-chat

Chat multiusuário **100% web** — **Fly.io** (2 instâncias) + **Upstash** (Redis), **US$ 0** no free tier.

## Demonstração em aula

1. Abra `https://SEU_APP.fly.dev` (após deploy).
2. Login com username → converse na sala global.
3. **Nada para instalar** no PC dos alunos.

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
├── frontend/       # React
├── server/         # FastAPI + SSE + Redis
├── common/         # Protocolo TCP (legado)
├── legacy/client/  # Proxy local (opcional, relatório)
├── Dockerfile
├── fly.toml
└── docs/
```

## Desenvolvimento local

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
# .env: REDIS_URL + PORT=8080
$env:PYTHONPATH = (Get-Location).Path
python -m server
```

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
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Arquitetura |
| [docs/PAYLOADS.md](docs/PAYLOADS.md) | API HTTP |

## Requisitos acadêmicos

| Requisito | Atendimento |
| --- | --- |
| Navegador, sem instalar | URL pública Fly |
| Servidor online | Fly.io |
| Threads | TCP opcional + pub/sub + SSE |
| Tolerância a falhas | 2 VMs + Redis + reconexão SSE |
| Histórico | Redis |
