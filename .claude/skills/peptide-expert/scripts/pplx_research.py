#!/usr/bin/env python3
"""
Perplexity research runner for the peptide-expert skill.

Reads PERPLEXITY_API_KEY from (in order):
  1. env var PERPLEXITY_API_KEY
  2. ~/.config/last30days/.env  (the same key last30days uses)

Usage:
  python3 pplx_research.py --model sonar-deep-research --prompt-file /path/to/prompt.txt
  echo "your question" | python3 pplx_research.py --model sonar-pro
  python3 pplx_research.py --model sonar-pro --prompt "one-line question"

Models:
  sonar-pro            fast, cited, good for protocols / dosing / focused Qs  (~$0.005-0.02)
  sonar-deep-research  slow (2-6 min), 30-40 searches, best for MECHANISM      (~$0.3-0.6)
  sonar                cheapest, quick facts

Output: the answer text, then a ===SOURCES=== block with citations,
then a ===USAGE=== line with token cost. Save the text and synthesize it
per SKILL.md — never dump it verbatim.
"""
import os, sys, json, argparse, urllib.request, pathlib


def load_key() -> str:
    k = os.environ.get("PERPLEXITY_API_KEY")
    if k:
        return k.strip()
    env = pathlib.Path.home() / ".config" / "last30days" / ".env"
    if env.exists():
        for line in env.read_text().splitlines():
            if line.startswith("PERPLEXITY_API_KEY="):
                return line.split("=", 1)[1].strip()
    sys.exit("ERROR: PERPLEXITY_API_KEY not found (env or ~/.config/last30days/.env). "
             "See SKILL.md setup.")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="sonar-pro",
                    choices=["sonar", "sonar-pro", "sonar-deep-research", "sonar-reasoning-pro"])
    ap.add_argument("--prompt", help="inline prompt text")
    ap.add_argument("--prompt-file", help="read prompt from a file")
    ap.add_argument("--timeout", type=int, default=560)
    ap.add_argument("--out", help="also write raw answer text to this file")
    args = ap.parse_args()

    if args.prompt_file:
        prompt = pathlib.Path(args.prompt_file).read_text()
    elif args.prompt:
        prompt = args.prompt
    else:
        prompt = sys.stdin.read()
    if not prompt.strip():
        sys.exit("ERROR: empty prompt.")

    body = json.dumps({
        "model": args.model,
        "messages": [{"role": "user", "content": prompt}],
    }).encode()
    req = urllib.request.Request(
        "https://api.perplexity.ai/chat/completions",
        data=body,
        headers={"Authorization": f"Bearer {load_key()}",
                 "Content-Type": "application/json"},
    )
    try:
        resp = urllib.request.urlopen(req, timeout=args.timeout)
        d = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        sys.exit(f"ERROR HTTP {e.code}: {e.read().decode()[:400]}")

    content = d["choices"][0]["message"]["content"]
    print(content)
    if args.out:
        pathlib.Path(args.out).write_text(content)

    cites = d.get("citations", [])
    if cites:
        print("\n===SOURCES===")
        for i, c in enumerate(cites[:40], 1):
            print(f"[{i}] {c}")

    u = d.get("usage", {})
    cost = (u.get("cost") or {}).get("total_cost")
    print(f"\n===USAGE=== model={args.model} "
          f"searches={u.get('num_search_queries', '?')} "
          f"total_tokens={u.get('total_tokens', '?')} "
          f"cost=${cost if cost is not None else '?'}")


if __name__ == "__main__":
    main()
