// Visual overlay composition: B-roll (full-screen takeover) and
// before/after side-by-side splits, composited onto the cleaned video
// with fade-in/out transitions.
//
// Input: a manifest describing overlays with timestamps on the
// CLEANED video timeline. Output: a single composited video.
//
// Manifest shape (overlays.json):
// {
//   "overlays": [
//     {
//       "type": "broll",
//       "src": "path/to/clip.mp4",
//       "at": 8.0,                 // start (sec) on the cleaned video
//       "duration": 4.0,           // how long the overlay shows
//       "fadeIn": 0.3,             // optional, default 0.3s
//       "fadeOut": 0.3             // optional, default 0.3s
//     },
//     {
//       "type": "before-after",
//       "before": "path/to/before.jpg",
//       "after":  "path/to/after.jpg",
//       "at": 18.0,
//       "duration": 4.0,
//       "fadeIn": 0.3,
//       "fadeOut": 0.3,
//       "divider": "#FFFFFF"       // optional vertical-line color
//     }
//   ]
// }

import fs from "node:fs";
import path from "node:path";
import { runFfmpeg, ffprobeJson } from "./ffmpeg.mjs";

const IMAGE_EXTS = new Set([".jpg", ".jpeg", ".png", ".webp", ".bmp"]);

function isImage(p) {
  return IMAGE_EXTS.has(path.extname(p).toLowerCase());
}

async function videoDimensions(filePath) {
  const meta = await ffprobeJson(filePath);
  const v = (meta.streams || []).find((s) => s.codec_type === "video");
  if (!v) throw new Error(`No video stream in ${filePath}`);
  return { width: Number(v.width), height: Number(v.height) };
}

async function videoFps(filePath) {
  const meta = await ffprobeJson(filePath);
  const v = (meta.streams || []).find((s) => s.codec_type === "video");
  if (!v) return 30;
  const rate = v.avg_frame_rate || v.r_frame_rate || "30/1";
  const [num, den] = rate.split("/").map(Number);
  if (Number.isFinite(num) && Number.isFinite(den) && den > 0) return num / den;
  return 30;
}

