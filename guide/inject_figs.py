"""Re-injects generated SVG into the chapter sources.

The generators are the source of truth; the HTML in guide/src only ever holds
their output. Run this after touching gen_donts.py or gen_undereye.py, then
run build.py. Injection is idempotent — it rewrites the same regions in place.
"""
import re, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gen_donts import PAIRS, pair_html
from gen_undereye import trio_html

SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src")


def inject_donts():
    p = os.path.join(SRC, "body-09-dont.html")
    html = open(p, encoding="utf-8").read()
    hit = []

    def sub(m):
        block = m.group(0)
        for key, (_, _, cap_bad, _) in PAIRS.items():
            if cap_bad in block:
                hit.append(key)
                return pair_html(key)
        raise SystemExit("unrecognised .vs block:\n" + block[:200])

    html = re.sub(r'<div class="vs">.*?</div>', sub, html, flags=re.S)
    open(p, "w", encoding="utf-8").write(html)
    print(f"  donts: {len(hit)} pairs -> {', '.join(hit)}")


def inject_undereye():
    p = os.path.join(SRC, "body-04-tech.html")
    html = open(p, encoding="utf-8").read()
    a, b = "<!--UE_FIG-->", "<!--/UE_FIG-->"
    if a not in html or b not in html:
        raise SystemExit("missing UE_FIG markers in body-04-tech.html")
    html = re.sub(re.escape(a) + ".*?" + re.escape(b), a + trio_html() + b, html, flags=re.S)
    open(p, "w", encoding="utf-8").write(html)
    print("  undereye: 3 panels")


if __name__ == "__main__":
    inject_donts()
    inject_undereye()
