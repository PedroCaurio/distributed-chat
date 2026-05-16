# Deploy no Render

> **Custo zero:** use `plan: free` e `numInstances: 1` (já no `render.yaml`).
>
> **Duas instâncias sem pagar:** use [DEPLOY_FREE.md](./DEPLOY_FREE.md) (Fly.io).

## Render Free (US$ 0)

1. [dashboard.render.com](https://dashboard.render.com) → **New +** → **Blueprint** → repo.
2. Confirme que o blueprint mostra **Free** (não Starter).
3. **Environment** → `REDIS_URL` (Upstash `rediss://...`).
4. Deploy → abra `https://SEU_SERVICO.onrender.com`.

### Se o Render estimar ~US$ 7

Você está no plano **Starter** ou com **2 instâncias**. Corrija:

1. **Settings** → **Instance type** → **Free**.
2. **Scaling** → **1 instance**.
3. Ou apague o serviço e recrie pelo Blueprint atualizado do GitHub.

### Limitações free

- Uma instância só.
- Hibernação após inatividade — configure [UptimeRobot](https://uptimerobot.com) em `/health`.

## Demonstração em aula

Abra a URL pública; nenhuma instalação local.

Failover com **duas VMs**: veja Fly.io em [DEPLOY_FREE.md](./DEPLOY_FREE.md).
