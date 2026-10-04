#!/usr/bin/env python3
"""Transcribe local media or any yt-dlp URL (TikTok / YouTube / Instagram / Drive file, single video or a
whole profile / playlist) into .txt / .srt / .json per item plus a combined.md.

Engines:
  whisper     Local faster-whisper (default). No API key, no quota. Hebrew (--lang he) uses ivrit.ai's
              Hebrew-tuned large-v3-turbo; other languages use large-v3-turbo. --fast uses "small".
  elevenlabs  ElevenLabs Scribe (needs ELEVENLABS_API_KEY with Speech-to-Text): word timing + speakers.
  gemini      Gemini multimodal (needs GEMINI_API_KEY): speech + on-screen text + visual description.
              Free-tier quota is small; spreads calls over several models and stops cleanly when spent.
  --visual    Adds a Gemini pass (on-screen text, labels, what is shown) on top of whisper/elevenlabs.
"""
import argparse
import concurrent.futures as cf
import datetime as dt
import glob
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
import uuid

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gemini_pool  # noqa: E402

MEDIA_EXT = {".mp4", ".mov", ".m4v", ".mkv", ".webm", ".avi", ".mp3", ".m4a", ".wav", ".aac", ".ogg",
             ".opus", ".flac", ".wma", ".amr", ".3gp"}
VIDEO_EXT = {".mp4", ".mov", ".m4v", ".mkv", ".webm", ".avi", ".3gp"}
MIME = {".mp4": "video/mp4", ".m4v": "video/mp4", ".mov": "video/quicktime", ".webm": "video/webm",
        ".mkv": "video/x-matroska", ".avi": "video/x-msvideo", ".3gp": "video/3gpp", ".mp3": "audio/mpeg",
        ".m4a": "audio/mp4", ".wav": "audio/wav", ".aac": "audio/aac", ".ogg": "audio/ogg",
        ".opus": "audio/ogg", ".flac": "audio/flac"}

WHISPER_MODELS = {"he": "ivrit-ai/whisper-large-v3-turbo-ct2"}
WHISPER_DEFAULT = "deepdml/faster-whisper-large-v3-turbo-ct2"
WHISPER_FAST = "Systran/faster-whisper-small"

# ElevenLabs takes ISO 639-3 codes.
EL_LANG = {"he": "heb", "en": "eng", "ar": "ara", "es": "spa", "fr": "fra", "de": "deu", "it": "ita",
           "ru": "rus", "pt": "por", "nl": "nld", "pl": "pol", "tr": "tur", "uk": "ukr", "ja": "jpn",
           "ko": "kor", "zh": "zho", "hi": "hin"}

GEMINI_TRANSCRIBE_PROMPT = """Transcribe this media completely. Return JSON only:
{"language": "<ISO 639-1>",
 "segments": [{"start": <seconds, number>, "end": <seconds, number>, "text": "<verbatim speech>"}],
 "on_screen_text": ["<every caption, overlay, label, package or vial text, number shown>"],
 "visual": "<step by step: what is physically shown and done>"}
Speech stays in its original language, verbatim, nothing summarized or translated. If there is no speech,
return an empty segments list."""

GEMINI_VISUAL_PROMPT = """Describe only what is SEEN in this video. Return JSON only:
{"on_screen_text": ["<every caption, overlay, label, package or vial text, number shown, verbatim>"],
 "visual": "<step by step: what is physically shown and done>"}
Do not transcribe the speech."""

_print_lock = threading.Lock()


def log(*a):
    with _print_lock:
        print(*a, flush=True)


def die(msg):
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(2)


# ---------------------------------------------------------------- inputs

def slug(s, n=60):
    s = re.sub(r"[^\w\-.]+", "_", s, flags=re.UNICODE).strip("_")
    return s[:n] or "item"


def is_tiktok(url):
    return "tiktok.com" in (url or "")


