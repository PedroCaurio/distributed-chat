# Glossário — termos do projeto

Leia este arquivo primeiro se alguma palavra nos outros documentos não estiver clara.

## Socket (TCP)

Conexão de rede entre dois programas. No nosso chat, o **cliente** (processo Python que atende o navegador) abre um **socket TCP** com o **servidor** de chat. As mensagens trafegam como linhas de texto JSON (protocolo NDJSON em `common/protocol.py`).

**Por que importa no enunciado:** o trabalho exige comunicação por sockets, não apenas HTTP entre navegador e servidor final.

## Thread

“Fio” de execução dentro do mesmo processo. Vários trechos de código rodam em paralelo sem abrir outro programa.

| Onde | O que faz |
|------|-----------|
| `server/session.py` | Uma thread **por usuário conectado** no servidor TCP |
| `client/socket_bridge.py` | Uma thread **por usuário** só para **receber** mensagens do servidor (`socket-recv-<nome>`) |

## Cliente e servidor (enunciado)

- **Servidor (`server/`):** recebe todas as mensagens, grava no Redis e repassa aos demais.
- **Cliente (`client/`):** no nosso projeto é o **proxy** entre navegador e servidor TCP. O enunciado pede um processo cliente com thread de recepção — é este pacote.

## HTTP

Protocolo que o **navegador** usa para falar com o cliente Python. Rotas como `POST /login` e `GET /events` estão em `client/app.py` (framework FastAPI).

## SSE (Server-Sent Events)

Forma de o servidor **empurrar** atualizações para o navegador por HTTP (sem WebSocket). O front abre `GET /events` e recebe eventos de chat em tempo real.

## Redis

Banco em memória na nuvem (usamos **Upstash**). Guarda histórico de mensagens, sessões e um canal **pub/sub** para as duas máquinas do Fly trocarem eventos.

## Fly.io

Serviço onde hospedamos o app. Cada **máquina (VM)** roda um container com servidor TCP + cliente HTTP. Com **duas máquinas**, se uma cair, a outra continua — tolerância a falhas do enunciado.

## Docker

Empacota o projeto (Python + build do React) numa imagem. O `Dockerfile` na raiz é o que o Fly usa no deploy. Comando de produção dentro do container: `python -m stack`.

## NDJSON

“JSON por linha”: cada mensagem no socket é uma linha UTF-8 com um objeto JSON. Facilita ler com `readline` na thread de recepção.

## Failover (tolerância a falhas)

1. Duas instâncias no Fly (`fly scale count 2`).
2. Estado compartilhado no Redis (histórico não se perde na VM que sobrou).
3. Se a VM do usuário cair, ele faz login de novo; `GET /history?since=` recupera mensagens após reconectar o SSE.

## Arquivos com prefixo `LOCAL_`

Só para desenvolvimento e testes no seu computador — **não** vão para a demonstração em aula:

| Arquivo | Função |
|---------|--------|
| `LOCAL_run.ps1` | Sobe `python -m stack` no PC |
| `LOCAL_front.ps1` | Sobe o React com Vite |
| `server/tests/LOCAL_*.py` | Testes opcionais (Redis real, imports) |

A demonstração oficial usa a URL pública do Fly (`docs/DEPLOY.md`).
