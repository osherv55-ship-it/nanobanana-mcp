#!/usr/bin/env python3
"""Merge new invoice rows into invoices/ledger.csv, dedupe, sort, summarize.

Usage: merge_ledger.py new_rows.csv [more.csv ...]

Each input file: CSV rows (header optional) in ledger schema:
date,vendor,invoice_number,amount,currency,direction,gmail_message_id,notes

direction is "income" (the user's business issued the document) or "expense"
(the user is the payer). Rows in the old 7-column schema (no direction) are
accepted and upgraded with direction=UNKNOWN.
"""
import csv
import sys
from collections import defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
LEDGER = REPO_ROOT / "invoices" / "ledger.csv"
FIELDS = ["date", "vendor", "invoice_number", "amount", "currency",
          "direction", "gmail_message_id", "notes"]
OLD_FIELDS = ["date", "vendor", "invoice_number", "amount", "currency",
              "gmail_message_id", "notes"]


DIRECTIONS = {"income", "expense", "UNKNOWN"}


def read_rows(path):
    rows = []
    with open(path, newline="", encoding="utf-8") as f:
        for raw in csv.reader(f):
            if not raw or raw[0].strip() == "date":
                continue
            raw = [c.strip() for c in raw]
            # Old 7-column rows have a gmail id (hex) where direction sits.
            if len(raw) < 6 or raw[5] not in DIRECTIONS:
                raw = dict(zip(OLD_FIELDS, raw + [""] * len(OLD_FIELDS)))
                raw["direction"] = "UNKNOWN"
                rows.append({k: raw.get(k, "") for k in FIELDS})
            else:
                raw += [""] * (len(FIELDS) - len(raw))
                rows.append(dict(zip(FIELDS, raw[: len(FIELDS)])))
    return rows


def main(paths):
    existing = read_rows(LEDGER) if LEDGER.exists() else []
    seen = {(r["gmail_message_id"], r["invoice_number"]) for r in existing}
    added = 0
    for p in paths:
        for r in read_rows(p):
            key = (r["gmail_message_id"], r["invoice_number"])
            if key in seen:
                continue
            seen.add(key)
            existing.append(r)
            added += 1

    existing.sort(key=lambda r: (r["date"], r["vendor"]))
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    with open(LEDGER, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(existing)

    totals = defaultdict(float)
    unknown = 0
    for r in existing:
        try:
            amt = float(r["amount"].replace(",", ""))
        except ValueError:
            unknown += 1
            continue
        totals[(r["direction"] or "UNKNOWN", r["currency"] or "?")] += amt
    print(f"added {added} rows; ledger now {len(existing)} rows -> {LEDGER}")
    for (direction, cur), total in sorted(totals.items()):
        print(f"  {direction} {cur}: {total:,.2f}")
    if unknown:
        print(f"  {unknown} rows with UNKNOWN amount (PDF-only)")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    main(sys.argv[1:])
