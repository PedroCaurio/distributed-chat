# Avaliação em relação ao enunciado

Checklist objetivo para o trabalho **ChatNet v2** (implementação única neste repositório).

## 1. Requisitos técnicos obrigatórios

| Requisito | Atendido? | Evidência |
|-----------|-----------|-----------|
| Múltiplos usuários simultâneos | **Sim** | Várias conexões TCP + sessões Redis |
| Servidor: thread por conexão | **Sim** | `server.py` → `ClientSession(threading.Thread)` |
| Cliente: thread dedicada à recepção | **Sim** | `proxy.py` → `TCPSession._recv_thread` |
| Aplicação acessível via navegador | **Sim** | `index.html` + rotas HTTP em `proxy.py` |
| Servidor HTTP embutido no cliente | **Sim** | `proxy.py` (`http.server`, porta 8080) |
| Mensagens passam pelo servidor | **Sim** | `server.py` grava e faz broadcast antes dos clientes |
| Tolerância a falhas (réplica) | **Sim** | `fly scale count 2` + Redis + `affinity.py` + `/resume` |

## 2. Acesso via navegador e hospedagem online

| Critério | Atendido? | Evidência |
|----------|-----------|-----------|
| Funciona no navegador sem instalar | **Sim** | URL pública, HTML servido pelo proxy |
| Hospedado online (não localhost) | **Sim** | https://chatnet-v2.fly.dev/ |
| Deploy em serviço cloud | **Sim** | Fly.io (`fly.toml`, `Dockerfile`) |

## 3. Criatividade e extras

| Extra | Presente? |
|-------|-----------|
| Interface amigável | **Sim** — tema escuro, bolhas, lista online |
| Identificação de usuários | **Sim** — apelido único, `client_id` no localStorage |
| Histórico de mensagens | **Sim** — Redis + `welcome.history` + `/history` |
| Failover com recuperação | **Sim** — resume + SSE + histórico `since` |
| Testes automatizados | **Sim** — `pytest` em `tests/` |

## 4. Qualidade do código e organização

| Critério | Atendido? |
|----------|-----------|
| Código modular (`src/chatnet/`: protocol, server, proxy, …) | **Sim** |
| Comentário no topo de cada script | **Sim** |
| Docstrings em funções e classes | **Sim** |
| `requirements.txt` | **Sim** |
| `README.md` com execução | **Sim** |
| Documentação em `docs/` | **Sim** |

## 5. Entrega AVA (responsabilidade do grupo)

| Item | Status no repo |
|------|----------------|
| Código-fonte completo | **Incluído** |
| `requirements.txt` | **Incluído** |
| `README.md` | **Incluído** |
| Relatório PDF | **Fora do git** — entregar no AVA conforme orientação |

## 6. Apresentação presencial — o que preparar

1. Explicar fluxo navegador → proxy → servidor → Redis → SSE.
2. Mostrar threads em `server.py` e `proxy.py`.
3. Executar: `.\LOCAL_run.ps1` **ou** usar URL Fly.
4. Demo: 2 usuários + opcional `fly machine stop`.

## 7. Lacunas / observações honestas

- **Relatório PDF** não está versionado; deve ser produzido pelo grupo usando `docs/` como base.
- **WebSocket** não é usado (SSE + TCP cumprem o enunciado de sockets no backend).
- Em desenvolvimento local é necessário **Redis** (`REDIS_URL`); no Fly usa Upstash.

## Conclusão

O projeto **cumpre o enunciado** nos pontos de sockets, threads, cliente-servidor, interface web, servidor HTTP no processo cliente e tolerância a falhas com segunda instância Fly + estado compartilhado em Redis. A nota final depende ainda do **relatório PDF** e da **apresentação presencial** (40% do critério de avaliação).
