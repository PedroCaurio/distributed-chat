# API — HTTP (navegador) e TCP (proxy ↔ servidor)

## HTTP — `proxy.py` (porta 8080)

| Método | Rota | Descrição |
|--------|------|-----------|
| `GET` | `/` | Interface `index.html` |
| `POST` | `/login` | Body: `{ "username", "client_id?" }` → `{ "session_id", "history", "users" }` |
| `POST` | `/resume` | Body: `{ "username", "client_id", "since?" }` — retoma após failover |
| `POST` | `/message` | Header `X-Session-Id`; body `{ "text" }` |
| `GET` | `/events?session=<id>` | SSE — eventos `chat`, `user_joined`, `user_left` |
| `POST` | `/heartbeat` | Header `X-Session-Id` — mantém sessão |
| `POST` | `/logout` | Encerra sessão TCP |
| `GET` | `/history?since=<float>` | Mensagens após timestamp |
| `GET` | `/health` | `{ "status": "ok", "role": "proxy", ... }` |

Credenciais: cookie `fly_machine_id` (Fly) + header `X-Session-Id` nas rotas autenticadas.

## SSE — formato

```
data: {"type":"chat","id":"...","username":"...","text":"...","ts":123.4}

```

Keepalive: linhas `: keepalive` ou comentário de padding.

## TCP — NDJSON (`protocol.py`)

Cada frame é uma linha UTF-8 JSON + `\n`.

### Cliente → Servidor (proxy → server)

| type | Campos |
|------|--------|
| `login` | `username`, `client_id?`, `since?` |
| `message` | `text` |
| `ping` | — |
| `logout` | — |
| `history_since` | `since` |

### Servidor → Cliente

| type | Campos |
|------|--------|
| `welcome` | `session_id`, `username`, `history`, `users`, `rejoined?` |
| `chat` | `id`, `username`, `text`, `ts` |
| `user_joined` / `user_left` | `username`, `ts`, `users` |
| `history` | `items` |
| `pong` | `ts` |
| `error` | `message` |

## Redis pub/sub

Canal: `chat:events`. Payload JSON com `_origin` (ID da VM) para evitar eco duplicado no servidor TCP.
