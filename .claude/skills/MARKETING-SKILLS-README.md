# Marketing Skills (vendored)

47 marketing skills vendored from [coreyhaines31/marketingskills](https://github.com/coreyhaines31/marketingskills) (MIT, see `MARKETING-SKILLS-LICENSE`).

Covers: copywriting, ad creative, paid ads, CRO, SEO, emails, social, video, offers,
pricing, marketing psychology, competitor research, and more.

## How they work together

`product-marketing` is the foundation skill — every other skill reads it first to
understand the product, audience, and positioning. For this business that context is:
**marketing for aesthetic-medicine clinics in Israel (Hebrew-first)** — before/after
content, doctor testimonial videos, Meta + Google Ads campaigns.

Most relevant skills for this business: `ad-creative`, `ads`, `copywriting`, `social`,
`video`, `marketing-psychology`, `offers`, `competitor-profiling`, `content-strategy`.

To update to a newer upstream version: re-clone the repo and re-copy `skills/*` here.

# Paid-Ads Audit Suite (vendored)

The `paid-ads` orchestrator + 22 `ads-*` sub-skills + 10 agents in `.claude/agents/`
are vendored from [AgriciDaniel/claude-ads](https://github.com/AgriciDaniel/claude-ads)
(MIT, see `paid-ads/LICENSE`). The upstream orchestrator was named `ads`; it is
renamed `paid-ads` here to avoid colliding with the Corey Haines `ads` strategy
skill. Sub-skills keep their upstream `ads-*` names, and upstream docs referring
to `/ads <cmd>` correspond to `/paid-ads <cmd>` in this repo.

Entry points: `/paid-ads audit` (full parallel audit), `/paid-ads google`,
`/paid-ads meta`, `ads-math` (no API needed), `ads-generate` / `ads-photoshoot`
(use this repo's own nanobanana MCP for ad imagery).
