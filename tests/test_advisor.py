"""Tests for A3 advisor (scripts/advisor.py).

farm_priority() turns compute_teams' `gaps` (meta teams you cannot field + which
units are missing) into a ranked "what to farm" list. A unit that is the SOLE
missing piece of a high-rate meta team is the highest-value farm (immediate
unlock); units missing from teams that also need other units rank lower.
"""
import advisor


def _gac(gaps_by_fmt):
    """Minimal gac_result.json shape with the given gaps per format."""
    return {fmt: {"defense": [], "offense": [], "gaps": g, "unique_units": 0}
            for fmt, g in gaps_by_fmt.items()}


def test_sole_blocker_ranks_first():
    gac = _gac({"3v3": {"def": [
        {"rate": 38, "leader": "Hondo", "missing": ["GL Hondo"]},   # sole blocker of 38%
        {"rate": 50, "leader": "X", "missing": ["A", "B"]},         # needs two -> not sole
    ], "off": []}})
    out = advisor.farm_priority(gac)
    assert out[0]["unit"] == "GL Hondo"
    assert out[0]["sole_blocker_of"][0]["rate"] == 38


def test_aggregates_across_formats_and_perspectives():
    gac = _gac({
        "5v5": {"def": [{"rate": 30, "leader": "L1", "missing": ["Third Sister", "Z"]}], "off": []},
        "3v3": {"def": [{"rate": 20, "leader": "L2", "missing": ["Third Sister"]}], "off": []},
    })
    ts = [u for u in advisor.farm_priority(gac) if u["unit"] == "Third Sister"][0]
    assert ts["also_needed_in"] == 2
    assert ts["best_rate"] == 30
    assert len(ts["sole_blocker_of"]) == 1  # only the 3v3 team (single missing unit)


def test_empty_gaps_returns_empty():
    assert advisor.farm_priority(_gac({"5v5": {"def": [], "off": []}})) == []


def test_relic_priority_flags_low_relic_board_units_by_importance():
    # rt is +2: rt 5 -> R3, rt 9 -> R7. Target is the DISPLAYED level.
    gac = {"5v5": {"defense": [{"rate": 86, "units": ["A", "B"]}],
                   "offense": [{"rate": 50, "units": ["A"]}], "gaps": {}}}
    roster = {"units": [{"b": "A", "n": "Ace", "rt": 5}, {"b": "B", "n": "Bee", "rt": 9}]}
    out = advisor.relic_priority(gac, roster, target=7)
    assert [e["unit"] for e in out] == ["Ace"]   # B is R7, already at target -> excluded
    assert out[0]["best_rate"] == 86             # ranked by the strongest team it holds
    assert out[0]["relic"] == 3                  # reported as the game displays it, not rt 5


def test_relic_priority_target_is_the_displayed_level_not_raw_rt():
    """The off-by-two: an R7 unit must NOT count as satisfying a target of R9.

    Reading rt directly made target=9 mean "below R7", so the whole R7 pile — the exact
    thing this account needs to convert — was treated as already done and never surfaced.
    """
    gac = {"5v5": {"defense": [{"rate": 70, "units": ["R7UNIT"]}], "offense": [], "gaps": {}}}
    roster = {"units": [{"b": "R7UNIT", "n": "Parked", "rt": 9}]}   # rt 9 == R7
    assert [e["unit"] for e in advisor.relic_priority(gac, roster, target=9)] == ["Parked"]
    assert advisor.relic_priority(gac, roster, target=7) == []      # already at R7


def test_relic_priority_default_target_is_r9():
    gac = {"5v5": {"defense": [{"rate": 70, "units": ["R8UNIT"]}], "offense": [], "gaps": {}}}
    roster = {"units": [{"b": "R8UNIT", "n": "Eight", "rt": 10}]}   # rt 10 == R8
    out = advisor.relic_priority(gac, roster)
    assert [e["unit"] for e in out] == ["Eight"] and out[0]["relic"] == 8


def test_relic_priority_ignores_units_missing_from_roster():
    gac = {"3v3": {"defense": [{"rate": 40, "units": ["OWNED", "UNOWNED"]}], "offense": [], "gaps": {}}}
    roster = {"units": [{"b": "OWNED", "n": "Owned", "rt": 4}]}
    out = advisor.relic_priority(gac, roster, target=7)
    assert [e["unit"] for e in out] == ["Owned"]  # UNOWNED has no relic data -> skipped
