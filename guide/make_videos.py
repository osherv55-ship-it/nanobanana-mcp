"""Renders the twelve routine scenes to vertical MP4s.

Reuses the exact scenes and timeline engine the guide plays inline, so a clip
and its diagram can never drift apart: the renderer just seeks the same
scene to successive frame times and screenshots it.
"""
import os, sys, subprocess, shutil, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gen_anim import SCENES, TITLES

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "video")
FRAMES = "/tmp/claude-0/-home-user-nanobanana-mcp/90335711-4b4e-5366-bbb5-4e261c51b9ba/scratchpad/frames"
FONTS = "/tmp/claude-0/-home-user-nanobanana-mcp/90335711-4b4e-5366-bbb5-4e261c51b9ba/scratchpad/fonts/fonts.css"
EXE = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
W, H, FPS = 1080, 1920, 24

TOKENS = """
:root{
  --ground:#F1EEF2; --surface:#FBFAFC; --surface-2:#E8E3EC;
  --ink:#221A26; --ink-soft:#5C5264; --ink-faint:#8A7F92;
  --rule:#DCD4E1; --rule-strong:#C6BBCE;
  --accent:#8E3B5B; --accent-ink:#6E2843; --accent-soft:#F5E4EB; --accent-line:#D9A9BE;
  --cognac:#9A6533; --cognac-soft:#F4E9DA;
  --z-red:#2E8C68; --z-pore:#4E79AC; --z-bronze:#A96A2C;
  --z-blush:#C4557C; --z-glow:#C89322; --z-conceal:#7A68BC; --z-powder:#7E8794;
  --skin:#F4E7DC; --skin-line:#5A4740; --skin-edge:#B99C89; --hair:#937052;
  --serif:'Frank Ruhl Libre',serif; --sans:'Assistant',sans-serif;
}"""

PAGE_CSS = """
*{box-sizing:border-box;margin:0}
body{width:1080px;height:1920px;overflow:hidden;background:var(--ground);
  font-family:var(--sans);direction:rtl;text-align:right;-webkit-font-smoothing:antialiased}
.slide{position:absolute;inset:0;display:none;flex-direction:column;padding:70px 64px 64px}
.slide.on{display:flex}
.top{display:flex;align-items:center;gap:26px;margin-bottom:14px}
.num{width:96px;height:96px;border-radius:50%;background:var(--surface);border:3px solid var(--accent-line);
  display:grid;place-items:center;font-size:38px;font-weight:700;color:var(--accent);flex:none;
  font-variant-numeric:tabular-nums}
.ttl{font-family:var(--serif);font-size:62px;font-weight:700;line-height:1.1;letter-spacing:-.02em;color:var(--ink)}
.when{font-size:27px;font-weight:600;color:var(--ink-faint);margin:6px 0 0 0}
.stage{flex:1;display:grid;place-items:center;padding:4px 0}
.stage svg{width:100%;height:100%;max-height:1180px}
.cap{font-family:var(--serif);font-size:52px;font-weight:700;color:var(--accent-ink);
  text-align:center;line-height:1.25;padding:0 20px;text-wrap:balance}
.note{font-size:30px;color:var(--ink-soft);text-align:center;line-height:1.45;margin-top:22px;
  padding:0 26px;text-wrap:balance}
.foot{display:flex;align-items:center;justify-content:space-between;margin-top:34px;
  padding-top:24px;border-top:2px solid var(--rule)}
.wordmark{font-family:var(--serif);font-size:32px;font-weight:700;color:var(--ink)}
.wordmark em{font-style:normal;color:var(--accent)}
.count{font-size:26px;font-weight:700;color:var(--ink-faint);font-variant-numeric:tabular-nums;direction:ltr}
.bar{position:absolute;left:0;right:0;bottom:0;height:10px;background:var(--surface-2)}
.bar i{display:block;height:100%;width:0;background:var(--accent)}
"""

NOTES = {
 0: "ניקוי, לחות, קרם עיניים קליל, מקדם הגנה — ואז לחכות. אם העור חלקלק, עוד מוקדם.",
 1: "רק אף, מצח ולחי פנימית. לחיצה עם קצה האצבע, לא מריחה מעגלית.",
 2: "רקות · מתחת לעצם הלחי · קו לסת · צדי האף. הקו עוצר בקו האישון.",
 3: "אצבע מעל קצה האף, אצבע החוצה. סומק נמוך מוריד את הפנים.",
 4: "מרכז המצח, סביב האף, הסנטר והלחיים הפנימיות. הנמשים חייבים להישאר גלויים.",
 5: "א׳ אודם בכנפי האף · ב׳ שליש פנימי של השקע · ג׳ כתמים. לא משולש גדול.",
 6: "אף · סנטר · נגיעה מתחת לפינה הפנימית. הלחיים נשארות בלי פודרה.",
 7: "לסרק כלפי מעלה, לקבע בג׳ל. עיפרון רק בדילול ובזנב — וגוון קריר.",
 8: "צללית מעל הקפל במקום שנשאר גלוי, עיפרון מרוח בשליש החיצוני בלבד.",
 9: "גג עצם הלחי · פינה פנימית · קשת קופידון · מתחת לקשת הגבה. סאטן בלבד.",
 10: "לחדד את קשת הקופידון ולהרים כל זווית בחצי מילימטר. ואז לטשטש פנימה.",
 11: "כף יד שטוחה על הלחי — לא קצות אצבעות. ללחוץ, לספור 5, ולהרים ישר למעלה. לא למרוח.",
}
WHEN = {0:"3 דקות",1:"20 שניות",2:"90 שניות",3:"40 שניות",4:"90 שניות",5:"60 שניות",
        6:"20 שניות",7:"40 שניות",8:"3 דקות",9:"20 שניות",10:"60 שניות",11:"20 שניות"}


