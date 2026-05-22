#!/usr/bin/env node
// Main entry point for the doctor-video-editor skill.
// Subcommands: transcribe, find-cuts, apply-cuts, translate, overlay, all.

import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { buildMediaPart, generateJson, DEFAULT_MODEL } from "./lib/gemini.mjs";
import { runFfmpeg, ffprobeJson, getDuration } from "./lib/ffmpeg.mjs";
import { buildAss, buildAssWordByWord } from "./lib/ass.mjs";
import { transcribeFile as elevenlabsTranscribe, toInternalTranscript } from "./lib/elevenlabs.mjs";
import { extractAudio } from "./lib/audio.mjs";
import { detectDisfluencies, remapWords } from "./lib/disfluency.mjs";
import { detectHiddenDisfluencies } from "./lib/audio-disfluency.mjs";
import { buildProfile } from "./lib/profile.mjs";
import { compose as composeOverlays } from "./lib/overlay.mjs";
import { buildManifestFromDir } from "./lib/manifest.mjs";

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

  // Pick transcriber. Defaults to ElevenLabs when its key is available, since
  // it gives word-level + speaker info that the rest of the pipeline depends
  // on for accurate filler / side-talk cuts. Force one with --transcriber.
  const explicit = (args.transcriber || "").toString().toLowerCase();
  let useElevenlabs;
  if (explicit === "elevenlabs") useElevenlabs = true;
  else if (explicit === "gemini") useElevenlabs = false;
  else useElevenlabs = !!process.env.ELEVENLABS_API_KEY;

  if (useElevenlabs) {
    log(`transcribing ${input} via ElevenLabs Scribe (source-lang=${sourceLang})`);
    const audioPath = path.join(
      path.dirname(out),
      path.basename(out, path.extname(out)) + ".audio.flac",
    );
    ensureDir(path.dirname(audioPath));
    log(`extracting audio to ${audioPath}`);
    await extractAudio(input, audioPath, { format: "flac" });
    const raw = await elevenlabsTranscribe(audioPath, {
      languageCode: sourceLang,
      diarize: true,
      tagAudioEvents: true,
    });
    const data = toInternalTranscript(raw);
    writeJson(out, data);
    log(
      `wrote transcript (${data.transcriber}, ${data.words.length} words / ${data.segments.length} segments, lang=${data.detected_language}) to ${out}`,
    );
    return;
  }

  log(`transcribing ${input} via Gemini (source-lang=${sourceLang}, model=${model})`);

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
  data.transcriber = "gemini";
  writeJson(out, data);
  log(`wrote transcript (gemini, ${data.segments.length} segments) to ${out}`);
}

