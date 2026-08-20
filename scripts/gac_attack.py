#!/usr/bin/env python3
"""
gac_attack.py — the attack ROUTE, which is where Astra's rounds are actually lost.

THE PROBLEM THIS SOLVES
-----------------------
Across the last ten rounds Astra converted a mean of 37% of the available banners.
Reading his own match data (HotUtils gac/get, six matches), the shortfall splits
into two failures, and neither is about which squads are good:

  1. HALF-CLEARED LANES. A back territory is invisible and unattackable until the
     front territory in the SAME lane is 100% conquered. Astra repeatedly left one
     squad alive in a front zone. In the S81 loss to Drew that single survivor cost
     755 banners — 57 for the battle, 260 for the territory, 438 for the fleet
     territory it kept locked — and the match was lost by 199.
  2. ZONES NEVER OPENED AT ALL. A mean of 731 banners per round sat in territories
     that were open and simply never attacked.

So the deliverable is not a ranked list of good squads. It is an ORDER: which lane
to commit to, which of your squads goes at which enemy squad, and when to stop.

THE RULES IT ENCODES
--------------------
  * Conquer a lane or do not enter it. A front zone at 3/4 pays the same territory
    banners as one at 0/4: zero.
  * Two attempts maximum on any one target. Attempt 2 is worth 20 fewer banners and
    attempt 3 is worth 30 fewer, and every unit you spend is gone win or lose.
    Astra threw seven squads at one wall in the live S82 round.
  * Units are single-use across the whole round, so the assignment is a matching,
    not a per-battle choice.
  * Undersize where it still wins: +1 banner per empty slot, and far more valuable,
    it leaves units alive for another battle worth 65-79.

Reads  : data/board_result.json (our offense bank), an opponent snapshot from
         HotUtils gac/get (output/gac_current_*.json), data/unit_tags.json
Writes : output/gac_attack_plan.json (+ the route on stdout)
"""
import glob
import json
import math
import os
import sys

import numpy as np
from scipy.optimize import linear_sum_assignment

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gac_score as gs                # noqa: E402
import swgoh_meta                     # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
OUT = os.path.join(ROOT, "output")

# Average attacker win rate across all GAC battles, used to de-bias the two marginal
# rates below. swgoh.gg defensive Hold% averages ~0.2 at Kyber, so the complementary
# attacker rate is ~0.8.
BASE_WIN = 0.80


def logit(p):
    p = min(0.995, max(0.005, p))
    return math.log(p / (1 - p))


def p_win(my_win_pct, their_hold_pct):
    """P(my squad beats their squad), from two marginals and nothing else.

    swgoh.gg gives the attacker's average win rate over everything it attacked, and
    the defender's average hold over everyone who attacked it. Bradley-Terry style,
    combine them on the log-odds scale and subtract the population baseline once so
    it is not counted twice. This is a MODEL: when a real head-to-head counter rate
    is available it should be used instead (see counters_cache).
    """
    return 1 / (1 + math.exp(-(logit(my_win_pct / 100) + logit(1 - their_hold_pct / 100)
                               - logit(BASE_WIN))))


def load_opponent(path=None, fmt="5v5"):
    """The enemy board as placed, straight off HotUtils gac/get."""
    if path is None:
        hits = sorted(glob.glob(os.path.join(OUT, "gac_current_*.json")))
        if not hits:
            raise SystemExit("no opponent snapshot — capture one with browser_recipes.md §6")
        path = hits[-1]
    g = json.load(open(path))["gac"]
    zones = {}
    for z in g["away"]["zones"]:
        key = next((zz["key"] for zz in gs.ZONES[fmt] if zz["zone_id"] == z["zoneId"]), None)
        if key is None:
            continue
        zones[key] = {
            "slots": z["squadCapacity"], "fleet": z["fleet"],
            "remaining": z["squadCount"], "defeated": z["defeatedSquadCount"],
            "visible": len(z["squads"]) > 0,
            # units[] are full unit objects; the board only needs the baseId and the
            # relic, which is the one number that says whether their copy is deeper
            # than the population average the published Hold% was measured on.
            "squads": [{"units": [u["baseId"] for u in s["units"]],
                        "relics": [u.get("relicLevel", 0) for u in s["units"]],
                        "power": s["power"],
                        "leader": s["team"]["leaderBaseId"],
                        "alive": s["status"] != 3,
                        "defends": s.get("successfulDefends", 0),
                        "datacron": bool(s.get("datacron"))}
                       for s in z["squads"]],
        }
    return {"name": g["away"]["player"]["name"], "gp": g["away"]["player"]["galacticPower"],
            "map": g["tournamentMapId"], "zones": zones, "path": path}


