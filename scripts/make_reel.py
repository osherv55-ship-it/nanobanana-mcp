#!/usr/bin/env python3
"""
make_reel.py — בונה ריל אנכי luxury (1080x1920) מתיקיית קליפים, מקומית, בלי CapCut.

סטייל Academy של AAA: כסוף (#C8CDD2) על שחור, פתיח/סגירה, מעברי Dissolve, זום איטי,
כיתוב עברי (RTL) — הכל נצרב ל-MP4 אחד מוכן לפרסום.

דרישות (פעם אחת):
    pip install "moviepy==1.0.3" pillow python-bidi
    (ffmpeg כבר מותקן אצלך)

שימוש:
    python make_reel.py --input "C:\\Users\\osher\\AAA\\ambiance" --output "C:\\Users\\osher\\AAA\\AAA_Academy_reel.mp4"

לכל הדרכה הבאה — רק מחליפים --input ו---caption.
"""

import argparse
import json
import os
import sys
import glob

import PIL.Image
# תאימות: moviepy 1.0.3 משתמש ב-Image.ANTIALIAS שהוסר ב-Pillow 10+
if not hasattr(PIL.Image, "ANTIALIAS"):
    PIL.Image.ANTIALIAS = PIL.Image.LANCZOS

from PIL import Image, ImageDraw, ImageFont
try:
    from bidi.algorithm import get_display
except Exception:
    get_display = lambda s: s  # אם אין python-bidi, ניפול חזרה (עברית עלולה להופיע הפוך)

from moviepy.editor import (
    VideoFileClip, ImageClip, CompositeVideoClip, concatenate_videoclips,
)

W, H = 1080, 1920
SILVER = (200, 205, 210)
BLACK = (10, 10, 10)
CLIP_DUR = 2.6        # משך כל קליפ בשניות
XFADE = 0.5           # משך מעבר Dissolve
CARD_DUR = 2.5        # משך כרטיס פתיח/סגירה
ZOOM = 0.03           # זום איטי 1.00 -> 1.03

# מועמדי פונטים. עברית: עדיף פונט יוקרתי שהורד (Frank Ruhl Libre / Heebo / Assistant);
# נופלים חזרה ל-David/Arial אם לא נמצא. אפשר גם לכפות עם --font / --title-font.
HEBREW_FONT_CANDIDATES = [
    r".\fonts\FrankRuhlLibre-Medium.ttf",
    r".\fonts\Heebo-Medium.ttf",
    r".\fonts\Assistant-SemiBold.ttf",
    r".\fonts\Rubik-Medium.ttf",
    r"C:\Windows\Fonts\FrankRuhlLibre-Medium.ttf",
    r"C:\Windows\Fonts\Heebo-Medium.ttf",
    r"C:\Windows\Fonts\Rubik-Medium.ttf",
    r"C:\Windows\Fonts\davidbd.ttf",
    r"C:\Windows\Fonts\arialbd.ttf",
]
TITLE_FONT_CANDIDATES = [
    r".\fonts\PlayfairDisplay-SemiBold.ttf",
    r".\fonts\Cormorant-SemiBold.ttf",
    r"C:\Windows\Fonts\georgia.ttf",
    r"C:\Windows\Fonts\times.ttf",
    r"C:\Windows\Fonts\arialbd.ttf",
]
FONT_HEB = r"C:\Windows\Fonts\arialbd.ttf"   # נקבע ב-main לפי resolve_font
FONT_TITLE = r"C:\Windows\Fonts\arialbd.ttf"


def resolve_font(explicit, candidates):
    if explicit and os.path.exists(explicit):
        return explicit
    for c in candidates:
        if os.path.exists(c):
            return c
    return candidates[-1]


def _font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()


def _draw_centered(draw, text, font, y, color, rtl=False):
    if rtl:
        text = get_display(text)
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    draw.text(((W - tw) / 2, y), text, font=font, fill=color)


