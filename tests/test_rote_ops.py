"""Tests for the RotE planner (scripts/rote_ops.py).

Device-free and network-free: everything runs off tests/fixtures/.

The tests that matter most here guard the two things that have actually cost this
account Territory Points:
  * the RELIC ENCODING TRAP — displayed relic is `rt - 2`, so "Relic 6+" is rt >= 8.
    A unit at rt 7 displays R5 and is REJECTED by the game (measured on the
    Geonosians against a "5x Geonosians (Relic 7+)" mission).
  * ordering — a deployed unit can never fill an operation slot again, so anything
    reserved for an operation must stay out of every mission squad.
"""
import json
import os

import pytest

import rote_ops as R

FIX = os.path.join(os.path.dirname(__file__), "fixtures")


@pytest.fixture(scope="module")
def roster():
    with open(os.path.join(FIX, "roster_live_145357294.json")) as f:
        return json.load(f)


@pytest.fixture(scope="module")
def areas():
    return R.load_operations(os.path.join(FIX, "rote_operations_phase2.json"))["areas"]


def _u(b, **kw):
    """A minimal roster unit. Defaults to a G13 character."""
    d = {"b": b, "n": b.title(), "ct": 1, "g": 13, "r": 7, "rt": None}
    d.update(kw)
    return d


def _area(planet, op, filled, slots):
    return {"planet": planet, "operation": op, "slots_total": 15,
            "slots_filled": filled,
            "slots": [{"unit": b, "filled": False, "gate": {"relic": 6}} for b in slots]}


# --- the relic encoding trap -------------------------------------------------------
def test_relic_gate_is_rt_minus_two_not_rt():
    """rt 8 displays R6 and PASSES "Relic 6+"; rt 7 displays R5 and FAILS it."""
    assert R.meets_gate(_u("A", rt=8), {"relic": 6}) is True
    assert R.meets_gate(_u("B", rt=7), {"relic": 6}) is False
    # and one tier up, the same offset: "Relic 7+" is rt >= 9
    assert R.meets_gate(_u("C", rt=9), {"relic": 7}) is True
    assert R.meets_gate(_u("D", rt=8), {"relic": 7}) is False


def test_displayed_relic_floors_unrelicked_and_locked_units_at_zero():
    assert R.displayed_relic(_u("A", rt=None)) == 0     # no relic object
    assert R.displayed_relic(_u("B", rt=1)) == 0        # locked / pre-G13
    assert R.displayed_relic(_u("C", rt=12)) == 10      # JML's tile reads R10
    assert R.meets_gate(_u("D", rt=1), {"relic": 1}) is False


def test_the_gate_key_decides_the_combat_type():
    """Characters are relic-gated and ships star-gated; neither satisfies the other."""
    ship = _u("SHIP", ct=2, g=1, r=7)
    char = _u("CHAR", rt=12, r=7)
    assert R.meets_gate(ship, {"stars": 7}) is True
    assert R.meets_gate(char, {"stars": 7}) is False    # 7 stars, but not a ship
    assert R.meets_gate(ship, {"relic": 6}) is False
    assert R.meets_gate(_u("SHIP6", ct=2, g=1, r=6), {"stars": 7}) is False


def test_unknown_gate_key_raises_rather_than_passing_everything():
    with pytest.raises(ValueError):
        R.meets_gate(_u("A", rt=12), {"gear": 13})


def test_eligible_returns_owned_units_meeting_the_gate_strongest_first():
    r = {"units": [_u("WEAK", rt=8, gp=1000), _u("STRONG", rt=8, gp=9000),
                   _u("SHORT", rt=7, gp=99999), _u("SHIP", ct=2, r=7, gp=50000)]}
    assert [u["b"] for u in R.eligible(r, {"relic": 6})] == ["STRONG", "WEAK"]
    assert [u["b"] for u in R.eligible(r, {"stars": 7})] == ["SHIP"]


# --- operation assignment ----------------------------------------------------------
def test_quota_caps_ten_units_per_operation_area(roster, areas):
    """Geonosis Op6 is 0/15 with 12 units Astra can field. The game allows 10."""
    res = R.assign_operations(roster, areas)
    op6 = [a for a in res["areas"] if a["planet"] == "Geonosis" and a["operation"] == 6][0]
    assert op6["remaining_before"] == 15
    assert len(op6["assign"]) == R.QUOTA_PER_AREA == 10
    assert not op6["completes"]              # 10 of 15 can never complete it alone


