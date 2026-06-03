# Stop Backend Server
# Run from project root: powershell -File scripts/stop-backend.ps1

Write-Host "Stopping backend server (ports 8000, 8001)..." -ForegroundColor Yellow

$killed = $false
$ports = @(8000, 8001)

foreach ($port in $ports) {
    $netstatOutput = netstat -ano | Select-String ":$port.*LISTENING"
    if (-not $netstatOutput) { continue }

    $pids = @()
    foreach ($line in $netstatOutput) {
        $parts = ($line -split '\s+') | Where-Object { $_ }
        $procId = $parts[-1]
        if ($procId -and $procId -ne '0') { $pids += $procId }
    }

    foreach ($procId in ($pids | Select-Object -Unique)) {
        Write-Host "  Stopping PID $procId on port $port" -ForegroundColor Red
        Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue
        $killed = $true
    }
}

# Kill uvicorn/python workers for this project (handles reload parent/child pairs)
$projectMarker = "Claude-masterclass"
Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
    Where-Object {
        $_.Name -match "^python(\.exe)?$" -and $_.CommandLine -and
        ($_.CommandLine -match "uvicorn") -and ($_.CommandLine -match $projectMarker)
    } |
    ForEach-Object {
        Write-Host "  Stopping uvicorn python PID $($_.ProcessId)" -ForegroundColor Red
        Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
        $killed = $true
    }

Start-Sleep -Milliseconds 500
$stillRunning = netstat -ano | Select-String ":8000.*LISTENING|:8001.*LISTENING"
if ($stillRunning) {
    Write-Host "WARNING: Backend may still be running on 8000/8001." -ForegroundColor Red
} elseif ($killed) {
    Write-Host "Backend server stopped." -ForegroundColor Green
} else {
    Write-Host "No backend server running on port 8000/8001." -ForegroundColor Cyan
}
