#!/usr/bin/env python3
"""Free keyless TikTok enrichment for /last30days.

TikTok keyword *search* is locked behind paid scrapers (ScrapeCreators/Apify).
But yt-dlp can pull full engagement data from any *known* TikTok video URL, and
can enumerate a creator's recent videos, for free. So the free pipeline is:

  1. Discover TikTok URLs / creator @handles via WebSearch (the host model's
     own tool). General web searches often surface individual /video/ URLs;
     domain-restricted ones surface /discover/ pages (topic aggregators).
  2. Pipe those URLs and/or @handles to this script -> real view/like/comment/
     repost data, ranked, PLUS an aggregate (average across all videos).

Usage:
  tiktok_free.py URL [URL ...]                 # enrich specific video URLs
  tiktok_free.py @creator [@creator ...]       # enumerate a creator's recent videos
  tiktok_free.py @a @b --match kpv,tesa        # keep only captions matching ANY term
  tiktok_free.py @a --per 20                   # pull 20 recent videos per creator
  tiktok_free.py @a --stats-only               # print only the aggregate, no per-video JSON
  printf '%s\n' url1 @creator2 | tiktok_free.py -

Accepts video URLs, profile URLs, @handles, or bare creator names. Outputs a
JSON array ranked by engagement on stdout, plus a per-video table AND an
aggregate summary (count, average/median/total views-likes-comments, date span)
on stderr. Requires yt-dlp on PATH. Fully free/keyless.
"""
import sys, json, subprocess, statistics, concurrent.futures

PER_CREATOR = 12  # default recent videos to pull per creator


def _run(args, timeout=120):
    try:
        out = subprocess.run(["yt-dlp", "--no-warnings", *args],
                             capture_output=True, text=True, timeout=timeout)
        return out.stdout
    except Exception:
        return ""


def creator_video_urls(handle: str, limit: int) -> list[str]:
    """List a creator's recent video URLs via flat-playlist (cheap, no download).

    Tolerates handle redirects (e.g. an old handle that now resolves to a new
    one) because we prefer yt-dlp's own url/webpage_url over reconstructing it.
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
    except Exception:
        return None
    return {
        "url": d.get("webpage_url") or url,
        "creator": d.get("uploader") or d.get("uploader_id"),
        "title": d.get("title") or d.get("description"),
        "description": d.get("description"),
        "views": d.get("view_count") or 0,
        "likes": d.get("like_count") or 0,
        "comments": d.get("comment_count") or 0,
        "reposts": d.get("repost_count") or 0,
        "date": d.get("upload_date"),
    }


def _pop_opt(args, name):
    """Pop `--name value` from args, returning value or None."""
    if name in args:
        i = args.index(name)
        val = args[i + 1] if i + 1 < len(args) else None
        del args[i:i + 2]
        return val
    return None


def aggregate(items: list[dict]) -> dict:
    """Compute the average-across-many-videos summary the report cares about."""
    if not items:
        return {}
    v = [x["views"] for x in items]
    l = [x["likes"] for x in items]
    c = [x["comments"] for x in items]
    dates = sorted(x["date"] for x in items if x.get("date"))
    return {
        "videos": len(items),
        "creators": len({x["creator"] for x in items}),
        "avg_views": round(statistics.mean(v)),
        "median_views": round(statistics.median(v)),
        "avg_likes": round(statistics.mean(l)),
        "median_likes": round(statistics.median(l)),
        "avg_comments": round(statistics.mean(c)),
        "total_views": sum(v),
        "total_likes": sum(l),
        "date_from": dates[0] if dates else None,
        "date_to": dates[-1] if dates else None,
    }


def main() -> int:
    args = sys.argv[1:]
    stats_only = False
    if "--stats-only" in args:
        stats_only = True
        args.remove("--stats-only")
    per = int(_pop_opt(args, "--per") or PER_CREATOR)
    match_raw = _pop_opt(args, "--match")
    # Comma-separated -> match ANY term (OR).
    terms = [t.strip().lower() for t in match_raw.split(",")] if match_raw else []

    if args == ["-"] or not args:
        tokens = [l.strip() for l in sys.stdin if l.strip()]
    else:
        tokens = args

    # Expand @handles / bare creator names into their recent video URLs; keep
    # explicit /video/ URLs as-is. De-dupe while preserving order.
    urls, seen = [], set()
    for t in tokens:
        expanded = []
        if "tiktok.com" in t and "/video/" in t:
            expanded = [t]
        elif "tiktok.com/@" in t:  # profile URL
            expanded = creator_video_urls(t.split("/@")[1].split("/")[0], per)
        else:  # @handle or bare name
            expanded = creator_video_urls(t, per)
        for u in expanded:
            key = u.split("?")[0]
            if key not in seen:
                seen.add(key)
                urls.append(u)

    items = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as ex:
        for r in ex.map(enrich, urls):
            if not r:
                continue
            if terms:
                hay = ((r.get("description") or "") + " " + (r.get("title") or "")).lower()
                if not any(term in hay for term in terms):
                    continue
            items.append(r)
    items.sort(key=lambda x: x["views"] + x["likes"] * 3 + x["comments"] * 5, reverse=True)

    agg = aggregate(items)
    if not stats_only:
        print(json.dumps(items, ensure_ascii=False, indent=2))

    # Per-video table
    print(f"\n{len(items)}/{len(urls)} TikTok videos enriched (free, keyless via yt-dlp):",
          file=sys.stderr)
    for it in items:
        print(f"  @{it['creator']} | {it['views']:,}v {it['likes']:,}L {it['comments']:,}c "
              f"| {it['date']} | {(it['title'] or '')[:70]}", file=sys.stderr)

    # Aggregate summary — the "average across many videos" view.
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
