"""push_ingame_presets: the RotE payload must actually produce tabs.

`memory/notes.md` told the next session to push `output/rote_squads.json` with this
script before phase 5. It could not: CATEGORY_TO_TAB listed only the GAC and TW
categories, so a RotE payload built ZERO tabs and the run exited silently having
sent nothing. All 14 phase-4 squads were then hand-built at ~10 taps each.
"""
import json
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import push_ingame_presets as p  # noqa: E402


def _payload(rows):
    return [{"cat": c, "n": n, "u": [[b, 0] for b in units]} for c, n, units in rows]


def test_rote_categories_build_one_tab_per_phase(tmp_path):
    f = tmp_path / "rote.json"
    f.write_text(json.dumps(_payload([
        ("TB RotE - P3", "P3 Tatooine jabba", ["JABBATHEHUTT", "EMBO"]),
        ("TB RotE - P3", "P3 Tatooine fennec", ["BOSSK", "FENNECSHAND"]),
        ("TB RotE - P1", "P1 Corellia aphra", ["DOCTORAPHRA", "BT1"]),
    ])))
    plan = p.build(str(f))
    assert [t["tab"] for t in plan] == ["TB RotE - P1", "TB RotE - P3"]
    assert [s["name"] for s in plan[1]["squads"]] == ["Tatooine jabba", "Tatooine fennec"]
    assert plan[0]["squads"][0]["unitBaseIds"] == ["DOCTORAPHRA", "BT1"]


def test_rote_and_gac_categories_coexist(tmp_path):
    f = tmp_path / "mixed.json"
    f.write_text(json.dumps(_payload([
        ("TB RotE - P2", "P2 Bracca wookiee", ["TARFFUL"]),
        ("GAC 3v3 - Defense", "3v3 D01 The Stranger 57%", ["STRANGER"]),
    ])))
    plan = p.build(str(f))
    assert [t["tab"] for t in plan] == ["GAC 3v3 - Defense", "TB RotE - P2"]
    # the GAC branch keeps its own naming rule (format tag and % dropped)
    assert plan[0]["squads"][0]["name"] == "D01 The Stranger"


@pytest.mark.parametrize("raw,want", [
    ("P3 Tatooine jabba", "Tatooine jabba"),
    ("P1 Corellia special MANUAL", "Corellia special"),
    ("P6 Death Star vader [aspir]", "Death Star vader"),
    ("P1 Coruscant jedi_named", "Corus jedi_named"),   # planet shortened, row kept whole
    ("P4 Kashyyyk LS A", "Kashyyyk LS A"),
])
def test_rote_preset_name(raw, want):
    got = p.rote_preset_name(raw)
    assert got == want
    assert len(got) <= p.NAME_MAX


def test_every_shipped_rote_name_fits():
    """The real payload must fit NAME_MAX, or the push aborts on the length guard."""
    path = os.path.join(ROOT, "output", "rote_squads.json")
    if not os.path.exists(path):
        pytest.skip("output/rote_squads.json not generated")
    plan = p.build(path)
    assert plan, "the shipped RotE payload produced no tabs"
    for tab in plan:
        for s in tab["squads"]:
            assert len(s["name"]) <= p.NAME_MAX, (tab["tab"], s["name"])
