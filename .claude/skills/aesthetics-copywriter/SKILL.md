---
name: aesthetics-copywriter
description: >
  Hebrew copywriting engine for the academy's and Glowness clinic's social
  content (reel captions, hooks, on-screen text, post copy). Use whenever
  writing ANY user-facing marketing text in this project — reel cue lines,
  hooks, CTAs, captions. Encodes the hook formulas learned from the
  aesthetics-tracker competitive research plus a mandatory anti-banality pass.
---

# aesthetics-copywriter

Never ship first-draft copy. Every piece of on-screen text goes through:
draft → banality check → multi-model critique (PAL, if available) → merge.

## Voice

- Hebrew, spoken register (לא "יש לבצע" — "ככה עושים"), confident, zero fluff.
- The academy sells **knowledge over courage**; Glowness sells **honesty over hype**.
- Reel cues: ≤6 words, ≤2.5s each. One idea per cue. No line-final
  punctuation except `?` (and append U+200F RLM after a final `?` for ASS/RTL).

## Hook formulas (from tracked viral posts — see aesthetics-tracker reports)

1. **Specific stake** — a tiny concrete detail with a huge consequence.
   "מילימטר אחד למטה / והעפעף הזה לא ייפתח מחר בבוקר" (beats "3 מקומות מסוכנים").
2. **Fear→relief arc** (Tim Pearce lane) — open on the complication everyone
   fears, resolve with method. Never open with the institution.
3. **Curiosity gap title** — "How NOT to inject the BRAIN" energy, Hebrew:
   "הטעות שכל מזריק מתחיל עושה בגבה".
4. **Confession/story-time** — "המטופלת ביקשה עוד מ"ל. אמרתי לא".
5. **Contrast couplet** — "בוטוקס זה לא אומץ. זה ידע" / "לא מנחשים. מציירים".
6. **Rhetorical check** — "העורק הזה? רואים אותו".

## Banality blacklist — rewrite on sight

Generic openers ("חשוב לדעת ש...", "הכירו את...", "טיפול מתקדם"),
institution-first lines ("באקדמיה שלנו..." as an opener), abstract nouns
without an image ("מקצועיות", "איכות", "חדשנות"), any line a competitor could
post unchanged. Test: if the line works for a rival clinic's feed — it's banal.

## Process (mandatory)

1. Draft cues mapped to the actual footage beats (write to the picture).
2. Kill every blacklist hit; force at least one formula-1 specific stake.
3. If PAL is reachable, run one critique pass (`mcp__pal__chat`, ask for
   ruthless line-by-line alternatives; adopt only upgrades). Note in the
   deliverable which model(s) contributed.
4. CTA: one action only, tied to the video's promise ("הקורס שמלמד לראות ·
   קישור בביו" — not "לפרטים נוספים").

## RTL/ASS gotchas (burned captions)

Line-final `?` `:` `—` `.` jump sides in libass — either drop them, keep them
mid-line, or append RLM (U+200F). Digits inside Hebrew lines are fine.
**Never set ASS `Spacing` > 0 with Hebrew** — libass letter-spacing reverses
RTL glyph order (renders backwards).

## Caption style presets

- **fast-modern** (default for punchy content): doctor-video-editor `ass.mjs`
  STYLE — Heebo bold 128/1920, white, black outline 9, one style for all cues.
- **brand-bordeaux** (USER-APPROVED academy style, 2026-07-05 — the default):
  title = Assistant 600 @118, soft bordeaux `&H00453076` (#763045) with thin
  white halo (outline 5 `&H30FFFFFF`, no shadow), centered mid-screen;
  body = Assistant 500 @90, off-white `&H00FAFAF8`, outline 2 plum
  `&H55362038`, shadow 3, MarginV 280, margins 90; every cue wrapped with
  `{\fad(260,260)\blur2}`. Body must NEVER go below ~85 — user rejected 62 as
  unreadable. No serif fonts (Frank Ruhl rejected). Fonts via google/fonts
  variable TTFs → `fontTools.varLib.instancer`. Reference: `subs9.ass` /
  final_v9 in media-memory.
- **silver-lux** (user-approved for lecturer/G2-adjacent content, 2026-07-15):
  same Assistant fonts; title @120 silver `&H00E8E8E8` with shimmer override
  `{\blur3\1c&HC0C0C0&\t(200,1600,\1c&HFFFFFF&)\t(1600,3400,\1c&HD0D0D0&)}`,
  thin charcoal outline 2.5 + shadow 6 over `&HA0000000`; body @90 off-white
  `&H00EDEDED`, outline 1.8, shadow 4. No bordeaux. Titles/credentials in
  HEBREW only (user rejected "M.D" on screen). Reference: `subs_erlich2.ass` /
  erlich v2 in media-memory.
