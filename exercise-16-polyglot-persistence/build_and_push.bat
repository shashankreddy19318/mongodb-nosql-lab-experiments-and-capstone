@echo off
set USERNAME=shashankreddy30
set IMAGE=mongodb-lab16
set TAG=latest

echo ==========================================================
echo   Building and Pushing Lab 16 Polyglot Docker Image
echo   Target: %USERNAME%/%IMAGE%:%TAG%
echo ==========================================================

docker build -t %USERNAME%/%IMAGE%:%TAG% -t %USERNAME%/%IMAGE%:latest -t shashankreddy30/nosql-lab16:latest -t chintan/%IMAGE%:latest -t %IMAGE%:latest .
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Docker build failed!
    exit /b %ERRORLEVEL%
)

docker push %USERNAME%/%IMAGE%:%TAG%
docker push shashankreddy30/nosql-lab16:latest

echo ==========================================================
echo [SUCCESS] Docker image pushed to https://hub.docker.com/r/%USERNAME%/%IMAGE%
echo ==========================================================
