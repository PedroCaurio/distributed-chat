# Deploy em produção

> **Atualizado:** arquitetura 100% web. Use [DEPLOY_RENDER.md](./DEPLOY_RENDER.md).

O guia Fly.io + proxy local foi substituído por:

- **Render** — 2 instâncias HTTP + load balancer
- **Upstash** — Redis
- **Uma URL** — front + API (Dockerfile na raiz)

Não é mais necessário `fly deploy`, `python -m client` nem duas portas de proxy para a banca.
