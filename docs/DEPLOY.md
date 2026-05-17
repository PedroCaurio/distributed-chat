# Deploy no Fly.io

**URL de demonstração:** [https://chatnet-v2.fly.dev/](https://chatnet-v2.fly.dev/)

## Pré-requisitos

| Item | Uso |
|------|-----|
| [Fly.io](https://fly.io) | Hospedagem |
| [Upstash Redis](https://console.upstash.com) | Histórico + pub/sub entre VMs |
| [Fly CLI](https://fly.io/docs/flyctl/install/) | `fly deploy`, `fly secrets` |

```powershell
powershell -Command "iwr https://fly.io/install.ps1 -useb | iex"
fly auth login
```

## Atualizar o servidor (deploy)

Na **raiz do repositório** (onde estão `fly.toml` e `Dockerfile`):

```powershell
cd C:\Users\pedro\OneDrive\Documentos\Faculdade\distributed-chat

# 1. Secret do Redis (só se mudou ou primeira vez)
fly secrets set REDIS_URL="rediss://default:SEU_TOKEN@SEU_HOST.upstash.io:6379"

# 2. Build e publicação
fly deploy

# 3. Duas máquinas para failover do enunciado
fly scale count 2

# 4. Conferir
fly status
fly logs
fly open
```

Primeira vez no Fly:

```powershell
fly launch --no-deploy --copy-config --name chatnet-v2 --region gru
fly secrets set REDIS_URL="..."
fly deploy
fly scale count 2
```

Teste: [https://chatnet-v2.fly.dev/health](https://chatnet-v2.fly.dev/health) → `"status":"ok"`.

## O que o container executa

`Dockerfile` → `CMD ["python", "stack.py"]`:

- `server.py` — TCP na porta **9000** (interna)
- `proxy.py` — HTTP na porta **8080** (pública via Fly)

## Variáveis (`fly.toml` + secrets)

| Variável | Valor | Significado |
|----------|-------|-------------|
| `REDIS_URL` | secret | Upstash |
| `PORT` | 8080 | HTTP do proxy |
| `SERVER_PORT` | 9000 | TCP do chat |
| `SERVER_HOST` | 127.0.0.1 | Servidor no mesmo container |

## Demo de failover na aula

```powershell
fly machines list
fly machine stop <ID_DA_VM>
```

Usuários na VM parada: `POST /resume` automático no front; histórico via Redis.

## Problemas comuns

| Sintoma | Ação |
|---------|------|
| Login 503 | Verificar `REDIS_URL` com `fly secrets list` |
| Mensagens só no histórico | Hard refresh (`Ctrl+Shift+R`); redeploy recente |
| `username já em uso` | Limpar chaves `chat:*` no console Upstash |

## Local (não substitui URL pública)

```powershell
copy .env.example .env
.\LOCAL_run.ps1
```

Abra http://localhost:8080
