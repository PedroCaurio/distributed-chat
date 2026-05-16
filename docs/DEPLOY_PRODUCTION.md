# Deploy em produção (ambiente real / banca)

Este guia cobre o cenário que o professor costuma pedir:

- Servidor **fora do localhost** (internet).
- **Duas instâncias** com **balanceamento** e tolerância a falhas.
- **Redis** compartilhado (estado + pub/sub).
- Teste na sua máquina com **dois usuários** (dois proxies + front).

## Visão geral da divisão de papéis

| Componente | Onde hospedar | Por quê |
| --- | --- | --- |
| Redis | **Upstash** (já usa) ou **Render Key Value** | Estado entre instâncias |
| Servidor TCP (`server/`) | **Fly.io** — 2 máquinas + LB | Render **não** expõe socket TCP bruto na internet |
| Proxy (`client/`) | **Seu PC** | Requisito acadêmico (thread `recv` + HTTP local) |
| Front (`frontend/`) | **Seu PC** (`npm run dev`) ou Vercel | UI no navegador |

> No relatório, escreva: *“Redis no Render/Upstash; duas réplicas do servidor TCP no Fly.io com balanceamento do Fly Proxy; Render Scaling documentado para serviços HTTP.”*

---

## Parte 0 — GitHub

### 0.1 Repositório

```powershell
cd c:\Users\pedro\OneDrive\Documentos\Faculdade\distributed-chat
git add .
git commit -m "feat: integração frontend e configs de deploy"
git branch -M main
git remote add origin https://github.com/SEU_USUARIO/distributed-chat.git
git push -u origin main
```

### 0.2 O que o professor verá no GitHub

- `Dockerfile.server` — build do servidor
- `fly.toml` — 2 instâncias TCP + porta 9000
- `render.yaml` — Redis opcional no Render
- `docs/DEPLOY_PRODUCTION.md` — este arquivo

Não commite `.env` (já está no `.gitignore`).

---

## Parte 1 — Redis (Upstash ou Render)

### Opção A — Upstash (recomendado se já configurou)

1. Painel Upstash → seu banco → **Redis Connect**.
2. Copie a URL `rediss://default:TOKEN@HOST:6379`.
3. Use em todos os deploys como `REDIS_URL`.

### Opção B — Render Key Value + GitHub

