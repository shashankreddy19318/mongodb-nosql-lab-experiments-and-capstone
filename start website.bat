@echo off
title Sentinel AI - Cyber Threat Intelligence Platform
color 0b

echo ===============================================================================
echo       Sentinel AI - Cyber Threat Intelligence ^& NoSQL Platform
echo       Author: G. Shashank Reddy (24BTRCL079)
echo ===============================================================================
echo.

:: Detect Python executable
set "PY_EXE="
if exist "%LOCALAPPDATA%\Python\pythoncore-3.14-64\python.exe" (
    set "PY_EXE=%LOCALAPPDATA%\Python\pythoncore-3.14-64\python.exe"
) else (
    where python >nul 2>&1
    if not errorlevel 1 (
        set "PY_EXE=python"
    ) else (
        where py >nul 2>&1
        if not errorlevel 1 (
            set "PY_EXE=py -3"
        )
    )
)

if "%PY_EXE%"=="" (
    echo [ERROR] Python was not found on your system!
    echo Please install Python 3.10+ or add it to your PATH.
    pause
    exit /b 1
)

:: Locate project directory containing app\chat_api.py
set "TARGET_DIR=%~dp0"
if exist "%~dp0app\chat_api.py" (
    set "TARGET_DIR=%~dp0"
) else if exist "%~dp0capstone-threat-intelligence-llm\app\chat_api.py" (
    set "TARGET_DIR=%~dp0capstone-threat-intelligence-llm"
) else if exist "c:\Users\chint\Downloads\llm model\app\chat_api.py" (
    set "TARGET_DIR=c:\Users\chint\Downloads\llm model"
)

cd /d "%TARGET_DIR%"
echo [OK] Working Directory: %TARGET_DIR%
echo [OK] Python Executable: %PY_EXE%
echo.

:: Check if server is already running on port 8000
netstat -ano | findstr /R /C:":8000 .*LISTENING" >nul 2>&1
if not errorlevel 1 (
    echo [INFO] Sentinel AI server is ALREADY RUNNING on http://localhost:8000!
) else (
    echo [STARTING] Launching FastAPI Sentinel AI backend on port 8000...
    start "Sentinel AI - Threat Intelligence Server" "%PY_EXE%" -m uvicorn app.chat_api:app --host 0.0.0.0 --port 8000
    timeout /t 3 /nobreak >nul
)

echo.
echo ===============================================================================
echo   Website URL:   http://localhost:8000
echo   API Swagger:   http://localhost:8000/docs
echo   Health Status: http://localhost:8000/health
echo ===============================================================================
echo.
echo [LAUNCHING] Opening default browser to http://localhost:8000...
start http://localhost:8000

echo.
echo Application launched! You can leave this window open or close it anytime.
echo.
pause
