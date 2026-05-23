# Self-contained Windows runner for the doctor-video-editor skill.
# Downloads Yasmin's demo clip from the YASMIN GitHub release and runs the
# full pipeline. Resolves Desktop dynamically (handles OneDrive redirects)
# and clones the repo if it isn't present.
#
# Invoke from any PowerShell prompt:
#   $env:GEMINI_API_KEY = "..."
#   $env:ELEVENLABS_API_KEY = "..."
#   iex (irm "https://raw.githubusercontent.com/osherv55-ship-it/nanobanana-mcp/claude/doctor-video-editing-5AveU/.claude/skills/doctor-video-editor/run-yasmin.ps1")

$ErrorActionPreference = "Stop"

function Section($msg) { Write-Host ""; Write-Host "==> $msg" -ForegroundColor Cyan }
function Note($msg)    { Write-Host "    $msg" -ForegroundColor DarkGray }

Section "Checking prerequisites"
foreach ($cmd in @("git", "node", "npm")) {
    if (-not (Get-Command $cmd -ErrorAction SilentlyContinue)) {
        throw "$cmd is not installed or not in PATH. Install Node.js (includes npm) and Git for Windows, then retry."
    }
    Note "$cmd ok"
}

Section "Resolving Desktop folder (OneDrive-aware)"
$desktop = [Environment]::GetFolderPath("Desktop")
if (-not (Test-Path $desktop)) {
    throw "Desktop folder not found at: $desktop"
}
Note "Desktop: $desktop"

Section "Cloning / updating repo"
$repoDir = Join-Path $desktop "nanobanana-mcp"
$branch = "claude/doctor-video-editing-5AveU"
if (-not (Test-Path $repoDir)) {
    git clone https://github.com/osherv55-ship-it/nanobanana-mcp.git $repoDir
}
Set-Location $repoDir
git fetch origin $branch
# checkout works whether or not the local branch exists yet.
git checkout -B $branch "origin/$branch"
git pull --ff-only origin $branch
Note "Repo at: $repoDir (branch $branch)"

Section "Installing skill deps (ffmpeg-static, etc.)"
$skillDir = Join-Path $repoDir ".claude\skills\doctor-video-editor"
Set-Location $skillDir
if (-not (Test-Path "node_modules")) {
    npm install --no-audit --no-fund
} else {
    Note "node_modules already present, skipping"
}

Section "Checking ElevenLabs key"
if (-not $env:ELEVENLABS_API_KEY) {
    throw "ELEVENLABS_API_KEY env var is not set. Run before invoking this script:`n  `$env:ELEVENLABS_API_KEY = '<your-key>'"
}
Note "Probing ElevenLabs key (GET /v1/user)..."
try {
    $u = Invoke-RestMethod -Uri "https://api.elevenlabs.io/v1/user" -Headers @{"xi-api-key" = $env:ELEVENLABS_API_KEY} -ErrorAction Stop
    $tier = if ($u.subscription -and $u.subscription.tier) { $u.subscription.tier } else { "unknown" }
    Note "ElevenLabs key OK (tier: $tier)"
} catch {
    $msg = $_.Exception.Message
    if ($_.Exception.Response) {
        try {
            $stream = $_.Exception.Response.GetResponseStream()
            $reader = New-Object System.IO.StreamReader($stream)
            $body = $reader.ReadToEnd()
            $msg = "$msg`n  Body: $body"
        } catch {}
    }
    throw "ElevenLabs key check failed:`n  $msg`n`nGo to https://elevenlabs.io/app/settings/api-keys, DELETE the failing key, CREATE A NEW one with 'Speech to Text' permission, then run:`n  `$env:ELEVENLABS_API_KEY = '<new key>'"
}

# Hebrew subtitles only -- no translation step, no Gemini needed.
$targetLangs = "he"

Section "Downloading Yasmin demo clip from GitHub release"
# Asset can be overridden via $env:YASMIN_VIDEO_ASSET (e.g., "IMG_9246.MOV"
# for the short clip, "IMG_9247.MOV" for the long interview). Defaults to
# the long interview since the short clip has no detectable disfluencies.
$asset = if ($env:YASMIN_VIDEO_ASSET) { $env:YASMIN_VIDEO_ASSET } else { "IMG_9247.MOV" }
$tag = [System.IO.Path]::GetFileNameWithoutExtension($asset)
$videoPath = Join-Path $desktop "yasmin_raw_$tag.mov"
if (-not (Test-Path $videoPath)) {
    $url = "https://github.com/osherv55-ship-it/nanobanana-mcp/releases/download/YASMIN/$asset"
    Note "GET $url"
    Invoke-WebRequest -Uri $url -OutFile $videoPath
} else {
    Note "Already downloaded, skipping"
}
$sizeMb = [math]::Round((Get-Item $videoPath).Length / 1MB, 1)
Note "Video: $videoPath ($sizeMb MB)"

