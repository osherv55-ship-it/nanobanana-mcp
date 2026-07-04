# מרכז הפפטידים להזרקה — דוח שבועי

A weekly Hebrew-language digest page that aggregates the social-media discourse
(TikTok / Instagram / Facebook) about **injectable peptides** — the processes people
report going through, the dramatic changes they describe, expert interpretation,
regulatory warnings, and the conclusions the community itself reaches.

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
2. Refresh, with live web search, each section:
   - **Trend table** — which injectable peptides trend now and on which platform; update
     volumes and regulatory-status pills.
   - **Experiences** — new transformation / recovery / regret stories and the timelines people report.
   - **Expert reality-check** — evidence level per category (GLP-1s, healing peptides,
     GH secretagogues, cosmetic/other); pull fresh expert quotes.
   - **Regulation** — new FDA / Health Canada / WADA / Israeli MoH actions on the timeline.
   - **Community conclusions** — pros, regrets, red flags.
   - **Israel angle** — Hebrew-community specifics.
   - **Sources** — replace with the URLs actually used this week.
3. Keep the medical disclaimer and the "no dosing" rule intact.
4. Re-publish the Artifact to the **same** URL (redeploy the same `file_path`) and commit the
   updated `index.html` to the working branch.

A scheduled trigger (Claude Code Remote routine) fires weekly with this brief.
