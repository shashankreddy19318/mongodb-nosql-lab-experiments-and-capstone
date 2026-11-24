# build_and_push.ps1 - PowerShell Docker Build & Push Script
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  Building Threat Intelligence LLM Platform Docker Image" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

$IMAGE_NAME = "shashankreddy19318/threat-intel-app:latest"

Write-Host ">>> Building Docker image: $IMAGE_NAME" -ForegroundColor Yellow
docker build -t $IMAGE_NAME .

if ($LASTEXITCODE -eq 0) {
    Write-Host "[OK] Docker image built successfully!" -ForegroundColor Green
    Write-Host ">>> To push to Docker Hub, run:" -ForegroundColor Cyan
    Write-Host "    docker push $IMAGE_NAME" -ForegroundColor White
} else {
    Write-Host "[ERROR] Docker build failed!" -ForegroundColor Red
}
