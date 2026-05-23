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

**macOS / Linux:**
```bash
cd .claude/skills/doctor-video-editor
bash setup.sh
```

**Windows (PowerShell):**
```powershell
powershell -ExecutionPolicy Bypass -File .\.claude\skills\doctor-video-editor\setup.ps1
$env:GEMINI_API_KEY = "your-key-here"        # required, used for translation
$env:ELEVENLABS_API_KEY = "your-key-here"    # optional, enables word-level cuts
```

This installs `ffmpeg-static` and Gemini deps locally inside the skill folder (no system ffmpeg required).

**Transcription backends:**
- `ELEVENLABS_API_KEY` (preferred) — ElevenLabs Scribe gives word-level timestamps + speaker diarization. With this, filler detection, stutter detection, long-pause cuts, and side-talk filtering all run programmatically against word data (no LLM judgment for the cut list — fast and deterministic).
- `GEMINI_API_KEY` (fallback) — Gemini 2.5 Flash transcribes at segment-level, and an LLM call selects cuts. Less precise on disfluencies but works on any video without a separate audio pipeline.

If both keys are set, ElevenLabs is used by default. Force a backend with `--transcriber elevenlabs|gemini`.

On Windows, all `node scripts/pipeline.mjs ...` commands below work identically from PowerShell or cmd. Paths may use either forward or backslashes — the pipeline normalizes them internally for ffmpeg's filter syntax.

## Permanent workflow (recommended)

One folder per doctor, drop assets in, run one command. The pipeline auto-
profiles the speaker, tightens pauses to their natural rhythm, catches the
"אה" the ASR filtered out via audio energy analysis, places overlays
evenly across the timeline, ducks the music under speech, prefixes the
intro, and burns Hebrew word-by-word subtitles.

### Folder convention (flat)

```
C:\Users\<you>\Desktop\doctors\<doctor-name>\
  main.mov                  REQUIRED — the main interview / promo clip
  intro.mov                 optional — auto-trimmed to ~6s (name + role)
  <broll-1>.mov             optional — any non-main video becomes B-roll
  <broll-2>.mov             optional
  before1.jpg / after1.jpg  optional — matched as a before/after split
  before2.jpg / after2.jpg  optional — second pair
  music.mp3                 optional — sidechain-ducked background bed
```

- Role detection is by filename prefix:
  - `main*` → main video (largest video wins if no explicit `main.*`)
  - `intro*` → intro prefix
  - `before*` + matching `after*` → before/after split
  - everything else with a video / image extension → B-roll
- Hebrew subtitles only by default — punctuation is auto-stripped from
  single-word cues and RTL direction is anchored, so periods and commas
  stay on the correct side.

### Run

**Once on first use** — clone the repo, set env vars (preferably
permanently via *System Properties → Environment Variables*):

```powershell
$env:ELEVENLABS_API_KEY = "<your-key with Speech to Text permission>"
```

**Per video** — one of these:

```powershell
# Option A: invoke the script directly (after first clone)
cd "$env:USERPROFILE\Desktop\nanobanana-mcp\.claude\skills\doctor-video-editor"
.\edit-doctor.ps1 -Folder "$env:USERPROFILE\Desktop\doctors\yasmin"
```

```powershell
# Option B: one-shot bootstrap (auto-clones / auto-updates the repo)
$env:DOCTOR_FOLDER = "$env:USERPROFILE\Desktop\doctors\yasmin"
iex (irm "https://raw.githubusercontent.com/osherv55-ship-it/nanobanana-mcp/claude/doctor-video-editing-5AveU/.claude/skills/doctor-video-editor/edit-doctor-bootstrap.ps1")
```

### Outputs

Everything lands in `<doctor-folder>/out/`:

| File | Notes |
|---|---|
| `final.he.mp4` | The deliverable — intro + main, overlays composed, subs burned, music mixed |
| `cleaned.mp4` | Main video after cuts, before overlays |
| `composed.mp4` | Cleaned + overlays, before subtitle burn |
| `transcript.json` | Word-level ElevenLabs Scribe output |
| `cuts.json` | Programmatic cut list + the auto-tuned profile that produced it |
| `subs/subs.he.{ass,srt}` | Subtitle sidecars |
| `intro/` | Sub-pipeline workspace for the intro clip |

### Tuning knobs (optional env vars)

| Env var | Effect | Default |
|---|---|---|
| `DVE_MUSIC_VOLUME` | Music bed loudness pre-ducking | `0.12` (~-18 dB) |

To override per-run: `$env:DVE_MUSIC_VOLUME = "0.06"` (quieter) before invoking.

---

## End-to-end run (legacy)

Polished default (ElevenLabs transcription, programmatic cuts, smooth transitions, word-by-word source-language captions):

```bash
node .claude/skills/doctor-video-editor/scripts/pipeline.mjs all \
  --input /path/to/raw.mp4 \
  --out-dir ./out \
  --source-lang he \
  --target-langs he,en \
  --word-by-word \
  --crossfade 0.10 \
  --burn-in
```

