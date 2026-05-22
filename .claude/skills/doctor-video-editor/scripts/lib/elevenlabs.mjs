// ElevenLabs Scribe (speech-to-text) client.
// Word-level timestamps + speaker diarization + audio events.

import fs from "node:fs";
import path from "node:path";

const API_BASE = "https://api.elevenlabs.io/v1";

function apiKey() {
  const k = process.env.ELEVENLABS_API_KEY;
  if (!k) throw new Error("ELEVENLABS_API_KEY is not set");
  return k;
}

// ElevenLabs uses ISO 639-3 codes. Map common 639-1 inputs.
const LANG_MAP = {
  he: "heb", en: "eng", ar: "ara", es: "spa", fr: "fra",
  de: "deu", it: "ita", ru: "rus", pt: "por", nl: "nld",
  pl: "pol", tr: "tur", uk: "ukr", ja: "jpn", ko: "kor",
  zh: "zho", hi: "hin",
};

function mapLang(code) {
  if (!code || code === "auto") return undefined;
  if (code.length === 3) return code;
  return LANG_MAP[code.toLowerCase()];
}

const MIME_FOR = {
  ".flac": "audio/flac",
  ".wav": "audio/wav",
  ".mp3": "audio/mpeg",
  ".m4a": "audio/mp4",
  ".aac": "audio/aac",
  ".ogg": "audio/ogg",
  ".opus": "audio/opus",
  ".mp4": "video/mp4",
  ".mov": "video/quicktime",
  ".webm": "video/webm",
  ".mkv": "video/x-matroska",
};

export async function transcribeFile(filePath, {
  model = "scribe_v1",
  languageCode,
  diarize = true,
  tagAudioEvents = true,
  numSpeakers,
  timestampsGranularity = "word",
  timeoutMs = 30 * 60 * 1000,
} = {}) {
  const stat = fs.statSync(filePath);
  const ext = path.extname(filePath).toLowerCase();
  const mime = MIME_FOR[ext] || "application/octet-stream";

  process.stderr.write(
    `[elevenlabs] uploading ${path.basename(filePath)} (${(stat.size / 1024 / 1024).toFixed(1)} MB, ${mime})\n`,
  );

  const buffer = fs.readFileSync(filePath);
  const form = new FormData();
  form.append("file", new Blob([buffer], { type: mime }), path.basename(filePath));
  form.append("model_id", model);
  const mapped = mapLang(languageCode);
  if (mapped) form.append("language_code", mapped);
  form.append("diarize", diarize ? "true" : "false");
  form.append("tag_audio_events", tagAudioEvents ? "true" : "false");
  if (numSpeakers) form.append("num_speakers", String(numSpeakers));
  form.append("timestamps_granularity", timestampsGranularity);

  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(new Error("ElevenLabs Scribe timeout")), timeoutMs);
  let res;
  try {
    res = await fetch(`${API_BASE}/speech-to-text`, {
      method: "POST",
      headers: { "xi-api-key": apiKey() },
      body: form,
      signal: controller.signal,
    });
  } finally {
    clearTimeout(timer);
  }

  if (!res.ok) {
    const body = await res.text();
    throw new Error(`ElevenLabs ${res.status}: ${body.slice(0, 800)}`);
  }
  return await res.json();
}

// Normalize Scribe response to our internal transcript format:
//   { detected_language, transcriber, words: [...], segments: [...] }
// where segments are derived by grouping words at natural pauses.
export function toInternalTranscript(elJson) {
  const rawWords = Array.isArray(elJson.words) ? elJson.words : [];
  const words = rawWords
    .filter((w) => typeof w.start === "number" && typeof w.end === "number")
    .map((w) => ({
      text: String(w.text || ""),
      start: w.start,
      end: w.end,
      type: w.type || "word", // "word" | "spacing" | "audio_event"
      speaker: w.speaker_id || null,
    }));

  const PAUSE_BREAK = 0.6; // seconds of silence between words → segment break
  const MAX_WORDS_PER_SEG = 14;
  const segments = [];
  let buf = [];
  const contentWords = words.filter((w) => w.type === "word");

  for (let i = 0; i < contentWords.length; i++) {
    const w = contentWords[i];
    buf.push(w);
    const next = contentWords[i + 1];
    const gap = next ? next.start - w.end : Infinity;
    const endsSentence = /[.!?。！？]$/.test(w.text.trim());
    if (gap > PAUSE_BREAK || endsSentence || buf.length >= MAX_WORDS_PER_SEG || !next) {
      const text = buf
        .map((x) => x.text)
        .join(" ")
        .replace(/\s+([.,!?;:])/g, "$1")
        .replace(/\s+/g, " ")
        .trim();
      if (text) {
        segments.push({
          start: buf[0].start,
          end: buf[buf.length - 1].end,
          text,
        });
      }
      buf = [];
    }
  }

  return {
    detected_language: elJson.language_code || null,
    language_probability: elJson.language_probability ?? null,
    transcriber: "elevenlabs",
    full_text: typeof elJson.text === "string" ? elJson.text : null,
    segments,
    words,
  };
}
