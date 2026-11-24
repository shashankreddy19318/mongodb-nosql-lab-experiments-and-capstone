@echo off
set USERNAME=shashankreddy30
set IMAGE_NAME=mongodb-lab18
set FULL_IMAGE=%USERNAME%/%IMAGE_NAME%:latest

echo ==========================================================
echo   Building and Pushing Lab 18 Threat Intel Demo Image
echo   Target Image: %FULL_IMAGE%
echo   Docker Hub:   https://hub.docker.com/r/%USERNAME%/%IMAGE_NAME%
echo ==========================================================

echo [1/3] Building Docker image...
docker build -t %FULL_IMAGE% -t %USERNAME%/%IMAGE_NAME%:latest -t shashankreddy30/nosql-lab18:latest -t chintan/%IMAGE_NAME%:latest -t %IMAGE_NAME%:latest .
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Docker build failed.
    exit /b %ERRORLEVEL%
)

echo [2/3] Pushing primary image to Docker Hub...
docker push %FULL_IMAGE%
docker push shashankreddy30/nosql-lab18:latest

echo ==========================================================
echo [SUCCESS] Image successfully published to Docker Hub!
echo Repository URL: https://hub.docker.com/r/%USERNAME%/%IMAGE_NAME%
echo Demonstration:  docker run --rm -it %FULL_IMAGE% demo
echo ==========================================================
