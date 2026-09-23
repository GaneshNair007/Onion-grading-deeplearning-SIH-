$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root
if (-not (Test-Path ".venv\Scripts\python.exe")) { throw "Run scripts\setup.ps1 first." }
$Temp = Join-Path $Root ".test-tmp-final"
& ".\.venv\Scripts\python.exe" -m pytest -q --basetemp $Temp -p no:cacheprovider
