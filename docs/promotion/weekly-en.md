# Weekly MCP Red/Black List · English template (ongoing rhythm)

> Same cadence as the Chinese weekly (see `weekly-zh.md`): every Monday after the auto-refresh, fill in 【】from https://trustlens.icodestar.net/en/ and post to X / Dev.to / Reddit / LinkedIn (pick one or two — don't spam all four).
> Verify numbers against the live leaderboard before posting.

## Template

**Title:**
This week's MCP leaderboard: 【N】new servers, 【X】grade F

**Body:**

TrustLens re-runs 112+ real MCP servers weekly, zero credentials, 90s handshake. This week's refresh (data as of 【date】):

**Green list (actually usable):**
1. 【server】 — 【score】/100 — 【one line: e.g. "clean docs, handshake in <1s"】
2. 【server】 — 【score】/100 — 【one line】
3. 【server】 — 【score】/100 — 【one line】

**Red list (failed the boot test):**
1. 【server】 — 【score】/100 — 【failure mode: e.g. "crashes on missing API key"】
2. 【server】 — 【score】/100 — 【failure mode】
3. 【server】 — 【score】/100 — 【failure mode】

**One-liner take:**
【e.g. "Half of this week's new entries are still F — the ecosystem is still wild."】

Full leaderboard (bilingual, searchable, weekly CI update): https://trustlens.icodestar.net/en/
Repo (Apache-2.0, all data public): https://github.com/hyqzz/trustlens

Want us to deep-check a specific category next week? Name it in the comments.

**Hashtags (X/LinkedIn):** #MCP #AI #LLM #OpenSource

## Channel notes

- **X**: post the 3+3 list as one tweet; quote-reply the most interesting entry with a link to its detail page
- **Dev.to**: can become a short "Weekly MCP Watch" series (same title prefix each week → build a series)
- **Reddit**: only r/mcp, once every 2–3 weeks (don't be the spammer)
- **LinkedIn**: reuse L1-style framing but keep it shorter
- Keep the failure mode honest (audited from stderr) — that's what makes this trustworthy instead of "bashing"

## Notes

- Green list ≠ just high scores; feature servers that are actually being used and hold up in re-tests — it builds "we really use this" credibility
- Red list must always state the audited failure mode, never just "bad"
- One week's content can derive: X thread + Dev.to short + LinkedIn post
