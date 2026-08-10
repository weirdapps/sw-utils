"""Tests for scripts/potency_build.py — the potency loadout solver.

Grounded in measurements taken off the live HotUtils dump on 2026-08-10:
  * `statValueDecimal` for a percentage stat is the percentage x100 (CX-2 carried
    potency secondaries of 162 and 183, and his statEffects[17] read 0.03457).
  * A completed potency set (2 mods, both level 15) is worth exactly +15.00pp —
    measured across seven units; PAO with four such mods reads +30.01pp.
"""
import pytest

from potency_build import (
    POTENCY_SET_ID,
    POTENCY_STAT_ID,
    SET_BONUS_PP,
    best_loadout,
    potency_of,
    projected_potency,
    protected_units,
)


def _mod(primary=48, secondaries=(), set_id=1, slot=2, level=15, unit=None):
    return {
        "setId": str(set_id),
        "slot": slot,
        "level": level,
        "unit": unit,
        "primaryStat": {"stat": {"unitStatId": primary, "statValueDecimal": 2400}},
        "secondaryStat": [
            {"stat": {"unitStatId": s, "statValueDecimal": v}} for s, v in secondaries
        ],
    }


class TestPotencyOf:
    def test_potency_primary_is_hundredths_of_a_percent(self):
        assert potency_of(_mod(primary=POTENCY_STAT_ID, slot=7)) == pytest.approx(24.0)

    def test_non_potency_primary_contributes_nothing(self):
        assert potency_of(_mod(primary=48)) == pytest.approx(0.0)

    def test_potency_secondaries_accumulate(self):
        # CX-2's real cross+arrow rolls: 1.62 + 1.83 = 3.45pp
        mod = _mod(secondaries=((POTENCY_STAT_ID, 162), (POTENCY_STAT_ID, 183), (5, 140000)))
        assert potency_of(mod) == pytest.approx(3.45)

    def test_speed_secondary_is_not_mistaken_for_potency(self):
        # Speed uses a different scale entirely; counting it would read as +1400pp.
        assert potency_of(_mod(secondaries=((5, 140000),))) == pytest.approx(0.0)


class TestProtectedUnits:
    """Shapes here mirror the real files, which are NOT uniform:
    `board['5v5']['defense']` is a list of {units: [...]}, `arena['deployed']` is a
    bare list of ids, and `arena['climb']` nests squads under opponents[].attack.
    Over-protecting is the safe direction — there are 13-17 candidate mods per slot.
    """

    def test_characters_in_board_squads_are_protected(self):
        board = {"5v5": {"defense": [{"rate": 50.1, "units": ["LORDVADER", "APPO"]}]}}
        assert protected_units(board, {}, {}) >= {"LORDVADER", "APPO"}

    def test_fleet_ships_expand_to_their_crew(self):
        """Ships take no mods — a fleet's strength is its CREW's mods.

        Darth Maul holds the roster's only 6-dot 30pp potency cross and crews the
        Sith Infiltrator, which flies in 'Fleet - Arena'. A protected set built from
        literal unit ids alone misses him, and the solver would strip the #1 fleet.
        """
        board = {"fleets": {"Fleet - Arena": [{"name": "Leviathan",
                                               "units": ["CAPITALLEVIATHAN", "SITHINFILTRATOR"]}]}}
        crew = {"crew": {"SITHINFILTRATOR": [{"unit": "MAUL", "name": "Darth Maul", "slot": 1}]}}
        assert "MAUL" in protected_units(board, {}, crew)

    def test_bare_id_lists_are_protected(self):
        """arena['deployed'] is a flat list of ids, not a list of squad dicts."""
        assert "CADBANE" in protected_units({}, {"deployed": ["CADBANE", "GREEDO"]}, {})

    def test_squads_nested_under_opponents_are_protected(self):
        arena = {"climb": {"opponents": [
            {"rank": 1, "name": "BobaTeafett",
             "attack": {"units": ["GLLEIA", "CAPTAINREX"], "win": 96.0}}]}}
        assert {"GLLEIA", "CAPTAINREX"} <= protected_units({}, arena, {})

    def test_the_targets_themselves_are_not_protected(self):
        """Scorch and CX-2 sit on 5v5 defense #3, so they appear in the board —
        but their own mods are exactly what we are re-arranging."""
        board = {"5v5": {"defense": [{"units": ["SCORCH", "OPERATIVE", "APPO"]}]}}
        got = protected_units(board, {}, {}, targets=("SCORCH", "OPERATIVE"))
        assert "SCORCH" not in got
        assert "OPERATIVE" not in got
        assert "APPO" in got

    def test_lowercase_and_short_strings_are_not_mistaken_for_unit_ids(self):
        board = {"5v5": {"defense": [{"basis": "shard", "why": "57% mean hold",
                                      "units": ["APPO"]}]}}
        got = protected_units(board, {}, {})
        assert got == {"APPO"}

    def test_baseids_that_start_with_a_digit_are_protected(self):
        """4LOM and 50RT lead with a digit. An id pattern anchored on [A-Z] silently
        misses them — and 4LOM really does fly on 5v5 defense, so the solver would
        have handed out mods off a live board squad and reported 'no squads touched'.
        """
        board = {"5v5": {"defense": [{"units": ["JANGOFETT", "4LOM", "ZUCKUSS"]}]}}
        assert "4LOM" in protected_units(board, {}, {})

    def test_known_ids_filter_out_formatted_numbers(self):
        """Relaxing the pattern to allow a leading digit also swallows the board's
        formatted counts ("29K", "120K"). Intersecting with the real roster is exact
        where a pattern can only ever be a guess."""
        board = {"5v5": {"defense": [{"seen": "29K", "seenN": "120K",
                                      "units": ["APPO", "4LOM"]}]}}
        got = protected_units(board, {}, {}, known_ids={"APPO", "4LOM"})
        assert got == {"APPO", "4LOM"}


