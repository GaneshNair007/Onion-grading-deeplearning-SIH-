$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root
if (-not (Test-Path ".venv\Scripts\python.exe")) { throw "Run scripts\setup.ps1 first." }
& ".\.venv\Scripts\python.exe" -m uvicorn server.app:app --host 127.0.0.1 --port 8000
