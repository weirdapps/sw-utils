<!-- MOVED HERE 2026-08-12 from ~/Downloads so it is not lost with the scratch dir.

     SCOPE: this spec covers TWO repos. Sections 5 and 6 are the sw-utils work that
     shipped as PR #23. Sections 4 and 7 describe a StockTwits sentiment source in
     plessas-trading-stack (PR #149) and are kept only because they carry the shared
     reasoning: the same Cloudflare and headless findings drove both designs.

     OUTCOME vs this spec, so nobody reads it as current truth:
       - Section 6 (Reddit board chatter) shipped as designed.
       - Section 5 (swgoh.gg meta) shipped PARTLY. The conversion is scripted and
         tested. The TRANSPORT is not: Cloudflare challenges every parameterised
         /gac/squads/ URL for a Playwright-launched browser, so the in-session MCP
         browser remains the only route. See CLAUDE.md step 3, which is authoritative.
       - Fleet meta from /gac/ship-counters/ was deferred and is still OPEN.
-->

# Design: market sentiment + SWGOH meta ingestion

Date: 2026-08-11
Scope: StockTwits, swgoh.gg, Reddit (SWGOH only). X is out of scope.
Repos touched: `plessas-trading-stack`, `sw-utils`. No shared code between them.

## 1. Goal

Replace a silently dead sentiment input in the investment committee, and automate two
manual SWGOH data steps. This work was scoped as the alternative to installing the
third-party Agent Reach framework, which was declined for this machine.

## 2. Verified access facts

All tested live on 2026-08-11 from the work Mac (egress 94.67.74.34) and, where noted,
from the Hetzner VPS (167.233.42.38). Both hosts behaved identically, so none of these
results are IP-reputation artefacts.

| Source | Plain HTTP client | Real browser | Auth | Notes |
|---|---|---|---|---|
| Reddit `.json` | 403 | 403 | OAuth required | Reddit's own block page, not Cloudflare |
| Reddit `.rss` | **200** | n/a | **none** | 25 live entries; throttled ~10 QPM unauth |
| StockTwits `api/2` | 403 Cloudflare | **200** | **none** | 30 msgs/page, `cursor.max` paginates |
| swgoh.gg `/api/` | 403 Cloudflare | **200** | **none** | 340 characters returned |
| swgoh.gg `/gac/` | 403 Cloudflare | renders | none | server-side HTML, no JSON XHR |

Two distinct 403 mechanisms, and the difference drives the architecture:

- **Cloudflare bot-detection** (StockTwits, swgoh.gg): a 5.7 KB "Just a moment" interstitial.
  A real browser engine passes it with no credentials. `requests` never will.
- **Reddit policy block** (`.json`): 190 KB of Reddit's own themed HTML. No browser trick
  helps; only OAuth. `.rss` was left open because it exposes a narrower surface.

## 3. Out of scope, and why

- **X / Twitter.** Dropped by owner decision. For the record: the tier ladder was replaced
  by pay-per-use on 2026-02-06, there is no free read tier, and reads bill per resource
  returned at roughly $0.005 each.
- **Reddit for market sentiment.** Superseded by StockTwits. The existing Reddit market
  path is removed, not repaired.
- **StockTwits terms of service.** `api/2/streams/*` is an undocumented internal endpoint
  and their self-serve developer programme is closed to new registrations. Driving a
  browser at it is automated access they have not sanctioned. This was flagged and the
  owner elected to proceed. Recorded here so the decision is not re-litigated later.

## 4. Deliverable A: StockTwits sentiment into the committee

Repo: `plessas-trading-stack`
File: `plugins/trading-hub/scripts/sentiment_analysis.py` (447 lines)

### 4.1 The defect being fixed

```python
resp = requests.get(url, headers=REDDIT_HEADERS, timeout=10)
if resp.status_code != 200:
    return []            # <- sentiment_analysis.py:101-102
```

A 403 returns an empty list with no log line. The `except` branch prints only on network
exceptions, never on a bad status. The Social Sentiment analyst has therefore been
reporting on Yahoo headlines alone, and a dead source is indistinguishable from neutral
sentiment in the committee output.

### 4.2 Changes

Remove: `fetch_reddit_posts()`, `fetch_all_reddit()`, `REDDIT_SUBREDDITS`,
`REDDIT_LIMIT`, `REDDIT_TIMEFRAME`, `REDDIT_DELAY`, `REDDIT_HEADERS`, and the Reddit
branch of `analyze_stock_sentiment()`.

Add: `fetch_stocktwits(ticker)` returning the same post-dict shape the Reddit fetcher
produced, so the downstream scoring and reporting code is unchanged in structure.

- Transport: local Playwright Chromium, **headed** (`headless=False`). The script must
  remain runnable standalone (`python3 sentiment_analysis.py`), so it drives its own
  browser rather than depending on the agent to pre-fetch via the MCP browser.

  **Correction, 2026-08-11, after implementation began.** This section originally claimed
  the approach stayed portable to an unattended VPS run. That is false. Cloudflare returns
  403 with an empty body to headless Chromium and to headless real Chrome alike; only a
  headed browser gets 200. Verified across all four combinations of {bundled chromium,
  channel=chrome} x {headless, headed}. The consequence, accepted by the owner: a visible
  browser window opens for the duration of the sentiment step, and the script cannot run
  unattended on macOS. The VPS path remains recoverable later via `xvfb-run`, which
  supplies a virtual display to a headed browser, but that is out of scope here.
- Endpoint: `https://api.stocktwits.com/api/2/streams/symbol/{TICKER}.json`
- Pagination: 30 messages per response. Fetch one page per ticker by default. Follow
  `cursor.max` for at most one additional page, and only when the first page yields fewer
  than `VOLUME_MEDIUM` (5), the existing threshold below which mention volume is already
  classified LOW. Hard cap of two pages per ticker.
- Reuse one browser context across all tickers in a run. Do not launch per ticker.

### 4.3 Scoring: hybrid (owner decision)

In the live sample, 12 of 30 messages carried `entities.sentiment.basic`
("Bullish" 10, "Bearish" 2) and 18 were untagged.

- Where `entities.sentiment.basic` is present, use it directly. It is the author's own
  stated position, not an inference. Map Bullish to +0.8 and Bearish to -0.8 on the same
  compound scale VADER produces, so `vader_to_score()` and `classify_view()` are reused
  without modification.

  The magnitude is deliberate. Mapping to the full +/-1.0 would place every declared
  label at the extreme of the scale, where VADER compounds on real text almost never
  reach, so declared messages would dominate any blended average purely as an artefact of
  scale rather than as an intentional weighting. +/-0.8 keeps declared labels stronger
  than typical inferred scores without saturating the range. This value is a starting
  point to calibrate against real output, not a derived constant.
- Where it is absent, score `body` with VADER as today.
- Report the split (declared vs inferred) in the per-stock output so the proportion of
  inferred signal is visible rather than hidden.

Weighting: equal weight with recency preference. Do **not** weight by follower count;
it is gameable and heavily skewed. A `likes` field was not confirmed present in the
payload, so no engagement-based weighting is to be assumed without verifying it first.

### 4.4 Coverage and failure semantics

StockTwits is cashtag-based and US-centric. International tickers such as `0700.HK` and
`NOVO-B.CO` will not resolve. These must be reported as **"no coverage"**, which is a
distinct state from **"neutral sentiment"** and must not contribute a 50/100 score to
any aggregate.

Failure semantics, the point of the exercise:

| Condition | Behaviour |
|---|---|
| Cloudflare challenge or non-200 | Log an explicit error naming the ticker and status; mark the ticker `SOURCE_FAILED` |
| Symbol resolves but zero messages | Mark `NO_COVERAGE`; do not score |
| All tickers fail | Exit non-zero. A totally dead source must not produce a clean-looking report |

## 5. Deliverable B: swgoh.gg meta scrape, scripted

Repo: `sw-utils`
New file: `scripts/fetch_meta.py`

`scripts/browser_recipes.md` §3 already documents a working recipe, including the
non-obvious part:

> the base `/gac/squads/` passes, but PARAM URLs get JS-challenged. chrome-devtools
> can't solve it; Playwright MCP passes IF you navigate the base page first (warm
> session) then the param URL.

