#!/usr/bin/env python3
"""advisor.py — A3 farm/priority advisor.

Turns compute_teams' `gaps` (top meta teams you cannot field + which units are
missing) into a ranked "what to farm next" list, so the daily brief (A1) and the
farming macro (B1) know where to spend energy.

Ranking heuristic (the tunable decision — edit `_sort_key` to reweight):
  1. SOLE-BLOCKERS first — a unit that is the ONLY missing piece of a meta team
     unlocks that team immediately; rank by the best such team's rate.
  2. then BREADTH — how many gap teams the unit appears in,
  3. then QUALITY — the best rate of any team needing it.

Usage:  python3 scripts/advisor.py            # reads data/gac_result.json
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GAC_RESULT = os.path.join(ROOT, "data", "gac_result.json")


def _sort_key(entry):
    best_sole = max((s["rate"] for s in entry["sole_blocker_of"]), default=0)
    return (-best_sole, -entry["also_needed_in"], -entry["best_rate"])


def farm_priority(gac_result):
    """Rank missing units by board-unlock impact.

    Returns a list of dicts sorted best-first:
        {unit, sole_blocker_of:[{fmt,persp,leader,rate}], also_needed_in, best_rate}
    """
    agg = {}
    for fmt, fmtdata in gac_result.items():
        for persp, gaps in (fmtdata.get("gaps") or {}).items():
            for team in gaps:
                missing = team.get("missing", [])
                for unit in missing:
                    d = agg.setdefault(unit, {"unit": unit, "sole_blocker_of": [],
                                              "also_needed_in": 0, "best_rate": 0})
                    d["also_needed_in"] += 1
                    d["best_rate"] = max(d["best_rate"], team["rate"])
                    if len(missing) == 1:
                        d["sole_blocker_of"].append(
                            {"fmt": fmt, "persp": persp,
                             "leader": team.get("leader"), "rate": team["rate"]})
    return sorted(agg.values(), key=_sort_key)


def relic_priority(gac_result, roster, target=9):
    """Rank your FIELDED board units that sit below a relic target, by the strongest
    team they hold. Board units are already G13 (board rule), so relic is the next
    lever — reinforce your highest-value walls/attackers first. Default target 9 is
    the practical floor for a strong (Kyber) account; laggards at relic 7-8 surface.

    Returns [{unit, rt, best_rate, in_teams}] sorted best-first.
    """
    rt_by_b = {u["b"]: u.get("rt") for u in roster.get("units", [])}
    name_by_b = {u["b"]: u.get("n", u["b"]) for u in roster.get("units", [])}
    agg = {}
    for _fmt, d in gac_result.items():
        for persp in ("defense", "offense"):
            for team in d.get(persp, []):
                rate = team.get("rate", 0)
                for b in team.get("units", []):
                    rt = rt_by_b.get(b)
                    if rt is None or rt >= target:  # unowned or already at target
                        continue
                    e = agg.setdefault(b, {"unit": name_by_b.get(b, b), "rt": rt,
                                           "best_rate": 0, "in_teams": 0})
                    e["best_rate"] = max(e["best_rate"], rate)
                    e["in_teams"] += 1
    return sorted(agg.values(), key=lambda x: (-x["best_rate"], x["rt"]))


def load_gac_result(path=GAC_RESULT):
    with open(path) as f:
        return json.load(f)


if __name__ == "__main__":
    ranked = farm_priority(load_gac_result())
    print(f"Farm priority — {len(ranked)} missing units block your board\n")
    for e in ranked[:15]:
        sole = e["sole_blocker_of"]
        tag = ""
        if sole:
            best = max(sole, key=lambda s: s["rate"])
            tag = f"  ⭐ SOLE-BLOCKER of {best['rate']}% {best['fmt']} {best['persp']} ({best['leader']})"
        print(f"  {e['unit']:<26} in {e['also_needed_in']} gap-teams, best {e['best_rate']}%{tag}")
