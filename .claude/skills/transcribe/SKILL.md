---
name: transcribe
description: Transcribe audio/video to text, subtitles and searchable notes — local files, folders, or links (a single TikTok/YouTube/Instagram/Drive video, or a whole TikTok profile / YouTube channel / playlist). Default engine is local Whisper (free, no API key, no quota; Hebrew uses ivrit.ai's Hebrew-tuned model); optional ElevenLabs Scribe (speaker labels, word timing) and Gemini (speech + on-screen text + what is shown). Writes .txt/.srt/.json per item plus combined.md, and can filter a large batch to the items that mention something (--match). Use whenever the user asks to transcribe, caption, subtitle, "go over the videos", summarize what someone says across many videos, or search spoken content. Triggers on Hebrew "תמלל", "תמלול", "תתמלל לי", "תעבור על הסרטונים", "מה היא אומרת בסרטונים", "כתוביות", "תוריד ותתמלל", and English "transcribe", "transcript", "subtitles", "captions", "speech to text".
---

# transcribe

One CLI for every transcription job: `scripts/transcribe.py`. It downloads (yt-dlp), transcribes, and writes
per-item files plus a combined, date-sorted `combined.md` you can read in one go.

## One-time setup (each fresh container)

```bash
bash .claude/skills/transcribe/setup.sh          # Windows: .claude\skills\transcribe\setup.ps1
```

Creates `.claude/skills/transcribe/.venv` (gitignored) with faster-whisper, yt-dlp and curl_cffi. Whisper
models download from Hugging Face on first use (≈1.6 GB for the turbo models, ≈0.5 GB for `--fast`).

Run as:

```bash
T=".claude/skills/transcribe/.venv/bin/python .claude/skills/transcribe/scripts/transcribe.py"
$T <inputs...> --out <folder> [options]
```

## Choosing the engine

| Need | Command | Notes |
|---|---|---|
| Default — accurate speech, free | `--engine whisper` (default) | Local CPU, no key, no quota. ~4× real time on 4 cores |
| Hebrew | add `--lang he` | Uses `ivrit-ai/whisper-large-v3-turbo-ct2` (Hebrew-tuned). Always pass it for Hebrew content |
| Bulk screening of hundreds of clips | add `--fast` | Whisper `small`, greedy — ~3× faster, slightly less accurate |
| Text that only appears on screen (labels, overlays, captions) | add `--visual` | Gemini pass on top of the speech engine. Free-tier quota is per model per day; when spent, speech is still saved and a later run with `--visual` fills in only the missing part |
| Most accurate, speaker labels — Hebrew, interviews, meetings, anything where exact wording matters | `--engine elevenlabs` | Needs `ELEVENLABS_API_KEY` (Speech-to-Text permission; same key doctor-video-editor uses). Seconds per clip, perfect on the Hebrew test set. Spends the ElevenLabs plan's STT allowance, so use whisper for bulk sweeps of hundreds of clips |
| Speech + on-screen text in one call | `--engine gemini` | Free tier is limited; prefer whisper + `--visual` for big batches |

**Picking by default:** if `ELEVENLABS_API_KEY` is set and the job is a handful of files, use
`--engine elevenlabs`; for large batches (whole profiles) use whisper, optionally re-running only the
`matches.md` hits through ElevenLabs. Without the key, whisper.

Pass `--lang` whenever you know the language (`he`, `en`, `pt`, `ar`, …) — auto-detect works but a
fixed language is faster and avoids misdetection on short clips.

## Inputs

- Local file(s) or a folder (recursive; any common audio/video format).
- URL of a single video, or of a profile / channel / playlist — every entry is listed first, then filtered:
  - `--since YYYY-MM-DD` / `--until YYYY-MM-DD` — date window
  - `--title-match REGEX` — keep only entries whose title/caption matches (before downloading)
  - `--limit N`
- `@list.txt` — one input per line.

TikTok works out of the box (browser impersonation via curl_cffi). YouTube and Instagram often refuse cloud
IPs ("Sign in to confirm you're not a bot"): ask the user for an exported `cookies.txt` and pass `--cookies`,
or ask them to put the files in Google Drive and transcribe the downloaded files instead. A blocked link is
skipped with that explanation; the rest of the batch continues.

## Outputs (in `--out`)

- `<id>.txt` — header (source, date, uploader, views, caption, engine) + transcript (+ on-screen text / visual)
- `<id>.srt` — subtitles with timestamps (speaker tags with ElevenLabs)
- `<id>.json` — everything structured (segments, meta, engine, model)
- `combined.md` — all items sorted by date: **read this** instead of opening files one by one
- `matches.md` — only with `--match REGEX`: the items whose transcript, caption or on-screen text match

Re-running the same command resumes: finished items are skipped (`--force` redoes them). Downloaded media
is deleted after transcription unless `--keep-media`.

## Recipes

```bash
# A TikTok profile, Portuguese, only videos from June on that mention CBL anywhere (speech or screen)
$T "https://www.tiktok.com/@someone" --lang pt --since 2026-06-01 --visual --match "cbl|514" --out out/someone

# Huge profile: cheap first pass on speech, then a full pass only on the hits
$T "https://www.tiktok.com/@someone" --lang pt --fast --match "cbl|514" --out out/screen
# then feed the matching URLs (from matches.md "source:" lines) into a normal run with --visual

# Hebrew interview from a folder, with subtitles
$T ~/videos/interview --lang he --out out/interview

# Speaker-separated meeting recording
$T meeting.m4a --engine elevenlabs --lang he --out out/meeting
```

## Rules

- Output folders go in the scratchpad (or a path the user names), not in the repo.
- Bulk downloads of other people's videos are working files: they are deleted after transcription and are
  **not** ingested into media-memory. Media the user sends, or asks to keep, still follows the media-memory
  rule in CLAUDE.md.
- When reporting back, quote the transcript in its original language when exact wording matters, and say
  which items were speech-only (no `--visual`) so the user knows on-screen text may be missing.
- Long batches: run in the background and give the user short progress updates.
