@echo off
set USERNAME=shashankreddy30
set IMAGE=mongodb-lab15
set TAG=latest

echo ==========================================================
echo   Building and Pushing Lab 15 Multi-Tenant SaaS Demo Image
echo   Target Image: %USERNAME%/%IMAGE%:%TAG%
echo   Docker Hub:   https://hub.docker.com/r/%USERNAME%/%IMAGE%
echo ==========================================================

docker build -t %USERNAME%/%IMAGE%:%TAG% -t %USERNAME%/%IMAGE%:latest -t shashankreddy30/nosql-lab15:latest -t chintan/%IMAGE%:latest -t %IMAGE%:latest .
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Docker build failed.
    exit /b %ERRORLEVEL%
)

docker push %USERNAME%/%IMAGE%:%TAG%
docker push shashankreddy30/nosql-lab15:latest

echo ==========================================================
echo [SUCCESS] Published to Docker Hub!
echo URL: https://hub.docker.com/r/%USERNAME%/%IMAGE%
echo Run: docker run --rm -it %USERNAME%/%IMAGE%:%TAG% demo
echo ==========================================================
