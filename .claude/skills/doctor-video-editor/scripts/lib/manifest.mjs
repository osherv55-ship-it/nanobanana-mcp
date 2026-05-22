// Auto-build an overlay manifest from a folder of media assets.
//
// Convention-over-configuration: the user drops a folder of B-roll
// videos and/or before/after image pairs, the pipeline figures out the
// roles and distributes them evenly along the cleaned video timeline.
//
// File-role detection:
//   *.mp4 / *.mov / *.webm / *.mkv     → B-roll video
//   before*.{jpg,png,...} paired with
//     after*.{jpg,png,...} of the same
//     suffix                            → before-after pair
//     (e.g. before1.jpg + after1.jpg,
//      before.jpg + after.jpg)
//   any other still image               → single-image B-roll
//
// Placement: avoid the first/last 2 seconds, distribute the remaining
// time into N equal slots, place one overlay centered inside each.

import fs from "node:fs";
import path from "node:path";

const VIDEO_EXT = /\.(mp4|mov|webm|mkv|m4v|avi)$/i;
const IMAGE_EXT = /\.(jpg|jpeg|png|webp|bmp)$/i;

function listMedia(dir) {
  const files = fs
    .readdirSync(dir)
    .filter((f) => !f.startsWith("."))
    .map((f) => ({
      name: f,
      full: path.join(dir, f),
      isVideo: VIDEO_EXT.test(f),
      isImage: IMAGE_EXT.test(f),
    }))
    .filter((f) => f.isVideo || f.isImage);
  // Stable ordering by filename so repeat runs produce identical manifests.
  files.sort((a, b) => a.name.localeCompare(b.name, "en", { numeric: true }));
  return files;
}

// Find before/after pairs by matching prefix patterns:
//   "before<suffix>.<ext>" pairs with "after<suffix>.<ext>"
// where suffix is anything (including empty). Case-insensitive.
function findBeforeAfterPairs(images) {
  const pairs = [];
  const used = new Set();
  for (const img of images) {
    if (used.has(img.name)) continue;
    const m = img.name.match(/^before(.*)\.([a-z]+)$/i);
    if (!m) continue;
    const suffix = m[1];
    const counterpart = images.find(
      (o) =>
        !used.has(o.name) &&
        new RegExp(`^after${suffix.replace(/[.*+?^${}()|[\\]\\\\]/g, "\\\\$&")}\\.[a-z]+$`, "i").test(o.name),
    );
    if (counterpart) {
      pairs.push({ before: img, after: counterpart });
      used.add(img.name);
      used.add(counterpart.name);
    }
  }
  return { pairs, used };
}

export function buildManifestFromDir(dir, cleanedDurationSec, opts = {}) {
  const {
    edgePaddingSec = 2.0,        // never overlay in the first/last N seconds
    overlayDurationSec = 4.0,    // each overlay shown for this long
    fadeSec = 0.3,
  } = opts;

  if (!fs.existsSync(dir) || !fs.statSync(dir).isDirectory()) {
    throw new Error(`overlay assets directory not found: ${dir}`);
  }
  const all = listMedia(dir);
  const videos = all.filter((f) => f.isVideo);
  const images = all.filter((f) => f.isImage);

  const { pairs, used } = findBeforeAfterPairs(images);
  const singleImages = images.filter((i) => !used.has(i.name));

  // Build the overlay list. Order: B-roll first (videos + singles), then
  // before/after pairs near the back (after the doctor's pitch lands).
  const items = [];
  for (const v of videos) items.push({ type: "broll", src: v.full });
  for (const i of singleImages) items.push({ type: "broll", src: i.full });
  for (const p of pairs) items.push({ type: "before-after", before: p.before.full, after: p.after.full });

  const count = items.length;
  if (count === 0) {
    return { overlays: [], source_dir: dir, note: "no media files found" };
  }

  // Position: divide the usable window into N equal slots, center each
  // overlay inside its slot. If the slot is shorter than the requested
  // overlay duration, shrink to fit.
  const usable = Math.max(1, cleanedDurationSec - edgePaddingSec * 2);
  const slotSize = usable / count;
  const dur = Math.min(overlayDurationSec, slotSize - 0.5);
  const effectiveDur = Math.max(2.0, dur);
  const fade = Math.min(fadeSec, effectiveDur * 0.2);

  const overlays = items.map((item, i) => ({
    ...item,
    at: Number((edgePaddingSec + slotSize * i + (slotSize - effectiveDur) / 2).toFixed(2)),
    duration: Number(effectiveDur.toFixed(2)),
    fadeIn: Number(fade.toFixed(2)),
    fadeOut: Number(fade.toFixed(2)),
  }));

  return {
    overlays,
    source_dir: dir,
    detected: {
      videos: videos.map((f) => f.name),
      pairs: pairs.map((p) => `${p.before.name} + ${p.after.name}`),
      single_images: singleImages.map((f) => f.name),
    },
    generated_at: new Date().toISOString(),
  };
}
