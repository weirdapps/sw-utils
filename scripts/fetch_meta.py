#!/usr/bin/env python3
"""fetch_meta.py - pull swgoh.gg GAC meta into data/meta/.

Automates browser_recipes.md §3. Two things there are load-bearing and are
reproduced exactly:
  - swgoh.gg is behind Cloudflare, so a real browser engine is required.
  - Parameterised URLs get JS-challenged unless the base /gac/squads/ page is
    loaded first to warm the session.

The season id is an argument, not inferred. Guessing it wrong silently writes a
different season's meta into the board inputs.

Usage:  python3 scripts/fetch_meta.py --season-5v5 80 --season-3v3 81
"""
import argparse
import datetime
import json
import os

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("ERROR: playwright missing. pip install playwright && python3 -m playwright install chromium")
    raise SystemExit(1)


class MetaFetchFailed(RuntimeError):
    """swgoh.gg did not return a parseable table."""

BASE = "https://swgoh.gg/gac/squads/"
SEASON_PREFIX = "CHAMPIONSHIPS_GRAND_ARENA_GA2_EVENT_SEASON_"
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
