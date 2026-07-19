#!/usr/bin/env python3
"""
level_priority.py — after the optimizer MOVES mods, decide which mods to LEVEL to 15.

Grandivory's "Move mods in-game" only relocates mods; it never levels/slices/calibrates them.
The optimizer reports a big "level up to 15" credit figure covering EVERY recommended mod that is
below level 15 — but most of those sit on filler characters. This script keeps only the ones on your
actual GAC squads (from gac_result.json), so you spend credits where they convert to GAC wins.

INPUT  (grounded, scraped from the Grandivory review view, "Show me: Mod Upgrades"):
  data/mod_upgrades_below15_<date>.json  = { "<display name>": <#mods below 15>, ... }
  (scrape recipe: on the review page, for each .mod read .mod-level and its .assigned-character
   .avatar-name; tally names where level < 15. See browser_recipes.md.)

Reads gac_result.json (squad membership) + the roster (name<->base_id). Prints DEF first (defense
holds GAC), then OFF. Filler characters are summarised, not listed.

Usage: python3 scripts/level_priority.py [path-to-upgrades-json]
"""
import json, os, sys, glob

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")

up_path = sys.argv[1] if len(sys.argv) > 1 else sorted(
    glob.glob(os.path.join(DATA, "mod_upgrades_below15_*.json")))[-1]
up = json.load(open(up_path))
gac = json.load(open(os.path.join(DATA, "gac_result.json")))
ros_file = sorted(glob.glob(os.path.join(DATA, "roster", "swgoh_roster_fresh_*.json")))[-1]
ros = json.load(open(ros_file))

name_by_b = {u["b"]: u["n"] for u in ros["units"]}
b_by_name = {u["n"]: u["b"] for u in ros["units"]}

# base_id -> set of "5v5 DEF (leader)" tags, split by perspective
squad = {}
for fmt in ("5v5", "3v3"):
    for persp, lab in (("defense", "DEF"), ("offense", "OFF")):
        for sq in gac[fmt][persp]:
            lead = name_by_b.get(sq["units"][0], sq["units"][0])
            for b in sq["units"]:
                squad.setdefault(b, set()).add((lab, f"{fmt} {lab} ({lead})"))

rows = []           # (is_def, cnt, name, tags)
filler_c = filler_m = 0
for nm, cnt in up.items():
    b = b_by_name.get(nm)
    if b in squad:
        tags = squad[b]
        is_def = any(t[0] == "DEF" for t in tags)
        rows.append((is_def, cnt, nm, sorted({t[1] for t in tags})))
    else:
        filler_c += 1
        filler_m += cnt

# DEF first, then by mod count
rows.sort(key=lambda r: (not r[0], -r[1], r[2]))


def emit(fh):
    fh.write("# Mod leveling priority (post-optimize)\n\n")
    fh.write(f"Source: `{os.path.basename(up_path)}` · roster `{os.path.basename(ros_file)}`\n\n")
    sq_m = sum(r[1] for r in rows)
    fh.write(f"- **Level these {sq_m} mods on {len(rows)} GAC-squad characters** "
             f"(defense first — defense holds GAC).\n")
    fh.write(f"- Skip the **{filler_m} mods on {filler_c} filler characters** "
             f"(not on any squad).\n")
    fh.write(f"- Total below-15 = {sum(up.values())} mods "
             f"(the optimizer's full 'level up to 15' figure).\n\n")
    for header, want in (("## DEFENSE squads (top priority)", True),
                         ("## OFFENSE banks", False)):
        grp = [r for r in rows if r[0] == want]
        if not grp:
            continue
        fh.write(header + "\n\n| mods | character | squads |\n|---:|---|---|\n")
        for _, cnt, nm, tags in grp:
            fh.write(f"| {cnt} | {nm} | {', '.join(tags)} |\n")
        fh.write("\n")
    fh.write("_Leveling is manual in-game (no tool spends credits for you). "
             "Slicing to 6-dot and calibrating 6-dot secondaries are separate, "
             "material-gated, and also manual._\n")


out = os.path.join(ROOT, "output", "level_priority.md")
os.makedirs(os.path.dirname(out), exist_ok=True)
with open(out, "w") as fh:
    emit(fh)
emit(sys.stdout)
print(f"\nwrote {os.path.relpath(out, ROOT)}", file=sys.stderr)
