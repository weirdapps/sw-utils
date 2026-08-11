<!-- MOVED HERE 2026-08-12 from ~/Downloads so it is not lost with the scratch dir.
     Executed as PR #23 (merged). Read the outcome notes below BEFORE the plan body.

     WHAT SHIPPED AS WRITTEN: Tasks 1-4. Reddit RSS reader, the board-unit matcher,
     the daily-brief chatter section, and rows_to_json.

     WHAT DID NOT: Task 5's premise. The plan assumes fetch_meta.py can drive the
     scrape itself. It cannot. Verified 2026-08-12 across bundled Chromium and real
     Chrome, headed and headless, fresh contexts and a persistent profile: Cloudflare
     challenges EVERY parameterised /gac/squads/ URL. Only the in-session MCP browser
     gets through, in about 15 seconds. main() is kept for the day that changes.
     CLAUDE.md step 3 is the authoritative instruction, not this plan.

     CORRECTIONS ALREADY FOLDED INTO THE BODY BELOW (they were wrong in the first draft):
       - season_id needs the full CHAMPIONSHIPS_GRAND_ARENA_GA2_EVENT_SEASON_<n> prefix;
         the bare form 404s BEHIND the Cloudflare interstitial, so it reads as a block.
       - headless=False is mandatory.
       - The JSON reader is swgoh_meta.parse_json_def, not parse_json.

     A LATER BUG NOT IN THIS PLAN: match_entries shipped with \b{name}\b, which can
     never fire for a name ending in ) or ". That hid 17 of 137 board units. Fixed with
     (?<!\w)...(?!\w). If you touch the regex, its purpose is that Rey must not fire on
     Greyjoy.

     STILL OPEN: fleet meta from /gac/ship-counters/.
-->

# SWGOH Meta Automation and Reddit Board Chatter Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Automate the manual swgoh.gg GAC meta export, and add a Reddit section to the daily brief that surfaces only chatter about units on the current GAC board.

**Architecture:** Two independent scripts in `sw-utils/scripts/`, following the repo's existing flat-module pattern. `fetch_meta.py` automates the browser recipe already documented in `scripts/browser_recipes.md` §3, writing the same file formats `compute_teams.py` already reads, so no consumer changes. `reddit_swgoh.py` reads the public Reddit RSS feed and filters entries against the units in `data/gac_result.json`, feeding a new section into `daily_brief.brief_sections()`.

**Tech Stack:** Python 3, Playwright (sync API), pytest.

**Spec:** `~/Downloads/202608111925_sentiment_swgoh_ingestion_design.md` sections 5, 6, 7, 8.

## Global Constraints

- Repo is clean on `master` as of 2026-08-11. Work on a branch.
- Tests import scripts flat (`import daily_brief`), because `tests/conftest.py` puts `scripts/` on `sys.path`. Follow that; do not add package `__init__.py` files.
- Test style in this repo: plain pytest functions named `test_<thing>_<behaviour>`, no classes. Fixtures live in `tests/fixtures/`.
- `requirements-dev.txt` states floors only, never ceilings, and pulls in `farmbot/requirements.txt`. Two dependencies are needed: `playwright` (Task 5) and `defusedxml` (Task 1). Check whether either already resolves through `farmbot/requirements.txt` before adding a floor line.
- Parse network XML with `defusedxml`, never `xml.etree.ElementTree`. Stdlib ElementTree does not expand external entities, so XXE is not the exposure, but it is vulnerable to entity-expansion DoS on hostile input.
- Reddit requires a descriptive User-Agent per its own documentation. Use `sw-utils-brief/1.0 (personal use)`.
- Unauthenticated Reddit feeds throttle around 10 QPM and return 429 when exceeded. One retry after a sleep, never a tight loop.
- **Season ids carry a prefix.** `browser_recipes.md` §3 writes the URL grammar as
  `?season_id=...SEASON_<n>`, and that leading `...` is literal shorthand, not decoration.
  The real value is `CHAMPIONSHIPS_GRAND_ARENA_GA2_EVENT_SEASON_<n>`. Passing the bare
  `SEASON_80` returns a **404**, which arrives behind a Cloudflare interstitial and so
  looks like a block. Verified live 2026-08-11.
- **Current seasons, verified live 2026-08-11:** season **81** is running (odd, so 3v3) and
  season **80** is the last complete 5v5 (even). The shipped `meta_5v5_defense_s80.json`
  is season 80 and has 31 rows, which matches what the site returns today.
- **`headless=False` is mandatory.** Verified against swgoh.gg: headless Chromium gets 403
  on the base page AND the param page; headed gets 200 on the base page. This is the same
  finding as the StockTwits work in the sibling plan, and it is a property of headless
  mode, not of the site. Do not attempt stealth plugins or user-agent spoofing.
