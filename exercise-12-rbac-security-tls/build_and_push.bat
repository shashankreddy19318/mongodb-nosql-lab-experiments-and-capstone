@echo off
REM ==============================================================================
REM Helper script to build and push the MongoDB Security Lab image to Docker Hub
REM ==============================================================================

setlocal enabledelayedexpansion

echo ====================================================================
echo      MongoDB Security Lab: Docker Build & Push to Docker Hub
echo ====================================================================

set /p DOCKER_USER="Enter your Docker Hub Username: "
if "%DOCKER_USER%"=="" (
    echo [ERROR] Docker Hub username cannot be empty.
    pause
    exit /b 1
)

set IMAGE_NAME=%DOCKER_USER%/mongodb-security-lab:latest

echo.
echo [1/3] Building Docker image '%IMAGE_NAME%'...
docker build -t %IMAGE_NAME% .
if errorlevel 1 (
    echo [ERROR] Docker build failed!
    pause
    exit /b 1
)

echo.
echo [2/3] Logging in to Docker Hub (if not already logged in)...
docker login

echo.
echo [3/3] Pushing '%IMAGE_NAME%' to Docker Hub...
docker push %IMAGE_NAME%
if errorlevel 1 (
    echo [ERROR] Docker push failed! Check credentials or network connection.
    pause
    exit /b 1
)

echo.
echo ====================================================================
echo [SUCCESS] Image successfully published to Docker Hub!
echo Repository URL: https://hub.docker.com/r/%DOCKER_USER%/mongodb-security-lab
echo.
echo Grader demonstration command:
echo   docker run -it -p 27017:27017 -p 27100:27100 %IMAGE_NAME%
echo ====================================================================
pause