class TestSetBonus:
    def test_a_completed_potency_set_is_fifteen_points(self):
        assert SET_BONUS_PP == pytest.approx(15.0)

    def test_potency_set_id_is_seven(self):
        assert POTENCY_SET_ID == 7


def _pool(**per_slot):
    """{slot: [potency_value_in_hundredths, ...]} -> a flat mod list, all potency set."""
    out = []
    for slot, values in per_slot.items():
        for value in values:
            out.append(_mod(secondaries=((POTENCY_STAT_ID, value),),
                            set_id=POTENCY_SET_ID, slot=int(slot.lstrip("s"))))
    return out


class TestBestLoadout:
    def test_picks_the_highest_potency_mod_in_each_slot(self):
        mods = _pool(s2=[100, 500, 300], s3=[200, 900])
        got = best_loadout(mods)
        assert potency_of(got[2]) == pytest.approx(5.0)
        assert potency_of(got[3]) == pytest.approx(9.0)

    def test_only_potency_set_mods_are_chosen(self):
        """A non-set mod would have to beat the 15pp set bonus it breaks, and no
        secondary roll comes close — so the solver never considers them."""
        strong_wrong_set = _mod(secondaries=((POTENCY_STAT_ID, 2000),), set_id=1, slot=2)
        weak_right_set = _mod(secondaries=((POTENCY_STAT_ID, 100),),
                              set_id=POTENCY_SET_ID, slot=2)
        got = best_loadout([strong_wrong_set, weak_right_set])
        assert got[2] is weak_right_set

    def test_a_slot_with_no_candidate_is_absent(self):
        got = best_loadout(_pool(s2=[100]))
        assert set(got) == {2}

    def test_excluded_mods_are_not_offered(self):
        """Scorch and CX-2 compete for the same pool — whatever the first takes
        must be off the table for the second."""
        mods = _pool(s2=[100, 500])
        first = best_loadout(mods)
        second = best_loadout(mods, exclude={id(first[2])})
        assert potency_of(first[2]) == pytest.approx(5.0)
        assert potency_of(second[2]) == pytest.approx(1.0)

    def test_unlevelled_mods_are_skipped(self):
        """The +15pp set bonus is the max-level value; a sub-15 mod does not pay it."""
        low = _mod(secondaries=((POTENCY_STAT_ID, 900),), set_id=POTENCY_SET_ID,
                   slot=2, level=12)
        maxed = _mod(secondaries=((POTENCY_STAT_ID, 100),), set_id=POTENCY_SET_ID,
                     slot=2, level=15)
        assert best_loadout([low, maxed])[2] is maxed


class TestProjectedPotency:
    def test_adds_base_mods_and_one_set_bonus(self):
        loadout = {2: _mod(secondaries=((POTENCY_STAT_ID, 200),), set_id=POTENCY_SET_ID),
                   3: _mod(secondaries=((POTENCY_STAT_ID, 300),), set_id=POTENCY_SET_ID,
                           slot=3)}
        # base 36.0 + (2.00 + 3.00) + one completed set
        assert projected_potency(36.0, loadout) == pytest.approx(36.0 + 5.0 + 15.0)

    def test_an_odd_mod_out_pays_no_set_bonus(self):
        loadout = {2: _mod(secondaries=((POTENCY_STAT_ID, 200),), set_id=POTENCY_SET_ID)}
        assert projected_potency(36.0, loadout) == pytest.approx(38.0)

    def test_six_potency_mods_pay_three_set_bonuses(self):
        loadout = {s: _mod(set_id=POTENCY_SET_ID, slot=s) for s in (2, 3, 4, 5, 6, 7)}
        assert projected_potency(36.0, loadout) == pytest.approx(36.0 + 45.0)