- **Cloudflare's interstitial clears on its own.** A param URL can answer 403 with
  "Just a moment..." and then resolve a few seconds later. Wait for the real content
  rather than treating the first status as final; see Task 5.
- Exact meta file formats, verified 2026-08-11:
  - JSON: `{"season", "format", "perspective", "pulled", "rows": [{"hold": "57%", "seen": "29.8K", "banners": "25.21", "units": ["STRANGER", ...]}]}`
  - TXT: one line per squad, `rate%|seen|banners|CSV,of,baseIds`, e.g. `32%|34.9K|36.35|GLREY,BENSOLO,LUMINARAUNDULI`

## File Structure

| File | Responsibility |
|---|---|
| `scripts/reddit_swgoh.py` (create) | Fetch and parse the subreddit RSS feed; match entries to board units |
| `scripts/fetch_meta.py` (create) | Drive the browser through the §3 recipe; convert and write `data/meta/` files |
| `scripts/daily_brief.py` (modify) | Add the chatter section to `brief_sections()` and both renderers |
| `tests/test_reddit_swgoh.py` (create) | Parser and matcher tests |
| `tests/test_fetch_meta.py` (create) | Row-format conversion tests |
| `tests/test_daily_brief.py` (modify) | Section assembly test for chatter |
| `tests/fixtures/reddit_swgoh.rss` (create) | Real captured feed |
| `tests/fixtures/gac_rows_5v5_def.txt` (create) | Real captured extractor output |

---

### Task 1: Reddit RSS parsing

**Files:**
- Create: `scripts/reddit_swgoh.py`
- Create: `tests/test_reddit_swgoh.py`
- Create: `tests/fixtures/reddit_swgoh.rss`

**Interfaces:**
- Consumes: nothing
- Produces: `parse_feed(xml: str) -> list[dict]`, each entry `{"title": str, "link": str, "updated": str, "author": str}`. Titles are HTML-unescaped, so `&quot;` becomes `"`.

- [ ] **Step 1: Create the branch**

```bash
cd ~/SourceCode/sw-utils
git checkout -b feat/meta-automation-and-reddit
```

- [ ] **Step 2: Capture the fixture**

```bash
cd ~/SourceCode/sw-utils
curl -sS -m 20 -A 'sw-utils-brief/1.0 (personal use)' \
  "https://www.reddit.com/r/SWGalaxyOfHeroes/hot/.rss?limit=25" \
  -o tests/fixtures/reddit_swgoh.rss
grep -c '<entry>' tests/fixtures/reddit_swgoh.rss
```

Expected: `25`. If it prints `0` or the file contains an error page, you were rate limited. Wait 60 seconds and retry once. If it still fails, Reddit has closed RSS as it closed `.json`; stop and report.

- [ ] **Step 3: Write the failing tests**

```python
"""Tests for the r/SWGalaxyOfHeroes board-chatter signal (scripts/reddit_swgoh.py)."""
import os

import reddit_swgoh

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")


def _feed():
    with open(os.path.join(FIXTURES, "reddit_swgoh.rss"), encoding="utf-8") as fh:
        return fh.read()


def test_parse_feed_returns_all_entries():
    entries = reddit_swgoh.parse_feed(_feed())
    assert len(entries) == 25
    assert all(e["title"] and e["link"] for e in entries)


def test_parse_feed_unescapes_html_entities():
    xml = (
        '<feed xmlns="http://www.w3.org/2005/Atom"><entry>'
        "<title>The &amp;quot;Guardians&amp;quot; problem</title>"
        '<link href="https://example.com/x"/>'
        "<updated>2026-08-11T10:00:00+00:00</updated>"
        "<author><name>/u/someone</name></author>"
        "</entry></feed>"
    )
    entries = reddit_swgoh.parse_feed(xml)
    assert entries[0]["title"] == 'The "Guardians" problem'


def test_parse_feed_on_empty_document_returns_empty_list():
    assert reddit_swgoh.parse_feed('<feed xmlns="http://www.w3.org/2005/Atom"/>') == []
```

- [ ] **Step 4: Install defusedxml and run tests to verify they fail**

```bash
cd ~/SourceCode/sw-utils
python3 -c "import defusedxml; print(defusedxml.__version__)" 2>&1 || python3 -m pip install defusedxml
grep -n defusedxml requirements-dev.txt farmbot/requirements.txt
```

If it is not already resolved through `farmbot/requirements.txt`, add a `defusedxml` floor line to `requirements-dev.txt`.

Run: `cd ~/SourceCode/sw-utils && python3 -m pytest tests/test_reddit_swgoh.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'reddit_swgoh'`

- [ ] **Step 5: Implement**

