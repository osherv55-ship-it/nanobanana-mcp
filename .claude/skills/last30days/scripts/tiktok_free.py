#!/usr/bin/env python3
"""Free keyless TikTok enrichment for /last30days.

TikTok keyword *search* is locked behind paid scrapers (ScrapeCreators/Apify).
But yt-dlp can pull full engagement data from any *known* TikTok video URL for
free. So the free pipeline is:

  1. Discover TikTok URLs via WebSearch (the hosting model's own tool).
  2. Pipe those URLs to this script -> real view/like/comment/repost data.

Usage:
  tiktok_free.py URL [URL ...]              # enrich specific video URLs
  tiktok_free.py @creator [@creator ...]    # enumerate a creator's recent videos
  printf '%s\n' url1 @creator2 | tiktok_free.py -

Accepts video URLs, @handles, or bare creator names. For creators it lists
recent videos (via yt-dlp --flat-playlist), optionally filtered by --match
keyword against the caption. Outputs a JSON array ranked by engagement plus a
human-readable table on stderr. Requires yt-dlp on PATH. Fully free/keyless.
"""
import sys, json, subprocess, concurrent.futures

PER_CREATOR = 12  # how many recent videos to pull per creator


def _run_json(args, timeout=120):
    try:
        out = subprocess.run(["yt-dlp", "--no-warnings", *args],
                             capture_output=True, text=True, timeout=timeout)
        return out.stdout
    except Exception:
        return ""


def creator_video_urls(handle: str, limit: int = PER_CREATOR) -> list[str]:
    """List a creator's recent video URLs via flat-playlist (cheap, no download)."""
    handle = handle.lstrip("@").strip()
    if not handle:
        return []
    raw = _run_json(["--flat-playlist", "--dump-json", "--playlist-end", str(limit),
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


def enrich(url: str) -> dict | None:
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
    except (subprocess.TimeoutExpired, json.JSONDecodeError, Exception):
        return None
    return {
        "url": url,
        "creator": d.get("uploader") or d.get("uploader_id"),
        "title": d.get("title") or d.get("description"),
        "description": d.get("description"),
        "views": d.get("view_count") or 0,
        "likes": d.get("like_count") or 0,
        "comments": d.get("comment_count") or 0,
        "reposts": d.get("repost_count") or 0,
        "date": d.get("upload_date"),
    }


def main() -> int:
    args = sys.argv[1:]
    match = None
    if "--match" in args:
        i = args.index("--match")
        match = args[i + 1].lower()
        del args[i:i + 2]
    if args == ["-"] or not args:
        tokens = [l.strip() for l in sys.stdin if l.strip()]
    else:
        tokens = args
    # Expand @handles / bare creator names into their recent video URLs.
    urls = []
    for t in tokens:
        if "tiktok.com" in t and "/video/" in t:
            urls.append(t)
        elif "tiktok.com/@" in t:  # profile URL
            urls.extend(creator_video_urls(t.split("/@")[1].split("/")[0]))
        else:  # @handle or bare name
            urls.extend(creator_video_urls(t))
    items = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as ex:
        for r in ex.map(enrich, urls):
            if r:
                if match and match not in ((r.get("description") or "") + (r.get("title") or "")).lower():
                    continue
                items.append(r)
    items.sort(key=lambda x: x["views"] + x["likes"] * 3 + x["comments"] * 5, reverse=True)
    print(json.dumps(items, ensure_ascii=False, indent=2))
    # Human-readable table to stderr
    print(f"\n{len(items)}/{len(urls)} TikTok videos enriched (free, keyless via yt-dlp):", file=sys.stderr)
    for it in items:
        print(f"  @{it['creator']} | {it['views']:,}v {it['likes']:,}L {it['comments']:,}c "
              f"| {it['date']} | {(it['title'] or '')[:70]}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
