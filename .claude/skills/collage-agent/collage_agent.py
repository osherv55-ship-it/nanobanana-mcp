#!/usr/bin/env python3
"""Collage agent: pair before/after photos with GPT vision, compose collages.

Takes a folder of treatment photos, asks an OpenAI vision model (default
gpt-5.5) to match them into before/after pairs, then composes a vertical-split
collage per pair (the photo.jpg overlay format used by the doctor-video-editor
skill). Labels are drawn in Hebrew (לפני / אחרי) with proper RTL handling.

Usage:
    python collage_agent.py <photos_dir> [--out <dir>] [--model gpt-5.5]

Env: OPENAI_API_KEY required (falls back to ~/pal-mcp-server/.env).
Honors HTTPS_PROXY and SSL_CERT_FILE for managed egress environments.
"""

import argparse
import base64
import io
import json
import os
import sys
from pathlib import Path

import httpx
from PIL import Image, ImageDraw, ImageFont, features
from bidi.algorithm import get_display

# With libraqm Pillow shapes RTL text natively; manual bidi would double-reverse.
HAS_RAQM = features.check("raqm")

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp"}
FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
]
CANVAS_W, CANVAS_H = 1600, 1000  # wide overlay card, split into two halves
LABEL_BEFORE, LABEL_AFTER = "לפני", "אחרי"

PAIRING_PROMPT = """You are matching clinical treatment photos into before/after pairs.
You receive numbered photos. Decide which photos belong to the same patient/treatment
area, and within each pair which one is BEFORE (pre-treatment) and which is AFTER
(post-treatment, improved result). Use visual cues: same person/angle/area, skin
condition, filenames if hinted.

Reply with STRICT JSON only, no prose:
{"pairs": [{"before": <photo number>, "after": <photo number>, "caption": "<short Hebrew caption describing the treatment, e.g. מילוי שפתיים>"}], "unmatched": [<numbers>]}
"""


def load_api_key() -> str:
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        env_file = Path.home() / "pal-mcp-server" / ".env"
        if env_file.exists():
            for line in env_file.read_text().splitlines():
                if line.startswith("OPENAI_API_KEY="):
                    key = line.split("=", 1)[1].strip()
    if not key:
        sys.exit("OPENAI_API_KEY not set (env var or ~/pal-mcp-server/.env)")
    return key


def encode_for_vision(path: Path, max_side: int = 768) -> str:
    """Downscale + JPEG-encode a photo for the vision request."""
    img = Image.open(path).convert("RGB")
    img.thumbnail((max_side, max_side))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=80)
    return base64.b64encode(buf.getvalue()).decode()


def pair_photos(photos: list[Path], model: str, api_key: str) -> dict:
    content = [{"type": "text", "text": PAIRING_PROMPT}]
    for i, p in enumerate(photos, 1):
        content.append({"type": "text", "text": f"Photo {i} (filename: {p.name}):"})
        content.append(
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{encode_for_vision(p)}"},
            }
        )

    resp = httpx.post(
        "https://api.openai.com/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}"},
        json={
            "model": model,
            "messages": [{"role": "user", "content": content}],
            "max_completion_tokens": 4000,
            "response_format": {"type": "json_object"},
        },
        timeout=180,
    )
    if resp.status_code != 200:
        sys.exit(f"OpenAI API error {resp.status_code}: {resp.text[:500]}")
    body = resp.json()
    return json.loads(body["choices"][0]["message"]["content"])


def load_font(size: int) -> ImageFont.FreeTypeFont:
    for cand in FONT_CANDIDATES:
        if Path(cand).exists():
            return ImageFont.truetype(cand, size)
    return ImageFont.load_default()


def fit_cover(img: Image.Image, w: int, h: int) -> Image.Image:
    """Scale + center-crop to exactly (w, h)."""
    scale = max(w / img.width, h / img.height)
    img = img.resize((round(img.width * scale), round(img.height * scale)))
    left, top = (img.width - w) // 2, (img.height - h) // 2
    return img.crop((left, top, left + w, top + h))


def draw_label(draw: ImageDraw.ImageDraw, xy: tuple[int, int], text: str, font) -> None:
    """Draw a Hebrew label (RTL-corrected) with a dark pill behind it."""
    shaped = text if HAS_RAQM else get_display(text)
    bbox = draw.textbbox(xy, shaped, font=font, anchor="mm")
    pad = 18
    draw.rounded_rectangle(
        (bbox[0] - pad, bbox[1] - pad, bbox[2] + pad, bbox[3] + pad),
        radius=16,
        fill=(0, 0, 0, 190),
    )
    draw.text(xy, shaped, font=font, fill="white", anchor="mm")


def compose_collage(before: Path, after: Path, caption: str, out_path: Path) -> None:
    half_w = CANVAS_W // 2
    canvas = Image.new("RGBA", (CANVAS_W, CANVAS_H), "white")
    # Hebrew reading order: before on the RIGHT half, after on the LEFT half
    canvas.paste(fit_cover(Image.open(before).convert("RGB"), half_w, CANVAS_H), (half_w, 0))
    canvas.paste(fit_cover(Image.open(after).convert("RGB"), half_w, CANVAS_H), (0, 0))

    overlay = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    draw.rectangle((half_w - 3, 0, half_w + 3, CANVAS_H), fill="white")
    label_font, caption_font = load_font(64), load_font(44)
    # RTL: before on the right half, after on the left half
    draw_label(draw, (half_w + half_w // 2, 80), LABEL_BEFORE, label_font)
    draw_label(draw, (half_w // 2, 80), LABEL_AFTER, label_font)
    if caption:
        draw_label(draw, (CANVAS_W // 2, CANVAS_H - 70), caption, caption_font)

    Image.alpha_composite(canvas, overlay).convert("RGB").save(out_path, quality=92)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("photos_dir", type=Path)
    ap.add_argument("--out", type=Path, default=None)
    ap.add_argument("--model", default="gpt-5.5")
    args = ap.parse_args()

    photos = sorted(p for p in args.photos_dir.iterdir() if p.suffix.lower() in IMAGE_EXTS)
    if len(photos) < 2:
        sys.exit(f"Need at least 2 photos in {args.photos_dir}, found {len(photos)}")
    out_dir = args.out or args.photos_dir / "collages"
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"Pairing {len(photos)} photos with {args.model}...")
    result = pair_photos(photos, args.model, load_api_key())

    made = []
    for n, pair in enumerate(result.get("pairs", []), 1):
        before = photos[pair["before"] - 1]
        after = photos[pair["after"] - 1]
        name = "photo.jpg" if n == 1 else f"photo{n}.jpg"
        out_path = out_dir / name
        compose_collage(before, after, pair.get("caption", ""), out_path)
        made.append(out_path)
        print(f"  {name}: {before.name} (before) + {after.name} (after) — {pair.get('caption', '')}")

    unmatched = result.get("unmatched", [])
    if unmatched:
        print(f"  unmatched photos: {', '.join(photos[i - 1].name for i in unmatched)}")
    print(json.dumps({"collages": [str(p) for p in made]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
