"""Shared SVG face-chart primitives for the makeup guide illustrations.

Every diagram in the guide is drawn on the same 420x520 face so a placement
learned in one figure reads identically in the next.
"""

VB = "0 0 420 520"

FACE_D = ("M210,68 C272,68 330,112 334,192 C336,234 330,264 321,294 "
          "C310,338 291,378 261,408 C246,423 227,434 210,434 "
          "C193,434 174,423 159,408 C129,378 110,338 99,294 "
          "C90,264 84,234 86,192 C90,112 148,68 210,68 Z")

HAIR_D = ("M210,36 C300,36 356,98 358,190 C359,254 352,322 360,418 "
          "C362,444 364,462 368,480 L322,480 C318,448 316,412 315,374 "
          "C314,322 318,258 314,206 C312,150 292,110 258,98 "
          "C244,93 228,90 210,90 C192,90 176,93 162,98 "
          "C128,110 108,150 106,206 C102,258 106,322 105,374 "
          "C104,412 102,448 98,480 L52,480 C56,462 58,444 60,418 "
          "C68,322 61,254 62,190 C64,98 120,36 210,36 Z")

NECK_D = "M172,404 C172,432 170,450 163,464 L257,464 C250,450 248,432 248,404"

# freckles — the thing the whole guide is built around keeping visible
FRECKLES = [(168,286,2.1),(180,296,1.7),(156,300,1.9),(190,282,1.5),(174,272,1.6),
            (252,286,2.1),(240,296,1.7),(264,300,1.9),(230,282,1.5),(246,272,1.6),
            (198,268,1.4),(222,268,1.4),(210,258,1.5),(163,266,1.5),(257,266,1.5),
            (196,150,1.3),(224,146,1.3),(210,132,1.2)]


def defs(uid):
    """Arrow markers, scoped per-figure so ids never collide."""
    return f'''<defs>
  <marker id="ar{uid}" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="5.5" markerHeight="5.5"
          orient="auto-start-reverse"><path d="M0,1 L9,5 L0,9 Z" fill="context-stroke"/></marker>
  <clipPath id="fc{uid}"><path d="{FACE_D}"/></clipPath>
</defs>'''


def base(uid, hair=True, freckles=False, features=True, faint=1.0):
    """The face itself: neck, skin, optional freckles, features, hair on top."""
    out = [f'<path d="{NECK_D}" fill="var(--skin)" stroke="var(--skin-edge)" stroke-width="1.4"/>',
           f'<path d="{FACE_D}" fill="var(--skin)" stroke="var(--skin-edge)" stroke-width="1.8"/>']
    if freckles:
        out.append('<g fill="#B07C57" fill-opacity=".5">' + "".join(
            f'<circle cx="{x}" cy="{y}" r="{r}"/>' for x, y, r in FRECKLES) + '</g>')
    if features:
        o = faint
        out.append(f'''<g fill="none" stroke="var(--skin-line)" stroke-width="1.7" stroke-opacity="{o}"
   stroke-linecap="round" stroke-linejoin="round">
 <path d="M232,225 C244,208 272,206 282,222"/><path d="M282,222 C275,239 245,241 232,225"/>
 <path d="M188,225 C176,208 148,206 138,222"/><path d="M138,222 C145,239 175,241 188,225"/>
 <path d="M192,311 C196,323 224,323 228,311"/>
 <path d="M192,311 C184,315 182,325 190,329"/><path d="M228,311 C236,315 238,325 230,329"/>
 <path d="M201,268 C199,286 197,300 195,309" stroke-opacity="{o*.3:.2f}"/>
 <path d="M219,268 C221,286 223,300 225,309" stroke-opacity="{o*.3:.2f}"/>
 <path d="M172,372 C185,358 198,367 210,364 C222,367 235,358 248,372"/>
 <path d="M172,372 C187,394 233,394 248,372"/>
 <path d="M210,364 L210,372" stroke-opacity="{o*.4:.2f}"/>
</g>
<circle cx="257" cy="224" r="10" fill="var(--skin-line)" fill-opacity="{o*.8:.2f}"/>
<circle cx="163" cy="224" r="10" fill="var(--skin-line)" fill-opacity="{o*.8:.2f}"/>
<circle cx="260" cy="221" r="3" fill="#fff" fill-opacity=".8"/>
<circle cx="166" cy="221" r="3" fill="#fff" fill-opacity=".8"/>
<path d="M228,201 C244,187 274,183 296,193 C291,199 282,197 269,198 C253,200 238,204 228,206 Z"
      fill="var(--skin-line)" fill-opacity="{o*.72:.2f}"/>
<path d="M192,201 C176,187 146,183 124,193 C129,199 138,197 151,198 C167,200 182,204 192,206 Z"
      fill="var(--skin-line)" fill-opacity="{o*.72:.2f}"/>''')
    if hair:
        out.append(f'<path d="{HAIR_D}" fill="var(--hair)" fill-opacity=".38"/>')
    return "\n".join(out)


def arrow(uid, d, color="var(--ink)", w=2.4, op=.9, dash=None):
    dd = f' stroke-dasharray="{dash}"' if dash else ""
    return (f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{w}" stroke-opacity="{op}"'
            f' stroke-linecap="round" marker-end="url(#ar{uid})"{dd}/>')


def figure(uid, overlay, hair=True, freckles=False, features=True, label="", cls="fig"):
    """Wrap an overlay (already clipped by the caller where needed) into a full figure."""
    return f'''<svg class="{cls}" viewBox="{VB}" role="img" aria-label="{label}">
{defs(uid)}
{base(uid, hair=hair, freckles=freckles, features=features)}
{overlay}
</svg>'''


def clipped(uid, inner):
    return f'<g clip-path="url(#fc{uid})">{inner}</g>'


# ---- shared zone geometry, so every figure agrees with the master map ----
PORE = ('<ellipse cx="210" cy="152" rx="52" ry="23"/>'
        '<path d="M204,258 C202,284 201,300 200,310 L220,310 C219,300 218,284 216,258 Z"/>'
        '<ellipse cx="250" cy="296" rx="21" ry="17"/><ellipse cx="170" cy="296" rx="21" ry="17"/>')

BRONZE_STROKES = [
    "M318,184 C322,208 318,230 310,246", "M102,184 C98,208 102,230 110,246",
    "M324,254 C306,274 284,286 262,292", "M96,254 C114,274 136,286 158,292",
    "M308,318 C300,352 282,382 260,404", "M112,318 C120,352 138,382 160,404",
]
BLUSH_STROKES = ["M252,282 C274,272 294,258 310,240", "M168,282 C146,272 126,258 110,240"]
