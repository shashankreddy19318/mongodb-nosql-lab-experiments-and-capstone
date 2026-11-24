<#
.SYNOPSIS
    Generates a secure 756-byte keyfile for MongoDB Replica Set authentication on Windows.
#>
param(
    [string]$Path = "$PSScriptRoot\keyfile"
)

$bytes = New-Object byte[] 756
$rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
$rng.GetBytes($bytes)
$base64 = [Convert]::ToBase64String($bytes)
# Write raw string with ASCII encoding (no BOM, UNIX LF)
[System.IO.File]::WriteAllText($Path, $base64.Trim() + "`n", [System.Text.Encoding]::ASCII)

Write-Host "[OK] Keyfile generated at: $Path ($((Get-Item $Path).Length) bytes)"
