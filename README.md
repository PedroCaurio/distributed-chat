# distributed-chat

Chat multiusuário **100% web**, **US$ 0** na operação recomendada: **Fly.io** (2 instâncias) + **Upstash** (Redis free).

## Demonstração em aula

1. Abra a URL pública (ex.: `https://seu-app.fly.dev`).
2. Login com username → sala global.
3. **Nada para instalar.**

## Deploy gratuito (escolha uma)

| Opção | Custo | 2 instâncias / LB | Guia |
| --- | --- | --- | --- |
| **Fly.io + Upstash** | $0 | Sim | [docs/DEPLOY_FREE.md](docs/DEPLOY_FREE.md) |
| **Render + Upstash** | $0 | Não (só 1 instância) | [docs/DEPLOY_RENDER.md](docs/DEPLOY_RENDER.md) |

> Render **Starter** com 2 instâncias ≈ **US$ 7/mês**. O `render.yaml` do repo usa **plan: free** e **1 instância** para evitar isso.

## Estrutura

```text
distributed-chat/
├── frontend/     # React (embutido no Docker)
├── server/       # FastAPI + SSE + Redis
├── Dockerfile    # Build único (Fly ou Render)
├── fly.toml      # 2 VMs free (recomendado)
├── render.yaml   # 1 instância free (alternativa)
└── docs/
```

## Comandos rápidos (Fly — recomendado)

```powershell
fly auth login
fly launch --no-deploy --copy-config --name distributed-chat-SEUNOME --region gru
fly secrets set REDIS_URL="rediss://..."
fly deploy
fly scale count 2
fly open
```

## Desenvolvimento local

```powershell
pip install -r requirements.txt
$env:PORT="8080"; $env:REDIS_URL="rediss://..."; $env:PYTHONPATH=(Get-Location).Path
python -m server
```

```bash
cd frontend && npm run dev
```

## Documentação

- [docs/DEPLOY_FREE.md](docs/DEPLOY_FREE.md) — **principal, $0**
- [docs/DEPLOY_RENDER.md](docs/DEPLOY_RENDER.md) — Render free (1 instância)
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- [docs/PAYLOADS.md](docs/PAYLOADS.md)

## Testes

```powershell
python -m pytest -q
```
