$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root
if (-not (Test-Path ".venv\Scripts\python.exe")) { throw "Run scripts\setup.ps1 first." }
Write-Host "Starting YOLOv8 Grading & Metrology Backend on http://127.0.0.1:5000"
& ".\.venv\Scripts\python.exe" "backend\model_backend\api.py"
