# push_all_experiments.ps1 - Automated GitHub Push Helper for shashankreddy19318
param(
    [string]$GitHubUser = "shashankreddy19318",
    [string]$Token = ""
)

$gitExe = "C:\Users\chint\AppData\Local\GitHubDesktop\app-3.5.4\resources\app\git\cmd\git.exe"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  GitHub Push Helper for $GitHubUser" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# 1. Push Threat Intelligence Capstone
$capstoneDir = "C:\Users\chint\Downloads\llm model"
Write-Host "`n>>> [1/2] Processing Capstone Threat Intelligence Project..." -ForegroundColor Yellow
Set-Location -Path $capstoneDir

$remoteUrl = "https://github.com/$GitHubUser/threat-intelligence-nosql-llm.git"
if ($Token -ne "") {
    $remoteUrl = "https://$($GitHubUser):$($Token)@github.com/$GitHubUser/threat-intelligence-nosql-llm.git"
}

& $gitExe remote set-url origin $remoteUrl
Write-Host "Pushed to: $remoteUrl" -ForegroundColor Green
Write-Host "Executing git push -u origin main..." -ForegroundColor White
& $gitExe push -u origin main

Write-Host "`n==========================================================" -ForegroundColor Cyan
Write-Host "  Push complete! Check: https://github.com/$GitHubUser" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan
