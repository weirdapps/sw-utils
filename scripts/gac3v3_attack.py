#!/usr/bin/env python3
"""
gac3v3_attack.py: the 3v3 attack ROUTE against the LIVE opponent board.

WHY A SECOND ATTACK SCRIPT
--------------------------
`gac_attack.py` prices a 5v5 round off `data/board_result.json`, a bank this repo
only builds for 5v5. Season 83 is 3v3, the format has its own banner chart, its own
tier lists, and (measured on the S83 counter pages) 1- and 2-unit attacker lineups
that sit at the TOP of the table. So the 3v3 route is its own problem.

WHAT IT MAXIMISES
-----------------
Units are single-use across the whole round, so this is a matching, not a list of
good squads. For each enemy squad we know, from swgoh.gg's Kyber-scoped
`/gac/counters/<LEADER>/` pages for the LIVE season, the measured win rate of every
observed attacker lineup. Value of assigning lineup L to target T:

    p(L,T) * MAX_BATTLE_for(|L|)          battle banners, first attempt
  + the zone's 260 conquest banners, credited once the whole zone is expected to fall

...subject to every unit being used at most once, owned at G13+, and NOT locked on
our own defence (a defender cannot attack).

MATCH QUALITY, AND WHY IT IS PRINTED
------------------------------------
A counter row is indexed two ways, best first:
    exact    the attacker lineup was measured against THIS defender lineup (set match)
    leader   measured against the same defending LEADER, a different supporting cast
Never quote a `leader` number as if it were measured against the exact wall.
`--min-seen` drops thin rows; swgoh.gg ships plenty of n<100 lines and they are
noise at Kyber.

Reads  : output/gac_current_<date>.json      (HotUtils gac/get, both boards)
         data/meta/counters/counters_3v3_s83_<date>.json
         data/roster/swgoh_roster_fresh_<date>.json
Writes : output/gac3v3_attack_plan.json (+ the route on stdout)
"""
import argparse
import glob
import json
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gac_score as gs                                              # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
OUT = os.path.join(ROOT, "output")

FMT = "3v3"
# 3v3 squad zones pay 260 for conquest, the fleet zone 219 (gac_score, verified
# first-party off the in-game territory panel).
CONQ_SQUAD = gs.territory_banners("3v3", 5)
CONQ_FLEET = gs.territory_banners("fleet", 3)


def newest(pattern):
    hits = sorted(glob.glob(os.path.join(ROOT, pattern)))
    if not hits:
        raise SystemExit(f"no file matches {pattern}")
    return hits[-1]


def load_roster(path=None):
    path = path or newest("data/roster/swgoh_roster_fresh_*.json")
    d = json.load(open(path))
    by_id = {u["b"]: u for u in d["units"]}
    return path, by_id


def parse_seen(s):
    """'1,142' -> 1142 ; '35.6K' -> 35600."""
    s = str(s).replace(",", "").strip()
    mult = 1
    if s.endswith("K"):
        mult, s = 1000, s[:-1]
    elif s.endswith("M"):
        mult, s = 1000000, s[:-1]
    try:
        return int(float(s) * mult)
    except ValueError:
        return 0


def load_counters(path=None):
    path = path or newest("data/meta/counters/counters_3v3_s83_*.json")
    raw = json.load(open(path))
    out = {}
    for leader, blk in raw.items():
        if "rows" not in blk:
            continue
        rows = []
        for r in blk["rows"]:
            rows.append({"A": r["A"], "D": r["D"], "n": parse_seen(r["seen"]),
                         "win": r["win"] / 100.0, "avg": r.get("avg")})
        out[leader] = rows
    return path, out


def load_board(path=None):
    path = path or newest("output/gac_current_*.json")
    g = json.load(open(path))["gac"]
    return path, g


def my_locked(g):
    """Units the defender has placed. They cannot attack."""
    chars, ships = set(), set()
    for z in g["home"]["zones"]:
        fleet = z["squadCapacity"] == 3 and "phase02_conflict01" in z["zoneId"]
        for sq in z.get("squads", []):
            for u in sq.get("units", []):
                (ships if fleet else chars).add(u["baseId"])
    return chars, ships


def targets(g):
    """Enemy squads we can see, front zones first."""
    out = []
    for z in g["away"]["zones"]:
        zid = z["zoneId"]
        # ⛔ A CLEARED ZONE STILL LISTS ITS DEAD SQUADS, and the per-squad `defeated`
        # flag is NOT set on them. Only `state` (4 = conquered) and
        # `defeatedSquadCount` say so. Filtering on the flag alone re-targeted five
        # corpses on 2026-09-22 and printed "NO FIELDABLE COUNTER" for each.
        if z.get("state") == 4 or z.get("defeatedSquadCount", 0) >= z["squadCapacity"]:
            continue
        front = "phase01" in zid
        fleet = (not front) and z["squadCapacity"] == 3
        for i, sq in enumerate(z.get("squads", [])):
            if sq.get("defeated"):
                continue
            units = [u["baseId"] for u in sq.get("units", [])]
            out.append({"zone": zid, "front": front, "fleet": fleet, "idx": i,
                        "units": units, "leader": units[0] if units else None,
                        "cron": bool(sq.get("datacron"))})
    return out


def candidates(tgt, counters, owned, locked, min_seen, min_gear):
    """Every attacker lineup we can actually field against this target, ranked."""
    rows = counters.get(tgt["leader"], [])
    dset = frozenset(tgt["units"])
    seen_lineups, cands = set(), []
    for r in rows:
        if r["n"] < min_seen:
            continue
        A = r["A"]
        if not A or tuple(A) in seen_lineups:
            continue
        bad = False
        for b in A:
            u = owned.get(b)
            if u is None or u["ct"] != 1 or u["g"] < min_gear or b in locked:
                bad = True
                break
        if bad:
            continue
        seen_lineups.add(tuple(A))
        exact = frozenset(r["D"]) == dset
        cands.append({"A": A, "win": r["win"], "n": r["n"], "avg": r.get("avg"),
                      "match": "exact" if exact else "leader"})
    # highest win rate first; exact match breaks a tie; then sample size
    cands.sort(key=lambda c: (-c["win"], c["match"] != "exact", -c["n"]))
    return cands


def value(c):
    return c["win"] * gs.battle_banners(FMT, team_size=len(c["A"]))


def solve(tgt_list, cand_map, restarts=400, seed=7):
    """Unit-disjoint assignment, maximising expected banners.

    Greedy in a given target order (each target takes its best still-fieldable
    lineup), then randomised restarts over shuffled orders. The problem is small
    (10 targets), so this converges well inside a second.
    """
    rng = random.Random(seed)

    def run(order):
        used, plan = set(), {}
        for t in order:
            for c in cand_map[t["zone"], t["idx"]]:
                if any(b in used for b in c["A"]):
                    continue
                plan[t["zone"], t["idx"]] = c
                used.update(c["A"])
                break
        return plan

    def score(plan):
        tot = sum(value(c) for c in plan.values())
        by_zone = {}
        for t in tgt_list:
            by_zone.setdefault(t["zone"], []).append(t)
        for ts in by_zone.values():
            p = 1.0
            for t in ts:
                c = plan.get((t["zone"], t["idx"]))
                p *= c["win"] if c else 0.0
            tot += p * (CONQ_FLEET if ts[0]["fleet"] else CONQ_SQUAD)
        return tot

    best_plan = run(tgt_list)
    best = score(best_plan)
    for _ in range(restarts):
        order = tgt_list[:]
        rng.shuffle(order)
        p = run(order)
        s = score(p)
        if s > best:
            best, best_plan = s, p
    return best_plan, best


