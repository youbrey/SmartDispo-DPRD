[CmdletBinding()]
param(
    [string]$BackupRoot
)

$ErrorActionPreference = "Stop"
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
if ([string]::IsNullOrWhiteSpace($BackupRoot)) {
    $BackupRoot = Join-Path $repoRoot "backups"
}
$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$workingDirectory = Join-Path $BackupRoot "smartdispo-$timestamp"
$archivePath = "$workingDirectory.zip"
New-Item -ItemType Directory -Path $workingDirectory -Force | Out-Null
Set-Location $repoRoot

docker compose exec -T postgres sh -lc 'pg_dump --clean --if-exists --no-owner --no-privileges -U "$POSTGRES_USER" "$POSTGRES_DB" > /tmp/smartdispo.sql'
if ($LASTEXITCODE -ne 0) { throw "Backup PostgreSQL gagal." }
docker compose cp postgres:/tmp/smartdispo.sql (Join-Path $workingDirectory "smartdispo.sql")
docker compose exec -T postgres rm -f /tmp/smartdispo.sql

docker compose cp api:/app/generated (Join-Path $workingDirectory "generated")
docker compose cp api:/app/storage/attachments (Join-Path $workingDirectory "attachments")
docker compose cp api:/app/storage/templates (Join-Path $workingDirectory "uploaded-templates")
Copy-Item (Join-Path $repoRoot "templates") (Join-Path $workingDirectory "builtin-templates") -Recurse

Compress-Archive -Path (Join-Path $workingDirectory "*") -DestinationPath $archivePath -CompressionLevel Optimal
Write-Host "Backup selesai: $archivePath" -ForegroundColor Green
Write-Warning "Simpan salinan ZIP ini di disk/komputer lain. File .env tidak dimasukkan karena berisi rahasia server."
