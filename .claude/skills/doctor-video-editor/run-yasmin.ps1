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
if (-not $env:GEMINI_API_KEY) {
    throw "GEMINI_API_KEY env var is not set. Set it in the same PowerShell session before running:`n  `$env:GEMINI_API_KEY = '<your-key>'"
}
Note "GEMINI_API_KEY: set"
if (-not $env:ELEVENLABS_API_KEY) {
    Write-Warning "ELEVENLABS_API_KEY not set — pipeline will fall back to Gemini-only transcription (less precise on Hebrew fillers + no diarization)."
} else {
    Note "ELEVENLABS_API_KEY: set (ElevenLabs Scribe will be used)"
}

Section "Downloading Yasmin demo clip from GitHub release"
$videoPath = Join-Path $desktop "yasmin_raw.mov"
if (-not (Test-Path $videoPath)) {
    $url = "https://github.com/osherv55-ship-it/nanobanana-mcp/releases/download/YASMIN/IMG_9246.MOV"
    Note "GET $url"
    Invoke-WebRequest -Uri $url -OutFile $videoPath
} else {
    Note "Already downloaded, skipping"
}
$sizeMb = [math]::Round((Get-Item $videoPath).Length / 1MB, 1)
Note "Video: $videoPath ($sizeMb MB)"

Section "Running pipeline (transcribe → cuts → trim → translate → burn-in)"
$outDir = Join-Path $desktop "yasmin_out"
node scripts\pipeline.mjs all `
    --input $videoPath `
    --out-dir $outDir `
    --source-lang he `
    --target-langs he,en `
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