def test_deployed_units_are_excluded_entirely(roster, areas):
    """Deployment is irreversible: a deployed unit must not appear in any slot."""
    free = R.assign_operations(roster, areas)
    assert "KYLORENUNMASKED" in free["reserved"]

    res = R.assign_operations(roster, areas, already_deployed={"KYLORENUNMASKED"})
    assert "KYLORENUNMASKED" not in res["reserved"]
    assert all(a["unit"] != "KYLORENUNMASKED" for a in res["assignments"])
    op1 = [a for a in res["areas"] if a["planet"] == "Felucia" and a["operation"] == 1]
    assert op1 == [] or op1[0]["assign"] == []   # the 14/15 slot is now unfillable
    assert res["expected_tp"] < free["expected_tp"]


def test_a_unit_is_spent_once_and_goes_to_the_nearer_operation(roster, areas):
    """KYLORENUNMASKED is named by Felucia Op1 (14/15) and Op2 (11/15).

    This is the real phase-2 situation. He can be spent once; the near-complete
    operation is where the marginal slot is worth most.
    """
    res = R.assign_operations(roster, areas)
    where = [(a["planet"], a["operation"]) for a in res["assignments"]
             if a["unit"] == "KYLORENUNMASKED"]
    assert where == [("Felucia", 1)]


def test_close_to_complete_weighting_changes_the_assignment():
    """Same units, same structure — only the guild-wide fill counts differ.

    One shared unit, two areas, each with only that unit as a candidate. A model
    that just counts filled slots is indifferent here (one slot either way); the
    completion-weighted objective is not, and follows the near-complete operation.
    """
    r = {"units": [_u("SHARED", rt=8)]}

    near_first = [_area("A", 1, 14, ["SHARED"]), _area("B", 1, 3, ["SHARED"])]
    near_second = [_area("A", 1, 3, ["SHARED"]), _area("B", 1, 14, ["SHARED"])]

    a = R.assign_operations(r, near_first)
    b = R.assign_operations(r, near_second)

    assert len(a["assignments"]) == len(b["assignments"]) == 1   # count is identical
    assert a["assignments"][0]["planet"] == "A"                  # ...the CHOICE is not
    assert b["assignments"][0]["planet"] == "B"
    assert a["expected_tp"] == b["expected_tp"]                  # mirror images


def test_completed_and_empty_areas_contribute_nothing(roster, areas):
    res = R.assign_operations(roster, areas)
    op5 = [a for a in res["areas"] if a["planet"] == "Bracca" and a["operation"] == 5][0]
    assert op5["remaining_before"] == 0
    assert op5["assign"] == [] and op5["expected_tp"] == 0
    assert R.assign_operations({"units": []}, areas)["assignments"] == []


def test_the_guild_wide_assumption_is_stated_not_hidden(roster, areas):
    res = R.assign_operations(roster, areas)
    assert "GUILD-WIDE" in res["assumption"]
    assert res["guild_fill_p"] == R.GUILD_SLOT_FILL_P
    # never credited the full 11M for a slot Astra cannot complete alone
    op1 = [a for a in res["areas"] if a["operation"] == 1][0]
    assert 0 < op1["expected_tp"] < R.OPERATION_TP


def test_area_value_rises_with_contribution_and_is_convex():
    v = [R.area_value(6, k) for k in range(7)]
    assert v[0] == 0
    assert all(v[i] < v[i + 1] for i in range(6))          # more slots, more TP
    steps = [v[i + 1] - v[i] for i in range(6)]
    assert all(steps[i] < steps[i + 1] for i in range(5))  # the completing slot pays most
    assert v[6] < R.OPERATION_TP                           # never the whole prize


def test_gross_and_net_differ_by_the_deployment_forgone(roster, areas):
    res = R.assign_operations(roster, areas)
    assert res["forgone_deploy_tp"] > 0
    assert res["net_tp"] == res["expected_tp"] - res["forgone_deploy_tp"]


def test_load_operations_derives_slots_filled_when_the_badge_is_missing(tmp_path):
    p = tmp_path / "operations_9.json"
    p.write_text(json.dumps({"phase": 9, "areas": [{"planet": "X", "operation": 1, "slots": [
        {"unit": "A", "filled": True, "gate": {"relic": 6}},
        {"unit": "B", "filled": False, "gate": {"relic": 6}}]}]}))
    a = R.load_operations(str(p))["areas"][0]
    assert a["slots_total"] == 15 and a["slots_filled"] == 1
    assert R.remaining_slots(a) == 14


