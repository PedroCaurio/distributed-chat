# Sobe servidor TCP + proxy HTTP (mesmo processo que no Fly)
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

if (-not $env:REDIS_URL) {
    if (Test-Path ".env") {
        Get-Content ".env" | ForEach-Object {
            if ($_ -match '^\s*([^#][^=]+)=(.*)$') {
                $name = $matches[1].Trim()
                $value = $matches[2].Trim()
                Set-Item -Path "env:$name" -Value $value
            }
        }
    }
}

if (-not $env:REDIS_URL) {
    Write-Host "Defina REDIS_URL em .env ou no ambiente." -ForegroundColor Red
    exit 1
}

$env:SERVER_HOST = "127.0.0.1"
$env:SERVER_PORT = "9000"
$env:PORT = "8080"

$env:PYTHONPATH = Join-Path $PSScriptRoot "src"

Write-Host "ChatNet v2 — http://localhost:8080" -ForegroundColor Cyan
python -m chatnet
