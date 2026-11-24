param (
    [string]$Username = "chintan",
    [string]$Tag = "latest"
)

$ImageName = "mongodb-lab14"
$FullImage = "$Username/${ImageName}:$Tag"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  Building and Pushing Lab 14 Demonstration Docker Image" -ForegroundColor Cyan
Write-Host "  Target Image: $FullImage" -ForegroundColor Yellow
Write-Host "  Docker Hub:   https://hub.docker.com/r/$Username/$ImageName" -ForegroundColor Yellow
Write-Host "==========================================================" -ForegroundColor Cyan

# 1. Build Docker image
Write-Host "`n[1/2] Building Docker image..." -ForegroundColor Green
docker build -t "$FullImage" -t "$Username/${ImageName}:latest" -t "${ImageName}:latest" .
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Docker build failed. Ensure Docker Desktop is running." -ForegroundColor Red
    exit $LASTEXITCODE
}

# 2. Push to Docker Hub
Write-Host "`n[2/2] Pushing image to Docker Hub..." -ForegroundColor Green
docker push "$FullImage"
if ($Tag -ne "latest") {
    docker push "$Username/${ImageName}:latest"
}

Write-Host "`n==========================================================" -ForegroundColor Cyan
Write-Host "[SUCCESS] Image published to Docker Hub!" -ForegroundColor Green
Write-Host "Repository URL: https://hub.docker.com/r/$Username/$ImageName" -ForegroundColor Cyan
Write-Host "Demonstration Command: docker run --rm -it $FullImage demo" -ForegroundColor Yellow
Write-Host "==========================================================" -ForegroundColor Cyan
