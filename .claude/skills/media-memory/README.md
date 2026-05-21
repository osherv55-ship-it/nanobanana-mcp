# media-memory skill

Local multimodal memory for this project. See `SKILL.md` for the operational instructions Claude follows when ingesting and searching.

## What lives where

```
.claude/skills/media-memory/
  SKILL.md              # instructions auto-loaded by Claude Code
  schema.json           # JSON Schema for a metadata record
  requirements.txt      # Python deps (google-genai, chromadb)
  scripts/
    lib.py              # shared utilities (paths, Gemini, ChromaDB)
    ingest.py           # add a file to memory
    search.py           # semantic + structured search
    list_media.py       # metadata-only listing
    reindex.py          # rebuild ChromaDB from metadata.jsonl

media-memory/           # at repo root: raw files + metadata.jsonl
.chroma/                # at repo root: ChromaDB persistent dir (gitignored)
```

## One-time setup

```bash
cd .claude/skills/media-memory
python3 -m venv .venv
.venv/bin/pip install -q -r requirements.txt
```

Set `GEMINI_API_KEY` in your environment (the same key the MCP server uses).

## Quick reference

```bash
# Ingest a file
.claude/skills/media-memory/.venv/bin/python \
  .claude/skills/media-memory/scripts/ingest.py \
  --path ./logo.png --source user_upload --tags logo,brand

# Semantic search
.claude/skills/media-memory/.venv/bin/python \
  .claude/skills/media-memory/scripts/search.py \
  --query "red logo on white background" --type image --top-k 5

# Filter-only listing
.claude/skills/media-memory/.venv/bin/python \
  .claude/skills/media-memory/scripts/list_media.py \
  --source generated --after 2026-01-01

# Rebuild the vector index
.claude/skills/media-memory/.venv/bin/python \
  .claude/skills/media-memory/scripts/reindex.py
```

## Design notes

- **Source of truth:** `media-memory/metadata.jsonl` (append-only). ChromaDB is a derived index — rebuildable via `reindex.py`.
- **Embedding model:** `gemini-embedding-001` (configurable via `MEDIA_MEMORY_EMBED_MODEL`). Gemini Embedding is text-only, so for non-text media we embed a "semantic document" = `description + extracted_text + tags`. Description and tags are auto-generated with Gemini multimodal (`gemini-2.5-flash` by default; override via `MEDIA_MEMORY_DESCRIBE_MODEL`).
- **Filtering:** Chroma's `where` clause handles `type`, `source`, and timestamp ranges. Tags are stored as a comma-separated string (Chroma metadata is scalar-only) and AND-matched in Python after the vector query — `search.py` over-fetches and post-filters so tag filtering doesn't starve results.
- **Similarity:** Chroma returns cosine distance; `search.py` converts to similarity = `1 - distance`. Strong match > 0.75, plausible 0.55–0.75.
