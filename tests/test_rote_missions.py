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


# --- how a mission is PLAYED ---------------------------------------------------
# Added after the 2026-08-19 session threw away the Bracca Zeffo attempt on AUTO.
# The requirements were right and the squad was right; the mission still lost,
# because it cannot be auto-battled at all.
def test_every_special_mission_is_flagged_manual():
    bad = [f"P{p} {m['planet']}/{m['mission']}"
           for p, m in _all_missions() if m["kind"] == "special" and m["auto"]]
    assert bad == [], "specials must never be auto-battled: " + "; ".join(bad)


def test_combat_missions_default_to_auto():
    # Phase-2 combat is community-documented as "mostly auto" and this account went
    # 3-for-3 on it, so auto is the right default — the cost of manual play is time.
    autos = [m for _p, m in _all_missions() if m["kind"] == "combat" and m["auto"]]
    assert len(autos) > 50, "combat missions should default to auto"


def test_tactics_squads_are_real_base_ids(name_map):
    bad = []
    for key, tac in rm.TACTICS.items():
        for base in tac.get("squad") or ():
            if base not in name_map:
                bad.append(f"{key}: {base}")
    assert bad == [], "unknown baseIds in TACTICS: " + "; ".join(bad)


def test_tactics_keys_point_at_missions_that_exist():
    known = {(p, m["planet"], m["mission"]) for p, m in _all_missions()}
    assert set(rm.TACTICS) <= known, \
        f"TACTICS keys with no mission: {sorted(set(rm.TACTICS) - known)}"


def test_the_zeffo_unlock_carries_its_turn_plan_and_never_autos():
    p2 = {m["mission"]: m for m in rm.build(2)["missions"]}
    zeffo = p2["unlock_zeffo"]
    assert zeffo["auto"] is False
    assert zeffo["tactics"]["squad"] == ["CEREJUNDA", "JEDIKNIGHTCAL"]
    # The two facts that decide the fight, both from gaming-fans' walkthrough.
    assert "NEVER AUTO" in zeffo["tactics"]["note"]
    assert "dispel" in zeffo["tactics"]["note"]


# --- TACTICS squads must be playable on THIS roster ----------------------------------
#
# Added 2026-08-20 after two encoded squads turned out to be unfillable. Both came
# straight from a community guide and both named a unit Astra owns but below the
# phase's relic floor:
#   P3 Kashyyyk wookiee -> VANDOR CHEWBACCA at R5 against a R7 floor
#   P3 Tatooine fennec  -> DENGAR at R6 against a R7 floor
# Neither raises anything at runtime: rote_ops just drops the unit and reports the
# row "UNFILLABLE (short 1)", which reads exactly like a genuine roster gap. So a
# guide's lineup would quietly become a plan the account cannot execute.

def _roster_by_base():
    import swgoh_data as sd
    with open(sd.latest_roster_file()) as f:
        return {u["b"]: u for u in json.load(f)["units"]}, sd


def _required_for(phase, planet, mission):
    for ph, m in _all_missions():
        if ph == phase and m["planet"] == planet and m["mission"] == mission:
            return set(m.get("required") or ())
    return set()


def test_tactics_squads_are_fillable_on_the_live_roster():
    """Every FREE slot in a TACTICS squad must be a unit that can actually be played.

    The distinction that matters: a unit the mission REQUIRES sitting below the relic floor
    is a roster gap, and `--gaps` already reports it. A unit we CHOSE for a free slot sitting
    below the floor is a planning bug we introduced, and nothing else catches it — rote_ops
    just drops it and prints "UNFILLABLE (short 1)", which is indistinguishable from the gap.
    Squads that document a target the account cannot field yet opt out with `aspirational`.
    """
    units, sd = _roster_by_base()
    bad = []
    for (phase, planet, mission), tac in sorted(rm.TACTICS.items()):
        if tac.get("aspirational"):
            continue
        floor = rm.PHASES[phase]["relic"]
        required = _required_for(phase, planet, mission)
        for base in tac.get("squad") or ():
            if base in required:
                continue                      # a gap, not a bug — see --gaps
            u = units.get(base)
            if u is None:
                bad.append(f"P{phase} {planet}/{mission}: {base} NOT OWNED")
            elif u.get("ct", 1) == 1 and sd.displayed_relic(u) < floor:
                bad.append(f"P{phase} {planet}/{mission}: {base} is R"
                           f"{sd.displayed_relic(u)}, phase floor is R{floor}")
    assert bad == [], ("TACTICS free slots that cannot be played (pick an eligible unit, or "
                       "mark the entry aspirational and say why):\n  " + "\n  ".join(bad))


def test_aspirational_squads_say_why_they_are_unplayable():
    """`aspirational` must never become a quiet way to silence the fillability test."""
    thin = [k for k, t in rm.TACTICS.items()
            if t.get("aspirational") and "aspirational" not in (t.get("note") or "").lower()]
    assert thin == [], f"aspirational entries whose note does not explain it: {sorted(thin)}"


def test_no_unit_is_double_booked_inside_one_phase():
    """A unit can be spent on exactly one mission per phase, so the plans must not collide."""
    from collections import defaultdict
    clashes = []
    per_phase = defaultdict(lambda: defaultdict(list))
    for (phase, planet, mission), tac in sorted(rm.TACTICS.items()):
        for base in tac.get("squad") or ():
            per_phase[phase][base].append(f"{planet}/{mission}")
    for phase, seen in sorted(per_phase.items()):
        for base, rows in sorted(seen.items()):
            if len(rows) > 1:
                clashes.append(f"P{phase} {base} used by {', '.join(rows)}")
    assert clashes == [], "same unit planned twice in one phase:\n  " + "\n  ".join(clashes)


def test_the_jabba_row_keeps_boba_fett_free_for_fennec():
    """The two Tatooine rows share a Bounty Hunter pool; the guide's whole planning tip
    is to spend Cad Bane on Jabba so Boba Fett is still available for Fennec."""
    jabba = rm.TACTICS[(3, "Tatooine", "jabba")]["squad"]
    fennec = rm.TACTICS[(3, "Tatooine", "fennec")]["squad"]
    assert "BOBAFETT" not in jabba, "Boba must stay out of the Jabba row"
    assert "BOBAFETT" in fennec
    assert "CADBANE" in jabba
