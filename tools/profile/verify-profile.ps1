[CmdletBinding()]
param(
    [string]$RepositoryPath = ""
)

$ErrorActionPreference = "Continue"

if ([string]::IsNullOrWhiteSpace($RepositoryPath)) {
    $RepositoryPath = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot "..\..\"))
}

$failed = $false

function Pass([string]$Message) {
    Write-Host "[PASS] $Message" -ForegroundColor Green
}

function Fail([string]$Message) {
    Write-Host "[FAIL] $Message" -ForegroundColor Red
    $script:failed = $true
}

function Warn([string]$Message) {
    Write-Host "[WARN] $Message" -ForegroundColor Yellow
}

if (Test-Path -LiteralPath (Join-Path $RepositoryPath ".git") -PathType Container) {
    Pass "Git repository detected."
}
else {
    Fail ".git directory is missing."
}

$readmePath = Join-Path $RepositoryPath "README.md"
if (-not (Test-Path -LiteralPath $readmePath -PathType Leaf)) {
    Fail "README.md is missing."
}
else {
    $readme = Get-Content -LiteralPath $readmePath -Raw

    if ($readme.Length -gt 100) { Pass "README.md contains profile content." }
    else { Fail "README.md is unexpectedly short." }

    foreach ($required in @("Kevin Cusnir", "Lirioth Teltanion", "kevincusnir@gmail.com")) {
        if ($readme.Contains($required)) {
            Pass "Required identity found: $required"
        }
        else {
            Fail "Required identity is missing: $required"
        }
    }

    if ($readme -match "kevincusnir@(?:gmail\.)?dot\s+com") {
        Fail "A written 'dot com' email typo was detected."
    }

    $matches = [regex]::Matches($readme, '(?i)(?:src\s*=\s*["'']|\]\()(?<path>\.?/?assets/[^)"''\s>]+)')
    $assetPaths = @($matches | ForEach-Object { $_.Groups["path"].Value } | Sort-Object -Unique)

    if ($assetPaths.Count -eq 0) {
        Warn "No relative assets were detected in README.md."
    }
    else {
        $missing = 0
        foreach ($relativePath in $assetPaths) {
            $normalized = $relativePath.TrimStart(".", "/").Replace("/", "\")
            $fullPath = Join-Path $RepositoryPath $normalized
            if (-not (Test-Path -LiteralPath $fullPath -PathType Leaf)) {
                Fail "Missing local asset: $relativePath"
                $missing++
            }
        }
        if ($missing -eq 0) {
            Pass "All $($assetPaths.Count) detected local README assets exist."
        }
    }
}

if (Test-Path -LiteralPath (Join-Path $RepositoryPath "AGENTS.md") -PathType Leaf) {
    Pass "AGENTS.md is available to Codex."
}
else {
    Fail "AGENTS.md is missing."
}

Write-Host ""
if ($failed) {
    Write-Host "PROFILE VERIFICATION FAILED" -ForegroundColor Red
    exit 1
}
else {
    Write-Host "PROFILE VERIFICATION PASSED" -ForegroundColor Green
    exit 0
}
