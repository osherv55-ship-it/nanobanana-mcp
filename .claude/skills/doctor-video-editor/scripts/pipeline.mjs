#!/usr/bin/env node
// Main entry point for the doctor-video-editor skill.
// Subcommands: transcribe, find-cuts, apply-cuts, translate, overlay, all.

import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { buildMediaPart, generateJson, DEFAULT_MODEL } from "./lib/gemini.mjs";
import { runFfmpeg, ffprobeJson, getDuration } from "./lib/ffmpeg.mjs";
import { buildAss } from "./lib/ass.mjs";

const __filename = fileURLToPath(import.meta.url);

// ---------- arg parsing ----------

function parseArgs(argv) {
  const args = { _: [] };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a.startsWith("--")) {
      const key = a.slice(2);
      const next = argv[i + 1];
      if (next === undefined || next.startsWith("--")) {
        args[key] = true;
      } else {
        args[key] = next;
        i++;
      }
    } else {
      args._.push(a);
    }
  }
  return args;
}

function need(args, name) {
  if (args[name] === undefined || args[name] === true) {
    die(`missing required --${name}`);
  }
  return args[name];
}

function die(msg) {
  process.stderr.write(`error: ${msg}\n`);
  process.exit(1);
}

function log(msg) {
  process.stderr.write(`[doctor-video-editor] ${msg}\n`);
}

function ensureDir(p) {
  fs.mkdirSync(p, { recursive: true });
  return p;
}

function writeJson(filePath, data) {
  ensureDir(path.dirname(filePath));
  fs.writeFileSync(filePath, JSON.stringify(data, null, 2));
}

function readJson(filePath) {
  return JSON.parse(fs.readFileSync(filePath, "utf8"));
}

// ---------- subcommands ----------

async function cmdTranscribe(args) {
  const input = need(args, "input");
  const out = need(args, "out");
  const sourceLang = args["source-lang"] || "auto";
  const model = args.model || DEFAULT_MODEL;

  log(`transcribing ${input} (source-lang=${sourceLang}, model=${model})`);

  const mimeType = mimeFromPath(input);
  const mediaPart = await buildMediaPart(input, mimeType);

  const sys =
    "You are a professional video transcriber. You produce timestamped transcripts " +
    "with millisecond-level accuracy. You never invent content. " +
    "If a section is silent or unintelligible, mark it as such.";

  const userPrompt = [
    "Transcribe the spoken audio in this video.",
    `Source language hint: ${sourceLang} (use \"auto\" detection if uncertain).`,
    "",
    "Return STRICT JSON with this schema:",
    "{",
    '  "detected_language": "<ISO 639-1 code>",',
    '  "segments": [',
    '    {',
    '      "start": <seconds, float>,',
    '      "end": <seconds, float>,',
    '      "text": "<exact spoken text in source language>",',
    '      "speaker": "<optional speaker label, e.g. doctor|interviewer>",',
    '      "is_filler": <true if this segment is ONLY filler words / hesitation>,',
    '      "has_disfluency": <true if it contains stutters, restarts, long pauses inside>',
    '    }',
    "  ]",
    "}",
    "",
    "Segment granularity: break at natural pauses; keep each segment under ~10 seconds.",
    "Use the SOURCE language for the text — do not translate.",
    "Preserve filler words verbatim (so we can find them) — DO NOT silently clean them.",
  ].join("\n");

  const data = await generateJson({
    model,
    parts: [mediaPart, { text: userPrompt }],
    systemInstruction: sys,
    temperature: 0.1,
  });

  if (!Array.isArray(data.segments)) {
    die(`transcript response missing 'segments' array: ${JSON.stringify(data).slice(0, 300)}`);
  }
  writeJson(out, data);
  log(`wrote transcript with ${data.segments.length} segments to ${out}`);
}

