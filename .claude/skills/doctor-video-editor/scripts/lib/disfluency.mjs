// Programmatic disfluency / side-talk detector that operates on word-level
// transcripts (currently produced by ElevenLabs Scribe).
//
// Produces the same { cuts: [{ start, end, reason, note? }] } shape that the
// LLM-based detector emits, so the rest of the pipeline is interchangeable.

const HEBREW_FILLERS_SAFE = [
  "אממ", "אהה", "אם", "אה", "אהמ", "אמ", "הממ", "ממ", "אהההה",
  "הא", "מממ", "אהם", "אהמם", "אאאא", "אהמ׳", "המ", "ההה",
];
const HEBREW_FILLERS_AGGRESSIVE = ["כאילו", "יעני", "בקיצור", "בעצם"];

const ENGLISH_FILLERS_SAFE = [
  "um", "umm", "ummm", "uh", "uhh", "uhhh", "er", "erm", "hmm",
  "ah", "ahh", "uhm",
];
const ENGLISH_FILLERS_AGGRESSIVE = ["like", "actually", "basically", "literally"];

const ARABIC_FILLERS_SAFE = ["آه", "أه", "إيه", "ام", "اه"];
const ARABIC_FILLERS_AGGRESSIVE = ["يعني"];

function normalizeWord(s) {
  return String(s || "")
    .toLowerCase()
    // strip punctuation incl. Hebrew geresh/gershayim and common ASCII
    .replace(/[.,!?;:"'״׳`()\[\]{}—–\-]/g, "")
    .replace(/\s+/g, "")
    .trim();
}

function pickPrimarySpeaker(words) {
  const counts = {};
  for (const w of words) {
    if (w.type === "word" && w.speaker) {
      counts[w.speaker] = (counts[w.speaker] || 0) + 1;
    }
  }
  const ranked = Object.entries(counts).sort((a, b) => b[1] - a[1]);
  return { primary: ranked[0]?.[0] || null, counts, multiSpeaker: ranked.length > 1 };
}

export function detectDisfluencies(words, opts = {}) {
  const {
    aggressive = false,
    fillerPadding = 0.05,
    longPauseThreshold = 1.0,
    longPauseLeave = 0.15,
    stutterMaxGap = 0.4,
    sideTalkMinDuration = 0.4,
    sideTalk = true,
    breaths = true,
  } = opts;

  const fillerSet = new Set();
  for (const w of [...HEBREW_FILLERS_SAFE, ...ENGLISH_FILLERS_SAFE, ...ARABIC_FILLERS_SAFE]) {
    fillerSet.add(normalizeWord(w));
  }
  if (aggressive) {
    for (const w of [...HEBREW_FILLERS_AGGRESSIVE, ...ENGLISH_FILLERS_AGGRESSIVE, ...ARABIC_FILLERS_AGGRESSIVE]) {
      fillerSet.add(normalizeWord(w));
    }
  }

  const { primary: primarySpeaker, counts: speakerCounts, multiSpeaker } =
    pickPrimarySpeaker(words);

  const cuts = [];

  // 1. Filler words (exact match against the normalized filler set).
  for (const w of words) {
    if (w.type !== "word") continue;
    const norm = normalizeWord(w.text);
    if (norm && fillerSet.has(norm)) {
      cuts.push({
        start: Math.max(0, w.start - fillerPadding),
        end: w.end + fillerPadding,
        reason: "filler",
        note: norm,
      });
    }
  }

  // 2. Stutters: immediate same-word or prefix repetition within stutterMaxGap.
  const contentWords = words.filter((w) => w.type === "word");
  for (let i = 0; i < contentWords.length - 1; i++) {
    const a = contentWords[i];
    const b = contentWords[i + 1];
    const aNorm = normalizeWord(a.text);
    const bNorm = normalizeWord(b.text);
    if (!aNorm || !bNorm) continue;
    if (b.start - a.end >= stutterMaxGap) continue;

    if (aNorm === bNorm) {
      cuts.push({
        start: Math.max(0, a.start - 0.02),
        end: a.end + 0.02,
        reason: "stutter",
        note: aNorm,
      });
    } else if (aNorm.length >= 2 && bNorm.length > aNorm.length && bNorm.startsWith(aNorm)) {
      // partial stutter: "אנ-" → "אני"
      cuts.push({
        start: Math.max(0, a.start - 0.02),
        end: a.end + 0.02,
        reason: "stutter",
        note: `${aNorm}-`,
      });
    }
  }

  // 3. Long pauses: gaps between consecutive content words.
  for (let i = 0; i < contentWords.length - 1; i++) {
    const a = contentWords[i];
    const b = contentWords[i + 1];
    const gap = b.start - a.end;
    if (gap > longPauseThreshold) {
      const cutStart = a.end + longPauseLeave;
      const cutEnd = b.start - longPauseLeave;
      if (cutEnd - cutStart > 0.05) {
        cuts.push({ start: cutStart, end: cutEnd, reason: "long-pause" });
      }
    }
  }

  // 4. Audible breaths / sighs (ElevenLabs scribe audio events).
  if (breaths) {
    for (const w of words) {
      if (w.type !== "audio_event") continue;
      const t = String(w.text || "").toLowerCase();
      if (/breath|inhale|exhale|sigh/.test(t)) {
        cuts.push({ start: w.start, end: w.end, reason: "breath", note: t });
      }
    }
  }

  // 5. Side talk: contiguous runs of non-primary-speaker words.
  if (sideTalk && multiSpeaker && primarySpeaker) {
    let runStart = null;
    let runEnd = null;
    let runWords = 0;
    const flush = () => {
      if (runStart !== null && runEnd !== null && runEnd - runStart >= sideTalkMinDuration) {
        cuts.push({
          start: Math.max(0, runStart - 0.05),
          end: runEnd + 0.05,
          reason: "side-talk",
          note: `${runWords}w/non-primary`,
        });
      }
      runStart = null;
      runEnd = null;
      runWords = 0;
    };

    for (const w of words) {
      if (w.type !== "word") continue;
      if (w.speaker && w.speaker !== primarySpeaker) {
        if (runStart === null) runStart = w.start;
        runEnd = w.end;
        runWords++;
      } else {
        flush();
      }
    }
    flush();
  }

  // Sort + merge overlapping/adjacent cuts (within 50 ms).
  cuts.sort((a, b) => a.start - b.start);
  const merged = [];
  for (const c of cuts) {
    const last = merged[merged.length - 1];
    if (last && c.start <= last.end + 0.05) {
      last.end = Math.max(last.end, c.end);
      const tags = new Set(last.reason.split("+"));
      tags.add(c.reason);
      last.reason = [...tags].join("+");
      if (c.note) last.note = last.note ? `${last.note}, ${c.note}` : c.note;
    } else {
      merged.push({ ...c });
    }
  }

  return {
    cuts: merged,
    primary_speaker: primarySpeaker,
    speakers: speakerCounts,
    multi_speaker: multiSpeaker,
  };
}

// Map original-timeline words to the post-cut timeline. Words that fall fully
// inside a cut are dropped; words that straddle a cut boundary get clamped.
export function remapWords(words, cuts) {
  if (!cuts || cuts.length === 0) return words.map((w) => ({ ...w }));

  function shiftAt(t) {
    let shift = 0;
    for (const c of cuts) {
      if (c.end <= t) shift += c.end - c.start;
      else if (c.start < t && c.end > t) shift += t - c.start;
    }
    return shift;
  }

  function inCut(t) {
    for (const c of cuts) {
      if (t >= c.start && t < c.end) return true;
    }
    return false;
  }

  const out = [];
  for (const w of words) {
    // Drop word entirely if midpoint is inside a cut.
    const mid = (w.start + w.end) / 2;
    if (inCut(mid)) continue;
    const newStart = Math.max(0, w.start - shiftAt(w.start));
    const newEnd = Math.max(newStart + 0.04, w.end - shiftAt(w.end));
    out.push({ ...w, start: newStart, end: newEnd });
  }
  return out;
}
