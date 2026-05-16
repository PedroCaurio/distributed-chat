# Deploy no Fly.io (gratuito)

Stack: **Fly.io** (app Docker com React + API) + **Upstash** (Redis).  
Custo operacional: **US$ 0** dentro do [free allowance](https://fly.io/docs/about/pricing/) do Fly.

## Pré-requisitos

- Conta [fly.io](https://fly.io)
- URL Redis do [Upstash](https://console.upstash.com) (`rediss://...`)
- Repositório no GitHub (opcional; deploy via CLI na pasta do projeto)
- [Fly CLI](https://fly.io/docs/flyctl/install/):

```powershell
powershell -Command "iwr https://fly.io/install.ps1 -useb | iex"
fly auth login
```

## Primeiro deploy

Na raiz do repositório:

```powershell
cd c:\Users\pedro\OneDrive\Documentos\Faculdade\distributed-chat
fly launch --no-deploy --copy-config --name distributed-chat-SEUNOME --region gru
```

- Confirme `Dockerfile` e `fly.toml`.
- **Não** crie Postgres/Redis no Fly (use Upstash).

```powershell
fly secrets set REDIS_URL="rediss://default:TOKEN@HOST.upstash.io:6379"
fly deploy --no-cache
```

> Use `--no-cache` se o build do front falhar por cache antigo do Docker.

## Duas instâncias (load balancer + demo de failover)

```powershell
fly scale count 2
fly status
```

## URL pública

```powershell
fly open
```

Exemplo: `https://distributed-chat-SEUNOME.fly.dev`

Teste: `https://SEU_APP.fly.dev/health` → `{"status":"ok",...}`

## Uso em aula (zero instalação)

1. Compartilhe a URL `https://....fly.dev`.
2. Cada pessoa abre no navegador, faz login e conversa.
3. **Não** é necessário `python -m client`, proxy local nem `npm run dev`.

### Dois usuários

| Contexto | Username |
|----------|----------|
| Aba 1 | `pedro` |
| Aba anônima / outro navegador | `maria` |

### Demo: professor derruba uma instância

```powershell
fly machines list
fly machine stop <ID>
```

Usuários veem reconexão automática e banner *“Conexão restabelecida”*.

```powershell
fly machine start <ID>
```

## Cold start (free tier)

VMs podem parar quando ociosas. Antes da aula, abra a URL ou configure [UptimeRobot](https://uptimerobot.com) em `/health` (5 min).

## Atualizar após mudanças no código

```powershell
git pull
fly deploy
```

## Variáveis (Fly secrets / fly.toml)

| Variável | Obrigatório | Descrição |
|----------|-------------|-----------|
| `REDIS_URL` | Sim (secret) | URL Upstash |
| `ENABLE_TCP_SERVER` | Não | `false` no Fly (`fly.toml`) |
| `PORT` | Automático | `8080` (HTTP interno) |

## Desenvolvimento local

```powershell
$env:PORT="8080"
$env:REDIS_URL="rediss://..."
$env:PYTHONPATH=(Get-Location).Path
python -m server
```

```bash
cd frontend && npm install && npm run dev
```

`frontend/.env`: `VITE_API_URL=/api` (proxy Vite → `:8080`).

## Problemas comuns

| Sintoma | Solução |
|---------|---------|
| Build: `sessionStorage` não encontrado | `fly deploy --no-cache`; confira `frontend/src/lib/sessionStorage.ts` |
| Build: mesmo erro após criar arquivo | `.dockerignore` não pode ter `**/lib` genérico |
| Login falha | `fly secrets list`; teste `REDIS_URL` no Upstash |
| `username já está em uso` | Console Upstash: `DEL chat:user:NOME` |
| App lento ao abrir | Cold start; aguarde ou UptimeRobot |
