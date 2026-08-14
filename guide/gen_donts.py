"""Paired wrong/right diagrams for the mistakes chapter.

Each pair zooms the same 420x520 face to the region the mistake happens in,
so the two panels differ only in the thing being taught.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from facelib import defs, base, clipped, FRECKLES

Z = dict(pore="var(--z-pore)", red="var(--z-red)", bronze="var(--z-bronze)",
         blush="var(--z-blush)", glow="var(--z-glow)", conceal="var(--z-conceal)",
         powder="var(--z-powder)", bad="var(--cognac)")


def mini(uid, vb, overlay, freckles=False, hair=True, label=""):
    return (f'<svg class="fig" viewBox="{vb}" role="img" aria-label="{label}">'
            f'{defs(uid)}{base(uid, hair=hair, freckles=freckles)}{overlay}</svg>')


# ---------- 1. undereye: whole triangle vs the inner third ----------
VB_EYE = "112 196 196 118"

def eye_bad(u):
    ov = clipped(u, f'<path d="M234,238 C258,238 276,244 288,250 L252,300 Z" fill="{Z["conceal"]}" fill-opacity=".55"/>'
                    f'<path d="M186,238 C162,238 144,244 132,250 L168,300 Z" fill="{Z["conceal"]}" fill-opacity=".55"/>')
    return mini(u, VB_EYE, ov, hair=False, label="משולש קונסילר גדול — שגוי")

def eye_good(u):
    ov = clipped(u, f'<path d="M231,240 C236,250 244,255 253,255 C244,262 233,258 228,248 Z" fill="{Z["conceal"]}" fill-opacity=".7"/>'
                    f'<path d="M189,240 C184,250 176,255 167,255 C176,262 187,258 192,248 Z" fill="{Z["conceal"]}" fill-opacity=".7"/>')
    ov += (f'<circle cx="233" cy="226" r="6" fill="{Z["glow"]}" fill-opacity=".9"/>'
           f'<circle cx="187" cy="226" r="6" fill="{Z["glow"]}" fill-opacity=".9"/>')
    return mini(u, VB_EYE, ov, hair=False, label="שליש פנימי בלבד ונקודת אור — נכון")


# ---------- 2. blush: low on the apple vs high toward the temple ----------
VB_CHEEK = "72 200 276 190"

def blush_bad(u):
    ov = clipped(u, f'<ellipse cx="262" cy="322" rx="34" ry="26" fill="{Z["blush"]}" fill-opacity=".5"/>'
                    f'<ellipse cx="158" cy="322" rx="34" ry="26" fill="{Z["blush"]}" fill-opacity=".5"/>')
    return mini(u, VB_CHEEK, ov, hair=False, label="סומק נמוך על התפוח — שגוי")

def blush_good(u):
    inner = "".join(f'<path d="{d}" fill="none" stroke="{Z["blush"]}" stroke-opacity=".5"'
                    f' stroke-width="30" stroke-linecap="round"/>'
                    for d in ["M252,282 C274,272 294,258 310,240", "M168,282 C146,272 126,258 110,240"])
    inner += f'<path d="M92,300 L328,300" stroke="{Z["blush"]}" stroke-width="2" stroke-opacity=".5" stroke-dasharray="6 5"/>'
    return mini(u, VB_CHEEK, clipped(u, inner), hair=False, label="סומק גבוה ומופנה לרקה — נכון")


# ---------- 3. highlight: glitter on the texture zones vs satin on the cheekbone ----------
VB_FACE = "46 30 328 460"

def glow_bad(u):
    ov = clipped(u, f'<ellipse cx="210" cy="150" rx="52" ry="24" fill="{Z["glow"]}" fill-opacity=".3"/>'
                    f'<path d="M204,258 C202,284 201,300 200,310 L220,310 C219,300 218,284 216,258 Z"'
                    f' fill="{Z["glow"]}" fill-opacity=".34"/>')
    spark = ("M0,-9 L2,-2 L9,0 L2,2 L0,9 L-2,2 L-9,0 L-2,-2 Z")
    ov += "".join(f'<g transform="translate({x},{y}) scale({sc})"><path d="{spark}" fill="#fff"'
                  f' stroke="{Z["glow"]}" stroke-width="1.4"/></g>'
                  for x, y, sc in [(192,144,1.0),(228,152,.85),(210,134,.7),(206,268,.8),
                                   (214,290,.95),(203,304,.7),(174,150,.65),(246,142,.65)])
    return mini(u, VB_FACE, ov, label="נצנצים על האף והמצח — שגוי")

def glow_good(u):
    ov = (f'<path d="M286,250 C298,240 308,232 316,222" stroke="{Z["glow"]}" stroke-opacity=".7"'
          f' stroke-width="10" stroke-linecap="round" fill="none"/>'
          f'<path d="M134,250 C122,240 112,232 104,222" stroke="{Z["glow"]}" stroke-opacity=".7"'
          f' stroke-width="10" stroke-linecap="round" fill="none"/>'
          f'<path d="M198,362 C203,356 207,362 210,364 C213,362 217,356 222,362" fill="none"'
          f' stroke="{Z["glow"]}" stroke-width="4.5" stroke-linecap="round"/>')
    return mini(u, VB_FACE, ov, label="סאטן גבוה על עצם הלחי בלבד — נכון")


# ---------- 4. application motion: circles vs press ----------
VB_NOSE = "132 232 156 116"

def motion_bad(u):
    ov = clipped(u, f'<g fill="{Z["bad"]}" fill-opacity=".3">'
                    '<path d="M204,258 C202,284 201,300 200,310 L220,310 C219,300 218,284 216,258 Z"/></g>')
    ov += (f'<g fill="none" stroke="{Z["bad"]}" stroke-width="3" stroke-linecap="round">'
           f'<circle cx="210" cy="286" r="22" stroke-dasharray="9 7"/>'
           f'<path d="M228,272 L233,284 L221,285 Z" fill="{Z["bad"]}" stroke="none"/></g>')
    return mini(u, VB_NOSE, ov, hair=False, label="מריחה מעגלית — שגוי")

def motion_good(u):
    ov = clipped(u, f'<g fill="{Z["pore"]}" fill-opacity=".3">'
                    '<path d="M204,258 C202,284 201,300 200,310 L220,310 C219,300 218,284 216,258 Z"/></g>')
    ov += f'<defs><marker id="am{u}" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse"><path d="M0,1 L9,5 L0,9 Z" fill="context-stroke"/></marker></defs>'
    for x, y in [(196,254),(224,254),(210,246),(196,292),(224,292)]:
        ov += (f'<path d="M{x},{y} L{x},{y+20}" fill="none" stroke="{Z["pore"]}" stroke-width="3"'
               f' stroke-linecap="round" marker-end="url(#am{u})"/>')
    return mini(u, VB_NOSE, ov, hair=False, label="לחיצות מלמעלה — נכון")


# ---------- 5. freckles: erased vs kept ----------
def freck_bad(u):
    ov = clipped(u, f'<ellipse cx="210" cy="260" rx="128" ry="176" fill="var(--skin)" fill-opacity=".97"/>')
    return mini(u, VB_FACE, ov, freckles=True, label="בסיס אטום שמוחק נמשים — שגוי")

def freck_good(u):
    inner = "".join(f'<path d="{d}" fill="none" stroke="{Z["blush"]}" stroke-opacity=".34"'
                    f' stroke-width="28" stroke-linecap="round"/>'
                    for d in ["M252,282 C274,272 294,258 310,240", "M168,282 C146,272 126,258 110,240"])
    return mini(u, VB_FACE, clipped(u, inner), freckles=True, label="סקין־טינט שקוף, נמשים גלויים — נכון")


PAIRS = {
 "undereye": (eye_bad, eye_good, "עוד ועוד קונסילר", "שליש פנימי + נקודת אור"),
 "blush":    (blush_bad, blush_good, "נמוך על התפוח", "גבוה, מופנה לרקה"),
 "glow":     (glow_bad, glow_good, "נצנץ על אף ומצח", "סאטן על עצם הלחי"),
 "motion":   (motion_bad, motion_good, "מריחה במעגלים", "לחיצות מלמעלה"),
 "freckles": (freck_bad, freck_good, "בסיס שמוחק הכל", "שקוף — הנמשים נשארים"),
}


def pair_html(key):
    bad, good, cap_bad, cap_good = PAIRS[key]
    return (f'<div class="vs">'
            f'<figure class="vs-cell bad">{bad(key+"b")}'
            f'<figcaption><span class="mk">✕</span>{cap_bad}</figcaption></figure>'
            f'<figure class="vs-cell good">{good(key+"g")}'
            f'<figcaption><span class="mk">✓</span>{cap_good}</figcaption></figure>'
            f'</div>')
