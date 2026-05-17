# Roteiro de apresentação

Checklist para quem for sorteado na hora. URL do chat: [https://distributed-chat-teste.fly.dev/](https://distributed-chat-teste.fly.dev/)

## Antes de entrar na sala

- [ ] `fly open` abre o chat
- [ ] `/health` responde `{"status":"ok",...}`
- [ ] Duas máquinas: `fly scale count 2`
- [ ] Abrir o chat em duas abas com usuários diferentes e trocar mensagens

## 1. Problema (30 s)

Chat multiusuário em tempo real: várias pessoas na mesma sala, mensagens passam **sempre** pelo servidor antes de chegar aos outros.

## 2. Arquitetura (2 min)

Desenhe ou mostre o diagrama em [ARQUITETURA.md](ARQUITETURA.md):

- Navegador não fala TCP direto com o servidor de chat — fala HTTP com o **cliente** (`client/`).
- O **cliente** mantém o socket TCP e a **thread de recepção** (requisito).
- O **servidor** (`server/`) tem **uma thread por conexão TCP**.
- **Redis** guarda histórico e sincroniza duas VMs no Fly.

Termos: ver [GLOSSARIO.md](GLOSSARIO.md).

## 3. Mostrar logs ao vivo (recomendado)

### Console do navegador (camada web)

1. Abra o chat → **F12** → aba **Console**.
2. No Fly, basta `DEMO_LOGS=1` no servidor — o front lê `/health` e ativa os logs automaticamente (não precisa rebuild).
3. Em dev local, `VITE_DEMO_LOGS=true` em `frontend/.env` também funciona (`LOCAL_front.ps1` já cria).
4. Faça login e envie uma mensagem — aparecem linhas `[DEMO][navegador]` com o **arquivo/função** (ex.: `chatService.sendMessage`, `useChatEvents.onmessage`).

O banner explica: a **thread TCP** não roda no navegador; ela está no Python (`client/socket_bridge.py`).

### Terminal do servidor (Python)

**No seu PC:**

```powershell
# .env com DEMO_LOGS=1 (LOCAL_run.ps1 já define)
.\LOCAL_run.ps1
```

**No Fly (durante a aula):**

```powershell
fly secrets set DEMO_LOGS=1
fly deploy
fly logs
```

Deixe `fly logs` aberto em um terminal projetado na tela. Os logs vêm em **blocos curtos** (não uma linha gigante):

```text
[DEMO] HTTP POST /login — navegador entrou; proxy abrirá TCP
  thread: MainThread
  código: client.app.login
  username: pedro

[DEMO] Socket TCP
  tipo: message
  direção: → enviado
  username: pedro
  código: client.socket_bridge.SocketBridge.send_message
```

| Prefixo | Significado |
|---------|-------------|
| `[DEMO]` | Fluxo normal (login, TCP, SSE) |
| `[TRACE]` | Diagnóstico de sessão inválida / loop |
| `código:` | Arquivo/função Python que executou |
| `thread:` | Nome da thread (requisito do enunciado) |

**Roteiro visual:** envie uma mensagem na aba 1 → no navegador aparece `POST /messages` → no terminal aparece `ProxyRuntime.send_chat` → `TCP → enviado` → `ClientSession.run` → `ChatCore.send_message` → `pub/sub` → `socket-recv` → `SSE → navegador`.

## 4. Demonstração ao vivo (3 min)

1. Compartilhe [https://distributed-chat-teste.fly.dev/](https://distributed-chat-teste.fly.dev/).
2. Login com dois nomes (duas abas ou dois celulares).
3. Envie mensagens — todas aparecem para todos.
4. Mostre histórico ao recarregar a página (vem do Redis).

## 5. Failover opcional (1 min)

```powershell
fly machines list
fly machine stop <ID>
```

Explique: uma VM parou; usuários reconectam; histórico permanece no Redis; banner de reconexão no front.

## 6. Código sob demanda (se pedirem)

| Pergunta provável | Abrir |
|-------------------|--------|
| Onde está a thread por conexão? | `server/session.py` |
| Onde está a thread recv do cliente? | `client/socket_bridge.py` |
| Onde está o HTTP para o navegador? | `client/app.py` |
| Como sobe em produção? | `stack/__main__.py`, `Dockerfile` |

Mapa completo: [MAPA_CODIGO.md](MAPA_CODIGO.md).

## 7. Extras (criatividade)

- Interface React com username
- Histórico persistido
- Identificação de entrou/saiu na sala

## O que NÃO fazer na demo

- Não depender de `localhost` — a avaliação exige URL online.
- Não precisar instalar Python/Node nos PCs da turma — só o navegador.

## Loop de 401 no `fly logs` (`/events` + `/history`)

Significa **aba antiga** com sessão que não existe mais no servidor (ex.: após `fly deploy` ou login que falhou).

1. **Feche todas as abas** do chat.
2. Rode `fly deploy` (rebuild do front incluso).
3. Abra o site de novo com **Ctrl+Shift+R** (limpa cache do JS).
4. Faça login outra vez.

Se ainda aparecer o mesmo `session=33862f...` em loop, é cache/aba antiga — não é tráfego novo.

### Ler os logs `[TRACE]` (diagnóstico)

Exemplo no `fly logs` (várias linhas, fácil de ler):

```text
[TRACE] sessao ausente nesta vm — GET /history → 401
  sessão: 33862f6677bf… | req: 9dd3fdf9 | tentativas(30s): 4
  → Provável JS em cache — feche abas e use Ctrl+Shift+R
  local vm: 2863022c99…
  session na vm: sim
  ativas: 0
```

| Campo | Significado |
|-------|-------------|
| `aba navegador` | ID da aba (`-` = JS antigo em cache) |
| `session na vm: sim` | Esta VM **não** tem a sessão |
| `ativas` / `conhecidas` | Quem está logado nesta VM agora |
| linha `→` | Dica do que fazer |

No navegador (F12): `[TRACE][aba abc12345 #1] …` — o mesmo ID deve aparecer em `aba navegador` no Fly.

**Interpretação rápida:**

- `trace_tab=-` e loop continua → aba com **JavaScript em cache** (Ctrl+Shift+R).
- `session_na_vm=sim` e `conhecidas` com outros IDs → sessão morta; feche a aba e faça login de novo.
- `fly-replay` antes do 401 → requisição caiu na VM errada (afinidade).

**Exemplo real (seu log):**

```text
session=33862f6677bf… | session_na_vm=sim | ativas=0 | conhecidas=[] | trace_tab=-
```

Significa: alguém pede histórico de uma sessão que **não existe mais** nesta VM (0 usuários online nela). O `trace_tab=-` indica **front antigo em cache** (sem o header da versão nova). **Solução:** fechar todas as abas → Ctrl+Shift+R → login de novo. Após 4 tentativas o servidor responde **410** e para o spam no `fly logs`.

## Entrega AVA

Zip com: código, `requirements.txt`, `README.md`, relatório PDF (estrutura no enunciado).