# --- readiness / what to farm --------------------------------------------------------
def test_readiness_gaps_rank_by_slots_unlocked_then_shortfall(roster, areas):
    gaps = R.readiness_gaps(roster, areas, within=2)
    by_unit = {g["unit"]: g for g in gaps}

    # Barriss is one relic short of TWO slots -> top of the list, ahead of every
    # single-slot unit. Then single-slot units by cheapest shortfall, and the
    # short-2 pair splits on TP (Bracca Op3 is 3 from done, Geonosis Op2 is 6).
    assert [g["unit"] for g in gaps] == [
        "BARRISSOFFEE", "HERMITYODA", "MG100STARFORTRESSSF17", "POGGLETHELESSER"]
    assert [g["slots"] for g in gaps] == [2, 1, 1, 1]
    assert [g["short"] for g in gaps] == [1, 1, 2, 2]
    assert by_unit["BARRISSOFFEE"]["have"] == 5 and by_unit["BARRISSOFFEE"]["need"] == 6
    assert by_unit["MG100STARFORTRESSSF17"]["tp"] > by_unit["POGGLETHELESSER"]["tp"]

    # ships gap on STARS, not relic
    assert by_unit["MG100STARFORTRESSSF17"]["kind"] == "stars"
    assert by_unit["MG100STARFORTRESSSF17"]["have"] == 5
    assert by_unit["MG100STARFORTRESSSF17"]["need"] == 7


def test_readiness_gaps_exclude_far_misses_unowned_units_and_units_already_fielding(
        roster, areas):
    names = {g["unit"] for g in R.readiness_gaps(roster, areas, within=2)}
    assert "GEONOSIANSPY" not in names      # R3 vs R6 gate: three short, not a plan
    assert "SUNFAC" not in names            # R4 vs R7 gate: three short
    assert "THIRDSISTER" not in names       # unowned entirely
    assert "GLHONDO" not in names           # unowned entirely
    assert "CASSIANANDOR" not in names      # already meets the gate

    wider = {g["unit"] for g in R.readiness_gaps(roster, areas, within=3)}
    assert {"GEONOSIANSPY", "SUNFAC"} <= wider


# --- mission squads --------------------------------------------------------------------
CATALOG = {
    "GL_A": {"n": "GL A", "align": "Dark Side", "cats": ["Galactic Legend", "Sith"]},
    "GL_B": {"n": "GL B", "align": "Dark Side", "cats": ["Galactic Legend", "Sith"]},
    "GL_C": {"n": "GL C", "align": "Light Side", "cats": ["Galactic Legend", "Jedi"]},
    "DS_1": {"n": "DS 1", "align": "Dark Side", "cats": ["Sith"]},
    "DS_2": {"n": "DS 2", "align": "Dark Side", "cats": ["Sith"]},
    "DS_3": {"n": "DS 3", "align": "Dark Side", "cats": ["Geonosian"]},
    "DS_4": {"n": "DS 4", "align": "Dark Side", "cats": ["Geonosian"]},
    "LS_1": {"n": "LS 1", "align": "Light Side", "cats": ["Jedi"]},
}


def _gl_roster():
    """Three GLs, all stronger than any filler, so a naive "take the top 5" would
    put three Galactic Legends in one squad. The game permits exactly one."""
    return {"units": [
        _u("GL_A", rt=12, gp=90_000), _u("GL_B", rt=12, gp=89_000),
        _u("GL_C", rt=12, gp=88_000),
        _u("DS_1", rt=10, gp=40_000), _u("DS_2", rt=10, gp=39_000),
        _u("DS_3", rt=10, gp=38_000), _u("DS_4", rt=10, gp=37_000),
        _u("LS_1", rt=10, gp=36_000)]}


def test_only_one_galactic_legend_per_squad():
    m = [{"planet": "P", "mission": "m1", "kind": "combat", "slots": 5,
          "gate": {"relic": 6}}]
    squad = R.mission_squads(_gl_roster(), m, catalog=CATALOG)[0]
    gls = [b for b in squad["units"] if b in ("GL_A", "GL_B", "GL_C")]
    assert len(gls) == 1
    assert gls == ["GL_A"]                       # and it is the strongest one
    assert len(squad["units"]) == 5 and squad["fillable"]


def test_alignment_and_faction_filters_are_honoured():
    m = [{"planet": "P", "mission": "geo", "kind": "combat", "slots": 5,
          "gate": {"relic": 6}, "faction": "Geonosian"}]
    squad = R.mission_squads(_gl_roster(), m, catalog=CATALOG)[0]
    assert set(squad["units"]) == {"DS_3", "DS_4"}
    assert squad["fillable"] is False and squad["short"] == 3

    m = [{"planet": "P", "mission": "ds", "kind": "combat", "slots": 5,
          "gate": {"relic": 6}, "align": ["Dark Side"]}]
    squad = R.mission_squads(_gl_roster(), m, catalog=CATALOG)[0]
    assert "LS_1" not in squad["units"] and "GL_C" not in squad["units"]


