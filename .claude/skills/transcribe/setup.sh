#!/usr/bin/env bash
# Idempotent setup for the transcribe skill: local venv with faster-whisper, yt-dlp and curl_cffi.
set -euo pipefail
cd "$(dirname "$0")"

if [ ! -x .venv/bin/python ]; then
  python3 -m venv .venv
fi
.venv/bin/pip install -q --upgrade pip
.venv/bin/pip install -q --upgrade -r requirements.txt

if ! command -v ffmpeg >/dev/null 2>&1; then
  echo "WARNING: ffmpeg not found. URL downloads that need merging and --engine elevenlabs need it (apt-get install -y ffmpeg)." >&2
fi
[ -n "${GEMINI_API_KEY:-}" ] || echo "note: GEMINI_API_KEY not set (only needed for --engine gemini / --visual)" >&2
[ -n "${ELEVENLABS_API_KEY:-}" ] || echo "note: ELEVENLABS_API_KEY not set (only needed for --engine elevenlabs)" >&2

echo "transcribe ready: .claude/skills/transcribe/.venv/bin/python .claude/skills/transcribe/scripts/transcribe.py --help"
