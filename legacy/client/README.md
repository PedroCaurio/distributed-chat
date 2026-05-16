# Proxy local (legado)

Não use na apresentação. Produção: URL pública Fly.io — [docs/DEPLOY.md](../../docs/DEPLOY.md).

## Execução (dev)

Na raiz do repositório:

```powershell
$env:PYTHONPATH = "$(Get-Location);$(Get-Location)\legacy"
$env:CHAT_SERVER_HOST = "127.0.0.1"
$env:CHAT_SERVER_PORT = "9000"
$env:PROXY_HTTP_PORT = "5000"
python -m client
```

Front: `frontend/.env` com `VITE_API_URL=http://127.0.0.1:5000`