// Build the filter graph for a list of overlays on top of [0:v] / [0:a].
// Also returns the per-overlay -i argument fragments to add to the ffmpeg
// invocation, IN ORDER (this is critical — stream indices match input order).
function buildFilterGraph(overlays, mainW, mainH, mainFps) {
  const filterParts = [];
  const inputArgs = []; // per-overlay -i arguments (with -loop -t for stills)
  let inputIdx = 1; // 0 is the main video; each overlay consumes 1 or 2 indices
  let prevStream = "[0:v]";

  for (let i = 0; i < overlays.length; i++) {
    const ov = overlays[i];
    const fadeIn = Number(ov.fadeIn ?? 0.3);
    const fadeOut = Number(ov.fadeOut ?? 0.3);
    const duration = Number(ov.duration);
    if (!Number.isFinite(duration) || duration <= 0) {
      throw new Error(`overlay #${i}: invalid duration ${ov.duration}`);
    }
    const at = Number(ov.at);
    if (!Number.isFinite(at) || at < 0) {
      throw new Error(`overlay #${i}: invalid 'at' ${ov.at}`);
    }
    const fadeOutStart = Math.max(0, duration - fadeOut);

    let overlayStream;

    if (ov.type === "broll") {
      if (!ov.src) throw new Error(`overlay #${i} (broll): missing 'src'`);
      const isImg = isImage(ov.src);
      if (isImg) inputArgs.push("-loop", "1", "-t", String(duration), "-i", ov.src);
      else inputArgs.push("-i", ov.src);
      const idx = inputIdx++;
      overlayStream = `[ovl_${i}]`;
      filterParts.push(
        `[${idx}:v]` +
          `scale=${mainW}:${mainH}:force_original_aspect_ratio=decrease,` +
          `pad=${mainW}:${mainH}:(ow-iw)/2:(oh-ih)/2:color=black,setsar=1,` +
          `fps=${mainFps},` +
          `trim=duration=${duration.toFixed(3)},setpts=PTS-STARTPTS,` +
          `format=yuva420p,` +
          `fade=t=in:st=0:d=${fadeIn.toFixed(3)}:alpha=1,` +
          `fade=t=out:st=${fadeOutStart.toFixed(3)}:d=${fadeOut.toFixed(3)}:alpha=1,` +
          `setpts=PTS+${at.toFixed(3)}/TB` +
          `${overlayStream}`,
      );
    } else if (ov.type === "before-after") {
      if (!ov.before || !ov.after) {
        throw new Error(`overlay #${i} (before-after): need both 'before' and 'after'`);
      }
      // Each still gets its own -loop input (always images here).
      inputArgs.push("-loop", "1", "-t", String(duration), "-i", ov.before);
      inputArgs.push("-loop", "1", "-t", String(duration), "-i", ov.after);
      const bIdx = inputIdx++;
      const aIdx = inputIdx++;
      const half = Math.floor(mainW / 2);
      const dividerColor = ov.divider || "white@0.8";
      overlayStream = `[ovl_${i}]`;
      // before/after labels are intentionally omitted — ffmpeg-static is
      // built without libfreetype, so drawtext isn't available. The
      // divider line still makes the split obvious; bake labels into the
      // image assets if you want them.
      filterParts.push(
        `[${bIdx}:v]scale=${half}:${mainH}:force_original_aspect_ratio=increase,` +
          `crop=${half}:${mainH},setsar=1,fps=${mainFps}[ba_b_${i}];` +
          `[${aIdx}:v]scale=${half}:${mainH}:force_original_aspect_ratio=increase,` +
          `crop=${half}:${mainH},setsar=1,fps=${mainFps}[ba_a_${i}];` +
          `[ba_b_${i}][ba_a_${i}]hstack=inputs=2,` +
          `drawbox=x=${half - 2}:y=0:w=4:h=${mainH}:color=${dividerColor}:t=fill,` +
          `trim=duration=${duration.toFixed(3)},setpts=PTS-STARTPTS,` +
          `format=yuva420p,` +
          `fade=t=in:st=0:d=${fadeIn.toFixed(3)}:alpha=1,` +
          `fade=t=out:st=${fadeOutStart.toFixed(3)}:d=${fadeOut.toFixed(3)}:alpha=1,` +
          `setpts=PTS+${at.toFixed(3)}/TB` +
          `${overlayStream}`,
      );
    } else {
      throw new Error(`overlay #${i}: unknown type '${ov.type}'`);
    }

    // Composite this overlay onto the running main stream.
    const isLast = i === overlays.length - 1;
    const outLabel = isLast ? "[outv]" : `[mc_${i}]`;
    filterParts.push(
      `${prevStream}${overlayStream}` +
        `overlay=enable='between(t,${at.toFixed(3)},${(at + duration).toFixed(3)})':` +
        `eof_action=pass${outLabel}`,
    );
    prevStream = outLabel;
  }

  return { filter: filterParts.join(";"), inputArgs };
}

export async function compose(inputVideo, manifestPath, outputPath) {
  const manifest = JSON.parse(fs.readFileSync(manifestPath, "utf8"));
  const overlays = Array.isArray(manifest.overlays) ? manifest.overlays : [];
  if (overlays.length === 0) {
    throw new Error(`manifest has no overlays`);
  }

  const { width: mainW, height: mainH } = await videoDimensions(inputVideo);
  const mainFps = await videoFps(inputVideo);

  // Validate sources up-front so we fail before re-encoding.
  for (const ov of overlays) {
    const srcs = ov.type === "broll" ? [ov.src] : [ov.before, ov.after];
    for (const s of srcs) {
      if (!s || !fs.existsSync(s)) {
        throw new Error(`overlay source missing: ${s}`);
      }
    }
  }

  const { filter, inputArgs } = buildFilterGraph(overlays, mainW, mainH, mainFps);

  await runFfmpeg([
    "-y",
    "-i", inputVideo,
    ...inputArgs,
    "-filter_complex", filter,
    "-map", "[outv]",
    "-map", "0:a?",
    "-c:v", "libx264",
    "-preset", "medium",
    "-crf", "20",
    "-c:a", "aac",
    "-b:a", "192k",
    "-movflags", "+faststart",
    outputPath,
  ]);

  return outputPath;
}
