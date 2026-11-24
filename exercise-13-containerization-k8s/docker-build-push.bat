@echo off
REM docker-build-push.bat
REM Automates building and pushing the Lab 13 Demonstration container to Docker Hub on Windows

setlocal enabledelayedexpansion

set DOCKERHUB_USERNAME=%1
if "%DOCKERHUB_USERNAME%"=="" (
    echo [ERROR] Please provide your Docker Hub username as the first argument.
    echo Usage:   docker-build-push.bat ^<your-dockerhub-username^> [tag]
    echo Example: docker-build-push.bat johndoe latest
    exit /b 1
)

set TAG=%2
if "%TAG%"=="" set TAG=latest

set IMAGE_NAME=mongodb-replica-k8s-lab13
set FULL_IMAGE=%DOCKERHUB_USERNAME%/%IMAGE_NAME%:%TAG%

echo ==========================================================
echo   Building and Pushing Lab 13 Demonstration Docker Image
echo   Target Image: %FULL_IMAGE%
echo   Docker Hub:   https://hub.docker.com/r/%DOCKERHUB_USERNAME%/%IMAGE_NAME%
echo ==========================================================

REM 1. Check/generate keyfile
if not exist "keyfile" (
    echo [1/3] Generating replica set keyfile...
    powershell -Command "$b = New-Object byte[] 756; (New-Object System.Security.Cryptography.RNGCryptoServiceProvider).GetBytes($b); [System.IO.File]::WriteAllText('keyfile', [Convert]::ToBase64String($b) + [Environment]::NewLine, [System.Text.Encoding]::ASCII)"
)

REM 2. Build Docker image
echo [2/3] Building Docker image...
docker build -t "%FULL_IMAGE%" -t "%DOCKERHUB_USERNAME%/%IMAGE_NAME%:latest" .
if %errorlevel% neq 0 (
    echo [ERROR] Docker build failed. Ensure Docker Desktop is running.
    exit /b %errorlevel%
)

REM 3. Push to Docker Hub
echo [3/3] Pushing image to Docker Hub...
echo (Ensure you have run 'docker login' beforehand)
docker push "%FULL_IMAGE%"
if "%TAG%" neq "latest" (
    docker push "%DOCKERHUB_USERNAME%/%IMAGE_NAME%:latest"
)

echo ==========================================================
echo [SUCCESS] Uploaded to Docker Hub!
echo Docker Hub URL: https://hub.docker.com/r/%DOCKERHUB_USERNAME%/%IMAGE_NAME%
echo Evaluator Run Command:
echo   docker run -it --rm %FULL_IMAGE%
echo ==========================================================
