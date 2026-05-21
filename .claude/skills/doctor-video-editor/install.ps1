# One-shot bootstrap for the doctor-video-editor skill on Windows.
#
# Usage (paste into PowerShell):
#   iwr https://raw.githubusercontent.com/osherv55-ship-it/nanobanana-mcp/claude/doctor-video-editing-5AveU/.claude/skills/doctor-video-editor/install.ps1 | iex
#
# Or download and run with a custom target dir:
#   .\install.ps1 -TargetDir C:\Projects\nanobanana-mcp

param(
    [string]$TargetDir = (Join-Path $HOME "Projects\nanobanana-mcp"),
    [string]$Branch = "claude/doctor-video-editing-5AveU",
    [string]$RepoUrl = "https://github.com/osherv55-ship-it/nanobanana-mcp.git"
)

$ErrorActionPreference = "Stop"

function Step($msg) { Write-Host "==> $msg" -ForegroundColor Cyan }
function Ok($msg)   { Write-Host "    $msg" -ForegroundColor Green }
function Warn($msg) { Write-Host "    $msg" -ForegroundColor Yellow }

# 1. Verify prerequisites.
Step "Checking prerequisites"
foreach ($tool in @("git", "node", "npm")) {
    $found = Get-Command $tool -ErrorAction SilentlyContinue
    if (-not $found) {
        throw "$tool is not installed or not on PATH. Install it first and re-run."
    }
    Ok "$tool found: $($found.Source)"
}

$nodeVersion = (& node --version).TrimStart("v")
$major = [int]($nodeVersion.Split(".")[0])
if ($major -lt 20) {
    throw "Node.js >=20 required, found $nodeVersion. Update at https://nodejs.org"
}
Ok "Node.js $nodeVersion OK"

# 2. Clone or update the repo.
Step "Setting up repo at $TargetDir"
if (Test-Path $TargetDir) {
    if (Test-Path (Join-Path $TargetDir ".git")) {
        Ok "Repo already cloned. Fetching latest..."
        Push-Location $TargetDir
        try {
            git fetch origin --quiet
            git checkout $Branch --quiet
            git pull origin $Branch --quiet
        } finally {
            Pop-Location
        }
    } else {
        throw "Path $TargetDir exists but is not a git repo. Pick a different --TargetDir or remove it first."
    }
} else {
    New-Item -ItemType Directory -Path (Split-Path $TargetDir -Parent) -Force | Out-Null
    git clone --branch $Branch $RepoUrl $TargetDir
    Ok "Cloned $RepoUrl @ $Branch"
}

# 3. Install skill dependencies.
Step "Installing skill dependencies (ffmpeg-static, ffprobe-static)"
$skillDir = Join-Path $TargetDir ".claude\skills\doctor-video-editor"
Push-Location $skillDir
try {
    if (Test-Path "node_modules") {
        Ok "node_modules already present, skipping npm install."
    } else {
        npm install --no-audit --no-fund --silent
        Ok "Dependencies installed."
    }
} finally {
    Pop-Location
}

# 4. Set GEMINI_API_KEY persistently if missing.
Step "Checking GEMINI_API_KEY"
if (-not $env:GEMINI_API_KEY) {
    $existing = [System.Environment]::GetEnvironmentVariable("GEMINI_API_KEY", "User")
    if ($existing) {
        $env:GEMINI_API_KEY = $existing
        Ok "Found persisted GEMINI_API_KEY in user env."
    } else {
        Warn "GEMINI_API_KEY is not set. Paste your Gemini API key now (or press Enter to skip)."
        $key = Read-Host "GEMINI_API_KEY"
        if ($key) {
            [System.Environment]::SetEnvironmentVariable("GEMINI_API_KEY", $key, "User")
            $env:GEMINI_API_KEY = $key
            Ok "Saved to user environment (persists across reboots)."
        } else {
            Warn "Skipped. Set it manually before running the pipeline: `$env:GEMINI_API_KEY = '...'"
        }
    }
} else {
    Ok "GEMINI_API_KEY is already set in this session."
}

# 5. Open VS Code on the project if available.
Step "Opening VS Code"
if (Get-Command code -ErrorAction SilentlyContinue) {
    code $TargetDir
    Ok "VS Code opened on $TargetDir"
} else {
    Warn "'code' command not found on PATH. Open VS Code manually and use File -> Open Folder -> $TargetDir"
    Warn "(To enable the 'code' command: in VS Code, press Ctrl+Shift+P -> 'Shell Command: Install code command in PATH'.)"
}

Write-Host ""
Write-Host "==============================================" -ForegroundColor Green
Write-Host " Setup complete." -ForegroundColor Green
Write-Host "==============================================" -ForegroundColor Green
Write-Host ""
Write-Host "Project: $TargetDir"
Write-Host "Branch:  $Branch"
Write-Host ""
Write-Host "Next steps inside VS Code:"
Write-Host "  1. Open the Claude Code panel (Ctrl+Esc, or the Claude icon in the sidebar)."
Write-Host "  2. Ask Claude to run the doctor-video-editor pipeline on a video, e.g.:"
Write-Host "     'Run the doctor-video-editor pipeline on C:\\Users\\Osher\\Downloads\\IMG_8622.MOV,"
Write-Host "      translate to en and he, with burn-in.'"
Write-Host ""
Write-Host "Or run directly from PowerShell inside the project folder:"
Write-Host "  node .\.claude\skills\doctor-video-editor\scripts\pipeline.mjs all ``"
Write-Host "    --input <path-to-video> --out-dir .\out ``"
Write-Host "    --source-lang he --target-langs en,he --burn-in"
