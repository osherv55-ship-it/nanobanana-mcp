"""Generates body-03-routine.html — every step carries its own face diagram."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from facelib import (figure, clipped, arrow, PORE, BRONZE_STROKES, BLUSH_STROKES)

Z = dict(pore="var(--z-pore)", red="var(--z-red)", bronze="var(--z-bronze)",
         blush="var(--z-blush)", glow="var(--z-glow)", conceal="var(--z-conceal)",
         powder="var(--z-powder)", no="var(--cognac)")


def fig00(u):
    ov = clipped(u, f'<ellipse cx="210" cy="250" rx="150" ry="200" fill="{Z["pore"]}" fill-opacity=".13"/>')
    ov += ''.join(f'<g transform="translate({x},{y})"><path d="M0,-7 C4,-2 6,1 6,3 A6,6 0 0 1 -6,3 C-6,1 -4,-2 0,-7 Z"'
                  f' fill="var(--z-pore)" fill-opacity=".55"/></g>' for x, y in
                  [(128,140),(300,150),(112,250),(322,258),(150,392),(276,398)])
    ov += ('<g transform="translate(345,432)"><circle r="30" fill="var(--surface)" stroke="var(--ink)"'
           ' stroke-width="2" stroke-opacity=".5"/><path d="M0,-17 A17,17 0 1 1 -14,9" fill="none"'
           ' stroke="var(--accent)" stroke-width="4.5" stroke-linecap="round"/>'
           '<text y="6" text-anchor="middle" font-family="Assistant,sans-serif" font-size="17"'
           ' font-weight="700" fill="var(--ink)">90</text></g>')
    return figure(u, ov, freckles=True, label="הכנה"), "לחות ← ואז 90 שניות המתנה"


def fig01(u):
    ov = clipped(u, f'<g fill="{Z["pore"]}" fill-opacity=".34">{PORE}</g>')
    for x, y in [(210,120),(186,270),(234,270),(170,286),(250,286)]:
        ov += arrow(u, f"M{x},{y} L{x},{y+26}", Z["pore"], 2.6, .95)
    return figure(u, ov, label="פריימר מטשטש על אזורי הנקבוביות בלבד"), "ללחוץ ↓ · לא למרוח"


def fig02(u):
    inner = "".join(f'<path d="{d}" fill="none" stroke="{Z["bronze"]}" stroke-opacity=".5"'
                    f' stroke-width="21" stroke-linecap="round"/>' for d in BRONZE_STROKES)
    inner += (f'<path d="M225,236 C228,266 229,290 230,306" stroke="{Z["bronze"]}" stroke-opacity=".3"'
              f' stroke-width="7" stroke-linecap="round" fill="none"/>'
              f'<path d="M195,236 C192,266 191,290 190,306" stroke="{Z["bronze"]}" stroke-opacity=".3"'
              f' stroke-width="7" stroke-linecap="round" fill="none"/>')
    ov = clipped(u, inner)
    ov += arrow(u, "M262,300 C286,288 306,272 320,254", Z["bronze"], 3, 1)
    ov += arrow(u, "M158,300 C134,288 114,272 100,254", Z["bronze"], 3, 1)
    return figure(u, ov, label="ברונזר קרמי ברקות, מתחת לעצם הלחי ובקו הלסת"), "תמיד כלפי מעלה וחוץ"


def fig03(u):
    inner = "".join(f'<path d="{d}" fill="none" stroke="{Z["blush"]}" stroke-opacity=".46"'
                    f' stroke-width="30" stroke-linecap="round"/>' for d in BLUSH_STROKES)
    inner += (f'<path d="M92,300 L328,300" stroke="{Z["no"]}" stroke-width="2.6" stroke-opacity=".85"'
              f' stroke-dasharray="7 6"/>')
    ov = clipped(u, inner)
    ov += arrow(u, "M246,290 C270,278 292,262 308,244", Z["blush"], 3, 1)
    ov += arrow(u, "M174,290 C150,278 128,262 112,244", Z["blush"], 3, 1)
    ov += (f'<g transform="translate(344,318)"><circle r="17" fill="var(--cognac-soft)"'
           f' stroke="{Z["no"]}" stroke-width="2"/><path d="M-7,-7 L7,7 M7,-7 L-7,7" stroke="{Z["no"]}"'
           f' stroke-width="3" stroke-linecap="round"/></g>')
    return figure(u, ov, label="סומק גבוה על עצם הלחי, מופנה לרקה"), "שום סומק מתחת לקו הזה"


def fig04(u):
    inner = (f'<g fill="{Z["pore"]}" fill-opacity=".2">'
             '<ellipse cx="210" cy="150" rx="46" ry="26"/>'
             '<ellipse cx="210" cy="300" rx="62" ry="46"/>'
             '<ellipse cx="210" cy="398" rx="34" ry="22"/></g>')
    ov = clipped(u, inner)
    for d in ["M210,300 L268,286", "M210,300 L152,286", "M210,150 L272,138", "M210,150 L148,138"]:
        ov += arrow(u, d, Z["pore"], 2.6, .95)
    return figure(u, ov, freckles=True, label="סקין־טינט על מרכז הפנים בלבד, החוצה עד לאין"), "מהמרכז החוצה · ~40%"


def fig05(u):
    ov = clipped(u, (
        f'<path d="M231,240 C236,250 244,255 253,255 C244,262 233,258 228,248 Z" fill="{Z["conceal"]}" fill-opacity=".62"/>'
        f'<path d="M189,240 C184,250 176,255 167,255 C176,262 187,258 192,248 Z" fill="{Z["conceal"]}" fill-opacity=".62"/>'
        f'<ellipse cx="187" cy="318" rx="9" ry="7" fill="{Z["red"]}" fill-opacity=".62"/>'
        f'<ellipse cx="233" cy="318" rx="9" ry="7" fill="{Z["red"]}" fill-opacity=".62"/>'
        f'<circle cx="272" cy="272" r="7" fill="{Z["red"]}" fill-opacity=".62"/>'))
    for cx, cy, n in [(246,250,"ב"),(210,332,"א"),(288,262,"ג")]:
        ov += (f'<circle cx="{cx}" cy="{cy}" r="13" fill="var(--surface)" stroke="var(--ink)"'
               f' stroke-width="1.6" stroke-opacity=".45"/>'
               f'<text x="{cx}" y="{cy+6}" text-anchor="middle" font-family="Assistant,sans-serif"'
               f' font-size="16" font-weight="700" fill="var(--ink)">{n}</text>')
    return figure(u, ov, label="קונסילר בשלוש נקודות: אודם, שקע פנימי, כתם"), "שלוש נקודות · לא משולש"


def fig06(u):
    ov = clipped(u, (
        f'<g fill="{Z["powder"]}" fill-opacity=".55">'
        '<path d="M206,286 C205,298 204,306 203,312 L217,312 C216,306 215,298 214,286 Z"/>'
        '<ellipse cx="210" cy="403" rx="14" ry="8"/>'
        '<path d="M233,243 C238,250 245,254 252,254 C245,259 235,256 231,249 Z"/>'
        '<path d="M187,243 C182,250 175,254 168,254 C175,259 185,256 189,249 Z"/></g>'))
    return figure(u, ov, label="פודרה על האף, הסנטר ונגיעה מתחת לעין"), "שלושה אזורים · זהו"


def fig07(u):
    ov = ""
    for x in (140,163,186,234,257,280):
        ov += arrow(u, f"M{x},214 L{x},190", Z["bronze"], 2.4, .95)
    ov += (f'<circle cx="152" cy="197" r="11" fill="none" stroke="{Z["bronze"]}" stroke-width="2.4"'
           f' stroke-dasharray="4 3"/>'
           f'<circle cx="292" cy="194" r="11" fill="none" stroke="{Z["bronze"]}" stroke-width="2.4"'
           f' stroke-dasharray="4 3"/>')
    ov += arrow(u, "M296,194 L318,186", Z["bronze"], 2.6, 1)
    return figure(u, ov, label="גבות: סירוק כלפי מעלה ומילוי נקודתי בלבד"), "לסרק ↑ · למלא רק בעיגולים"


def fig08(u):
    """Zoomed eye — the one place a whole-face view is not enough."""
    return f'''<svg class="fig" viewBox="60 150 300 160" role="img" aria-label="מיפוי עפעף עם עיניים פקוחות">
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
<path d="M232,214 C248,204 272,203 288,210" fill="none" stroke="{Z['bronze']}" stroke-width="9"
      stroke-opacity=".5" stroke-linecap="round"/>
<path d="M188,214 C172,204 148,203 132,210" fill="none" stroke="{Z['bronze']}" stroke-width="9"
      stroke-opacity=".5" stroke-linecap="round"/>
<g fill="none" stroke="var(--skin-line)" stroke-width="1.9" stroke-linecap="round">
 <path d="M232,225 C244,208 272,206 282,222"/><path d="M282,222 C275,239 245,241 232,225"/>
 <path d="M188,225 C176,208 148,206 138,222"/><path d="M138,222 C145,239 175,241 188,225"/></g>
<circle cx="257" cy="224" r="10" fill="var(--skin-line)" fill-opacity=".8"/>
<circle cx="163" cy="224" r="10" fill="var(--skin-line)" fill-opacity=".8"/>
<path d="M270,228 C278,226 284,224 289,221" stroke="var(--ink)" stroke-width="4.5"
      stroke-opacity=".75" stroke-linecap="round" fill="none"/>
<path d="M150,228 C142,226 136,224 131,221" stroke="var(--ink)" stroke-width="4.5"
      stroke-opacity=".75" stroke-linecap="round" fill="none"/>
<path d="M290,212 C302,204 310,198 316,192" fill="none" stroke="{Z['bronze']}" stroke-width="2.6"
      stroke-linecap="round" marker-end="url(#ar{u})"/>
<path d="M130,212 C118,204 110,198 104,192" fill="none" stroke="{Z['bronze']}" stroke-width="2.6"
      stroke-linecap="round" marker-end="url(#ar{u})"/>
<text x="210" y="176" text-anchor="middle" font-family="Assistant,sans-serif" font-size="13"
      font-weight="700" fill="{Z['bronze']}">הצללית מעל הקפל — במקום שנשאר גלוי</text>
<text x="210" y="303" text-anchor="middle" font-family="Assistant,sans-serif" font-size="13"
      font-weight="700" fill="var(--ink)">עיפרון מרוח — שליש חיצוני בלבד</text>
</svg>''', "הכל מעל הקפל וכלפי חוץ"


def fig09(u):
    pts = [(288,250),(132,250),(233,226),(187,226),(210,361),(210,420)]
    ov = ""
    for x, y in pts:
        ov += (f'<circle cx="{x}" cy="{y}" r="13" fill="{Z["glow"]}" fill-opacity=".3"/>'
               f'<circle cx="{x}" cy="{y}" r="6" fill="{Z["glow"]}" fill-opacity=".85"/>')
    ov += (f'<path d="M268,256 C286,246 300,236 310,226" stroke="{Z["glow"]}" stroke-opacity=".6"'
           f' stroke-width="10" stroke-linecap="round" fill="none"/>'
           f'<path d="M152,256 C134,246 120,236 110,226" stroke="{Z["glow"]}" stroke-opacity=".6"'
           f' stroke-width="10" stroke-linecap="round" fill="none"/>')
    return figure(u, ov, label="נקודות ההארה: עצם הלחי, פינה פנימית, קשת קופידון"), "סאטן · אפס נצנצים"


def fig10(u):
    ov = (f'<path d="M198,362 C203,356 207,362 210,364 C213,362 217,356 222,362" fill="none"'
          f' stroke="{Z["glow"]}" stroke-width="4" stroke-linecap="round"/>'
          f'<path d="M172,372 C185,358 198,367 210,364 C222,367 235,358 248,372" fill="none"'
          f' stroke="{Z["blush"]}" stroke-width="3" stroke-opacity=".9"/>')
    ov += arrow(u, "M168,376 C164,368 164,362 166,356", Z["blush"], 3, 1)
    ov += arrow(u, "M252,376 C256,368 256,362 254,356", Z["blush"], 3, 1)
    ov += (f'<circle cx="210" cy="356" r="15" fill="none" stroke="{Z["glow"]}" stroke-width="2.2"'
           f' stroke-dasharray="4 3"/>')
    return figure(u, ov, label="עיפרון שפתיים: חידוד קשת הקופידון והרמת שתי הזוויות"), "קשת קופידון + הרמת זוויות"


def fig11(u):
    ov = "".join(f'<circle cx="{x}" cy="{y}" r="{r}" fill="var(--z-pore)" fill-opacity=".4"/>'
                 for x, y, r in [(120,110,4),(180,86,3),(250,96,4),(310,120,3),(96,190,3),
                                 (330,200,4),(140,60,3),(280,62,4),(210,72,3)])
    ov += clipped(u, '<ellipse cx="210" cy="250" rx="150" ry="200" fill="var(--z-glow)" fill-opacity=".14"/>')
    ov += ('<g stroke="var(--ink)" stroke-opacity=".55" stroke-width="2.4" fill="none" stroke-linecap="round">'
           '<path d="M108,300 C96,292 92,278 94,266"/><path d="M312,300 C324,292 328,278 326,266"/></g>')
    ov += arrow(u, "M118,306 L142,316", "var(--ink)", 2.4, .6)
    ov += arrow(u, "M302,306 L278,316", "var(--ink)", 2.4, .6)
    return figure(u, ov, freckles=True, label="ספריי קיבוע ולחיצת כפות ידיים"), "לרסס ואז ללחוץ בכפות הידיים"


FIGS = {0: fig00, 1: fig01, 2: fig02, 3: fig03, 4: fig04, 5: fig05,
        6: fig06, 7: fig07, 8: fig08, 9: fig09, 10: fig10, 11: fig11}
