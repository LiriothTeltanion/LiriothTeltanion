[CmdletBinding()]
param(
    [string]$RepositoryPath = ""
)

$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($RepositoryPath)) {
    $RepositoryPath = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot "..\..\"))
}

$readme = Join-Path $RepositoryPath "README.md"
if (-not (Test-Path -LiteralPath $readme -PathType Leaf)) {
    throw "README.md was not found at: $readme"
}

$backupDirectory = Join-Path $RepositoryPath ".local-backups"
New-Item -ItemType Directory -Path $backupDirectory -Force | Out-Null

$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$backup = Join-Path $backupDirectory "README-$timestamp.md"
Copy-Item -LiteralPath $readme -Destination $backup -Force

Write-Host "README backup created:" -ForegroundColor Green
Write-Host $backup -ForegroundColor White
