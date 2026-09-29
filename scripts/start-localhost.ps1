$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

$Python = ".\.venv\Scripts\python.exe"
if (-not (Test-Path $Python)) {
    $Python = "python"
}

Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host "  🧅 Launching Unified Onion Grading System on Localhost..." -ForegroundColor Green
Write-Host "========================================================================" -ForegroundColor Cyan

& $Python "run_localhost.py"
