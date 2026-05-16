# Contrato de payloads (TCP — NDJSON)

Todas as mensagens são **uma linha UTF-8** com um único objeto JSON, terminada em `\n` (estilo NDJSON).

## Tipos comuns

| Campo | Tipo | Descrição |
| --- | --- | --- |
| `type` | string | Discriminador do payload (ver tabelas abaixo). |

---

## Cliente → Servidor (proxy envia estes tipos)

### `login`

Autentica o usuário na sessão TCP.

```json
{"type":"login","username":"alice"}
```

Regras:

- Deve ser o primeiro comando “de aplicação” após conectar; antes do login só `ping` é aceito.
- `username`: 1–32 caracteres (trim), não vazio.

### `message`

Envia mensagem de bate-papo após autenticado.

```json
{"type":"message","text":"Olá, pessoal!"}
```

Regras:

- `text`: 1–4000 caracteres (trim), não vazio.

### `ping` (opcional)

Keep-alive / diagnóstico. Pode ser enviado **antes** do `login`.

```json
{"type":"ping"}
```

---

## Servidor → Cliente (broadcast ou resposta direta)

### `welcome` (resposta direta ao `login`)

```json
{"type":"welcome","client_id":"<uuid>","username":"alice","history":[{"username":"bob","text":"oi","ts":1710000000.123,"id":"<uuid>"}]}
```

- `history`: mais recentes por último na lista (ordenado cronologicamente no JSON).

### `error`

```json
{"type":"error","message":"username já está em uso"}
```

### `chat` (broadcast via pub/sub + entrega local)

```json
{"type":"chat","username":"alice","text":"Oi!","ts":1710000000.123,"id":"<uuid>"}
```

### `user_joined`

```json
{"type":"user_joined","username":"alice","ts":1710000000.123}
```

### `user_left`

```json
{"type":"user_left","username":"alice","ts":1710000000.123}
```

### `pong` (resposta a `ping`)

```json
{"type":"pong","ts":1710000000.123}
```

---

## HTTP do Proxy (contrato para o front)

O front-end (`frontend/`) consome estas rotas via `chatService.ts`. Em desenvolvimento, o prefixo base é `/api` (proxy do Vite); em produção, use `VITE_PROXY_URL`.

### `GET /health`

```json
{"status":"ok","connected":true,"user":"alice"}
```

### `POST /login`

Body:

```json
{"username":"alice"}
```

200:

```json
{"type":"welcome","client_id":"...","username":"alice","history":[...]}
```

401 (erro vindo do servidor):

```json
{"type":"error","message":"..."}
```

### `POST /messages`

Body:

```json
{"text":"Olá"}
```

200:

```json
{"status":"enqueued"}
```

### `GET /events` (SSE)

Frames:

```
data: {"type":"chat",...}

data: {"type":"user_joined",...}

```

> Eventos `welcome`/`error` do TCP são consumidos internamente pelo proxy durante o login e normalmente **não** aparecem no SSE.
