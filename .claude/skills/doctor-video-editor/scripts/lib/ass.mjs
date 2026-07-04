// Build a styled .ass subtitle file from a list of timestamped segments.
// "Modern fast-paced" style: bold Heebo (sans, Hebrew-friendly), white text +
// thick black outline, bottom-center, one short phrase per cue
// (max ~6 words / ~2.5s). Skips empty/whitespace-only segments.

const STYLE = {
  fontName: "Heebo",
  fontSize: 72,
  primaryColor: "&H00FFFFFF", // white (ASS = &HAABBGGRR)
  outlineColor: "&H00000000", // black outline
  backColor: "&H80000000",    // 50% black shadow
  bold: -1,                   // -1 = true in ASS (libass uses bold variant of variable font)
  outline: 5,
  shadow: 1,
  alignment: 2,               // 2 = bottom-center
  marginV: 140,
};

const MAX_WORDS_PER_CUE = 6;
const MAX_SECONDS_PER_CUE = 2.5;
const MIN_SECONDS_PER_CUE = 0.4; // anything shorter just won't read on screen

function fmtTime(sec) {
  const s = Math.max(0, sec);
  const h = Math.floor(s / 3600);
  const m = Math.floor((s % 3600) / 60);
  const rest = s - h * 3600 - m * 60;
  const secInt = Math.floor(rest);
  const cs = Math.round((rest - secInt) * 100);
  return `${h}:${String(m).padStart(2, "0")}:${String(secInt).padStart(2, "0")}.${String(cs).padStart(2, "0")}`;
}

function header({ width = 1920, height = 1080, fontName = STYLE.fontName } = {}) {
  const s = { ...STYLE, fontName };
  return `[Script Info]
ScriptType: v4.00+
PlayResX: ${width}
PlayResY: ${height}
WrapStyle: 0
ScaledBorderAndShadow: yes
YCbCr Matrix: TV.709

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,${s.fontName},${s.fontSize},${s.primaryColor},&H000000FF,${s.outlineColor},${s.backColor},${s.bold},0,0,0,100,100,0,0,1,${s.outline},${s.shadow},${s.alignment},80,80,${s.marginV},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
`;
}

// Split one transcript segment into multiple shorter cues if it's long.
function splitSegment(seg) {
  const words = (seg.text || "").trim().split(/\s+/).filter(Boolean);
  const dur = Math.max(0.1, seg.end - seg.start);
  if (words.length === 0) return [];
  if (words.length <= MAX_WORDS_PER_CUE && dur <= MAX_SECONDS_PER_CUE) {
    return [{ start: seg.start, end: seg.end, text: words.join(" ") }];
  }

  const chunks = [];
  for (let i = 0; i < words.length; i += MAX_WORDS_PER_CUE) {
    chunks.push(words.slice(i, i + MAX_WORDS_PER_CUE).join(" "));
  }

  const totalWords = words.length;
  const cues = [];
  let consumed = 0;
  for (const chunk of chunks) {
    const w = chunk.split(/\s+/).length;
    const start = seg.start + (consumed / totalWords) * dur;
    const end = seg.start + ((consumed + w) / totalWords) * dur;
    cues.push({ start, end, text: chunk });
    consumed += w;
  }
  return cues;
}

export function buildAss(segments, opts = {}) {
  const cues = segments
    .flatMap(splitSegment)
    .filter((c) => c.text.trim().length > 0 && c.end - c.start >= MIN_SECONDS_PER_CUE);
  const lines = cues.map((c) => {
    const text = c.text.replace(/\r?\n/g, " ").trim();
    // U+200F (Right-to-Left Mark) anchors the cue's bidi direction as RTL so
    // trailing punctuation, numbers, or stray Latin doesn't drift to the
    // wrong side of Hebrew/Arabic lines.
    return `Dialogue: 0,${fmtTime(c.start)},${fmtTime(c.end)},Default,,0,0,0,,‏${text}`;
  });
  return header(opts) + lines.join("\n") + "\n";
}

// Word-by-word "pop" style: each spoken word appears solo, briefly, with a
// fast fade. Modern Reels/Shorts feel. Requires word-level timing.
const WORD_MIN_DURATION = 0.18;   // never shorter than this on screen
const WORD_HOLD_EXTRA = 0.05;     // small tail to avoid flicker
const WORD_GAP_FILL = 0.18;       // if next word > this away, let prev hold
// Latin + Arabic/Hebrew sentence punctuation that should NOT be carried into
// single-word cues — alone, a trailing period renders to the wrong side of
// an RTL word (",אני" instead of "אני,").
const WORD_TRAIL_PUNCT = /[.,!?;:،۔؟]+$/;

export function buildAssWordByWord(words, opts = {}) {
  const lines = [];
  const list = words.filter((w) => w.type === "word" || w.type === undefined);
  for (let i = 0; i < list.length; i++) {
    const w = list[i];
    let text = String(w.text || "").replace(/\s+/g, " ").trim();
    if (!text) continue;
    text = text.replace(WORD_TRAIL_PUNCT, "").trim();
    if (!text) continue;
    const next = list[i + 1];
    let start = Math.max(0, w.start);
    let end = w.end + WORD_HOLD_EXTRA;
    if (next) {
      const gap = next.start - w.end;
      // hold until next word arrives, but don't bridge huge silences
      end = Math.min(next.start - 0.01, w.end + Math.max(WORD_HOLD_EXTRA, Math.min(gap, WORD_GAP_FILL)));
    }
    if (end - start < WORD_MIN_DURATION) end = start + WORD_MIN_DURATION;
    lines.push(
      `Dialogue: 0,${fmtTime(start)},${fmtTime(end)},Default,,0,0,0,,{\\fad(30,30)}‏${text}`,
    );
  }
  return header(opts) + lines.join("\n") + "\n";
}
