#!/usr/bin/env python3
"""
delta_check.py — what changed in the meta since last run.

Compares the two most recent snapshots in data/history/<date>/gac_result.json and reports, per group:
  + teams that ENTERED your plan   - teams that DROPPED OUT
  ~ Hold%/Win% shifts for teams present in both
  gaps opened/closed (meta teams you can't field)

compute_teams.py auto-archives each run into data/history/<date>/. Run this AFTER compute_teams.py.
"""
import json, os, glob

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HIST = os.path.join(ROOT, "data", "history")

snaps = sorted(glob.glob(os.path.join(HIST, "*", "gac_result.json")))
if len(snaps) < 2:
    print(f"Only {len(snaps)} snapshot(s) in data/history — this is the baseline; run again next season to see a delta.")
    raise SystemExit(0)

prev_path, cur_path = snaps[-2], snaps[-1]
prev = json.load(open(prev_path))
cur = json.load(open(cur_path))
prev_date = os.path.basename(os.path.dirname(prev_path))
cur_date = os.path.basename(os.path.dirname(cur_path))
print(f"DELTA  {prev_date}  ->  {cur_date}\n" + "=" * 60)


def leadmap(res, fmt, persp):
    # key = leader base id -> (rate, comp tuple)
    out = {}
    for sq in res.get(fmt, {}).get(persp, []):
        out[sq["units"][0]] = (sq["rate"], tuple(sq["units"]))
    return out


for fmt in ("5v5", "3v3"):
    for persp in ("defense", "offense"):
        a = leadmap(prev, fmt, persp)
        b = leadmap(cur, fmt, persp)
        added = [k for k in b if k not in a]
        dropped = [k for k in a if k not in b]
        changed = []
        for k in b:
            if k in a:
                if b[k][0] != a[k][0]:
                    changed.append((k, a[k][0], b[k][0]))
                elif b[k][1] != a[k][1]:
                    changed.append((k, "comp", "comp"))  # same leader, different members
        if not (added or dropped or changed):
            print(f"{fmt} {persp:8}: no change")
            continue
        print(f"{fmt} {persp}:")
        for k in added:
            print(f"   + ENTERED  {k}  ({b[k][0]}%)")
        for k in dropped:
            print(f"   - DROPPED  {k}  (was {a[k][0]}%)")
        for k, o, n in changed:
            if o == "comp":
                print(f"   ~ {k}: same leader, members changed")
            else:
                arrow = "up" if n > o else "down"
                print(f"   ~ {k}: {o}% -> {n}%  ({arrow})")

# gap changes (by leader, per format)
print("-" * 60)
for fmt in ("5v5", "3v3"):
    for persp in ("def", "off"):
        pa = {g["leader"] for g in prev.get(fmt, {}).get("gaps", {}).get(persp, [])}
        pb = {g["leader"] for g in cur.get(fmt, {}).get("gaps", {}).get(persp, [])}
        newg = pb - pa
        closed = pa - pb
        for k in newg:
            print(f"gap OPENED  {fmt} {persp}: {k} (now meta, can't field)")
        for k in closed:
            print(f"gap CLOSED  {fmt} {persp}: {k}")
print("done")
