# distributed-chat (MVP servidor + proxy)

Chat multiusuário com **TCP + threads** no servidor, **Redis** para estado e replicação via **pub/sub**, e **proxy local** com **FastAPI + SSE** para integração com o front-end.

> O front-end React não faz parte deste MVP no repositório atual.

## Requisitos

- Python 3.11+
- Redis compatível com `redis-py` (Render Key Value, Upstash, Redis Cloud, etc.)

## Instalação

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Copie `.env.example` para `.env` e preencha as variáveis.

## Executar o servidor (Linux/Windows)

Na raiz do repositório:

```bash
# Windows PowerShell
$env:PYTHONPATH="$PWD"; python -m server
```

```bash
# Linux/macOS
PYTHONPATH=. python -m server
```

## Executar o proxy local (HTTP para o front)

```bash
# Windows PowerShell
$env:PYTHONPATH="$PWD"; python -m client
```

```bash
# Linux/macOS
PYTHONPATH=. python -m client
```

Endpoints principais:

- `GET http://127.0.0.1:5000/health`
- `POST http://127.0.0.1:5000/login`
- `POST http://127.0.0.1:5000/messages`
- `GET http://127.0.0.1:5000/events` (SSE)

## Testes

```bash
pytest
```

Diagnóstico opcional de Redis (precisa de `REDIS_URL`):

```bash
pytest -m integration
```

## Documentação

- `docs/ARCHITECTURE.md`
- `docs/PAYLOADS.md`
- `docs/DEPLOY_RENDER.md`
