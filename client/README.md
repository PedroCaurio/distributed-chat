# Proxy local (opcional)

Este módulo era necessário quando o navegador não acessava o servidor diretamente.

Na versão **100% web**, o deploy Render expõe API + front na mesma URL. **Não use o proxy na apresentação em aula.**

## Quando usar

- Desenvolvimento local com servidor TCP na porta 9000
- Demonstrar thread `recv` + socket nativo no relatório

## Execução (legado)

```powershell
$env:PYTHONPATH = (Get-Location).Path
$env:CHAT_SERVER_HOST = "127.0.0.1"
$env:CHAT_SERVER_PORT = "9000"
python -m client
```

Front em dev com `VITE_PROXY_URL=http://127.0.0.1:5000`.
