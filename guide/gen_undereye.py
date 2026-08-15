"""The advanced under-eye sequence — three panels on one zoomed eye.

Same 420x520 face as every other figure, just a tighter viewBox, so the
placement taught here sits exactly where the routine figures put it.
The three panels are cumulative: each one keeps the previous layer, faded.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from facelib import defs, base, clipped, arrow, stroke

VB = "216 176 118 106"

TROUGH = "M228,246 C244,262 262,266 278,262"        # the structural shadow itself
CORRECT = "M229,247 C240,256 249,261 255,262"       # deepest inner part only
CONCEAL = "M229,247 C242,257 254,262 262,262"       # a whisper, no wider
FOLD = "M240,267 C252,274 265,275 275,271"          # the strip that folds on a smile
NO_DRAG = "M270,259 C280,255 289,248 296,240"       # where it must not be pulled

Z = dict(trough="var(--z-trough)", peach="var(--z-peach)",
         conceal="var(--z-conceal)", powder="var(--z-powder)", bad="var(--cognac)")


def mini(uid, overlay, label):
    return (f'<svg class="fig" viewBox="{VB}" role="img" aria-label="{label}">'
            f'{defs(uid)}{base(uid, hair=False)}{overlay}</svg>')


def dashed(d, color, w, op, pattern):
    return stroke(d, color, w, op).replace(
        'stroke-linecap="round"', f'stroke-linecap="round" stroke-dasharray="{pattern}"')


def cross(x, y, color, r=4.5):
    return (f'<g stroke="{color}" stroke-width="2.4" stroke-linecap="round">'
            f'<path d="M{x-r},{y-r} L{x+r},{y+r}"/><path d="M{x+r},{y-r} L{x-r},{y+r}"/></g>')


def p1(u):
    ov = clipped(u, stroke(TROUGH, Z["trough"], 15, .34)
                  + stroke(CORRECT, Z["peach"], 8, .95))
    return mini(u, ov, "קורקטור אפרסק רק בעומק שקע הדמעה")


def p2(u):
    ov = clipped(u, stroke(TROUGH, Z["trough"], 15, .16)
                  + stroke(CORRECT, Z["peach"], 8, .45)
                  + stroke(CONCEAL, Z["conceal"], 12, .36))
    # blend direction: down and slightly out, never back and forth
    for x, y, dx in ((238, 266, 1), (250, 270, 2), (261, 269, 3)):
        ov += arrow(u, f"M{x},{y} L{x+dx},{y+10}", Z["conceal"], 1.9, .9)
    ov += dashed(NO_DRAG, Z["bad"], 2.2, .85, "5 5") + cross(298, 238, Z["bad"])
    return mini(u, ov, "שכבת קונסילר דקה מעל, מטושטשת כלפי מטה בלבד")


def p3(u):
    ov = clipped(u, stroke(TROUGH, Z["trough"], 15, .12)
                  + stroke(CONCEAL, Z["conceal"], 12, .22)
                  + dashed(FOLD, Z["powder"], 7, .95, "1.2 5.5"))
    return mini(u, ov, "פודרה רק על רצועת הקיפול")


PANELS = [
    (p1, "1", "קורקטור — רק בעומק הצל"),
    (p2, "2", "קונסילר — לחישה, וכלפי מטה"),
    (p3, "3", "קיבוע — רק קו הקיפול"),
]


def trio_html():
    cells = "".join(
        f'<figure class="vs-cell seq">{fn("ue"+n)}'
        f'<figcaption><span class="mk">{n}</span>{cap}</figcaption></figure>'
        for fn, n, cap in PANELS)
    return f'<div class="vs trio">{cells}</div>'


if __name__ == "__main__":
    print(trio_html())
