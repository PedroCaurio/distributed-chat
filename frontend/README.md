# Front-end (React + Vite)

Interface do chat. Em produção o build é embutido no Docker e servido pelo `server/` na mesma URL Fly.io.

## Desenvolvimento

```bash
npm install
npm run dev
```

Configure `frontend/.env`:

```env
VITE_API_URL=/api
```

O `vite.config.ts` encaminha `/api` para `http://127.0.0.1:8080` (servidor local).

## Build

```bash
npm run build
```

Saída em `dist/` — copiada automaticamente pelo `Dockerfile` na raiz.

## Deploy

Não publique o front separadamente. Use o deploy unificado: [../docs/DEPLOY.md](../docs/DEPLOY.md).
