# Stop Frontend Server
# Run from project root: powershell -File scripts/stop-frontend.ps1

Write-Host "Stopping frontend server (port 5173)..." -ForegroundColor Yellow

$killed = $false
$netstatOutput = netstat -ano | Select-String ":5173.*LISTENING"

if ($netstatOutput) {
    $pids = @()
    foreach ($line in $netstatOutput) {
        $parts = ($line -split '\s+') | Where-Object { $_ }
        $procId = $parts[-1]
        if ($procId -and $procId -ne '0') { $pids += $procId }
    }

    foreach ($procId in ($pids | Select-Object -Unique)) {
        Write-Host "  Stopping PID $procId" -ForegroundColor Red
        Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue
        $killed = $true
    }
}

Start-Sleep -Milliseconds 500
$stillRunning = netstat -ano | Select-String ":5173.*LISTENING"
if ($stillRunning) {
    Write-Host "WARNING: Frontend may still be running." -ForegroundColor Red
} elseif ($killed) {
    Write-Host "Frontend server stopped." -ForegroundColor Green
} else {
    Write-Host "No frontend server running on port 5173." -ForegroundColor Cyan
}
