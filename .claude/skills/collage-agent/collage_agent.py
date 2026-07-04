#!/usr/bin/env python3
"""Collage agent: pair before/after photos with GPT vision, compose collages.

Takes a folder of treatment photos, asks an OpenAI vision model (default
gpt-5.5) to match them into before/after pairs, then composes a collage per
pair in the clinic's design template.

Templates:
  stacked (default) — the clinic's original design: Before on top, After
      below, elegant serif English labels on white bands, tight crop on the
      treated area (GPT returns a crop box per photo, e.g. lips → nose-to-chin).
  wide — vertical-split photo.jpg overlay used by doctor-video-editor
      (before right / after left, Hebrew labels).

Usage:
    python collage_agent.py <photos_dir> [--out DIR] [--model gpt-5.5]
                            [--treatment שפתיים] [--template stacked|wide]

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
from PIL import Image, ImageDraw, ImageFont, ImageOps, features
from bidi.algorithm import get_display

try:  # iPhone HEIC photos
    from pillow_heif import register_heif_opener

    register_heif_opener()
except ImportError:
    pass

# With libraqm Pillow shapes RTL text natively; manual bidi would double-reverse.
HAS_RAQM = features.check("raqm")

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".heic", ".heif"}
SANS_FONTS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
]
SERIF_FONTS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
]

PAIRING_PROMPT = """You are matching clinical treatment photos into before/after pairs.
You receive numbered photos. Decide which photos belong to the same patient/treatment
area, and within each pair which one is BEFORE (pre-treatment) and which is AFTER
(post-treatment, improved result). Use visual cues: same person/angle/area, skin
condition, filenames if hinted.

For EACH photo in a pair also return, as fractions of image width/height
([x0, y0, x1, y1], 0,0 = top-left, be VERY precise):
- "nose": tight box around the nose only — x0/x1 exactly at the outer edges of
  the nostrils, y1 at the nose tip's base.
- "area": tight box around the treated feature itself (lips only for lip
  treatments, etc.).

Reply with STRICT JSON only, no prose:
{"pairs": [{"before": <n>, "after": <n>,
            "nose_before": [...], "nose_after": [...],
            "area_before": [...], "area_after": [...],
            "caption": "<short Hebrew treatment caption, e.g. מילוי שפתיים>"}],
 "unmatched": [<numbers>]}
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


def open_photo(path: Path) -> Image.Image:
    return ImageOps.exif_transpose(Image.open(path)).convert("RGB")


def encode_for_vision(path: Path, max_side: int = 768) -> str:
    """Downscale + JPEG-encode a photo for the vision request."""
    img = open_photo(path)
    img.thumbnail((max_side, max_side))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=80)
    return base64.b64encode(buf.getvalue()).decode()


def pair_photos(
    photos: list[Path],
    model: str,
    api_key: str,
    treatment: str | None = None,
    single_frontal: bool = False,
) -> dict:
    prompt = PAIRING_PROMPT
    if treatment:
        prompt += (
            f"\nThe clinic folder says the treatment is: {treatment}. "
            "Base the Hebrew captions on it unless the photos clearly show otherwise."
        )
    if single_frontal:
        prompt += (
            "\nIMPORTANT: Return EXACTLY ONE pair — the most frontal, straight-facing "
            "before photo and the most frontal after photo. Angled or profile shots must "
            "NOT be paired; list every other photo under unmatched."
        )
    content = [{"type": "text", "text": prompt}]
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


def valid_box(box) -> bool:
    return (
        isinstance(box, (list, tuple))
        and len(box) == 4
        and all(isinstance(v, (int, float)) for v in box)
        and 0 <= box[0] < box[2] <= 1
        and 0 <= box[1] < box[3] <= 1
    )


def fetch_boxes(path: Path, model: str, api_key: str) -> dict:
    """Fallback: ask for face + treated-area boxes of a single photo."""
    resp = httpx.post(
        "https://api.openai.com/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}"},
        json={
            "model": model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": (
                                "Locate in this clinical photo, as fractions of image "
                                "width/height ([x0, y0, x1, y1], 0,0 = top-left, VERY precise): "
                                '"nose" — tight box, x0/x1 exactly at the outer nostril edges; '
                                '"area" — tight box around the lips. '
                                'STRICT JSON only: {"nose": [...], "area": [...]}'
                            ),
                        },
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{encode_for_vision(path)}"},
                        },
                    ],
                }
            ],
            "max_completion_tokens": 1000,
            "response_format": {"type": "json_object"},
        },
        timeout=120,
    )
    if resp.status_code != 200:
        return {}
    try:
        return json.loads(resp.json()["choices"][0]["message"]["content"])
    except (KeyError, ValueError):
        return {}


