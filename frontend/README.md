# Front-end — Zenith Chat (React + Vite)

Interface web que conversa com o **proxy Python** (`client/`) via HTTP e SSE.

## Pré-requisitos

- Node.js 20+
- Proxy rodando em `http://127.0.0.1:5000` (ou URL configurada)

## Instalação

```bash
cd frontend
npm install
```

## Desenvolvimento

```bash
npm run dev
```

Abre em `http://localhost:5173`. O Vite encaminha `/api/*` para o proxy local (ver `vite.config.ts`).

## Variáveis de ambiente

Copie `.env.example` para `.env` se precisar apontar para outro host:

```env
VITE_PROXY_URL=http://127.0.0.1:5000
```

Se `VITE_PROXY_URL` não estiver definida, o front usa `/api` (proxy do Vite em dev).

## Build de produção

```bash
npm run build
npm run preview
```

Para deploy na Vercel, configure `VITE_PROXY_URL` com a URL **acessível pelo navegador do usuário** do proxy (em avaliação local, normalmente `http://127.0.0.1:5000`).
