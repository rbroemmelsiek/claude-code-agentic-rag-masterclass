# Close PowerShell windows opened by start-all.ps1 (and any matching stragglers).
# Called from stop-all.ps1 - not usually run directly.

param(
    [string]$ProjectRoot = ""
)

if (-not $ProjectRoot) {
    if ($PSScriptRoot) {
        $ProjectRoot = Split-Path -Parent $PSScriptRoot
    } else {
        $ProjectRoot = Get-Location
    }
}

$runDir = Join-Path $ProjectRoot ".run"
$currentPid = $PID
$closed = 0

function Stop-DevShellPid {
    param([string]$PidFile, [string]$Label)
    $path = Join-Path $runDir $PidFile
    if (-not (Test-Path $path)) { return }
    $procId = (Get-Content $path -Raw).Trim()
    Remove-Item $path -Force -ErrorAction SilentlyContinue
    if ($procId -and [int]$procId -ne $currentPid) {
        $p = Get-Process -Id $procId -ErrorAction SilentlyContinue
        if ($p) {
            Write-Host "  Closing $Label shell (PID $procId)" -ForegroundColor Red
            Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue
            $script:closed++
        }
    }
}

Write-Host "Closing dev PowerShell windows..." -ForegroundColor Yellow

if (-not (Test-Path $runDir)) {
    Write-Host "  No .run directory - nothing tracked." -ForegroundColor Gray
}

Stop-DevShellPid "dev-backend-shell.pid" "backend"
Stop-DevShellPid "dev-frontend-shell.pid" "frontend"

$escapedRoot = [regex]::Escape($ProjectRoot)
$patterns = @(
    "start-backend\.ps1",
    "start-frontend\.ps1",
    "uvicorn app\.main:app",
    "npm run dev",
    $escapedRoot
)

Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
    Where-Object { $_.Name -in @("powershell.exe", "pwsh.exe") } |
    ForEach-Object {
        $cmd = $_.CommandLine
        if (-not $cmd) { return }
        if ($_.ProcessId -eq $currentPid) { return }
        $match = $false
        foreach ($pat in $patterns) {
            if ($cmd -match $pat) { $match = $true; break }
        }
        if (-not $match) { return }
        if ($cmd -match "stop-all\.ps1|close-dev-shells\.ps1") { return }
        Write-Host "  Closing stray shell PID $($_.ProcessId)" -ForegroundColor Red
        Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
        $script:closed++
    }

if ($closed -eq 0) {
    Write-Host "  No dev PowerShell windows found." -ForegroundColor Cyan
} else {
    Write-Host ('  Closed {0} dev shells.' -f $closed) -ForegroundColor Green
}
