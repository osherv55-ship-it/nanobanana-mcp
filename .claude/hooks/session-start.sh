#!/bin/bash
# SessionStart hook for nanobanana-mcp.
#
# Prepares the workspace so a session is ready to use immediately:
#   1. Installs Node deps (so server.js is runnable for local debugging).
#   2. Creates the media-memory skill's Python venv and installs its deps,
#      so .claude/skills/media-memory is usable without any manual setup.
#
# Idempotent: re-running is a no-op when deps are already installed.

set -euo pipefail

cd "${CLAUDE_PROJECT_DIR:-$(pwd)}"

echo "[session-start] preparing nanobanana-mcp workspace..."

# --- Node dependencies (MCP server) ---
if [ -f package.json ]; then
  echo "[session-start] installing Node deps..."
  npm install --no-audit --no-fund --silent
fi

# --- Python venv for the media-memory skill ---
SKILL_DIR=".claude/skills/media-memory"
VENV_DIR="$SKILL_DIR/.venv"
REQS="$SKILL_DIR/requirements.txt"

if [ -f "$REQS" ]; then
  if [ ! -x "$VENV_DIR/bin/python" ]; then
    echo "[session-start] creating media-memory venv at $VENV_DIR..."
    python3 -m venv "$VENV_DIR"
  fi
  echo "[session-start] installing media-memory Python deps..."
  "$VENV_DIR/bin/pip" install --quiet --upgrade pip
  "$VENV_DIR/bin/pip" install --quiet -r "$REQS"

  # Ensure storage dirs exist so first ingest doesn't race.
  mkdir -p media-memory .chroma
  touch media-memory/metadata.jsonl
fi

# Warn (don't fail) if the API key isn't present — the skill needs it at runtime.
if [ -z "${GEMINI_API_KEY:-}" ] && [ -z "${GOOGLE_API_KEY:-}" ]; then
  echo "[session-start] note: GEMINI_API_KEY is not set; media-memory ingest/search will fail until it is."
fi

echo "[session-start] done."