async function cmdFindCuts(args) {
  const transcriptPath = need(args, "transcript");
  const out = need(args, "out");
  const aggressive = !!args.aggressive;
  const model = args.model || DEFAULT_MODEL;

  const transcript = readJson(transcriptPath);
  log(`detecting cuts (aggressive=${aggressive}) over ${transcript.segments.length} segments`);

  const sys =
    "You are a video editor specializing in talking-head doctor testimonials. " +
    "You decide which spans of a transcript should be CUT to produce a clean, " +
    "professional, fast-paced final edit. You never remove medical claims or " +
    "key content — only disfluencies and dead air.";

  const policy = aggressive
    ? "AGGRESSIVE mode: also cut weak rephrasings (when the speaker restates the same idea worse), tangents, and obvious throat-clearing. Be willing to remove up to 25% of total duration."
    : "CONSERVATIVE mode: cut only obvious disfluencies — filler words (umm/uhh/אה/אם), stutters, repeated words, false starts, audible breaths longer than a beat, and silent pauses longer than 1.2 seconds. Never cut medical content.";

  const userPrompt = [
    "Given this timestamped transcript, produce a list of time ranges to CUT.",
    "",
    `Policy: ${policy}`,
    "",
    "Rules:",
    "- Ranges must be expressed in absolute seconds (matching the transcript timestamps).",
    "- Do not overlap ranges. Order them ascending.",
    "- Prefer many short cuts over a few long ones.",
    "- For each cut include a short reason (filler|stutter|repeat|long-pause|false-start|tangent|breath).",
    "",
    "Return STRICT JSON:",
    "{",
    '  "cuts": [',
    '    { "start": <sec>, "end": <sec>, "reason": "<reason>", "note": "<optional human note>" }',
    "  ]",
    "}",
    "",
    "Transcript:",
    JSON.stringify(transcript, null, 2),
  ].join("\n");

  const data = await generateJson({
    model,
    parts: [{ text: userPrompt }],
    systemInstruction: sys,
    temperature: 0.1,
  });

  if (!Array.isArray(data.cuts)) die("cut detector did not return a 'cuts' array");

  // Sanitize: ensure non-overlapping, ascending, valid ranges.
  const cuts = data.cuts
    .map((c) => ({
      start: Number(c.start),
      end: Number(c.end),
      reason: String(c.reason || "unknown"),
      note: c.note ? String(c.note) : undefined,
    }))
    .filter((c) => Number.isFinite(c.start) && Number.isFinite(c.end) && c.end > c.start)
    .sort((a, b) => a.start - b.start);

  const merged = [];
  for (const c of cuts) {
    const last = merged[merged.length - 1];
    if (last && c.start <= last.end) {
      last.end = Math.max(last.end, c.end);
      last.reason = `${last.reason}+${c.reason}`;
    } else {
      merged.push({ ...c });
    }
  }

  writeJson(out, { cuts: merged });
  const removed = merged.reduce((acc, c) => acc + (c.end - c.start), 0);
  log(`wrote ${merged.length} cuts (~${removed.toFixed(1)}s removed) to ${out}`);
}

async function cmdApplyCuts(args) {
  const input = need(args, "input");
  const cutsPath = need(args, "cuts");
  const out = need(args, "out");

  const { cuts } = readJson(cutsPath);
  const duration = await getDuration(input);

  // Compute KEEP intervals = complement of cuts within [0, duration].
  const keeps = [];
  let cursor = 0;
  for (const c of cuts) {
    if (c.start > cursor) keeps.push({ start: cursor, end: Math.min(c.start, duration) });
    cursor = Math.max(cursor, c.end);
  }
  if (cursor < duration) keeps.push({ start: cursor, end: duration });

  if (keeps.length === 0) die("nothing left to keep — cut list covers the entire video");

  log(`assembling ${keeps.length} keep intervals into ${out}`);
  ensureDir(path.dirname(out));

  // Build a single ffmpeg invocation using the concat filter on labeled trims.
  // This is frame-accurate (re-encodes) and avoids the brittleness of -c copy
  // across mid-GOP cut points.
  const filterParts = [];
  for (let i = 0; i < keeps.length; i++) {
    const { start, end } = keeps[i];
    filterParts.push(
      `[0:v]trim=start=${start.toFixed(3)}:end=${end.toFixed(3)},setpts=PTS-STARTPTS[v${i}]`,
    );
    filterParts.push(
      `[0:a]atrim=start=${start.toFixed(3)}:end=${end.toFixed(3)},asetpts=PTS-STARTPTS[a${i}]`,
    );
  }
  const concatInputs = keeps.map((_, i) => `[v${i}][a${i}]`).join("");
  filterParts.push(`${concatInputs}concat=n=${keeps.length}:v=1:a=1[outv][outa]`);
  const filterComplex = filterParts.join(";");

  await runFfmpeg([
    "-y",
    "-i", input,
    "-filter_complex", filterComplex,
    "-map", "[outv]",
    "-map", "[outa]",
    "-c:v", "libx264",
    "-preset", "medium",
    "-crf", "20",
    "-c:a", "aac",
    "-b:a", "192k",
    "-movflags", "+faststart",
    out,
  ]);

  // Also emit a "kept-segments" timing map so subtitle generation can remap
  // original timestamps onto the cleaned timeline.
  const mapPath = out + ".keeps.json";
  writeJson(mapPath, { source: input, duration, keeps });
  log(`wrote cleaned video to ${out} and keep map to ${mapPath}`);
}

