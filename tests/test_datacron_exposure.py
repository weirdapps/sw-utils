"""Tests for datacron expiry handling.

The bug these pin: the set table used to carry a hardcoded `days` countdown read off
swgoh.gg on one particular morning, so it was wrong every morning after. By 2026-08-17
it still listed set 30 as live with "1 day" left, eleven days after it had lapsed —
which handed every Sith and Galactic Republic squad a phantom expiry haircut forever.
Expiry is now a DATE and the countdown is derived, so `today` is injected here rather
than read from the clock.
"""
from datetime import date

import datacron_exposure as dx


# Two Old Republic units (set 31) and one Resistance unit (set 33).
UNIT_MAP = {
    "OR_A": {"role": "Attacker", "cats": ["Old Republic"]},
    "OR_B": {"role": "Tank", "cats": ["Old Republic"]},
    "RES": {"role": "Support", "cats": ["Resistance"]},
}
SQUAD_OR = ["OR_A", "OR_B"]


def test_countdown_is_derived_from_the_date_not_frozen():
    s31 = next(s for s in dx.SETS if s["id"] == 31)
    assert dx.days_left(s31, today=date(2026, 9, 1)) == 2
    assert dx.days_left(s31, today=date(2026, 8, 4)) == 30
    assert dx.days_left(s31, today=date(2026, 9, 10)) == -7   # lapsed, and says so


def test_a_lapsed_set_drops_out_of_live_sets():
    after_31 = date(2026, 9, 4)
    live = {s["id"] for s in dx.live_sets(today=after_31)}
    assert 31 not in live and {32, 33} <= live


def test_every_shipped_set_is_still_live_on_the_date_they_were_read():
    """If someone adds an already-dead set to the table, this fails."""
    assert len(dx.live_sets(today=date(2026, 8, 17))) == len(dx.SETS)


def test_no_live_set_supports_sith_or_galactic_republic():
    """The standing consequence: those factions rent nothing, so they lose nothing."""
    affixes = {tag for s in dx.live_sets(today=date(2026, 8, 17)) for _, tag in s["affixes"]}
    assert "Sith" not in affixes and "Galactic Republic" not in affixes


def test_expired_set_stops_producing_a_haircut():
    """The actual bug: a dead set must not keep discounting squads."""
    day_before = date(2026, 9, 2)          # set 31 has 1 day left -> imminent
    mult, why = dx.verdict(SQUAD_OR, UNIT_MAP, today=day_before)
    assert mult < 1.0 and why and "Old Republic" in why

    day_after = date(2026, 9, 4)           # set 31 gone -> nothing to price in
    assert dx.verdict(SQUAD_OR, UNIT_MAP, today=day_after) == (1.0, None)


def test_a_distant_expiry_is_reported_but_not_discounted():
    mult, why = dx.verdict(SQUAD_OR, UNIT_MAP, today=date(2026, 8, 1))
    assert mult == 1.0
    assert why and "leans on" in why


def test_exposure_reports_live_days_remaining():
    exp = dx.exposure(SQUAD_OR, UNIT_MAP, today=date(2026, 8, 17))
    by_tag = {e["tag"]: e for e in exp}
    assert by_tag["Old Republic"]["coverage"] == 1.0
    assert by_tag["Old Republic"]["days"] == 17      # 2026-09-03 minus 2026-08-17