def test_units_reserved_for_operations_are_never_deployed_into_a_mission():
    m = [{"planet": "P", "mission": "m1", "kind": "combat", "slots": 5,
          "gate": {"relic": 6}}]
    squad = R.mission_squads(_gl_roster(), m, reserved={"GL_A", "DS_1"},
                             catalog=CATALOG)[0]
    assert "GL_A" not in squad["units"] and "DS_1" not in squad["units"]
    assert squad["units"][0] == "GL_B"


def test_required_units_are_protected_from_the_missions_that_do_not_need_them():
    """The measured failure: auto-fill spent a gated unit on a mission that did not
    need it. A unit any mission REQUIRES is off-limits to every other mission."""
    missions = [
        {"planet": "P", "mission": "open", "kind": "combat", "slots": 5,
         "gate": {"relic": 6}},
        {"planet": "P", "mission": "gated", "kind": "combat", "slots": 2,
         "gate": {"relic": 6}, "required": ["GL_A", "DS_1"]},
    ]
    rows = {r["mission"]: r for r in R.mission_squads(_gl_roster(), missions,
                                                      catalog=CATALOG)}
    assert set(rows["gated"]["units"]) == {"GL_A", "DS_1"}
    assert rows["gated"]["fillable"]
    assert "GL_A" not in rows["open"]["units"] and "DS_1" not in rows["open"]["units"]


def test_a_missing_required_unit_is_reported_not_silently_dropped():
    missions = [{"planet": "P", "mission": "special", "kind": "special", "slots": 2,
                 "gate": {"relic": 6}, "required": ["GL_A", "NOT_OWNED"]}]
    row = R.mission_squads(_gl_roster(), missions, catalog=CATALOG)[0]
    assert row["units"] == ["GL_A"] and row["fillable"] is False
    assert "NOT_OWNED" in row["note"]


def test_no_unit_is_used_by_two_missions_and_fleets_pay_double():
    missions = [
        {"planet": "P", "mission": "a", "kind": "combat", "slots": 3,
         "gate": {"relic": 6}},
        {"planet": "P", "mission": "b", "kind": "combat", "slots": 3,
         "gate": {"relic": 6}},
        {"planet": "P", "mission": "f", "kind": "fleet", "slots": 1,
         "gate": {"stars": 7}},
    ]
    r = _gl_roster()
    r["units"].append(_u("SHIP_1", ct=2, g=1, r=7, gp=70_000))
    rows = R.mission_squads(r, missions, catalog=CATALOG)
    used = [b for row in rows for b in row["units"]]
    assert len(used) == len(set(used))
    fleet = [row for row in rows if row["kind"] == "fleet"][0]
    assert fleet["units"] == ["SHIP_1"] and fleet["win_tp"] == R.FLEET_WIN_TP
    assert all(row["win_tp"] == R.COMBAT_WIN_TP for row in rows if row["kind"] != "fleet")


# --- the whole phase ---------------------------------------------------------------------
def test_plan_reserves_operations_first_then_missions_then_the_remainder(roster, areas):
    missions = [{"planet": "Geonosis", "mission": "g1", "kind": "combat", "slots": 5,
                 "gate": {"relic": 6}, "align": ["Dark Side", "Neutral"]}]
    p = R.plan(roster, areas, missions=missions)

    assert p["order"][0] == "special missions" and p["order"][2] == "OPERATIONS"
    reserved = set(p["operations"]["reserved"])
    assert reserved                                   # the reservation list exists
    for squad in p["missions"]:
        assert not reserved & set(squad["units"])     # and nothing deploys out of it

    spent = reserved | {b for s in p["missions"] for b in s["units"]}
    assert p["deploy"]["units"] == len(roster["units"]) - len(spent)
    assert p["totals"]["operations_tp"] == p["operations"]["expected_tp"]


def test_plan_excludes_already_deployed_units_from_everything(roster, areas):
    p = R.plan(roster, areas, already_deployed={"KYLORENUNMASKED", "CASSIANANDOR"})
    assert "KYLORENUNMASKED" not in p["operations"]["reserved"]
    assert "CASSIANANDOR" not in p["operations"]["reserved"]
    assert all("CASSIANANDOR" not in s["units"] for s in p["missions"])