Produces in `--out-dir`:
- `transcript.json`            — timestamped transcript (word-level when using ElevenLabs)
- `cuts.json`                  — list of segments removed (with reasons + primary-speaker info)
- `cleaned.mp4`                — video with disfluencies / side talk removed, optionally crossfaded
- `cleaned.mp4.keeps.json`     — keep-interval map (used for subtitle remapping)
- `subs/subs.<lang>.ass`       — styled subtitle file per target language
- `subs/subs.<lang>.srt`       — plain SRT alongside the ASS, for editing pipelines
- `final.<lang>.mp4`           — cleaned video with burned-in captions (only when `--burn-in`)

Without `--burn-in`, the cleaned video plus sidecar `.ass` / `.srt` files ship as deliverables — useful when the editor wants to load subs into Premiere/Resolve.

**Flags worth knowing:**
- `--word-by-word` — single-word pop captions for the source language (uses ElevenLabs word timings). Other target languages fall back to phrase-level cues.
- `--crossfade 0.10` — smooth 100 ms dissolve between every cut. Default is 0 (hard cuts). Auto-degrades to hard cut if any keep interval is too short.
- `--transition fade` — xfade transition name. Try `fadeblack`, `wipeleft`, `dissolve`, etc. (ffmpeg xfade list).
- `--aggressive` — also strip soft fillers (כאילו, יעני, like, basically).
- `--transcriber elevenlabs|gemini` — force a transcription backend.
- `--detector programmatic|gemini` — force a cut-detector backend.

## Subcommands (for partial / debug flows)

Each step writes its output to disk so the next step can resume.

```bash
# 1. Transcribe a video to timestamped JSON.
#    Uses ElevenLabs Scribe when ELEVENLABS_API_KEY is set, Gemini otherwise.
pipeline.mjs transcribe --input raw.mp4 --out transcript.json --source-lang he

# 2. Detect filler words / stutters / pauses / side talk and produce a cut list.
#    Programmatic against word-level data; falls back to Gemini for segment-only transcripts.
pipeline.mjs find-cuts --transcript transcript.json --out cuts.json

# 3. Apply the cut list with ffmpeg. Optional crossfade smooths every join.
pipeline.mjs apply-cuts --input raw.mp4 --cuts cuts.json --out cleaned.mp4 --crossfade 0.10

# 4. Translate cleaned-segment transcript to one or more languages.
#    Same-language outputs skip Gemini and use the source transcript directly.
#    --word-by-word produces single-word pop captions for the source language.
pipeline.mjs translate --transcript transcript.json --cuts cuts.json \
  --target-langs he,en --out-dir ./subs --word-by-word --crossfade 0.10

# 5. Burn the .ass subtitles into the cleaned video.
pipeline.mjs overlay --input cleaned.mp4 --subs subs/subs.he.ass --out final.he.mp4
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

## What gets cut

When transcribing with ElevenLabs (the default when `ELEVENLABS_API_KEY` is set) the cut list is built **programmatically** from the word stream, not by an LLM:

| Class | Trigger | Notes |
|---|---|---|
| `filler` | Word matches a built-in list of pure filler sounds (Hebrew: אממ/אהה/אם/אה/הממ/ממ. English: um/umm/uh/erm/hmm. Arabic: آه/إيه). | The list grows with `--aggressive` to also include כאילו/יעני/like/actually/basically/literally. |
| `stutter` | Same normalized word repeated within 0.4 s. Also catches prefix stutters like "אנ-" → "אני". | Only the first instance is cut. |
| `long-pause` | Gap between consecutive content words > 1.0 s. | Leaves 0.15 s on each side as natural breathing room. |
| `breath` | ElevenLabs Scribe audio event tagged with breath/inhale/exhale/sigh. | Off-by-default in conservative mode? No — on by default; subtle but cleans up between sentences. |
| `side-talk` | Contiguous run of words from a speaker that is NOT the primary speaker (determined by word-count majority). | Requires diarization (default on). 0.4 s minimum run-length so single interjections don't trigger. |

When transcribing with Gemini, the LLM-based cut detector is used instead — that path still works but is less precise and can't see speakers.

## Notes & limits

- Gemini Files API is used for any video over ~18 MB (inline payload limit). Files live ~48h on Google's side then auto-expire.
- ElevenLabs Scribe accepts up to ~2 GB per file. The pipeline extracts a 16 kHz mono FLAC track via ffmpeg before uploading, so even hour-long videos send ~50 MB of audio.
- Default transcription model: `gemini-2.5-flash` (Gemini path) / `scribe_v1` (ElevenLabs path). Override Gemini with `--model` or `GEMINI_VIDEO_MODEL`.
- Conservative by default — only obvious disfluencies. `--aggressive` adds soft fillers and (Gemini-only) phrase-level repetitions / tangents.
- For videos >10 minutes via Gemini, expect long-running calls (5–15 min). The pipeline writes progress to stderr.
- ffmpeg cut step uses re-encoding (libx264 + AAC) for frame-accurate edits. Lossless cutting via `-c copy` is unreliable with mid-GOP cuts.
- Crossfade requires CFR input; the pipeline detects the source frame rate via ffprobe and pins the trimmed segments to it. If any keep interval is shorter than the requested crossfade, the pipeline auto-shrinks the crossfade or falls back to a hard cut for that join.
