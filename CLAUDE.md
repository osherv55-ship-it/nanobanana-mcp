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

## Clothing shopping agent

`shop_for_clothes` (in `server.js`) is a style-aware shopping stylist tool. It wraps
Perplexity Sonar with a stylist persona and returns a shortlist of concrete,
purchasable items (direct product links, prices, styling notes). It **discovers and
recommends** — it never places orders or touches payment.

Run the agent as a three-part loop, not a single tool call:

1. **Remember the style.** Before shopping, query media-memory (`search.py`) for the
   user's style profile and any inspo images they sent. When the user states new
   preferences or sends inspiration shots, log them with `ingest.py`
   (`--tags style-profile`) so the taste persists across sessions. Feed what you find
   into the tool's `style_preferences` argument.
2. **Find the clothes.** Call `shop_for_clothes` with `request` plus as many of
   `style_preferences`, `budget`, `sizes`, `gender`, `region`, `occasion`, `avoid` as
   you know. Pass `search_domain_filter` to focus on (or exclude) specific retailers.
3. **Visualize the look.** Use `generate_image` to render a mood board or an outfit
   mockup from the shortlist, then log the output to media-memory (`--source generated`).
   If the user shares a photo of themselves, `edit_image` can preview a piece on them.

Be honest about limits: prices/stock/links come from Sonar and must be verified at
checkout; the agent cannot complete a purchase.

## Code conventions

- Node 20+, ESM (`"type": "module"`). Match `server.js` style: top-level async helpers, small focused functions, env-var config block at top.
- The MCP server is **stateless** — one `Server` instance per HTTP request. Don't add cross-request shared state without a deliberate reason.
- All long-running external API calls (Gemini, Perplexity) should have timeouts and surface API error bodies in the thrown message.
- Keep tool descriptions in `ListToolsRequestSchema` honest and concrete — they're prompts to the calling model.

## Git

- Work on the branch the session opened on; never push to `main` directly.
- Confirm with the user before any destructive git operation.
