# Idempotent setup for the transcribe skill on Windows: local venv with faster-whisper, yt-dlp and curl_cffi.
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

if (-not (Test-Path ".venv\Scripts\python.exe")) {
  python -m venv .venv
}
& .venv\Scripts\python.exe -m pip install -q --upgrade pip
& .venv\Scripts\python.exe -m pip install -q --upgrade -r requirements.txt

if (-not (Get-Command ffmpeg -ErrorAction SilentlyContinue)) {
  Write-Warning "ffmpeg not found. URL downloads that need merging and --engine elevenlabs need it (winget install Gyan.FFmpeg)."
}
Write-Host "transcribe ready: .claude\skills\transcribe\.venv\Scripts\python.exe .claude\skills\transcribe\scripts\transcribe.py --help"
