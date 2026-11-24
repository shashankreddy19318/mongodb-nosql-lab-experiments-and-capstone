@echo off
setlocal
set "GIT_EXE=C:\Users\chint\AppData\Local\GitHubDesktop\app-3.5.4\resources\app\git\cmd\git.exe"
set "REPO_URL=https://github.com/shashankreddy19318/mongodb-nosql-lab-experiments-and-capstone.git"

echo =========================================================================
echo   Pushing All 18 NoSQL Labs + Capstone to GitHub
echo   Target: %REPO_URL%
echo =========================================================================
echo.
echo If prompted, sign in via the browser pop-up or enter your GitHub Personal Access Token.
echo.

cd /d "%~dp0"
"%GIT_EXE%" push -u origin main

if %ERRORLEVEL% equ 0 (
    echo.
    echo =========================================================================
    echo   [SUCCESS] All 18 Labs and Capstone have been pushed successfully!
    echo   Single Link: https://github.com/shashankreddy19318/mongodb-nosql-lab-experiments-and-capstone
    echo =========================================================================
) else (
    echo.
    echo [ERROR] Push failed. If the repository does not exist on GitHub yet, please create it at:
    echo https://github.com/new (Name: mongodb-nosql-lab-experiments-and-capstone, do NOT check README).
)

echo.
pause
