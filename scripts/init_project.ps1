param(
  [switch]$SkipNpmInstall
)

$ErrorActionPreference = "Stop"
$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
$Backend = Join-Path $Root "backend"
$Frontend = Join-Path $Root "frontend"
$env:npm_config_cache = "I:\software Project\.npm-cache"
$env:PIP_CACHE_DIR = "I:\software Project\.pip-cache"

Write-Host "== Breast PCR system init =="
Write-Host "Project: $Root"
Write-Host "npm cache: $env:npm_config_cache"
Write-Host "pip cache: $env:PIP_CACHE_DIR"

Push-Location $Backend
python -m pip install -r requirements.txt
python -m app.services.reset_to_real_dataset
python -m app.ml.train_from_local_dataset
Pop-Location

Push-Location $Frontend
if (-not $SkipNpmInstall) {
  npm.cmd install
}
npm.cmd run build
Pop-Location

Write-Host "Init finished."
