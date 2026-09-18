[CmdletBinding()]
param(
    [switch]$RegenerateEnvironment,
    [switch]$SkipFirewall
)

$ErrorActionPreference = "Stop"
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$environmentFile = Join-Path $repoRoot ".env"

function New-RandomHex([int]$byteCount) {
    $bytes = New-Object byte[] $byteCount
    $generator = [System.Security.Cryptography.RandomNumberGenerator]::Create()
    try {
        $generator.GetBytes($bytes)
    }
    finally {
        $generator.Dispose()
    }
    return (($bytes | ForEach-Object { $_.ToString("x2") }) -join "")
}

function Convert-SecureStringToPlainText([Security.SecureString]$secureValue) {
    $pointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secureValue)
    try {
        return [Runtime.InteropServices.Marshal]::PtrToStringBSTR($pointer)
    }
    finally {
        [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($pointer)
    }
}

function Get-LanAddress {
    $route = Get-NetRoute -AddressFamily IPv4 -DestinationPrefix "0.0.0.0/0" -ErrorAction SilentlyContinue |
        Sort-Object RouteMetric, InterfaceMetric |
        Select-Object -First 1
    if ($null -eq $route) { return $null }
    return Get-NetIPAddress -AddressFamily IPv4 -InterfaceIndex $route.InterfaceIndex -ErrorAction SilentlyContinue |
        Where-Object { $_.IPAddress -notlike "169.254.*" -and $_.IPAddress -ne "127.0.0.1" } |
        Select-Object -ExpandProperty IPAddress -First 1
}

Set-Location $repoRoot

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    throw "Docker tidak ditemukan. Instal dan jalankan Docker Desktop terlebih dahulu."
}
docker compose version | Out-Null
if ($LASTEXITCODE -ne 0) {
    throw "Docker Compose tidak tersedia atau Docker Desktop belum berjalan."
}

if (-not (Test-Path $environmentFile) -or $RegenerateEnvironment) {
    $adminUsername = Read-Host "Nama pengguna administrator [admin]"
    if ([string]::IsNullOrWhiteSpace($adminUsername)) { $adminUsername = "admin" }
    if ($adminUsername -notmatch "^[A-Za-z0-9._-]{3,64}$") {
        throw "Nama pengguna hanya boleh berisi huruf, angka, titik, garis bawah, atau tanda minus."
    }

    $securePassword = Read-Host "Kata sandi administrator (minimal 12 karakter)" -AsSecureString
    $adminPassword = Convert-SecureStringToPlainText $securePassword
    if ($adminPassword -notmatch "^[A-Za-z0-9!@#%_+=.,:-]{12,128}$") {
        throw "Kata sandi wajib 12-128 karakter dan hanya boleh memakai huruf, angka, atau ! @ # % _ + = . , : -"
    }

    $postgresPassword = New-RandomHex 24
    $jwtSecret = New-RandomHex 48
    $sipsApiKey = New-RandomHex 32
    $environment = @"
SMARTDISPO_ENV=local
SMARTDISPO_BIND_ADDRESS=0.0.0.0
SMARTDISPO_API_PORT=8000
SMARTDISPO_ADMIN_PORT=8080
SMARTDISPO_POSTGRES_DB=smartdispo
SMARTDISPO_POSTGRES_USER=smartdispo
SMARTDISPO_POSTGRES_PASSWORD=$postgresPassword
SMARTDISPO_DATABASE_URL=postgresql+asyncpg://smartdispo:$postgresPassword@postgres:5432/smartdispo
SMARTDISPO_JWT_SECRET=$jwtSecret
SMARTDISPO_ACCESS_TOKEN_MINUTES=15
SMARTDISPO_REFRESH_TOKEN_DAYS=7
SMARTDISPO_CORS_ORIGINS=http://localhost:8080,http://127.0.0.1:8080
SMARTDISPO_MAX_ATTACHMENT_BYTES=10485760
SMARTDISPO_SIPS_API_KEY=$sipsApiKey
SMARTDISPO_FIREBASE_PROJECT_ID=
SMARTDISPO_FIREBASE_SERVICE_ACCOUNT_FILE=/run/secrets/firebase-service-account.json
SMARTDISPO_PUSH_POLL_SECONDS=5
SMARTDISPO_REDIS_URL=redis://redis:6379/0
SMARTDISPO_API_RATE_LIMIT_PER_MINUTE=240
SMARTDISPO_LOGIN_RATE_LIMIT_PER_MINUTE=10
SMARTDISPO_BOOTSTRAP_ADMIN_USERNAME=$adminUsername
SMARTDISPO_BOOTSTRAP_ADMIN_PASSWORD=$adminPassword
"@
    $utf8WithoutBom = New-Object System.Text.UTF8Encoding($false)
    [IO.File]::WriteAllText($environmentFile, $environment, $utf8WithoutBom)
    Write-Host "Konfigurasi server dibuat di .env." -ForegroundColor Green
}
else {
    Write-Host "Konfigurasi .env yang sudah ada dipertahankan." -ForegroundColor Yellow
}

if (-not $SkipFirewall) {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($identity)
    $isAdministrator = $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
    if ($isAdministrator) {
        foreach ($port in 8000, 8080) {
            $ruleName = "SmartDispo LAN TCP $port"
            if (-not (Get-NetFirewallRule -DisplayName $ruleName -ErrorAction SilentlyContinue)) {
                New-NetFirewallRule -DisplayName $ruleName -Direction Inbound -Action Allow `
                    -Protocol TCP -LocalPort $port -Profile Private -RemoteAddress LocalSubnet | Out-Null
            }
        }
        Write-Host "Firewall Windows mengizinkan port 8000 dan 8080 hanya dari jaringan lokal Private." -ForegroundColor Green
    }
    else {
        Write-Warning "PowerShell tidak dijalankan sebagai Administrator; aturan firewall belum dibuat. Jalankan ulang sebagai Administrator atau ikuti langkah firewall pada panduan."
    }
}

Write-Host "Membangun dan menjalankan SmartDispo..." -ForegroundColor Cyan
docker compose up -d --build
if ($LASTEXITCODE -ne 0) { throw "Docker gagal membangun atau menjalankan SmartDispo." }

$healthy = $false
for ($attempt = 1; $attempt -le 45; $attempt++) {
    try {
        $response = Invoke-RestMethod -Uri "http://127.0.0.1:8000/health" -TimeoutSec 3
        if ($null -ne $response) { $healthy = $true; break }
    }
    catch {
        Start-Sleep -Seconds 2
    }
}
if (-not $healthy) {
    docker compose ps
    throw "API belum sehat. Periksa log dengan: docker compose logs api --tail 200"
}

$lanAddress = Get-LanAddress
docker compose ps
Write-Host ""
Write-Host "SmartDispo aktif." -ForegroundColor Green
Write-Host "API komputer       : http://127.0.0.1:8000"
Write-Host "Panel Admin        : http://127.0.0.1:8080"
if ($lanAddress) {
    Write-Host "Alamat untuk APK   : $lanAddress`:8000" -ForegroundColor Cyan
    Write-Host "Panel Admin LAN    : http://$lanAddress`:8080" -ForegroundColor Cyan
}
else {
    Write-Warning "Alamat LAN tidak ditemukan. Jalankan ipconfig dan gunakan IPv4 Wi-Fi/Ethernet."
}
Write-Host "Gunakan nama pengguna dan kata sandi administrator yang Anda masukkan saat setup."
