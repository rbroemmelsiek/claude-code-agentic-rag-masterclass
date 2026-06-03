# Start All Services
# Run from project root: powershell -File scripts/start-all.ps1
# This opens two new terminal windows for backend and frontend

# Determine project root
if ($MyInvocation.MyCommand.Path) {
    $projectRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
} elseif ($PSScriptRoot) {
    $projectRoot = Split-Path -Parent $PSScriptRoot
} else {
    $projectRoot = Get-Location
}

Write-Host "Starting all services..." -ForegroundColor Green
Write-Host "Project root: $projectRoot" -ForegroundColor Gray

$runDir = Join-Path $projectRoot ".run"
New-Item -ItemType Directory -Force -Path $runDir | Out-Null

# Start backend in new window (track shell PID for stop-all)
$backendShell = Start-Process powershell -PassThru -ArgumentList @(
    "-NoExit",
    "-Command",
    "Set-Location '$projectRoot'; & '.\scripts\start-backend.ps1'"
)
$backendShell.Id | Out-File -FilePath (Join-Path $runDir "dev-backend-shell.pid") -Encoding ascii -NoNewline

# Brief pause to stagger startup
Start-Sleep -Milliseconds 500

# Start frontend in new window (track shell PID for stop-all)
$frontendShell = Start-Process powershell -PassThru -ArgumentList @(
    "-NoExit",
    "-Command",
    "Set-Location '$projectRoot'; & '.\scripts\start-frontend.ps1'"
)
$frontendShell.Id | Out-File -FilePath (Join-Path $runDir "dev-frontend-shell.pid") -Encoding ascii -NoNewline

Write-Host "Services starting in separate windows:" -ForegroundColor Cyan
Write-Host "  Backend:  http://localhost:8000" -ForegroundColor Yellow
Write-Host "  Frontend: http://localhost:5173" -ForegroundColor Yellow
