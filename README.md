# nanobanana-mcp

Remote [MCP](https://modelcontextprotocol.io) server (Node 20+, Express, stateless) exposing:

| Tool | Backend | What it does |
|---|---|---|
| `generate_image` | Google Nano Banana (Gemini Flash Image) | Text-to-image. Supports Hebrew prompts, aspect ratios, 512–4K output. |
| `edit_image` | Google Nano Banana | Image-to-image editing from an HTTPS URL or inline base64. |
| `gpt_image_generate` | OpenAI `gpt-image-2` | Text-to-image via the OpenAI API. Strong at text-in-image and complex compositions. Per-image cost. |
| `gpt_image_edit` | OpenAI `gpt-image-2` | Multi-image editing/composition with optional mask. Per-call cost. |
| `deep_research` | Perplexity `sonar-deep-research` | Slow (30s+) multi-source web research with citations. |

## Environment variables

| Variable | Required | Default | Purpose |
|---|---|---|---|
| `GEMINI_API_KEY` | yes | — | Google AI Studio key for image generation/editing. |
| `MCP_AUTH_TOKEN` | recommended | none (unauthenticated!) | Bearer token required on `/mcp`. |
| `PERPLEXITY_API_KEY` | for `deep_research` | — | Perplexity API key; only needed when the tool is called. |
| `OPENAI_API_KEY` | for `gpt_image_*` | — | OpenAI API key; only needed when those tools are called. |
| `OPENAI_IMAGE_MODEL` | no | `gpt-image-2-2026-04-21` | Override the OpenAI image model. |
| `OPENAI_TIMEOUT_MS` | no | `180000` | Abort OpenAI image calls after this many ms. |
| `ALLOW_LOCAL_FILES` | no | `false` | Allow file:// / local-path image inputs (only for self-hosted local servers). |
| `GEMINI_IMAGE_MODEL` | no | `gemini-3.1-flash-image-preview` | Override the image model. |
| `GEMINI_TIMEOUT_MS` | no | `120000` | Abort Gemini calls after this many ms. |
| `GEMINI_MAX_RETRIES` | no | `2` | Retries on 429/5xx/network errors (exponential backoff). |
| `PERPLEXITY_TIMEOUT_MS` | no | `300000` | Abort deep-research calls after this many ms. |
| `PERPLEXITY_BASE_URL` | no | `https://api.perplexity.ai` | Override the Perplexity endpoint. |
| `PORT` | no | `8080` | Injected by Cloud Run automatically. |

## Deploy to Cloud Run

```bash
gcloud run deploy nanobanana-mcp \
  --source . \
  --region europe-west1 \
  --allow-unauthenticated \
  --set-env-vars GEMINI_API_KEY=...,MCP_AUTH_TOKEN=...,PERPLEXITY_API_KEY=...
```

`--allow-unauthenticated` refers to Cloud Run IAM; the `/mcp` endpoint itself is protected by `MCP_AUTH_TOKEN`. Health check is `GET /`.

## Connect as an MCP server

Point any MCP client at the streamable-HTTP endpoint:

- URL: `https://<cloud-run-url>/mcp`
- Header: `Authorization: Bearer <MCP_AUTH_TOKEN>`

The server is stateless — one MCP `Server` instance per request, no sessions.

## Local development

```bash
npm ci
GEMINI_API_KEY=... node server.js   # http://localhost:8080
npm test                            # integration smoke tests (no API key needed)
```

## Also in this repo

- `.claude/skills/media-memory/` — persistent multimodal memory (Gemini embeddings + ChromaDB) for every asset shared or generated in Claude Code sessions. See `CLAUDE.md`.
- `.claude/skills/doctor-video-editor/` — end-to-end pipeline for cleaning and captioning doctor talking-head videos (transcription, disfluency cuts, music ducking, RTL subtitles, vertical Reels output).
