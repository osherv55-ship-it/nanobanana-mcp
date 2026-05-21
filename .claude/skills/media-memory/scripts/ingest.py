#!/usr/bin/env python3
"""Ingest a media file into media-memory.

Accepts a local path, an HTTPS URL, or base64 bytes. Stores the file under
media-memory/YYYY/MM/, appends a metadata record to metadata.jsonl, and
embeds the semantic document into the local ChromaDB collection.
"""

from __future__ import annotations

import argparse
import base64
import json
import shutil
import sys
import urllib.request
import uuid
from datetime import datetime, timezone
from pathlib import Path

import lib


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Ingest a file into media-memory.")
    src = p.add_mutually_exclusive_group(required=True)
    src.add_argument("--path", help="Local path to a file to ingest.")
    src.add_argument("--url", help="HTTPS URL to download and ingest.")
    src.add_argument("--base64", help="Base64-encoded file bytes (use with --filename and --mime-type).")
    src.add_argument("--stdin-base64", action="store_true", help="Read base64 bytes from stdin (use with --filename and --mime-type).")

    p.add_argument("--filename", help="Filename to assign (required with --base64 / --stdin-base64 / --url without a clear name).")
    p.add_argument("--mime-type", help="MIME type override (required with --base64 / --stdin-base64 when not inferable).")
    p.add_argument("--source", default="unknown", help="Where the asset came from (user_upload, generated, web_download, ...).")
    p.add_argument("--description", default="", help="Human-written description. If empty, auto-generated with Gemini.")
    p.add_argument("--extracted-text", default="", help="Optional pre-extracted OCR/transcript text.")
    p.add_argument("--tags", default="", help="Comma-separated semantic tags.")
    p.add_argument("--extra", default="", help="JSON object of extra metadata.")
    p.add_argument("--no-embed", action="store_true", help="Skip embedding (still stores file + metadata).")
    p.add_argument("--no-auto-describe", action="store_true", help="Skip Gemini auto-description even if no description provided.")
    return p.parse_args()


def _load_source(args: argparse.Namespace) -> tuple[bytes, str, str]:
    """Return (bytes, filename, mime_type) regardless of input mode."""
    if args.path:
        src = Path(args.path).expanduser().resolve()
        if not src.is_file():
            raise SystemExit(f"File not found: {src}")
        data = src.read_bytes()
        filename = args.filename or src.name
        mime_type = args.mime_type or lib.infer_mime(src)
        return data, filename, mime_type

    if args.url:
        if not args.url.startswith("https://"):
            raise SystemExit("--url must be HTTPS.")
        with urllib.request.urlopen(args.url) as resp:
            data = resp.read()
            mime_type = args.mime_type or resp.headers.get_content_type() or "application/octet-stream"
        # Derive filename from URL tail if not given.
        filename = args.filename or args.url.rsplit("/", 1)[-1].split("?")[0] or "downloaded"
        return data, filename, mime_type

    if args.base64:
        if not args.filename:
            raise SystemExit("--filename is required with --base64.")
        data = base64.b64decode(args.base64)
        mime_type = args.mime_type or lib.infer_mime(Path(args.filename))
        return data, args.filename, mime_type

    if args.stdin_base64:
        if not args.filename:
            raise SystemExit("--filename is required with --stdin-base64.")
        data = base64.b64decode(sys.stdin.read().strip())
        mime_type = args.mime_type or lib.infer_mime(Path(args.filename))
        return data, args.filename, mime_type

    raise SystemExit("No source provided.")


def _store_file(data: bytes, filename: str, file_id: str) -> Path:
    now = datetime.now(timezone.utc)
    year_month_dir = lib.MEDIA_DIR / f"{now.year:04d}" / f"{now.month:02d}"
    year_month_dir.mkdir(parents=True, exist_ok=True)
    # Sanitize filename: strip path separators, keep extension.
    safe_name = Path(filename).name.replace("/", "_").replace("\\", "_")
    dest = year_month_dir / f"{file_id}_{safe_name}"
    dest.write_bytes(data)
    return dest


def main() -> int:
    args = _parse_args()
    data, filename, mime_type = _load_source(args)

    file_id = str(uuid.uuid4())
    stored = _store_file(data, filename, file_id)

    media_type = lib.infer_type(mime_type)
    tags = [t.strip().lower() for t in args.tags.split(",") if t.strip()]
    extra = json.loads(args.extra) if args.extra else {}

    description = args.description.strip()
    extracted_text = args.extracted_text.strip()

    # Auto-describe with Gemini multimodal when caller didn't supply a description,
    # we have inline-data-friendly bytes, and the caller didn't opt out.
    auto_describable = mime_type.startswith(("image/", "audio/", "video/")) or mime_type == "application/pdf"
    if not description and auto_describable and not args.no_auto_describe:
        d, et, t = lib.describe_media(data, mime_type)
        description = d
        if not extracted_text:
            extracted_text = et
        # Merge auto-tags with caller-provided ones, preserving order, no dupes.
        for tag in t:
            if tag not in tags:
                tags.append(tag)

    # For plain text files, read content as extracted_text if not provided.
    if not extracted_text and media_type == "text":
        try:
            extracted_text = data.decode("utf-8", errors="replace")[:50_000]
        except Exception:
            pass

    rec = lib.Record(
        id=file_id,
        filename=filename,
        stored_path=str(stored.relative_to(lib.REPO_ROOT)),
        type=media_type,
        mime_type=mime_type,
        size_bytes=len(data),
        timestamp=lib.iso_now(),
        source=args.source,
        description=description,
        extracted_text=extracted_text,
        tags=tags,
        embedding_model="",
        embedded=False,
        extra=extra,
    )

    if not args.no_embed:
        document = lib.build_semantic_document(rec)
        if document.strip():
            try:
                vector = lib.embed_text(document)
                lib.chroma_upsert(rec, vector, document)
                rec.embedded = True
                rec.embedding_model = lib.EMBED_MODEL
            except Exception as e:
                print(f"[media-memory] embedding failed (record still saved): {e}", file=sys.stderr)
        else:
            print("[media-memory] no semantic content to embed; skipping vector.", file=sys.stderr)

    lib.append_record(rec)
    lib.write_json({"ok": True, "record": rec.to_dict()})
    return 0


if __name__ == "__main__":
    sys.exit(main())
