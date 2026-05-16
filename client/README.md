# Cliente (proxy HTTP + TCP)

Processo **cliente** do enunciado: servidor HTTP embutido para o navegador e thread dedicada de recepção em socket TCP para o servidor de chat.

## Papel na arquitetura

```text
Navegador ──HTTP/SSE──► client/ (este pacote) ──TCP──► server/
```

- Cada usuário logado = **1 conexão TCP** + **1 thread `socket-recv-<user>`**
- Rotas HTTP: `/login`, `/messages`, `/events`, `/history`, `/heartbeat`
- Em produção, servido junto com o servidor via `python -m stack`

## Execução local (dev)

Terminal 1 — servidor TCP:

```powershell
$env:PYTHONPATH = (Get-Location).Path
$env:REDIS_URL = "rediss://..."
python -m server
```

Terminal 2 — cliente HTTP:

```powershell
$env:PYTHONPATH = (Get-Location).Path
$env:CHAT_SERVER_HOST = "127.0.0.1"
$env:CHAT_SERVER_PORT = "9000"
$env:PORT = "8080"
python -m client
```

Terminal 3 — front:

```bash
cd frontend && npm run dev
```

`frontend/.env`: `VITE_API_URL=/api` (proxy Vite → `:8080`)

## Ou stack unificada

```powershell
python -m stack
```
