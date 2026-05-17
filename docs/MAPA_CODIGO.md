# Onde está cada requisito do enunciado

| Requisito | Arquivo | O que mostrar na apresentação |
|-----------|---------|-------------------------------|
| Socket TCP | `src/chatnet/protocol.py` | `encode` / `decode`, tipos `login`, `message`, `chat` |
| Thread por conexão (servidor) | `src/chatnet/server.py` | `class ClientSession(threading.Thread)` |
| Thread de recepção (cliente) | `src/chatnet/proxy.py` | `TCPSession._recv_loop` |
| HTTP embutido no cliente | `src/chatnet/proxy.py` | `ProxyHandler`, rotas `/login`, `/message`, `/events` |
| Interface web | `src/chatnet/static/index.html` | Login, chat, lista online |
| Mensagens via servidor | `src/chatnet/server.py` | `append_history` + `_publish_event` |
| Tolerância a falhas | `fly.toml`, `affinity.py`, `redis_backend.py` | 2 VMs + Redis + demo `fly machine stop` |
| Produção | `src/chatnet/stack.py`, `Dockerfile` | `python -m chatnet` no container |

## Fluxo em uma frase

Navegador → **HTTP** → `proxy.py` → **TCP** → `server.py` → **Redis** → broadcast → **SSE** de volta ao navegador.

## Testes

```powershell
python -m pytest -q
```