def build_page():
    slides = []
    meta = []
    for i in range(12):
        svg, cap, dur = SCENES[i](f"v{i}")
        svg = svg.replace('class="fig anim"', 'class="fig anim"', 1)
        meta.append({"i": i, "dur": dur})
        slides.append(f'''<div class="slide" data-i="{i}">
  <div class="top"><div class="num">{i:02d}</div>
    <div><div class="ttl">{TITLES[i]}</div><div class="when">{WHEN[i]}</div></div></div>
  <div class="stage">{svg}</div>
  <div class="cap">{cap}</div>
  <div class="note">{NOTES[i]}</div>
  <div class="foot"><div class="wordmark">עור, <em>לא איפור</em></div>
    <div class="count">{i+1} / 12</div></div>
  <div class="bar"><i></i></div>
</div>''')
    anim = open(os.path.join(ROOT, "src", "anim.js"), encoding="utf-8").read()
    html = f'''<!doctype html><html lang="he" dir="rtl"><head><meta charset="utf-8">
<style>{open(FONTS,encoding="utf-8").read()}{TOKENS}{PAGE_CSS}</style></head><body>
{"".join(slides)}
<script>window.__videoMode=true;</script>
<script>{anim}</script>
<script>
window.__show=function(i){{
  document.querySelectorAll('.slide').forEach(function(s){{ s.classList.toggle('on', +s.dataset.i===i); }});
}};
window.__frame=function(i,t){{
  var s=document.querySelector('.slide[data-i="'+i+'"]');
  window.__seekFig(s.querySelector('svg.fig.anim'), t);
  s.querySelector('.bar i').style.width=(t*100).toFixed(2)+'%';
}};
window.__META={json.dumps(meta)};
</script></body></html>'''
    p = os.path.join(FRAMES, "stage.html")
    os.makedirs(FRAMES, exist_ok=True)
    open(p, "w", encoding="utf-8").write(html)
    return p, meta


def render(only=None):
    from playwright.sync_api import sync_playwright
    import imageio_ffmpeg
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    page_path, meta = build_page()
    os.makedirs(OUT, exist_ok=True)
    made = []
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path=EXE, args=["--no-sandbox", "--force-color-profile=srgb"])
        pg = b.new_page(viewport={"width": W, "height": H}, device_scale_factor=1, color_scheme="light")
        errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.goto("file://" + page_path, wait_until="networkidle")
        pg.wait_for_timeout(900)
        if errs:
            print("PAGE ERRORS:", errs[:3])
        for m in meta:
            i, dur = m["i"], m["dur"]
            if only is not None and i not in only:
                continue
            d = os.path.join(FRAMES, f"s{i:02d}")
            shutil.rmtree(d, ignore_errors=True)
            os.makedirs(d)
            pg.evaluate("i=>window.__show(i)", i)
            pg.wait_for_timeout(140)
            total = int(dur * FPS)
            hold = int(1.1 * FPS)          # let the finished frame breathe
            for f in range(total + hold):
                t = min(1.0, f / total)
                pg.evaluate("([i,t])=>window.__frame(i,t)", [i, t])
                pg.screenshot(path=os.path.join(d, f"f{f:04d}.png"))
            mp4 = os.path.join(OUT, f"step-{i:02d}.mp4")
            cmd = [ff, "-y", "-loglevel", "error", "-framerate", str(FPS),
                   "-i", os.path.join(d, "f%04d.png"),
                   "-c:v", "libx264", "-preset", "medium", "-crf", "20",
                   "-pix_fmt", "yuv420p", "-movflags", "+faststart", mp4]
            subprocess.run(cmd, check=True)
            shutil.rmtree(d, ignore_errors=True)
            sz = os.path.getsize(mp4) / 1024
            print(f"  ✓ step-{i:02d}.mp4  {total+hold} frames  {sz:.0f}KB  ({TITLES[i]})")
            made.append(mp4)
        b.close()
    return made


def concat(made):
    import imageio_ffmpeg
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    lst = os.path.join(FRAMES, "list.txt")
    with open(lst, "w") as f:
        for m in sorted(made):
            f.write(f"file '{m}'\n")
    full = os.path.join(OUT, "routine-full.mp4")
    subprocess.run([ff, "-y", "-loglevel", "error", "-f", "concat", "-safe", "0",
                    "-i", lst, "-c", "copy", "-movflags", "+faststart", full], check=True)
    print(f"  ✓ routine-full.mp4  {os.path.getsize(full)/1048576:.1f}MB")
    return full


if __name__ == "__main__":
    only = None
    if len(sys.argv) > 1:
        only = [int(x) for x in sys.argv[1].split(",")]
    made = render(only)
    if only is None and made:
        concat(made)
