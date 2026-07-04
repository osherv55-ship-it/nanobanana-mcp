---
name: aesthetics-academy-tracker
description: >
  Recurring competitive-intelligence agent that tracks leading aesthetic-medicine
  academies and injector-educators in Israel and worldwide, finds their
  high-traffic / viral posts, and produces a Hebrew marketing report with links,
  engagement notes, and fresh content ideas for promoting the user's academy.
  Use whenever the user asks for "דוח מעקב", "מה חדש אצל המתחרים", "רעיונות תוכן
  לאקדמיה", or when the weekly tracker routine fires.
---

# Aesthetics Academy Tracker

## Purpose

Track the social accounts on the watchlist (`watchlist.json`), surface the posts
with the highest traffic/engagement since the last run, and turn them into
actionable, innovative content ideas for promoting the user's aesthetic-medicine
academy. The deliverable of every run is a **Hebrew report** committed to
`reports/aesthetics-tracker/` in this repo.

## Inputs

- `watchlist.json` (next to this file) — the tracked accounts, split into
  `israel` and `global`, plus `trend_queries` (search phrases) and `hashtags`.
  Keep it alive: every run may add newly-discovered strong accounts and prune
  dead ones (note additions/removals in the report).
- Previous reports in `reports/aesthetics-tracker/` — read the most recent one
  so you never repeat the same links/ideas two runs in a row.

## Workflow (every run)

1. **Load context.** Read `watchlist.json` and the latest report in
   `reports/aesthetics-tracker/` (if any).

2. **Sweep for high-traffic posts.** Fan out parallel research agents
   (WebSearch/WebFetch) across these angles — Instagram/TikTok can't be scraped
   directly, so hunt via search engines, Google News, YouTube, press coverage
   of viral posts, and each account's site/blog:
   - Per-region sweep: recent standout posts/reels from the `israel` list and
     from the `global` list (search `site:instagram.com <handle>`, the account
     name + "viral"/"reel", YouTube channel uploads, news mentions).
   - Trend sweep: run the `trend_queries` and `hashtags` from the watchlist for
     posts/articles from the last ~14 days.
   - Newsjacking sweep: regulatory approvals (FDA/EMA), new products (toxins,
     fillers, exosomes, polynucleotides), congress news (IMCAS, AMWC, DASIL),
     Israeli health-ministry news relevant to aesthetics training.
   Collect only items with a working URL. Prefer items with visible engagement
   signals (view counts, "went viral" coverage, high comment counts).

3. **Cross-check with connected marketing tools when available.**
   - `Motion_Creative_Analytics` `get_inspo_creatives` / `get_inspo_brand_context`
     for competitor Meta creatives.
   - `PIPEBOARD` Instagram/Facebook tools (`get_instagram_posts`,
     `get_facebook_posts`) for the user's own accounts as a baseline.
   Skip silently if a connector is unavailable in the session.

4. **Multi-model idea generation.** Feed the collected findings to the PAL MCP
   server and generate promotion ideas with more than one model — e.g.
   `mcp__pal__consensus` (or `mcp__pal__chat` / `mcp__pal__clink` with Gemini and
   Codex) with a prompt like: "Given these viral aesthetic-medicine posts,
   propose innovative, practical content ideas for an Israeli aesthetic-medicine
   academy — adapted to Hebrew-speaking audience, Instagram-first." Merge the
   best ideas from all models; attribute is not needed, quality is. If PAL is
   unavailable, generate the ideas yourself and say so in the report.

5. **Write the report** to
   `reports/aesthetics-tracker/YYYY-MM-DD.md` (run date), **in Hebrew**, using
   the template below. Every claim about a post must carry its link. Rank items
   by expected value to the academy, not by date.

6. **Feed page (user's preferred delivery).** Besides the markdown report,
   build `reports/aesthetics-tracker/YYYY-MM-DD-feed.html` — an RTL Hebrew
   dashboard where every surfaced post is a clickable card (region + platform
   filters, direct post links, newsjacking list, ranked ideas). Use the
   previous feed file as the template. When running interactively, publish it
   with the Artifact tool so the user gets a live link.

7. **Persist.** `git add` the report + feed page (+ any watchlist changes),
   commit with a descriptive message, and push to the session's working branch
   (never `main`).

8. **Deliver.** Post a short Hebrew summary of the top 3-5 findings and ideas
   in the conversation, with links, and mention the report path.

## Report template (Hebrew)

```markdown
# דוח מעקב אקדמיות רפואה אסתטית — YYYY-MM-DD

## 🔥 הפרסומים החמים של התקופה
| # | חשבון | פלטפורמה | קישור | למה זה עבד | רלוונטיות לאקדמיה |
(5–10 שורות, ממוינות לפי ערך)

## 🇮🇱 ישראל — מה המתחרים עשו
(סעיף קצר לכל חשבון ישראלי עם פעילות בולטת + קישורים)

## 🌍 עולם — טרנדים ופורמטים
(פורמטים עולים, האשטגים, נושאים חמים — עם דוגמאות מקושרות)

## 📰 ניוזג'קינג — חדשות לרכוב עליהן
(אישורים רגולטוריים, מוצרים חדשים, כנסים — ורעיון פוסט לכל אחת)

## 💡 רעיונות תוכן לאקדמיה (מסונתז מכמה מודלים)
(5–10 רעיונות קונקרטיים: פורמט, hook, קריאייטיב, CTA)

## 🗂 עדכוני רשימת מעקב
(חשבונות שנוספו/הוסרו והסיבה; "אין שינוי" אם אין)
```

## Scheduling (weekly routine)

**Active scheduler:** `.github/workflows/aesthetics-tracker.yml` — a GitHub
Actions workflow (Sunday ~06:23 UTC) that runs Claude Code with this skill and
pushes the report to a `claude/aesthetics-tracker-run-<date>` branch. It
requires the `CLAUDE_CODE_OAUTH_TOKEN` repository secret (generate with
`claude setup-token` locally, then add under repo Settings → Secrets and
variables → Actions). It can also be fired manually from the Actions tab
(workflow_dispatch).

Alternative scheduler (if the MCP approval flow is available in-session): a
Claude Code Remote trigger via `create_trigger` on the claude-code-remote MCP
server — in past sessions this call was blocked by a platform-level approval
that never surfaced, so the GitHub Action is the default. Config if created:

- **name:** `Aesthetics Academy Tracker — weekly`
- **cron_expression:** `23 6 * * 0` (Sunday ~06:23 UTC ≈ 09:23 Israel)
- **create_new_session_on_fire:** `true`
- **notifications:** `{"push": true, "email": true}`
- **prompt:** a standalone Hebrew instruction to read this SKILL.md and run
  the full workflow above, committing the report to a fresh
  `claude/aesthetics-tracker-run-<date>` branch and ending with a Hebrew
  summary of the top findings + links.

Verify with `list_triggers` before creating — don't duplicate.

## Quality bar

- No link — no item. Never invent URLs or engagement numbers.
- Don't repeat links or ideas from the previous report; build on them instead.
- 5–10 ideas per run, each concrete enough to shoot this week.
- Hebrew for the report body; account handles and hashtags stay in original
  language.
