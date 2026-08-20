"""Tests for the calibration target ordering.

The anchor here is the attenuator PRICE LADDER, which is a game rule, not a repo
opinion: an attempt on a mod costs >=15 attenuators the first time, >=25 the second,
>=35 the third. The hit rate does not improve with prior attempts, so the same stock
buys strictly more attempts when never-calibrated mods go first. These tests pin that
ordering, and pin the escape hatch that restores the old importance-first order.
"""
import calibrate as cal


def mod(mid, b, spd, rolls, rr, dots=6, tier=5):
    return {"id": mid, "b": b, "spd": spd, "spdRolls": rolls, "rr": rr,
            "dots": dots, "tier": tier}


# rank 0 is the most important unit. "cheap" mods are rr=0 (15 attenuators an attempt).
RANK = {"top": 0, "mid": 10, "low": 20}


def test_cheap_first_attempts_outrank_an_important_but_thrice_rerolled_mod():
    """The whole point: 3 fresh attempts cost less than 2 repeat attempts."""
    mods = [mod("expensive", "top", spd=19, rolls=5, rr=2),   # rank 0 but 35 attenuators
            mod("cheap", "low", spd=11, rolls=3, rr=0)]       # rank 20 but 15 attenuators
    out = cal.rank_candidates(mods, RANK)
    assert [m["id"] for _, _, m in out] == ["cheap", "expensive"]


def test_rank_still_breaks_ties_inside_one_price_tier():
    """Cost first, importance second — not importance discarded."""
    mods = [mod("low", "low", spd=11, rolls=3, rr=0),
            mod("top", "top", spd=11, rolls=3, rr=0)]
    out = cal.rank_candidates(mods, RANK)
    assert [m["id"] for _, _, m in out] == ["top", "low"]


def test_by_rank_restores_the_old_importance_first_order():
    mods = [mod("expensive", "top", spd=19, rolls=5, rr=2),
            mod("cheap", "low", spd=11, rolls=3, rr=0)]
    out = cal.rank_candidates(mods, RANK, by_rank=True)
    assert [m["id"] for _, _, m in out] == ["expensive", "cheap"]


def test_biggest_deficit_wins_within_the_same_price_tier_and_rank():
    mods = [mod("lucky", "mid", spd=12, rolls=3, rr=0),    # deficit 1.5
            mod("unlucky", "mid", spd=9, rolls=3, rr=0)]   # deficit 4.5
    out = cal.rank_candidates(mods, RANK)
    assert [m["id"] for _, _, m in out] == ["unlucky", "lucky"]


def test_only_unlucky_mods_are_eligible():
    """A mod at or above expectation regresses to the mean when rerolled — skip it."""
    above = mod("above", "top", spd=23, rolls=4, rr=0)      # deficit -5.0
    assert cal.rank_candidates([above], RANK) == []


def test_min_deficit_is_honoured():
    marginal = mod("marginal", "top", spd=13, rolls=3, rr=0)   # deficit 0.5
    assert cal.rank_candidates([marginal], RANK, min_deficit=1) == []
    assert len(cal.rank_candidates([marginal], RANK, min_deficit=0)) == 1


def test_ineligible_mods_are_filtered_out():
    off_ladder = mod("off", "not_on_ladder", spd=9, rolls=3, rr=0)
    unequipped = {**mod("bare", "top", spd=9, rolls=3, rr=0), "b": ""}
    five_dot = mod("5dot", "top", spd=9, rolls=3, rr=0, dots=5)
    not_tier_a = mod("6E", "top", spd=9, rolls=3, rr=0, tier=1)
    no_speed = mod("nospd", "top", spd=0, rolls=0, rr=0)
    mods = [off_ladder, unequipped, five_dot, not_tier_a, no_speed]
    assert cal.rank_candidates(mods, RANK) == []


def test_ordering_buys_more_attempts_from_a_fixed_attenuator_stock():
    """The reason the default changed, expressed as the thing we actually care about."""
    cost = {0: 15, 1: 25, 2: 35}
    mods = [mod("a", "top", spd=19, rolls=5, rr=2), mod("b", "mid", spd=21, rolls=5, rr=2),
            mod("c", "low", spd=11, rolls=3, rr=0), mod("d", "low", spd=9, rolls=3, rr=0),
            mod("e", "low", spd=8, rolls=3, rr=0)]

    def attempts_within(order, stock=86):
        n = 0
        for _, _, m in order:
            if stock < cost[m["rr"]]:
                break
            stock -= cost[m["rr"]]
            n += 1
        return n

    assert attempts_within(cal.rank_candidates(mods, RANK)) == 4           # 15*3 + 35 = 80
    assert attempts_within(cal.rank_candidates(mods, RANK, by_rank=True)) == 3   # 35+35+15 = 85
