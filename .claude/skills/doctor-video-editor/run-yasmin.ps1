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

Section "Checking API keys"
if (-not $env:ELEVENLABS_API_KEY) {
    throw "ELEVENLABS_API_KEY env var is not set. Run before invoking this script:`n  `$env:ELEVENLABS_API_KEY = '<your-key>'"
}
Note "Probing ElevenLabs key (GET /v1/user)..."
$keyOk = $false
try {
    $u = Invoke-RestMethod -Uri "https://api.elevenlabs.io/v1/user" -Headers @{"xi-api-key" = $env:ELEVENLABS_API_KEY} -ErrorAction Stop
    $tier = if ($u.subscription -and $u.subscription.tier) { $u.subscription.tier } else { "unknown" }
    Note "ElevenLabs key OK (tier: $tier)"
    $keyOk = $true
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

# Gemini is only needed when target-langs contains a language other than the
# source. For this script we default to Hebrew-only (source language) so
# Gemini becomes optional.
$useGemini = $false
$targetLangs = "he"
if ($env:GEMINI_API_KEY) {
    Note "Probing Gemini key..."
    try {
        $g = Invoke-RestMethod -Uri "https://generativelanguage.googleapis.com/v1beta/models?key=$env:GEMINI_API_KEY" -ErrorAction Stop
        Note "Gemini key OK ($(($g.models | Measure-Object).Count) models available)"
        $useGemini = $true
        $targetLangs = "he,en"
        Note "Translation enabled → target-langs = $targetLangs"
    } catch {
        Write-Warning "Gemini key is set but failed validation; skipping English translation."
    }
} else {
    Note "GEMINI_API_KEY not set — emitting Hebrew subtitles only (no translation)."
}

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

Section "Running pipeline (transcribe → cuts → trim → translate → burn-in)"
$outDir = Join-Path $desktop "yasmin_out_$tag"
node scripts\pipeline.mjs all `
    --input $videoPath `
    --out-dir $outDir `
    --source-lang he `
    --target-langs $targetLangs `
    --word-by-word `
    --crossfade 0.10 `
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