def ytdlp_base(url, args):
    cmd = [sys.executable, "-m", "yt_dlp", "--no-warnings"]
    if is_tiktok(url):
        try:
            import curl_cffi  # noqa: F401  (TikTok blocks plain clients; impersonation needs curl_cffi)
            cmd += ["--impersonate", "chrome"]
        except ImportError:
            pass
    if args.cookies:
        cmd += ["--cookies", args.cookies]
    return cmd


def item_from_info(e, fallback_url):
    url = e.get("webpage_url") or e.get("url") or fallback_url
    if not re.match(r"https?://", url or ""):
        url = fallback_url
    vid = str(e.get("id") or hashlib.md5(url.encode()).hexdigest()[:12])
    ts = e.get("timestamp")
    if not ts and e.get("upload_date"):
        try:
            ts = dt.datetime.strptime(e["upload_date"], "%Y%m%d").replace(tzinfo=dt.timezone.utc).timestamp()
        except ValueError:
            ts = None
    return {"id": slug(f"{e.get('ie_key') or e.get('extractor_key') or 'web'}-{vid}".lower()),
            "url": url, "path": None,
            "meta": {k: e.get(k) for k in ("title", "description", "uploader", "channel", "duration",
                                            "view_count", "like_count", "comment_count")} | {"timestamp": ts}}


def expand_url(url, args):
    cmd = ytdlp_base(url, args) + ["--flat-playlist", "--dump-json", url]
    for attempt in range(3):
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)
        lines = [l for l in r.stdout.splitlines() if l.strip().startswith("{")]
        if lines:
            break
        time.sleep(3 * (attempt + 1))
    else:
        raise RuntimeError(f"yt-dlp could not list {url}: {r.stderr.strip()[-400:]}")
    items = [item_from_info(json.loads(l), url) for l in lines]
    since = args.since and dt.datetime.strptime(args.since, "%Y-%m-%d").replace(tzinfo=dt.timezone.utc).timestamp()
    until = args.until and dt.datetime.strptime(args.until, "%Y-%m-%d").replace(tzinfo=dt.timezone.utc).timestamp()
    pat = args.title_match and re.compile(args.title_match, re.I)
    out = []
    for it in items:
        ts = it["meta"]["timestamp"]
        if since and ts and ts < since:
            continue
        if until and ts and ts >= until + 86400:
            continue
        if pat and not pat.search(f"{it['meta'].get('title') or ''} {it['meta'].get('description') or ''}"):
            continue
        out.append(it)
    if len(items) > 1:
        log(f"[list] {url}: {len(items)} entries, {len(out)} after filters")
    return out


def local_item(path):
    path = os.path.abspath(path)
    base = os.path.splitext(os.path.basename(path))[0]
    return {"id": slug(base) + "-" + hashlib.md5(path.encode()).hexdigest()[:6], "url": None, "path": path,
            "meta": {"title": os.path.basename(path), "timestamp": os.path.getmtime(path)}}


def expand(inputs, args):
    items = []
    for inp in inputs:
        if inp.startswith("@") and os.path.isfile(inp[1:]):
            lines = [l.strip() for l in open(inp[1:], encoding="utf-8")]
            items += expand([l for l in lines if l and not l.startswith("#")], args)
        elif re.match(r"https?://", inp):
            try:
                items += expand_url(inp, args)
            except Exception as e:  # one blocked link should not sink the rest of the batch
                log(f"[skip] {e}")
                if "Sign in to confirm" in str(e) or "login" in str(e).lower():
                    log("       this site wants a signed-in session from this IP: export cookies.txt and pass --cookies")
        elif os.path.isdir(inp):
            for p in sorted(glob.glob(os.path.join(inp, "**", "*"), recursive=True)):
                if os.path.splitext(p)[1].lower() in MEDIA_EXT and ".transcribe-media" not in p.split(os.sep):
                    items.append(local_item(p))
        elif os.path.isfile(inp):
            items.append(local_item(inp))
        else:
            die(f"input not found: {inp}")
    seen, uniq = set(), []
    for it in items:
        if it["id"] not in seen:
            seen.add(it["id"])
            uniq.append(it)
    if args.limit:
        uniq = uniq[:args.limit]
    return uniq


