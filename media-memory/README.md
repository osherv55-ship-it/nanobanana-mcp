# media-memory

Persistent storage for every media asset the user shares or Claude generates in this project.

- `metadata.jsonl` — append-only log; one JSON record per ingested item. Source of truth.
- `YYYY/MM/<uuid>_<original_name>` — the raw files, organized by ingest date.

Managed by the [`media-memory` skill](../.claude/skills/media-memory/SKILL.md). The vector index lives in `.chroma/` at the repo root (gitignored) and can be rebuilt from this directory with `scripts/reindex.py`.

Both `metadata.jsonl` and the raw files are committed to git — sessions run in ephemeral cloud containers, so anything not committed and pushed is lost when the container is reclaimed. After ingesting, commit and push. If large video files start bloating the repo, move them to Git LFS.

Do not edit files in subdirectories by hand — write through the skill so the JSONL and ChromaDB stay consistent.
