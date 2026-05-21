---
name: doctor-video-editor
description: End-to-end editor for doctor promo/testimonial videos. Transcribes with Gemini, auto-detects filler words/stutters/long pauses, cuts them out with ffmpeg, then generates and burns in multi-language subtitles (Hebrew/English/Arabic/etc.) in a modern fast-paced style. Use whenever the user has a raw doctor interview or talking-head video and wants a cleaned, captioned, translated final cut. Logs all artifacts to media-memory.
---

# doctor-video-editor

Production pipeline for cleaning up doctor talking-head videos and adding modern multi-language captions.

## When to use

Trigger this skill when the user provides a raw video file and asks to:
- Remove stutters, filler words ("אהה", "umm"), repetitions, long pauses, or false starts.
- Add burned-in captions in one or more languages.
- Translate spoken Hebrew/English/Arabic into other languages with synced subtitles.
- Produce a "fast modern" cut suitable for Reels / Shorts / LinkedIn.

If the user only wants ONE of these (e.g. just transcription or just translation), still run the relevant subcommand — the script supports partial flows.

## Setup (one-time)

```bash
cd .claude/skills/doctor-video-editor
bash setup.sh
```

This installs `ffmpeg-static` and Gemini deps locally inside the skill folder (no system ffmpeg required). Required env var: `GEMINI_API_KEY` (same key the MCP server uses).

## End-to-end run

```bash
node .claude/skills/doctor-video-editor/scripts/pipeline.mjs all \
  --input /path/to/raw.mp4 \
  --out-dir ./out \
  --source-lang he \
  --target-langs en,he \
  --burn-in
```

Produces in `--out-dir`:
- `transcript.json`            — Gemini timestamped transcript of the raw video
- `cuts.json`                  — list of segments removed (with reasons)
- `cleaned.mp4`                — video with stutters/fillers/long pauses removed
- `subs.<lang>.ass`            — styled subtitle file per target language
- `final.<lang>.mp4`           — cleaned video with burned-in captions (only when `--burn-in`)

Without `--burn-in`, the cleaned video plus sidecar `.ass` / `.srt` files ship as deliverables — useful when the editor wants to load subs into Premiere/Resolve.

## Subcommands (for partial / debug flows)

Each step writes its output to disk so the next step can resume.

```bash
# 1. Transcribe a video to timestamped JSON
pipeline.mjs transcribe --input raw.mp4 --out transcript.json --source-lang he

# 2. Detect filler words / stutters / pauses and produce a cut list
pipeline.mjs find-cuts --transcript transcript.json --out cuts.json

# 3. Apply the cut list with ffmpeg
pipeline.mjs apply-cuts --input raw.mp4 --cuts cuts.json --out cleaned.mp4

# 4. Translate cleaned-segment transcript to one or more languages
pipeline.mjs translate --transcript transcript.json --cuts cuts.json \
  --target-langs en,ar --out-dir ./subs

# 5. Burn the .ass subtitles into the cleaned video
pipeline.mjs overlay --input cleaned.mp4 --subs subs/subs.en.ass --out final.en.mp4
```

## Style — "fast modern pace"

The ASS subtitle generator (`scripts/lib/ass.mjs`) outputs:
- Bold sans-serif, large font, white text + thick black outline, drop shadow.
- One short phrase per caption (≤6 words / ≤2.5 sec each — long segments are auto-split).
- Bottom-center positioning, safe-area aware.
- RTL handled correctly for Hebrew/Arabic via libass.

To tweak: edit the `STYLE` block at the top of `ass.mjs`.

## Media-memory integration

The skill expects you (Claude) to log artifacts after each run. After a successful pipeline:

1. Log the input as `--source user_upload`.
2. Log `cleaned.mp4` and each `final.<lang>.mp4` as `--source generated` with `--extra '{"tool":"doctor-video-editor","stage":"<stage>","langs":[...]}'`.
3. Pass meaningful tags: `doctor-promo`, `cleaned`, the doctor's name if known, languages, etc.

Do this before reporting the task complete.

## Notes & limits

- Gemini Files API is used for any video over ~18 MB (inline payload limit). Files live ~48h on Google's side then auto-expire.
- Default transcription model: `gemini-2.5-flash`. Override with `--model` or `GEMINI_VIDEO_MODEL` env var.
- Cut detection is conservative by default — it removes obvious disfluencies, not "boring" content. Use `--aggressive` to also cut weak rephrasings and tangents.
- For videos >10 minutes, expect long-running Gemini calls (5–15 min). The pipeline writes progress to stderr.
- The ffmpeg cut step uses re-encoding (libx264 + AAC) for frame-accurate edits. Lossless cutting via `-c copy` is unreliable with mid-GOP cuts, so we don't use it.
