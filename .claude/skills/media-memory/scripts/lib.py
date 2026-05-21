"""Shared utilities for the media-memory skill.

Resolves repo paths, configures Gemini and ChromaDB clients, and exposes
helpers for MIME/type inference, multimodal description, embedding, and
ChromaDB upsert/query.
"""

from __future__ import annotations

import json
import mimetypes
import os
import sys
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

# Resolve repo root from this file's location: <repo>/.claude/skills/media-memory/scripts/lib.py
REPO_ROOT = Path(__file__).resolve().parents[4]
MEDIA_DIR = REPO_ROOT / "media-memory"
METADATA_PATH = MEDIA_DIR / "metadata.jsonl"
CHROMA_DIR = REPO_ROOT / ".chroma"
COLLECTION_NAME = "media_memory"

EMBED_MODEL = os.environ.get("MEDIA_MEMORY_EMBED_MODEL", "gemini-embedding-001")
DESCRIBE_MODEL = os.environ.get("MEDIA_MEMORY_DESCRIBE_MODEL", "gemini-2.5-flash")


def _ensure_dirs() -> None:
    MEDIA_DIR.mkdir(parents=True, exist_ok=True)
    CHROMA_DIR.mkdir(parents=True, exist_ok=True)


def infer_type(mime_type: str) -> str:
    """Map a MIME type to one of our high-level categories."""
    if not mime_type:
        return "other"
    mt = mime_type.lower()
    if mt.startswith("image/"):
        return "image"
    if mt.startswith("video/"):
        return "video"
    if mt.startswith("audio/"):
        return "audio"
    if mt.startswith("text/"):
        return "text"
    if mt in {
        "application/pdf",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/vnd.ms-excel",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/vnd.ms-powerpoint",
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        "application/rtf",
        "application/json",
        "application/xml",
    }:
        return "document"
    return "other"


def infer_mime(path: Path) -> str:
    mt, _ = mimetypes.guess_type(str(path))
    return mt or "application/octet-stream"


def iso_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ---------- Metadata I/O ----------

@dataclass
class Record:
    id: str
    filename: str
    stored_path: str
    type: str
    mime_type: str
    size_bytes: int
    timestamp: str
    source: str
    description: str
    extracted_text: str = ""
    tags: list[str] = field(default_factory=list)
    embedding_model: str = ""
    embedded: bool = False
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def append_record(rec: Record) -> None:
    _ensure_dirs()
    with METADATA_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec.to_dict(), ensure_ascii=False) + "\n")


def iter_records() -> Iterable[Record]:
    if not METADATA_PATH.exists():
        return
    with METADATA_PATH.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            d = json.loads(line)
            yield Record(**d)


def load_record(record_id: str) -> Record | None:
    for r in iter_records():
        if r.id == record_id:
            return r
    return None


# ---------- Gemini ----------

def _gemini_client():
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is not set. Export it (same key as the MCP server) before using media-memory."
        )
    from google import genai
    return genai.Client(api_key=api_key)


def describe_media(file_bytes: bytes, mime_type: str) -> tuple[str, str, list[str]]:
    """Use Gemini multimodal to produce (description, extracted_text, tags).

    For image/audio/video/pdf, we send the bytes as inline_data alongside an
    instruction asking for a strict-JSON response. Falls back gracefully to
    an empty description if the model output can't be parsed.
    """
    from google.genai import types

    client = _gemini_client()
    prompt = (
        "Describe this media for a personal memory index. Respond as strict JSON with keys:\n"
        '  - description (string, 1-3 sentences, factual)\n'
        '  - extracted_text (string, transcript for audio/video, OCR for images/PDFs, "" if none)\n'
        '  - tags (array of 3-8 short lowercase semantic tags)\n'
        "No markdown, no commentary, just the JSON object."
    )
    try:
        resp = client.models.generate_content(
            model=DESCRIBE_MODEL,
            contents=[
                types.Part.from_bytes(data=file_bytes, mime_type=mime_type),
                prompt,
            ],
            config=types.GenerateContentConfig(response_mime_type="application/json"),
        )
        text = (resp.text or "").strip()
        data = json.loads(text)
        return (
            str(data.get("description", "")).strip(),
            str(data.get("extracted_text", "")).strip(),
            [str(t).strip().lower() for t in data.get("tags", []) if str(t).strip()],
        )
    except Exception as e:
        print(f"[media-memory] describe_media failed: {e}", file=sys.stderr)
        return "", "", []


