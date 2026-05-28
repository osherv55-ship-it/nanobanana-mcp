# Generic doctor-video editor.
#
# Convention: put every asset for one doctor into a single folder. The script
# detects roles by filename and runs the full pipeline (cuts, overlays,
# music, subtitles, intro prefix) end-to-end.
#
# Required env var: ELEVENLABS_API_KEY (must include Speech to Text scope).
#
# Folder convention (flat):
#   <doctor-folder>/
#     main.<mov|mp4|...>          REQUIRED -- the main interview / promo clip
#     intro.<mov|mp4|...>         optional -- auto-trimmed to ~6s + role intro
#     <anything-else>.<mov|mp4>   optional -- B-roll overlays
#     before*.<jpg|png>           optional -- paired with after*.<jpg|png>
#     after*.<jpg|png>            optional
#     music.<mp3|m4a|wav|...>     optional -- background bed
#
# Output:
#   <doctor-folder>/out/final.he.mp4
#
# Usage (PowerShell):
#   $env:ELEVENLABS_API_KEY = "<key>"
#   .\edit-doctor.ps1 -Folder "C:\Users\osher\OneDrive\Desktop\doctors\yasmin"
#
# Or invoke via the one-line bootstrap if your repo is fresh:
#   $env:ELEVENLABS_API_KEY = "<key>"
#   iex (irm "https://raw.githubusercontent.com/osherv55-ship-it/nanobanana-mcp/claude/doctor-video-editing-5AveU/.claude/skills/doctor-video-editor/edit-doctor-bootstrap.ps1") -Args "<folder>"

param(
    [Parameter(Mandatory=$true, Position=0)]
    [string]$Folder
)

$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot

function Section($msg) { Write-Host ""; Write-Host "==> $msg" -ForegroundColor Cyan }
function Note($msg)    { Write-Host "    $msg" -ForegroundColor DarkGray }

Section "Resolving doctor folder"
if (-not (Test-Path $Folder)) { throw "Folder not found: $Folder" }
$Folder = (Resolve-Path $Folder).Path
Note $Folder

Section "Checking prerequisites"
foreach ($cmd in @("git", "node", "npm")) {
    if (-not (Get-Command $cmd -ErrorAction SilentlyContinue)) {
        throw "$cmd is not installed or not in PATH. Install Node.js (includes npm) and Git for Windows."
    }
    Note "$cmd ok"
}
function Test-ElevenLabsKey {
    param([string]$Key)
    if ([string]::IsNullOrWhiteSpace($Key)) { return $null }
    try {
        $r = Invoke-RestMethod -Uri "https://api.elevenlabs.io/v1/user" -Headers @{"xi-api-key" = $Key} -ErrorAction Stop
        return $r
    } catch { return $null }
}

function Get-ValidatedElevenLabsKey {
    # Try in priority: current session, persistent User env var, prompt.
    foreach ($candidate in @($env:ELEVENLABS_API_KEY, [Environment]::GetEnvironmentVariable("ELEVENLABS_API_KEY", "User"))) {
        if (-not [string]::IsNullOrWhiteSpace($candidate)) {
            $r = Test-ElevenLabsKey $candidate
            if ($r) {
                $env:ELEVENLABS_API_KEY = $candidate
                Note "ElevenLabs key OK (tier: $($r.subscription.tier))"
                return
            }
        }
    }

    # Nothing worked -- prompt and save.
    Write-Host ""
    Write-Host "    Saved ElevenLabs key is missing or no longer valid (401 unauthorized)." -ForegroundColor Yellow
    Write-Host "    Generate a fresh one with Speech-to-Text scope:" -ForegroundColor Yellow
    Write-Host "       https://elevenlabs.io/app/settings/api-keys" -ForegroundColor Yellow
    Write-Host ""
    for ($attempt = 1; $attempt -le 3; $attempt++) {
        $secure = Read-Host -Prompt "    Paste ELEVENLABS_API_KEY" -AsSecureString
        $bstr = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
        $plain = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto($bstr)
        [System.Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr)
        if ([string]::IsNullOrWhiteSpace($plain)) { Write-Warning "Empty input."; continue }
        $r = Test-ElevenLabsKey $plain
        if (-not $r) {
            Write-Warning "Key rejected by ElevenLabs (attempt $attempt of 3). Check that Speech-to-Text scope is enabled."
            continue
        }
        [Environment]::SetEnvironmentVariable("ELEVENLABS_API_KEY", $plain, "User")
        $env:ELEVENLABS_API_KEY = $plain
        Note "ElevenLabs key OK (tier: $($r.subscription.tier))"
        Note "Saved permanently to user environment -- won't ask again."
        return
    }
    throw "Failed to obtain a valid ElevenLabs key after 3 attempts."
}

Get-ValidatedElevenLabsKey

