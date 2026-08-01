"""Tests for A2 opponent scouting (scripts/scout.py)."""
import scout


def test_owned_g13_set_keeps_only_g13_characters():
    roster = {"units": [
        {"b": "A", "ct": 1, "g": 13},
        {"b": "B", "ct": 1, "g": 12},   # under-geared
        {"b": "S", "ct": 2, "g": 13},   # ship
    ]}
    assert scout.owned_g13_set(roster) == {"A"}


def test_fieldable_defenses_excludes_teams_missing_a_unit_and_sorts_by_hold():
    meta_def = [
        {"rate": 50, "units": ["A", "B"], "seenN": 100},
        {"rate": 80, "units": ["A", "C"], "seenN": 50},   # C not owned -> excluded
        {"rate": 30, "units": ["A"], "seenN": 10},
    ]
    out = scout.fieldable_defenses({"A", "B"}, meta_def)
    assert [t["rate"] for t in out] == [50, 30]           # 80 dropped; rest Hold%-desc
