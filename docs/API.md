# API — como navegador e servidor se falam

Referência rápida. Conceitos: [GLOSSARIO.md](GLOSSARIO.md).

## HTTP (navegador → `client/`)

Base em produção: `https://SEU_APP.fly.dev` (mesma origem do React).

Após o login, envie o header `X-Session-Id: <session_id>` nas requisições.

### `POST /login`

Entrada:

```json
{ "username": "pedro" }
```

Resposta (sucesso):

```json
{
  "type": "welcome",
  "session_id": "...",
  "username": "pedro",
  "history": [ { "id": "...", "username": "...", "text": "...", "ts": 1.0 } ]
}
```

### `POST /messages`

```json
{ "text": "Olá!" }
```

### `GET /events?session=<session_id>`

Stream SSE (`text/event-stream`): eventos `chat`, `user_joined`, `user_left`.

### `GET /history?since=<timestamp>`

Recupera mensagens após um instante (útil após reconexão).

### `POST /heartbeat` e `POST /logout`

Mantêm ou encerram a sessão TCP no servidor.

---

## TCP ( `client/` → `server/` )

Uma linha = um JSON. Definição dos tipos em `common/protocol.py`.

| type | Sentido | Significado |
|------|---------|-------------|
| `login` | → servidor | Primeiro frame após conectar |
| `welcome` | ← servidor | Login OK + histórico |
| `message` | → servidor | Usuário enviou texto |
| `chat` | ← servidor | Mensagem para todos |
| `user_joined` / `user_left` | ← servidor | Presença na sala |
| `history_since` / `history` | ↔ | Sincronizar após queda |
| `ping` / `pong` | ↔ | Manter conexão viva |
| `error` | ← servidor | Erro (ex.: username em uso) |

Exemplo de envio:

```json
{"type":"message","text":"Olá"}
```

Exemplo de recepção:

```json
{"type":"chat","id":"...","username":"maria","text":"Oi","ts":1715000000.0}
```
