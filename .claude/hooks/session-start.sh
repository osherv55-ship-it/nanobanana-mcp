#!/bin/bash
set -euo pipefail

# SessionStart hook for Claude Code on the web.
# 1. Installs repo npm dependencies so tests can run.
# 2. Installs and registers the PAL MCP server (clink/consensus/codereview)
#    so remote sessions get the same multi-model team as the local machine.

if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

# --- Repo dependencies -------------------------------------------------------
if [ -f "$CLAUDE_PROJECT_DIR/package.json" ]; then
  (cd "$CLAUDE_PROJECT_DIR" && npm install --no-audit --no-fund)
fi

# --- PAL MCP server ----------------------------------------------------------
# PAL refuses to start without at least one model API key, so skip cleanly
# when the environment doesn't provide one.
if [ -z "${GEMINI_API_KEY:-}" ]; then
  echo "PAL skipped: GEMINI_API_KEY is not set in this environment (add it in the claude.ai/code environment settings)."
  exit 0
fi

PAL_DIR="$HOME/pal-mcp-server"
PAL_PY="$PAL_DIR/.pal_venv/bin/python"

if [ ! -d "$PAL_DIR" ]; then
  git clone --depth 1 https://github.com/BeehiveInnovations/pal-mcp-server.git "$PAL_DIR"
fi

if [ ! -x "$PAL_PY" ]; then
  if command -v uv >/dev/null 2>&1; then
    uv venv "$PAL_DIR/.pal_venv"
    uv pip install --python "$PAL_PY" -r "$PAL_DIR/requirements.txt"
  else
    python3 -m venv "$PAL_DIR/.pal_venv"
    "$PAL_PY" -m pip install --quiet -r "$PAL_DIR/requirements.txt"
  fi
fi

if ! claude mcp get pal >/dev/null 2>&1; then
  claude mcp add pal --scope user -- "$PAL_PY" "$PAL_DIR/server.py"
fi

echo "PAL MCP server is installed and registered: clink (codex/gemini handoffs), consensus, codereview and more are available."