def plausible(nose, area) -> bool:
    """Anatomical sanity: nose is narrower than the lips (roughly 0.35–1.0×)
    and sits above them, horizontally aligned."""
    if not (valid_box(nose) and valid_box(area)):
        return False
    nose_w, lips_w = nose[2] - nose[0], area[2] - area[0]
    nose_cx, lips_cx = (nose[0] + nose[2]) / 2, (area[0] + area[2]) / 2
    return (
        0.35 * lips_w <= nose_w <= 1.0 * lips_w
        and abs(nose_cx - lips_cx) <= lips_w * 0.5
        and nose[3] <= (area[1] + area[3]) / 2
    )


def ensure_boxes(pair: dict, before: Path, after: Path, model: str, api_key: str) -> None:
    """Guarantee valid, anatomically plausible boxes per side, re-asking if needed."""
    for side, path in (("before", before), ("after", after)):
        if not plausible(pair.get(f"nose_{side}"), pair.get(f"area_{side}")):
            boxes = fetch_boxes(path, model, api_key)
            if valid_box(boxes.get("nose")):
                pair[f"nose_{side}"] = boxes["nose"]
            if valid_box(boxes.get("area")):
                pair[f"area_{side}"] = boxes["area"]
        nose, area = pair.get(f"nose_{side}"), pair.get(f"area_{side}")
        if not plausible(nose, area):
            if valid_box(area):
                # Synthesize a nose box from the lips: ~0.65 lip-width, centered.
                lips_w = area[2] - area[0]
                cx = (area[0] + area[2]) / 2
                nose_w = 0.65 * lips_w
                pair[f"nose_{side}"] = [cx - nose_w / 2, max(0, area[1] - lips_w), cx + nose_w / 2, area[1]]
                print(f"  note: synthesized nose box for {path.name} (model box implausible)")
            else:
                print(f"  WARNING: no usable crop boxes for {path.name}; tile left uncropped")


def load_font(size: int, serif: bool = False) -> ImageFont.FreeTypeFont:
    for cand in SERIF_FONTS if serif else SANS_FONTS:
        if Path(cand).exists():
            return ImageFont.truetype(cand, size)
    return ImageFont.load_default()


def fit_cover(img: Image.Image, w: int, h: int) -> Image.Image:
    """Scale + center-crop to exactly (w, h)."""
    scale = max(w / img.width, h / img.height)
    img = img.resize((round(img.width * scale), round(img.height * scale)))
    left, top = (img.width - w) // 2, (img.height - h) // 2
    return img.crop((left, top, left + w, top + h))


def frame_lower_face(
    img: Image.Image,
    nose: list[float] | None,
    area: list[float] | None,
    aspect: float,
    ratio: float,
) -> Image.Image:
    """Crop the clinic's lip-template frame: nose-to-chin, lips centered.

    Zoom is anchored to the NOSE width — a small, precisely locatable feature
    that treatment doesn't change — so both tiles of a pair show the patient
    at an identical scale regardless of how each photo was shot.
    """
    if not (valid_box(nose) and valid_box(area)):
        return img
    nose_w = (nose[2] - nose[0]) * img.width
    lips_cx = (area[0] + area[2]) / 2 * img.width
    lips_cy = (area[1] + area[3]) / 2 * img.height

    # ratio is crop height in units of this photo's nose width; sharing the
    # ratio across a pair keeps both tiles at the same scale.
    crop_h = ratio * nose_w
    crop_w = crop_h * aspect

    # Lips pinned at the horizontal center, 45% down the crop.
    x0 = max(0, min(lips_cx - crop_w / 2, img.width - crop_w))
    y0 = max(0, min(lips_cy - 0.45 * crop_h, img.height - crop_h))
    return img.crop((round(x0), round(y0), round(x0 + crop_w), round(y0 + crop_h)))


# Base crop: width ≈ 4.1 nose-widths (cheek-to-cheek), height per the aspect.
BASE_RATIO = 4.1 / (1340 / 900)


def max_frame_ratio(img: Image.Image, nose, area, aspect: float) -> float:
    """Largest lips-anchored crop (in nose-width units) this photo can host.

    Caps the crop so lips can actually sit at 45% height — a photo already cut
    tight at the chin forces a smaller window instead of drifting up the face.
    """
    if not (valid_box(nose) and valid_box(area)):
        return BASE_RATIO
    nose_w = (nose[2] - nose[0]) * img.width
    lips_cy = (area[1] + area[3]) / 2 * img.height
    limits = [
        (img.height - lips_cy) / 0.55,  # room below the lips
        lips_cy / 0.45,  # room above the lips
        img.height,
        img.width / aspect,
    ]
    return min(min(limits) / nose_w, BASE_RATIO)


