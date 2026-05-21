#!/usr/bin/env python3
"""Rebuild the ChromaDB index from media-memory/metadata.jsonl.

Use when .chroma was wiped, when the embedding model changes, or to
re-embed records that failed the first time.
"""

from __future__ import annotations

import argparse
import sys

import lib


def main() -> int:
    p = argparse.ArgumentParser(description="Rebuild ChromaDB index from metadata.jsonl.")
    p.add_argument("--only-missing", action="store_true", help="Only embed records where embedded=False.")
    args = p.parse_args()

    ok = 0
    skipped = 0
    failed = 0
    for rec in lib.iter_records():
        if args.only_missing and rec.embedded:
            skipped += 1
            continue
        document = lib.build_semantic_document(rec)
        if not document.strip():
            skipped += 1
            continue
        try:
            vector = lib.embed_text(document)
            lib.chroma_upsert(rec, vector, document)
            ok += 1
        except Exception as e:
            print(f"[reindex] {rec.id}: {e}", file=sys.stderr)
            failed += 1

    lib.write_json({"reindexed": ok, "skipped": skipped, "failed": failed})
    return 0


if __name__ == "__main__":
    sys.exit(main())
