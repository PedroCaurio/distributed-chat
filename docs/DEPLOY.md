# Deploy no Fly.io

Stack: **cliente HTTP** (público) + **servidor TCP** (interno) + **Upstash Redis**.

## Pré-requisitos

- Conta [fly.io](https://fly.io)
- URL Redis [Upstash](https://console.upstash.com) (`rediss://...`)
- [Fly CLI](https://fly.io/docs/flyctl/install/):

```powershell
powershell -Command "iwr https://fly.io/install.ps1 -useb | iex"
fly auth login
```

## Primeiro deploy

```powershell
cd c:\Users\pedro\OneDrive\Documentos\Faculdade\distributed-chat
fly launch --no-deploy --copy-config --name distributed-chat-SEUNOME --region gru
fly secrets set REDIS_URL="rediss://default:TOKEN@HOST.upstash.io:6379"
fly deploy --no-cache
fly scale count 2
fly open
```

URL: `https://distributed-chat-SEUNOME.fly.dev`

Teste: `https://SEU_APP.fly.dev/health` → `{"status":"ok","role":"client",...}`

## Uso em aula

1. Compartilhe a URL `https://....fly.dev`.
2. Cada pessoa abre no navegador, faz login e conversa.
3. **Não** é necessário instalar Python nem Node nos PCs dos alunos.

### Demo failover

```powershell
fly machines list
fly machine stop <ID>
```

Usuários veem reconexão e banner *“Conexão restabelecida”*.

## Variáveis

| Variável | Onde | Descrição |
|----------|------|-----------|
| `REDIS_URL` | secret | Upstash |
| `PORT` | 8080 | HTTP do **cliente** (público) |
| `CHAT_SERVER_PORT` | 9000 | TCP do **servidor** (interno) |
| `CHAT_SERVER_HOST` | 127.0.0.1 | Servidor no mesmo container |

## Desenvolvimento local

```powershell
$env:PYTHONPATH = (Get-Location).Path
# .env com REDIS_URL
python -m stack
```

```bash
cd frontend && npm run dev
```

`frontend/.env`: `VITE_API_URL=/api`

## Problemas comuns

| Sintoma | Solução |
|---------|---------|
| Login falha / 503 | Verifique `REDIS_URL`; servidor TCP precisa do Redis |
| Mensagens somem / não aparecem | Com 2 VMs, faça redeploy após correção de afinidade; limpe cookies do site |
| `username já está em uso` | `DEL chat:user:NOME` no console Upstash |
| Cold start lento | Abra `/health` antes da aula ou UptimeRobot |
| Build front falha | `fly deploy --no-cache` |
