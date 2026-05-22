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
    return `Dialogue: 0,${fmtTime(c.start)},${fmtTime(c.end)},Default,,0,0,0,,${text}`;
  });
  return header(opts) + lines.join("\n") + "\n";
}
