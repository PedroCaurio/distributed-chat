# Roteiro de apresentação

Checklist para quem for sorteado na hora. A URL pública do Fly deve estar no ar **antes** da aula.

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

## 3. Demonstração ao vivo (3 min)

1. Compartilhe `https://SEU_APP.fly.dev`.
2. Login com dois nomes (duas abas ou dois celulares).
3. Envie mensagens — todas aparecem para todos.
4. Mostre histórico ao recarregar a página (vem do Redis).

## 4. Failover opcional (1 min)

```powershell
fly machines list
fly machine stop <ID>
```

Explique: uma VM parou; usuários reconectam; histórico permanece no Redis; banner de reconexão no front.

## 5. Código sob demanda (se pedirem)

| Pergunta provável | Abrir |
|-------------------|--------|
| Onde está a thread por conexão? | `server/session.py` |
| Onde está a thread recv do cliente? | `client/socket_bridge.py` |
| Onde está o HTTP para o navegador? | `client/app.py` |
| Como sobe em produção? | `stack/__main__.py`, `Dockerfile` |

Mapa completo: [MAPA_CODIGO.md](MAPA_CODIGO.md).

## 6. Extras (criatividade)

- Interface React com username
- Histórico persistido
- Identificação de entrou/saiu na sala

## O que NÃO fazer na demo

- Não depender de `localhost` — a avaliação exige URL online.
- Não precisar instalar Python/Node nos PCs da turma — só o navegador.

## Entrega AVA

Zip com: código, `requirements.txt`, `README.md`, relatório PDF (estrutura no enunciado).
