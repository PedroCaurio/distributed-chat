# Onde está cada requisito do enunciado

Use esta tabela na apresentação para abrir o arquivo certo na hora.

| Requisito do enunciado | Arquivo principal | O que mostrar |
|------------------------|-------------------|---------------|
| Socket TCP entre cliente e servidor | `common/protocol.py` | Tipos de mensagem (`login`, `message`, `chat`…) |
| Servidor com thread por conexão | `server/session.py` | Classe `ClientSession(threading.Thread)` |
| Cliente com thread de recepção | `client/socket_bridge.py` | `_recv_loop` na thread `socket-recv-*` |
| Servidor HTTP embutido no cliente | `client/app.py` | Rotas `/login`, `/messages`, `/events` |
| Interface web | `frontend/src/` | Telas de login e chat |
| Mensagens passam pelo servidor | `server/chat_core.py` | Grava e publica no Redis antes do broadcast |
| Tolerância a falhas (réplica) | `fly.toml` + `docs/DEPLOY.md` | 2 máquinas Fly + Redis compartilhado |
| Entrada em produção | `stack/__main__.py` | `python -m stack` (TCP + HTTP juntos) |
| Deploy online | `Dockerfile`, `fly.toml` | Build e URL pública |

## Fluxo em uma frase

Navegador → **HTTP** → `client/` → **socket TCP** → `server/` → **Redis** → broadcast → de volta ao navegador via **SSE**.

## Testes automáticos (opcional no PC)

```powershell
$env:PYTHONPATH = (Get-Location).Path
python -m pytest -q
```

Testes com prefixo `LOCAL_` no nome são smoke checks locais; `LOCAL_test_redis.py` só roda com `REDIS_URL` definido.
