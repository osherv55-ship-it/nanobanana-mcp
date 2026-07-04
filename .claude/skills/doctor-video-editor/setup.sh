#!/usr/bin/env bash
set -euo pipefail

# Idempotent setup for the doctor-video-editor skill.
# Installs ffmpeg-static + ffprobe-static locally inside the skill folder
# so we don't depend on a system ffmpeg.

cd "$(dirname "$0")"

if [ ! -d node_modules ]; then
  echo "Installing npm deps for doctor-video-editor..."
  npm install --no-audit --no-fund --silent
else
  echo "node_modules already present, skipping npm install."
fi

if [ -z "${GEMINI_API_KEY:-}" ]; then
  echo "WARNING: GEMINI_API_KEY is not set. The pipeline will fail at the first Gemini call." >&2
fi

echo "Done."
