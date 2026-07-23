#!/usr/bin/env python3
"""Free keyless TikTok enrichment + transcripts for /last30days.

TikTok keyword *search* is locked behind paid scrapers (ScrapeCreators/Apify),
but yt-dlp can, for free:
  - pull full engagement data (views/likes/comments/reposts) from any video URL,
  - enumerate a creator's recent videos,
  - AND download the auto-generated CAPTIONS/subtitles (the spoken transcript).

So the free pipeline is:
  1. Discover TikTok video URLs / creator @handles via WebSearch (host model's
     own tool). General searches often surface /video/ URLs; domain-restricted
     ones surface /discover/ topic pages.
  2. Pipe those to this script -> engagement + (optionally) the transcript,
     ranked, plus an aggregate (average across many videos). With --transcripts,
     --match also searches the SPOKEN words, not just the caption — so you can
     find "what reta creators actually SAY about bloating," not just hashtags.

Usage:
  tiktok_free.py URL [URL ...]                  # enrich video URLs
  tiktok_free.py @creator [@creator ...]        # enumerate recent videos
  tiktok_free.py @a --transcripts               # also pull spoken transcript
  tiktok_free.py @a --transcripts --match bloating,gas   # match spoken words too
  tiktok_free.py @a --per 20 --stats-only       # aggregate only
  printf '%s\n' url1 @creator2 | tiktok_free.py -

Requires yt-dlp on PATH. Fully free/keyless.
"""
import sys, os, re, json, glob, tempfile, subprocess, statistics, concurrent.futures

PER_CREATOR = 12  # default recent videos to pull per creator


def _run(args, timeout=120):
    try:
        out = subprocess.run(["yt-dlp", "--no-warnings", *args],
                             capture_output=True, text=True, timeout=timeout)
        return out.stdout
    except Exception:
        return ""


def creator_video_urls(handle: str, limit: int) -> list[str]:
    """List a creator's recent video URLs (flat-playlist, cheap, no download).

    Prefers yt-dlp's own url/webpage_url so it tolerates handle redirects.
    """
    handle = handle.lstrip("@").strip().rstrip("/")
    if not handle:
        return []
    raw = _run(["--flat-playlist", "--dump-json", "--playlist-end", str(limit),
                f"https://www.tiktok.com/@{handle}"])
    urls = []
    for line in raw.splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            d = json.loads(line)
        except json.JSONDecodeError:
            continue
        u = d.get("url") or d.get("webpage_url")
        if not u and d.get("id"):
            u = f"https://www.tiktok.com/@{handle}/video/{d['id']}"
        if u:
            urls.append(u)
    return urls


def _clean_vtt(path: str) -> str:
    """Turn a .vtt subtitle file into a plain deduped transcript string."""
    try:
        txt = open(path, encoding="utf-8").read()
    except Exception:
        return ""
    lines = []
    for l in txt.splitlines():
        if ("-->" in l or l.strip().isdigit() or l.startswith(("WEBVTT", "Kind", "Language"))
                or not l.strip()):
            continue
        l = re.sub(r"<[^>]+>", "", l).strip()
        if l and (not lines or lines[-1] != l):
            lines.append(l)
    return " ".join(lines)


def fetch_transcript(url: str) -> str:
    """Download TikTok auto-captions for a video and return the plain text.

    Free: TikTok exposes eng-US auto-captions on many videos, which yt-dlp can
    write without downloading the video itself.
    """
    with tempfile.TemporaryDirectory() as tmp:
        out_tpl = os.path.join(tmp, "s.%(ext)s")
        _run(["--write-auto-subs", "--write-subs", "--sub-langs", "eng-US,en.*",
              "--sub-format", "vtt", "--skip-download", "-o", out_tpl, url], timeout=90)
        vtts = glob.glob(os.path.join(tmp, "*.vtt"))
        return _clean_vtt(vtts[0]) if vtts else ""


