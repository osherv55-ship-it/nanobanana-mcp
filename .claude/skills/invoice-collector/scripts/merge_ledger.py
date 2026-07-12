#!/usr/bin/env python3
"""Merge new invoice rows into invoices/ledger.csv, dedupe, sort, summarize.

Usage: merge_ledger.py new_rows.csv [more.csv ...]

Each input file: CSV rows (header optional) in ledger schema:
date,vendor,invoice_number,amount,currency,gmail_message_id,notes
"""
import csv
import sys
from collections import defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
LEDGER = REPO_ROOT / "invoices" / "ledger.csv"
FIELDS = ["date", "vendor", "invoice_number", "amount", "currency",
          "gmail_message_id", "notes"]


def read_rows(path):
    rows = []
    with open(path, newline="", encoding="utf-8") as f:
        for raw in csv.reader(f):
            if not raw or raw[0].strip() == "date":
                continue
            raw = [c.strip() for c in raw] + [""] * (len(FIELDS) - len(raw))
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
            totals[r["currency"] or "?"] += float(r["amount"].replace(",", ""))
        except ValueError:
            unknown += 1
    print(f"added {added} rows; ledger now {len(existing)} rows -> {LEDGER}")
    for cur, total in sorted(totals.items()):
        print(f"  total {cur}: {total:,.2f}")
    if unknown:
        print(f"  {unknown} rows with UNKNOWN amount (PDF-only)")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    main(sys.argv[1:])