Create `scripts/reddit_swgoh.py`:

```python
#!/usr/bin/env python3
"""reddit_swgoh.py - board-relevant chatter from r/SWGalaxyOfHeroes.

Reads the public Atom feed. No OAuth: Reddit closed unauthenticated .json in
May 2026 but left .rss open. The trade is that RSS carries no score and no
comment counts, so entries can be ranked by recency and relevance only, never
by popularity.

Usage:  python3 scripts/reddit_swgoh.py
"""
import html
import time
import urllib.request

# defusedxml, not xml.etree: stdlib ElementTree does not expand external
# entities (so XXE is not the concern) but it is vulnerable to entity-expansion
# DoS. This parses bytes off the network, so use the hardened parser.
from defusedxml import ElementTree as ET

FEED_URL = "https://www.reddit.com/r/SWGalaxyOfHeroes/hot/.rss?limit=25"
USER_AGENT = "sw-utils-brief/1.0 (personal use)"
ATOM = "{http://www.w3.org/2005/Atom}"
RETRY_SLEEP = 30


def parse_feed(xml_text):
    """Parse an Atom feed into [{"title","link","updated","author"}]."""
    root = ET.fromstring(xml_text)
    entries = []
    for entry in root.findall(f"{ATOM}entry"):
        title_el = entry.find(f"{ATOM}title")
        link_el = entry.find(f"{ATOM}link")
        updated_el = entry.find(f"{ATOM}updated")
        author_el = entry.find(f"{ATOM}author/{ATOM}name")
        title = html.unescape((title_el.text or "").strip()) if title_el is not None else ""
        entries.append(
            {
                "title": title,
                "link": link_el.get("href", "") if link_el is not None else "",
                "updated": (updated_el.text or "")[:10] if updated_el is not None else "",
                "author": (author_el.text or "") if author_el is not None else "",
            }
        )
    return entries


def fetch_feed(url=FEED_URL):
    """Fetch the feed. Retries once on 429, which is the unauth throttle."""
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        if exc.code != 429:
            raise
        time.sleep(RETRY_SLEEP)
        with urllib.request.urlopen(req, timeout=20) as resp:
            return resp.read().decode("utf-8", errors="replace")
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `cd ~/SourceCode/sw-utils && python3 -m pytest tests/test_reddit_swgoh.py -v`
Expected: 3 passed

- [ ] **Step 7: Commit**

```bash
cd ~/SourceCode/sw-utils
git add scripts/reddit_swgoh.py tests/test_reddit_swgoh.py tests/fixtures/reddit_swgoh.rss requirements-dev.txt
git commit -m "feat: parse r/SWGalaxyOfHeroes RSS feed"
```

---

### Task 2: Match chatter to units on the board

This is what makes the section worth reading. A post about a unit sitting on the GAC defense board is a signal the board may be going stale. A post about anything else is noise and is dropped.

**Files:**
- Modify: `scripts/reddit_swgoh.py`
- Modify: `tests/test_reddit_swgoh.py`

**Interfaces:**
- Consumes: `parse_feed` (Task 1); `data/name_type_map.json`, a dict of `base_id -> {"ct": int, "n": "Display Name"}` with 829 entries; `data/gac_result.json`, shaped `{"5v5": {"defense": [{"units": [base_id, ...]}], "offense": [...]}, "3v3": {...}}`
- Produces:
  - `board_units(gac_result: dict) -> set[str]` returning every base id on the board across both formats and both perspectives
  - `match_entries(entries: list[dict], units: set[str], name_map: dict) -> list[dict]`, each result being the entry plus `{"units": [base_id, ...]}`, with non-matching entries dropped

- [ ] **Step 1: Write the failing tests**

```python
NAME_MAP = {
    "GLREY": {"ct": 1, "n": "Rey"},
    "BENSOLO": {"ct": 1, "n": "Ben Solo"},
    "LORDVADER": {"ct": 1, "n": "Lord Vader"},
    "HONDO": {"ct": 1, "n": "Hondo Ohnaka"},
}


def test_board_units_collects_both_formats_and_perspectives():
    gac = {
        "5v5": {"defense": [{"units": ["GLREY", "BENSOLO"]}], "offense": [{"units": ["LORDVADER"]}]},
        "3v3": {"defense": [{"units": ["GLREY"]}], "offense": []},
    }
    assert reddit_swgoh.board_units(gac) == {"GLREY", "BENSOLO", "LORDVADER"}


def test_board_units_of_empty_result_is_empty():
    assert reddit_swgoh.board_units({}) == set()


