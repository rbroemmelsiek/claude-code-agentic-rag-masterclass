# Full Module validation — API smoke + RAG golden loop
# Run from repo root: powershell -File scripts/validate-all.ps1

param(
    [int]$Module = 1,
    [switch]$LangSmith,
    [string]$Ingestion = "",
    [string]$ManifestDir = ".agent/validation/fixtures/manifests"
)

$ErrorActionPreference = "Stop"
if ($MyInvocation.MyCommand.Path) {
    $projectRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
} else {
    $projectRoot = Get-Location
}

Set-Location $projectRoot
Write-Host "=== validate-all (module $Module) ===" -ForegroundColor Cyan

$venvPython = Join-Path $projectRoot "backend\venv\Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    Write-Host "ERROR: backend venv not found. Run backend setup first." -ForegroundColor Red
    exit 1
}

Write-Host "`n--- API smoke test ---" -ForegroundColor Yellow
& $venvPython scripts/api-smoke-test.py
$apiExit = $LASTEXITCODE

Write-Host "`n--- RAG validation ---" -ForegroundColor Yellow
$ragArgs = @(
    "scripts/rag-validation.py",
    "--manifest-dir", $ManifestDir,
    "--module", $Module,
    "--write-results", ".agent/validation/rag-latest.json"
)
if ($LangSmith) { $ragArgs += "--langsmith" }
if ($Ingestion) { $ragArgs += @("--ingestion", $Ingestion) }

& $venvPython @ragArgs
$ragExit = $LASTEXITCODE

Write-Host "`n=== validate-all complete ===" -ForegroundColor Cyan
Write-Host "API smoke exit: $apiExit"
Write-Host "RAG validation exit: $ragExit"
Write-Host "Results JSON: .agent/validation/rag-latest.json"

if ($apiExit -ne 0 -or $ragExit -ne 0) { exit 1 }
exit 0
