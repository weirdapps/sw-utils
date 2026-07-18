# SWGOH GAC Team Builder

Grounded Grand Arena (GAC) team builder for **Astra** (ally `145357294`, Kyber 3 → Kyber 2).
Pulls live swgoh.gg meta + your roster, builds defense-first + offense squads and full fleets under
the real single-use / owned / G13+ rules, and uploads them to **HotUtils** as clean category groups.

Everything is **grounded**: defense = top swgoh.gg **Hold%**, offense = top **Win%**. Sort swgoh.gg the
same way and you'll see the same teams.

## What it produces
- **4 squad groups** (HotUtils categories): `GAC 5v5 - Defense` (11), `GAC 5v5 - Offense` (15),
  `GAC 3v3 - Defense` (15), `GAC 3v3 - Offense` (15).
- **2 fleet groups** (full ~8-ship lineups): `GAC Fleet - Defense` (3), `GAC Fleet - Offense` (3).
- `output/playbook.html` — human-readable plan (hold/win %, reasoning, GL split, gaps, fleets).

## Layout
```
CLAUDE.md                 orchestration + rules (read this first)
scripts/
  compute_teams.py        roster + meta  -> data/gac_result.json   (defense-first, no-repeat, GL reserve)
  generate_hotutils.py    gac_result     -> output/ (6 category JSONs, upload_payload.json, playbook.html)
  browser_recipes.md      the browser JS (roster pull, board read, meta scrape, HotUtils API)
data/
  roster/                 swgoh.gg roster pulls
  meta/                   swgoh.gg meta snapshots (5v5/3v3 def/off)
  hotutils_backup/        HotUtils squad exports (restore point)
  gac_result.json         computed picks + gaps
output/                   generated deliverables (git-ignored except playbook)
memory/notes.md           board counts, gaps, key facts
```

## Run it (each GAC season / when meta shifts)
See CLAUDE.md "Full workflow". TL;DR:
1. Browser: refresh roster, read board counts, scrape meta (browser_recipes.md).
2. `python3 scripts/compute_teams.py`
3. `python3 scripts/generate_hotutils.py`
4. Browser: upload `output/upload_payload.json` to HotUtils (browser_recipes.md §4).

## Status (last run 2026-07-18)
62 squads live in HotUtils. Biggest upgrades: **GL Hondo** (squad) + **Profundity** (fleet).