def enrich(url: str, want_transcript: bool = False) -> dict | None:
    url = url.strip()
    if not url or "tiktok.com" not in url:
        return None
    try:
        out = subprocess.run(
            ["yt-dlp", "--dump-json", "--skip-download", "--no-warnings", url],
            capture_output=True, text=True, timeout=90,
        )
        if out.returncode != 0 or not out.stdout.strip():
            return None
        d = json.loads(out.stdout)
    except Exception:
        return None
    item = {
        "url": d.get("webpage_url") or url,
        "creator": d.get("uploader") or d.get("uploader_id"),
        "title": d.get("title") or d.get("description"),
        "description": d.get("description"),
        "views": d.get("view_count") or 0,
        "likes": d.get("like_count") or 0,
        "comments": d.get("comment_count") or 0,
        "reposts": d.get("repost_count") or 0,
        "date": d.get("upload_date"),
        "transcript": "",
    }
    if want_transcript:
        item["transcript"] = fetch_transcript(item["url"])
    return item


def _pop_opt(args, name):
    if name in args:
        i = args.index(name)
        val = args[i + 1] if i + 1 < len(args) else None
        del args[i:i + 2]
        return val
    return None


def aggregate(items: list[dict]) -> dict:
    if not items:
        return {}
    v = [x["views"] for x in items]
    l = [x["likes"] for x in items]
    c = [x["comments"] for x in items]
    dates = sorted(x["date"] for x in items if x.get("date"))
    return {
        "videos": len(items),
        "creators": len({x["creator"] for x in items}),
        "avg_views": round(statistics.mean(v)), "median_views": round(statistics.median(v)),
        "avg_likes": round(statistics.mean(l)), "median_likes": round(statistics.median(l)),
        "avg_comments": round(statistics.mean(c)),
        "total_views": sum(v), "total_likes": sum(l),
        "date_from": dates[0] if dates else None, "date_to": dates[-1] if dates else None,
    }


def main() -> int:
    args = sys.argv[1:]
    stats_only = "--stats-only" in args
    if stats_only:
        args.remove("--stats-only")
    want_transcript = "--transcripts" in args
    if want_transcript:
        args.remove("--transcripts")
    per = int(_pop_opt(args, "--per") or PER_CREATOR)
    match_raw = _pop_opt(args, "--match")
    terms = [t.strip().lower() for t in match_raw.split(",")] if match_raw else []

    tokens = [l.strip() for l in sys.stdin if l.strip()] if (args == ["-"] or not args) else args

    urls, seen = [], set()
    for t in tokens:
        if "tiktok.com" in t and "/video/" in t:
            expanded = [t]
        elif "tiktok.com/@" in t:
            expanded = creator_video_urls(t.split("/@")[1].split("/")[0], per)
        else:
            expanded = creator_video_urls(t, per)
        for u in expanded:
            key = u.split("?")[0]
            if key not in seen:
                seen.add(key)
                urls.append(u)

    items = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as ex:
        for r in ex.map(lambda u: enrich(u, want_transcript), urls):
            if not r:
                continue
            if terms:
                # With transcripts, match the SPOKEN words too, not just the caption.
                hay = " ".join([r.get("description") or "", r.get("title") or "",
                                r.get("transcript") or ""]).lower()
                if not any(term in hay for term in terms):
                    continue
            items.append(r)
    items.sort(key=lambda x: x["views"] + x["likes"] * 3 + x["comments"] * 5, reverse=True)

    if not stats_only:
        print(json.dumps(items, ensure_ascii=False, indent=2))

    print(f"\n{len(items)}/{len(urls)} TikTok videos enriched"
          f"{' + transcripts' if want_transcript else ''} (free, keyless via yt-dlp):",
          file=sys.stderr)
    for it in items:
        line = (f"  @{it['creator']} | {it['views']:,}v {it['likes']:,}L {it['comments']:,}c "
                f"| {it['date']} | {(it['title'] or '')[:60]}")
        print(line, file=sys.stderr)
        if want_transcript and it.get("transcript"):
            print(f"      🗣 {it['transcript'][:160]}", file=sys.stderr)

    agg = aggregate(items)
    if agg:
        print("\n=== AGGREGATE (average across many videos) ===", file=sys.stderr)
        print(f"  {agg['videos']} videos from {agg['creators']} creators "
              f"| {agg['date_from']}–{agg['date_to']}", file=sys.stderr)
        print(f"  views:    avg {agg['avg_views']:,}  median {agg['median_views']:,}  "
              f"total {agg['total_views']:,}", file=sys.stderr)
        print(f"  likes:    avg {agg['avg_likes']:,}  median {agg['median_likes']:,}  "
              f"total {agg['total_likes']:,}", file=sys.stderr)
        print(f"  comments: avg {agg['avg_comments']:,}", file=sys.stderr)

    if stats_only:
        print(json.dumps(agg, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
