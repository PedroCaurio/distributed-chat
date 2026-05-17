# LOCAL: interface React com proxy para o cliente HTTP em :8080.
# Uso: em outro terminal, com a stack já rodando (.\LOCAL_run.ps1)

$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "frontend")

if (-not (Test-Path ".env")) {
    @"
VITE_API_URL=/api
"@ | Set-Content -Encoding utf8 ".env"
    Write-Host "Criado frontend/.env com VITE_API_URL=/api" -ForegroundColor Yellow
}

if (-not (Test-Path "node_modules")) {
    npm install
}

Write-Host "Front em http://localhost:5173 (API via /api -> :8080)" -ForegroundColor Cyan
npm run dev
