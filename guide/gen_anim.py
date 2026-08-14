"""Animated versions of the twelve routine figures.

Each scene is a normalised timeline: the JS engine seeks it to any t in [0,1],
which makes it identical whether it is played live in the guide or captured
frame-by-frame for video. At t=1 a scene matches the static diagram exactly.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from facelib import (defs, base, clipped, A, stroke, VB, hand,
                     PORE, BRONZE_STROKES, BLUSH_STROKES)

Z = dict(pore="var(--z-pore)", red="var(--z-red)", bronze="var(--z-bronze)",
         blush="var(--z-blush)", glow="var(--z-glow)", conceal="var(--z-conceal)",
         powder="var(--z-powder)", no="var(--cognac)")


def seq(n, t0, t1, hold=0.0):
    """n evenly spaced (start, end) windows between t0 and t1."""
    span = (t1 - t0) / n
    return [(round(t0 + i * span, 3), round(t0 + (i + 1) * span + hold, 3)) for i in range(n)]


def arrow_a(uid, d, color, w, t0, t1, op=.95):
    el = (f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{w}" stroke-opacity="{op}"'
          f' stroke-linecap="round" marker-end="url(#ar{uid})"/>')
    return A(el, "sweep", t0, t1)


def scene(uid, overlay, hair=True, freckles=False, label="", applicator=True):
    app = (f'<circle class="applicator" r="11" fill="var(--surface)" stroke="var(--ink)"'
           f' stroke-width="2.2" opacity="0"/>'
           f'<circle class="applicator-dot" r="3.4" fill="var(--ink)" opacity="0"/>') if applicator else ""
    return (f'<svg class="fig anim" viewBox="{VB}" role="img" aria-label="{label}">'
            f'{defs(uid)}{base(uid, hair=hair, freckles=freckles)}{overlay}{app}</svg>')


# ------------------------------------------------------------------ 00 prep
def s00(u):
    ov = clipped(u, A(f'<ellipse cx="210" cy="250" rx="150" ry="200" fill="{Z["pore"]}"'
                      f' fill-opacity=".13"/>', "fade", .45, .8))
    drops = [(128,140),(300,150),(112,250),(322,258),(150,392),(276,398)]
    for (x, y), (a, b) in zip(drops, seq(len(drops), .05, .5, .12)):
        ov += A(f'<g transform="translate({x},{y})"><path d="M0,-7 C4,-2 6,1 6,3 A6,6 0 0 1 -6,3'
                f' C-6,1 -4,-2 0,-7 Z" fill="{Z["pore"]}" fill-opacity=".55"/></g>',
                "drop", a, b, dy=26)
    ov += ('<g transform="translate(345,432)">'
           '<circle r="30" fill="var(--surface)" stroke="var(--ink)" stroke-width="2" stroke-opacity=".5"/>'
           + A('<path d="M0,-17 A17,17 0 1 1 -14,9" fill="none" stroke="var(--accent)"'
               ' stroke-width="4.5" stroke-linecap="round"/>', "draw", .5, .95) +
           '<text y="6" text-anchor="middle" font-family="Assistant,sans-serif" font-size="17"'
           ' font-weight="700" fill="var(--ink)">90</text></g>')
    return scene(u, ov, freckles=True, label="הכנה", applicator=False), "לחות ← ואז 90 שניות המתנה", 6


# ------------------------------------------------------------- 01 pore blur
def s01(u):
    parts = [f'<ellipse cx="210" cy="152" rx="52" ry="23" fill="{Z["pore"]}" fill-opacity=".34"/>',
             f'<path d="M204,258 C202,284 201,300 200,310 L220,310 C219,300 218,284 216,258 Z"'
             f' fill="{Z["pore"]}" fill-opacity=".34"/>',
             f'<ellipse cx="250" cy="296" rx="21" ry="17" fill="{Z["pore"]}" fill-opacity=".28"/>',
             f'<ellipse cx="170" cy="296" rx="21" ry="17" fill="{Z["pore"]}" fill-opacity=".28"/>']
    inner = "".join(A(p, "fade", a, b) for p, (a, b) in zip(parts, seq(len(parts), .05, .55, .1)))
    ov = clipped(u, inner)
    presses = [(210,120),(186,270),(234,270),(170,286),(250,286)]
    for (x, y), (a, b) in zip(presses, seq(len(presses), .12, .78, .08)):
        ov += arrow_a(u, f"M{x},{y} L{x},{y+26}", Z["pore"], 2.6, a, b)
    return scene(u, ov, label="פריימר על אזורי הנקבוביות"), "ללחוץ ↓ · לא למרוח", 7


# ------------------------------------------------------------- 02 underpaint
def s02(u):
    order = [0, 1, 2, 3, 4, 5]
    inner = ""
    for i, (a, b) in zip(order, seq(6, .05, .78)):
        inner += A(stroke(BRONZE_STROKES[i], Z["bronze"], 21, .5), "draw", a, b)
    for d, (a, b) in zip(["M225,236 C228,266 229,290 230,306", "M195,236 C192,266 191,290 190,306"],
                         seq(2, .6, .85)):
        inner += A(stroke(d, Z["bronze"], 7, .3), "draw", a, b)
    ov = clipped(u, inner)
    ov += arrow_a(u, "M262,300 C286,288 306,272 320,254", Z["bronze"], 3, .82, .97)
    ov += arrow_a(u, "M158,300 C134,288 114,272 100,254", Z["bronze"], 3, .82, .97)
    return scene(u, ov, label="ברונזר קרמי — Underpainting"), "תמיד כלפי מעלה וחוץ", 9


# ------------------------------------------------------------------ 03 blush
def s03(u):
    inner = ""
    for d, (a, b) in zip(BLUSH_STROKES, seq(2, .08, .62)):
        inner += A(stroke(d, Z["blush"], 30, .46), "draw", a, b)
    inner += A(f'<path d="M92,300 L328,300" stroke="{Z["no"]}" stroke-width="2.6"'
               f' stroke-opacity=".85" stroke-dasharray="7 6" fill="none"/>', "fade", .66, .8)
    ov = clipped(u, inner)
    ov += arrow_a(u, "M246,290 C270,278 292,262 308,244", Z["blush"], 3, .55, .72)
    ov += arrow_a(u, "M174,290 C150,278 128,262 112,244", Z["blush"], 3, .55, .72)
    ov += A(f'<g transform="translate(344,318)"><circle r="17" fill="var(--cognac-soft)"'
            f' stroke="{Z["no"]}" stroke-width="2"/><path d="M-7,-7 L7,7 M7,-7 L-7,7"'
            f' stroke="{Z["no"]}" stroke-width="3" stroke-linecap="round"/></g>',
            "pop", .8, .95, cx=344, cy=318)
    return scene(u, ov, label="סומק גבוה, מופנה לרקה"), "שום סומק מתחת לקו הזה", 8


# -------------------------------------------------------------- 04 skin tint
def s04(u):
    zones = [f'<ellipse cx="210" cy="300" rx="62" ry="46" fill="{Z["pore"]}" fill-opacity=".2"/>',
             f'<ellipse cx="210" cy="150" rx="46" ry="26" fill="{Z["pore"]}" fill-opacity=".2"/>',
             f'<ellipse cx="210" cy="398" rx="34" ry="22" fill="{Z["pore"]}" fill-opacity=".2"/>']
    inner = "".join(A(z, "fade", a, b) for z, (a, b) in zip(zones, seq(3, .05, .5, .12)))
    ov = clipped(u, inner)
    ds = ["M210,300 L268,286", "M210,300 L152,286", "M210,150 L272,138", "M210,150 L148,138"]
    for d, (a, b) in zip(ds, seq(4, .5, .92, .06)):
        ov += arrow_a(u, d, Z["pore"], 2.6, a, b)
    return scene(u, ov, freckles=True, label="סקין־טינט מהמרכז החוצה"), "מהמרכז החוצה · ~40%", 8


# -------------------------------------------------------------- 05 concealer
def s05(u):
    marks = [
        (f'<ellipse cx="187" cy="318" rx="9" ry="7" fill="{Z["red"]}" fill-opacity=".62"/>'
         f'<ellipse cx="233" cy="318" rx="9" ry="7" fill="{Z["red"]}" fill-opacity=".62"/>', 210, 318, "א"),
        (f'<path d="M231,240 C236,250 244,255 253,255 C244,262 233,258 228,248 Z" fill="{Z["conceal"]}" fill-opacity=".62"/>'
         f'<path d="M189,240 C184,250 176,255 167,255 C176,262 187,258 192,248 Z" fill="{Z["conceal"]}" fill-opacity=".62"/>',
         246, 250, "ב"),
        (f'<circle cx="272" cy="272" r="7" fill="{Z["red"]}" fill-opacity=".62"/>', 288, 262, "ג"),
    ]
    inner, badges = "", ""
    for (svg, bx, by, n), (a, b) in zip(marks, seq(3, .05, .66, .1)):
        inner += A(f'<g>{svg}</g>', "fade", a, b)
        badges += A(f'<g><circle cx="{bx}" cy="{by}" r="13" fill="var(--surface)" stroke="var(--ink)"'
                    f' stroke-width="1.6" stroke-opacity=".45"/>'
                    f'<text x="{bx}" y="{by+6}" text-anchor="middle" font-family="Assistant,sans-serif"'
                    f' font-size="16" font-weight="700" fill="var(--ink)">{n}</text></g>',
                    "pop", round(b - .04, 3), round(b + .12, 3), cx=bx, cy=by)
    return scene(u, clipped(u, inner) + badges, label="קונסילר בשלוש נקודות",
                 applicator=False), "שלוש נקודות · לא משולש", 8


# ----------------------------------------------------------------- 06 powder
def s06(u):
    zones = [f'<path d="M206,286 C205,298 204,306 203,312 L217,312 C216,306 215,298 214,286 Z"'
             f' fill="{Z["powder"]}" fill-opacity=".55"/>',
             f'<ellipse cx="210" cy="403" rx="14" ry="8" fill="{Z["powder"]}" fill-opacity=".55"/>',
             f'<g><path d="M233,243 C238,250 245,254 252,254 C245,259 235,256 231,249 Z"'
             f' fill="{Z["powder"]}" fill-opacity=".5"/>'
             f'<path d="M187,243 C182,250 175,254 168,254 C175,259 185,256 189,249 Z"'
             f' fill="{Z["powder"]}" fill-opacity=".5"/></g>']
    inner = "".join(A(z, "fade", a, b) for z, (a, b) in zip(zones, seq(3, .08, .72, .14)))
    ov = clipped(u, inner)
    for (x, y), (a, b) in zip([(210,262),(210,378),(210,222)], seq(3, .08, .72, .14)):
        ov += arrow_a(u, f"M{x},{y-24} L{x},{y}", Z["powder"], 2.4, a, b)
    return scene(u, ov, label="פודרה בשלושה אזורים", applicator=False), "שלושה אזורים · זהו", 7


# ------------------------------------------------------------------ 07 brows
def s07(u):
    ov = ""
    xs = (280, 257, 234, 186, 163, 140)
    for x, (a, b) in zip(xs, seq(6, .05, .62, .07)):
        ov += arrow_a(u, f"M{x},214 L{x},190", Z["bronze"], 2.4, a, b)
    ov += A(f'<circle cx="152" cy="197" r="11" fill="none" stroke="{Z["bronze"]}"'
            f' stroke-width="2.4" stroke-dasharray="4 3"/>', "pop", .66, .82, cx=152, cy=197)
    ov += A(f'<circle cx="292" cy="194" r="11" fill="none" stroke="{Z["bronze"]}"'
            f' stroke-width="2.4" stroke-dasharray="4 3"/>', "pop", .72, .88, cx=292, cy=194)
    ov += arrow_a(u, "M296,194 L318,186", Z["bronze"], 2.6, .86, .98)
    return scene(u, ov, label="גבות — סירוק כלפי מעלה", applicator=False), "לסרק ↑ · למלא רק בעיגולים", 8


# ------------------------------------------------------------------- 08 eyes
def s08(u):
    return (f'''<svg class="fig anim" viewBox="60 150 300 160" role="img" aria-label="מיפוי עפעף">
<defs><marker id="ar{u}" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="5.5" markerHeight="5.5"
 orient="auto-start-reverse"><path d="M0,1 L9,5 L0,9 Z" fill="context-stroke"/></marker></defs>
<rect x="60" y="150" width="300" height="160" fill="var(--skin)"/>
<path d="M228,201 C244,187 274,183 296,193 C291,199 282,197 269,198 C253,200 238,204 228,206 Z"
      fill="var(--skin-line)" fill-opacity=".72"/>
<path d="M192,201 C176,187 146,183 124,193 C129,199 138,197 151,198 C167,200 182,204 192,206 Z"
      fill="var(--skin-line)" fill-opacity=".72"/>
<path d="M236,222 C250,214 268,213 280,219" fill="none" stroke="var(--skin-line)" stroke-width="1.3"
      stroke-opacity=".45" stroke-dasharray="4 4"/>
<path d="M184,222 C170,214 152,213 140,219" fill="none" stroke="var(--skin-line)" stroke-width="1.3"
      stroke-opacity=".45" stroke-dasharray="4 4"/>
{A(stroke("M232,214 C248,204 272,203 288,210", Z["bronze"], 9, .5), "draw", .06, .42)}
{A(stroke("M188,214 C172,204 148,203 132,210", Z["bronze"], 9, .5), "draw", .06, .42)}
<g fill="none" stroke="var(--skin-line)" stroke-width="1.9" stroke-linecap="round">
 <path d="M232,225 C244,208 272,206 282,222"/><path d="M282,222 C275,239 245,241 232,225"/>
 <path d="M188,225 C176,208 148,206 138,222"/><path d="M138,222 C145,239 175,241 188,225"/></g>
<circle cx="257" cy="224" r="10" fill="var(--skin-line)" fill-opacity=".8"/>
<circle cx="163" cy="224" r="10" fill="var(--skin-line)" fill-opacity=".8"/>
{A(stroke("M270,228 C278,226 284,224 289,221", "var(--ink)", 4.5, .75), "draw", .46, .72)}
{A(stroke("M150,228 C142,226 136,224 131,221", "var(--ink)", 4.5, .75), "draw", .46, .72)}
{arrow_a(u, "M290,212 C302,204 310,198 316,192", Z["bronze"], 2.6, .76, .94)}
{arrow_a(u, "M130,212 C118,204 110,198 104,192", Z["bronze"], 2.6, .76, .94)}
<circle class="applicator" r="8" fill="var(--surface)" stroke="var(--ink)" stroke-width="2" opacity="0"/>
<circle class="applicator-dot" r="2.6" fill="var(--ink)" opacity="0"/>
</svg>''', "הכל מעל הקפל וכלפי חוץ", 9)


# -------------------------------------------------------------- 09 highlight
def s09(u):
    ov = ""
    for d, (a, b) in zip(["M268,256 C286,246 300,236 310,226", "M152,256 C134,246 120,236 110,226"],
                         seq(2, .05, .48)):
        ov += A(stroke(d, Z["glow"], 10, .6), "draw", a, b)
    pts = [(233,226),(187,226),(210,361),(210,420)]
    for (x, y), (a, b) in zip(pts, seq(4, .45, .92, .08)):
        ov += A(f'<g><circle cx="{x}" cy="{y}" r="13" fill="{Z["glow"]}" fill-opacity=".3"/>'
                f'<circle cx="{x}" cy="{y}" r="6" fill="{Z["glow"]}" fill-opacity=".85"/></g>',
                "pop", a, b, cx=x, cy=y)
    return scene(u, ov, label="ארבע נקודות הארה"), "סאטן · אפס נצנצים", 8


# ------------------------------------------------------------------- 10 lips
def s10(u):
    ov = A(stroke("M198,362 C203,356 207,362 210,364 C213,362 217,356 222,362", Z["glow"], 4), "draw", .06, .32)
    ov += A(stroke("M172,372 C185,358 198,367 210,364 C222,367 235,358 248,372", Z["blush"], 3, .9), "draw", .3, .62)
    ov += arrow_a(u, "M168,376 C164,368 164,362 166,356", Z["blush"], 3, .62, .82)
    ov += arrow_a(u, "M252,376 C256,368 256,362 254,356", Z["blush"], 3, .62, .82)
    ov += A(f'<circle cx="210" cy="356" r="15" fill="none" stroke="{Z["glow"]}"'
            f' stroke-width="2.2" stroke-dasharray="4 3"/>', "pop", .84, .98, cx=210, cy=356)
    return scene(u, ov, label="עיפרון שפתיים"), "קשת קופידון + הרמת זוויות", 8


# --------------------------------------------------------------- 11 set spray
def s11(u):
    """Mist, then the palms actually land on the cheeks and lift straight off."""
    mist = [(120,110,4),(180,86,3),(250,96,4),(310,120,3),(96,190,3),
            (330,200,4),(140,60,3),(280,62,4),(210,72,3)]
    ov = ""
    for (x, y, r), (a, b) in zip(mist, seq(len(mist), .02, .3, .14)):
        ov += A(f'<circle cx="{x}" cy="{y}" r="{r}" fill="{Z["pore"]}" fill-opacity=".4"/>',
                "drop", a, b, dy=40)
    # the palms: slide in from the sides, hold on the cheeks, lift off
    ov += A(hand(126, 322, rot=-14), "press", .40, .58, dx=-150, dy=40, t2=.86, t3=1.0)
    ov += A(hand(294, 322, rot=14), "press", .40, .58, dx=150, dy=40, t2=.86, t3=1.0)
    # warmth under the palms while they are pressing
    ov += clipped(u, A(f'<ellipse cx="210" cy="250" rx="150" ry="200" fill="{Z["glow"]}"'
                       f' fill-opacity=".16"/>', "fade", .58, .74))
    # the 5-second count
    ov += A('<g transform="translate(210,452)">'
            '<circle r="30" fill="var(--surface)" stroke="var(--accent-line)" stroke-width="2.5"/>'
            '<text y="9" text-anchor="middle" font-family="Assistant,sans-serif" font-size="26"'
            ' font-weight="700" fill="var(--accent)">5</text></g>',
            "pop", .62, .76, cx=210, cy=452)
    return scene(u, ov, freckles=True, label="לרסס, להניח כפות ידיים וללחוץ",
                 applicator=False), "להניח · ללחוץ 5 · להרים ישר", 9


SCENES = {0: s00, 1: s01, 2: s02, 3: s03, 4: s04, 5: s05,
          6: s06, 7: s07, 8: s08, 9: s09, 10: s10, 11: s11}

TITLES = {
 0: "הכנה — והמתנה", 1: "טשטוש ממוקד", 2: "Underpainting — ברונזר קרמי",
 3: "סומק קרמי — גבוה", 4: "סקין־טינט — שכבה דקה", 5: "קונסילר — שלוש נקודות",
 6: "פודרה — שלושה אזורים", 7: "גבות — לסרק, לא למלא", 8: "עיניים — חוץ ולמעלה",
 9: "הארה — ארבע נקודות", 10: "שפתיים — הגדרה והרמה", 11: "קיבוע — ולחיצה",
}
