# רטטרוטייד (Reta) — דוח שבועי בסושיאל

A weekly Hebrew-language digest page focused specifically on **retatrutide**
(Eli Lilly's investigational "Triple-G" triple-agonist) and everything published
about it on social media that week — **good and bad**: the dramatic trial efficacy
people are excited about, the personal experiences on TikTok/Reddit/Facebook, the
gray-market danger, harms/hospitalizations, expert interpretation, the regulatory
timeline, and the conclusions the community reaches.

> Scope note: the user narrowed this page from "all injectable peptides" to
> **retatrutide only** — approved GLP-1s (Ozempic/Wegovy/Mounjaro) were removed.

The page is public-health / harm-reduction oriented: it summarizes what is being said
online and cross-checks it against medical evidence and regulators. It is **not** medical
advice and contains **no dosing or usage instructions**.

## Files

- `index.html` — the standalone page (RTL Hebrew, dark/light, self-contained; opens in any
  browser and imports cleanly as a Claude Artifact — no external assets).

## How it is generated

A multi-model agent run assembles the page:

- **Claude** — orchestration, synthesis, page authoring.
- **Live web search** — trending peptides, view/post counts, news, studies, regulator actions.
- **Gemini / GPT (via PAL `clink` / `chat`)** — optional "expert interpretation" second opinion,
  used when the CLIs are installed and API quota is available. If unavailable, Claude produces
  the section from the researched sources (as it did for the first edition).

## Weekly refresh — brief for the agent

Re-run once per week and regenerate `index.html`. Steps:

1. Update the header week range and the "updated weekly" / date chips.
2. Refresh, with live web search, each section (all focused on **retatrutide**):
   - **הצד הטוב** — latest trial efficacy (TRIUMPH / TRANSCEND readouts) as a dose-response
     chart of *clinical-trial* results; the "food noise gone" / stall-breaker buzz.
   - **בסושיאל השבוע** — new TikTok/Reddit/Facebook experiences, good and bad, with the
     side-effect pattern people report (racing heart, insomnia, "wiped out", etc.).
   - **הצד המסוכן** — fresh harms: hospitalizations, liver failures, deaths, poison-center
     numbers, gray-market vendor/clinic counts, FDA warning-letter status.
   - **פרשנות מומחים** — reality-check quotes (e.g. authenticity "likely not retatrutide", liver flags).
   - **ציר הזמן** — new trial results vs. regulatory/enforcement/harm events.
   - **מסקנות** — pros vs. concerns · **בישראל** — MoH status, fraud warnings.
   - **מקורות** — replace with the URLs actually used this week.

   Keep it retatrutide-only unless the user says otherwise. Efficacy figures are
   controlled-trial results, framed as such — **never** a usage/dosing protocol.
3. Keep the medical disclaimer and the "no dosing" rule intact.
4. Re-publish the Artifact to the **same** URL (redeploy the same `file_path`) and commit the
   updated `index.html` to the working branch.

A scheduled trigger (Claude Code Remote routine) fires weekly with this brief.
