# Validates SoX/rec + API key before opening Gemini (run in PowerShell)
$ErrorActionPreference = 'Stop'
$soxDir = 'C:\Users\rmbsa\AppData\Local\Microsoft\WinGet\Packages\ChrisBagwell.SoX_Microsoft.Winget.Source_8wekyb3d8bbwe\sox-14.4.2'
$env:AUDIODRIVER = 'waveaudio'
$env:Path = "$soxDir;$env:APPDATA\npm;$env:Path"

Write-Host '=== Voice pipeline check ===' -ForegroundColor Cyan

$recPaths = & where.exe rec 2>$null
if (-not $recPaths) { Write-Host 'FAIL: where.exe rec found nothing' -ForegroundColor Red; exit 1 }
Write-Host "OK where.exe rec:`n  $($recPaths -join "`n  ")" -ForegroundColor Green

# Gemini uses raw PCM via rec (same as test-gemini-voice-env.js), not wav files
$nodeTestEnv = Join-Path $PSScriptRoot 'test-gemini-voice-env.js'
$nodeEnvOut = node $nodeTestEnv 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "FAIL: Gemini-style mic capture:`n$nodeEnvOut" -ForegroundColor Red
    exit 1
}
Write-Host ($nodeEnvOut -join "`n") -ForegroundColor Green

$envFile = Join-Path $env:USERPROFILE '.gemini\.env'
if (-not (Test-Path $envFile)) { Write-Host 'FAIL: missing ~/.gemini/.env' -ForegroundColor Red; exit 1 }
Get-Content $envFile | ForEach-Object {
    if ($_ -match '^\s*GEMINI_API_KEY\s*=\s*(.+)\s*$') { $env:GEMINI_API_KEY = $matches[1].Trim() }
}
if (-not $env:GEMINI_API_KEY) { Write-Host 'FAIL: GEMINI_API_KEY not in .env' -ForegroundColor Red; exit 1 }
Write-Host "OK: GEMINI_API_KEY length $($env:GEMINI_API_KEY.Length)" -ForegroundColor Green

$liveTest = Join-Path $PSScriptRoot 'test-gemini-live-ws.js'
$liveLog = Join-Path $env:TEMP "gemini-live-test-$PID.log"
cmd /c "node `"$liveTest`" > `"$liveLog`" 2>&1"
$liveOut = Get-Content $liveLog -ErrorAction SilentlyContinue
Remove-Item $liveLog -Force -ErrorAction SilentlyContinue
if ($LASTEXITCODE -ne 0) {
    Write-Host 'FAIL: Gemini Live API (cloud voice backend)' -ForegroundColor Red
    $liveOut | ForEach-Object { Write-Host $_ -ForegroundColor Yellow }
    Write-Host ''
    Write-Host 'Fix: enable "Generative Language API" for the Google Cloud project that owns this API key:' -ForegroundColor Cyan
    Write-Host '  https://console.cloud.google.com/apis/library/generativelanguage.googleapis.com' -ForegroundColor White
    Write-Host 'Voice /voice UI may still open, but Space will not transcribe until this passes.' -ForegroundColor DarkGray
    exit 1
}
Write-Host ($liveOut -join "`n") -ForegroundColor Green

Write-Host ''
Write-Host 'All checks passed. Start Gemini with:' -ForegroundColor Cyan
Write-Host '  .\scripts\Launch-GeminiVoice.bat' -ForegroundColor White
Write-Host '  or:  & "$env:APPDATA\npm\gemini-voice.ps1"' -ForegroundColor White
