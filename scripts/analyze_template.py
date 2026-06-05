#!/usr/bin/env python3
"""
analyze_template.py — מחלץ "מתכון" (spec) מסרטון תבנית CapCut.

מנתח וידאו לדוגמה ומפיק template_spec.json עם:
  - תזמוני החיתוכים (זיהוי מעברי סצנה) → כמה סצנות וכמה שניות כל אחת
  - אורך כולל, רזולוציה, fps, אוריינטציה

לא קורא את "הענן" של CapCut (אין API) — מהנדס לאחור את הקצב/מבנה מתוך הווידאו.

שימוש:
    reelenv\\Scripts\\python.exe scripts\\analyze_template.py --input "C:\\path\\template.mov" --output "C:\\Users\\osher\\AAA\\template_spec.json"

ואז מחילים על הקליפים שלך:
    reelenv\\Scripts\\python.exe scripts\\make_reel.py --input "...\\ambiance" --output "...\\reel.mp4" --spec "C:\\Users\\osher\\AAA\\template_spec.json"
"""
import argparse
import json
import re
import subprocess

import imageio_ffmpeg
from moviepy.editor import VideoFileClip


def detect_cuts(path, threshold=0.30):
    """מחזיר רשימת חותמות-זמן של מעברי סצנה (חיתוכים) באמצעות ffmpeg scene detection."""
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    cmd = [ff, "-i", path, "-filter:v",
           f"select='gt(scene,{threshold})',showinfo", "-an", "-f", "null", "-"]
    p = subprocess.run(cmd, stderr=subprocess.PIPE, stdout=subprocess.DEVNULL,
                       text=True, encoding="utf-8", errors="ignore")
    times = [float(m) for m in re.findall(r"pts_time:([0-9.]+)", p.stderr)]
    return sorted(set(times))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, help="נתיב לסרטון התבנית (mp4/mov)")
    ap.add_argument("--output", default="template_spec.json")
    ap.add_argument("--threshold", type=float, default=0.30,
                    help="רגישות זיהוי חיתוכים (0.2 רגיש יותר, 0.4 פחות)")
    args = ap.parse_args()

    clip = VideoFileClip(args.input)
    dur = float(clip.duration)
    w, h = clip.size
    fps = float(clip.fps or 30)

    cuts = detect_cuts(args.input, args.threshold)
    bounds = [0.0] + cuts + [dur]
    segs = []
    for a, b in zip(bounds[:-1], bounds[1:]):
        d = round(b - a, 3)
        if d >= 0.3:                 # מתעלמים מסצנות זעירות (רעש)
            segs.append(d)

    spec = {
        "source": args.input,
        "duration": round(dur, 3),
        "width": w, "height": h, "fps": round(fps, 3),
        "orientation": "vertical" if h >= w else "horizontal",
        "num_segments": len(segs),
        "segment_durations": segs,
        "cut_times": [round(c, 3) for c in cuts],
        "avg_segment": round(sum(segs) / len(segs), 3) if segs else None,
    }
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(spec, f, ensure_ascii=False, indent=2)

    print("✅ spec:", args.output)
    print(f"   {len(segs)} סצנות | אורך {spec['duration']}ש' | "
          f"ממוצע {spec['avg_segment']}ש' לסצנה | {w}x{h} ({spec['orientation']})")
    print("   משכי סצנות:", segs)


if __name__ == "__main__":
    main()
