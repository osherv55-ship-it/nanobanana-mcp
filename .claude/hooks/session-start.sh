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

# --- PAL customizations (survive fresh containers) ---------------------------
# 1. OpenAI: PAL strips proxy env vars, which breaks it behind the managed
#    egress proxy — re-apply the proxy patch on every fresh clone.
"$PAL_PY" "$CLAUDE_PROJECT_DIR/.claude/pal/patch-openai-proxy.py" "$PAL_DIR" || true

# 2. Model catalog: use the repo's copy (adds gpt-5.4/gpt-5.5/gpt-5.5-pro).
# 3. API keys: PAL reads $PAL_DIR/.env at startup. OPENAI_API_KEY comes from
#    the environment settings at claude.ai/code (same place as GEMINI_API_KEY);
#    fall back to a key already saved in .env so reruns don't wipe it.
PAL_OPENAI_KEY="${OPENAI_API_KEY:-}"
if [ -z "$PAL_OPENAI_KEY" ] && [ -f "$PAL_DIR/.env" ]; then
  PAL_OPENAI_KEY=$(grep -m1 '^OPENAI_API_KEY=' "$PAL_DIR/.env" | cut -d= -f2- || true)
fi
{
  echo "OPENAI_MODELS_CONFIG_PATH=$CLAUDE_PROJECT_DIR/.claude/pal/openai_models.json"
  if [ -n "$PAL_OPENAI_KEY" ]; then
    echo "OPENAI_API_KEY=$PAL_OPENAI_KEY"
  fi
} > "$PAL_DIR/.env"
chmod 600 "$PAL_DIR/.env"

if ! claude mcp get pal >/dev/null 2>&1; then
  claude mcp add pal --scope user -- "$PAL_PY" "$PAL_DIR/server.py"
fi

echo "PAL MCP server is installed and registered: clink (codex/gemini handoffs), consensus, codereview and more are available."
