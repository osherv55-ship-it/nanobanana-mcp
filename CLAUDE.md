# CLAUDE.md

Project memory for this repo. Loaded into every Claude Code session.

## Project

`nanobanana-mcp` — a remote MCP server (Node 20+, Express) exposing Google's Nano Banana (Gemini Flash Image) as `generate_image` / `edit_image`, plus Perplexity Sonar deep research as `deep_research`. Deployed to Cloud Run via the Dockerfile. Source lives in `server.js` (stateless, one MCP server per request).

## Multimodal memory — required behavior

This project has a persistent multimodal memory system. Every image, video, audio clip, or file the user sends, or that you generate, must be logged. When the user refers to a past asset, query the memory before assuming you need to recreate or re-ask.

Skill: `.claude/skills/media-memory/SKILL.md` (read it for command details and edge cases).

### Always log

Call `ingest.py` whenever any of these happen:
- The user attaches or sends a file in the conversation (image, video, audio, PDF, document, etc.).
- You produce media — including outputs of `generate_image`, `edit_image`, any chart/diagram you write to disk, or files you download from a URL.
- The user gives you a URL to a media asset they want remembered.

Use the right `--source`:
- `user_upload` — user-attached file
- `generated` — produced by a tool call (also set `--extra` to record the tool name and params)
- `web_download` — you fetched it from a URL
- `screenshot`, `export`, etc. — be specific

Provide `--description` when you already know the content (e.g. the prompt you used to generate it). Otherwise let the script auto-describe with Gemini multimodal. Always pass meaningful `--tags`.

### Always query before assuming an asset is new

Call `search.py` when the user references past media with vague language ("the logo from last week", "that recording", "the screenshot I sent you"), asks "do we have anything about/showing X?", or when you're about to generate something a previous asset may already cover.

Treat cosine similarity > 0.75 as a strong match, 0.55–0.75 as worth surfacing to the user, below 0.55 as probably unrelated.

### How to invoke

The skill scripts live at `.claude/skills/media-memory/scripts/`. The skill's `SKILL.md` documents the exact CLI for `ingest.py`, `search.py`, `list_media.py`, and `reindex.py`. Use the venv at `.claude/skills/media-memory/.venv/bin/python`. On a fresh checkout, run the one-time setup block in `SKILL.md`.

Required env var: `GEMINI_API_KEY` (same key the MCP server uses).

## Doctor video editor — standard workflow

The `doctor-video-editor` skill (at `.claude/skills/doctor-video-editor/`) is the
permanent way to edit doctor promo / testimonial videos. The user maintains a
**one-folder-per-doctor** convention. Whenever the user references a doctor
by name (Yasmin, ETTY, etc.) or asks to "edit a doctor video", assume this
layout and the bootstrap entry point unless told otherwise.

### Folder convention (flat, one per doctor)

```
<doctor-name>/
  main.mov           REQUIRED — the main interview / promo clip
  intro.mov          optional — auto-trimmed to ~6s (name + role intro)
  b-roll.mov         optional — B-roll #1 (any non-main video name works)
  b-roll2.mov        optional — B-roll #2
  photo.jpg          optional — before/after collage shown as overlay
  photo2.jpg         optional — second collage
  music.mp3          optional — background bed with sidechain ducking
```

Role detection is automatic by filename prefix: `main*` is the main video,
`intro*` is the prefix clip (auto-trimmed to the doctor's role intro),
`before*` matched with `after*` becomes a vertical-split before/after, every
other image / video file becomes a still or B-roll overlay distributed evenly
across the cleaned timeline. The first audio file becomes the music bed.

### Invocation

```powershell
$env:DOCTOR_FOLDER = "C:\Users\osher\OneDrive\...\<doctor-name>"
iex (irm "https://raw.githubusercontent.com/osherv55-ship-it/nanobanana-mcp/claude/doctor-video-editing-5AveU/.claude/skills/doctor-video-editor/edit-doctor-bootstrap.ps1")
```

Output: `<doctor-folder>/out/final.he.mp4`. `ELEVENLABS_API_KEY` (Speech-to-Text
scope) must be set in the user environment. If the user mentions an asset is
missing (no intro / no music / etc.), the pipeline skips that step gracefully —
never block on a missing optional piece.

A `new-doctor-folder.ps1` helper scaffolds an empty folder with a README that
documents the convention. Suggest it when the user is starting on a new doctor.

## Code conventions

- Node 20+, ESM (`"type": "module"`). Match `server.js` style: top-level async helpers, small focused functions, env-var config block at top.
- The MCP server is **stateless** — one `Server` instance per HTTP request. Don't add cross-request shared state without a deliberate reason.
- All long-running external API calls (Gemini, Perplexity) should have timeouts and surface API error bodies in the thrown message.
- Keep tool descriptions in `ListToolsRequestSchema` honest and concrete — they're prompts to the calling model.

## Git

- Work on the branch the session opened on; never push to `main` directly.
- Confirm with the user before any destructive git operation.
