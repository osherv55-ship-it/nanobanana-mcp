// Audio-based hidden disfluency detection.
//
// ElevenLabs Scribe (and most ASR models) silently filter brief filler
// vocalizations like "אה" / "uh" from their transcript output — they
// transcribe what was *said* but not the non-word noises in between.
// This module fills that gap by running ffmpeg silencedetect over the
// extracted audio and flagging loud regions that fall *inside* gaps
// between transcribed words.
//
// In other words: if there's audible energy between two words but the
// transcript doesn't account for it, that energy is almost certainly a
// hidden filler / breath / mouth click.

import { runFfmpeg } from "./ffmpeg.mjs";

export async function detectHiddenDisfluencies(audioPath, words, opts = {}) {
  const {
    silenceDb = -38,
    silenceMinDur = 0.04,
    minGapForCheck = 0.2,
    minFillerDur = 0.06,
    maxFillerDur = 0.8,
    paddingSec = 0.03,
  } = opts;

  const silenceIntervals = await runSilenceDetect(audioPath, silenceDb, silenceMinDur);

  const content = (words || []).filter((w) => w.type === "word" || w.type === "audio_event");
  if (content.length === 0) return { cuts: [], silenceIntervals };

  // Build "loud region" set = complement of silence within audio duration.
  // We don't need exact audio duration; we just iterate inside transcript gaps.
  const cuts = [];
  for (let i = 0; i < content.length - 1; i++) {
    const a = content[i];
    const b = content[i + 1];
    const gapStart = a.end;
    const gapEnd = b.start;
    if (gapEnd - gapStart < minGapForCheck) continue;

    // Find loud regions inside this gap = portions of [gapStart, gapEnd]
    // not covered by any silence interval.
    const loudInGap = loudWithin(silenceIntervals, gapStart, gapEnd);

    for (const loud of loudInGap) {
      const dur = loud.end - loud.start;
      if (dur < minFillerDur) continue;       // too short — probably noise/click
      if (dur > maxFillerDur) continue;       // too long — real speech ASR missed; safer to leave
      cuts.push({
        start: Math.max(0, loud.start - paddingSec),
        end: loud.end + paddingSec,
        reason: "hidden-filler",
        note: `unspoken ${dur.toFixed(2)}s`,
      });
    }
  }

  return { cuts, silenceIntervals };
}

function loudWithin(silenceIntervals, gapStart, gapEnd) {
  // Sort silence intervals that intersect the gap; complement gives loud regions.
  const intersecting = silenceIntervals
    .filter((s) => s.end > gapStart && s.start < gapEnd)
    .map((s) => ({
      start: Math.max(s.start, gapStart),
      end: Math.min(s.end, gapEnd),
    }))
    .sort((a, b) => a.start - b.start);

  const loud = [];
  let cursor = gapStart;
  for (const s of intersecting) {
    if (s.start > cursor) loud.push({ start: cursor, end: s.start });
    cursor = Math.max(cursor, s.end);
  }
  if (cursor < gapEnd) loud.push({ start: cursor, end: gapEnd });
  return loud;
}

function runSilenceDetect(audioPath, silenceDb, minDur) {
  const intervals = [];
  let currentStart = null;
  return new Promise((resolve, reject) => {
    runFfmpeg(
      [
        "-hide_banner",
        "-i", audioPath,
        "-af", `silencedetect=noise=${silenceDb}dB:d=${minDur}`,
        "-f", "null",
        "-",
      ],
      {
        onStderr: (chunk) => {
          for (const line of chunk.split(/\r?\n/)) {
            const sm = line.match(/silence_start:\s*([-\d.]+)/);
            if (sm) currentStart = parseFloat(sm[1]);
            const em = line.match(/silence_end:\s*([-\d.]+)/);
            if (em && currentStart !== null) {
              const end = parseFloat(em[1]);
              intervals.push({ start: currentStart, end });
              currentStart = null;
            }
          }
        },
      },
    ).then(() => resolve(intervals)).catch(reject);
  });
}
