#!/usr/bin/env python3
"""
gac_cron_assign.py: put the right DATACRON on each defensive squad.

WHY THIS EXISTS
---------------
On 2026-09-22 the live GAC defence board was found with **all fifteen squads
carrying no datacron at all**, while the account holds a set-33 LEVEL 15 cron and
six level 9s. Owner: *"we seem to have forgotten datacrons on the defense squads
... thats a serious mistake"*, then *"use best datacrons on defense. optimize the
allocation though."* This is that optimisation, written down so it cannot be
forgotten or re-argued.

A datacron on defence is free denial: it costs nothing, it is not consumed, and it
is the only thing on the board that lifts a hold rate above what the published
tier list measures. Leaving one in the inventory is giving away the largest edge
the format offers.

THE MODEL
---------
A cron is a chain of affixes in groups of three: two STAT affixes and one
MECHANIC affix. From `account/data/all`, `affix[].targetRule` names the scope, so
tier k of the cron is `affix[3k-1]`.

  * The two STAT affixes apply to the whole squad unconditionally, so their value
    scales with the cron's LEVEL and nothing else.
  * The MECHANIC affix only fires for units matching its scope, and deeper tiers
    carry bigger mechanics. So a level-9 cron whose tiers 4-9 scope to a faction
    the squad does not have is worth barely more than a level-3.

    value(cron, squad) = STAT_W * level  +  sum over matching tiers k of k

...maximised over a one-to-one assignment, each term weighted by how much the
squad's zone is worth. Holding a FRONT territory denies its own 260 plus the whole
lane behind it (707-805 banners); holding a BACK one denies only 260. That ratio
is the `--front-weight`.

Reads  : output/gac_current_*.json, output/hu_account_all_*.json, data/unit_tags.json
Writes : output/gac_cron_plan.json (+ the table on stdout)
"""
import argparse
import glob
import json
import os
import re

import numpy as np
from scipy.optimize import linear_sum_assignment

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# A tier's two stat affixes are worth roughly this much per cron level against one
# matching mechanic tier. Stats are reliable, mechanics are conditional but larger.
STAT_W = 0.6


def newest(pattern):
    hits = sorted(glob.glob(os.path.join(ROOT, pattern)))
    if not hits:
        raise SystemExit(f"no file matches {pattern}")
    return hits[-1]


def norm(s):
    return re.sub(r"[^a-z0-9]", "", str(s).lower())


def load_tags():
    return json.load(open(os.path.join(ROOT, "data", "unit_tags.json")))


def unit_matches(tag, base_id, tags):
    """Does this one unit satisfy a cron tier's targetRule?"""
    t = norm(tag)
    if t == norm(base_id):
        return True
    info = tags.get(base_id)
    if not info:
        return False
    if t == norm(info.get("a", "")):                    # lightside / darkside
        return True
    if t == norm(info.get("r", "")):                    # tank / support / healer / attacker
        return True
    return any(t == norm(c) for c in info.get("c", []))  # faction categories


def cron_tiers(c):
    """[(tier_number, scope_tag), ...] for a cron, deepest last."""
    aff = c.get("affix") or []
    out = []
    for i, a in enumerate(aff):
        if (i + 1) % 3 == 0:                            # the mechanic affix of each tier
            rule = a.get("targetRule")
            if rule:
                out.append(((i + 1) // 3, rule.replace("target_datacron_", "")))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--board")
    ap.add_argument("--account")
    ap.add_argument("--front-weight", type=float, default=2.5,
                    help="a front territory denies its lane too, so it is worth more")
    ap.add_argument("--json", default=os.path.join(ROOT, "output", "gac_cron_plan.json"))
    a = ap.parse_args()

    g = json.load(open(a.board or newest("output/gac_current_*.json")))["gac"]
    acct = json.load(open(a.account or newest("output/hu_account_all_*.json")))["data"]
    tags = load_tags()

    squads = []
    for z in g["home"]["zones"]:
        zid = z["zoneId"]
        if z["squadCapacity"] == 3 and "phase02_conflict01" in zid:
            continue                                     # the fleet zone takes no cron
        lane = ("FRONT-A" if "phase01_conflict01" in zid else
                "FRONT-B" if "phase01" in zid else "BACK-B")
        for sq in z.get("squads", []):
            ids = [u["baseId"] for u in sq["units"]]
            squads.append({"lane": lane, "ids": ids,
                           "names": [tags.get(b, {}).get("n", b) for b in ids],
                           "weight": a.front_weight if lane.startswith("FRONT") else 1.0,
                           "has_cron": bool(sq.get("datacron"))})

    crons = []
    for c in acct.get("datacrons", []):
        lvl = len(c.get("affix") or [])
        if lvl == 0:
            continue                                     # unbuilt, a random affix roll
        crons.append({"id": c.get("id"), "set": c.get("setId"), "level": lvl,
                      "tiers": cron_tiers(c)})
    crons.sort(key=lambda c: -c["level"])

    n, m = len(squads), len(crons)
    val = np.zeros((n, m))
    detail = {}
    for i, s in enumerate(squads):
        for j, c in enumerate(crons):
            hits = [k for k, tag in c["tiers"]
                    if any(unit_matches(tag, b, tags) for b in s["ids"])]
            v = STAT_W * c["level"] + sum(hits)
            val[i, j] = v * s["weight"]
            detail[i, j] = hits
    r, col = linear_sum_assignment(-val)

    print(f"squads {n} · crons {m} · front weight {a.front_weight}\n")
    plan = []
    for i, j in sorted(zip(r, col), key=lambda p: (squads[p[0]]["lane"], -val[p])):
        s, c = squads[i], crons[j]
        hits = detail[i, j]
        tier_txt = ", ".join(f"t{k}:{tag}" for k, tag in c["tiers"]
                             if k in hits) or "stats only"
        print(f"{s['lane']:<8} {' / '.join(s['names']):<58}")
        print(f"         <- set{c['set']} Lvl {c['level']:<3} [{tier_txt}]  id={c['id']}")
        plan.append({"lane": s["lane"], "squad": s["ids"], "names": s["names"],
                     "cron_id": c["id"], "cron_set": c["set"],
                     "cron_level": c["level"], "matching_tiers": hits,
                     "score": round(float(val[i, j]), 2)})
    unused = [c for k, c in enumerate(crons) if k not in set(col)]
    if unused:
        print("\nunassigned crons: " +
              ", ".join(f"set{c['set']} L{c['level']}" for c in unused))
    json.dump(plan, open(a.json, "w"), indent=1)
    print(f"\nwrote {a.json}")


if __name__ == "__main__":
    main()
