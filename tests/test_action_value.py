"""Tests for the relic-economy value model.

The anchors here are game rules, not repo opinions:

  * A relic upgrade consumes a FIXED BASKET. You cannot convert a unit with nine of
    the ten materials, so throughput is the MINIMUM over (stock/need) — never the mean.
  * Stores sell in lots (2 for 530, 3 for 795). Only the per-unit rate compares.
  * Scrap points and raid tokens are different units. A minimum taken across them is
    arithmetic on incommensurable quantities, and the first draft of this model did
    exactly that — reporting scrap as "cheapest" because 90 < 250.
  * Roster relic is `rt - 2`. Reading that offset wrong cost a capped raid attempt on
    2026-08-17, and advisor.py carried the same bug in the other direction (02e6842).
"""
import action_value as av


ECON = {
    "relic_recipe": {
        "7": {"credits": 1000000, "impulse_detector": 20, "aeromagnifier": 20},
        "8": {"credits": 1500000, "impulse_detector": 20, "gyrda_keypad": 20},
    },
    "routes": {
        "impulse_detector": [
            {"store": "Guild Activity Store", "currency": "mk3_raid_token", "qty": 2, "cost": 530},
            {"store": "Guild Activity Store", "currency": "mk3_raid_token", "qty": 3, "cost": 600},
            {"store": "Scavenger", "currency": "scrap_points", "qty": 1, "cost": 110},
        ],
        "aeromagnifier": [
            {"store": "Guild Activity Store", "currency": "mk3_raid_token", "qty": 2, "cost": 400},
            {"store": "Weekly Shipment", "currency": "crystals", "qty": 5, "cost": 100},
        ],
        "gyrda_keypad": [],
    },
    "event_only": {"gyrda_keypad": ["Assault Battles"]},
}


def test_basket_sums_every_step_in_the_band():
    """R7->R9 is two upgrades, so a material used in both is needed twice."""
    bask = av.basket(ECON, 7, 9)
    assert bask["impulse_detector"] == 40      # 20 in each step
    assert bask["aeromagnifier"] == 20         # 7->8 only
    assert bask["gyrda_keypad"] == 20          # 8->9 only
    assert bask["credits"] == 2_500_000


def test_basket_rejects_a_backwards_band():
    try:
        av.basket(ECON, 9, 7)
    except ValueError:
        return
    raise AssertionError("converting downward should not be expressible")


def test_unit_cost_prefers_the_better_lot_not_the_smaller_sticker():
    """3-for-600 (200/ea) beats 2-for-530 (265/ea) despite the larger total."""
    costs = av.unit_costs(ECON)
    assert costs["impulse_detector"]["mk3_raid_token"]["unit_cost"] == 200


def test_throughput_is_the_minimum_not_the_average():
    """Nine surplus materials buy nothing when the tenth is empty."""
    bask = {"impulse_detector": 40, "aeromagnifier": 20}
    rate, binding, _ = av.throughput(bask, {"impulse_detector": 4000, "aeromagnifier": 20})
    assert rate == 1.0                    # not the mean of 100 and 1
    assert binding == ["aeromagnifier"]


def test_throughput_reports_ties_as_jointly_binding():
    bask = {"a": 10, "b": 20}
    _, binding, _ = av.throughput(bask, {"a": 10, "b": 20})
    assert binding == ["a", "b"]


def test_missing_stock_is_unknown_rather_than_zero():
    """A partial inventory must degrade honestly, not report a false hard zero."""
    bask = {"impulse_detector": 40, "droid_brain": 20}
    rate, binding, unknown = av.throughput(bask, {"impulse_detector": 400})
    assert unknown == ["droid_brain"]
    assert rate == 10.0 and binding == ["impulse_detector"]


def test_routes_are_never_compared_across_currencies():
    """The regression that mattered: scrap 110 must not beat mk3 200 as a global 'min'.

    Both routes survive, each priced in its own unit, and neither is crowned.
    """
    rows = av.plan_routes({"impulse_detector": 40}, av.unit_costs(ECON))
    opts = rows[0]["options"]
    assert set(opts) == {"mk3_raid_token", "scrap_points"}
    assert opts["mk3_raid_token"]["spend"] == 8000     # 40 * 200
    assert opts["scrap_points"]["spend"] == 4400       # 40 * 110
    assert rows[0]["forced"] is None                   # it has a substitute


