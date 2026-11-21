# Route Resilience - Interactive Web Trial Server Launcher (PowerShell)
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

$PythonPath = "$env:LOCALAPPDATA\Programs\Python\Python313\python.exe"
if (-not (Test-Path $PythonPath)) {
    $cmd = Get-Command python -ErrorAction SilentlyContinue
    if ($cmd) { $PythonPath = $cmd.Source }
}

Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "ROUTE RESILIENCE: 3D NON-STOP FLOW & AERIAL REPORT GENERATOR" -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "Using Python : $PythonPath" -ForegroundColor Gray
Write-Host "Server URL   : http://localhost:8000" -ForegroundColor Green
Write-Host "Opening your browser..." -ForegroundColor Yellow

Start-Process "http://localhost:8000"
& $PythonPath app.py