Section "Looking for overlay assets + music + intro"
# Convention: any media files inside <Desktop>/overlay/ are auto-composed
# onto the cleaned video -- videos as B-roll, image pairs named
# before*/after* as before/after splits, other images as still B-roll.
# Files named intro.* are reserved as the prefix (introduction) clip,
# auto-trimmed to the first sentence and concatenated in front of the
# main pipeline output.
$overlayDir = Join-Path $desktop "overlay"
$overlayArgs = @()
$musicArgs = @()
$introArgs = @()
if (Test-Path $overlayDir) {
    $assets = Get-ChildItem $overlayDir -File | Where-Object {
        $_.Extension -match '\.(mp4|mov|webm|mkv|jpg|jpeg|png|webp)$' -and $_.BaseName -notmatch '^intro'
    }
    if ($assets.Count -gt 0) {
        Note "Overlay folder: $overlayDir ($($assets.Count) visual file(s))"
        $overlayArgs = @("--overlays", $overlayDir)
    } else {
        Note "Overlay folder exists but no media inside -- skipping overlays"
    }
    # Intro clip: any file whose basename starts with "intro" (case-insensitive)
    # -- Intro.mov, intro_v1.mp4, Intro-yasmin.mov, etc.
    $introFile = Get-ChildItem $overlayDir -File | Where-Object {
        $_.BaseName -match '^intro' -and $_.Extension -match '\.(mp4|mov|webm|mkv|m4v)$'
    } | Select-Object -First 1
    if ($introFile) {
        Note "Intro clip: $($introFile.Name)"
        $introArgs = @("--intro", $introFile.FullName)
    } else {
        $allMov = Get-ChildItem $overlayDir -File | Where-Object { $_.Extension -match '\.(mp4|mov|webm|mkv|m4v)$' } | ForEach-Object { $_.Name }
        if ($allMov) {
            Note ("No intro file detected. Video files in folder: " + ($allMov -join ', '))
            Note "Name a file starting with 'intro' (e.g., intro.mov) to use it as the prefix."
        }
    }
    # Background music: any audio file (mp3/m4a/wav/aac/flac/ogg) in the
    # same folder is mixed under the dialogue with sidechain ducking.
    # Default volume 0.05 (~-26 dB); override per-run with
    # $env:DVE_MUSIC_VOLUME = "0.07" for example.
    $musicFile = Get-ChildItem $overlayDir -File | Where-Object { $_.Extension -match '\.(mp3|m4a|wav|aac|flac|ogg)$' } | Select-Object -First 1
    if ($musicFile) {
        if ($env:DVE_MUSIC_VOLUME) {
            Note "Music bed: $($musicFile.Name) @ volume $($env:DVE_MUSIC_VOLUME) (overridden)"
            $musicArgs = @("--music", $musicFile.FullName, "--music-volume", $env:DVE_MUSIC_VOLUME)
        } else {
            Note "Music bed: $($musicFile.Name) (pipeline default volume + sidechain duck)"
            $musicArgs = @("--music", $musicFile.FullName)
        }
    }
} else {
    Note "No overlay folder at $overlayDir -- skipping overlays (create the folder and drop B-roll / before-after images / a music file / intro.mov to enable)"
}

Section "Running pipeline (transcribe -> cuts -> trim -> overlay -> subs -> burn-in)"
$outDir = Join-Path $desktop "yasmin_out_$tag"
# No hard-coded --aggressive or --pause-threshold here on purpose: the
# pipeline builds a per-video profile from the transcript and tunes those
# parameters to the speaker's natural rhythm. Override on the command line
# when running pipeline.mjs directly if you need to force a behavior.
node scripts\pipeline.mjs all `
    --input $videoPath `
    --out-dir $outDir `
    --source-lang he `
    --target-langs $targetLangs `
    --word-by-word `
    --crossfade 0.10 `
    @overlayArgs `
    @musicArgs `
    @introArgs `
    --burn-in

Section "Done"
Write-Host "Outputs in: $outDir" -ForegroundColor Green
if (Test-Path $outDir) {
    Get-ChildItem $outDir -Recurse -File | Select-Object @{N="File";E={$_.FullName.Substring($outDir.Length + 1)}}, @{N="MB";E={[math]::Round($_.Length/1MB, 2)}} | Format-Table -AutoSize
    $finalHe = Join-Path $outDir "final.he.mp4"
    if (Test-Path $finalHe) {
        Write-Host ""
        Write-Host "Open the final cut:" -ForegroundColor Green
        Write-Host "  Invoke-Item '$finalHe'"
    }
}
