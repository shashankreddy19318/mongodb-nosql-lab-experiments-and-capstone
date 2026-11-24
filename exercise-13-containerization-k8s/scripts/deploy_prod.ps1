<#
.SYNOPSIS
    Automated deployment and initialization script for Lab 13.1 on Windows.
#>
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  Lab 13.1: Deploy Production 3-Node Replica Set" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# 1. Keyfile check
if (-not (Test-Path "$Root\keyfile")) {
    Write-Host "[Step 1] Generating keyfile..." -ForegroundColor Yellow
    $bytes = New-Object byte[] 756
    $rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
    $rng.GetBytes($bytes)
    $base64 = [Convert]::ToBase64String($bytes)
    [System.IO.File]::WriteAllText("$Root\keyfile", $base64.Trim() + "`n", [System.Text.Encoding]::ASCII)
    Write-Host "[OK] Keyfile generated." -ForegroundColor Green
} else {
    Write-Host "[Step 1] Keyfile already exists." -ForegroundColor Green
}

# 2. Docker Compose
Write-Host "`n[Step 2] Starting MongoDB containers via docker-compose..." -ForegroundColor Yellow
docker-compose -f docker-compose.yml up -d mongo-rs0-1 mongo-rs0-2 mongo-rs0-3

Write-Host "Waiting 15 seconds for mongod instances to initialize..."
Start-Sleep -Seconds 15

# 3. Initialize Replica Set
Write-Host "`n[Step 3] Initializing Replica Set 'rs0'..." -ForegroundColor Yellow
Get-Content "$Root\scripts\init-replica.js" | docker exec -i prod-mongo-1 mongosh --quiet

# 4. Exporter
Write-Host "`n[Step 4] Starting Prometheus Exporter & Prometheus Server..." -ForegroundColor Yellow
docker-compose -f docker-compose.yml up -d mongo-exporter prometheus
Start-Sleep -Seconds 5

# 5. Status
Write-Host "`n[Step 5] Checking Replica Set Status..." -ForegroundColor Yellow
docker exec -i prod-mongo-1 mongosh -u admin -p AdminPass123! --authenticationDatabase admin --quiet --eval "rs.status().members.forEach(m => print('Member [' + m.name + '] : State=' + m.stateStr + ', Health=' + m.health));"

Write-Host "`n[OK] Lab 13.1 Deployment Complete!" -ForegroundColor Green
