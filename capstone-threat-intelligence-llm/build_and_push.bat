@echo off
echo ==========================================================
echo   Building Threat Intelligence LLM Platform Docker Image
echo ==========================================================

set IMAGE_NAME=shashankreddy19318/threat-intel-app:latest

echo >>> Building Docker image: %IMAGE_NAME%
docker build -t %IMAGE_NAME% .

if %ERRORLEVEL% equ 0 (
    echo [OK] Docker image built successfully!
    echo >>> To push to Docker Hub, run:
    echo     docker push %IMAGE_NAME%
) else (
    echo [ERROR] Docker build failed!
)
pause
