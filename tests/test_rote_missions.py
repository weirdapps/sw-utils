#!/usr/bin/env python3
"""
Tests for scripts/rote_missions.py — the RotE mission map.

The load-bearing test here is test_every_required_unit_is_a_real_base_id. A
mistyped baseId does not raise: rote_ops just reports "required unit X unavailable
(unowned, gated, or already used)", which is indistinguishable from a genuine
roster gap. So the map would quietly tell the player to farm a unit that does not
exist, and nothing downstream would notice.
"""
import json
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import rote_missions as rm            # noqa: E402


@pytest.fixture(scope="module")
def name_map():
    with open(os.path.join(ROOT, "data", "name_type_map.json")) as f:
        return json.load(f)


def _all_missions():
    for phase in sorted(rm.PHASES):
        for m in rm.build(phase)["missions"]:
            yield phase, m


def _all_fleets():
    for phase in sorted(rm.PHASES):
        for f in rm.build(phase)["fleets"]:
            yield phase, f


def test_every_required_unit_is_a_real_base_id(name_map):
    bad = []
    for phase, m in _all_missions():
        for base in m.get("required") or ():
            if base not in name_map:
                bad.append(f"P{phase} {m['planet']}/{m['mission']}: {base}")
    assert bad == [], "unknown baseIds in the mission map: " + "; ".join(bad)


def test_every_required_fleet_ship_is_a_real_base_id(name_map):
    bad = []
    for phase, f in _all_fleets():
        for base in f.get("required") or ():
            if base not in name_map:
                bad.append(f"P{phase} {f['planet']}: {base}")
    assert bad == [], "unknown ship baseIds: " + "; ".join(bad)


def test_faction_tags_exist_in_the_category_catalog():
    # A faction tag that does not exist filters the pool to nothing, so the mission
    # silently becomes unfillable rather than erroring.
    import datacron_exposure as dx
    known = {c for v in dx.load_units().values() for c in (v.get("cats") or ())}
    used = {m["faction"] for _p, m in _all_missions() if m.get("faction")}
    assert used <= known, f"unknown faction tags: {sorted(used - known)}"


def test_alignments_are_catalog_values():
    import datacron_exposure as dx
    known = {v.get("align") for v in dx.load_units().values()} - {None}
    used = {a for _p, m in _all_missions() for a in (m.get("align") or ())}
    assert used <= known, f"unknown alignments: {sorted(used - known)}"


def test_mixed_territories_carry_no_align_key():
    # Deliberate: _mission_pool drops any unit missing from the 340-unit catalog
    # whenever `align` is set, and the roster is 398. A mixed territory has no
    # alignment rule, so the key must be absent rather than list all three.
    for _phase, m in _all_missions():
        if m["alignment"] == "mixed":
            assert "align" not in m, f"{m['planet']}/{m['mission']} should not filter align"


def test_repeated_missions_expand_to_distinct_ids():
    p1 = rm.build(1)["missions"]
    mustafar = [m["mission"] for m in p1 if m["planet"] == "Mustafar"]
    assert mustafar == ["ds_1", "ds_2", "ds_3", "vader"]
    assert len(mustafar) == len(set(mustafar))


def test_bracca_unlock_keeps_its_own_relic_floor_above_the_phase():
    # The one row on the map gated higher than its phase: phase 2 is R6, this is R7.
    p2 = {m["mission"]: m for m in rm.build(2)["missions"]}
    assert p2["unlock_zeffo"]["gate"] == {"relic": 7}
    assert p2["ls_1"]["gate"] == {"relic": 6}
    assert p2["unlock_zeffo"]["slots"] == 2      # both slots are named units


def test_mandalore_bokatan_row_is_gated_at_r9_inside_an_r8_phase():
    p4 = {m["mission"]: m for m in rm.build(4)["missions"]}
    assert p4["bokatan"]["gate"] == {"relic": 9}
    assert p4["mixed"]["gate"] == {"relic": 8}


def test_every_phase_is_present_with_the_documented_relic_floor():
    assert sorted(rm.PHASES) == [1, 2, 3, 4, 5, 6]
    assert [rm.build(p)["relic_floor"] for p in range(1, 7)] == [5, 6, 7, 8, 9, 9]


def test_gaps_sorts_cheapest_first_and_puts_unowned_last():
    roster = {"units": [
        {"b": "QIRA", "ct": 1, "g": 13, "r": 7, "rt": 9},          # R7, needs R8 -> 1
        {"b": "VADER", "ct": 1, "g": 13, "r": 7, "rt": 9},         # R7, needs R9 -> 2
        {"b": "JABBATHEHUTT", "ct": 1, "g": 13, "r": 7, "rt": 12},  # R10, fine
    ]}
    rows = rm.gaps(roster)
    shorts = [r["short"] for r in rows if r["owned"]]
    assert shorts == sorted(shorts), "owned gaps must be cheapest-first"
    assert all(not r["owned"] for r in rows[len(shorts):]), "unowned units sort last"
    assert "JABBATHEHUTT" not in {r["unit"] for r in rows}, "a satisfied gate is not a gap"


def test_gaps_merges_one_unit_that_gates_several_missions():
    roster = {"units": [{"b": "K2SO", "ct": 1, "g": 13, "r": 7, "rt": 9}]}   # R7, needs R9
    rows = [r for r in rm.gaps(roster) if r["unit"] == "K2SO"]
    assert len(rows) == 1, "one row per (unit, gate), not one per mission"
    assert len(rows[0]["missions"]) >= 2
