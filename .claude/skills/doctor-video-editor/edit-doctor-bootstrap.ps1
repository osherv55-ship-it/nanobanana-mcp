# Bootstrap for edit-doctor.ps1 — clones/updates the repo, then runs the
# generic doctor-video editor against $env:DOCTOR_FOLDER.
#
# Usage (PowerShell):
#   $env:ELEVENLABS_API_KEY = "<key>"
#   $env:DOCTOR_FOLDER = "C:\Users\osher\OneDrive\Desktop\doctors\yasmin"
#   iex (irm "https://raw.githubusercontent.com/osherv55-ship-it/nanobanana-mcp/claude/doctor-video-editing-5AveU/.claude/skills/doctor-video-editor/edit-doctor-bootstrap.ps1")

$ErrorActionPreference = "Stop"

function Section($msg) { Write-Host ""; Write-Host "==> $msg" -ForegroundColor Cyan }
function Note($msg)    { Write-Host "    $msg" -ForegroundColor DarkGray }

if (-not $env:DOCTOR_FOLDER) {
    throw "Set `$env:DOCTOR_FOLDER first to the folder containing the doctor's assets.`nExample:`n  `$env:DOCTOR_FOLDER = 'C:\Users\osher\OneDrive\Desktop\doctors\yasmin'"
}
if (-not (Test-Path $env:DOCTOR_FOLDER)) {
    throw "Doctor folder does not exist: $env:DOCTOR_FOLDER"
}

# Key handling (load saved / prompt + persist on first use, retry on 401)
# lives inside edit-doctor.ps1 — single source of truth.

Section "Locating repo workspace"
$desktop = [Environment]::GetFolderPath("Desktop")
$repoDir = Join-Path $desktop "nanobanana-mcp"
$branch = "claude/doctor-video-editing-5AveU"

if (-not (Test-Path $repoDir)) {
    Note "Cloning repo to $repoDir"
    git clone https://github.com/osherv55-ship-it/nanobanana-mcp.git $repoDir
} else {
    Note "Repo at $repoDir"
}
Set-Location $repoDir
git fetch origin $branch
git checkout -B $branch "origin/$branch"
git pull --ff-only origin $branch

Set-Location (Join-Path $repoDir ".claude\skills\doctor-video-editor")
& ".\edit-doctor.ps1" -Folder $env:DOCTOR_FOLDER