def test_a_single_allowed_currency_is_marked_forced():
    """Aeromagnifier's only non-crystal route is Mk III, so Mk III is a forced draw."""
    rows = av.plan_routes({"aeromagnifier": 20}, av.unit_costs(ECON))
    assert rows[0]["forced"] == "mk3_raid_token"


def test_crystal_routes_are_excluded_entirely():
    """Standing owner rule: never spend crystals. Cheapness must not resurrect them."""
    rows = av.plan_routes({"aeromagnifier": 20}, av.unit_costs(ECON))
    assert "crystals" not in rows[0]["options"]


def test_material_with_no_route_is_flagged_event_only():
    rows = av.plan_routes({"gyrda_keypad": 20}, av.unit_costs(ECON))
    assert rows[0]["event_only"] is True and rows[0]["options"] == {}


def test_forced_and_discretionary_demand_are_separated():
    """The allocation rule: reserve a contested currency for what has no substitute."""
    rows = av.plan_routes({"aeromagnifier": 20, "impulse_detector": 40},
                          av.unit_costs(ECON))
    forced, optional = av.currency_demand(rows, "mk3_raid_token")
    assert set(forced) == {"aeromagnifier"}
    assert set(optional) == {"impulse_detector"}


def test_relic_tier_applies_the_rt_minus_two_offset():
    """rt=9 is Relic 7. This is the exact misread that cost a raid attempt."""
    assert av.relic_of({"rt": 9}) == 7
    assert av.relic_of({"rt": 7}) == 5
    assert av.relic_of({"rt": 1}) == 0      # no relic
    assert av.relic_of({}) == 0


def test_shortfall_subtracts_what_is_already_held():
    gap = av.shortfall({"impulse_detector": 40, "credits": 100}, {"impulse_detector": 30}, 1)
    assert gap == {"impulse_detector": 10}   # credits are tracked separately


def test_shipped_economy_file_parses_and_prices_the_real_band():
    """Guards the shipped data: the R7->R9 basket must stay complete and sourced."""
    econ = av.load_economy()
    bask = av.basket(econ, 7, 9)
    assert bask["flawed_signal_data"] == 100      # 45 + 55, the largest line
    assert bask["droid_brain"] == 20
    costs = av.unit_costs(econ)
    total, _, unbuyable = av.basket_cost(bask, costs, "mk3_raid_token")
    assert total == 35300
    assert "droid_brain" in unbuyable and "flawed_signal_data" in unbuyable


def test_material_names_map_onto_opaque_hotutils_ids_by_word():
    """Ids are undocumented and get renamed; word-matching survives a prefix change."""
    ids = ["RELIC_MAT_IMPULSE_DETECTOR", "MOD_SLICING_SALVAGE_TIER05_01",
           "GRIND_AEROMAGNIFIER_V2"]
    assert av.match_material("impulse_detector", ids) == "RELIC_MAT_IMPULSE_DETECTOR"
    assert av.match_material("aeromagnifier", ids) == "GRIND_AEROMAGNIFIER_V2"
    assert av.match_material("droid_brain", ids) is None      # no guess


def test_match_prefers_the_tightest_id_when_several_contain_the_words():
    ids = ["AEROMAGNIFIER", "AEROMAGNIFIER_BUNDLE_LEGACY"]
    assert av.match_material("aeromagnifier", ids) == "AEROMAGNIFIER"


def test_stock_loads_from_the_full_material_dict(tmp_path):
    p = tmp_path / "pull.json"
    p.write_text('{"all_mats": {"RELIC_IMPULSE_DETECTOR": 41, "JUNK": 3}}')
    assert av.load_stock(str(p), ["impulse_detector", "droid_brain"]) == {"impulse_detector": 41}


def test_an_explicit_override_beats_id_matching(tmp_path):
    p = tmp_path / "pull.json"
    p.write_text('{"relic_mats": {"droid_brain": 7}, "all_mats": {"DROID_BRAIN": 999}}')
    assert av.load_stock(str(p), ["droid_brain"]) == {"droid_brain": 7}


def test_absent_stock_file_is_empty_not_an_error():
    assert av.load_stock("/nonexistent/path.json", ["impulse_detector"]) == {}
