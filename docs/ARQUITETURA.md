# Arquitetura do sistema

## Visão geral

```text
┌─────────────┐   HTTP/SSE    ┌──────────────────────────────────┐
│  Navegador  │ ────────────► │  Fly.io (máquina 1 ou 2)         │
│  (React)    │               │  ┌────────────┐   TCP    ┌───────┐ │
└─────────────┘               │  │ client/    │ ───────► │server/│ │
                              │  │ :8080 HTTP │  :9000   │ chat  │ │
                              │  └────────────┘          └───┬───┘ │
                              └──────────────────────────────┼─────┘
                                                             │
                                                    ┌────────▼────────┐
                                                    │ Redis (Upstash) │
                                                    └─────────────────┘
```

O navegador **nunca** abre socket TCP com o servidor de chat. Isso é feito pelo processo **cliente** em Python — atendendo ao enunciado (cliente com thread de recepção + servidor com thread por conexão).

## Papéis dos pacotes

| Pasta | Papel |
|-------|--------|
| `frontend/` | Telas React (login, sala de chat) |
| `client/` | Servidor HTTP para o browser + proxy TCP (thread recv por usuário) |
| `server/` | Servidor de chat TCP (thread por conexão) |
| `common/` | Formato das mensagens no socket (JSON por linha) |
| `stack/` | Liga servidor + cliente no mesmo processo (produção e `LOCAL_run.ps1`) |

## Caminho de uma mensagem

1. Usuário digita no React e clica enviar.
2. Navegador faz `POST /messages` (HTTP) para o **cliente**.
3. Cliente envia `{"type":"message",...}` pelo **socket TCP** ao **servidor**.
4. Servidor valida, salva no **Redis** e avisa as outras instâncias (pub/sub).
5. Servidor envia frame `chat` a todos os TCP conectados.
6. Thread **recv** do cliente recebe o frame e encaminha ao navegador via **SSE** (`GET /events`).

Todas as mensagens passam pelo servidor antes de chegar aos outros — requisito do trabalho.

## Threads (ponto central da avaliação)

| Local | Implementação |
|-------|----------------|
| Servidor | `ClientSession` em `server/session.py` estende `threading.Thread` — uma por conexão |
| Cliente | `SocketBridge._recv_loop` em `client/socket_bridge.py` — uma por usuário logado |
| Servidor (2 VMs) | Thread que escuta o canal Redis pub/sub e repete para os TCP locais |

## Duas máquinas no Fly (failover)

- Comando: `fly scale count 2`.
- Cada máquina tem seu próprio processo; conexões TCP dos usuários ficam na memória **daquela** máquina.
- O Redis guarda o que precisa sobreviver à queda de uma VM (histórico, pub/sub).
- Cookie `fly_machine_id` + middleware em `client/affinity.py` mantêm o HTTP do mesmo usuário na VM certa.

Se uma VM cair: usuário faz login de novo na VM viva; `GET /history?since=` recupera mensagens após reconectar.

## Como executar

| Situação | Comando |
|----------|---------|
| Produção / Fly / Docker | `python -m stack` |
| No seu PC | `.\LOCAL_run.ps1` + `.\LOCAL_front.ps1` |
| Só servidor TCP (debug) | `python -m server` |
| Só cliente HTTP (debug) | `python -m client` (servidor TCP já deve estar rodando) |

Mais detalhes de deploy: [DEPLOY.md](DEPLOY.md).  
Contratos HTTP/TCP: [API.md](API.md).