# ---------------------------------------------------------------- download

def fetch(it, args, media_dir):
    """Return a local media path for the item (downloading URLs with yt-dlp)."""
    if it["path"]:
        return it["path"]
    found = [p for p in glob.glob(os.path.join(media_dir, it["id"] + ".*")) if not p.endswith(".part")]
    if found:
        return found[0]
    audio_only = args.engine in ("whisper", "elevenlabs") and not args.visual and not is_tiktok(it["url"])
    # TikTok's separate "audio" format is the background track, not the voice, so always take the muxed file.
    fmt = "ba/b" if audio_only else "b[height<=720]/bv*[height<=720]+ba/b"
    cmd = ytdlp_base(it["url"], args) + ["-q", "--no-playlist", "-f", fmt, "--merge-output-format", "mp4",
                                         "-o", os.path.join(media_dir, it["id"] + ".%(ext)s"),
                                         "-j", "--no-simulate", it["url"]]
    err = ""
    for attempt in range(3):
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)
        found = [p for p in glob.glob(os.path.join(media_dir, it["id"] + ".*")) if not p.endswith(".part")]
        if found:
            for line in r.stdout.splitlines():
                if line.startswith("{"):
                    fresh = item_from_info(json.loads(line), it["url"])["meta"]
                    it["meta"].update({k: v for k, v in fresh.items() if v not in (None, "")})
            return found[0]
        err = r.stderr.strip()[-400:]
        time.sleep(3 * (attempt + 1))
    raise RuntimeError(f"download failed: {err}")


# ---------------------------------------------------------------- engines

class WhisperEngine:
    def __init__(self, args):
        from faster_whisper import WhisperModel
        name = args.model or (WHISPER_FAST if args.fast else WHISPER_MODELS.get(args.lang, WHISPER_DEFAULT))
        log(f"[whisper] loading {name} (first run downloads it)")
        self.model = WhisperModel(name, device="cpu", compute_type="int8", cpu_threads=args.threads)
        self.name = name
        self.args = args

    def run(self, path):
        lang = None if self.args.lang == "auto" else self.args.lang
        segs, info = self.model.transcribe(path, language=lang, vad_filter=True,
                                           beam_size=1 if self.args.fast else 5,
                                           condition_on_previous_text=False)
        segments = [{"start": round(s.start, 2), "end": round(s.end, 2), "text": s.text.strip()} for s in segs]
        return {"engine": "whisper", "model": self.name, "language": info.language, "segments": segments}


def _multipart(fields, file_field, path, mime):
    boundary = uuid.uuid4().hex
    out = []
    for k, v in fields.items():
        out.append(f'--{boundary}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode())
    out.append(f'--{boundary}\r\nContent-Disposition: form-data; name="{file_field}"; '
               f'filename="{os.path.basename(path)}"\r\nContent-Type: {mime}\r\n\r\n'.encode())
    out.append(open(path, "rb").read())
    out.append(f"\r\n--{boundary}--\r\n".encode())
    return b"".join(out), f"multipart/form-data; boundary={boundary}"


def to_audio(path, tmp_dir):
    """Small mono mp3 for upload engines; falls back to the original file if ffmpeg is missing."""
    if not shutil.which("ffmpeg"):
        return path, False
    out = os.path.join(tmp_dir, slug(os.path.basename(path)) + f".{uuid.uuid4().hex[:6]}.mp3")
    r = subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", path, "-vn", "-ac", "1", "-ar", "16000",
                        "-b:a", "48k", out], capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"ffmpeg could not extract audio: {r.stderr.strip()[-300:]}")
    return out, True


