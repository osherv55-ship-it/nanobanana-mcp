#!/usr/bin/env python3
"""Semantic + structured search across media-memory.

Embeds the query with Gemini Embedding, queries ChromaDB, and applies
metadata filters (type, tags, source, date range) via Chroma's `where`
clause plus a post-filter for tag membership (tags are stored as
comma-separated strings since Chroma metadata is scalar-only).
"""

from __future__ import annotations

import argparse
import sys
from typing import Any

import lib


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Search media-memory.")
    p.add_argument("--query", required=True, help="Natural-language query. Pass '' to skip semantic ranking and only filter.")
    p.add_argument("--top-k", type=int, default=10, help="Max results to return.")
    p.add_argument("--type", choices=["image", "video", "audio", "document", "text", "other"], help="Filter by media type.")
    p.add_argument("--source", help="Exact source match (user_upload, generated, ...).")
    p.add_argument("--tags", help="Comma-separated tags; results must contain ALL of these (AND).")
    p.add_argument("--after", help="ISO date/datetime; only items at or after this timestamp.")
    p.add_argument("--before", help="ISO date/datetime; only items at or before this timestamp.")
    p.add_argument("--min-score", type=float, default=None, help="Drop results with cosine similarity below this.")
    return p.parse_args()


def _build_where(args: argparse.Namespace) -> dict[str, Any] | None:
    """Build a ChromaDB `where` clause from the structured filters.

    Tags are NOT included here — Chroma requires scalar equality and we store
    tags as a joined string; we post-filter for tag membership instead.
    """
    clauses: list[dict[str, Any]] = []
    if args.type:
        clauses.append({"type": args.type})
    if args.source:
        clauses.append({"source": args.source})
    if args.after:
        clauses.append({"timestamp": {"$gte": args.after}})
    if args.before:
        clauses.append({"timestamp": {"$lte": args.before}})
    if not clauses:
        return None
    if len(clauses) == 1:
        return clauses[0]
    return {"$and": clauses}


def _matches_tags(metadata: dict[str, Any], required: list[str]) -> bool:
    if not required:
        return True
    have = {t.strip().lower() for t in (metadata.get("tags") or "").split(",") if t.strip()}
    return all(t in have for t in required)


def main() -> int:
    args = _parse_args()
    where = _build_where(args)
    required_tags = [t.strip().lower() for t in (args.tags or "").split(",") if t.strip()]

    results: list[dict[str, Any]]
    if args.query.strip():
        vector = lib.embed_text(args.query)
        # Over-fetch so we can post-filter tags without running short.
        fetch_k = max(args.top_k * 3, args.top_k)
        raw = lib.chroma_query(vector, top_k=fetch_k, where=where)
    else:
        raw = lib.chroma_get(where=where, limit=args.top_k * 3)
        for r in raw:
            r["score"] = None

    filtered = []
    for r in raw:
        if not _matches_tags(r.get("metadata", {}), required_tags):
            continue
        if args.min_score is not None and r.get("score") is not None and r["score"] < args.min_score:
            continue
        filtered.append({
            "id": r["id"],
            "score": r.get("score"),
            "stored_path": r["metadata"].get("stored_path"),
            "metadata": r["metadata"],
            "document": r.get("document", ""),
        })
        if len(filtered) >= args.top_k:
            break

    lib.write_json({"query": args.query, "count": len(filtered), "results": filtered})
    return 0


if __name__ == "__main__":
    sys.exit(main())
