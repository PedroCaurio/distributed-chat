# distributed-chat

Chat multiusuário **100% web** para apresentação em aula: React + FastAPI no **Render** (2 instâncias + load balancer), estado no **Redis (Upstash)**, failover com reconexão SSE transparente.

## Demonstração (professor / alunos)

1. Abra a URL do deploy (ex.: `https://distributed-chat.onrender.com`).
2. Informe um username e converse na sala global.
3. **Nenhuma instalação** (Python, proxy, npm) é necessária na máquina do aluno.

## Estrutura

```text
distributed-chat/
├── frontend/     # React (build embutido no Docker)
├── server/       # API HTTP + SSE + TCP opcional
├── common/       # Protocolo NDJSON (TCP legado)
├── client/       # Proxy local (opcional, dev/acadêmico)
├── Dockerfile    # Build front + API
├── render.yaml   # 2 instâncias Render
└── docs/
```

## Deploy rápido (Render + Upstash)

1. Push no GitHub.
2. Render → **Blueprint** → repo → definir `REDIS_URL` (Upstash).
3. Aguardar build → abrir URL pública.

Detalhes: [docs/DEPLOY_RENDER.md](docs/DEPLOY_RENDER.md)

## Desenvolvimento local

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
# .env com REDIS_URL e PORT=10000
$env:PYTHONPATH = (Get-Location).Path
python -m server
```

```bash
cd frontend && npm install && npm run dev
```

Use `frontend/.env` com `VITE_API_URL=/api` (proxy Vite → porta 10000).

## Testes

```powershell
$env:PYTHONPATH = (Get-Location).Path
python -m pytest -q
```

## Documentação

- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- [docs/PAYLOADS.md](docs/PAYLOADS.md)
- [docs/DEPLOY_RENDER.md](docs/DEPLOY_RENDER.md)

## Requisitos acadêmicos

| Requisito | Como é atendido |
| --- | --- |
| Navegador, sem instalar | SPA na URL pública Render |
| Servidor online | Render Web Service |
| Thread por conexão | TCP opcional: 1 thread/cliente; SSE: recepção bloqueante por conexão |
| Tolerância a falhas | 2 instâncias + Redis + reconexão SSE |
| Histórico | Redis `chat:history` |
