---
name: media-memory
description: Persistent multimodal memory for media (images, video, audio, files). Use whenever the user sends a file, you generate one (e.g. via generate_image), or the user references a past asset ("the logo from last week", "that recording", "the screenshot I sent"). Stores files in media-memory/ with rich metadata and embeds each item with Gemini Embedding into a local ChromaDB. Supports semantic search and structured filtering by type, date, tags, and source.
---

# media-memory

Local multimodal memory for this project. Every image, video, audio clip, or file the user shares — or that you generate — is stored in `media-memory/`, described with Gemini, embedded with `gemini-embedding-001`, and indexed in a local ChromaDB collection. You can later recall items by meaning ("the dog photo with the red collar") or by structured filter (`type=image`, `tags includes 'logo'`, `after 2026-01-01`).

## When to use this skill

**Log on intake (always):**
- The user attaches/sends any file (image, video, audio, PDF, document).
- You generate or save any media (e.g. result of `generate_image`, an exported chart, a downloaded URL).
- The user gives you a URL to a media asset they want remembered.

**Query before assuming the asset is new:**
- The user refers to a past asset using vague language: "the one from yesterday", "that logo", "the photo of X", "the recording where I said Y".
- The user asks "do we have anything about/showing X?"
- You're about to generate or fetch something and a similar asset may already exist (avoid duplicate work).

If you're unsure whether an asset has been logged before, search first. Cheap.

## Setup (one-time, idempotent)

Before the first use in a fresh checkout, ensure the Python environment is ready:

```bash
cd .claude/skills/media-memory
python3 -m venv .venv
.venv/bin/pip install -q -r requirements.txt
```

Required env var: `GEMINI_API_KEY` (same key used by the MCP server). Optional: `MEDIA_MEMORY_EMBED_MODEL` (default `gemini-embedding-001`), `MEDIA_MEMORY_DESCRIBE_MODEL` (default `gemini-2.5-flash`).

All scripts below assume the venv. Run them as `.claude/skills/media-memory/.venv/bin/python .claude/skills/media-memory/scripts/<script>.py ...` from the repo root.

## Ingest a file

Use when a file arrives or you generate one. Stores the file in `media-memory/YYYY/MM/<uuid>_<original_name>`, writes a metadata record, embeds it, and adds to ChromaDB.

```bash
.claude/skills/media-memory/.venv/bin/python \
  .claude/skills/media-memory/scripts/ingest.py \
  --path /path/to/file.png \
  --source user_upload \
  --description "Optional human-written description. Auto-generated if omitted." \
  --tags logo,brand,red \
  --extra '{"conversation_turn": 12}'
```

Required: `--path` (or `--url` for an HTTPS URL, or `--base64` + `--filename` + `--mime-type` for inline data; or `--stdin-base64` to read base64 from stdin).
Optional: `--source` (default `unknown`), `--description`, `--tags` (comma-separated), `--extra` (JSON), `--no-embed` (skip embedding for huge files).

Outputs a JSON object with the assigned `id`, `stored_path`, and the full metadata record.

**Sources to use:** `user_upload` (file the user sent), `generated` (you produced it via a tool), `web_download` (you fetched a URL), `screenshot`, `export`, or any specific tool name (e.g. `generate_image`).

## Search

Semantic search, optionally filtered by metadata.

```bash
.claude/skills/media-memory/.venv/bin/python \
  .claude/skills/media-memory/scripts/search.py \
  --query "red logo on white background" \
  --top-k 5 \
  --type image \
  --tags logo \
  --source generated \
  --after 2026-01-01 \
  --before 2026-12-31
```

All filters are optional. `--query` is required for semantic search. Pass `--query ""` with filters only for a pure metadata listing (or use `list_media.py` for that).

Returns JSON: `{ results: [{ id, score, metadata, stored_path }, ...] }`. `score` is cosine similarity (higher = closer).

## List / filter without semantic search

```bash
.claude/skills/media-memory/.venv/bin/python \
  .claude/skills/media-memory/scripts/list_media.py \
  --type audio \
  --tags meeting,q2 \
  --after 2026-04-01 \
  --limit 20
```

## Workflow you should follow

1. **On media intake:** call `ingest.py`. Pass `--description` if you already understand the content (e.g. you just generated it with a known prompt — use the prompt). Otherwise let the script auto-describe with Gemini multimodal. Always pass meaningful `--tags` and the right `--source`.
2. **Before answering a reference to past media:** call `search.py` with a natural-language query derived from the user's words. If the top result has a high score (> ~0.7) and matches, reference it (mention the stored path and a short description). If nothing is a confident match, say so before assuming you need to regenerate.
3. **When you generate media via another tool:** save the bytes to a temp file, then `ingest.py --source generated --description "<the prompt you used>"`. Add `--extra` with the tool name and params for traceability.

## Metadata schema

See `schema.json`. Every record has: `id`, `filename`, `stored_path`, `type`, `mime_type`, `size_bytes`, `timestamp`, `source`, `description`, `extracted_text`, `tags`, `embedding_model`, `embedded`, `extra`.

`type` is one of: `image`, `video`, `audio`, `document`, `text`, `other`. The script infers it from the mime type.

## Storage layout

```
media-memory/
  metadata.jsonl          # append-only log, one JSON record per line
  2026/05/                # files organized by year/month of ingest
    <uuid>_originalname.png
    ...
.chroma/                  # ChromaDB persistent dir (gitignored)
  chroma.sqlite3
  ...
```

The JSONL log is the source of truth; ChromaDB is a derived index. If Chroma is wiped, re-run `scripts/reindex.py` to rebuild from the JSONL.

## Notes & limits

- Gemini Embedding handles text only. For non-text media we embed a synthetic "semantic document" = `description + extracted_text + tags`. Quality depends on the description, so write/generate good ones.
- Audio transcription and OCR are best-effort via Gemini multimodal (audio/PDF input). For large videos, expect long-running calls; consider chunking before ingest.
- Cosine similarity scores are not absolute. Treat > 0.75 as a strong match, 0.55–0.75 as worth surfacing, below 0.55 as probably unrelated.