def backup(tgt, cand_map, chosen, used_by_others):
    """Second attempt lineup: disjoint from every FIRST-attempt lineup."""
    for c in cand_map[tgt["zone"], tgt["idx"]]:
        if c is chosen:
            continue
        if any(b in used_by_others for b in c["A"]):
            continue
        return c
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--board")
    ap.add_argument("--counters")
    ap.add_argument("--roster")
    ap.add_argument("--min-seen", type=int, default=60,
                    help="drop counter rows measured on fewer battles than this")
    ap.add_argument("--min-gear", type=int, default=13)
    ap.add_argument("--used", default="", metavar="BASEID,...",
                    help="units already spent this round (they cannot attack again)")
    ap.add_argument("--json", default=os.path.join(OUT, "gac3v3_attack_plan.json"))
    ap.add_argument("--payload-out", default=None, metavar="PATH",
                    help="also write a push_ingame_presets.py payload of the route, "
                         "so each battle is one SELECT SQUAD tap")
    ap.add_argument("--restarts", type=int, default=400)
    a = ap.parse_args()

    bpath, g = load_board(a.board)
    cpath, counters = load_counters(a.counters)
    rpath, owned = load_roster(a.roster)
    locked_c, locked_s = my_locked(g)
    spent = {s.strip().upper() for s in a.used.split(",") if s.strip()}
    locked_c |= spent

    print(f"board    : {os.path.basename(bpath)}  map={g['tournamentMapId']} "
          f"round={g['currentRound']} match={g['currentMatchId']}")
    print(f"counters : {os.path.basename(cpath)}   roster: {os.path.basename(rpath)}")
    print(f"opponent : {g['away']['player']['name']} "
          f"(skill {g['away']['player']['skillRating']})")
    print(f"locked: {len(locked_c)} characters ({len(spent)} already spent this "
          f"round), {len(locked_s)} ships\n")

    tl = [t for t in targets(g) if not t["fleet"]]
    fleets = [t for t in targets(g) if t["fleet"]]
    cand_map = {}
    for t in tl:
        cand_map[t["zone"], t["idx"]] = candidates(
            t, counters, owned, locked_c, a.min_seen, a.min_gear)

    plan, total = solve(tl, cand_map, restarts=a.restarts)

    NM = {b: u["n"] for b, u in owned.items()}

    def nm(b):
        return NM.get(b, b)

    first_used = set()
    for c in plan.values():
        first_used.update(c["A"])

    out = {"board": os.path.basename(bpath), "map": g["tournamentMapId"],
           "opponent": g["away"]["player"]["name"],
           "expected_banners": round(total, 1), "zones": {}}

    for zid in sorted({t["zone"] for t in tl}):
        ts = [t for t in tl if t["zone"] == zid]
        lane = ("FRONT-A (gates the FLEET zone)" if "phase01_conflict01" in zid else
                "FRONT-B (gates BACK-B)" if "phase01" in zid else "BACK")
        pz = 1.0
        print("=" * 78)
        print(f"{zid}   {lane}")
        rows = []
        for t in ts:
            c = plan.get((t["zone"], t["idx"]))
            dl = " / ".join(nm(b) for b in t["units"])
            if c is None:
                print(f"  [{t['idx']}] {dl}")
                print(f"        NO FIELDABLE COUNTER "
                      f"({len(cand_map[t['zone'], t['idx']])} rows, all blocked)")
                pz = 0.0
                rows.append({"target": t["units"], "attacker": None})
                continue
            pz *= c["win"]
            bk = backup(t, cand_map, c, first_used)
            print(f"  [{t['idx']}] vs {dl}{'  <CRON>' if t['cron'] else ''}")
            print(f"        ATTACK  {' / '.join(nm(b) for b in c['A'])}")
            print(f"        {int(c['win']*100)}% on n={c['n']:,} ({c['match']}), "
                  f"{len(c['A'])} units, max "
                  f"{gs.battle_banners(FMT, team_size=len(c['A']))} banners")
            if bk:
                print(f"        backup  {' / '.join(nm(b) for b in bk['A'])} "
                      f"({int(bk['win']*100)}% n={bk['n']:,} {bk['match']})")
            rows.append({"target": t["units"],
                         "target_names": [nm(b) for b in t["units"]],
                         "attacker": c["A"],
                         "attacker_names": [nm(b) for b in c["A"]],
                         "win": c["win"], "n": c["n"], "match": c["match"],
                         "backup": bk["A"] if bk else None,
                         "backup_names": [nm(b) for b in bk["A"]] if bk else None,
                         "backup_win": bk["win"] if bk else None})
        conq = CONQ_FLEET if ts[0]["fleet"] else CONQ_SQUAD
        print(f"  -> P(zone falls) {pz*100:.0f}%, conquest {conq} banners "
              f"(expected {pz*conq:.0f})")
        out["zones"][zid] = {"lane": lane, "p_clear": pz, "conquest": conq,
                             "rows": rows}

    if fleets:
        print("=" * 78)
        print(f"FLEET zone: {len(fleets)} enemy fleets, planned separately "
              f"(ship counters are not in this file)")

    print("=" * 78)
    print(f"EXPECTED BANNERS from the two visible fronts: {total:.0f}")
    print("(the two back zones open only when their own front is 5/5 cleared)")
    json.dump(out, open(a.json, "w"), indent=1)
    print(f"wrote {a.json}")

    if a.payload_out:
        # In-game preset names are capped at ~16 chars, so the slot tag (A1..B5,
        # matching the printed route) comes first and the leader is squeezed after it.
        payload = []
        for zid in sorted(out["zones"]):
            tag = "A" if "phase01_conflict01" in zid else "B"
            for i, r in enumerate(out["zones"][zid]["rows"], start=1):
                if not r.get("attacker"):
                    continue
                lead = "".join(w for w in r["attacker_names"][0].title()
                               if w.isalnum())
                name = f"{tag}{i} {lead}"[:16].rstrip()
                payload.append({"n": name, "sz": len(r["attacker"]), "ct": 1,
                                "cat": "GAC 3v3 - Offense",
                                "u": [[b, n] for b, n in
                                      zip(r["attacker"], r["attacker_names"])]})
        json.dump(payload, open(a.payload_out, "w"), indent=1)
        print(f"wrote {a.payload_out} ({len(payload)} presets)")


if __name__ == "__main__":
    main()