1. [dashboard.render.com](https://dashboard.render.com) → **New +** → **Blueprint**.
2. Conecte o repositório GitHub `distributed-chat`.
3. O Render lê `render.yaml` e cria o Key Value.
4. Em **Connect** / **Internal Redis URL**, copie a URL para `REDIS_URL`.

**Importante:** se o Redis for só interno ao Render, instâncias no **Fly.io** precisam de Redis **público** (Upstash) ou liberar IP no allowlist. Por isso **Upstash é mais simples** para Fly + PC local.

---

## Parte 2 — Por que o TCP não vai em “2 Web Services” no Render

O Render balanceia tráfego **entrante** em Web Services e Private Services, mas:

- **Web Service** público = **HTTP(S)** no hostname `*.onrender.com`, porta esperada pelo painel (ex.: `10000`).
- O chat usa **TCP bruto na porta 9000** (sockets nativos, sem WebSocket).

Conclusão: as **duas instâncias do servidor de chat** com load balancer funcional para o seu proxy local devem ficar no **Fly.io** (ou VPS/Railway com TCP). O Render entra como **Redis** e, se quiser, hospedagem do front estático.

Documentação Render sobre scaling (útil no relatório):  
https://render.com/docs/scaling

---

## Parte 3 — Deploy das 2 instâncias TCP no Fly.io (load balancer)

### 3.1 Instalar CLI

Windows (PowerShell):

```powershell
powershell -Command "iwr https://fly.io/install.ps1 -useb | iex"
```

Feche e abra o terminal. Login:

```powershell
fly auth login
```

### 3.2 Criar app (primeira vez)

Na raiz do repositório:

```powershell
cd c:\Users\pedro\OneDrive\Documentos\Faculdade\distributed-chat
fly launch --no-deploy --name distributed-chat --region gru --copy-config
```

- Confirme uso do `Dockerfile.server`.
- Não crie Postgres/Redis no Fly se já usa Upstash.

### 3.3 Segredos (Redis)

```powershell
fly secrets set REDIS_URL="rediss://default:SUA_SENHA@SEU_HOST.upstash.io:6379"
```

### 3.4 Build e deploy

```powershell
fly deploy
```

### 3.5 Duas instâncias + load balancer

```powershell
fly scale count 2
fly status
```

O **Fly Proxy** distribui novas conexões TCP entre as máquinas (menor carga / menor latência). Com **Redis pub/sub**, mensagens entre usuários em réplicas diferentes ainda chegam a todos.

### 3.6 Host e porta para o `.env` local

```powershell
fly info
```

Anote o hostname (ex.: `distributed-chat.fly.dev`). No `.env` da raiz:

```env
CHAT_SERVER_HOST=distributed-chat.fly.dev
CHAT_SERVER_PORT=9000
```

Teste TCP (opcional):

```powershell
Test-NetConnection distributed-chat.fly.dev -Port 9000
```

---

## Parte 4 — Render: o que configurar na prática

Mesmo sem TCP no Render, você pode demonstrar conhecimento do painel:

### 4.1 Conectar GitHub ao Render

1. **Account Settings** → **GitHub** → autorize o repositório.
2. **New** → **Blueprint** → selecione `distributed-chat` (Redis via `render.yaml`).

### 4.2 “Duas instâncias” no relatório (conceito Render)

Para um **Web Service** HTTP (ex.: futuro painel admin):

1. Abra o serviço → **Scaling**.
2. **Manual Scaling** → arraste para **2 instances** → **Save**.

Isso ativa o load balancer HTTP do Render. No seu projeto, o equivalente operacional para o chat TCP é `fly scale count 2`.

### 4.3 UptimeRobot (manter acordado)

1. [uptimerobot.com](https://uptimerobot.com) → monitor **TCP** ou **Ping** para `distributed-chat.fly.dev:9000` (ou HTTP se adicionar health depois).
2. Intervalo 5 min no plano gratuito.

---

## Parte 5 — Teste completo no seu PC (2 usuários)

### 5.1 `.env` na raiz

```env
REDIS_URL=rediss://...upstash...

CHAT_SERVER_HOST=distributed-chat.fly.dev
CHAT_SERVER_PORT=9000

PROXY_HTTP_HOST=127.0.0.1
PROXY_HTTP_PORT=5000
```

### 5.2 Terminal 1 — proxy usuário A

```powershell
cd c:\Users\pedro\OneDrive\Documentos\Faculdade\distributed-chat
.\.venv\Scripts\Activate.ps1
$env:PYTHONPATH = (Get-Location).Path
$env:PROXY_HTTP_PORT = "5000"
python -m client
```

### 5.3 Terminal 2 — proxy usuário B

```powershell
$env:PYTHONPATH = (Get-Location).Path
$env:PROXY_HTTP_PORT = "5001"
python -m client
```

### 5.4 Terminal 3 — front usuário A

```powershell
cd frontend
npm run dev
```

Abra http://localhost:5173 → login `pedro`.

### 5.5 Terminal 4 — front usuário B

Crie `frontend/.env`:

```env
VITE_PROXY_URL=http://127.0.0.1:5001
```

```powershell
npm run dev -- --port 5174
```

Abra http://localhost:5174 → login `maria`.

Envie mensagens em uma aba; a outra deve atualizar em tempo real (SSE).

---

## Parte 6 — Checklist para a apresentação

- [ ] `fly scale count 2` e `fly status` mostrando 2 machines
- [ ] `REDIS_URL` igual nas duas (Upstash/Render)
- [ ] Mensagem de A chega em B com instâncias no Fly
- [ ] Relatório explica: Render (Redis / scaling HTTP) + Fly (TCP + LB)
- [ ] Repositório GitHub público ou acessível ao professor

---

## Falhas comuns

| Sintoma | Causa | Ação |
| --- | --- | --- |
| Proxy timeout | `CHAT_SERVER_HOST` ainda `127.0.0.1` ou placeholder | Use hostname Fly |
| `username já está em uso` | Redis com presença antiga | Upstash CLI / console: `DEL chat:online` |
| Segundo usuário não recebe | Só um proxy rodando | Portas 5000 e 5001 |
| Fly deploy falha Redis | URL errada / TLS | Use `rediss://` do painel |

---

## Comandos resumidos (cola rápida)

```powershell
# Fly — deploy 2 instâncias
fly secrets set REDIS_URL="rediss://..."
fly deploy
fly scale count 2
fly status

# Local — dois usuários
# Terminal A: PROXY_HTTP_PORT=5000 && python -m client
# Terminal B: PROXY_HTTP_PORT=5001 && python -m client
# frontend: npm run dev  (e segunda instância com VITE_PROXY_URL=http://127.0.0.1:5001)
```
