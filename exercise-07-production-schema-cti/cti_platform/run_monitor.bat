@echo off
setlocal
echo ====================================================================
echo  Executing Activity 7.2: 10-Second WiredTiger Monitor & Crawler
echo ====================================================================

set PYTHON_CMD=python
if exist "C:\Users\chint\AppData\Local\Python\pythoncore-3.14-64\python.exe" (
    set PYTHON_CMD="C:\Users\chint\AppData\Local\Python\pythoncore-3.14-64\python.exe"
) else (
    where py >nul 2>&1 && set PYTHON_CMD=py
)

cd /d "%~dp0\backend"
%PYTHON_CMD% monitor_wiredtiger_threats.py --interval 10
pause
