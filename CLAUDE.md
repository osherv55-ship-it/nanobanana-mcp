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

The skill scripts live at `.claude/skills/media-memory/scripts/`. The skill's `SKILL.md` documents the exact CLI for `ingest.py`, `search.py`, `list_media.py`, and `reindex.py`. Use the venv at `.claude/skills/media-memory/.venv/bin/python`.

The `.claude/hooks/session-start.sh` SessionStart hook auto-provisions the venv and installs deps at the start of every session — no manual setup needed on a fresh checkout.

Required env var: `GEMINI_API_KEY` (same key the MCP server uses).

### Reusing the skill in a new project

To activate this skill on a different repo:

1. Copy `.claude/skills/media-memory/` and `.claude/hooks/session-start.sh` into the target repo.
2. Merge the `hooks` block from `.claude/settings.json` into the target's `.claude/settings.json` (create it if absent).
3. Add the `.gitignore` entries: `.chroma/`, `.claude/skills/media-memory/.venv/`, and the `media-memory/**` allowlist block.
4. Copy this "Multimodal memory" section into the target's `CLAUDE.md` so Claude knows to log/query.
5. Ensure `GEMINI_API_KEY` is available in that project's environment.

The hook will create the venv and storage dirs on first session start; the skill is then ready to use.

## Code conventions

- Node 20+, ESM (`"type": "module"`). Match `server.js` style: top-level async helpers, small focused functions, env-var config block at top.
- The MCP server is **stateless** — one `Server` instance per HTTP request. Don't add cross-request shared state without a deliberate reason.
- All long-running external API calls (Gemini, Perplexity) should have timeouts and surface API error bodies in the thrown message.
- Keep tool descriptions in `ListToolsRequestSchema` honest and concrete — they're prompts to the calling model.

## Git

- Work on the branch the session opened on; never push to `main` directly.
- Confirm with the user before any destructive git operation.
