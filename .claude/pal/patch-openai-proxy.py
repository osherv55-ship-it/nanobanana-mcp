"""Idempotent patch: make PAL's OpenAI-compatible client honor HTTPS_PROXY.

PAL deliberately strips proxy env vars when building its httpx client, which
breaks it in managed egress environments (Claude Code on the web) where all
outbound traffic must go through HTTPS_PROXY. This re-injects the proxy
explicitly. Safe to run repeatedly; exits 0 if already applied.

Usage: python patch-openai-proxy.py /path/to/pal-mcp-server
"""

import sys
from pathlib import Path

pal_dir = Path(sys.argv[1])
target = pal_dir / "providers" / "openai_compatible.py"
src = target.read_text()

if "explicit_proxy" in src:
    print("proxy patch: already applied")
    sys.exit(0)

anchor = 'proxy_env_vars = ["HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "http_proxy", "https_proxy", "all_proxy"]'
capture = (
    anchor
    + "\n\n            # Managed egress environments require all outbound traffic to go"
    + "\n            # through HTTPS_PROXY — capture it before suppression and pass it"
    + "\n            # explicitly so the client still works there."
    + '\n            explicit_proxy = get_env("HTTPS_PROXY") or get_env("https_proxy")'
)

old_client = """                    else:
                        # Normal production client
                        http_client = httpx.Client(
                            timeout=timeout_config,
                            follow_redirects=True,
                        )"""
new_client = """                    else:
                        # Normal production client
                        client_args = {
                            "timeout": timeout_config,
                            "follow_redirects": True,
                        }
                        if explicit_proxy:
                            client_args["proxy"] = explicit_proxy
                        http_client = httpx.Client(**client_args)"""

if anchor not in src or old_client not in src:
    print("proxy patch: WARNING - upstream code changed, patch not applied", file=sys.stderr)
    sys.exit(1)

src = src.replace(anchor, capture, 1).replace(old_client, new_client, 1)
target.write_text(src)
print("proxy patch: applied")