def test_match_keeps_only_posts_naming_a_board_unit():
    entries = [
        {"title": "Lord Vader is still unkillable", "link": "a", "updated": "", "author": ""},
        {"title": "Best cantina farming route", "link": "b", "updated": "", "author": ""},
    ]
    out = reddit_swgoh.match_entries(entries, {"LORDVADER"}, NAME_MAP)
    assert len(out) == 1
    assert out[0]["units"] == ["LORDVADER"]


def test_match_ignores_units_not_on_the_board():
    entries = [{"title": "Why is Hondo Ohnaka a Galactic Legend?", "link": "a", "updated": "", "author": ""}]
    assert reddit_swgoh.match_entries(entries, {"LORDVADER"}, NAME_MAP) == []


def test_match_is_case_insensitive():
    entries = [{"title": "lord vader counters?", "link": "a", "updated": "", "author": ""}]
    out = reddit_swgoh.match_entries(entries, {"LORDVADER"}, NAME_MAP)
    assert len(out) == 1


def test_match_respects_word_boundaries():
    """'Rey' must not match inside 'Greyjoy' or 'Reyna'."""
    entries = [{"title": "Greyjoy tier list", "link": "a", "updated": "", "author": ""}]
    assert reddit_swgoh.match_entries(entries, {"GLREY"}, NAME_MAP) == []


def test_match_reports_every_board_unit_in_one_title():
    entries = [{"title": "Rey vs Ben Solo, who wins", "link": "a", "updated": "", "author": ""}]
    out = reddit_swgoh.match_entries(entries, {"GLREY", "BENSOLO"}, NAME_MAP)
    assert sorted(out[0]["units"]) == ["BENSOLO", "GLREY"]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd ~/SourceCode/sw-utils && python3 -m pytest tests/test_reddit_swgoh.py -v -k "board_units or match"`
Expected: FAIL with `AttributeError: module 'reddit_swgoh' has no attribute 'board_units'`

- [ ] **Step 3: Implement**

Add to `scripts/reddit_swgoh.py`:

```python
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GAC_RESULT = os.path.join(ROOT, "data", "gac_result.json")
NAME_MAP_FILE = os.path.join(ROOT, "data", "name_type_map.json")


def board_units(gac_result):
    """Every base id currently placed on the board, both formats, both sides."""
    units = set()
    for fmt in gac_result.values():
        for perspective in ("defense", "offense"):
            for squad in fmt.get(perspective, []):
                units.update(squad.get("units", []))
    return units


def match_entries(entries, units, name_map):
    """Keep only entries naming a board unit; annotate with the ids matched.

    Matching is on the display name with word boundaries, so 'Rey' does not fire
    on 'Greyjoy'. Entries naming no board unit are dropped rather than ranked
    low: the section is about the board, not about the subreddit.
    """
    patterns = []
    for base_id in units:
        display = (name_map.get(base_id) or {}).get("n")
        if not display:
            continue
        patterns.append((base_id, re.compile(rf"\b{re.escape(display)}\b", re.IGNORECASE)))

    matched = []
    for entry in entries:
        hits = [base_id for base_id, pattern in patterns if pattern.search(entry["title"])]
        if hits:
            item = dict(entry)
            item["units"] = sorted(hits)
            matched.append(item)
    return matched


def load_board_chatter(feed_xml=None, gac_path=GAC_RESULT, name_map_path=NAME_MAP_FILE):
    """End to end: feed plus board plus names -> board-relevant entries."""
    xml_text = feed_xml if feed_xml is not None else fetch_feed()
    with open(gac_path) as fh:
        gac = json.load(fh)
    with open(name_map_path) as fh:
        name_map = json.load(fh)
    return match_entries(parse_feed(xml_text), board_units(gac), name_map)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd ~/SourceCode/sw-utils && python3 -m pytest tests/test_reddit_swgoh.py -v`
Expected: 10 passed

- [ ] **Step 5: Sanity check against the real board**

```bash
cd ~/SourceCode/sw-utils
python3 -c "
import sys; sys.path.insert(0, 'scripts')
import reddit_swgoh
out = reddit_swgoh.load_board_chatter(open('tests/fixtures/reddit_swgoh.rss').read())
print(f'{len(out)} board-relevant of 25')
for e in out: print(' -', e['units'], e['title'][:70])
"
```

Expected: a small number, plausibly 0 to 5. Zero is a valid result for one snapshot of the feed and does not mean the matcher is broken; confirm by temporarily printing `board_units()` and checking a few names appear in `name_type_map.json`.

- [ ] **Step 6: Commit**

```bash
cd ~/SourceCode/sw-utils
git add scripts/reddit_swgoh.py tests/test_reddit_swgoh.py
git commit -m "feat: filter subreddit chatter to units on the current GAC board"
```

---

### Task 3: Surface chatter in the daily brief

**Files:**
- Modify: `scripts/daily_brief.py`
- Modify: `tests/test_daily_brief.py`

**Interfaces:**
- Consumes: `load_board_chatter()` (Task 2)
- Produces: `brief_sections()` gains a keyword argument `chatter=None` and returns a `"chatter"` key. Both renderers display it.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_daily_brief.py`:

