#!/usr/bin/env python3
"""
gac_place.py — put the chosen defensive squads on the actual GAC map.

The board builder picks WHICH squads defend. Until now nothing decided WHERE they
go, so they were placed in rank order, which is the one ordering the map does not
reward. The map is two lanes:

    FRONT TOP    (4 squads) ──gates──>  FLEET territory  (3 fleets)
    FRONT BOTTOM (4 squads) ──gates──>  BACK territory   (3 squads)

Both fronts are open from the first second of the attack phase. A back territory
is invisible and unattackable until every squad in its own front is dead. So a
squad that survives in a front denies 657-696 banners; the same squad surviving in
the back denies 210-219. That is the whole reason this file exists.

WHAT IT OPTIMISES
-----------------
Expected banners CONCEDED, which is the only thing defense contributes to a GAC
scoreline. For each zone:

    conceded(zone) = SUM over squads of  b_i                     (battle banners)
                   + P(zone falls) * conquest(zone)              (territory banners)
    and for a FRONT zone, add
                     P(zone falls) * total(back zone in this lane)

`b_i` is not modelled — it is swgoh.gg's published "Banners" column, the average
banners an attacker actually earns against that exact lineup. It already prices in
second attempts and lost attackers, which is what a wall really does for you at
Kyber, where nothing holds outright.

`P(zone falls)` uses per-squad conquest odds derived from Hold% (see ATTEMPTS).
That part IS a model and is flagged as such; the sensitivity is printed so you can
see how much any conclusion leans on it.

Reads  : data/board_result.json, data/roster/*.json, data/unit_tags.json
Writes : output/gac_placement.json (+ a map on stdout)
"""
import itertools
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gac_score as gs                # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
OUT = os.path.join(ROOT, "output")

# How many times a Kyber opponent will throw a squad at one wall before giving up.
# Not a measurement. It is the one free parameter here, so main() prints the answer
# at 1.5 / 2.5 / 4.0 and you can see whether the placement actually depends on it.
# Evidence it should be >1: Astra's own live board was cleared 14/14 by a 15.2M
# opponent, and swgoh.gg Hold% is per-BATTLE, not per-round.
ATTEMPTS = 2.5


def conquest_odds(hold_pct, attempts=ATTEMPTS):
    """P(this wall is eventually beaten during the 24h attack phase)."""
    h = max(0.0, min(0.95, hold_pct / 100.0))
    return 1.0 - h ** attempts


def zone_cost(fmt, z, squads, attempts=ATTEMPTS):
    """Expected banners conceded from ONE zone, in isolation.

    A squad only pays out its banners if it is actually beaten, and the territory
    bonus only if every squad in the zone is. Nothing about the lane is priced in
    here — that is lane_cost's job, so the back zone is never counted twice.
    """
    battles = p_falls = 0.0
    p_falls = 1.0
    for s in squads:
        q = conquest_odds(s["rate"], attempts)
        battles += q * s["ban"]
        p_falls *= q
    return battles + p_falls * gs.zone_conquest(fmt, z), p_falls


def lane_cost(fmt, lane, placed, fleets, attempts=ATTEMPTS):
    """Expected banners conceded by a whole lane: front, plus the back it gates.

    The back only ever pays out if the front is fully conquered first, so its whole
    cost is multiplied by P(front falls). That conditional is the entire reason a
    front slot is worth more than a back slot.
    """
    front = next(z for z in gs.ZONES[fmt] if z["phase"] == 1 and z["lane"] == lane)
    back = next(z for z in gs.ZONES[fmt] if z["phase"] == 2 and z["lane"] == lane)
    fc, p_front = zone_cost(fmt, front, placed[front["key"]], attempts)
    if back["fleet"]:
        # Fleet hold rates are not published per lineup, so the fleet zone is priced
        # at its ceiling. That is deliberately pessimistic: it never lets a strong
        # fleet excuse a weak gate in front of it.
        bc = gs.zone_total(fmt, back) if len(fleets) == back["slots"] else gs.zone_total(fmt, back)
    else:
        bc, _ = zone_cost(fmt, back, placed[back["key"]], attempts)
    return fc + p_front * bc, p_front, fc, bc


def partitions(items, sizes):
    """Every way to split `items` into groups of the given sizes. Order inside a
    group is irrelevant to the score, so this is combinations, not permutations:
    11 squads into 4/4/3 is 11,550 partitions and 15 into 5/5/5 is 756,756 — both
    small enough to enumerate exactly rather than search."""
    if not sizes:
        yield []
        return
    n, rest = sizes[0], sizes[1:]
    idx = range(len(items))
    for pick in itertools.combinations(idx, n):
        taken = set(pick)
        chosen = [items[i] for i in pick]
        left = [items[i] for i in idx if i not in taken]
        for tail in partitions(left, rest):
            yield [chosen] + tail


def char_zones(fmt):
    return [z for z in gs.ZONES[fmt] if not z["fleet"]]


def total_cost(fmt, placed, fleets, attempts=ATTEMPTS):
    return sum(lane_cost(fmt, ln, placed, fleets, attempts)[0] for ln in ("top", "bottom"))


