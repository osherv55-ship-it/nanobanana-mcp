# media-memory

Persistent storage for every media asset the user shares or Claude generates in this project.

- `metadata.jsonl` — append-only log; one JSON record per ingested item. Source of truth.
- `YYYY/MM/<uuid>_<original_name>` — the raw files, organized by ingest date.

Managed by the [`media-memory` skill](../.claude/skills/media-memory/SKILL.md). The vector index lives in `.chroma/` at the repo root (gitignored) and can be rebuilt from this directory with `scripts/reindex.py`.

Do not edit files in subdirectories by hand — write through the skill so the JSONL and ChromaDB stay consistent.