```python
def test_brief_sections_includes_chatter():
    chatter = [
        {"title": "Lord Vader counters", "link": "https://x", "updated": "2026-08-11",
         "author": "/u/a", "units": ["LORDVADER"]},
    ]
    s = daily_brief.brief_sections({}, [], chatter=chatter)
    assert len(s["chatter"]) == 1
    assert s["chatter"][0]["units"] == ["LORDVADER"]


def test_brief_sections_chatter_defaults_to_empty():
    s = daily_brief.brief_sections({}, [])
    assert s["chatter"] == []
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd ~/SourceCode/sw-utils && python3 -m pytest tests/test_daily_brief.py -v -k chatter`
Expected: FAIL with `TypeError: brief_sections() got an unexpected keyword argument 'chatter'`

- [ ] **Step 3: Implement**

In `scripts/daily_brief.py`, change the signature:

```python
def brief_sections(gac_result, farm_ranked, events_list=None, relic_list=None, top_n=8,
                   chatter=None):
```

and the return at lines 42 to 43:

```python
    return {"board": board, "farm": farm_ranked[:top_n],
            "events": events_list or [], "relic": relic_list or [],
            "chatter": chatter or []}
```

In the terminal renderer, after the `relic` block that ends around line 74, add:

```python
    print("\nBoard chatter (r/SWGalaxyOfHeroes)")
    if sections.get("chatter"):
        for e in sections["chatter"][:6]:
            print(f"  [{','.join(e['units'])}] {e['title'][:70]}")
    else:
        print("  no board-relevant chatter")
```

In the HTML renderer, after the `relic` loop that ends around line 98, add the equivalent block. Match the surrounding markup style in that function rather than inventing new markup.

The empty case prints an explicit line rather than omitting the section. A silently missing section is indistinguishable from a broken matcher, which is the same failure mode this whole piece of work exists to remove.

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd ~/SourceCode/sw-utils && python3 -m pytest tests/test_daily_brief.py -v`
Expected: all pass, including the pre-existing tests

- [ ] **Step 5: Wire the real call into main**

Find where `daily_brief.py` builds its sections for the real run and pass the chatter in, guarding on network failure so a Reddit outage cannot break the whole brief:

```python
    try:
        chatter = reddit_swgoh.load_board_chatter()
    except Exception as exc:  # network, throttle, or feed removed
        print(f"  (chatter unavailable: {exc})")
        chatter = []
```

Add `import reddit_swgoh` alongside the existing `import advisor`, `import events`, `import swgoh_data`.

- [ ] **Step 6: Run the brief end to end**

Run: `cd ~/SourceCode/sw-utils && python3 scripts/daily_brief.py`
Expected: the brief renders with a "Board chatter" section, either with entries or the explicit no-chatter line. Confirm `output/brief_<date>.html` also contains it.

- [ ] **Step 7: Commit**

```bash
cd ~/SourceCode/sw-utils
git add scripts/daily_brief.py tests/test_daily_brief.py
git commit -m "feat: board chatter section in the daily brief"
```

---

### Task 4: Convert extractor output to the meta file formats

The browser recipe in `browser_recipes.md` §3 already produces `rate%|seen|banners|CSVunits` lines. Python's job is converting those to the two on-disk formats. That conversion is the testable part; the JS extractor is proven and stays as documented.

**Files:**
- Create: `scripts/fetch_meta.py`
- Create: `tests/test_fetch_meta.py`
- Create: `tests/fixtures/gac_rows_5v5_def.txt`

**Interfaces:**
- Consumes: nothing
- Produces:
  - `rows_to_json(text: str, season: str, fmt: str, perspective: str, pulled: str) -> dict` producing `{"season", "format", "perspective", "pulled", "rows": [{"hold", "seen", "banners", "units"}]}`
  - `EXTRACT_JS: str`, the extractor from `browser_recipes.md` §3, verbatim

- [ ] **Step 1: Create the fixture**

Create `tests/fixtures/gac_rows_5v5_def.txt` with real lines copied from `data/meta/meta_def3v3.txt`, which is already in the exact output format:

```
32%|34.9K|36.35|GLREY,BENSOLO,LUMINARAUNDULI
31%|70.4K|37.83|LORDVADER,APPO,OPERATIVE
31%|7,837|38.3|JANGOFETT,4LOM,ASAJJDARKDISCIPLE
```

Note the third line's `seen` value contains a comma inside a number. Splitting must be on `|` only, never on `,` for the first three fields.

- [ ] **Step 2: Write the failing tests**

```python
"""Tests for swgoh.gg GAC meta conversion (scripts/fetch_meta.py)."""
import os