def solve(fmt, squads, fleets, attempts=ATTEMPTS):
    """Assign squads to the three CHARACTER zones, minimising conceded banners."""
    zs = char_zones(fmt)
    sizes = [z["slots"] for z in zs]
    if sum(sizes) != len(squads):
        raise SystemExit(
            f"{fmt}: {len(squads)} squads for {sum(sizes)} slots. Every slot must be "
            f"filled — an unset one hands the attacker {gs.MAX_BATTLE[fmt]} free banners.")
    best, best_cost = None, float("inf")
    worst_cost = 0.0
    for groups in partitions(squads, sizes):
        placed = {z["key"]: g for z, g in zip(zs, groups)}
        c = total_cost(fmt, placed, fleets, attempts)
        if c < best_cost:
            best, best_cost = placed, c
        worst_cost = max(worst_cost, c)
    return best, best_cost, worst_cost


def rank_order(fmt, squads, fleets, attempts=ATTEMPTS):
    """What the pipeline effectively did before: fill the zones in rank order."""
    zs, out, i = char_zones(fmt), {}, 0
    for z in zs:
        out[z["key"]] = squads[i:i + z["slots"]]
        i += z["slots"]
    return out, total_cost(fmt, out, fleets, attempts)


def main():
    B = json.load(open(os.path.join(DATA, "board_result.json")))
    tags = json.load(open(os.path.join(DATA, "unit_tags.json")))

    def nm(b):
        return (tags.get(b) or {}).get("n") or b

    plan = {"model": {"attempts": ATTEMPTS,
                      "objective": "expected banners conceded (lower is better)"}}
    for fmt in ("5v5", "3v3"):
        squads = sorted(B[fmt]["defense"], key=lambda s: -s["rate"])
        fleets = B["fleets"].get("GAC Fleet - Defense", [])
        placed, cost, worst = solve(fmt, squads, fleets)
        _, naive = rank_order(fmt, squads, fleets)

        print("=" * 96)
        print(f"{fmt} DEFENSE PLACEMENT — the opponent's ceiling against you is "
              f"{gs.ceiling(fmt)} banners")
        print("=" * 96)
        for lane in ("top", "bottom"):
            lc, p_front, fc, bc = lane_cost(fmt, lane, placed, fleets)
            front = next(z for z in gs.ZONES[fmt] if z["phase"] == 1 and z["lane"] == lane)
            back = next(z for z in gs.ZONES[fmt] if z["phase"] == 2 and z["lane"] == lane)
            print(f"\n### LANE {lane.upper()} — expected conceded {lc:.0f}")
            print(f"  FRONT  {front['key']:<13} {front['slots']} slots   "
                  f"(gate: hold ONE here and the whole lane behind it stays invisible)")
            for s in placed[front["key"]]:
                print(f"     {s['rate']:>5.1f}% hold · concedes {s['ban']:>5.1f}   "
                      + " · ".join(nm(u) for u in s["units"]))
            print(f"     -> P(front falls) {p_front:.0%}, front concedes {fc:.0f}")
            print(f"  BACK   {back['key']:<13} {back['slots']} slots   "
                  f"(only reachable {p_front:.0%} of the time)")
            if back["fleet"]:
                for i, f in enumerate(fleets, 1):
                    print(f"     F{i} {f['name']}")
                if len(fleets) != back["slots"]:
                    print(f"     ⚠ {len(fleets)} fleets for {back['slots']} slots — "
                          f"{gs.MAX_BATTLE['fleet']} free banners each")
            else:
                for s in placed[back["key"]]:
                    print(f"     {s['rate']:>5.1f}% hold · concedes {s['ban']:>5.1f}   "
                          + " · ".join(nm(u) for u in s["units"]))
            print(f"     -> back concedes {bc:.0f} if reached")

        print(f"\n  EXPECTED CONCEDED {cost:.0f} of {gs.ceiling(fmt)}   "
              f"(rank-order fill {naive:.0f} · worst arrangement {worst:.0f})")
        print(f"  Placement alone is worth {naive - cost:.0f} banners vs a rank-order fill "
              f"and {worst - cost:.0f} vs the worst case. Read that honestly: the ordering is "
              f"cheap to get right and it is NOT where a round is won.")
        for a in (1.5, 2.5, 4.0):
            _, c2, _ = solve(fmt, squads, fleets, a)
            print(f"    sensitivity ATTEMPTS={a}: {c2:.0f} conceded")
        print()

        plan[fmt] = {
            "expected_conceded": round(cost),
            "ceiling_against_you": gs.ceiling(fmt),
            "zones": {k: [{"rate": round(s["rate"], 1), "ban": s["ban"], "units": s["units"],
                           "names": [nm(u) for u in s["units"]]} for s in v]
                      for k, v in placed.items()},
        }
        plan[fmt]["zones"]["back_fleet"] = [{"name": f["name"], "units": f["units"]}
                                            for f in fleets]

    os.makedirs(OUT, exist_ok=True)
    json.dump(plan, open(os.path.join(OUT, "gac_placement.json"), "w"), indent=1)
    print("wrote output/gac_placement.json")


if __name__ == "__main__":
    sys.exit(main())
