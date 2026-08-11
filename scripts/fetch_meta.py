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
