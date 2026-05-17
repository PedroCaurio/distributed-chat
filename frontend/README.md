# Pacote `frontend/` — interface React

Telas de login e chat. Em **produção**, o build vira arquivos estáticos servidos pelo `client/` na mesma URL do Fly.

## Desenvolvimento no PC

Use o script [../LOCAL_front.ps1](../LOCAL_front.ps1) (sobe Vite com proxy `/api` → porta 8080).

Ou manualmente:

```bash
npm install
npm run dev
```

`frontend/.env`: `VITE_API_URL=/api`

## Build

```bash
npm run build
```

A pasta `dist/` entra na imagem Docker automaticamente.

## Deploy

Não publique o front separado. Deploy unificado: [../docs/DEPLOY.md](../docs/DEPLOY.md).
