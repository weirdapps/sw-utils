#!/usr/bin/env python3
"""Tests for scripts/execute_upgrades.py — the slice/promote allocator.

Owner, 2026-08-20: *"make the best allocation as per our prio order and the mats available.
Do not assume an 'optimal' allocation we cannot reach."*

That is the invariant this file defends. The allocator was failing it in BOTH directions
because the 5-dot cost was a flat 22 averaged over 89 mixed-tier steps:
  * t1 steps really cost 10-15, so it over-charged and silently HID affordable steps —
    38 T05_01 buys three at the low end and it planned one;
  * t4 costs more than 22, so it proposed a step the server refused, twice.
A plan the server rejects is exactly the "optimal allocation we cannot reach" — and a plan
that under-spends stock we hold is the same failure wearing the other hat.

The deeper finding: the cost is NOT a per-tier constant. Two isolated t1 steps the same
afternoon cost 15 and then 10, salvage and credits both scaling 1.5x together. So the table
holds observed MINIMA and the server arbitrates, because a refusal is free and a silent
over-charge is not.
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import execute_upgrades as eu        # noqa: E402


def _mod(i, dots, tier, b, spd=0):
    return {"id": f"m{i}", "b": b, "dots": dots, "tier": tier, "spd": spd,
            "lvl": 15, "rr": 0, "spdRolls": 0, "set": 1, "slot": 1}


def _inputs(mods, mats):
    rank = {"A": 0, "B": 1, "C": 2}
    name = {k: k for k in rank}
    mode = {k: "ARENA" for k in rank}
    return {"mods": mods, "mats": mats}, rank, name, mode


# --- the measured constants -----------------------------------------------------
def test_five_dot_costs_are_the_observed_minimum_not_an_average():
    """The cost VARIES PER MOD: two isolated t1 steps on 2026-08-20 cost 15 then 10, same
    tier and same dots, with credits moving by the same 1.5x. So no static table is exactly
    right, and the table must hold the observed MINIMUM — over-charging silently drops
    upgrades we could afford, while proposing one we cannot costs an API call and no
    materials, because run() retires the budget on responseCode."""
    assert eu.STEP5_SALVAGE[1] == ("T05_01", 10)
    assert eu.STEP5_SALVAGE[2] == ("T05_02", 15)
    assert eu.STEP5_SALVAGE[1][1] < 22, "the old flat average must not creep back"


def test_the_unmeasured_costs_stay_pessimistic():
    """t4 and the promote are REFUSAL BOUNDS, not measurements. They must never drift back
    below the value the server actually rejected, or the planner proposes that call again."""
    assert eu.STEP5_SALVAGE[4][1] > 27, "server refused a t4 step with 27 T05_04 in hand"
    assert eu.PROMO_T0506 > 91, "server refused a promote with 91 T05_06 in hand"


# --- the invariant --------------------------------------------------------------
def test_planner_never_proposes_more_than_the_stock_can_pay_for():
    mats = {"T05_01": 38, "T05_02": 0, "T05_03": 0, "T05_04": 0, "T05_05": 0,
            "T05_06": 0, "PROMO_T5_T6": 0, "T06_01": 0, "T06_02": 0, "T06_03": 0}
    mods = [_mod(i, 5, 1, "A") for i in range(10)]
    d, rank, name, mode = _inputs(mods, mats)
    _s6, s5, _p = eu.build_plan(d, rank, name, mode)
    spent = sum(eu.STEP5_SALVAGE[t][1] for _m, steps in s5 for t in steps)
    assert spent <= int(mats["T05_01"] * eu.MARGIN), f"planned {spent} from {mats['T05_01']}"


def test_the_corrected_cost_unlocks_a_step_the_old_average_hid():
    """38 T05_01 at the observed minimum buys three steps; at the old flat 22 it bought one.
    This is the 'we are not reaching what we could' half of the owner's instruction."""
    mats = {k: 0 for k in ("T05_02", "T05_03", "T05_04", "T05_05", "T05_06",
                           "PROMO_T5_T6", "T06_01", "T06_02", "T06_03")}
    mats["T05_01"] = 38
    mods = [_mod(i, 5, 1, "A") for i in range(5)]
    d, rank, name, mode = _inputs(mods, mats)
    _s6, s5, _p = eu.build_plan(d, rank, name, mode)
    steps = sum(len(s) for _m, s in s5)
    assert steps >= 2, f"old flat 22 planned 1; observed-minimum costing must beat that ({steps})"


def test_a_promote_is_not_planned_on_stock_the_server_already_refused():
    mats = {k: 0 for k in ("T05_01", "T05_02", "T05_03", "T05_04", "T05_05",
                           "T06_01", "T06_02", "T06_03")}
    mats.update({"T05_06": 91, "PROMO_T5_T6": 364})
    d, rank, name, mode = _inputs([_mod(0, 5, 5, "A")], mats)
    _s6, _s5, promote = eu.build_plan(d, rank, name, mode)
    assert promote == [], "91 T05_06 was refused live; planning it again is fiction"


def test_six_dot_slicing_is_all_or_nothing_so_material_is_not_stranded():
    """A partial 6-dot run buys one random secondary bump and strands the material in a mod
    that still cannot be calibrated — 6A is the only tier calibration accepts."""
    one_step = {k: v for k, v in eu.STEP6_BUNDLE.items()}
    d, rank, name, mode = _inputs([_mod(0, 6, 3, "A")], {**one_step, "T05_01": 0})
    s6, _s5, _p = eu.build_plan(d, rank, name, mode)
    assert s6 == [], "tier 3 needs two steps; one step's worth must buy nothing"


# --- the display label has to track the ladder ----------------------------------
def test_mode_labels_match_the_current_invest_plan_tiers():
    """This is the line a human reads to confirm the re-order took effect, so a stale
    mapping defeats the point. Under the old one, GAC 5v5 defence printed as ARENA."""
    assert eu.mode_of(1) == "ARENA"     # the one deployed wall
    assert eu.mode_of(2) == "GAC"       # GAC 5v5 defence — used to say ARENA
    assert eu.mode_of(3) == "GAC"       # GAC 3v3 defence — used to say ARENA
    assert eu.mode_of(5) == "GAC"
    assert eu.mode_of(6) == "ARENA"     # squad-arena climb
    assert eu.mode_of(8) == "TB"
    assert eu.mode_of(10) == "TW"
    assert eu.mode_of(11) == "fleet"