import fetch_meta
import swgoh_meta

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")


def _rows_text():
    with open(os.path.join(FIXTURES, "gac_rows_5v5_def.txt")) as fh:
        return fh.read()


def test_rows_to_json_builds_the_expected_envelope():
    out = fetch_meta.rows_to_json(_rows_text(), "SEASON_80", "5v5", "defense", "2026-08-11")
    assert out["season"] == "SEASON_80"
    assert out["format"] == "5v5"
    assert out["perspective"] == "defense"
    assert out["pulled"] == "2026-08-11"
    assert len(out["rows"]) == 3


def test_rows_to_json_row_shape_matches_the_shipped_file():
    out = fetch_meta.rows_to_json(_rows_text(), "SEASON_80", "5v5", "defense", "2026-08-11")
    row = out["rows"][0]
    assert set(row) == {"hold", "seen", "banners", "units"}
    assert row["hold"] == "32%"
    assert row["seen"] == "34.9K"
    assert row["banners"] == "36.35"
    assert row["units"] == ["GLREY", "BENSOLO", "LUMINARAUNDULI"]


def test_rows_to_json_preserves_commas_inside_seen_counts():
    out = fetch_meta.rows_to_json(_rows_text(), "S", "5v5", "defense", "d")
    assert out["rows"][2]["seen"] == "7,837"
    assert out["rows"][2]["units"] == ["JANGOFETT", "4LOM", "ASAJJDARKDISCIPLE"]


def test_rows_to_json_skips_blank_lines():
    out = fetch_meta.rows_to_json("\n\n32%|1K|2|A,B\n\n", "S", "5v5", "defense", "d")
    assert len(out["rows"]) == 1


def test_output_round_trips_through_the_existing_parser(tmp_path):
    """The whole point of matching the format: swgoh_meta must read it unchanged."""
    import json

    out = fetch_meta.rows_to_json(_rows_text(), "SEASON_80", "5v5", "defense", "2026-08-11")
    path = tmp_path / "meta.json"
    path.write_text(json.dumps(out))
    parsed = swgoh_meta.parse_json_def(str(path))
    assert len(parsed) == 3
```

The JSON reader is `parse_json_def` (verified: `swgoh_meta.py` exposes `seen_num`, `parse_txt`, `parse_json_def`, `load_meta`). Inspect what `parse_json_def` returns before asserting on it, and assert on the real shape rather than assuming a list of three.

- [ ] **Step 3: Run tests to verify they fail**

Run: `cd ~/SourceCode/sw-utils && python3 -m pytest tests/test_fetch_meta.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'fetch_meta'`

- [ ] **Step 4: Implement**

Create `scripts/fetch_meta.py`:

```python
#!/usr/bin/env python3
"""fetch_meta.py - pull swgoh.gg GAC meta into data/meta/.

Automates browser_recipes.md §3. Two things there are load-bearing and are
reproduced exactly:
  - swgoh.gg is behind Cloudflare, so a real browser engine is required.
  - Parameterised URLs get JS-challenged unless the base /gac/squads/ page is
    loaded first to warm the session.

The season id is an argument, not inferred. Guessing it wrong silently writes a
different season's meta into the board inputs.

Usage:  python3 scripts/fetch_meta.py --season 80
"""
import json
import os

BASE = "https://swgoh.gg/gac/squads/"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
META_DIR = os.path.join(ROOT, "data", "meta")

# Verbatim from browser_recipes.md §3. Returns one line per squad:
#   rate%|seen|banners|CSV,of,baseIds
EXTRACT_JS = """
() => { const t=document.querySelector('table');
  return [...t.querySelectorAll('tbody tr')].map(tr=>{
    const units=[...tr.querySelectorAll('[data-unit-def-tooltip-app]')].map(d=>d.getAttribute('data-unit-def-tooltip-app'));
    const n=[...tr.children].slice(1).map(td=>td.textContent.trim().replace(/\\s+/g,' '));
    return n[1]+'|'+n[0]+'|'+n[2]+'|'+units.join(','); // rate%|seen|banners|CSVunits
  }).join('\\n'); }
"""


