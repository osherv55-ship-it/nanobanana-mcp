#!/usr/bin/env python3
"""Flag dosing language near restricted compounds in the skill's files or in an agent output.

Usage: python3 dose_scan.py <file-or-dir> [...]
Exit code 1 if any hit is found. Restricted = peptides, research compounds,
prescription drugs and hormones (see SKILL.md, dosing boundary). Supplements are allowed.
"""
import re, sys, pathlib

RESTRICTED = [
    r"BPC[- ]?157", r"TB[- ]?500", r"thymosin", r"MOTS[- ]?c", r"SS[- ]?31", r"elamipretide", r"epitalon|epithalon",
    r"GHK[- ]?Cu", r"\bKPV\b", r"\bDSIP\b", r"kisspeptin", r"CJC[- ]?1295", r"ipamorelin", r"tesamorelin",
    r"5[- ]?amino[- ]?1MQ", r"retatrutide|רטטרוטייד", r"tirzepatide|mounjaro|zepbound", r"semaglutide|ozempic|wegovy",
    r"methylene blue|מתילן", r"metformin|מטפורמין", r"testosterone|טסטוסטרון|\bTRT\b", r"\bhCG\b", r"anastrozole",
    r"\bT3\b|liothyronine|levothyroxine", r"\bDHEA\b", r"\bLDN\b|naltrexone", r"rapamycin|sirolimus", r"aniracetam",
    r"enclomiphene|clomiphene", r"\bNAD\+? (?:inject|IV|sub)", r"SARMs?", r"MK[- ]?677", r"cerebrolysin",
]
AMOUNT = r"\b\d+(?:[.,]\d+)?\s?(?:mg|mcg|µg|ug|iu|IU|units?|ml|mL|מ\"ג|מ״ג|מק\"ג|מיקרוגרם|מיליגרם|יחידות)\b"
ROUTE = r"\b(?:subq|sub-q|subcutaneous(?:ly)?|intramuscular(?:ly)?|\bIM\b|intranasal(?:ly)?|reconstitut\w*|bacteriostatic|twice (?:daily|weekly|a week)|once (?:daily|weekly|a week)|\d+\s?(?:x|times)\s?(?:/|per|a)\s?(?:day|week)|\d+ weeks? on|תת[- ]עורי|לתוך השריר|פעמיים ביום|פעם ביום|פעמיים בשבוע)\b"
WINDOW = 120  # characters on each side of a restricted name, same line only

def scan(text):
    hits = []
    for rx in RESTRICTED:
        for m in re.finditer(rx, text, re.I):
            ls = text.rfind("\n", 0, m.start()) + 1
            le = text.find("\n", m.end()); le = len(text) if le < 0 else le
            a, b = max(ls, m.start() - WINDOW), min(le, m.end() + WINDOW)
            ctx = text[a:b]
            for kind, pat in (("amount", AMOUNT), ("route/schedule", ROUTE)):
                mm = re.search(pat, ctx, re.I)
                if mm:
                    line = text.count("\n", 0, m.start()) + 1
                    hits.append((line, m.group(0), kind, ctx.replace("\n", " ").strip()))
                    break
    return hits

def main(paths):
    files = []
    for p in paths:
        p = pathlib.Path(p)
        files += sorted(p.rglob("*.md")) if p.is_dir() else [p]
    total = 0
    for f in files:
        if f.name == "dose_scan.py":
            continue
        hits = scan(f.read_text(errors="ignore"))
        seen = set()
        for line, name, kind, ctx in hits:
            key = (line, name.lower())
            if key in seen:
                continue
            seen.add(key); total += 1
            print(f"{f}:{line}: [{kind}] {name} :: …{ctx[:220]}…")
    print(f"\n{total} potential dosing hit(s)")
    return 1 if total else 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:] or ["."]))
