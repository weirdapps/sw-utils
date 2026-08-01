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