def elevenlabs_run(path, args, tmp_dir):
    key = os.environ.get("ELEVENLABS_API_KEY")
    if not key:
        raise RuntimeError("ELEVENLABS_API_KEY is not set (needs the Speech-to-Text permission)")
    audio, made = to_audio(path, tmp_dir)
    try:
        fields = {"model_id": args.el_model, "diarize": "true", "tag_audio_events": "false",
                  "timestamps_granularity": "word"}
        if args.lang != "auto":
            fields["language_code"] = EL_LANG.get(args.lang, args.lang)
        body, ctype = _multipart(fields, "file", audio, MIME.get(os.path.splitext(audio)[1].lower(),
                                                                 "application/octet-stream"))
        req = urllib.request.Request("https://api.elevenlabs.io/v1/speech-to-text", data=body, method="POST",
                                     headers={"xi-api-key": key, "Content-Type": ctype})
        try:
            with urllib.request.urlopen(req, timeout=1800) as r:
                resp = json.load(r)
        except urllib.error.HTTPError as e:
            raise RuntimeError(f"ElevenLabs HTTP {e.code}: {e.read().decode(errors='replace')[:400]}")
    finally:
        if made and os.path.exists(audio):
            os.remove(audio)
    # Group words into subtitle-sized segments: break on speaker change, a pause > 0.8 s, the end of a
    # sentence once a few words are in, or a hard cap so a run-on sentence still splits.
    segments, cur = [], None
    for w in resp.get("words", []):
        if w.get("type") == "spacing":
            continue
        spk = w.get("speaker_id")
        gap = cur and w.get("start") is not None and w["start"] - cur["end"] > 0.8
        sentence_end = cur and len(cur["words"]) >= 4 and re.search(r"[.!?…]$", cur["words"][-1])
        clause_end = cur and len(cur["words"]) >= 14 and cur["words"][-1].endswith(",")
        if not cur or spk != cur["speaker"] or gap or sentence_end or clause_end or len(cur["words"]) >= 30:
            cur = {"start": w.get("start", 0), "end": w.get("end", 0), "speaker": spk, "words": []}
            segments.append(cur)
        cur["words"].append(w.get("text", ""))
        cur["end"] = w.get("end", cur["end"])
    segs = [{"start": round(s["start"], 2), "end": round(s["end"], 2), "speaker": s["speaker"],
             "text": " ".join(s["words"]).replace(" ,", ",").replace(" .", ".").strip()} for s in segments]
    if not segs and resp.get("text"):
        segs = [{"start": 0, "end": 0, "text": resp["text"].strip()}]
    return {"engine": "elevenlabs", "model": args.el_model, "language": resp.get("language_code"),
            "segments": segs}


def _json_from(text):
    text = text.strip()
    m = re.search(r"\{.*\}", text, re.S)
    return json.loads(m.group(0) if m else text)


def gemini_run(path, pool, visual_only=False):
    mime = MIME.get(os.path.splitext(path)[1].lower(), "video/mp4")
    part = gemini_pool.media_part(path, mime)
    prompt = GEMINI_VISUAL_PROMPT if visual_only else GEMINI_TRANSCRIBE_PROMPT
    model, text = pool.generate([part, {"text": prompt}], {"responseMimeType": "application/json"})
    data = _json_from(text)
    out = {"on_screen_text": data.get("on_screen_text") or [], "visual": data.get("visual") or "",
           "visual_model": model}
    if not visual_only:
        segs = []
        for s in data.get("segments") or []:
            try:
                segs.append({"start": float(s.get("start") or 0), "end": float(s.get("end") or 0),
                             "text": str(s.get("text", "")).strip()})
            except (TypeError, ValueError):
                segs.append({"start": 0, "end": 0, "text": str(s.get("text", "")).strip()})
        out.update(engine="gemini", model=model, language=data.get("language"), segments=segs)
    return out


# ---------------------------------------------------------------- output

def srt_time(t):
    t = max(0.0, float(t or 0))
    h, rem = divmod(int(t), 3600)
    m, s = divmod(rem, 60)
    return f"{h:02d}:{m:02d}:{s:02d},{int(round((t - int(t)) * 1000)) % 1000:03d}"


def fmt_date(ts):
    return dt.datetime.fromtimestamp(ts, dt.timezone.utc).strftime("%Y-%m-%d") if ts else "?"