Section "Ensuring skill deps are installed"
if (-not (Test-Path "node_modules")) {
    npm install --no-audit --no-fund
} else {
    Note "node_modules already present, skipping"
}

Section "Cataloging assets"
$videos = Get-ChildItem $Folder -File | Where-Object { $_.Extension -match '\.(mp4|mov|webm|mkv|m4v|avi)$' }
$images = Get-ChildItem $Folder -File | Where-Object { $_.Extension -match '\.(jpg|jpeg|png|webp|bmp)$' }
$audios = Get-ChildItem $Folder -File | Where-Object { $_.Extension -match '\.(mp3|m4a|wav|aac|flac|ogg)$' }

# Main video: prefer a file named main.*, otherwise the largest non-intro video.
$main = $videos | Where-Object { $_.BaseName -match '^main' } | Select-Object -First 1
if (-not $main) {
    $main = $videos | Where-Object { $_.BaseName -notmatch '^intro' } | Sort-Object Length -Descending | Select-Object -First 1
}
if (-not $main) {
    throw "No main video found in $Folder.`nName it main.mov / main.mp4, or just drop the primary interview video in this folder."
}
Note "Main: $($main.Name) ($([math]::Round($main.Length/1MB, 1)) MB)"

# Intro: any file whose basename starts with 'intro'.
$intro = $videos | Where-Object { $_.BaseName -match '^intro' } | Select-Object -First 1
$introArgs = @()
if ($intro) {
    Note "Intro: $($intro.Name)"
    $introArgs = @("--intro", $intro.FullName)
}

# Music: first audio file in the folder.
$music = $audios | Select-Object -First 1
$musicArgs = @()
if ($music) {
    if ($env:DVE_MUSIC_VOLUME) {
        Note "Music: $($music.Name) @ volume $($env:DVE_MUSIC_VOLUME)"
        $musicArgs = @("--music", $music.FullName, "--music-volume", $env:DVE_MUSIC_VOLUME)
    } else {
        Note "Music: $($music.Name) (default volume + sidechain duck)"
        $musicArgs = @("--music", $music.FullName)
    }
}

# Overlay assets = everything else (other videos + all images).
$overlayFiles = @()
$overlayFiles += ($videos | Where-Object {
    $_.FullName -ne $main.FullName -and
    (-not $intro -or $_.FullName -ne $intro.FullName)
})
$overlayFiles += $images
$overlayArgs = @()
$overlayTmp = $null
if ($overlayFiles.Count -gt 0) {
    # Materialize overlay assets into an isolated subfolder so the auto-
    # manifest builder doesn't accidentally pick up main/intro/music files.
    $overlayTmp = Join-Path $Folder ".overlay_tmp"
    if (Test-Path $overlayTmp) { Remove-Item $overlayTmp -Recurse -Force }
    New-Item -ItemType Directory -Path $overlayTmp -Force | Out-Null
    foreach ($f in $overlayFiles) {
        # Prefer a hardlink (instant, zero disk). Fall back to a copy.
        try {
            New-Item -ItemType HardLink -Path (Join-Path $overlayTmp $f.Name) -Target $f.FullName -ErrorAction Stop | Out-Null
        } catch {
            Copy-Item $f.FullName -Destination (Join-Path $overlayTmp $f.Name)
        }
    }
    Note "Overlay assets staged: $($overlayFiles.Count) file(s)"
    $overlayArgs = @("--overlays", $overlayTmp)
}

$outDir = Join-Path $Folder "out"

$verticalMode = if ($env:DVE_VERTICAL) { $env:DVE_VERTICAL } else { "crop" }
Note "Vertical: $verticalMode (Reels 1080x1920; override with `$env:DVE_VERTICAL = 'off|crop|blur|fit')"

Section "Running pipeline"
try {
    node scripts\pipeline.mjs all `
        --input $main.FullName `
        --out-dir $outDir `
        --source-lang he `
        --target-langs he `
        --word-by-word `
        --crossfade 0.10 `
        --vertical-mode $verticalMode `
        @overlayArgs `
        @musicArgs `
        @introArgs `
        --burn-in
} finally {
    if ($overlayTmp -and (Test-Path $overlayTmp)) {
        Remove-Item $overlayTmp -Recurse -Force -ErrorAction SilentlyContinue
    }
}

Section "Done"
$final = Join-Path $outDir "final.he.mp4"
if (Test-Path $final) {
    Write-Host "Final video: $final" -ForegroundColor Green
    Get-ChildItem $outDir -File | Select-Object @{N="File";E={$_.Name}}, @{N="MB";E={[math]::Round($_.Length/1MB, 2)}} | Format-Table -AutoSize
    Write-Host ""
    Write-Host "Open: " -NoNewline; Write-Host "Invoke-Item '$final'" -ForegroundColor Yellow
} else {
    Write-Warning "Pipeline finished but final.he.mp4 not found in $outDir."
}
