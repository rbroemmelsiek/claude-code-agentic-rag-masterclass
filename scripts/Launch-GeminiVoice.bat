@echo off
REM Prefer PowerShell launcher (runs Live API + mic preflight). Fallback: env below + gemini.
cd /d "E:\Dev\Claude-masterclass"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0Test-VoicePipeline.ps1"
if errorlevel 1 (
  echo.
  echo Preflight failed. Fix the errors above, then run this launcher again.
  pause
  exit /b 1
)
powershell -NoProfile -ExecutionPolicy Bypass -File "%APPDATA%\npm\gemini-voice.ps1"
exit /b %ERRORLEVEL%
