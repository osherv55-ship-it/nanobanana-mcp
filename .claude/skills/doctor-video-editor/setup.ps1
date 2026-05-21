# Idempotent setup for the doctor-video-editor skill on Windows.
# Installs ffmpeg-static + ffprobe-static locally inside the skill folder
# so no system ffmpeg is required.
#
# Run from PowerShell (any directory):
#   powershell -ExecutionPolicy Bypass -File .\.claude\skills\doctor-video-editor\setup.ps1

$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot

if (-not (Test-Path "node_modules")) {
    Write-Host "Installing npm deps for doctor-video-editor..."
    npm install --no-audit --no-fund --silent
} else {
    Write-Host "node_modules already present, skipping npm install."
}

if (-not $env:GEMINI_API_KEY) {
    Write-Warning "GEMINI_API_KEY is not set. The pipeline will fail at the first Gemini call."
    Write-Host "Set it for this session with:"
    Write-Host "  `$env:GEMINI_API_KEY = 'your-key-here'"
    Write-Host "Or permanently via System Properties -> Environment Variables."
}

Write-Host "Done."
