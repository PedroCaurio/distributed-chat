# Glossário — termos do projeto

## Socket (TCP)

Conexão de rede entre dois programas. O **proxy** abre um socket TCP com o **servidor** de chat. Mensagens em linhas JSON (NDJSON) — ver `protocol.py`.

## Thread

Trecho de código que executa em paralelo no mesmo processo.

| Onde | Função |
|------|--------|
| `src/chatnet/server.py` | Uma thread **por conexão** TCP (`ClientSession`) |
| `src/chatnet/proxy.py` | Uma thread **por usuário** só para **receber** do servidor (`recv-*`) |

## Cliente e servidor (enunciado)

- **Servidor (`src/chatnet/server.py`):** centraliza mensagens, Redis e broadcast.
- **Cliente (`src/chatnet/proxy.py`):** proxy entre navegador e servidor TCP — processo cliente com thread de recepção.

## HTTP / SSE

- **HTTP:** navegador fala com `proxy.py` (`POST /login`, `POST /message`, …).
- **SSE (Server-Sent Events):** `GET /events` mantém conexão aberta; servidor envia `data: {...}\n\n`. **Não é WebSocket.**

## Redis (Upstash)

Histórico, sessões, lista de online e canal **pub/sub** para sincronizar as duas VMs do Fly.

## Fly.io

Hospedagem com duas máquinas (`fly scale count 2`). Se uma cair, a outra continua — tolerância a falhas do enunciado.

## NDJSON

Um objeto JSON por linha, terminada em `\n`. Facilita `readline` / buffer na thread de recepção.

## Failover

1. Duas instâncias no Fly.
2. Redis compartilhado (histórico sobrevive).
3. `POST /resume` + `GET /history?since=` após queda da VM do usuário.

## Arquivos `LOCAL_*`

| Arquivo | Função |
|---------|--------|
| `LOCAL_run.ps1` | Sobe `python stack.py` no PC |

A demonstração oficial usa a URL pública: [DEPLOY.md](DEPLOY.md).
