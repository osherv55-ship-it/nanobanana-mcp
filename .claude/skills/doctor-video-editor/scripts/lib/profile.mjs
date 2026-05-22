// Per-video editing profile: analyzes a word-level transcript and returns
// detector parameters tuned to the speaker's natural rhythm.
//
// The goal is for every video — whether the speaker is polished, raw, fast,
// slow, or multi-party — to be edited at the same "tightness" relative to
// its own baseline, without per-video manual configuration.

const HEBREW_FILLERS = ["אממ","אהה","אם","אה","אהמ","אמ","הממ","ממ","אהההה","הא","מממ","אהם","אהמם","אאאא","המ","ההה"];
const ENGLISH_FILLERS = ["um","umm","ummm","uh","uhh","uhhh","er","erm","hmm","ah","ahh","uhm"];
const ARABIC_FILLERS = ["آه","أه","إيه","ام","اه"];

function normalize(s) {
  return String(s || "")
    .toLowerCase()
    .replace(/[.,!?;:"'״׳`()\[\]{}—–\-]/g, "")
    .replace(/\s+/g, "")
    .trim();
}

const FILLER_SET = new Set([...HEBREW_FILLERS, ...ENGLISH_FILLERS, ...ARABIC_FILLERS].map(normalize));

function quantile(sorted, q) {
  if (sorted.length === 0) return 0;
  const idx = Math.min(sorted.length - 1, Math.max(0, Math.floor(sorted.length * q)));
  return sorted[idx];
}

function median(arr) {
  if (arr.length === 0) return 0;
  const s = [...arr].sort((a, b) => a - b);
  const mid = Math.floor(s.length / 2);
  return s.length % 2 ? s[mid] : (s[mid - 1] + s[mid]) / 2;
}

function round(n, d = 2) {
  const f = Math.pow(10, d);
  return Math.round(n * f) / f;
}

const clamp = (n, lo, hi) => Math.min(hi, Math.max(lo, n));

// Build a per-video profile. Returns BOTH a human-readable summary
// (saved into cuts.json so the user can see what was decided) AND
// the detectorOpts to pass into detectDisfluencies.
export function buildProfile(words, opts = {}) {
  const { minMeaningfulPause = 0.3 } = opts;
  const content = (words || []).filter((w) => w.type === "word");

  if (content.length < 5) {
    return defaultProfile("transcript too short for analysis");
  }

  // Speech rate
  const span = content[content.length - 1].end - content[0].start;
  const wpm = span > 0 ? (content.length / span) * 60 : 0;

  // Pause distribution — only count gaps that are meaningfully larger than
  // inter-word spacing, otherwise the distribution is dominated by tiny
  // typing-rhythm gaps and the percentiles are useless.
  const allPauses = [];
  for (let i = 0; i < content.length - 1; i++) {
    const gap = content[i + 1].start - content[i].end;
    if (gap > 0) allPauses.push(gap);
  }
  const meaningful = allPauses.filter((g) => g >= minMeaningfulPause).sort((a, b) => a - b);
  const naturalPause = meaningful.length ? median(meaningful) : 0.5;

  // Filler frequency
  let fillerCount = 0;
  for (const w of content) {
    if (FILLER_SET.has(normalize(w.text))) fillerCount++;
  }
  const fillerRate = wpm > 0 ? fillerCount / (content.length / wpm) : 0; // fillers / minute

  // Speakers (only counting those with actual words, not audio events)
  const speakers = {};
  for (const w of content) {
    if (w.speaker) speakers[w.speaker] = (speakers[w.speaker] || 0) + 1;
  }
  const speakerCount = Object.keys(speakers).length;

  // Style classification — best-effort heuristic, mostly informational
  let style;
  if (fillerCount === 0 && naturalPause < 0.7) style = "polished";
  else if (fillerCount >= 8 || fillerRate >= 8) style = "raw";
  else style = "natural";

  // Tuned detector parameters
  // — longPauseThreshold: cuts anything longer than the SPEAKER'S OWN
  //   natural inter-sentence pause. Polished speakers get a 20%
  //   tighter threshold (they're already snappy by design, so we
  //   tighten further to lift the pace). Raw speakers get a 30% looser
  //   threshold to avoid chopping their natural rhythm.
  let pauseMul = 1.0;
  if (style === "polished") pauseMul = 0.8;
  else if (style === "raw") pauseMul = 1.3;
  const longPauseThreshold = clamp(naturalPause * pauseMul, 0.4, 1.5);
  // — longPauseLeave: scales with threshold; tighter in polished mode.
  const leaveMul = style === "polished" ? 0.15 : 0.2;
  const longPauseLeave = clamp(longPauseThreshold * leaveMul, 0.06, 0.2);
  // — aggressive filler list: activated when fillers are frequent enough
  //   that the speaker likely uses "soft" fillers (כאילו/יעני/like/...).
  const aggressive = fillerCount >= 5;
  // — side-talk detection: enable whenever multiple speakers said words.
  const sideTalk = speakerCount > 1;

  return {
    speech: {
      words: content.length,
      duration_sec: round(span, 2),
      wpm: Math.round(wpm),
    },
    pauses: {
      meaningful_count: meaningful.length,
      p50: round(quantile(meaningful, 0.5), 2),
      p75: round(quantile(meaningful, 0.75), 2),
      p90: round(quantile(meaningful, 0.9), 2),
      natural: round(naturalPause, 2),
    },
    fillers: {
      count: fillerCount,
      rate_per_min: round(fillerRate, 2),
    },
    speakers: {
      count: speakerCount,
      breakdown: speakers,
    },
    style,
    detectorOpts: {
      longPauseThreshold: round(longPauseThreshold, 2),
      longPauseLeave: round(longPauseLeave, 2),
      aggressive,
      sideTalk,
    },
  };
}

function defaultProfile(reason) {
  return {
    speech: { words: 0, duration_sec: 0, wpm: 0 },
    pauses: { meaningful_count: 0, p50: 0, p75: 0, p90: 0, natural: 0.7 },
    fillers: { count: 0, rate_per_min: 0 },
    speakers: { count: 0, breakdown: {} },
    style: "natural",
    note: `auto-profile fell back to defaults: ${reason}`,
    detectorOpts: {
      longPauseThreshold: 0.7,
      longPauseLeave: 0.14,
      aggressive: false,
      sideTalk: false,
    },
  };
}
