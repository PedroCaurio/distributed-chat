# Deploy no Fly.io

Hospedagem usada na demonstração: URL pública, sem instalar nada nos PCs da turma.

**URL do projeto:** [https://distributed-chat-teste.fly.dev/](https://distributed-chat-teste.fly.dev/)  
**Nome do app no Fly:** `distributed-chat-teste` (ver `fly.toml`)

## O que você precisa

| Item | Para quê |
|------|----------|
| [Conta Fly.io](https://fly.io) | Hospedar o app |
| [Upstash Redis](https://console.upstash.com) | Histórico e sincronização entre 2 máquinas |
| [Fly CLI](https://fly.io/docs/flyctl/install/) | Comandos `fly deploy`, etc. |

Instalar CLI no Windows:

```powershell
powershell -Command "iwr https://fly.io/install.ps1 -useb | iex"
fly auth login
```

## Primeiro deploy

Na pasta do projeto:

```powershell
fly secrets set REDIS_URL="rediss://default:TOKEN@HOST.upstash.io:6379"
fly deploy --no-cache
fly scale count 2
fly open
```

Se for criar outro app do zero: `fly launch --no-deploy --copy-config --name distributed-chat-teste --region gru`

Teste rápido: [https://distributed-chat-teste.fly.dev/health](https://distributed-chat-teste.fly.dev/health) → JSON com `"status":"ok"`.

## O que o Docker faz aqui

O `Dockerfile`:

1. Compila o React (`npm run build`).
2. Instala dependências Python.
3. Copia `server/`, `client/`, `stack/`, `common/`.
4. Inicia com `python -m stack` (servidor TCP na porta 9000 **dentro** do container; HTTP na 8080 **pública**).

O Fly lê `fly.toml` e publica a porta 8080 na internet.

## Variáveis importantes

| Variável | Valor típico | Significado |
|----------|--------------|-------------|
| `REDIS_URL` | secret Fly | Conexão Upstash |
| `PORT` | 8080 | HTTP do cliente (navegador) |
| `CHAT_SERVER_PORT` | 9000 | TCP do servidor (interno) |
| `CHAT_SERVER_HOST` | 127.0.0.1 | Servidor no mesmo container |

## Demo de failover na aula

```powershell
fly machines list
fly machine stop <ID>
```

Explique: uma réplica parou; usuários reconectam; histórico no Redis; segunda máquina segue ativa.

## Problemas comuns

| Sintoma | O que verificar |
|---------|-----------------|
| Login falha / 503 | `REDIS_URL` no `fly secrets`; logs com `fly logs` |
| Mensagens não aparecem com 2 VMs | Redeploy após mudanças; limpar cookies do site |
| `username já está em uso` | Sessão antiga no Redis — apagar chave no console Upstash |
| App “dormindo” | Abrir `/health` antes da aula |

## Desenvolvimento no PC (não é a demo oficial)

Use os scripts com prefixo **LOCAL**:

```powershell
copy .env.example .env
# Edite REDIS_URL
.\LOCAL_run.ps1
```

Outro terminal:

```powershell
.\LOCAL_front.ps1
```

Abra `http://localhost:5173`.