def header_lines(rec):
    m = rec["meta"]
    lines = [f"source: {rec.get('url') or rec.get('path')}", f"date: {fmt_date(m.get('timestamp'))}"]
    for k in ("uploader", "duration", "view_count", "like_count"):
        if m.get(k) not in (None, ""):
            lines.append(f"{k}: {m[k]}")
    if m.get("description"):
        lines.append(f"caption: {m['description'].strip()}")
    lines.append(f"engine: {rec.get('engine')} ({rec.get('model')}), language: {rec.get('language')}")
    return lines


def multi_speaker(rec):
    return len({s.get("speaker") for s in rec.get("segments", []) if s.get("speaker")}) > 1


def rec_text(rec):
    return " ".join(s["text"] for s in rec.get("segments", []) if s.get("text")).strip()


def speaker_turns(rec):
    """'speaker: text' lines, merging consecutive segments of the same speaker."""
    turns = []
    for s in rec.get("segments", []):
        if not s.get("text"):
            continue
        if turns and turns[-1][0] == s.get("speaker"):
            turns[-1][1].append(s["text"])
        else:
            turns.append((s.get("speaker"), [s["text"]]))
    return "\n".join(f"{spk}: {' '.join(parts)}" for spk, parts in turns)


def write_outputs(rec, out_dir):
    base = os.path.join(out_dir, rec["id"])
    rec["text"] = rec_text(rec)
    with open(base + ".json", "w", encoding="utf-8") as f:
        json.dump(rec, f, ensure_ascii=False, indent=1)
    multi = multi_speaker(rec)
    body = header_lines(rec) + ["", (speaker_turns(rec) if multi else rec["text"]) or "(no speech detected)"]
    if rec.get("on_screen_text"):
        body += ["", "ON-SCREEN TEXT:"] + [f"- {t}" for t in rec["on_screen_text"]]
    if rec.get("visual"):
        body += ["", "VISUAL:", rec["visual"]]
    with open(base + ".txt", "w", encoding="utf-8") as f:
        f.write("\n".join(body) + "\n")
    timed = [s for s in rec.get("segments", []) if s.get("text") and (s.get("end") or 0) > 0]
    if timed:
        with open(base + ".srt", "w", encoding="utf-8") as f:
            for i, s in enumerate(timed, 1):
                spk = f"[{s['speaker']}] " if multi and s.get("speaker") else ""
                f.write(f"{i}\n{srt_time(s['start'])} --> {srt_time(s['end'])}\n{spk}{s['text']}\n\n")


def write_combined(recs, out_dir, pattern):
    recs = sorted(recs, key=lambda r: r["meta"].get("timestamp") or 0)
    def block(r):
        out = [f"## {fmt_date(r['meta'].get('timestamp'))} · {r['meta'].get('title') or r['id']}", ""]
        speech = speaker_turns(r) if multi_speaker(r) else r.get("text")
        out += [f"- {l}" for l in header_lines(r)] + ["", speech or "(no speech detected)"]
        if r.get("on_screen_text"):
            out += ["", "**On-screen text:** " + " | ".join(r["on_screen_text"])]
        if r.get("visual"):
            out += ["", "**Visual:** " + r["visual"]]
        return "\n".join(out) + "\n"
    with open(os.path.join(out_dir, "combined.md"), "w", encoding="utf-8") as f:
        f.write(f"# Transcripts ({len(recs)})\n\n" + "\n".join(block(r) for r in recs))
    if pattern:
        rx = re.compile(pattern, re.I)
        hits = [r for r in recs if rx.search(" ".join([r.get("text") or "", r["meta"].get("description") or "",
                                                        r["meta"].get("title") or "", r.get("visual") or "",
                                                        " ".join(r.get("on_screen_text") or [])]))]
        with open(os.path.join(out_dir, "matches.md"), "w", encoding="utf-8") as f:
            f.write(f"# Matches for /{pattern}/ ({len(hits)} of {len(recs)})\n\n" + "\n".join(block(r) for r in hits))
        log(f"[match] /{pattern}/: {len(hits)} of {len(recs)} items -> {os.path.join(out_dir, 'matches.md')}")


