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

# ElevenLabs key: prefer the current session, then the persistent User
# scope. If neither exists, prompt once and save permanently — you should
# never have to enter it again on this machine.
if (-not $env:ELEVENLABS_API_KEY) {
    $persisted = [Environment]::GetEnvironmentVariable("ELEVENLABS_API_KEY", "User")
    if ($persisted) {
        $env:ELEVENLABS_API_KEY = $persisted
        Note "Loaded ELEVENLABS_API_KEY from your saved user environment"
    } else {
        Section "First-time setup: ElevenLabs key"
        Write-Host "    No ElevenLabs key found in this session or your Windows user environment."
        Write-Host "    Paste your key once below (it will be saved permanently and reused forever)."
        Write-Host "    Generate one at: https://elevenlabs.io/app/settings/api-keys (needs Speech to Text scope)"
        $keyInput = Read-Host -Prompt "    ELEVENLABS_API_KEY" -AsSecureString
        $bstr = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($keyInput)
        $plain = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto($bstr)
        [System.Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr)
        if ([string]::IsNullOrWhiteSpace($plain)) { throw "No key entered. Aborting." }
        [Environment]::SetEnvironmentVariable("ELEVENLABS_API_KEY", $plain, "User")
        $env:ELEVENLABS_API_KEY = $plain
        Note "Saved to user environment — future runs will pick it up automatically."
    }
}

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
