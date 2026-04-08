$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$backendDir = Join-Path $repoRoot "backend"
$frontendDir = Join-Path $repoRoot "frontend"
$backendPython = Join-Path $backendDir ".venv\Scripts\python.exe"
$openApiPath = Join-Path $backendDir "openapi.json"

if (-not (Test-Path $backendPython)) {
    throw "Expected backend virtual environment at backend/.venv. Create it first so the OpenAPI export uses project dependencies."
}

Push-Location $backendDir
try {
    & $backendPython scripts/export_openapi.py --out $openApiPath
    if ($LASTEXITCODE -ne 0) {
        throw "OpenAPI export failed."
    }
}
finally {
    Pop-Location
}

Push-Location $frontendDir
try {
    npm exec openapi-typescript-codegen -- --input ..\backend\openapi.json --output src/api --client fetch
    if ($LASTEXITCODE -ne 0) {
        throw "Frontend API client generation failed."
    }
}
finally {
    Pop-Location
}
