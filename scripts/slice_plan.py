#!/usr/bin/env python3
"""
slice_plan.py — rank equipped mods for slicing/calibration, most-important first.

Input:
  data/mods_full_<date>.json   (from account/data/all: {mats, mods:[{id,b,dots,tier,lvl,set,slot,spd,spdArrow}]})
  data/gac_result.json         (squad membership)
  data/roster/swgoh_roster_fresh_*.json (base_id -> name; GL detection)

Ranking (most→least important):
  importance tier: 0 = in a GAC DEFENSE squad, 1 = OFFENSE-only squad, 2 = other owned char
  within tier: highest speed secondary first, speed-arrows boosted, then more dots/tier (closer to done)

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

gac = json.load(open(os.path.join(DATA, "gac_result.json")))
ros_file = sorted(glob.glob(os.path.join(DATA, "roster", "swgoh_roster_fresh_*.json")))[-1]
ros = json.load(open(ros_file))
name_by_b = {u["b"]: u["n"] for u in ros["units"]}

defense, offense = set(), set()
for fmt in ("5v5", "3v3"):
    for sq in gac[fmt]["defense"]:
        defense.update(sq["units"])
    for sq in gac[fmt]["offense"]:
        offense.update(sq["units"])


def imp(b):
    if b in defense:
        return 0
    if b in offense:
        return 1
    return 2


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
    m["name"] = name_by_b.get(m["b"], m["b"])
    m["action"] = action(m)

# most important first: imp asc, then speed desc, arrows first, then closer-to-done (dots, tier) desc
queue.sort(key=lambda m: (m["imp"], -m["spd"], not m["spdArrow"], -m["dots"], -m["tier"]))

out_q = os.path.join(ROOT, "output", "slice_queue.json")
os.makedirs(os.path.dirname(out_q), exist_ok=True)
json.dump(queue, open(out_q, "w"), indent=1)

# summary
from collections import Counter
imp_lbl = {0: "DEFENSE", 1: "offense", 2: "other"}
act_lbl = {"slice6": "6-dot slice-up", "promote": "5A->6 promote", "slice5": "5-dot slice-up"}
lines = ["# Slice / calibrate priority queue\n",
         f"Source: `{os.path.basename(mods_file)}` · {len(mods)} equipped mods\n",
         "\n## Materials on hand\n",
         "| promo 5->6 | T06-1 | T06-2 | T06-3 | T06-4 | T05-1..6 | credits |",
         "|---:|---:|---:|---:|---:|---|---:|",
         f"| {mats['PROMO_T5_T6']} | {mats['T06_01']} | {mats['T06_02']} | {mats['T06_03']} | {mats['T06_04']} | "
         f"{mats['T05_01']}/{mats['T05_02']}/{mats['T05_03']}/{mats['T05_04']}/{mats['T05_05']}/{mats['T05_06']} | {mats['credits']:,} |",
         f"\n## Queue: {len(queue)} upgradeable mods (not yet 6A)\n",
         "By importance × action:\n"]
cnt = Counter((m["imp"], m["action"]) for m in queue)
for i in (0, 1, 2):
    parts = [f"{act_lbl[a]}={cnt[(i,a)]}" for a in ("slice6", "promote", "slice5") if cnt[(i, a)]]
    lines.append(f"- **{imp_lbl[i]}**: " + ", ".join(parts))
lines.append("\n## Top 40 in queue (execute in this order)\n")
lines.append("| # | char | mod | speed | state | action |")
lines.append("|--:|---|---|--:|---|---|")
for i, m in enumerate(queue[:40], 1):
    st = f"{m['dots']}-dot t{m['tier']}" + ("  arrow" if m["spdArrow"] else "")
    lines.append(f"| {i} | {m['name']} | set{m['set']} slot{m['slot']} | {m['spd']} | {st} | {act_lbl[m['action']]} |")
lines.append("\n_Slicing boosts a random secondary; calibration (6-dot) is what targets speed. "
             "Executor slices in this order until each material type is exhausted._\n")

out_md = os.path.join(ROOT, "output", "slice_plan.md")
open(out_md, "w").write("\n".join(lines))
print("\n".join(lines[:60]))
print(f"\nwrote output/slice_queue.json ({len(queue)} mods) + output/slice_plan.md")
