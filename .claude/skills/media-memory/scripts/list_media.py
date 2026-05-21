#!/usr/bin/env python3
"""List/filter media-memory records by structured metadata only (no embedding).

Reads the JSONL log directly so this works even if ChromaDB is unavailable.
"""

from __future__ import annotations

import argparse
import sys

import lib


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="List media-memory records by metadata filters.")
    p.add_argument("--type", choices=["image", "video", "audio", "document", "text", "other"])
    p.add_argument("--source")
    p.add_argument("--tags", help="Comma-separated tags; result must contain ALL.")
    p.add_argument("--after", help="ISO timestamp lower bound (inclusive).")
    p.add_argument("--before", help="ISO timestamp upper bound (inclusive).")
    p.add_argument("--limit", type=int, default=50)
    p.add_argument("--order", choices=["newest", "oldest"], default="newest")
    return p.parse_args()


def main() -> int:
    args = _parse_args()
    required_tags = [t.strip().lower() for t in (args.tags or "").split(",") if t.strip()]

    rows = []
    for rec in lib.iter_records():
        if args.type and rec.type != args.type:
            continue
        if args.source and rec.source != args.source:
            continue
        if args.after and rec.timestamp < args.after:
            continue
        if args.before and rec.timestamp > args.before:
            continue
        if required_tags and not all(t in rec.tags for t in required_tags):
            continue
        rows.append(rec.to_dict())

    rows.sort(key=lambda r: r["timestamp"], reverse=(args.order == "newest"))
    rows = rows[: args.limit]
    lib.write_json({"count": len(rows), "results": rows})
    return 0


if __name__ == "__main__":
    sys.exit(main())
