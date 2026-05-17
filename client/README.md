# Pacote `client/` — proxy HTTP + TCP

Processo **cliente** do enunciado: o navegador fala **HTTP** com este pacote; este pacote fala **TCP** com o servidor de chat.

```text
Navegador ──HTTP/SSE──► client/ ──TCP──► server/
```

## Arquivos principais

| Arquivo | Função |
|---------|--------|
| `app.py` | Rotas `/login`, `/messages`, `/events`, … |
| `socket_bridge.py` | Socket TCP + thread `socket-recv-<user>` |
| `runtime.py` | Uma sessão por usuário logado |
| `affinity.py` | Manter o usuário na mesma VM no Fly (2 máquinas) |

## Documentação

Tudo está centralizado em [../docs/](../docs/) — comece por [MAPA_CODIGO.md](../docs/MAPA_CODIGO.md).

Para rodar no PC: [../LOCAL_run.ps1](../LOCAL_run.ps1) (não use na apresentação; use a URL do Fly).