The script automates exactly that recipe with local Playwright. It must:

- Warm the session on `/gac/squads/` before requesting any parameterised URL.
- Fetch the four documented views: 5v5 defense, 5v5 offense, latest 3v3 defense,
  latest 3v3 offense, using the `?season_id=...SEASON_<n>` grammar (even = 5v5,
  odd = 3v3), `?perspective=attack` for offense, `?sort=percent`.
- Fetch fleet meta from `/gac/ship-counters/`.
- Write into `data/meta/` in the **existing** formats so `compute_teams.py` and
  `swgoh_meta.py` need no change: the 5v5 defense file as JSON with
  `rows[].hold/seen/banners/units`, the others as the `rate%|seen|banners|CSVunits`
  line format.
- Take the season id as an argument rather than inferring it. Season detection is a
  separate concern and inferring it wrongly silently corrupts the board.

Verification: parsed output must round-trip through `swgoh_meta.py` and produce the same
record shape as the shipped `meta_5v5_defense_s80.json` and `meta_def3v3.txt`.

## 6. Deliverable C: Reddit SWGOH signal in the daily brief

Repo: `sw-utils`
New file: `scripts/reddit_swgoh.py`
Integration: new section in `scripts/daily_brief.py`, which already reserves space for
pluggable sections.

- Source: `https://www.reddit.com/r/SWGalaxyOfHeroes/hot/.rss?limit=25`
- Auth: none (owner decision). Requires a descriptive User-Agent, which Reddit's own
  docs mandate. Use `sw-utils-brief/1.0 (personal use)`.
