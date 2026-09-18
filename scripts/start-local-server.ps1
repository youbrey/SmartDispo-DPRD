$ErrorActionPreference = "Stop"
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $repoRoot

docker compose up -d
if ($LASTEXITCODE -ne 0) { throw "SmartDispo gagal dijalankan." }

docker compose ps
Write-Host "API: http://127.0.0.1:8000"
Write-Host "Panel Administrator: http://127.0.0.1:8080"