def rows_to_json(text, season, fmt, perspective, pulled):
    """Convert extractor lines into the JSON envelope compute_teams.py reads."""
    rows = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        # Split on '|' only: the seen count may itself contain commas ("7,837").
        rate, seen, banners, units_csv = line.split("|", 3)
        rows.append(
            {
                "hold": rate,
                "seen": seen,
                "banners": banners,
                "units": [u for u in units_csv.split(",") if u],
            }
        )
    return {
        "season": season,
        "format": fmt,
        "perspective": perspective,
        "pulled": pulled,
        "rows": rows,
    }
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd ~/SourceCode/sw-utils && python3 -m pytest tests/test_fetch_meta.py -v`
Expected: 5 passed

- [ ] **Step 6: Commit**

```bash
cd ~/SourceCode/sw-utils
git add scripts/fetch_meta.py tests/test_fetch_meta.py tests/fixtures/gac_rows_5v5_def.txt
git commit -m "feat: convert swgoh.gg extractor rows into the meta file formats"
```

---

### Task 5: Browser transport and file writing

**Files:**
- Modify: `scripts/fetch_meta.py`
- Modify: `requirements-dev.txt` (only if playwright is not already resolved)

**Interfaces:**
- Consumes: `EXTRACT_JS`, `rows_to_json` (Task 4)
- Produces: `fetch_view(page, season_id, perspective) -> str` returning extractor text, and a `main()` writing the four files into `data/meta/`

- [ ] **Step 1: Check whether playwright is already available**

```bash
cd ~/SourceCode/sw-utils
python3 -c "import playwright; print(playwright.__version__)" 2>&1
grep -rn playwright requirements-dev.txt farmbot/requirements.txt
```

If the import fails, add `playwright` as a floor line to `requirements-dev.txt`, matching the file's floors-only convention, then `python3 -m pip install playwright && python3 -m playwright install chromium`.

- [ ] **Step 2: Implement the transport**

Add to `scripts/fetch_meta.py`:

```python
import argparse
import datetime

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("ERROR: playwright missing. pip install playwright && python3 -m playwright install chromium")
    raise SystemExit(1)


class MetaFetchFailed(RuntimeError):
    """swgoh.gg did not return a parseable table."""


SEASON_PREFIX = "CHAMPIONSHIPS_GRAND_ARENA_GA2_EVENT_SEASON_"


def season_id(number):
    """Build the full season_id. The bare 'SEASON_80' form 404s; see Global Constraints."""
    return f"{SEASON_PREFIX}{number}"


def fetch_view(page, season, perspective):
    """Fetch one GAC squads view and return the extractor's line output.

    `season` is the bare number, e.g. 80. Two things about this page are not
    obvious and both were verified live on 2026-08-11:

    1. Cloudflare answers the first hit on a parameterised URL with a 403
       interstitial that CLEARS ON ITS OWN after a few seconds. Treating that
       first status as final reports a block that is not there. So we wait for
       the table instead of inspecting the response status.
    2. A wrong season id renders a real 404 page, which also arrives behind that
       interstitial. Waiting on the table distinguishes the two: a 404 never
       produces one, and the timeout message should say so.
    """
    url = f"{BASE}?season_id={season_id(season)}&sort=percent"
    if perspective == "offense":
        url += "&perspective=attack"
    page.goto(url, wait_until="domcontentloaded")
    try:
        page.wait_for_selector("table tbody tr", timeout=30000)
    except Exception:
        title = page.title()
        raise MetaFetchFailed(
            f"{url} produced no table (page title: {title!r}). "
            "A 404 title means the season id is wrong; 'Just a moment...' means the "
            "Cloudflare challenge did not clear inside 30s."
        )
    text = page.evaluate(EXTRACT_JS)
    if not text or not text.strip():
        raise MetaFetchFailed(f"{url} returned a table but no rows")
    return text


