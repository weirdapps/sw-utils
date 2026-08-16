"""Tests for the GAC banner model and the zone placement objective.

The ceiling tests are the important ones: they are anchored on numbers that came
from OUTSIDE this repo. HotUtils' GAC page independently printed "Your max: 2131"
for a Kyber 3v3 round, and swgoh.wiki's published banner components reproduce 1915
for Kyber 5v5. If either constant is ever edited by mistake, these fail.
"""
import gac_place as gp
import gac_score as gs


# --- banner table ------------------------------------------------------------
def test_perfect_first_attempt_clear_matches_the_published_table():
    # 45 + 5*slots - units_deployed, per swgoh.wiki
    assert [gs.battle_banners("5v5", team_size=k) for k in (5, 4, 3, 2, 1)] == [65, 66, 67, 68, 69]
    assert [gs.battle_banners("3v3", team_size=k) for k in (3, 2, 1)] == [57, 58, 59]
    assert [gs.battle_banners("fleet", team_size=k) for k in (7, 6, 5, 4, 3, 2, 1)] == \
        [73, 74, 75, 76, 77, 78, 79]


def test_later_attempts_cost_exactly_20_then_30():
    first = gs.battle_banners("5v5", team_size=5)
    assert first - gs.battle_banners("5v5", team_size=5, attempt=2) == 20
    assert first - gs.battle_banners("5v5", team_size=5, attempt=3) == 30


def test_undersizing_is_worth_one_banner_per_slot_and_no_more():
    """The folklore says undersizing is a big banner source. It is +1 a slot."""
    full = gs.battle_banners("5v5", team_size=5)
    solo = gs.battle_banners("5v5", team_size=1)
    assert solo - full == 4          # four omitted units, one banner each


def test_an_unset_slot_hands_over_the_maximum():
    """"Defeated Enemies: 1 per enemy, includes unset" — so an empty slot pays the
    attacker a solo-clear's worth, which is the most any single battle can pay."""
    assert gs.MAX_BATTLE["5v5"] == 69
    assert gs.MAX_BATTLE["3v3"] == 59
    assert gs.MAX_BATTLE["fleet"] == 79


# --- territory ---------------------------------------------------------------
def test_territory_conquest_formula():
    assert gs.territory_banners("5v5", 4) == 240
    assert gs.territory_banners("3v3", 5) == 260
    assert gs.territory_banners("fleet", 3) == 219


def test_kyber_ceilings_match_the_externally_observed_numbers():
    assert gs.ceiling("5v5") == 1915
    assert gs.ceiling("3v3") == 2131          # HotUtils printed exactly this


def test_conquest_is_about_half_the_score():
    for fmt in ("5v5", "3v3"):
        conquest = sum(gs.zone_conquest(fmt, z) for z in gs.ZONES[fmt])
        assert 0.45 < conquest / gs.ceiling(fmt) < 0.50


# --- zone topology -----------------------------------------------------------
def test_every_lane_has_exactly_one_front_and_one_back():
    for fmt in ("5v5", "3v3"):
        for lane in ("top", "bottom"):
            zs = [z for z in gs.ZONES[fmt] if z["lane"] == lane]
            assert sorted(z["phase"] for z in zs) == [1, 2]


def test_the_fleet_zone_is_a_back_zone():
    """It is gated behind a squad wall, which is why the fleet territory kept
    scoring zero: the front in its lane was never fully conquered."""
    for fmt in ("5v5", "3v3"):
        fleet = [z for z in gs.ZONES[fmt] if z["fleet"]]
        assert len(fleet) == 1
        assert fleet[0]["phase"] == 2


def test_slot_counts_match_the_live_kyber_board():
    assert [z["slots"] for z in gs.ZONES["5v5"]] == [4, 4, 3, 3]
    assert [z["slots"] for z in gs.ZONES["3v3"]] == [5, 5, 3, 5]


def test_a_front_hold_denies_far_more_than_a_back_hold():
    for fmt in ("5v5", "3v3"):
        front = gs.lane_value(fmt, "front_top")
        back = gs.lane_value(fmt, "back_bottom")
        assert front > 2.4 * back


# --- placement objective -----------------------------------------------------
def _squads(holds, ban=45.0):
    return [{"rate": h, "ban": ban, "units": [f"U{i}{j}" for j in range(5)]}
            for i, h in enumerate(holds)]