async function cmdTranslate(args) {
  const transcriptPath = need(args, "transcript");
  const cutsPath = args.cuts;
  const targetLangs = String(need(args, "target-langs"))
    .split(",")
    .map((s) => s.trim())
    .filter(Boolean);
  const outDir = need(args, "out-dir");
  const model = args.model || DEFAULT_MODEL;
  ensureDir(outDir);

  const transcript = readJson(transcriptPath);
  const cuts = cutsPath ? readJson(cutsPath).cuts : [];

  // Remap transcript segments onto the post-cut timeline.
  const remapped = remapSegments(transcript.segments, cuts);
  log(`remapped ${transcript.segments.length} -> ${remapped.length} segments after cuts`);

  for (const lang of targetLangs) {
    log(`translating to ${lang}...`);
    const sys =
      `You are a professional subtitle translator. You translate spoken doctor ` +
      `testimony into idiomatic ${lang}, preserving meaning and tone. ` +
      `Subtitles must be short and readable on screen.`;

    const userPrompt = [
      `Translate these subtitle segments into ${lang}.`,
      "Preserve segment boundaries — return exactly one translated 'text' per input segment.",
      "If a segment is very long, you may shorten the translation to keep it readable; do not split it.",
      "If a segment is meaningless (e.g. \"...\"), return an empty string.",
      "",
      "Return STRICT JSON:",
      "{",
      '  "segments": [',
      '    { "start": <sec>, "end": <sec>, "text": "<translated text>" }',
      "  ]",
      "}",
      "",
      "Input segments:",
      JSON.stringify(remapped, null, 2),
    ].join("\n");

    const data = await generateJson({
      model,
      parts: [{ text: userPrompt }],
      systemInstruction: sys,
      temperature: 0.3,
    });

    if (!Array.isArray(data.segments)) {
      die(`translate(${lang}) did not return 'segments' array`);
    }

    const ass = buildAss(data.segments);
    const assPath = path.join(outDir, `subs.${lang}.ass`);
    fs.writeFileSync(assPath, ass);
    const srtPath = path.join(outDir, `subs.${lang}.srt`);
    fs.writeFileSync(srtPath, segmentsToSrt(data.segments));
    log(`wrote ${assPath} and ${srtPath}`);
  }
}

