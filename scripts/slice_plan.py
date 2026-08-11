#!/usr/bin/env python3
"""
slice_plan.py — rank equipped mods for slicing/calibration, most-important first.

Input:
  data/mods_full_<date>.json   (from account/data/all: {mats, mods:[{id,b,dots,tier,lvl,set,slot,spd,spdArrow}]})
  output/invest_plan.json      (the priority ladder: Arena -> GAC -> TB -> TW -> fleets)

Ranking (most→least important):
  ladder rank from invest_plan.py's `mod_priority`, the SAME ordering execute_upgrades.py and
  calibrate.py execute in — this file is the human view of that queue, not a second opinion.
  It used to build its own defense/offense/other buckets from gac_result.json, which ranked
  differently from the executors and could not see TW units at all.
  within rank: highest speed secondary first, speed-arrows boosted, then closer-to-done.

Action per mod (only mods not already 6-dot gold "6A" are queued):
  6-dot, tier<5   -> "slice6"  (slice up toward 6A; uses TIER06 salvage)
  5-dot, tier=5   -> "promote" (5A -> 6E; uses PROMO_T5_T6 + TIER05_05/06 salvage) then slice6
  5-dot, tier<5   -> "slice5"  (slice up toward 5A; uses TIER05_01..04 salvage) then promote

Outputs:
  output/slice_plan.md      (human view, top of queue + summary)
  output/slice_queue.json   (ordered [{id,b,name,dots,tier,spd,spdArrow,imp,action}] for the executor)
"""
import json, os, glob

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")

mods_file = sorted(glob.glob(os.path.join(DATA, "mods_full_*.json")))[-1]
d = json.load(open(mods_file))
mats = d["mats"]
mods = [m for m in d["mods"] if m["b"]]                       # equipped only

ip = json.load(open(os.path.join(ROOT, "output", "invest_plan.json")))
rank_by_b = {b: i for i, b in enumerate(ip["mod_priority"])}
name_by_b = {e["unit"]: e["name"] for e in ip["priority"]}
tier_by_b = {e["unit"]: e["tier"] for e in ip["priority"]}
UNRANKED = len(rank_by_b)          # filler chars sort last, after every laddered unit


def imp(b):
    return rank_by_b.get(b, UNRANKED)


def mode(b):
    t = tier_by_b.get(b, 99)
    return ("ARENA" if t <= 3 else "GAC" if t <= 7 else "TB" if t == 8 else
            "TW" if t <= 10 else "fleet" if t == 11 else "other")


def is_6A(m):
    return m["dots"] == 6 and m["tier"] == 5


def action(m):
    if m["dots"] == 6:
        return "slice6"          # 6E..6B -> 6A
    if m["tier"] == 5:
        return "promote"         # 5A -> 6-dot
    return "slice5"              # 5E..5B -> 5A


queue = [m for m in mods if not is_6A(m)]
for m in queue:
    m["imp"] = imp(m["b"])
    m["mode"] = mode(m["b"])
    m["name"] = name_by_b.get(m["b"], m["b"])
    m["action"] = action(m)

# most important first: ladder rank asc, then speed desc, arrows first, then closer-to-done
queue.sort(key=lambda m: (m["imp"], -m["spd"], not m["spdArrow"], -m["dots"], -m["tier"]))

out_q = os.path.join(ROOT, "output", "slice_queue.json")
os.makedirs(os.path.dirname(out_q), exist_ok=True)
json.dump(queue, open(out_q, "w"), indent=1)

# summary
from collections import Counter
MODES = ("ARENA", "GAC", "TB", "TW", "fleet", "other")
act_lbl = {"slice6": "6-dot slice-up", "promote": "5A->6 promote", "slice5": "5-dot slice-up"}
lines = ["# Slice / calibrate priority queue\n",
         f"Source: `{os.path.basename(mods_file)}` · {len(mods)} equipped mods\n",
         "\n## Materials on hand\n",
         "| promo 5->6 | T06-1 | T06-2 | T06-3 | T06-4 | T05-1..6 | credits |",
         "|---:|---:|---:|---:|---:|---|---:|",
         f"| {mats['PROMO_T5_T6']} | {mats['T06_01']} | {mats['T06_02']} | {mats['T06_03']} | {mats['T06_04']} | "
         f"{mats['T05_01']}/{mats['T05_02']}/{mats['T05_03']}/{mats['T05_04']}/{mats['T05_05']}/{mats['T05_06']} | {mats['credits']:,} |",
         f"\n## Queue: {len(queue)} upgradeable mods (not yet 6A)\n",
         "By ladder rung × action:\n"]
cnt = Counter((m["mode"], m["action"]) for m in queue)
for lbl in MODES:
    parts = [f"{act_lbl[a]}={cnt[(lbl,a)]}" for a in ("slice6", "promote", "slice5") if cnt[(lbl, a)]]
    if parts:
        lines.append(f"- **{lbl}**: " + ", ".join(parts))
lines.append("\n## Top 40 in queue (execute in this order)\n")
lines.append("| # | rung | char | mod | speed | state | action |")
lines.append("|--:|---|---|---|--:|---|---|")
for i, m in enumerate(queue[:40], 1):
    st = f"{m['dots']}-dot t{m['tier']}" + ("  arrow" if m["spdArrow"] else "")
    lines.append(f"| {i} | {m['mode']} | {m['name']} | set{m['set']} slot{m['slot']} | {m['spd']} | {st} "
                 f"| {act_lbl[m['action']]} |")
lines.append("\n_Slicing boosts a random secondary; calibration (6-dot) is what targets speed. "
             "Executor slices in this order until each material type is exhausted._\n")

out_md = os.path.join(ROOT, "output", "slice_plan.md")
open(out_md, "w").write("\n".join(lines))
print("\n".join(lines[:60]))
print(f"\nwrote output/slice_queue.json ({len(queue)} mods) + output/slice_plan.md")
