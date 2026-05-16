# Contratos de API (HTTP — produção)

Em produção o navegador fala **somente HTTP/HTTPS** com o app no Fly.io.  
Base URL: `https://SEU_APP.fly.dev` (mesma origem do front após deploy).

Headers comuns:

| Header | Uso |
| --- | --- |
| `Content-Type` | `application/json` em POST |
| `X-Session-Id` | Sessão após login |

---

## `GET /health`

```json
{"status":"ok","instance":"fly-machine-id"}
```

---

## `POST /login`

Body:

```json
{"username":"alice"}
```

200:

```json
{
  "type":"welcome",
  "session_id":"abc123",
  "client_id":"abc123",
  "username":"alice",
  "history":[{"username":"bob","text":"oi","ts":1710000000.123,"id":"uuid"}]
}
```

401:

```json
{"type":"error","message":"username já está em uso"}
```

---

## `POST /messages`

Headers: `X-Session-Id`

Body:

```json
{"text":"Olá!"}
```

200:

```json
{"status":"enqueued"}
```

---

## `POST /heartbeat`

Headers: `X-Session-Id` — renova TTL da sessão (5 min).

---

## `GET /history?since=1710000000.0`

Headers: `X-Session-Id`

```json
{"messages":[{"username":"...","text":"...","ts":...,"id":"..."}]}
```

---

## `GET /events?session={session_id}`

SSE:

```
data: {"type":"chat","username":"alice","text":"Oi","ts":1710000000.123,"id":"uuid"}

data: {"type":"user_joined","username":"bob","ts":1710000000.5}
```

Keep-alive: `: keepalive`

---

## TCP legado (NDJSON)

Documentado para `legacy/client/` e `ENABLE_TCP_SERVER=true` em dev.

Tipos: `login`, `message`, `welcome`, `chat`, `error`, `user_joined`, `user_left`, `ping`, `pong`.
