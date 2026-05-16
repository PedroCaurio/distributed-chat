# Deploy 100% gratuito (US$ 0)

Custo estimado com as opções abaixo:

| Serviço | Plano | Custo |
| --- | --- | --- |
| **Upstash** Redis | Free | $0 |
| **Fly.io** (recomendado, 2 instâncias) | Free allowance | $0* |
| **Render** (alternativa, 1 instância) | Free | $0 |

\* Fly pode pedir cartão para verificação, mas não cobra se você ficar dentro do [free allowance](https://fly.io/docs/about/pricing/) (3× `shared-cpu-1x`, 256MB).

> **Por que não Render com 2 instâncias?** O plano **Starter** (~US$ 7/mês) é o mínimo para `numInstances: 2`. O plano **Free** só permite **1** instância.

---

## Opção A — Fly.io + Upstash (recomendado para a banca)

Atende: URL pública, **2 máquinas**, load balancer, failover, zero instalação no PC.

### 1. Upstash

1. [console.upstash.com](https://console.upstash.com) → banco Redis → copie `REDIS_URL` (`rediss://...`).

### 2. Instalar Fly CLI

```powershell
powershell -Command "iwr https://fly.io/install.ps1 -useb | iex"
fly auth login
```

### 3. Criar app (na raiz do repo)

```powershell
cd c:\Users\pedro\OneDrive\Documentos\Faculdade\distributed-chat
fly launch --no-deploy --copy-config --name distributed-chat-SEUNOME --region gru
```

- Confirme `Dockerfile` e `fly.toml`.
- **Não** crie Postgres/Redis no Fly.

### 4. Segredo Redis

```powershell
fly secrets set REDIS_URL="rediss://default:TOKEN@HOST.upstash.io:6379"
```

### 5. Deploy

```powershell
fly deploy
```

### 6. Duas instâncias (load balancer — gratuito dentro do allowance)

```powershell
fly scale count 2
fly status
```

Deve listar **2 machines**.

### 7. URL pública

```powershell
fly open
```

Ou: `https://distributed-chat-SEUNOME.fly.dev`

Abra no celular/PC da sala — **sem instalar nada**.

### 8. Manter acordado (opcional)

[UptimeRobot](https://uptimerobot.com) → monitor HTTP a cada 5 min em `https://SEU_APP.fly.dev/health`.

### 9. Demo failover (professor)

1. Duas abas, usuários diferentes, troque mensagens.
2. `fly machines list` → anote IDs.
3. Pare **uma** máquina: `fly machine stop <ID>`.
4. Chat reconecta na outra; banner “Conexão restabelecida”.
5. Suba de novo: `fly machine start <ID>`.

---

## Opção B — Render Free + Upstash (US$ 0, 1 instância)

Mais simples no painel, mas **só 1 instância** — o failover é “reiniciar o serviço” (mesmo efeito de reconexão SSE, sem LB entre duas VMs).

### 1. Apagar serviço Starter pago (se criou)

Render Dashboard → serviço → **Settings** → **Delete** (evita cobrança).

### 2. Blueprint com plano free

O `render.yaml` do repo já usa:

```yaml
plan: free
numInstances: 1
```

1. **New +** → **Blueprint** → repo GitHub.
2. **Environment** → `REDIS_URL` = URL Upstash.
3. Deploy → URL `https://....onrender.com`.

### 3. Limitações do free Render

- **1 instância** apenas.
- Serviço **hiberna** após ~15 min sem tráfego (primeiro acesso demora ~1 min).
- Use UptimeRobot em `/health` para reduzir hibernação.

### 4. Demo failover (1 instância)

**Manual Deploy** ou **Restart** no painel → usuários reconectam via SSE + Redis; não há segunda VM para derrubar.

No relatório: *“Plano gratuito Render: 1 réplica; alta disponibilidade com 2 réplicas demonstrada no Fly.io (free tier).”*

---

## Comparativo rápido

| | Fly.io free | Render free |
| --- | --- | --- |
| Custo | $0 | $0 |
| Instâncias | 2+ (`fly scale count 2`) | 1 |
| Derrubar 1 de 2 na demo | Sim | Não (só restart) |
| Hibernação | Pode parar VMs ociosas | Hiberna o web service |
| Cartão | Pode exigir | Não no free |

---

## Desenvolvimento local

```powershell
$env:PORT="8080"
$env:REDIS_URL="rediss://..."
$env:PYTHONPATH=(Get-Location).Path
python -m server
```

```bash
cd frontend && npm run dev
```

`frontend/.env`: `VITE_API_URL=/api` (proxy Vite → 8080).
