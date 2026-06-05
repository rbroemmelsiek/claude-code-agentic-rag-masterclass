# Stop All Services
# Run from project root: powershell -File scripts/stop-all.ps1

if ($MyInvocation.MyCommand.Path) {
    $projectRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
} elseif ($PSScriptRoot) {
    $projectRoot = Split-Path -Parent $PSScriptRoot
} else {
    $projectRoot = Get-Location
}

Write-Host "Stopping all services..." -ForegroundColor Yellow

& "$projectRoot\scripts\stop-backend.ps1"
& "$projectRoot\scripts\stop-frontend.ps1"
& "$projectRoot\scripts\close-dev-shells.ps1" -ProjectRoot $projectRoot

Write-Host "`nAll services stopped." -ForegroundColor Green
