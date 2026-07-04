# collage-agent

Pairs before/after treatment photos with GPT vision and composes vertical-split
collages — the `photo.jpg` overlay format the doctor-video-editor skill expects.

Use when the user asks to build before/after collages from a folder of photos
(local or downloaded from Google Drive), e.g. "תריץ את סוכן הקולאז'ים".

## How it works

1. All photos in the input folder are downscaled and sent in one vision request
   to an OpenAI model (default `gpt-5.5`).
2. The model returns strict JSON: before/after pairs plus a short Hebrew
   caption per pair (e.g. "מילוי שפתיים").
3. Pillow composes a 1600×1000 collage per pair — before on the RIGHT, after on
   the LEFT (Hebrew reading order), labels לפני/אחרי and the caption burned in.
4. Outputs `photo.jpg`, `photo2.jpg`, ... into `<input>/collages/` (or `--out`),
   ready to drop into a doctor folder.

## Setup (once per container)

```bash
uv venv /root/collage-venv
uv pip install --python /root/collage-venv/bin/python pillow python-bidi httpx
```

Requires `OPENAI_API_KEY` (env var, or read from `~/pal-mcp-server/.env`).

## Run

```bash
/root/collage-venv/bin/python .claude/skills/collage-agent/collage_agent.py <photos_dir> [--out DIR] [--model gpt-5.5]
```

## Google Drive workflow

The photos usually live in a Drive folder. Claude downloads them first via the
Google Drive MCP tools (`search_files` with `parentId = '<folder id>'`, then
`download_file_content` for each image) into a local folder, then runs the
script on that folder.

## Notes

- Pillow here has libraqm, which shapes Hebrew natively — the script detects
  this (`HAS_RAQM`) and skips manual bidi reversal to avoid double-flipping.
- Unmatched photos are reported, never force-paired.
- Per project rules, ingest produced collages into media-memory
  (`--source generated`, record model + pairing in `--extra`).
