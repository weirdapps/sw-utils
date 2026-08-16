#!/usr/bin/env python3
"""
gac_doctrine.py — settle "how much should go on defense?" by measurement.

THE QUESTION
------------
The owner's objection, and it is a good one: GAC pays banners ONLY on offense, you
control offense and you do not control defense, so the best squads belong on
offense and defense should be leftovers — the defensive GLs plus whatever meta
teams remain. Is that right?

It cannot be answered by arguing about Hold%, because the two sides pay out
differently:
  * an OFFENSE squad earns its banners, and can also be the squad that conquers a
    territory, which pays 210-240 more and unlocks a whole gated lane behind it;
  * a DEFENSE squad earns nothing. It only denies — and only against an opponent
    who would otherwise have taken those banners. Against someone who full-clears,
    a wall denies exactly zero.

So this simulates a whole round, both sides, under each doctrine, against REAL
opponent boards, and reports net banners. Whatever wins, wins.

WHAT IT SIMULATES
-----------------
For each doctrine (which GLs are forbidden from defense):
  1. rebuild the board with build_board
  2. DEFENSE: gac_place.solve -> expected banners conceded (exact, gated)
  3. OFFENSE: walk the enemy board lane by lane. Hungarian-match my squads onto
     their squads on log P(win); units are single-use, so a squad spent in the
     front is gone for the back. Territory conquest is credited at
     P(every squad in that zone beaten), and a back zone's whole value is
     multiplied by P(its front was conquered) — the gate.
  4. net = earned - conceded

Run:  python3 scripts/gac_doctrine.py
"""
import copy
import os
import sys

import numpy as np
from scipy.optimize import linear_sum_assignment

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import board_config as cfg            # noqa: E402
import build_board as bb              # noqa: E402
import gac_attack as ga               # noqa: E402
import gac_place as gp                # noqa: E402
import gac_score as gs                # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
OUT = os.path.join(ROOT, "output")

# Fleet win rates are constants here on purpose: ships never compete with characters
# for units, so the fleet allocation is identical under every doctrine. It still has
# to be simulated, because conquering front_top is what unlocks the fleet territory.
FLEET_WIN = [0.964, 0.925, 0.795]     # Leviathan, Executor, Negotiator — Kyber S81

DOCTRINES = {
    "A shipped": {
        "off_only": ["JEDIMASTERKENOBI", "GRANDMASTERLUKE", "SITHPALPATINE", "GLLEIA"],
        "note": "SLKR released to defense (#2 wall at Kyber, 47% hold)",
    },
    "B owner": {
        "off_only": ["JEDIMASTERKENOBI", "GRANDMASTERLUKE", "SITHPALPATINE", "GLLEIA",
                     "SUPREMELEADERKYLOREN"],
        "note": "the classic rule: the 5 attacking GLs are attack-only",
    },
    "C aggressive": {
        "off_only": ["JEDIMASTERKENOBI", "GRANDMASTERLUKE", "SITHPALPATINE", "GLLEIA",
                     "SUPREMELEADERKYLOREN", "GLAHSOKATANO", "GLREY"],
        "note": "only Lord Vader and Jabba are allowed to wall",
    },
    "D max offense": {
        "off_only": ["JEDIMASTERKENOBI", "GRANDMASTERLUKE", "SITHPALPATINE", "GLLEIA",
                     "SUPREMELEADERKYLOREN", "GLAHSOKATANO", "GLREY", "LORDVADER",
                     "JABBATHEHUTT"],
        "note": "no GL touches defense at all — but this STRANDS GL Rey, who has no "
                "offense row in either format, so five units go unused",
    },
    "E rey-walls": {
        "off_only": ["JEDIMASTERKENOBI", "GRANDMASTERLUKE", "SITHPALPATINE", "GLLEIA",
                     "SUPREMELEADERKYLOREN", "GLAHSOKATANO", "LORDVADER", "JABBATHEHUTT"],
        "note": "every GL that HAS an offense role attacks; GL Rey walls because she "
                "has none. This is the owner's rule stated precisely.",
    },
    "F rey+slkr wall": {
        "off_only": ["JEDIMASTERKENOBI", "GRANDMASTERLUKE", "SITHPALPATINE", "GLLEIA",
                     "GLAHSOKATANO", "LORDVADER", "JABBATHEHUTT"],
        "note": "E, but SLKR walls too — isolates the one GL the marginal table calls "
                "a toss-up",
    },
}


def meta_board(holds, n_squads):
    """A representative Kyber opponent: the top published walls, unit-disjoint.

    Round 3's opponent is unknown, so a doctrine must not be chosen on one captured
    board. This is the population Astra is actually matched against.
    """
    rows = sorted((v, k) for k, v in holds.items() if isinstance(k, frozenset))
    out, used = [], set()
    for rate, units in reversed(rows):
        if len(out) >= n_squads or used & set(units):
            continue
        out.append({"units": list(units), "leader": None, "hold": rate})
        used |= set(units)
    return out


