$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root
if (-not (Test-Path ".venv\Scripts\python.exe")) { throw "Run scripts\setup.ps1 first." }
Write-Host "ONION-Q will be available at http://127.0.0.1:8000/dashboard/app/scan.html"
$Backend = Start-Process -FilePath ".\.venv\Scripts\python.exe" `
    -ArgumentList "-m", "uvicorn", "server.app:app", "--host", "127.0.0.1", "--port", "8000" `
    -WorkingDirectory $Root -WindowStyle Hidden -PassThru
for ($Attempt = 0; $Attempt -lt 30; $Attempt++) {
    try {
        $Health = Invoke-RestMethod "http://127.0.0.1:8000/health" -TimeoutSec 1
        if ($Health.status -eq "ok") { break }
    } catch { Start-Sleep -Milliseconds 500 }
}
if ($Health.status -ne "ok") {
    Stop-Process -Id $Backend.Id -ErrorAction SilentlyContinue
    throw "Backend did not become healthy. Run scripts\start-backend.ps1 to see its logs."
}
Start-Process "http://127.0.0.1:8000/dashboard/app/scan.html"
Write-Host "Backend running as process $($Backend.Id)."
