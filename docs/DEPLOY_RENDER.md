# Deploy no Render (100% web, 2 instâncias)

Guia para demonstração em aula **sem instalar nada** no PC — apenas abrir a URL pública.

## Pré-requisitos

- Repositório no GitHub
- Conta [Render](https://render.com)
- URL Redis do **Upstash** (`rediss://...`)

## Passo 1 — Blueprint no Render

1. Acesse [dashboard.render.com](https://dashboard.render.com).
2. **New +** → **Blueprint**.
3. Conecte o repositório `distributed-chat`.
4. O Render lê `render.yaml` e cria o Web Service `distributed-chat` com **`numInstances: 2`** (load balancer HTTP automático).

## Passo 2 — Variável secreta

No serviço criado → **Environment**:

| Chave | Valor |
| --- | --- |
| `REDIS_URL` | Cole a URL completa do Upstash |
| `ENABLE_TCP_SERVER` | `false` (já no blueprint) |

Salve. O Render fará um novo deploy.

## Passo 3 — Aguardar build

O `Dockerfile` na raiz:

1. Compila o front (`npm run build`)
2. Copia `frontend/dist` para a imagem Python
3. Sobe FastAPI na porta `PORT` (Render injeta, ex. `10000`)

Logs devem mostrar: `HTTP escutando na porta 10000`.

## Passo 4 — URL pública

Após deploy:

```text
https://distributed-chat.onrender.com
```

(ou o nome que você definiu)

Abra no navegador da sala de aula — login e chat funcionam na mesma URL.

## Passo 5 — Load balancer (2 instâncias)

1. Serviço → **Scaling** → confirme **2 instances**.
2. Cada instância aparece em **Events** / **Metrics**.

Documentação: https://render.com/docs/scaling

## Passo 6 — Demonstração de failover

1. Dois alunos (ou duas abas anônimas) entram com usernames diferentes.
2. No painel Render → **Manual Deploy** ou **Restart** em **uma** instância (ou reduza para 1 e volte para 2).
3. Usuários podem ver breve pausa; em seguida banner **“Conexão restabelecida”** e mensagens continuam (histórico no Redis + SSE reconecta).

## Health check

Render usa `healthCheckPath: /health` do `render.yaml`.

Teste manual: `https://SEU_APP.onrender.com/health`

## Desenvolvimento local

```powershell
$env:PORT="10000"
$env:REDIS_URL="rediss://..."
$env:PYTHONPATH=(Get-Location).Path
python -m server
```

Front em dev:

```bash
cd frontend
npm run dev
# VITE_API_URL=/api no .env → proxy para :10000
```

## Plano Render

O blueprint usa `plan: starter` (necessário para múltiplas instâncias estáveis). Ajuste no `render.yaml` se usar free tier (pode limitar 2 instâncias).

## Relatório técnico

Explique:

- Estado centralizado no Upstash
- Duas réplicas stateless no Render
- LB HTTP do Render
- Sessões em Redis + reconexão SSE = tolerância a falha imperceptível ao usuário