# --- faction coherence in the free slots -------------------------------------------
# A leader ability only benefits units of its own faction, so five unrelated G13s
# field one working leader and four bystanders. notes.md 2026-08-12 measured this on
# the live account: a GL with filler bodies went 0-for-5 at 193,800 power while a
# coherent GL squad at similar power won.
COHERENCE_CATALOG = {
    "SITH_LEAD": {"n": "Sith Lead", "align": "Dark Side", "cats": ["Sith"]},
    "SITH_1": {"n": "Sith 1", "align": "Dark Side", "cats": ["Sith"]},
    "SITH_2": {"n": "Sith 2", "align": "Dark Side", "cats": ["Sith"]},
    "LONER_1": {"n": "Loner 1", "align": "Dark Side", "cats": ["Bounty Hunter"]},
    "LONER_2": {"n": "Loner 2", "align": "Dark Side", "cats": ["Empire"]},
    "LONER_3": {"n": "Loner 3", "align": "Dark Side", "cats": ["Droid"]},
}


def _coherence_roster():
    """The two Sith are WEAKER than every loner, so strongest-first would leave them
    on the bench and field an incoherent squad."""
    return {"units": [
        _u("SITH_LEAD", rt=12, gp=90_000),
        _u("LONER_1", rt=10, gp=80_000), _u("LONER_2", rt=10, gp=79_000),
        _u("LONER_3", rt=10, gp=78_000),
        _u("SITH_1", rt=10, gp=40_000), _u("SITH_2", rt=10, gp=39_000)]}


def test_free_slots_prefer_faction_mates_of_the_anchor_over_raw_power():
    m = [{"planet": "P", "mission": "m1", "kind": "combat", "slots": 3,
          "gate": {"relic": 6}}]
    squad = R.mission_squads(_coherence_roster(), m, catalog=COHERENCE_CATALOG)[0]
    assert squad["units"][0] == "SITH_LEAD", "anchor is still the strongest unit"
    assert set(squad["units"]) == {"SITH_LEAD", "SITH_1", "SITH_2"}, \
        "the two weaker Sith beat three stronger loners"


def test_required_units_anchor_the_faction_choice():
    # The mission names a weak Sith; the rest of the squad should follow ITS faction,
    # not the strongest-unit-on-the-roster faction.
    m = [{"planet": "P", "mission": "m1", "kind": "combat", "slots": 3,
          "gate": {"relic": 6}, "required": ["SITH_1"]}]
    squad = R.mission_squads(_coherence_roster(), m, catalog=COHERENCE_CATALOG)[0]
    assert squad["units"][0] == "SITH_1"
    assert set(squad["units"]) == {"SITH_1", "SITH_LEAD", "SITH_2"}


def test_coherence_degrades_to_strongest_first_when_nothing_shares_a_faction():
    roster = {"units": [_u("LONER_1", rt=10, gp=80_000),
                        _u("LONER_2", rt=10, gp=79_000),
                        _u("LONER_3", rt=10, gp=78_000)]}
    m = [{"planet": "P", "mission": "m1", "kind": "combat", "slots": 3,
          "gate": {"relic": 6}}]
    squad = R.mission_squads(roster, m, catalog=COHERENCE_CATALOG)[0]
    assert squad["units"] == ["LONER_1", "LONER_2", "LONER_3"], "power is the tie-break"


def test_one_galactic_legend_rule_survives_the_coherence_fill():
    # All three GLs share the Sith/Jedi tags with the fillers, so a coherence-only
    # rule would happily stack them.
    m = [{"planet": "P", "mission": "m1", "kind": "combat", "slots": 5,
          "gate": {"relic": 6}}]
    squad = R.mission_squads(_gl_roster(), m, catalog=CATALOG)[0]
    gls = [b for b in squad["units"] if b.startswith("GL_")]
    assert len(gls) == 1 and gls == ["GL_A"]


def test_colliding_display_names_are_disambiguated_by_baseid():
    # GLREY and REY are different units both displayed as "Rey"; a printed squad
    # reading "Rey, Rey" looks like a duplicate and risks picking the wrong one.
    cat = {"A": {"n": "Rey", "align": "Light Side", "cats": ["Resistance"]},
           "B": {"n": "Rey", "align": "Light Side", "cats": ["Resistance"]},
           "C": {"n": "BB-8", "align": "Light Side", "cats": ["Resistance"]}}
    roster = {"units": [_u("A", n="Rey", rt=10, gp=90_000),
                        _u("B", n="Rey", rt=10, gp=80_000),
                        _u("C", n="BB-8", rt=10, gp=70_000)]}
    m = [{"planet": "P", "mission": "m1", "kind": "combat", "slots": 3,
          "gate": {"relic": 6}}]
    row = R.mission_squads(roster, m, catalog=cat)[0]
    assert row["names"] == ["Rey [A]", "Rey [B]", "BB-8"]
    assert len(set(row["units"])) == 3, "distinct units, only the label collided"