- Rate: unauthenticated feeds throttle at roughly 10 QPM and return 429 when exceeded.
  One or two feed pulls per day is comfortably inside that. Retry once on 429 after a
  short sleep; do not hammer.
- Available fields: title, link, author, updated timestamp, HTML content.
  **Not** available: score, upvote ratio, comment count, comment bodies. Any ranking
  must therefore be by recency or keyword match, never by popularity.

### 6.1 The framing that makes this useful

Do not surface "what r/SWGalaxyOfHeroes is discussing". Surface **"what it is saying
about units on my board"**. Cross-reference entry titles against the unit names and base
IDs already available via `swgoh_data`, restricted to units present in
`data/gac_result.json`. A post about a unit currently sitting on the GAC defense board is
a signal the board may be going stale; a post about anything else is noise.

Unmatched entries are dropped, not shown. If the matcher yields nothing, the section
renders as "no board-relevant chatter" rather than being omitted, so a broken matcher is
visible rather than silent. This is the same principle as section 4.4.

## 7. Cross-cutting decisions

**No shared library.** The Playwright boilerplate is roughly 30 lines and is duplicated
in `plessas-trading-stack` and `sw-utils` rather than extracted. Coupling a private
trading monorepo to a private game repo for a helper that small is a worse trade than the
duplication. Each repo stays independently runnable and deployable.

**Local Playwright, not the MCP browser.** Per the browser-tooling rule, MCP browsers are
for interactive sessions and standalone Playwright for anything that must run on its own.
These scripts must run standalone, including under a future timer, so they own their
browser. Confirmed: the VPS already has `ms-playwright` and Chromium if that ever moves.

**Confirm Playwright is a declared dependency** in each repo before implementation.
It is present on the VPS but its presence in either project's dependency manifest has not
been verified.

## 8. Testing

TDD per the repo convention: tests first, then implementation.

- Capture real fixtures now, while access works: one StockTwits symbol response, one
  swgoh.gg GAC squads page, one Reddit RSS feed. Commit them as test fixtures.
- Parsers are pure functions over fixture text and are tested directly with no network
  and no browser.
- The browser transport layer is mocked in unit tests. One optional integration test per
  source, skipped by default, exercises real network.
- Explicit regression test for the defect in section 4.1: a non-200 response must raise
  or log an error, and must never yield a silent empty result.

## 9. Risks

| Risk | Likelihood | Mitigation |
|---|---|---|
| StockTwits closes the undocumented endpoint | Medium | Loud failure per 4.4 means it surfaces immediately rather than degrading silently |
| Reddit closes `.rss` as it closed `.json` | Medium | Fetcher isolated behind one function; OAuth swap is a single-file change |
| swgoh.gg changes GAC table markup | Medium | Parser tested against a committed fixture; failure is loud |
| Cloudflare hardens against headless Chromium | Medium | Recipe already documents the warm-session workaround; if it stops working the manual browser path in `browser_recipes.md` still exists as fallback |
| VADER misreads finance slang on the untagged 60% | High | Declared/inferred split reported per 4.3 so the proportion of weak signal is visible |

## 10. Done criteria

1. `sentiment_analysis.py` returns real StockTwits data for US tickers and reports
   `NO_COVERAGE` for non-US ones, with no path that silently returns empty.
2. A 403 from any source produces a visible error and a non-zero exit when total.
3. `scripts/fetch_meta.py` regenerates the four `data/meta/` files, and
   `compute_teams.py` runs against them unmodified.
4. `daily_brief.py` renders a board-relevant Reddit section, or an explicit
   "no board-relevant chatter" line.
5. Tests pass, including the silent-403 regression test.

## Note on location

Written to `~/Downloads` rather than either repo, because it spans two repos and neither
owns it. `~/Downloads` is not a git repository, so this document is not committed.
