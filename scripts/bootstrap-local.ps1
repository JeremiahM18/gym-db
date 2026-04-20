$backendEnvExample = Join-Path $PSScriptRoot "..\backend\.env.example"
$backendEnv = Join-Path $PSScriptRoot "..\backend\.env"
$frontendEnv = Join-Path $PSScriptRoot "..\frontend\.env.local"

if (-not (Test-Path $backendEnv)) {
    Copy-Item -LiteralPath $backendEnvExample -Destination $backendEnv
    Write-Host "Created backend/.env from .env.example"
} else {
    Write-Host "backend/.env already exists"
}

if (-not (Test-Path $frontendEnv)) {
    @"
VITE_API_BASE_URL=http://localhost:8000
# Optional when backend auth bypass is disabled:
# VITE_API_TOKEN=<bearer token>
"@ | Set-Content -LiteralPath $frontendEnv
    Write-Host "Created frontend/.env.local"
} else {
    Write-Host "frontend/.env.local already exists"
}

Write-Host ""
Write-Host "Next steps:"
Write-Host "1. docker compose up -d postgres"
Write-Host "2. cd backend; python -m venv .venv; .\.venv\Scripts\activate; pip install -r requirements-dev.txt"
Write-Host "3. Set TOMTOM_API_KEY in backend/.env before running ingest or publish flows"
Write-Host "4. .\.venv\Scripts\python.exe .\scripts\sync_dataset_to_postgres.py  # seeds the Nashville default slice into Postgres"
Write-Host "5. python -m uvicorn api.main:app --reload"
Write-Host "6. nvm use 24  # optional, if you manage Node with nvm"
Write-Host "7. cd frontend; npm install; npm run generate:api; npm run dev"
