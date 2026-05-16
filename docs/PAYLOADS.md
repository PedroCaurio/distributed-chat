# Contratos de mensagens

## HTTP (navegador → cliente)

Base URL: `https://SEU_APP.fly.dev` (mesma origem do React após deploy).

Headers comuns após login: `X-Session-Id: <session_id>`.

### `POST /login`

```json
{ "username": "pedro" }
```

Resposta 200:

```json
{
  "type": "welcome",
  "session_id": "abc...",
  "client_id": "...",
  "username": "pedro",
  "history": [{ "id": "...", "username": "...", "text": "...", "ts": 1.0 }]
}
```

### `POST /messages`

```json
{ "text": "Olá!" }
```

### `GET /events?session=<session_id>`

SSE (`text/event-stream`). Eventos: `chat`, `user_joined`, `user_left`.

### `GET /history?since=<timestamp>`

```json
{ "messages": [ ... ] }
```

### `POST /heartbeat`

Mantém sessão TCP viva (`ping` no socket).

### `POST /logout`

Encerra conexão TCP da sessão.

---

## TCP (cliente → servidor)

Uma linha UTF-8 = um JSON (NDJSON). Ver `common/protocol.py`.

| type | Direção | Descrição |
|------|---------|-----------|
| `login` | → servidor | Primeiro frame após conectar |
| `welcome` | ← servidor | OK + histórico |
| `message` | → servidor | Enviar chat |
| `chat` | ← servidor | Broadcast |
| `user_joined` / `user_left` | ← servidor | Presença |
| `history_since` | → servidor | Recuperar após `since` |
| `history` | ← servidor | Lista de mensagens |
| `ping` / `pong` | ↔ | Heartbeat |
| `error` | ← servidor | Erro |

Exemplo envio:

```json
{"type":"message","text":"Olá"}
```

Exemplo recepção:

```json
{"type":"chat","id":"...","username":"maria","text":"Oi","ts":1715000000.0}
```
