// Thin wrapper around ffmpeg-static / ffprobe-static.

import { spawn } from "node:child_process";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);

function resolveBinary(pkg) {
  const mod = require(pkg);
  // ffmpeg-static exports the binary path directly; ffprobe-static exports {path}.
  return typeof mod === "string" ? mod : mod.path;
}

export const FFMPEG = resolveBinary("ffmpeg-static");
export const FFPROBE = resolveBinary("ffprobe-static");

export function runFfmpeg(args, { onStderr } = {}) {
  return new Promise((resolve, reject) => {
    const child = spawn(FFMPEG, args, { stdio: ["ignore", "ignore", "pipe"] });
    let err = "";
    child.stderr.on("data", (chunk) => {
      const s = chunk.toString();
      err += s;
      if (onStderr) onStderr(s);
    });
    child.on("error", reject);
    child.on("close", (code) => {
      if (code === 0) resolve();
      else reject(new Error(`ffmpeg exited ${code}\n${err.slice(-2000)}`));
    });
  });
}

export function ffprobeJson(filePath) {
  return new Promise((resolve, reject) => {
    const child = spawn(
      FFPROBE,
      [
        "-v",
        "error",
        "-print_format",
        "json",
        "-show_format",
        "-show_streams",
        filePath,
      ],
      { stdio: ["ignore", "pipe", "pipe"] },
    );
    let out = "";
    let err = "";
    child.stdout.on("data", (c) => (out += c));
    child.stderr.on("data", (c) => (err += c));
    child.on("error", reject);
    child.on("close", (code) => {
      if (code !== 0) return reject(new Error(`ffprobe exited ${code}: ${err}`));
      try {
        resolve(JSON.parse(out));
      } catch (e) {
        reject(new Error(`ffprobe JSON parse failed: ${e.message}`));
      }
    });
  });
}

export async function getDuration(filePath) {
  const meta = await ffprobeJson(filePath);
  const d = parseFloat(meta.format?.duration);
  if (!Number.isFinite(d)) throw new Error(`Could not determine duration of ${filePath}`);
  return d;
}