def make_card(main, sub=None, path="_card.png"):
    """כרטיס מסך-מלא: רקע שחור + טקסט כסוף ממורכז."""
    img = Image.new("RGB", (W, H), BLACK)
    d = ImageDraw.Draw(img)
    rtl_main = any("֐" <= ch <= "׿" for ch in main)
    _draw_centered(d, main, _font(FONT_TITLE, 96), H // 2 - 90, SILVER, rtl=rtl_main)
    if sub:
        _draw_centered(d, sub, _font(FONT_TITLE, 40), H // 2 + 40, SILVER)
    img.save(path)
    return path


def make_caption(text, path="_caption.png"):
    """רצועת כיתוב שקופה עם טקסט עברי כסוף בתחתית (פונט יוקרתי)."""
    img = Image.new("RGBA", (W, 260), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, 260], fill=(0, 0, 0, 120))  # פס שחור חצי-שקוף לקריאות
    font = _font(FONT_HEB, 50)
    disp = get_display(text)
    bbox = d.textbbox((0, 0), disp, font=font)
    tw = bbox[2] - bbox[0]
    d.text(((W - tw) / 2, 95), disp, font=font, fill=SILVER)
    img.save(path)
    return path


def animate_overlay(clip, anim, y=1480):
    """אנימציית כניסה לכיתוב: fade / rise / zoom."""
    if anim == "rise":
        return (clip.set_position(lambda t: ("center", int(y + 45 * max(0, 1 - t / 0.5))))
                    .crossfadein(0.4).crossfadeout(0.4))
    if anim == "zoom":
        return (clip.resize(lambda t: 1.0 + 0.07 * max(0, 1 - t / 0.5))
                    .set_position(("center", y)).crossfadein(0.4).crossfadeout(0.4))
    return clip.set_position(("center", y)).crossfadein(0.5).crossfadeout(0.5)  # fade


def load_clip(path):
    """טוען קליפ ומתקן מימדים לפי הפריים האמיתי (פותר סיבוב/מתיחה של קבצי iPhone)."""
    clip = VideoFileClip(path)
    try:
        clip.rotation = 0  # למנוע סיבוב כפול ע"י moviepy (ffmpeg כבר מסובב)
    except Exception:
        pass
    fh, fw = clip.get_frame(0).shape[:2]   # גובה, רוחב אמיתיים של הפריים
    if (round(clip.w), round(clip.h)) != (fw, fh):
        clip = clip.resize((fw, fh))       # מצמיד את ה-size לפריים האמיתי
    return clip.without_audio()


def cover_resize(clip):
    """ממלא 1080x1920 (cover) + חיתוך מרכז."""
    scale = max(W / clip.w, H / clip.h)
    clip = clip.resize(scale)
    return clip.crop(x_center=clip.w / 2, y_center=clip.h / 2, width=W, height=H)


def slow_zoom(clip):
    """זום איטי חסין: מגדילים עם הזמן וקובעים על קנבס 1080x1920 (הקנבס חותך את העודף)."""
    dur = max(clip.duration, 0.01)
    zoomed = clip.resize(lambda t: 1.0 + ZOOM * (t / dur)).set_position("center")
    return CompositeVideoClip([zoomed], size=(W, H)).set_duration(clip.duration)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, help="תיקיית הקליפים (אנגלית בלבד בנתיב)")
    ap.add_argument("--output", required=True, help="נתיב קובץ ה-MP4 הסופי")
    ap.add_argument("--title", default="AAA ACADEMY")
    ap.add_argument("--subtitle", default="ADVANCED FACIAL SCULPTING")
    ap.add_argument("--caption", default="התארחנו אצל רשת רונית רפאל להדרכה מתקדמת — פיסול פנים בטכניקות מתקדמות")
    ap.add_argument("--order", default="", help="סדר קבצים מופרד בפסיקים (ללא סיומת). ריק=לפי שם.")
    ap.add_argument("--zoom", action="store_true", help="הפעלת זום איטי (כבוי כברירת מחדל, לריצה היציבה ביותר)")
    ap.add_argument("--spec", default="", help="נתיב ל-template_spec.json (מ-analyze_template.py) — מחיל את קצב/מבנה התבנית")
    ap.add_argument("--font", default="", help="נתיב לפונט עברי לכיתוב (.ttf) — למשל fonts\\FrankRuhlLibre-Medium.ttf")
    ap.add_argument("--title-font", default="", help="נתיב לפונט הכותרת (.ttf)")
    ap.add_argument("--caption-anim", default="rise", choices=["fade", "rise", "zoom"], help="אנימציית כניסת הכיתוב")
    args = ap.parse_args()

    global FONT_HEB, FONT_TITLE
    FONT_HEB = resolve_font(args.font, HEBREW_FONT_CANDIDATES)
    FONT_TITLE = resolve_font(args.title_font, TITLE_FONT_CANDIDATES)
    print("פונט כיתוב:", FONT_HEB)
    print("פונט כותרת:", FONT_TITLE)

    files = sorted(glob.glob(os.path.join(args.input, "*.MOV")) +
                   glob.glob(os.path.join(args.input, "*.mov")) +
                   glob.glob(os.path.join(args.input, "*.mp4")))
    if args.order:
        wanted = [w.strip().lower() for w in args.order.split(",")]
        bn = {os.path.splitext(os.path.basename(f))[0].lower(): f for f in files}
        files = [bn[w] for w in wanted if w in bn]
    if not files:
        sys.exit(f"לא נמצאו קליפים ב-{args.input}")
    print(f"נמצאו {len(files)} קליפים")

    # רצף הסצנות: לפי spec של תבנית (משכים + מספר סצנות), אחרת קליפ אחד לכל קובץ ב-CLIP_DUR
    if args.spec:
        spec = json.load(open(args.spec, encoding="utf-8"))
        durs = spec.get("segment_durations") or []
        seq = [(files[i % len(files)], durs[i]) for i in range(len(durs))]
        print(f"מחיל תבנית: {len(durs)} סצנות לפי {os.path.basename(args.spec)}")
    else:
        seq = [(f, CLIP_DUR) for f in files]

    # גוף הריל: כל סצנה -> cover -> משך -> (זום) -> crossfade
    body = []
    for i, (f, dur) in enumerate(seq):
        c = load_clip(f)
        c = cover_resize(c).subclip(0, min(dur, c.duration))
        if args.zoom:
            c = slow_zoom(c)
        if i > 0:
            c = c.crossfadein(XFADE)
        body.append(c)
    body_clip = concatenate_videoclips(body, method="compose", padding=-XFADE)
    first_dur = seq[0][1] if seq else CLIP_DUR

    # כיתוב כסוף מעל הגוף (מופיע אחרי הקליפ הראשון, ~4ש')
    cap = ImageClip(make_caption(args.caption)).set_duration(4).set_start(first_dur)
    cap = animate_overlay(cap, args.caption_anim, y=1480)
    body_clip = CompositeVideoClip([body_clip, cap], size=(W, H))

    # כרטיסי פתיח/סגירה
    intro = ImageClip(make_card(args.title, args.subtitle, "_intro.png")).set_duration(CARD_DUR)
    outro = ImageClip(make_card(args.title, None, "_outro.png")).set_duration(CARD_DUR)
    outro = outro.crossfadein(XFADE)
    body_clip = body_clip.crossfadein(XFADE)

    final = concatenate_videoclips([intro, body_clip, outro],
                                   method="compose", padding=-XFADE)
    final = final.resize((W, H))

    print(f"מרנדר ל-{args.output} ...")
    final.write_videofile(args.output, fps=30, codec="libx264",
                          audio=False, preset="medium", bitrate="8000k")
    print("✅ סיום:", args.output)


if __name__ == "__main__":
    main()