# --- stacked template (the clinic's original design) --------------------------
STACK_W = 1340  # canvas width
STACK_TILE_H = 900  # each photo tile
STACK_BAND_H = 130  # white label band above each tile


def compose_stacked(before: Path, after: Path, pair: dict, out_path: Path) -> None:
    """Before on top, After below; serif English labels on white bands."""
    total_h = 2 * (STACK_BAND_H + STACK_TILE_H)
    canvas = Image.new("RGB", (STACK_W, total_h), "white")
    draw = ImageDraw.Draw(canvas)
    font = load_font(76, serif=True)

    aspect = STACK_W / STACK_TILE_H
    img_b, img_a = open_photo(before), open_photo(after)
    ratio = min(
        max_frame_ratio(img_b, pair.get("nose_before"), pair.get("area_before"), aspect),
        max_frame_ratio(img_a, pair.get("nose_after"), pair.get("area_after"), aspect),
    )
    y = 0
    for label, img, nose, area in (
        ("Before", img_b, pair.get("nose_before"), pair.get("area_before")),
        ("After", img_a, pair.get("nose_after"), pair.get("area_after")),
    ):
        draw.text((STACK_W // 2, y + STACK_BAND_H // 2), label, font=font, fill="black", anchor="mm")
        y += STACK_BAND_H
        tile = fit_cover(frame_lower_face(img, nose, area, aspect, ratio), STACK_W, STACK_TILE_H)
        canvas.paste(tile, (0, y))
        y += STACK_TILE_H

    canvas.save(out_path, quality=92)


# --- wide template (doctor-video-editor photo.jpg overlay) --------------------
WIDE_W, WIDE_H = 1600, 1000
LABEL_BEFORE, LABEL_AFTER = "לפני", "אחרי"


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


def compose_wide(before: Path, after: Path, pair: dict, out_path: Path) -> None:
    half_w = WIDE_W // 2
    canvas = Image.new("RGBA", (WIDE_W, WIDE_H), "white")
    # Hebrew reading order: before on the RIGHT half, after on the LEFT half
    canvas.paste(fit_cover(open_photo(before), half_w, WIDE_H), (half_w, 0))
    canvas.paste(fit_cover(open_photo(after), half_w, WIDE_H), (0, 0))

    overlay = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    draw.rectangle((half_w - 3, 0, half_w + 3, WIDE_H), fill="white")
    label_font, caption_font = load_font(64), load_font(44)
    draw_label(draw, (half_w + half_w // 2, 80), LABEL_BEFORE, label_font)
    draw_label(draw, (half_w // 2, 80), LABEL_AFTER, label_font)
    caption = pair.get("caption", "")
    if caption:
        draw_label(draw, (WIDE_W // 2, WIDE_H - 70), caption, caption_font)

    Image.alpha_composite(canvas, overlay).convert("RGB").save(out_path, quality=92)


TEMPLATES = {"stacked": compose_stacked, "wide": compose_wide}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("photos_dir", type=Path)
    ap.add_argument("--out", type=Path, default=None)
    ap.add_argument("--model", default="gpt-5.5")
    ap.add_argument("--treatment", default=None, help="Treatment name hint for captions (e.g. שפתיים)")
    ap.add_argument("--template", choices=sorted(TEMPLATES), default="stacked")
    ap.add_argument(
        "--single-frontal",
        action="store_true",
        help="Produce exactly one collage from the frontal before/after pair (clinic rule for lips)",
    )
    args = ap.parse_args()

    photos = sorted(p for p in args.photos_dir.iterdir() if p.suffix.lower() in IMAGE_EXTS)
    if len(photos) < 2:
        sys.exit(f"Need at least 2 photos in {args.photos_dir}, found {len(photos)}")
    out_dir = args.out or args.photos_dir / "collages"
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"Pairing {len(photos)} photos with {args.model}...")
    result = pair_photos(photos, args.model, load_api_key(), args.treatment, args.single_frontal)
    if args.single_frontal and len(result.get("pairs", [])) > 1:
        result["pairs"] = result["pairs"][:1]

    compose = TEMPLATES[args.template]
    made = []
    for n, pair in enumerate(result.get("pairs", []), 1):
        before = photos[pair["before"] - 1]
        after = photos[pair["after"] - 1]
        name = "photo.jpg" if n == 1 else f"photo{n}.jpg"
        out_path = out_dir / name
        if args.template == "stacked":
            ensure_boxes(pair, before, after, args.model, load_api_key())
        compose(before, after, pair, out_path)
        made.append(out_path)
        print(f"  {name}: {before.name} (before) + {after.name} (after) — {pair.get('caption', '')}")

    unmatched = result.get("unmatched", [])
    if unmatched:
        print(f"  unmatched photos: {', '.join(photos[i - 1].name for i in unmatched)}")
    print(json.dumps({"collages": [str(p) for p in made]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
