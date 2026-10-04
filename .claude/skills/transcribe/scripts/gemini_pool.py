"""Gemini free-tier model pool.

Free-tier keys have small per-model limits (requests/minute and requests/day). The pool spreads
calls across several models, paces each one, honours the API's retryDelay on per-minute 429s and
drops a model for the rest of the run once its daily quota is gone. When every model is spent,
generate() raises Exhausted so callers can fall back instead of failing.
"""
import base64
import json
import os
import re
import threading
import time
import urllib.error
import urllib.request

API = "https://generativelanguage.googleapis.com"

# Full Flash models: better transcripts. Lite models: cheaper, separate quotas, fine for on-screen text.
FULL_MODELS = ["gemini-3.5-flash", "gemini-3.8-flash", "gemini-3.7-flash", "gemini-3.6-flash",
               "gemini-3-flash-preview", "gemini-flash-latest", "gemini-2.5-flash"]
LITE_MODELS = ["gemini-3.5-flash-lite", "gemini-3.1-flash-lite", "gemini-flash-lite-latest",
               "gemini-3.1-flash-lite-preview"]

INLINE_LIMIT = 19_000_000  # inline_data request cap is 20 MB; larger files go through the Files API


class Exhausted(Exception):
    pass


def _key():
    k = os.environ.get("GEMINI_API_KEY")
    if not k:
        raise RuntimeError("GEMINI_API_KEY is not set")
    return k


class Pool:
    def __init__(self, models, min_interval=5.0):
        self.models = list(models)
        self.next_ok = {m: 0.0 for m in self.models}
        self.dead = set()
        self.min_interval = min_interval
        self.lock = threading.Lock()

    def _acquire(self):
        while True:
            with self.lock:
                live = [m for m in self.models if m not in self.dead]
                if not live:
                    raise Exhausted("all Gemini models are out of quota for today")
                m = min(live, key=lambda x: self.next_ok[x])
                wait = self.next_ok[m] - time.time()
                if wait <= 0:
                    self.next_ok[m] = time.time() + self.min_interval
                    return m
            time.sleep(min(wait, 2))

    def _penalize(self, m, body):
        with self.lock:
            if "PerDay" in body:
                self.dead.add(m)
                print(f"[gemini] {m}: daily quota exhausted, dropped", flush=True)
            else:
                rd = re.findall(r'"retryDelay":\s*"(\d+)', body)
                self.next_ok[m] = time.time() + (int(rd[0]) + 1 if rd else 20)

    def generate(self, parts, gen_config=None, timeout=900):
        body = {"contents": [{"parts": parts}]}
        if gen_config:
            body["generationConfig"] = gen_config
        data = json.dumps(body).encode()
        for _ in range(4 * len(self.models) + 4):
            m = self._acquire()
            req = urllib.request.Request(f"{API}/v1beta/models/{m}:generateContent?key={_key()}", data=data,
                                         headers={"Content-Type": "application/json"}, method="POST")
            try:
                with urllib.request.urlopen(req, timeout=timeout) as r:
                    resp = json.load(r)
            except urllib.error.HTTPError as e:
                err = e.read().decode(errors="replace")
                if e.code == 429:
                    self._penalize(m, err)
                    continue
                if e.code == 404:  # model retired for this key
                    with self.lock:
                        self.dead.add(m)
                    continue
                if e.code in (500, 502, 503, 504):
                    time.sleep(5)
                    continue
                raise RuntimeError(f"Gemini {m} HTTP {e.code}: {err[:400]}")
            try:
                text = "".join(p.get("text", "") for p in resp["candidates"][0]["content"]["parts"])
            except (KeyError, IndexError):
                raise RuntimeError(f"Gemini {m} returned no text: {json.dumps(resp)[:400]}")
            return m, text
        raise RuntimeError("Gemini: too many retries")


def media_part(path, mime):
    """Inline small files; upload larger ones through the resumable Files API."""
    size = os.path.getsize(path)
    if size < INLINE_LIMIT:
        return {"inline_data": {"mime_type": mime, "data": base64.b64encode(open(path, "rb").read()).decode()}}
    start = urllib.request.Request(
        f"{API}/upload/v1beta/files?key={_key()}",
        data=json.dumps({"file": {"display_name": os.path.basename(path)}}).encode(),
        headers={"X-Goog-Upload-Protocol": "resumable", "X-Goog-Upload-Command": "start",
                 "X-Goog-Upload-Header-Content-Length": str(size),
                 "X-Goog-Upload-Header-Content-Type": mime, "Content-Type": "application/json"},
        method="POST")
    with urllib.request.urlopen(start, timeout=120) as r:
        upload_url = r.headers["X-Goog-Upload-URL"]
    with open(path, "rb") as f:
        up = urllib.request.Request(upload_url, data=f.read(),
                                    headers={"Content-Length": str(size), "X-Goog-Upload-Offset": "0",
                                             "X-Goog-Upload-Command": "upload, finalize"}, method="POST")
    with urllib.request.urlopen(up, timeout=900) as r:
        info = json.load(r)["file"]
    for _ in range(120):
        with urllib.request.urlopen(f"{API}/v1beta/{info['name']}?key={_key()}", timeout=60) as r:
            state = json.load(r)["state"]
        if state == "ACTIVE":
            return {"file_data": {"mime_type": mime, "file_uri": info["uri"]}}
        if state == "FAILED":
            raise RuntimeError("Gemini file processing FAILED")
        time.sleep(5)
    raise RuntimeError("Gemini file never became ACTIVE")
