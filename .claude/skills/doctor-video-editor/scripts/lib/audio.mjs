// Audio extraction from a video file via ffmpeg.
// Used to produce a small, transcription-ready audio file for ElevenLabs Scribe.

import { runFfmpeg } from "./ffmpeg.mjs";

export async function extractAudio(videoPath, audioPath, {
  format = "flac",   // flac | wav | mp3 | aac
  sampleRate = 16000,
  channels = 1,
} = {}) {
  const args = ["-y", "-i", videoPath, "-vn", "-ar", String(sampleRate), "-ac", String(channels)];
  switch (format) {
    case "flac":
      args.push("-c:a", "flac");
      break;
    case "wav":
      args.push("-c:a", "pcm_s16le");
      break;
    case "mp3":
      args.push("-c:a", "libmp3lame", "-b:a", "64k");
      break;
    case "aac":
      args.push("-c:a", "aac", "-b:a", "64k");
      break;
    default:
      throw new Error(`unsupported audio format: ${format}`);
  }
  args.push(audioPath);
  await runFfmpeg(args);
  return audioPath;
}
