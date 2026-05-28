# Scaffolds an empty doctor folder with a README documenting the asset
# convention, so future runs always know what file names to use.
#
# Usage:
#   .\new-doctor-folder.ps1 -Name "etty"
#       -> creates <Desktop>\doctors\etty\ with a README.txt inside.
#   .\new-doctor-folder.ps1 -Name "etty" -Parent "D:\videos"
#       -> creates D:\videos\etty\ instead.

param(
    [Parameter(Mandatory=$true, Position=0)]
    [string]$Name,

    [Parameter(Position=1)]
    [string]$Parent
)

$ErrorActionPreference = "Stop"

if (-not $Parent) {
    $desktop = [Environment]::GetFolderPath("Desktop")
    $Parent = Join-Path $desktop "doctors"
}
if (-not (Test-Path $Parent)) {
    New-Item -ItemType Directory -Path $Parent -Force | Out-Null
}

$folder = Join-Path $Parent $Name
if (Test-Path $folder) {
    Write-Warning "Folder already exists: $folder"
} else {
    New-Item -ItemType Directory -Path $folder | Out-Null
    Write-Host "Created: $folder" -ForegroundColor Green
}

$readme = Join-Path $folder "README.txt"
$readmeBody = @"
Doctor video -- asset convention
================================

Drop the doctor's assets directly into this folder using the names below.
The pipeline detects roles by filename -- you only need the bits you have.

  main.mov         REQUIRED -- the main interview / promo clip
  intro.mov        optional -- short clip; auto-trimmed to name + role intro
  b-roll.mov       optional -- B-roll #1 (any non-main video name works)
  b-roll2.mov      optional -- B-roll #2
  photo.jpg        optional -- before/after collage shown as overlay
  photo2.jpg       optional -- second collage
  music.mp3        optional -- background bed (any audio extension is fine)
  corrections.txt  optional -- name / term corrections, one rule per line
                              (e.g.  Lermer|Lerner   -- fixes ASR mishears)

When the assets are in place, run from PowerShell:

  `$env:DOCTOR_FOLDER = "$folder"
  iex (irm "https://raw.githubusercontent.com/osherv55-ship-it/nanobanana-mcp/claude/doctor-video-editing-5AveU/.claude/skills/doctor-video-editor/edit-doctor-bootstrap.ps1")

Output lands in:  out\final.he.mp4

Make sure `$env:ELEVENLABS_API_KEY` is set in your user environment with
the Speech-to-Text scope. The pipeline picks the rest automatically.
"@

Set-Content -Path $readme -Value $readmeBody -Encoding UTF8
Write-Host "Wrote: $readme" -ForegroundColor DarkGray

Write-Host ""
Write-Host "Drop assets into:" -ForegroundColor Cyan
Write-Host "  $folder"
Write-Host ""
Write-Host "Then run:" -ForegroundColor Cyan
Write-Host "  `$env:DOCTOR_FOLDER = `"$folder`""
Write-Host "  iex (irm `"https://raw.githubusercontent.com/osherv55-ship-it/nanobanana-mcp/claude/doctor-video-editing-5AveU/.claude/skills/doctor-video-editor/edit-doctor-bootstrap.ps1`")"
