# Roteiro de apresentação (≈10 min)

## 1. Problema e solução (1 min)

Chat em tempo real para vários usuários; mensagens sempre passam pelo servidor; hospedado no Fly, acessível pelo navegador sem instalar nada.

URL: **https://chatnet-v2.fly.dev/**

## 2. Arquitetura (2 min)

Mostrar diagrama em [ARQUITETURA.md](ARQUITETURA.md):

- Navegador: HTTP + SSE (não WebSocket)
- `proxy.py`: cliente do enunciado (HTTP + TCP + thread recv)
- `server.py`: servidor TCP (thread por conexão)
- Redis: histórico e sync entre 2 VMs

## 3. Threads e sockets (3 min) — critério forte

Abrir na IDE:

1. `server.py` → `class ClientSession(threading.Thread)` e `run()`
2. `proxy.py` → `TCPSession._recv_loop`
3. `protocol.py` → NDJSON uma linha por mensagem

Frase-chave: *“Cada aba do navegador gera uma conexão TCP; o servidor cria uma thread por socket; o proxy cria uma thread só para receber.”*

## 4. Demo ao vivo (3 min)

1. Abrir duas abas (ou celular + notebook) — usuários diferentes.
2. Enviar mensagens — tempo real.
3. `fly machines list` → `fly machine stop <id>` → mostrar que o chat continua na outra VM e que o histórico volta após resume.

## 5. Extras (1 min)

- Apelido + lista de online
- Histórico ao entrar
- Interface em `index.html` (HTML/CSS/JS puro, sem npm no deploy)

## 6. Perguntas esperadas

| Pergunta | Resposta curta |
|----------|----------------|
| Por que não WebSocket? | SSE + HTTP atende o browser; TCP puro entre proxy e servidor cumpre sockets no enunciado |
| Onde está o failover? | 2 máquinas Fly + Redis; cookie de afinidade |
| E se cair o Redis? | Histórico e sync param; VMs ainda servem TCP local até expirar sessão |

## Checklist antes da aula

- [ ] `fly status` — 2 máquinas `started`
- [ ] Abrir `/health` na URL pública
- [ ] Testar 2 abas na sala
- [ ] PDF do relatório pronto para o AVA