def main():
    parser = argparse.ArgumentParser(description="Pull swgoh.gg GAC meta into data/meta/")
    parser.add_argument("--season-5v5", required=True, type=int,
                        help="bare number, even = 5v5, e.g. 80")
    parser.add_argument("--season-3v3", required=True, type=int,
                        help="bare number, odd = 3v3, e.g. 81")
    args = parser.parse_args()

    if args.season_5v5 % 2 != 0 or args.season_3v3 % 2 == 0:
        parser.error("5v5 seasons are even and 3v3 seasons are odd; check the numbers")

    pulled = datetime.date.today().isoformat()
    os.makedirs(META_DIR, exist_ok=True)

    with sync_playwright() as pw:
        # headless=False is mandatory; see Global Constraints. Headless gets 403
        # from Cloudflare on this site even for the base page.
        browser = pw.chromium.launch(headless=False)
        page = browser.new_page()
        try:
            # Warm the session before any parameterised URL. See §3.
            page.goto(BASE, wait_until="domcontentloaded")

            def5v5 = fetch_view(page, args.season_5v5, "defense")
            off5v5 = fetch_view(page, args.season_5v5, "offense")
            def3v3 = fetch_view(page, args.season_3v3, "defense")
            off3v3 = fetch_view(page, args.season_3v3, "offense")
        finally:
            browser.close()

    json_path = os.path.join(META_DIR, f"meta_5v5_defense_s{args.season_5v5}.json")
    with open(json_path, "w") as fh:
        json.dump(
            rows_to_json(def5v5, season_id(args.season_5v5), "5v5", "defense", pulled),
            fh, indent=2,
        )
    print(f"wrote {json_path}")

    for name, text in (
        ("meta_off5v5.txt", off5v5),
        ("meta_def3v3.txt", def3v3),
        ("meta_off3v3.txt", off3v3),
    ):
        path = os.path.join(META_DIR, name)
        with open(path, "w") as fh:
            fh.write(text if text.endswith("\n") else text + "\n")
        print(f"wrote {path}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 3: Run it against the live site**

```bash
cd ~/SourceCode/sw-utils
cp -r data/meta /tmp/meta_backup_before_fetch
python3 scripts/fetch_meta.py --season-5v5 80 --season-3v3 81
```

Those numbers are correct as of 2026-08-11, verified live: season 81 is running (3v3) and 80 is the last complete 5v5. A browser window will open; that is expected and required.

Expected: four "wrote ..." lines. Then verify against ground truth, which exists: the shipped `data/meta/meta_5v5_defense_s80.json` has 31 rows and its first row is

```json
{"hold": "57%", "seen": "29.8K", "banners": "25.21",
 "units": ["STRANGER", "LUMINARAUNDULI", "MAULHATEFUELED", "STARKILLER", "VISASMARR"]}
```

The site returns exactly that today, so a correct run reproduces the same 31 rows and the same first row. If your output differs, the extractor or the conversion is wrong, not the site. Diff against the backup you just made.

If it raises `MetaFetchFailed`, read the page title in the message: a 404 means the season number is wrong, and "Just a moment..." means the challenge did not clear in 30s. Neither is a reason to redesign; report and stop.

- [ ] **Step 4: Verify the board still computes**

```bash
cd ~/SourceCode/sw-utils
python3 scripts/compute_teams.py
```

Expected: runs to completion and writes `data/gac_result.json` with no format errors. This is the real acceptance test: `compute_teams.py` was not modified, so if it reads the new files the formats match.

- [ ] **Step 5: Run the whole suite**

Run: `cd ~/SourceCode/sw-utils && python3 -m pytest tests/ -v`
Expected: all pass, including the pre-existing tests

- [ ] **Step 6: Commit**

```bash
cd ~/SourceCode/sw-utils
git add scripts/fetch_meta.py requirements-dev.txt
git commit -m "feat: script the swgoh.gg meta pull with the warm-session workaround"
```

- [ ] **Step 7: Update the repo map**

`CLAUDE.md` step 3 of the workflow currently says to scrape the meta manually via `browser_recipes.md` §3. Change it to invoke `scripts/fetch_meta.py`, keeping the §3 reference as the documented fallback for when Cloudflare hardens. Commit separately:

```bash
cd ~/SourceCode/sw-utils
git add CLAUDE.md
git commit -m "docs: point the workflow at fetch_meta.py, keep §3 as fallback"
```

---

## Self-Review

**Spec coverage:**

| Spec section | Task |
|---|---|
| 5 warm session, four views, existing formats, season as argument | Tasks 4, 5 |
| 5 fleet meta from `/gac/ship-counters/` | **Not covered.** See gap below |
| 6 RSS source, User-Agent, 429 retry, available fields | Task 1 |
| 6.1 board-unit framing, drop unmatched, explicit empty state | Tasks 2, 3 |
| 7 no shared library, local Playwright, confirm dependency | Task 5 step 1 |
| 8 fixtures, pure parsers, loud failure | Tasks 1, 2, 4 |

**Gap found during review:** the spec mentions fetching fleet meta from `/gac/ship-counters/` in section 5, and no task implements it. It is deliberately deferred rather than added, because the ship-counters page has a different shape from the squads table (per defending capital, with attacker Win% where lower is better) and the extractor in §3 does not cover it. Folding it in would double Task 5 and delay the four files that `compute_teams.py` actually blocks on. Recommend a follow-up plan once the squads path is running. **Flag this to the user rather than silently dropping it.**

**Placeholder scan:** one deliberate instruction to verify rather than assume, in Task 4 Step 2, where the JSON reader function name in `swgoh_meta.py` must be confirmed before the round-trip test is written. The docstring documents `parse_txt` explicitly but not the JSON entry point.

**Type consistency:** `rows_to_json(text, season, fmt, perspective, pulled)` is called with that argument order in Tasks 4 and 5. `match_entries(entries, units, name_map)` is consistent between Tasks 2 and 3. `board_units()` returns a set in both its definition and its use inside `load_board_chatter`.