def counters_cache(fmt):
    """Real head-to-head counter rates scraped from swgoh.gg /gac/counters/<LEADER>/.

    Files live in data/meta/counters/ as {leader: {rows: [{A, D, seen, win, avg}]}},
    where A is the attacking lineup and D the defending one. Keys in the "extra" file
    are prefixed with the format ("3v3_RACCOON"), so both shapes are normalised here.

    Returns two indexes, most specific first:
      exact[(frozenset(A), frozenset(D))] -> (win%, avg banners, seen)
      by_lead[(frozenset(A), defending_leader)] -> (win%, avg banners, seen)
    A real head-to-head beats the two-marginal model every time; without one, p_win()
    is a guess and the route prints "(model)" so you know which is which.
    """
    exact, by_lead = {}, {}
    d = os.path.join(DATA, "meta", "counters")
    if not os.path.isdir(d):
        return exact, by_lead
    for fn in sorted(os.listdir(d)):
        if not fn.endswith(".json"):
            continue
        for lead, blob in json.load(open(os.path.join(d, fn))).items():
            if "_" in lead and lead.split("_", 1)[0] in ("5v5", "3v3"):
                tag, lead = lead.split("_", 1)
                if tag != fmt:
                    continue
            elif fmt not in fn:
                continue
            for r in (blob or {}).get("rows", []):
                a, dd = frozenset(r["A"]), frozenset(r["D"])
                seen = swgoh_meta.seen_num(r.get("seen", 0))   # handles "14.5K" / "1.2M"
                val = (r["win"], r.get("avg"), seen)
                if exact.get((a, dd), (0, 0, -1))[2] < seen:
                    exact[(a, dd)] = val
                if by_lead.get((a, lead), (0, 0, -1))[2] < seen:
                    by_lead[(a, lead)] = val
    return exact, by_lead


def hold_lookup(fmt):
    """Published Hold% by lineup, so an enemy squad we have data on is priced right."""
    out = {}
    for fn in os.listdir(os.path.join(DATA, "meta")):
        if fmt.replace("v", "v") not in fn or "def" not in fn:
            continue
        p = os.path.join(DATA, "meta", fn)
        try:
            rows = (swgoh_meta.parse_json_def(p) if fn.endswith(".json")
                    else swgoh_meta.parse_txt(p))
        except Exception:
            continue
        for r in rows:
            out[frozenset(r["units"])] = r["rate"]
            out.setdefault(("lead", r["units"][0]), r["rate"])
    return out


def score_matrix(mine, targets, holds, counters):
    """P(win) and expected banners for every (my squad, their squad) pair.

    Three tiers of evidence, best first: an exact head-to-head on this lineup pair,
    a head-to-head on my lineup against this defending LEADER, then the model.
    """
    exact, by_lead = counters
    P = np.zeros((len(mine), len(targets)))
    BAN = np.zeros((len(mine), len(targets)))
    src = [["model"] * len(targets) for _ in mine]
    for j, t in enumerate(targets):
        tset = frozenset(t["units"])
        hold = holds.get(tset) or holds.get(("lead", t["leader"])) or 20
        for i, m in enumerate(mine):
            a = frozenset(m["units"])
            hit = exact.get((a, tset)) or by_lead.get((a, t["leader"]))
            if hit:
                P[i, j] = hit[0] / 100.0
                BAN[i, j] = hit[1] or P[i, j] * gs.MAX_BATTLE["5v5"]
                src[i][j] = f"n={int(hit[2]):,}"
            else:
                P[i, j] = p_win(m["rate"], hold)
                BAN[i, j] = P[i, j] * gs.REF_BATTLE["5v5"]
    return P, BAN, src


def assign(mine, targets, holds, counters):
    """Max-product matching of my squads onto their squads.

    Maximising the product of win probabilities is what "conquer the whole zone"
    means — one likely loss ruins the territory no matter how safe the others are —
    so the matching runs on log P and the objective is a sum again.
    """
    if not targets or not mine:
        return []
    P, BAN, src = score_matrix(mine, targets, holds, counters)
    cost = -np.log(np.clip(P, 1e-6, 1.0))
    rows, cols = linear_sum_assignment(cost)
    out = []
    for i, j in zip(rows, cols):
        out.append({"target": targets[j], "squad": mine[i], "p": float(P[i, j]),
                    "ban": float(BAN[i, j]), "how": src[i][j]})
    out.sort(key=lambda x: -x["p"])       # safest first: bank the certain banners
    return out


