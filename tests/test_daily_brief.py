"""Tests for A1 daily brief assembly (scripts/daily_brief.py).

brief_sections() is the pure assembly step: it folds the computed board
(gac_result.json) and the advisor's farm ranking into the section data the
terminal/HTML renderers consume.
"""
import daily_brief


def test_brief_sections_summarizes_board():
    gac = {
        "5v5": {"defense": [0] * 11, "offense": [0] * 15, "gaps": {}, "unique_units": 120},
        "3v3": {"defense": [0] * 15, "offense": [0] * 16, "gaps": {}, "unique_units": 88},
    }
    s = daily_brief.brief_sections(gac, [])
    assert s["board"]["5v5"]["def_count"] == 11
    assert s["board"]["5v5"]["off_count"] == 15
    assert s["board"]["3v3"]["def_count"] == 15
    assert s["board"]["3v3"]["unique"] == 88


def test_brief_sections_takes_top_n_farm():
    farm = [
        {"unit": "THIRDSISTER", "sole_blocker_of": [{"rate": 86, "fmt": "5v5", "persp": "off", "leader": "T"}],
         "also_needed_in": 6, "best_rate": 86},
        {"unit": "X", "sole_blocker_of": [], "also_needed_in": 1, "best_rate": 10},
    ]
    s = daily_brief.brief_sections({}, farm, top_n=1)
    assert len(s["farm"]) == 1
    assert s["farm"][0]["unit"] == "THIRDSISTER"