async function cmdOverlay(args) {
  const input = need(args, "input");
  const subs = need(args, "subs");
  const out = need(args, "out");

  log(`burning ${subs} into ${input} -> ${out}`);
  ensureDir(path.dirname(out));

  // ass filter automatically uses the styling embedded in the .ass file.
  // ffmpeg's filter parser is finicky about Windows paths — normalize
  // backslashes to forward slashes (accepted on all platforms), then escape
  // the drive-letter colon and any single quotes.
  const subsEscaped = subs
    .replace(/\\/g, "/")
    .replace(/:/g, "\\:")
    .replace(/'/g, "\\'");
  const filter = subs.toLowerCase().endsWith(".ass")
    ? `ass='${subsEscaped}'`
    : `subtitles='${subsEscaped}'`;

  await runFfmpeg([
    "-y",
    "-i", input,
    "-vf", filter,
    "-c:v", "libx264",
    "-preset", "medium",
    "-crf", "20",
    "-c:a", "copy",
    "-movflags", "+faststart",
    out,
  ]);
  log(`wrote ${out}`);
}

async function cmdAll(args) {
  const input = need(args, "input");
  const outDir = ensureDir(need(args, "out-dir"));
  const sourceLang = args["source-lang"] || "auto";
  const targetLangs = String(args["target-langs"] || "")
    .split(",")
    .map((s) => s.trim())
    .filter(Boolean);
  const burnIn = !!args["burn-in"];
  const aggressive = !!args.aggressive;

  if (targetLangs.length === 0) {
    die("--target-langs is required for 'all' (comma-separated, e.g. en,he)");
  }

  const transcriptPath = path.join(outDir, "transcript.json");
  const cutsPath = path.join(outDir, "cuts.json");
  const cleanedPath = path.join(outDir, "cleaned.mp4");
  const subsDir = path.join(outDir, "subs");

  await cmdTranscribe({ input, out: transcriptPath, "source-lang": sourceLang, model: args.model });
  await cmdFindCuts({ transcript: transcriptPath, out: cutsPath, aggressive, model: args.model });
  await cmdApplyCuts({ input, cuts: cutsPath, out: cleanedPath });
  await cmdTranslate({
    transcript: transcriptPath,
    cuts: cutsPath,
    "target-langs": targetLangs.join(","),
    "out-dir": subsDir,
    model: args.model,
  });

  if (burnIn) {
    for (const lang of targetLangs) {
      const subPath = path.join(subsDir, `subs.${lang}.ass`);
      const finalPath = path.join(outDir, `final.${lang}.mp4`);
      await cmdOverlay({ input: cleanedPath, subs: subPath, out: finalPath });
    }
  }

  log(`done. outputs in ${outDir}`);
}

// ---------- helpers ----------

function mimeFromPath(p) {
  const ext = path.extname(p).toLowerCase();
  return (
    {
      ".mp4": "video/mp4",
      ".mov": "video/quicktime",
      ".m4v": "video/x-m4v",
      ".webm": "video/webm",
      ".mkv": "video/x-matroska",
      ".avi": "video/x-msvideo",
      ".mp3": "audio/mpeg",
      ".wav": "audio/wav",
      ".m4a": "audio/mp4",
      ".aac": "audio/aac",
      ".ogg": "audio/ogg",
      ".flac": "audio/flac",
    }[ext] || "application/octet-stream"
  );
}

// Map original-timeline segments to the post-cut timeline.
// For each original segment, drop the portion that overlaps any cut, and
// shift the remainder left by the cumulative cut duration that precedes it.
function remapSegments(segments, cuts) {
  if (!cuts || cuts.length === 0) return segments.map((s) => ({ ...s }));

  function cutOverlap(start, end) {
    let overlap = 0;
    for (const c of cuts) {
      const o = Math.max(0, Math.min(c.end, end) - Math.max(c.start, start));
      overlap += o;
    }
    return overlap;
  }

  function shiftAt(t) {
    let shift = 0;
    for (const c of cuts) {
      if (c.end <= t) shift += c.end - c.start;
      else if (c.start < t && c.end > t) shift += t - c.start;
    }
    return shift;
  }

  const out = [];
  for (const s of segments) {
    const overlap = cutOverlap(s.start, s.end);
    const newDuration = (s.end - s.start) - overlap;
    if (newDuration <= 0.05) continue;
    const newStart = s.start - shiftAt(s.start);
    const newEnd = newStart + newDuration;
    out.push({ start: newStart, end: newEnd, text: s.text });
  }
  return out;
}

function segmentsToSrt(segments) {
  const fmt = (sec) => {
    const s = Math.max(0, sec);
    const h = Math.floor(s / 3600);
    const m = Math.floor((s % 3600) / 60);
    const rest = s - h * 3600 - m * 60;
    const secInt = Math.floor(rest);
    const ms = Math.round((rest - secInt) * 1000);
    return `${String(h).padStart(2, "0")}:${String(m).padStart(2, "0")}:${String(secInt).padStart(2, "0")},${String(ms).padStart(3, "0")}`;
  };
  return segments
    .map((s, i) => `${i + 1}\n${fmt(s.start)} --> ${fmt(s.end)}\n${(s.text || "").trim()}\n`)
    .join("\n");
}

// ---------- main ----------

async function main() {
  const [, , subcommand, ...rest] = process.argv;
  if (!subcommand || subcommand === "--help" || subcommand === "-h") {
    process.stdout.write(`Usage: pipeline.mjs <subcommand> [args]

Subcommands:
  transcribe   --input <video> --out <file> [--source-lang he|en|auto] [--model ...]
  find-cuts    --transcript <file> --out <file> [--aggressive]
  apply-cuts   --input <video> --cuts <file> --out <video>
  translate    --transcript <file> [--cuts <file>] --target-langs en,he --out-dir <dir>
  overlay      --input <video> --subs <ass|srt> --out <video>
  all          --input <video> --out-dir <dir> --target-langs en,he [--source-lang auto] [--burn-in] [--aggressive]
`);
    process.exit(subcommand ? 0 : 1);
  }

  const args = parseArgs(rest);
  const cmds = {
    transcribe: cmdTranscribe,
    "find-cuts": cmdFindCuts,
    "apply-cuts": cmdApplyCuts,
    translate: cmdTranslate,
    overlay: cmdOverlay,
    all: cmdAll,
  };
  const fn = cmds[subcommand];
  if (!fn) die(`unknown subcommand: ${subcommand}`);
  await fn(args);
}

main().catch((e) => {
  process.stderr.write(`fatal: ${e.stack || e.message}\n`);
  process.exit(1);
});
