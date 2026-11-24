param (
    [string]$Username = "shashankreddy30",
    [string]$Tag = "latest"
)

$ImageName = "mongodb-lab18"
$FullImage = "$Username/${ImageName}:$Tag"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  Building and Pushing Lab 18 Threat Intel Demo Image" -ForegroundColor Cyan
Write-Host "  Target Image: $FullImage" -ForegroundColor Yellow
Write-Host "  Docker Hub:   https://hub.docker.com/r/$Username/$ImageName" -ForegroundColor Yellow
Write-Host "==========================================================" -ForegroundColor Cyan

# 1. Build Docker image
Write-Host "`n[1/3] Building Docker image..." -ForegroundColor Green
docker build -t "$FullImage" -t "$Username/${ImageName}:latest" -t "shashankreddy30/nosql-lab18:latest" -t "chintan/${ImageName}:latest" -t "${ImageName}:latest" .
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Docker build failed. Ensure Docker Desktop is running." -ForegroundColor Red
    exit $LASTEXITCODE
}

# 2. Push to Docker Hub
Write-Host "`n[2/3] Pushing primary image to Docker Hub..." -ForegroundColor Green
docker push "$FullImage"
docker push "shashankreddy30/nosql-lab18:latest"

Write-Host "`n==========================================================" -ForegroundColor Cyan
Write-Host "[SUCCESS] Image successfully published to Docker Hub!" -ForegroundColor Green
Write-Host "Repository URL: https://hub.docker.com/r/$Username/$ImageName" -ForegroundColor Cyan
Write-Host "Alternative:    https://hub.docker.com/r/shashankreddy30/nosql-lab18" -ForegroundColor Cyan
Write-Host "Demonstration:  docker run --rm -it $FullImage demo" -ForegroundColor Yellow
Write-Host "==========================================================" -ForegroundColor Cyan