def embed_text(text: str) -> list[float]:
    """Embed a text document with Gemini Embedding."""
    if not text.strip():
        raise ValueError("Cannot embed empty text.")
    client = _gemini_client()
    result = client.models.embed_content(model=EMBED_MODEL, contents=text)
    # google-genai returns ContentEmbedding (or list of them).
    emb = result.embeddings
    if isinstance(emb, list):
        emb = emb[0]
    values = getattr(emb, "values", None) or getattr(emb, "value", None) or emb
    return list(values)


def build_semantic_document(rec: Record) -> str:
    """Concatenate the fields we want to embed."""
    parts = [
        f"Filename: {rec.filename}",
        f"Type: {rec.type}",
        f"Source: {rec.source}",
        f"Tags: {', '.join(rec.tags)}" if rec.tags else "",
        f"Description: {rec.description}" if rec.description else "",
        f"Extracted text: {rec.extracted_text}" if rec.extracted_text else "",
    ]
    return "\n".join(p for p in parts if p)


# ---------- ChromaDB ----------

def chroma_collection():
    """Return the persistent collection, creating it if needed."""
    import chromadb
    _ensure_dirs()
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"description": "media-memory: multimodal asset index"},
    )


def _chroma_metadata(rec: Record) -> dict[str, Any]:
    """Chroma only accepts scalar metadata values. Flatten lists/dicts."""
    return {
        "filename": rec.filename,
        "stored_path": rec.stored_path,
        "type": rec.type,
        "mime_type": rec.mime_type,
        "size_bytes": rec.size_bytes,
        "timestamp": rec.timestamp,
        "source": rec.source,
        # Tags stored as comma-separated string; we expose a $contains-style
        # filter in search.py for substring matching on this field.
        "tags": ",".join(rec.tags),
        "embedding_model": rec.embedding_model,
    }


def chroma_upsert(rec: Record, vector: list[float], document: str) -> None:
    col = chroma_collection()
    col.upsert(
        ids=[rec.id],
        embeddings=[vector],
        documents=[document],
        metadatas=[_chroma_metadata(rec)],
    )


def chroma_query(
    vector: list[float],
    top_k: int,
    where: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    col = chroma_collection()
    kwargs: dict[str, Any] = {"query_embeddings": [vector], "n_results": top_k}
    if where:
        kwargs["where"] = where
    res = col.query(**kwargs)
    out: list[dict[str, Any]] = []
    ids = (res.get("ids") or [[]])[0]
    dists = (res.get("distances") or [[]])[0]
    metas = (res.get("metadatas") or [[]])[0]
    docs = (res.get("documents") or [[]])[0]
    for i, _id in enumerate(ids):
        dist = dists[i] if i < len(dists) else None
        # Chroma returns cosine distance (0=same). Convert to similarity in [-1, 1].
        score = (1.0 - dist) if isinstance(dist, (int, float)) else None
        out.append({
            "id": _id,
            "score": score,
            "metadata": metas[i] if i < len(metas) else {},
            "document": docs[i] if i < len(docs) else "",
        })
    return out


def chroma_get(where: dict[str, Any] | None = None, limit: int | None = None) -> list[dict[str, Any]]:
    col = chroma_collection()
    kwargs: dict[str, Any] = {}
    if where:
        kwargs["where"] = where
    if limit:
        kwargs["limit"] = limit
    res = col.get(**kwargs)
    out: list[dict[str, Any]] = []
    for i, _id in enumerate(res.get("ids", [])):
        out.append({
            "id": _id,
            "metadata": res["metadatas"][i] if res.get("metadatas") else {},
            "document": res["documents"][i] if res.get("documents") else "",
        })
    return out


# ---------- CLI helpers ----------

def write_json(obj: Any) -> None:
    json.dump(obj, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
