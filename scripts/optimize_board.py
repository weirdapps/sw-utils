#!/usr/bin/env python3
"""
optimize_board.py — exact (ILP) GAC board builder.

Replaces the greedy "defense-first by Hold%" pass in compute_teams.py with a
solver that maximises the quantity that actually decides a GAC round.

THE OBJECTIVE
-------------
A round is won on net banners:

    net = (banners I take on offense) - (banners they take on my defense)
        ~ SUM over my offense squads of  P(clear)
        + SUM over my defense squads of  P(hold)

Both terms are probabilities of a successful outcome per squad, so they are in
the same units and add. That makes the board a weighted set-packing problem:
pick D defense squads and D offense squads, no unit used twice, maximising the
sum of their rates. `scipy.optimize.milp` (HiGHS) solves it exactly.

Why this beats greedy: greedy fills defense first by Hold%, so an 18%-hold wall
can consume the units of a 90%-win attacker. The solver sees that trade.

Rates may be adjusted first (see DURABILITY in board_config.py) so that a squad
propped up by a datacron that is about to rotate is not treated as durable.
"""
import os
from collections import defaultdict

import numpy as np
from scipy.optimize import milp, LinearConstraint, Bounds

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def solve(defense_pool, offense_pool, n_def, n_off, forced_off_leaders=(),
          forced_def_leaders=(), reserved_off_units=()):
    """Pick n_def defense + n_off offense squads, unit-disjoint, max total rate.

    Pools are lists of {"rate": int, "units": [baseId, ...], ...}. Returns
    (chosen_defense, chosen_offense) as sublists of the pools.

    forced_off_leaders / forced_def_leaders: baseIds that, if used at all, must
    be used on that side. Used to encode hard doctrine (e.g. an attack-only GL)
    without hand-picking the squad.
    """
    cand = ([("def", i, s) for i, s in enumerate(defense_pool)]
            + [("off", i, s) for i, s in enumerate(offense_pool)])
    n = len(cand)
    if not n:
        return [], []

    # `value` is in BANNERS (see board_config.price): banners earned for an offense
    # squad, banners denied plus gate share for a defense squad. Both sides are
    # therefore the same currency and genuinely add. `rate` is the pre-2026-08
    # fallback for callers that have not been repriced (Territory War).
    cost = np.array([-float(s.get("value", s["rate"])) for _, _, s in cand])  # milp minimises

    rows, lb, ub = [], [], []

    def add(coeffs, lo, hi):
        rows.append(coeffs)
        lb.append(lo)
        ub.append(hi)

    # exactly n_def defense squads and n_off offense squads
    add([1.0 if side == "def" else 0.0 for side, _, _ in cand], n_def, n_def)
    add([1.0 if side == "off" else 0.0 for side, _, _ in cand], n_off, n_off)

    # each unit used at most once across the whole format
    by_unit = defaultdict(list)
    for j, (_, _, s) in enumerate(cand):
        for u in s["units"]:
            by_unit[u].append(j)
    for js in by_unit.values():
        if len(js) > 1:
            v = [0.0] * n
            for j in js:
                v[j] = 1.0
            add(v, 0, 1)

    # doctrine: individual units the defense may not claim. Not the same thing as a
    # forced leader — this is for a SUPPORT unit that is the irreplaceable fifth of
    # an attack squad the board cannot do without. Without it the solver will happily
    # spend the unit on a wall worth 2 more banners and silently delete a 90% clear.
    for u in reserved_off_units:
        js = [j for j, (side, _, s) in enumerate(cand) if side == "def" and u in s["units"]]
        if js:
            v = [0.0] * n
            for j in js:
                v[j] = 1.0
            add(v, 0, 0)

    # doctrine: a forced-side leader's units may only appear on that side
    for leaders, banned_side in ((forced_off_leaders, "def"),
                                 (forced_def_leaders, "off")):
        for lead in leaders:
            js = [j for j, (side, _, s) in enumerate(cand)
                  if side == banned_side and lead in s["units"]]
            if js:
                v = [0.0] * n
                for j in js:
                    v[j] = 1.0
                add(v, 0, 0)

    A = np.array(rows, dtype=float)
    res = milp(c=cost,
               constraints=LinearConstraint(A, np.array(lb), np.array(ub)),
               integrality=np.ones(n),
               bounds=Bounds(0, 1))
    if not res.success:
        raise RuntimeError(f"ILP failed: {res.message}")

    pick = res.x > 0.5
    chosen_def = [s for j, (side, _, s) in enumerate(cand) if pick[j] and side == "def"]
    chosen_off = [s for j, (side, _, s) in enumerate(cand) if pick[j] and side == "off"]
    return chosen_def, chosen_off


def add_bench(chosen_def, chosen_off, offense_pool, max_bench):
    """Fill out the offense list with extra unit-disjoint squads.

    These cost nothing once the core is fixed (their units are otherwise idle),
    so they are pure upside: alternatives when a matchup is bad or a first
    attempt fails.
    """
    used = {u for s in chosen_def + chosen_off for u in s["units"]}
    chosen_keys = {tuple(s["units"]) for s in chosen_off}
    bench = []
    for s in sorted(offense_pool, key=lambda x: (-x.get("value", x["rate"]), -x["seenN"])):
        if len(bench) >= max_bench:
            break
        if tuple(s["units"]) in chosen_keys:
            continue
        if any(u in used for u in s["units"]):
            continue
        bench.append(s)
        used.update(s["units"])
        chosen_keys.add(tuple(s["units"]))
    return bench


def total(squads):
    return sum(s["rate"] for s in squads)
