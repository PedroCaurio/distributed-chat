# LOCAL: sobe servidor TCP + cliente HTTP no seu PC (mesmo comando do Docker/Fly).
# Uso: .\LOCAL_run.ps1
# Antes: copie .env.example para .env e preencha REDIS_URL.

$ErrorActionPreference = "Stop"
$root = $PSScriptRoot
Set-Location $root

if (-not (Test-Path ".env")) {
    Write-Host "Crie o arquivo .env a partir de .env.example (principalmente REDIS_URL)." -ForegroundColor Yellow
    exit 1
}

$env:PYTHONPATH = $root
if (-not $env:DEMO_LOGS) { $env:DEMO_LOGS = "1" }
Write-Host "Iniciando stack local (TCP :9000 + HTTP :8080) DEMO_LOGS=$env:DEMO_LOGS" -ForegroundColor Cyan
python -m stack