# ---------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("inputs", nargs="+", help="files, folders, URLs (video/profile/playlist) or @list.txt")
    ap.add_argument("--out", default="transcripts", help="output folder (default: ./transcripts)")
    ap.add_argument("--engine", choices=["whisper", "elevenlabs", "gemini"], default="whisper")
    ap.add_argument("--lang", default="auto", help="ISO 639-1 code (he, en, pt...) or auto. 'he' picks the "
                                                   "Hebrew-tuned Whisper model")
    ap.add_argument("--model", help="override the Whisper model (HF repo id or faster-whisper name)")
    ap.add_argument("--fast", action="store_true", help="Whisper small + greedy decoding (bulk screening)")
    ap.add_argument("--visual", action="store_true", help="add a Gemini pass for on-screen text and visuals")
    ap.add_argument("--match", help="regex; also write matches.md with items whose text/caption/visual match")
    ap.add_argument("--since", help="URL lists: only items on/after YYYY-MM-DD")
    ap.add_argument("--until", help="URL lists: only items on/before YYYY-MM-DD")
    ap.add_argument("--title-match", help="URL lists: regex on title/caption before downloading")
    ap.add_argument("--limit", type=int, help="process at most N items (after filters)")
    ap.add_argument("--keep-media", action="store_true", help="keep downloaded media in OUT/.transcribe-media")
    ap.add_argument("--force", action="store_true", help="redo items that already have output")
    ap.add_argument("--jobs", type=int, default=3, help="parallel downloads / API calls (default 3)")
    ap.add_argument("--threads", type=int, default=os.cpu_count() or 4, help="Whisper CPU threads")
    ap.add_argument("--cookies", help="cookies.txt for yt-dlp (Instagram / private content)")
    ap.add_argument("--el-model", default="scribe_v1", help="ElevenLabs model id (default scribe_v1)")
    ap.add_argument("--gemini-models", help="comma list overriding the Gemini model pool")
    args = ap.parse_args()

    if args.engine == "gemini" or args.visual:
        if not os.environ.get("GEMINI_API_KEY"):
            die("GEMINI_API_KEY is not set (needed for --engine gemini / --visual)")
    if args.engine == "elevenlabs" and not os.environ.get("ELEVENLABS_API_KEY"):
        die("ELEVENLABS_API_KEY is not set (needs the Speech-to-Text permission)")

    out_dir = os.path.abspath(args.out)
    media_dir = os.path.join(out_dir, ".transcribe-media")
    os.makedirs(media_dir, exist_ok=True)

    items = expand(args.inputs, args)
    if not items:
        die("nothing to transcribe")

    custom = args.gemini_models and args.gemini_models.split(",")
    full_pool = gemini_pool.Pool(custom or gemini_pool.FULL_MODELS + gemini_pool.LITE_MODELS)
    lite_pool = gemini_pool.Pool(custom or gemini_pool.LITE_MODELS + gemini_pool.FULL_MODELS)

    recs, todo = {}, []
    for it in items:
        jp = os.path.join(out_dir, it["id"] + ".json")
        if os.path.exists(jp) and not args.force:
            prev = json.load(open(jp, encoding="utf-8"))
            if args.visual and not prev.get("visual") and not prev.get("on_screen_text"):
                todo.append(it)  # speech exists, only the visual pass is missing
            else:
                recs[it["id"]] = prev
                continue
        else:
            todo.append(it)
    log(f"[plan] {len(items)} items: {len(recs)} already done, {len(todo)} to process "
        f"(engine={args.engine}{', +visual' if args.visual else ''}) -> {out_dir}")

    whisper = WhisperEngine(args) if args.engine == "whisper" and todo else None
    gate = threading.BoundedSemaphore(8)  # cap downloaded-but-unprocessed files on disk
    failed, gemini_out = [], threading.Event()

    def download(it):
        if not it["path"]:
            gate.acquire()
        try:
            return fetch(it, args, media_dir)
        except Exception:
            if not it["path"]:
                gate.release()
            raise

    def finish(it, path, rec):
        if rec is not None:
            write_outputs(rec, out_dir)
            recs[it["id"]] = rec
        if not it["path"]:
            if not args.keep_media and path and os.path.exists(path):
                os.remove(path)
            gate.release()

    def visual_pass(it, path, rec):
        try:
            if not gemini_out.is_set():
                rec.update(gemini_run(path, lite_pool, visual_only=True))
        except gemini_pool.Exhausted:
            gemini_out.set()
            log("[gemini] quota spent: remaining items keep speech only; rerun later with --visual to fill in")
        except Exception as e:
            log(f"[visual] {it['id']}: {e}")
        finish(it, path, rec)

    def api_item(it, path):
        try:
            jp = os.path.join(out_dir, it["id"] + ".json")
            if os.path.exists(jp) and not args.force:
                rec = json.load(open(jp, encoding="utf-8"))  # speech is done; only the visual pass is missing
            elif args.engine == "gemini":
                rec = gemini_run(path, full_pool)
            else:
                rec = elevenlabs_run(path, args, media_dir)
            if args.visual and not gemini_out.is_set() and not (rec.get("visual") or rec.get("on_screen_text")):
                try:
                    rec.update(gemini_run(path, lite_pool, visual_only=True))
                except gemini_pool.Exhausted:
                    gemini_out.set()
                    log("[gemini] quota spent: remaining items keep speech only; rerun later with --visual")
                except Exception as e:
                    log(f"[visual] {it['id']}: {e}")
            rec.update(id=it["id"], url=it["url"], path=it["path"], meta=it["meta"])
            finish(it, path, rec)
            log(f"[done] {it['id']} ({len(rec_text(rec))} chars)")
        except Exception as e:
            failed.append((it["id"], str(e)))
            log(f"[fail] {it['id']}: {e}")
            finish(it, path, None)

    t0 = time.time()
    with cf.ThreadPoolExecutor(args.jobs) as dl, cf.ThreadPoolExecutor(args.jobs) as api:
        futs = [(it, dl.submit(download, it)) for it in todo]
        pending = []
        for n, (it, fut) in enumerate(futs, 1):
            try:
                path = fut.result()
            except Exception as e:
                failed.append((it["id"], str(e)))
                log(f"[fail] {it['id']}: {e}")
                continue
            if args.engine == "whisper":
                jp = os.path.join(out_dir, it["id"] + ".json")
                try:
                    if os.path.exists(jp) and not args.force:
                        rec = json.load(open(jp, encoding="utf-8"))
                    else:
                        rec = whisper.run(path)
                        rec.update(id=it["id"], url=it["url"], path=it["path"], meta=it["meta"])
                    log(f"[{n}/{len(todo)}] {it['id']}: {len(rec_text(rec))} chars ({rec.get('language')})")
                except Exception as e:
                    failed.append((it["id"], str(e)))
                    log(f"[fail] {it['id']}: {e}")
                    finish(it, path, None)
                    continue
                if args.visual and not gemini_out.is_set():
                    write_outputs(rec, out_dir)  # speech is saved even if the visual pass fails later
                    pending.append(api.submit(visual_pass, it, path, rec))
                else:
                    finish(it, path, rec)
            else:
                pending.append(api.submit(api_item, it, path))
        cf.wait(pending)

    write_combined(list(recs.values()), out_dir, args.match)
    if not args.keep_media:
        shutil.rmtree(media_dir, ignore_errors=True)
    log(f"[summary] {len(recs)} transcribed, {len(failed)} failed, {time.time() - t0:.0f}s -> "
        f"{os.path.join(out_dir, 'combined.md')}")
    for vid, err in failed:
        log(f"  failed {vid}: {err[:200]}")
    sys.exit(1 if failed and not recs else 0)


if __name__ == "__main__":
    main()