def enemy_from_snapshot(fmt, holds):
    """The live opponent's board, with any zone we never unlocked filled from meta."""
    opp = ga.load_opponent(fmt=fmt)
    zones, filler = {}, meta_board(holds, 20)
    fi = 0
    for z in gs.ZONES[fmt]:
        if z["fleet"]:
            continue
        got = opp["zones"].get(z["key"], {})
        sq = [{"units": s["units"], "leader": s["leader"]} for s in got.get("squads", [])]
        while len(sq) < z["slots"]:            # hidden zone — substitute meta walls
            sq.append(filler[fi])
            fi += 1
        zones[z["key"]] = sq[:z["slots"]]
    return opp["name"], zones


def enemy_from_meta(fmt, holds):
    zones, filler, i = {}, meta_board(holds, 20), 0
    for z in gs.ZONES[fmt]:
        if z["fleet"]:
            continue
        zones[z["key"]] = filler[i:i + z["slots"]]
        i += z["slots"]
    return "meta board", zones


def simulate_offense(fmt, bank, enemy, holds, counters):
    """Expected banners earned in one round. Units are single-use across the board."""
    avail = list(bank)
    earned, detail = 0.0, {}
    for lane in ("top", "bottom"):
        front = next(z for z in gs.ZONES[fmt] if z["phase"] == 1 and z["lane"] == lane)
        back = next(z for z in gs.ZONES[fmt] if z["phase"] == 2 and z["lane"] == lane)

        def clear(zone_key, zone, pool):
            targets = enemy.get(zone_key, [])
            if not targets or not pool:
                return 0.0, 0.0, pool
            P, BAN, _ = ga.score_matrix(pool, targets, holds, counters)
            rows, cols = linear_sum_assignment(-np.log(np.clip(P, 1e-6, 1.0)))
            got, p_all, spent = 0.0, 1.0, set()
            for i, j in zip(rows, cols):
                got += P[i, j] * BAN[i, j]
                p_all *= P[i, j]
                spent.add(id(pool[i]))
            got += p_all * gs.zone_conquest(fmt, zone)
            return got, p_all, [s for s in pool if id(s) not in spent]

        f_got, p_front, avail = clear(front["key"], front, avail)
        if back["fleet"]:
            b_got = sum(FLEET_WIN) / 3 * gs.MAX_BATTLE["fleet"] * 3
            b_got += np.prod(FLEET_WIN) * gs.zone_conquest(fmt, back)
        else:
            b_got, _, avail = clear(back["key"], back, avail)
        earned += f_got + p_front * b_got
        detail[lane] = (p_front, f_got, b_got)
    return earned + gs.BANNER["first_attack"], detail


def run(fmt="5v5"):
    holds, counters = ga.hold_lookup(fmt), ga.counters_cache(fmt)
    boards = []
    try:
        boards.append(enemy_from_snapshot(fmt, holds))
    except SystemExit:
        pass
    boards.append(enemy_from_meta(fmt, holds))

    saved = copy.deepcopy(cfg.ATTACK_ONLY_BY_FORMAT)
    print("=" * 104)
    print(f"{fmt} DOCTRINE TEST — net banners per round, simulated against "
          f"{len(boards)} opponent board(s). Ceiling {gs.ceiling(fmt)}.")
    print("=" * 104)
    hdr = f"{'doctrine':<15}{'off sqds':>9}{'conceded':>10}"
    for nm, _ in boards:
        hdr += f"{nm[:16]:>18}"
    print(hdr + f"{'NET (avg)':>12}")
    rows = []
    for name, d in DOCTRINES.items():
        cfg.ATTACK_ONLY_BY_FORMAT[fmt] = d["off_only"]
        res = bb.build()
        dfn, off = res[fmt]["defense"], res[fmt]["offense"]
        _, conceded, _ = gp.solve(fmt, sorted(dfn, key=lambda s: -s["rate"]),
                                  res["fleets"].get("GAC Fleet - Defense", []))
        line = f"{name:<15}{len(off):>9}{conceded:>10.0f}"
        earned = []
        for _, enemy in boards:
            e, _det = simulate_offense(fmt, off, enemy, holds, counters)
            earned.append(e)
            line += f"{e:>18.0f}"
        net = sum(earned) / len(earned) - conceded
        rows.append((name, net, d["note"], len(off), conceded, earned))
        print(line + f"{net:>12.0f}")
    cfg.ATTACK_ONLY_BY_FORMAT.update(saved)

    rows.sort(key=lambda r: -r[1])
    best = rows[0]
    print(f"\n  BEST: {best[0]} — {best[2]}")
    for name, net, _note, n_off, conc, earned in rows:
        print(f"    {name:<15} net {net:>6.0f}   ({n_off} offense squads, "
              f"concedes {conc:.0f}, earns {sum(earned)/len(earned):.0f})")
    print("\n  Read the spread, not just the winner: if two doctrines are within ~30")
    print("  banners the model cannot separate them and the tie should be broken on")
    print("  something it cannot see (how reliably the attacks actually get played).")
    return rows


if __name__ == "__main__":
    run("5v5")
    print()
    run("3v3")