def test_conquest_odds_rise_with_attempts_and_fall_with_hold():
    assert gp.conquest_odds(50, attempts=1) < gp.conquest_odds(50, attempts=4)
    assert gp.conquest_odds(50) < gp.conquest_odds(10)


def test_a_zone_of_stronger_walls_concedes_less():
    z = gs.zone("5v5", "front_top")
    weak, _ = gp.zone_cost("5v5", z, _squads([10, 10, 10, 10]))
    strong, _ = gp.zone_cost("5v5", z, _squads([50, 50, 50, 50]))
    assert strong < weak


def test_lane_cost_never_double_counts_the_back_zone():
    """The bug this guards: pricing the back zone once inside the front's gate value
    and again as a zone of its own, which pushed the total above the ceiling."""
    placed = {"front_top": _squads([40, 30, 20, 20]),
              "front_bottom": _squads([40, 30, 20, 20]),
              "back_bottom": _squads([15, 15, 15])}
    total = sum(gp.lane_cost("5v5", ln, placed, fleets=[{}, {}, {}])[0]
                for ln in ("top", "bottom"))
    assert total < gs.ceiling("5v5")


def test_the_back_zone_only_costs_you_when_the_front_falls():
    """Make the front unbeatable and the lane's cost must collapse toward the front."""
    solid = {"front_top": _squads([95, 95, 95, 95]), "back_bottom": _squads([1, 1, 1])}
    lc, p_front, fc, bc = gp.lane_cost("5v5", "top", solid, fleets=[{}, {}, {}])
    assert p_front < 0.05
    assert lc < fc + 0.1 * bc


def test_solve_refuses_a_board_that_does_not_fill_every_slot():
    """An unset slot is a free 69 banners, so a short board must be an error, not a
    warning that scrolls past."""
    import pytest
    with pytest.raises(SystemExit):
        gp.solve("5v5", _squads([20] * 9), fleets=[])


def test_solve_fills_exactly_the_map():
    placed, cost, worst = gp.solve("5v5", _squads([50, 40, 35, 30, 25, 22, 20, 18, 16, 15, 12]),
                                   fleets=[{}, {}, {}])
    assert sorted(len(v) for v in placed.values()) == [3, 4, 4]
    assert cost <= worst


# --- doctrine ----------------------------------------------------------------
def test_only_gls_without_an_offense_role_are_allowed_to_wall():
    """The rule the owner argued for and the simulation confirmed: a GL walls only
    if it has no offense row at all. Today that is GL Rey and nobody else. If a
    future meta gives her one, or takes one away from another GL, this fails and the
    doctrine gets re-measured with scripts/gac_doctrine.py rather than drifting."""
    import board_config as cfg
    ALL_GLS = {"JEDIMASTERKENOBI", "GRANDMASTERLUKE", "SITHPALPATINE",
               "SUPREMELEADERKYLOREN", "GLLEIA", "LORDVADER", "GLREY",
               "JABBATHEHUTT", "GLAHSOKATANO"}
    for fmt in ("5v5", "3v3"):
        walls = ALL_GLS - set(cfg.ATTACK_ONLY_BY_FORMAT[fmt])
        assert walls == {"GLREY"}, f"{fmt} lets these GLs wall: {walls}"


def test_gl_rey_still_has_no_offense_row():
    """The single fact the exception rests on. Cheap to check, and it is the thing
    most likely to change under a new meta."""
    import build_board as bb
    _, _, _, _, pools = bb.load_pools()
    for fmt in ("5v5", "3v3"):
        rows = [s for s in pools[(fmt, "off")] if "GLREY" in s["units"]]
        assert not rows, f"GL Rey now has {len(rows)} {fmt} offense rows — re-run gac_doctrine.py"


def test_every_defensive_slot_is_filled_in_the_shipped_board():
    """An unset slot is a free 69 banners. This is the one board property that must
    never regress, whatever the doctrine says."""
    import json
    import os
    b = json.load(open(os.path.join(os.path.dirname(__file__), "..", "data",
                                    "board_result.json")))
    for fmt in ("5v5", "3v3"):
        want = sum(z["slots"] for z in gs.ZONES[fmt] if not z["fleet"])
        assert len(b[fmt]["defense"]) == want
        # and enough offense to conquer everything, with retry depth on top
        need = want + 3
        assert len(b[fmt]["offense"]) > need, \
            f"{fmt}: {len(b[fmt]['offense'])} offense squads for {need} required wins"