async function cmdFindCuts(args) {
  const transcriptPath = need(args, "transcript");
  const out = need(args, "out");
  const aggressive = !!args.aggressive;
  const videoPath = args.video; // optional but strongly recommended for Gemini accuracy
  const model = args.model || DEFAULT_MODEL;
  const detector = (args.detector || "auto").toString().toLowerCase();

  const transcript = readJson(transcriptPath);

  // Programmatic path — runs whenever we have word-level data (ElevenLabs).
  // It is more accurate and deterministic than the LLM detector for the
  // disfluency classes the user actually wants cut (fillers, stutters,
  // pauses, side talk).
  const hasWords = Array.isArray(transcript.words) && transcript.words.length > 0;
  const useProgrammatic = detector === "programmatic" || (detector === "auto" && hasWords);

  if (useProgrammatic) {
    if (!hasWords) {
      die("detector=programmatic requires word-level transcript (use --transcriber elevenlabs)");
    }

    // Phase 1: analyze the transcript to derive a per-video editing profile.
    // The profile's detectorOpts override the conservative built-in defaults
    // unless the caller explicitly passed --aggressive or --pause-threshold.
    const profile = buildProfile(transcript.words);
    log(
      `profile: style=${profile.style}, ${profile.speech.wpm} wpm, ` +
        `${profile.fillers.count} fillers, ${profile.speakers.count} speaker(s), ` +
        `natural pause ${profile.pauses.natural}s → threshold ${profile.detectorOpts.longPauseThreshold}s`,
    );

    // Phase 2: build detector opts. Profile is the base; CLI flags override.
    const detectorOpts = { ...profile.detectorOpts };
    if (aggressive) detectorOpts.aggressive = true;
    if (args["pause-threshold"] !== undefined && args["pause-threshold"] !== true) {
      detectorOpts.longPauseThreshold = parseFloat(args["pause-threshold"]);
    }

    log(
      `detecting cuts programmatically over ${transcript.words.length} words ` +
        `(aggressive=${detectorOpts.aggressive}, pauseThreshold=${detectorOpts.longPauseThreshold}s)`,
    );
    const result = detectDisfluencies(transcript.words, detectorOpts);
    let allCuts = [...result.cuts];

    // Phase 3: cross-reference audio energy against the transcript to find
    // disfluencies the ASR silently filtered out (e.g. brief "אה"/"uh" that
    // ElevenLabs Scribe doesn't tag). The audio file is the one
    // cmdTranscribe extracted for Scribe, sitting next to the transcript.
    const audioPath = transcriptPath.replace(/\.json$/i, ".audio.flac");
    let hiddenCount = 0;
    if (fs.existsSync(audioPath)) {
      log(`scanning audio (${path.basename(audioPath)}) for hidden disfluencies...`);
      try {
        const hidden = await detectHiddenDisfluencies(audioPath, transcript.words);
        hiddenCount = hidden.cuts.length;
        allCuts = allCuts.concat(hidden.cuts);
      } catch (e) {
        log(`warning: hidden-disfluency scan failed (${e.message}); continuing without it`);
      }
    }

    // Sort + merge overlapping/adjacent cuts across all sources.
    allCuts.sort((a, b) => a.start - b.start);
    const merged = [];
    for (const c of allCuts) {
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

    const removed = merged.reduce((acc, c) => acc + (c.end - c.start), 0);
    writeJson(out, {
      cuts: merged,
      primary_speaker: result.primary_speaker,
      speakers: result.speakers,
      detector: "programmatic+audio",
      profile,
      detectorOpts,
    });
    log(
      `wrote ${merged.length} cuts (~${removed.toFixed(1)}s removed, primary=${result.primary_speaker || "n/a"}, +${hiddenCount} hidden from audio scan) to ${out}`,
    );
    return;
  }

  log(
    `detecting cuts via Gemini (aggressive=${aggressive}, video=${videoPath ? "yes" : "no"}) over ${transcript.segments.length} segments`,
  );

  const sys =
    "You are a video editor specializing in talking-head doctor testimonials. " +
    "You decide which spans of audio to CUT to produce a clean, professional, " +
    "fast-paced final edit. You ONLY cut sub-word and sub-phrase disfluencies — " +
    "filler sounds, audible hesitations, repeated words, silent pauses. " +
    "You NEVER cut full sentences, even if they sound awkward or off-topic — " +
    "the editor will decide later whether to remove larger content.";

  const policy = aggressive
    ? "AGGRESSIVE mode: in addition to obvious disfluencies, you may also remove repeated phrases (when the same idea is restated within ~3 seconds) and clearly off-topic asides. Cap total removed time at 25% of the video."
    : "CONSERVATIVE mode (default): ONLY cut these specific things — (a) filler sounds: אממ / אהה / אה / אם / umm / uhh / like, (b) word-level stutters and immediate repetitions of the same word, (c) silent pauses longer than 1.2 seconds, (d) audible breaths longer than 0.6s. DO NOT cut full sentences. DO NOT cut content even if it sounds awkward or off-topic — those decisions belong to the human editor.";

  const promptHeader = videoPath
    ? [
        "Look at the attached video, listen to the audio, and produce a list of time ranges to CUT.",
        "The transcript below is a ROUGH starting point — its timestamps may be off by 0.5–2 seconds.",
        "Trust your ears over the transcript: locate each disfluency BY LISTENING and report",
        "millisecond-accurate start/end times aligned to the actual audio.",
      ]
    : [
        "Given ONLY this timestamped transcript, produce a list of time ranges to CUT.",
        "(For higher accuracy, re-run this step with --video so cuts can be aligned to the actual audio.)",
      ];

  const userPrompt = [
    ...promptHeader,
    "",
    `Policy: ${policy}`,
    "",
    "Rules:",
    "- Ranges must be expressed in absolute seconds from the start of the video.",
    "- Do not overlap ranges. Order them ascending.",
    "- Prefer many short cuts over a few long ones.",
    "- For each cut include a short reason (filler|stutter|repeat|long-pause|breath).",
    "- Do NOT use the reason 'false-start' or 'tangent' — those would imply cutting full content.",
    "",
    "Return STRICT JSON:",
    "{",
    '  "cuts": [',
    '    { "start": <sec>, "end": <sec>, "reason": "<reason>", "note": "<optional human note>" }',
    "  ]",
    "}",
    "",
    "Reference transcript:",
    JSON.stringify(transcript, null, 2),
  ].join("\n");

  const parts = [];
  if (videoPath) {
    const mimeType = mimeFromPath(videoPath);
    parts.push(await buildMediaPart(videoPath, mimeType));
  }
  parts.push({ text: userPrompt });

  const data = await generateJson({
    model,
    parts,
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
  const requestedCrossfade = parseFloat(args.crossfade ?? "0");
  const transition = (args.transition || "fade").toString();
  const musicPath = args.music && args.music !== true ? String(args.music) : null;
  const musicVolume = parseFloat(args["music-volume"] ?? "0.08");

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

  // Decide whether to use crossfades. xfade needs each side to be at least the
  // crossfade duration. If any keep is too short we shrink the requested
  // crossfade (or fall back to a hard cut for this run if shrinking it
  // would make it imperceptible).
  let crossfade = Math.max(0, requestedCrossfade);
  if (crossfade > 0 && keeps.length > 1) {
    const shortest = Math.min(...keeps.map((k) => k.end - k.start));
    const maxSafe = Math.max(0, (shortest - 0.05) * 0.5);
    if (maxSafe < 0.04) {
      log(
        `warning: shortest keep is ${shortest.toFixed(2)}s — too short for any crossfade; using hard cuts`,
      );
      crossfade = 0;
    } else if (maxSafe < crossfade) {
      log(
        `warning: clamping crossfade ${requestedCrossfade}s → ${maxSafe.toFixed(2)}s to fit shortest keep (${shortest.toFixed(2)}s)`,
      );
      crossfade = maxSafe;
    }
  }

  log(
    `assembling ${keeps.length} keep intervals into ${out} (transition=${crossfade > 0 ? `${transition}/${crossfade.toFixed(2)}s` : "hard cut"}${musicPath ? `, music=${path.basename(musicPath)}@${musicVolume}` : ""})`,
  );
  ensureDir(path.dirname(out));

  // xfade requires constant frame rate; `trim` doesn't preserve it. Pin the
  // post-trim segments to the source frame rate so xfade can chain them.
  const fps = crossfade > 0 ? await detectFps(input) : null;
  const vTail = fps ? `,fps=${fps}` : "";

  // When mixing in music, the speech chain outputs to [outa_speech], then a
  // separate music chain plus amix produces the final [outa]. Without music,
  // the speech chain outputs directly to [outa].
  const speechOutLabel = musicPath ? "outa_speech" : "outa";

  const filterParts = [];
  for (let i = 0; i < keeps.length; i++) {
    const { start, end } = keeps[i];
    filterParts.push(
      `[0:v]trim=start=${start.toFixed(3)}:end=${end.toFixed(3)},setpts=PTS-STARTPTS${vTail}[v${i}]`,
    );
    filterParts.push(
      `[0:a]atrim=start=${start.toFixed(3)}:end=${end.toFixed(3)},asetpts=PTS-STARTPTS[a${i}]`,
    );
  }

  if (crossfade > 0 && keeps.length > 1) {
    // Chain xfade for video and acrossfade for audio. After joining clip k+1
    // onto the running output, the new running duration is
    // running + new_clip - crossfade.
    let prevV = "v0";
    let prevA = "a0";
    let runningDur = keeps[0].end - keeps[0].start;
    for (let i = 1; i < keeps.length; i++) {
      const curDur = keeps[i].end - keeps[i].start;
      const offset = Math.max(0, runningDur - crossfade);
      const isLast = i === keeps.length - 1;
      const outV = isLast ? "outv" : `vx${i}`;
      const outA = isLast ? speechOutLabel : `ax${i}`;
      filterParts.push(
        `[${prevV}][v${i}]xfade=transition=${transition}:duration=${crossfade.toFixed(3)}:offset=${offset.toFixed(3)}[${outV}]`,
      );
      filterParts.push(
        `[${prevA}][a${i}]acrossfade=d=${crossfade.toFixed(3)}[${outA}]`,
      );
      prevV = outV;
      prevA = outA;
      runningDur = runningDur + curDur - crossfade;
    }
  } else {
    const concatInputs = keeps.map((_, i) => `[v${i}][a${i}]`).join("");
    filterParts.push(`${concatInputs}concat=n=${keeps.length}:v=1:a=1[outv][${speechOutLabel}]`);
  }

  // Cleaned-output duration (sum of keep durations less crossfade overlaps).
  const cleanedDur = keeps.reduce((acc, k) => acc + (k.end - k.start), 0)
    - (crossfade > 0 && keeps.length > 1 ? (keeps.length - 1) * crossfade : 0);

  // Music mixing chain: loop the music file forever, trim to cleaned-output
  // length, scale by volume, fade in/out, sidechain-duck under the speech,
  // then mix.
  if (musicPath) {
    if (!fs.existsSync(musicPath)) die(`music file not found: ${musicPath}`);
    const fadeIn = Math.min(1.0, cleanedDur * 0.05);
    const fadeOutStart = Math.max(0, cleanedDur - 1.5);
    filterParts.push(
      `[1:a]aloop=loop=-1:size=2e9,atrim=duration=${cleanedDur.toFixed(3)},asetpts=PTS-STARTPTS,` +
        `volume=${musicVolume.toFixed(3)},` +
        `afade=t=in:st=0:d=${fadeIn.toFixed(3)},` +
        `afade=t=out:st=${fadeOutStart.toFixed(3)}:d=1.5` +
        `[music_pre]`,
    );
    filterParts.push(`[outa_speech]asplit=2[speech_out][speech_key]`);
    filterParts.push(
      `[music_pre][speech_key]sidechaincompress=threshold=0.05:ratio=8:attack=10:release=300:level_sc=4[music_ducked]`,
    );
    filterParts.push(
      `[speech_out][music_ducked]amix=inputs=2:duration=first:dropout_transition=0,` +
        `dynaudnorm=p=0.71:m=8` +
        `[outa]`,
    );
  }

  const filterComplex = filterParts.join(";");

  const ffArgs = ["-y", "-i", input];
  if (musicPath) ffArgs.push("-i", musicPath);
  ffArgs.push(
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
  );
  await runFfmpeg(ffArgs);

  // Also emit a "kept-segments" timing map so subtitle generation can remap
  // original timestamps onto the cleaned timeline.
  const mapPath = out + ".keeps.json";
  writeJson(mapPath, { source: input, duration, keeps, crossfade, music: musicPath ? path.basename(musicPath) : null });
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
  const wordByWord = !!args["word-by-word"];
  const crossfade = parseFloat(args.crossfade ?? "0");
  ensureDir(outDir);

  const transcript = readJson(transcriptPath);
  const cuts = cutsPath ? (readJson(cutsPath).cuts || []) : [];

  const totalDuration = estimateTranscriptDuration(transcript);
  const keeps = computeKeepsFromCuts(cuts, totalDuration);

  // Two-step: (1) remap to post-cut timeline assuming hard cuts;
  // (2) shift back by k*crossfade where k is the keep index, to land on the
  // actual cleaned-video timeline.
  let remappedSegs = remapSegments(transcript.segments, cuts);
  remappedSegs = adjustForCrossfade(remappedSegs, keeps, crossfade);

  let remappedWords = Array.isArray(transcript.words)
    ? remapWords(transcript.words, cuts)
    : null;
  if (remappedWords) {
    remappedWords = adjustForCrossfade(remappedWords, keeps, crossfade);
  }

  log(
    `remapped ${transcript.segments.length} → ${remappedSegs.length} segments` +
      (remappedWords ? `, ${transcript.words.length} → ${remappedWords.length} words` : "") +
      (crossfade > 0 ? `, crossfade ${crossfade}s applied` : ""),
  );

  const sourceLang = String(transcript.detected_language || "").toLowerCase();
  const sourceShort = sourceLang.slice(0, 2);

  for (const lang of targetLangs) {
    const langShort = lang.toLowerCase().slice(0, 2);
    const sameLang = sourceShort && langShort === sourceShort;

    // Word-by-word output uses the original (untranslated) words, so it only
    // makes sense for the source language. If the user asked for word-by-word
    // on a non-source language, fall back to segment-level + a warning.
    if (wordByWord && sameLang && remappedWords) {
      log(`building word-by-word ${lang} subtitles from ${remappedWords.length} words`);
      writeAssAndSrt(outDir, lang, buildAssWordByWord(remappedWords), remappedSegs);
      continue;
    }
    if (wordByWord && !sameLang) {
      log(
        `note: word-by-word for ${lang} not supported (source is ${sourceLang || "unknown"}); using segment-level`,
      );
    }
    if (wordByWord && sameLang && !remappedWords) {
      log(`note: --word-by-word requested but transcript has no word data; using segment-level`);
    }

    // Same-language and no word-by-word: skip Gemini translate and use the
    // source transcript directly.
    if (sameLang) {
      log(`emitting ${lang} subtitles directly from source transcript (same language)`);
      writeAssAndSrt(outDir, lang, buildAss(remappedSegs), remappedSegs);
      continue;
    }

    log(`translating to ${lang} via Gemini...`);
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
      JSON.stringify(remappedSegs, null, 2),
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
    writeAssAndSrt(outDir, lang, buildAss(data.segments), data.segments);
  }
}

function writeAssAndSrt(outDir, lang, assContent, segmentsForSrt) {
  const assPath = path.join(outDir, `subs.${lang}.ass`);
  fs.writeFileSync(assPath, assContent);
  const srtPath = path.join(outDir, `subs.${lang}.srt`);
  fs.writeFileSync(srtPath, segmentsToSrt(segmentsForSrt));
  log(`wrote ${assPath} and ${srtPath}`);
}

async function cmdOverlay(args) {
  const input = need(args, "input");
  const subs = need(args, "subs");
  const out = need(args, "out");
  const fontsDir = args["fonts-dir"] || path.resolve(
    path.dirname(fileURLToPath(import.meta.url)),
    "..",
    "assets",
    "fonts",
  );

  log(`burning ${subs} into ${input} -> ${out} (fonts: ${fontsDir})`);
  ensureDir(path.dirname(out));

  // ass filter automatically uses the styling embedded in the .ass file.
  // ffmpeg's filter parser is finicky about Windows paths — normalize
  // backslashes to forward slashes (accepted on all platforms), then escape
  // the drive-letter colon and any single quotes.
  const escape = (p) => p.replace(/\\/g, "/").replace(/:/g, "\\:").replace(/'/g, "\\'");
  const subsEscaped = escape(subs);
  const fontsArg = fs.existsSync(fontsDir) ? `:fontsdir='${escape(fontsDir)}'` : "";
  const filter = subs.toLowerCase().endsWith(".ass")
    ? `ass='${subsEscaped}'${fontsArg}`
    : `subtitles='${subsEscaped}'${fontsArg}`;

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

// Concatenate a list of videos into one. All inputs are re-encoded into the
// concat output so codec/resolution mismatches are resolved gracefully.
async function concatVideos(inputs, out) {
  if (inputs.length === 0) throw new Error("concatVideos: no inputs");
  if (inputs.length === 1) {
    fs.copyFileSync(inputs[0], out);
    return out;
  }
  const ffArgs = ["-y"];
  for (const i of inputs) ffArgs.push("-i", i);
  // Normalize all inputs to the first input's resolution / fps before
  // concat, so mixed sources don't error out.
  const firstDims = await ffprobeJson(inputs[0]);
  const v = (firstDims.streams || []).find((s) => s.codec_type === "video");
  const W = Number(v?.width || 1080);
  const H = Number(v?.height || 1920);
  const r = v?.avg_frame_rate || v?.r_frame_rate || "30/1";
  const [rn, rd] = r.split("/").map(Number);
  const fps = Number.isFinite(rn) && Number.isFinite(rd) && rd > 0 ? Math.round((rn / rd) * 1000) / 1000 : 30;

  const filterParts = [];
  for (let i = 0; i < inputs.length; i++) {
    filterParts.push(
      `[${i}:v]scale=${W}:${H}:force_original_aspect_ratio=decrease,` +
        `pad=${W}:${H}:(ow-iw)/2:(oh-ih)/2:color=black,setsar=1,fps=${fps}[v${i}]`,
    );
    filterParts.push(`[${i}:a]aresample=async=1[a${i}]`);
  }
  const concatInputs = inputs.map((_, i) => `[v${i}][a${i}]`).join("");
  filterParts.push(`${concatInputs}concat=n=${inputs.length}:v=1:a=1[outv][outa]`);
  ffArgs.push(
    "-filter_complex", filterParts.join(";"),
    "-map", "[outv]",
    "-map", "[outa]",
    "-c:v", "libx264",
    "-preset", "medium",
    "-crf", "20",
    "-c:a", "aac",
    "-b:a", "192k",
    "-movflags", "+faststart",
    out,
  );
  await runFfmpeg(ffArgs);
  return out;
}

// Mix a music bed underneath an existing video's audio. Loops the music to
// match the video length, scales by volume, fades in/out, and applies
// sidechain compression keyed off the dialogue so the bed automatically
// ducks under speech and rises during pauses.
async function mixMusicOnto(input, musicPath, out, opts = {}) {
  const { volume = 0.08 } = opts;
  if (!fs.existsSync(musicPath)) throw new Error(`music file not found: ${musicPath}`);
  const dur = await getDuration(input);
  const fadeIn = Math.min(1.0, dur * 0.05);
  const fadeOutStart = Math.max(0, dur - 1.5);
  await runFfmpeg([
    "-y",
    "-i", input,
    "-i", musicPath,
    "-filter_complex",
    `[1:a]aloop=loop=-1:size=2e9,atrim=duration=${dur.toFixed(3)},asetpts=PTS-STARTPTS,` +
      `volume=${volume.toFixed(3)},` +
      `afade=t=in:st=0:d=${fadeIn.toFixed(3)},` +
      `afade=t=out:st=${fadeOutStart.toFixed(3)}:d=1.5[music_pre];` +
      `[0:a]asplit=2[speech_out][speech_key];` +
      `[music_pre][speech_key]sidechaincompress=threshold=0.05:ratio=8:attack=10:release=300:level_sc=4[music_ducked];` +
      `[speech_out][music_ducked]amix=inputs=2:duration=first:dropout_transition=0,` +
      `dynaudnorm=p=0.71:m=8[outa]`,
    "-map", "0:v",
    "-map", "[outa]",
    "-c:v", "copy",
    "-c:a", "aac",
    "-b:a", "192k",
    "-movflags", "+faststart",
    out,
  ]);
  return out;
}

async function cmdCompose(args) {
  const input = need(args, "input");
  const overlaysArg = need(args, "overlays");
  const out = need(args, "out");
  ensureDir(path.dirname(out));

  // `overlays` may be a JSON manifest or a directory of media assets.
  let manifestPath = overlaysArg;
  if (fs.statSync(overlaysArg).isDirectory()) {
    const dur = await getDuration(input);
    const manifest = buildManifestFromDir(overlaysArg, dur);
    if (manifest.overlays.length === 0) {
      die(`overlay directory ${overlaysArg} has no media files`);
    }
    manifestPath = path.join(path.dirname(out), "overlays.json");
    writeJson(manifestPath, manifest);
    log(
      `auto-built manifest from ${overlaysArg}: ${manifest.overlays.length} overlay(s) ` +
        `(${manifest.detected.videos.length} video, ${manifest.detected.single_images.length} still, ` +
        `${manifest.detected.pairs.length} before/after) → ${manifestPath}`,
    );
  }
  log(`composing overlays from ${manifestPath} onto ${input}`);
  await composeOverlays(input, manifestPath, out);
  log(`wrote composited video to ${out}`);
}

// Process an intro clip: transcribe it, find the first natural sentence
// boundary, trim everything after it, clean any disfluencies in the kept
// part, and burn Hebrew subtitles. Returns the path to the finished intro.
async function processIntro(introVideo, parentOutDir, opts) {
  const { sourceLang, wordByWord, transcriber } = opts;
  const introDir = path.join(parentOutDir, "intro");
  ensureDir(introDir);

  const transcriptPath = path.join(introDir, "transcript.json");
  await cmdTranscribe({
    input: introVideo,
    out: transcriptPath,
    "source-lang": sourceLang,
    transcriber,
  });

  const tr = readJson(transcriptPath);

  // Find the first sentence boundary: a segment ending in . ! ? OR the
  // first inter-word gap >= 0.6s. Fall back to ~5s if neither exists.
  const dur = await getDuration(introVideo);
  let boundary = null;
  for (const seg of tr.segments || []) {
    if (/[.!?]$/.test((seg.text || "").trim())) {
      boundary = seg.end + 0.15;
      break;
    }
  }
  if (boundary === null) {
    const w = (tr.words || []).filter((x) => x.type === "word");
    for (let i = 0; i < w.length - 1; i++) {
      const gap = w[i + 1].start - w[i].end;
      if (gap >= 0.6) {
        boundary = w[i].end + 0.15;
        break;
      }
    }
  }
  if (boundary === null) boundary = Math.min(5, dur);
  boundary = Math.min(boundary, dur);
  log(`intro: first sentence ends at ${boundary.toFixed(2)}s (source ${dur.toFixed(2)}s)`);

  const cutsPath = path.join(introDir, "cuts.json");
  writeJson(cutsPath, { cuts: [{ start: boundary, end: dur, reason: "intro-trim" }] });

  const cleanedPath = path.join(introDir, "cleaned.mp4");
  await cmdApplyCuts({ input: introVideo, cuts: cutsPath, out: cleanedPath, crossfade: 0 });

  const subsDir = path.join(introDir, "subs");
  await cmdTranslate({
    transcript: transcriptPath,
    cuts: cutsPath,
    "target-langs": "he",
    "out-dir": subsDir,
    "word-by-word": wordByWord,
    crossfade: 0,
  });

  const finalPath = path.join(introDir, "final.he.mp4");
  await cmdOverlay({
    input: cleanedPath,
    subs: path.join(subsDir, "subs.he.ass"),
    out: finalPath,
  });
  return finalPath;
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
  const wordByWord = !!args["word-by-word"];
  const crossfade = parseFloat(args.crossfade ?? "0");
  const transcriber = args.transcriber;
  const detector = args.detector;
  const transition = args.transition;
  const pauseThreshold = args["pause-threshold"];
  const music = args.music && args.music !== true ? String(args.music) : null;
  const musicVolume = parseFloat(args["music-volume"] ?? "0.12");
  const intro = args.intro && args.intro !== true ? String(args.intro) : null;

  if (targetLangs.length === 0) {
    die("--target-langs is required for 'all' (comma-separated, e.g. en,he)");
  }

  const transcriptPath = path.join(outDir, "transcript.json");
  const cutsPath = path.join(outDir, "cuts.json");
  const cleanedPath = path.join(outDir, "cleaned.mp4");
  const composedPath = path.join(outDir, "composed.mp4");
  const subsDir = path.join(outDir, "subs");

  await cmdTranscribe({
    input,
    out: transcriptPath,
    "source-lang": sourceLang,
    model: args.model,
    transcriber,
  });
  await cmdFindCuts({
    transcript: transcriptPath,
    out: cutsPath,
    video: input,
    aggressive,
    model: args.model,
    detector,
    "pause-threshold": pauseThreshold,
  });
  // Music is applied AFTER intro concatenation (post-mix) so the bed plays
  // continuously across the intro→main transition. Skip music in apply-cuts
  // here whenever there's an intro to concatenate; otherwise mix it in now
  // for the simpler no-intro flow.
  await cmdApplyCuts({
    input,
    cuts: cutsPath,
    out: cleanedPath,
    crossfade,
    transition,
    music: intro ? null : music,
    "music-volume": musicVolume,
  });

  // Optional overlay pass. --overlays may be either:
  //   - a JSON manifest file (overlays.json)
  //   - a directory of media files (auto-build manifest from contents)
  // If neither is passed, fall back to overlays.json or an overlay/ dir
  // next to the input video.
  let overlaysArg = args.overlays;
  if (!overlaysArg || overlaysArg === true) {
    const sidecarJson = path.join(path.dirname(input), "overlays.json");
    const sidecarDir = path.join(path.dirname(input), "overlay");
    if (fs.existsSync(sidecarJson)) overlaysArg = sidecarJson;
    else if (fs.existsSync(sidecarDir) && fs.statSync(sidecarDir).isDirectory()) overlaysArg = sidecarDir;
    else overlaysArg = null;
  }
  let videoForSubs = cleanedPath;
  if (overlaysArg) {
    let manifestPath;
    const stat = fs.statSync(overlaysArg);
    if (stat.isDirectory()) {
      const cleanedDur = await getDuration(cleanedPath);
      const manifest = buildManifestFromDir(overlaysArg, cleanedDur);
      if (manifest.overlays.length === 0) {
        log(`overlay dir ${overlaysArg} has no media — skipping compose`);
      } else {
        log(
          `auto-built overlay manifest from ${overlaysArg}: ` +
            `${manifest.overlays.length} overlay(s), placed across ${cleanedDur.toFixed(1)}s ` +
            `(${manifest.detected.videos.length} video, ${manifest.detected.single_images.length} still, ` +
            `${manifest.detected.pairs.length} before/after)`,
        );
        manifestPath = path.join(outDir, "overlays.json");
        writeJson(manifestPath, manifest);
      }
    } else {
      manifestPath = overlaysArg;
    }
    if (manifestPath) {
      await cmdCompose({ input: cleanedPath, overlays: manifestPath, out: composedPath });
      videoForSubs = composedPath;
    }
  }

  await cmdTranslate({
    transcript: transcriptPath,
    cuts: cutsPath,
    "target-langs": targetLangs.join(","),
    "out-dir": subsDir,
    model: args.model,
    "word-by-word": wordByWord,
    crossfade,
  });

  if (burnIn) {
    for (const lang of targetLangs) {
      const subPath = path.join(subsDir, `subs.${lang}.ass`);
      const finalPath = path.join(outDir, `final.${lang}.mp4`);
      await cmdOverlay({ input: videoForSubs, subs: subPath, out: finalPath });
    }
  }

  // Post-processing: intro concat + post-music mix. We do this only for
  // Hebrew (the source language) — if multiple target langs were burned,
  // the intro concatenation is skipped for the non-source variants.
  if (burnIn) {
    const mainFinal = path.join(outDir, "final.he.mp4");
    if (fs.existsSync(mainFinal)) {
      let workingPath = mainFinal;

      if (intro && fs.existsSync(intro)) {
        log(`processing intro clip ${path.basename(intro)}`);
        const introFinal = await processIntro(intro, outDir, {
          sourceLang,
          wordByWord,
          transcriber,
        });
        const combinedPath = path.join(outDir, "final.combined.mp4");
        log(`concatenating intro + main → ${path.basename(combinedPath)}`);
        await concatVideos([introFinal, mainFinal], combinedPath);
        workingPath = combinedPath;
      }

      if (intro && music) {
        const withMusic = path.join(outDir, "final.with_music.mp4");
        log(`mixing music bed across the full timeline`);
        await mixMusicOnto(workingPath, music, withMusic, { volume: musicVolume });
        workingPath = withMusic;
      }

      // Promote the post-processed result to be the canonical final.he.mp4.
      if (workingPath !== mainFinal) {
        fs.renameSync(mainFinal, path.join(outDir, "final.main_only.mp4"));
        fs.renameSync(workingPath, mainFinal);
      }
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

// Compute the complement of `cuts` within [0, totalDuration]. Used by translate
// to figure out keep indices so subtitle timestamps can be adjusted for
// crossfade offsets without needing access to the rendered video.
function computeKeepsFromCuts(cuts, totalDuration) {
  const keeps = [];
  let cursor = 0;
  for (const c of cuts || []) {
    if (c.start > cursor) keeps.push({ start: cursor, end: Math.min(c.start, totalDuration) });
    cursor = Math.max(cursor, c.end);
  }
  if (cursor < totalDuration) keeps.push({ start: cursor, end: totalDuration });
  return keeps;
}

// Detect the average frame rate of the video stream. Returns null if it can't
// be parsed. Used only when crossfade is requested (xfade needs CFR).
async function detectFps(videoPath) {
  try {
    const meta = await ffprobeJson(videoPath);
    const v = (meta.streams || []).find((s) => s.codec_type === "video");
    if (!v) return null;
    const rate = v.avg_frame_rate || v.r_frame_rate || "";
    const [num, den] = rate.split("/").map(Number);
    if (Number.isFinite(num) && Number.isFinite(den) && den > 0 && num > 0) {
      const fps = num / den;
      return Math.round(fps * 1000) / 1000;
    }
  } catch (_) {}
  return null;
}

// Best-effort guess at video duration from a transcript (no ffprobe needed).
function estimateTranscriptDuration(transcript) {
  let max = 0;
  for (const s of transcript.segments || []) if (s.end > max) max = s.end;
  for (const w of transcript.words || []) if (w.end > max) max = w.end;
  // Pad a hair so the trailing keep isn't zero-length.
  return max + 0.05;
}

// Each crossfade between adjacent keeps shrinks the output timeline by its
// duration. Items remapped to the "hard cut" timeline therefore drift right
// by k*crossfade where k is the index of their containing keep. This shifts
// them back by that amount.
function adjustForCrossfade(items, keeps, crossfade) {
  if (!(crossfade > 0) || !keeps || keeps.length < 2) return items;
  const keepStartsOut = [];
  let acc = 0;
  for (const k of keeps) {
    keepStartsOut.push(acc);
    acc += k.end - k.start;
  }
  return items.map((item) => {
    let k = 0;
    for (let i = keeps.length - 1; i >= 0; i--) {
      if (item.start + 1e-6 >= keepStartsOut[i]) {
        k = i;
        break;
      }
    }
    if (k <= 0) return item;
    const adj = k * crossfade;
    const newStart = Math.max(0, item.start - adj);
    const newEnd = Math.max(newStart + 0.04, item.end - adj);
    return { ...item, start: newStart, end: newEnd };
  });
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
  transcribe   --input <video> --out <file>
               [--source-lang he|en|auto] [--transcriber elevenlabs|gemini|auto] [--model ...]
               Default: elevenlabs when ELEVENLABS_API_KEY is set, else gemini.
  find-cuts    --transcript <file> --out <file>
               [--aggressive] [--detector programmatic|gemini|auto] [--video <video>]
               Default: programmatic when transcript has word-level data, else gemini.
  apply-cuts   --input <video> --cuts <file> --out <video>
               [--crossfade <seconds, default 0>] [--transition fade|fadeblack|wipeleft|...]
  translate    --transcript <file> [--cuts <file>] --target-langs en,he --out-dir <dir>
               [--word-by-word] [--crossfade <seconds, default 0>]
  overlay      --input <video> --subs <ass|srt> --out <video>
  all          --input <video> --out-dir <dir> --target-langs en,he
               [--source-lang auto] [--burn-in] [--aggressive]
               [--word-by-word] [--crossfade <s>] [--transition <name>]
               [--transcriber elevenlabs|gemini] [--detector programmatic|gemini]
               [--overlays <dir|json>] [--music <audio> [--music-volume 0.12]]
               [--intro <video>]   # trimmed to first sentence, prepended

Env:
  GEMINI_API_KEY        required for Gemini transcription / translation
  ELEVENLABS_API_KEY    enables ElevenLabs Scribe (word-level + diarization)
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
    compose: cmdCompose,
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