def main():
    fmt = "3v3" if "--3v3" in sys.argv else "5v5"
    B = json.load(open(os.path.join(DATA, "board_result.json")))
    tags = json.load(open(os.path.join(DATA, "unit_tags.json")))
    opp = load_opponent(fmt=fmt)
    # The four zoneIds are identical across formats, so a 3v3 run against a 5v5
    # snapshot silently "works" and reads the wrong slot counts. Catch it here.
    if fmt not in opp["map"]:
        raise SystemExit(f"snapshot {os.path.basename(opp['path'])} is a {opp['map']} board "
                         f"but you asked for {fmt} — re-capture the round first")
    holds, counters = hold_lookup(fmt), counters_cache(fmt)
    n_counters = len(counters[0])

    def nm(b):
        return (tags.get(b) or {}).get("n") or b

    bank = [dict(s) for s in B[fmt]["offense"]]
    used = set()
    plan, total = [], 0.0

    print("=" * 96)
    print(f"{fmt} ATTACK ROUTE vs {opp['name']} ({opp['gp']:,} GP)   map {opp['map']}")
    print(f"source: {os.path.basename(opp['path'])}   "
          f"counter rows: {n_counters:,} head-to-head pairs")
    print("=" * 96)

    # Rank the lanes. Commit to the one you are most likely to CONQUER, weighted by
    # what conquering it pays, because a lane you half-clear pays nothing.
    lanes = []
    for lane in ("top", "bottom"):
        front = next(z for z in gs.ZONES[fmt] if z["phase"] == 1 and z["lane"] == lane)
        back = next(z for z in gs.ZONES[fmt] if z["phase"] == 2 and z["lane"] == lane)
        fz = opp["zones"].get(front["key"], {})
        alive = [s for s in fz.get("squads", []) if s["alive"]]
        pairs = assign(bank, alive, holds, counters)
        p_conquer = 1.0
        for x in pairs:
            p_conquer *= x["p"]
        bz = opp["zones"].get(back["key"], {})
        prize = gs.zone_conquest(fmt, front) + gs.zone_total(fmt, back)
        done = not alive and bz.get("defeated", 0) >= bz.get("slots", 0)
        lanes.append({"lane": lane, "front": front, "back": back, "pairs": pairs,
                      "p": p_conquer, "prize": prize, "done": done,
                      "ev": 0 if done else p_conquer * prize})
    lanes.sort(key=lambda l: -l["ev"])

    for order, L in enumerate(lanes, 1):
        print(f"\n{'#' * 90}")
        if L["done"]:
            print(f"# LANE {L['lane'].upper()} — ALREADY CONQUERED, nothing left to take here")
            print(f"{'#' * 90}")
            continue
        print(f"# PRIORITY {order}: LANE {L['lane'].upper()}   "
              f"P(conquer the front) {L['p']:.0%}   prize behind it {L['prize']} banners"
              f"   expected {L['ev']:.0f}")
        print(f"{'#' * 90}")
        if order == 1:
            print("# Finish this lane COMPLETELY before touching the other one. A front zone")
            print("# at 3/4 pays exactly the same territory banners as one at 0/4: zero.")
        print(f"\n  FRONT {L['front']['key']} — {len(L['pairs'])} enemy squads standing")
        for k, x in enumerate(L["pairs"], 1):
            t, m = x["target"], x["squad"]
            if any(u in used for u in m["units"]):
                print(f"   {k}. ⚠ preferred squad already spent — pick from the bench below")
                continue
            used.update(m["units"])
            total += x["ban"]
            plan.append({"lane": L["lane"], "zone": L["front"]["key"], "p": round(x["p"], 3),
                         "banners": round(x["ban"], 1),
                         "target": [nm(u) for u in t["units"]], "squad": [nm(u) for u in m["units"]],
                         "how": x["how"]})
            print(f"   {k}. vs {', '.join(nm(u) for u in t['units'])}"
                  f"{'  [datacron]' if t['datacron'] else ''}")
            print(f"      send  {', '.join(nm(u) for u in m['units'])}")
            print(f"      P(win) {x['p']:.0%} ({x['how']}) -> {x['ban']:.0f} banners   "
                  f"{'⚠ under 70% — expect to need attempt 2, budget a second squad' if x['p'] < 0.70 else ''}")
        back = L["back"]
        bz = opp["zones"].get(back["key"], {})
        print(f"\n  BACK {back['key']} — "
              + ("fleets: send Leviathan at their best capital, then Executor, then Negotiator"
                 if back["fleet"] else
                 (f"{bz.get('remaining', back['slots'])} squads, "
                  + ("VISIBLE" if bz.get("visible") else "still hidden — it unlocks when the front falls"))))
        print(f"      worth {gs.zone_total(fmt, back)} banners. This is the payoff for finishing the front.")

    spare = [s for s in bank if not any(u in used for u in s["units"])]
    print(f"\n{'=' * 96}")
    print(f"RETRY BENCH — {len(spare)} unit-disjoint squads still unspent")
    for s in spare:
        print(f"   {s['rate']:>5.1f}% win  {', '.join(nm(u) for u in s['units'])}")
    print("\nHard rule: two attempts per target, then walk away and spend the units")
    print("finishing a different zone. Attempt 3 pays 30 fewer banners and costs another squad.")

    os.makedirs(OUT, exist_ok=True)
    json.dump({"opponent": opp["name"], "fmt": fmt, "route": plan,
               "bench": [[nm(u) for u in s["units"]] for s in spare]},
              open(os.path.join(OUT, "gac_attack_plan.json"), "w"), indent=1)
    print("\nwrote output/gac_attack_plan.json")


if __name__ == "__main__":
    sys.exit(main())
