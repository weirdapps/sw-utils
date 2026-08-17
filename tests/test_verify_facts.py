"""Tests for the roster fact-checker.

The point of this module is to fail loudly, so the tests that matter are the ones
proving it FAILS on the real historical error. A checker that only ever prints "ok"
is a false green, which is worse than no checker: it launders a wrong fact as verified.

Ground truth for the regression: on 2026-08-17 memory/order66-raid-mechanics.md said
the Order 66 squad was "gear 5-7, zero relics". The roster said g=13, rt=7 — Relic 5.
"""
import verify_facts as vf


ROSTER = {
    "IMAGUNDI": {"b": "IMAGUNDI", "g": 13, "rt": 7, "r": 7, "gp": 22303},
    "JOCASTANU": {"b": "JOCASTANU", "g": 12, "rt": 1, "r": 7, "gp": 16656},
    "GRANDINQUISITOR": {"b": "GRANDINQUISITOR", "g": 13, "rt": 9, "r": 7},
    "4LOM": {"b": "4LOM", "g": 11, "rt": 0, "r": 7},
}


def test_relic_offset_is_rt_minus_two():
    """rt=7 is Relic 5, rt=9 is Relic 7. The offset that caused the incident."""
    assert vf.relic_of(ROSTER["IMAGUNDI"]) == 5
    assert vf.relic_of(ROSTER["GRANDINQUISITOR"]) == 7


def test_low_rt_means_no_relic_not_a_negative_one():
    assert vf.relic_of(ROSTER["JOCASTANU"]) == 0
    assert vf.relic_of(ROSTER["4LOM"]) == 0
    assert vf.relic_of({}) == 0


def test_the_2026_08_17_misreading_is_caught():
    """THE REGRESSION. 'gear 5, zero relics' must fail against a G13 R5 unit."""
    ok, why = vf.check_claim({"unit": "IMAGUNDI", "gear": 5, "relic": 0}, ROSTER)
    assert not ok
    assert any("gear is 13" in w for w in why)
    assert any("relic is R5" in w for w in why)


def test_the_corrected_claim_passes():
    ok, _ = vf.check_claim({"unit": "IMAGUNDI", "gear": 13, "relic": 5}, ROSTER)
    assert ok


def test_all_units_checks_every_member_not_just_the_first():
    """A squad-wide claim must not pass because unit one happened to match."""
    claim = {"all_units": ["IMAGUNDI", "JOCASTANU"], "gear": 13, "relic": 5}
    ok, why = vf.check_claim(claim, ROSTER)
    assert not ok
    assert any("JOCASTANU" in w for w in why)


def test_a_unit_absent_from_the_roster_fails_rather_than_silently_passing():
    ok, why = vf.check_claim({"unit": "PROFUNDITY", "relic": 7}, ROSTER)
    assert not ok and "not on the roster" in why[0]


def test_min_relic_passes_at_or_above_the_threshold():
    assert vf.check_claim({"unit": "GRANDINQUISITOR", "min_relic": 7}, ROSTER)[0]
    assert not vf.check_claim({"unit": "GRANDINQUISITOR", "min_relic": 8}, ROSTER)[0]


def test_aggregate_counts_respect_the_drift_tolerance():
    """Piles grow. 152 against a claimed 156 is drift, not a lie — within tolerance."""
    roster = {f"U{i}": {"b": f"U{i}", "rt": 9} for i in range(152)}
    ok, _ = vf.check_claim({"relic_count": 7, "value": 156, "tolerance": 12}, roster)
    assert ok
    ok, why = vf.check_claim({"relic_count": 7, "value": 156, "tolerance": 2}, roster)
    assert not ok and "152" in why[0]


def test_min_relic_count_aggregates_upward():
    roster = {"a": {"b": "a", "rt": 11}, "b": {"b": "b", "rt": 12}, "c": {"b": "c", "rt": 9}}
    ok, _ = vf.check_claim({"min_relic_count": 9, "value": 2, "tolerance": 0}, roster)
    assert ok


def test_run_partitions_passes_from_failures():
    claims = [{"id": "good", "unit": "IMAGUNDI", "relic": 5},
              {"id": "bad", "unit": "IMAGUNDI", "relic": 9}]
    passed, failed = vf.run(claims, ROSTER)
    assert [c["id"] for c, _ in passed] == ["good"]
    assert [c["id"] for c, _ in failed] == ["bad"]


def test_describe_surfaces_the_ambiguous_number_explicitly():
    """The oracle must print BOTH gear and relic, since the card conflates them."""
    line = vf.describe("IMAGUNDI", ROSTER["IMAGUNDI"])
    assert "gear 13" in line and "relic 5" in line and "rt=7" in line


def test_shipped_claims_all_hold_against_the_live_roster():
    """Guards the repo: if a note drifts out of true, this test goes red."""
    import json
    roster = vf.load_roster(vf.latest_roster_path())
    with open(vf.CLAIMS) as f:
        claims = json.load(f)["claims"]
    _, failed = vf.run(claims, roster)
    assert not failed, "\n".join(
        f"{c['id']} [{c['source']}]: {'; '.join(w)}" for c, w in failed)
