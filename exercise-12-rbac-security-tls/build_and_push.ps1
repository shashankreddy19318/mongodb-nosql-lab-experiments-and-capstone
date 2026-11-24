# PowerShell helper script to build and push to Docker Hub
param (
    [string]$Username
)

Write-Host "====================================================================" -ForegroundColor Cyan
Write-Host "     MongoDB Security Lab: Docker Build & Push to Docker Hub        " -ForegroundColor Cyan
Write-Host "====================================================================" -ForegroundColor Cyan

if (-not $Username) {
    $Username = Read-Host "Enter your Docker Hub Username"
}

if (-not $Username) {
    Write-Host "[ERROR] Docker Hub username cannot be empty." -ForegroundColor Red
    exit 1
}

$imageName = "$Username/mongodb-security-lab:latest"

Write-Host "`n[1/3] Building Docker image '$imageName'..." -ForegroundColor Yellow
docker build -t $imageName .
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Docker build failed!" -ForegroundColor Red
    exit $LASTEXITCODE
}

Write-Host "`n[2/3] Logging in to Docker Hub..." -ForegroundColor Yellow
docker login

Write-Host "`n[3/3] Pushing '$imageName' to Docker Hub..." -ForegroundColor Yellow
docker push $imageName
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Docker push failed!" -ForegroundColor Red
    exit $LASTEXITCODE
}

Write-Host "`n====================================================================" -ForegroundColor Green
Write-Host "[SUCCESS] Image successfully published to Docker Hub!" -ForegroundColor Green
Write-Host "Repository URL: https://hub.docker.com/r/$Username/mongodb-security-lab" -ForegroundColor Green
Write-Host "`nGrader demonstration command:" -ForegroundColor White
Write-Host "  docker run -it -p 27017:27017 -p 27100:27100 $imageName" -ForegroundColor Cyan
Write-Host "====================================================================" -ForegroundColor Green
