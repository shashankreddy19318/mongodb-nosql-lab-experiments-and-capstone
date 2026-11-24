@echo off
REM docker-build-push.bat
REM Automates building and pushing the Lab 14 Demonstration container to Docker Hub on Windows

setlocal enabledelayedexpansion

set DOCKERHUB_USERNAME=%1
if "%DOCKERHUB_USERNAME%"=="" (
    set DOCKERHUB_USERNAME=chintan
)

set TAG=%2
if "%TAG%"=="" set TAG=latest

set IMAGE_NAME=mongodb-lab14
set FULL_IMAGE=%DOCKERHUB_USERNAME%/%IMAGE_NAME%:%TAG%

echo ==========================================================
echo   Building and Pushing Lab 14 Demonstration Docker Image
echo   Target Image: %FULL_IMAGE%
echo   Docker Hub:   https://hub.docker.com/r/%DOCKERHUB_USERNAME%/%IMAGE_NAME%
echo ==========================================================

REM 1. Build Docker image
echo [1/2] Building Docker image...
docker build -t "%FULL_IMAGE%" -t "%DOCKERHUB_USERNAME%/%IMAGE_NAME%:latest" -t "%IMAGE_NAME%:latest" .
if %errorlevel% neq 0 (
    echo [ERROR] Docker build failed. Ensure Docker Desktop is running.
    exit /b %errorlevel%
)

REM 2. Push to Docker Hub
echo [2/2] Pushing image to Docker Hub...
echo (Ensure you have run 'docker login' beforehand)
docker push "%FULL_IMAGE%"
if "%TAG%" neq "latest" (
    docker push "%DOCKERHUB_USERNAME%/%IMAGE_NAME%:latest"
)

echo ==========================================================
echo [SUCCESS] Uploaded to Docker Hub!
echo Image URL: https://hub.docker.com/r/%DOCKERHUB_USERNAME%/%IMAGE_NAME%
echo ==========================================================
