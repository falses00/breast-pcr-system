$ErrorActionPreference = "Stop"
$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
$env:npm_config_cache = "I:\software Project\.npm-cache"
$env:PIP_CACHE_DIR = "I:\software Project\.pip-cache"

Write-Host "== Breast PCR system verify =="

Push-Location $Root
python -m pytest backend\tests -q
python harness\api_test.py
python harness\model_test.py
docker compose config | Out-Null
Pop-Location

Push-Location (Join-Path $Root "backend")
python -m app.ml.train_from_local_dataset | Out-Null
Pop-Location

Push-Location (Join-Path $Root "frontend")
npm.cmd run build
Pop-Location

Write-Host "Verify finished."
