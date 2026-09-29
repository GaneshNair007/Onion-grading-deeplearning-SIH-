$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

$BundledPython = "C:\Users\Ganesh Nair\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
$Python = if (Get-Command python -ErrorAction SilentlyContinue) { "python" } elseif (Test-Path $BundledPython) { $BundledPython } else { throw "Python 3.12 is required." }

if (-not (Test-Path ".venv\Scripts\python.exe")) {
    & $Python -m venv .venv
}
& ".\.venv\Scripts\python.exe" -m pip install -r requirements.txt
Write-Host "Setup complete. Run scripts\start-demo.ps1"
