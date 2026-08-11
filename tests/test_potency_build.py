"""Tests for scripts/potency_build.py — the potency loadout solver.

Grounded in measurements taken off the live HotUtils dump on 2026-08-10:
  * `statValueDecimal` for a percentage stat is the percentage x100 (CX-2 carried
    potency secondaries of 162 and 183, and his statEffects[17] read 0.03457).
  * A completed potency set (2 mods, both level 15) is worth exactly +15.00pp —
    measured across seven units; PAO with four such mods reads +30.01pp.
"""
import json
import os

import pytest

import potency_build
from potency_build import (
    POTENCY_SET_ID,
    POTENCY_STAT_ID,
    SET_BONUS_PP,
    base_potency,
    best_loadout,
    current_loadout,
    equip_payload,
    equipped_on,
    is_noop_response,
    main,
    potency_of,
    projected_potency,
    protected_units,
)


def _mod(primary=48, secondaries=(), set_id=1, slot=2, level=15, unit=None, mod_id=None):
    return {
        "id": mod_id,
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


class TestEquipPayload:
    """`mods/task/equip` takes `units: [{id, modIds}]` — read off the HotUtils bundle,
    where backupCurrentBaseline builds exactly `{id: e.id, modIds: e.mods.map(m => m.id)}`.
    Getting this shape wrong writes real, unpredictable state to a live account.
    """

    def test_payload_is_unit_uuid_and_mod_uuids(self):
        loadout = {2: {"id": "mod-a"}, 7: {"id": "mod-b"}}
        assert equip_payload("unit-1", loadout) == {"id": "unit-1",
                                                    "modIds": ["mod-a", "mod-b"]}

    def test_mod_ids_follow_slot_order(self):
        """Slots come out of a dict; pin the order so a payload diff is readable."""
        loadout = {7: {"id": "cross"}, 2: {"id": "square"}, 4: {"id": "triangle"}}
        assert equip_payload("u", loadout)["modIds"] == ["square", "triangle", "cross"]

    def test_a_units_current_mods_round_trip(self):
        """The restore file is built the same way, from what a unit wears right now."""
        current = [{"id": "m1", "slot": 3}, {"id": "m2", "slot": 2}]
        loadout = {m["slot"]: m for m in current}
        assert equip_payload("u", loadout) == {"id": "u", "modIds": ["m2", "m1"]}


class TestNoopResponse:
    """The write path proves its payload shape by first re-equipping a unit's CURRENT
    mods — an operation that cannot change anything. Recognising the server's
    "nothing to do" answer is therefore the safety interlock, and it is version-
    dependent: the shipped bundle branches on `taskId === 0 && "TASK SKIPPED"`, but
    the live server answers `responseCode 2 / "No mod actions to perform!"`.
    Reading only the bundle's string aborts a perfectly good payload.
    """

    def test_live_servers_empty_diff_is_a_noop(self):
        assert is_noop_response({"responseCode": 2, "responseMessage": "ERROR",
                                 "errorMessage": "No mod actions to perform!"})

    def test_bundles_task_skipped_is_also_a_noop(self):
        assert is_noop_response({"responseCode": 1, "taskId": 0,
                                 "responseMessage": "TASK SKIPPED"})

    def test_an_unresolved_unit_is_not_a_noop(self):
        """This is the failure the interlock exists to catch — a payload whose unit
        key the server cannot resolve."""
        assert not is_noop_response({
            "responseCode": 2, "responseMessage": "ERROR",
            "errorMessage": "Unit 'ZZZZnotarealunitZZZZ' not found on player"})

    def test_a_real_queued_task_is_not_a_noop(self):
        assert not is_noop_response({"responseCode": 1, "taskId": 4711,
                                     "responseMessage": "OK"})


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


class TestEquippedOn:
    """`mod['unit']` is a DICT in the live dump, not a baseId string. Reading it as a
    string makes every mod look unassigned, which would hand the whole roster's mods
    out as 'free' and strip every board squad at once."""

    def test_reads_the_baseid_out_of_the_unit_dict(self):
        assert equipped_on(_mod(unit={"baseId": "PAO", "id": "u-pao"})) == "PAO"

    def test_an_unassigned_mod_has_no_holder(self):
        assert equipped_on(_mod(unit=None)) is None

    def test_a_missing_unit_key_has_no_holder(self):
        assert equipped_on({"slot": 2}) is None


class TestBasePotency:
    def test_baseStats_amount_is_a_fraction_scaled_to_points(self):
        # CX-2's measured base: 0.34 -> 34.0pp.
        unit = {"baseStats": [{"stat": 5, "amount": 255.0},
                              {"stat": POTENCY_STAT_ID, "amount": 0.34}]}
        assert base_potency(unit) == pytest.approx(34.0)

    def test_a_unit_with_no_potency_entry_reads_zero(self):
        assert base_potency({"baseStats": [{"stat": 5, "amount": 255.0}]}) == 0.0


class TestCurrentLoadout:
    """The restore point is built from this, so a miss here is an unrecoverable
    loadout: whatever it fails to record is not put back by --restore."""

    def test_only_this_units_mods_are_collected_keyed_by_slot(self):
        mine2 = _mod(slot=2, mod_id="m-mine-2", unit={"baseId": "SCORCH"})
        mine7 = _mod(slot=7, mod_id="m-mine-7", unit={"baseId": "SCORCH"})
        theirs = _mod(slot=2, mod_id="m-theirs", unit={"baseId": "PAO"})
        free = _mod(slot=3, mod_id="m-free", unit=None)
        got = current_loadout({"baseId": "SCORCH"}, [mine2, theirs, free, mine7])
        assert got == {2: mine2, 7: mine7}

    def test_a_naked_unit_has_an_empty_loadout(self):
        assert current_loadout({"baseId": "SCORCH"}, [_mod(unit={"baseId": "PAO"})]) == {}


# --- the write path -----------------------------------------------------------------
# `--apply` and `--restore` are the only two things in this repo that mutate a live
# game account. Everything below drives main() end to end with the HTTP call replaced
# by a recorder, and asserts on WHAT WOULD HAVE BEEN SENT.

def _unit(base_id, uuid, potency=36.0, base=0.32):
    return {"baseId": base_id, "id": uuid,
            "stats": {"potency": potency},
            "baseStats": [{"stat": POTENCY_STAT_ID, "amount": base}]}


def _potency_mod(mod_id, slot, points, holder=None):
    """A level-15 potency-set mod worth `points` pp, optionally worn by `holder`."""
    return _mod(secondaries=((POTENCY_STAT_ID, int(points * 100)),),
                set_id=POTENCY_SET_ID, slot=slot, mod_id=mod_id,
                unit={"baseId": holder} if holder else None)


@pytest.fixture
def account(tmp_path, monkeypatch):
    """A three-unit account: the target, a PROTECTED board unit wearing the single
    best slot-2 mod, and an idle donor wearing a weaker one.

    APPO is the trap. His mod is strictly the best in the slot, so any solver that
    forgets the board hands it over — and that is the exact failure ("no squads
    touched", while a live 5v5 defense squad is stripped) this script exists to avoid.
    """
    mods = [
        _mod(slot=2, mod_id="m-scorch-old", unit={"baseId": "SCORCH"}),   # off-set
        _potency_mod("m-appo-best", 2, 9.0, holder="APPO"),               # PROTECTED
        _potency_mod("m-pao-ok", 2, 5.0, holder="PAO"),                   # takeable
        _potency_mod("m-free", 3, 4.0),                                   # unassigned
    ]
    units = [_unit("SCORCH", "u-scorch"), _unit("APPO", "u-appo"), _unit("PAO", "u-pao")]

    dump = tmp_path / "dump.json"
    dump.write_text(json.dumps({"data": {
        "summary": {"gameDataAgeUtc": "2026-08-10T09:00:00Z"},
        "units": {"units": units},
        "mods": {"mods": mods}}}))
    board = tmp_path / "board.json"
    board.write_text(json.dumps({"5v5": {"defense": [{"units": ["SCORCH", "APPO"]}]}}))

    (tmp_path / "output").mkdir()
    monkeypatch.chdir(tmp_path)          # main() writes output/potency_restore.json
    monkeypatch.setenv("HU_SID", "sid-123")
    monkeypatch.setenv("HU_UID", "uid-456")

    calls = []

    def record(replies):
        def fake_api(path, body, sid, uid):
            calls.append((path, body, sid, uid))
            return replies[min(len(calls) - 1, len(replies) - 1)]
        monkeypatch.setattr(potency_build, "api", fake_api)
        return calls

    return {"argv": ["--unit", "SCORCH", "--dump", str(dump), "--board", str(board),
                     "--arena", str(tmp_path / "nope.json"),
                     "--crew", str(tmp_path / "nope.json")],
            "record": record, "calls": calls, "tmp": tmp_path}


NOOP = {"responseCode": 2, "responseMessage": "ERROR",
        "errorMessage": "No mod actions to perform!"}
QUEUED = {"responseCode": 1, "taskId": 55247, "responseMessage": "OK"}
UNRESOLVED = {"responseCode": 2, "responseMessage": "ERROR",
              "errorMessage": "Unit 'u-scorch' not found on player"}


class TestApplyIsInert:
    def test_without_apply_nothing_is_sent(self, account):
        calls = account["record"]([QUEUED])
        assert main(account["argv"]) == 0
        assert calls == []

    def test_apply_without_a_session_id_refuses_to_run(self, account, monkeypatch):
        """HU_SID rotates every session. An empty one must stop at argparse, not
        reach the network with no credential."""
        calls = account["record"]([QUEUED])
        monkeypatch.delenv("HU_SID")
        with pytest.raises(SystemExit) as exc:
            main(account["argv"] + ["--apply"])
        assert exc.value.code == 2
        assert calls == []


class TestApplyWritePath:
    def test_a_failed_probe_aborts_before_the_real_write(self, account):
        """The interlock: the shape check re-equips the target's CURRENT mods, which
        the server must refuse as an empty diff. If it answers anything else the
        payload shape is unproven, and NOTHING further may be sent."""
        calls = account["record"]([UNRESOLVED])
        assert main(account["argv"] + ["--apply"]) == 1
        assert len(calls) == 1
        assert calls[0][1]["units"] == [{"id": "u-scorch", "modIds": ["m-scorch-old"]}]

    def test_a_confirmed_probe_is_followed_by_the_solved_loadout(self, account):
        calls = account["record"]([NOOP, QUEUED])
        assert main(account["argv"] + ["--apply"]) == 0
        assert len(calls) == 2
        path, body, sid, uid = calls[1]
        assert path == "mods/task/equip"
        assert body["units"] == [{"id": "u-scorch", "modIds": ["m-pao-ok", "m-free"]}]
        assert body["simulation"] is False
        assert (sid, uid) == ("sid-123", "uid-456")

    def test_a_protected_board_units_mod_is_never_in_the_payload(self, account):
        """m-appo-best is 9.00pp against m-pao-ok's 5.00pp, so it wins on merit and
        loses on safety. APPO is on 5v5 defense."""
        calls = account["record"]([NOOP, QUEUED])
        main(account["argv"] + ["--apply"])
        assert "m-appo-best" not in calls[1][1]["units"][0]["modIds"]

    def test_a_rejected_write_is_a_non_zero_exit(self, account):
        calls = account["record"]([NOOP, {"responseCode": 2, "errorMessage": "nope"}])
        assert main(account["argv"] + ["--apply"]) == 1
        assert len(calls) == 2

    def test_the_restore_point_covers_the_target_and_every_donor(self, account):
        """Written BEFORE the probe, and it must hold each touched unit's mods as they
        were: SCORCH keeps his off-set square, PAO gets his slot-2 mod back."""
        account["record"]([NOOP, QUEUED])
        main(account["argv"] + ["--apply"])
        saved = json.loads((account["tmp"] / "output" / "potency_restore.json").read_text())
        assert saved["captured"] == "2026-08-10T09:00:00Z"
        assert {u["id"]: u["modIds"] for u in saved["units"]} == {
            "u-scorch": ["m-scorch-old"], "u-pao": ["m-pao-ok"]}

    def test_the_restore_point_survives_a_write_that_was_never_sent(self, account):
        """An aborted run still leaves a usable restore file — the mods it describes
        are exactly the ones still equipped."""
        account["record"]([UNRESOLVED])
        main(account["argv"] + ["--apply"])
        assert (account["tmp"] / "output" / "potency_restore.json").exists()


class TestRestorePath:
    def test_restore_replays_the_saved_units_verbatim(self, account):
        saved = {"captured": "2026-08-10T09:00:00Z",
                 "units": [{"id": "u-scorch", "modIds": ["m-scorch-old"]},
                           {"id": "u-pao", "modIds": ["m-pao-ok"]}]}
        path = account["tmp"] / "restore.json"
        path.write_text(json.dumps(saved))
        calls = account["record"]([QUEUED])

        assert main(account["argv"] + ["--restore", str(path)]) == 0
        assert len(calls) == 1
        assert calls[0][0] == "mods/task/equip"
        assert calls[0][1]["units"] == saved["units"]
        assert calls[0][1]["simulation"] is False

    def test_restore_does_not_solve_anything_first(self, account):
        """--restore is a replay, not a re-solve: it must not consult the dump, so it
        still works when the account has moved on."""
        path = account["tmp"] / "restore.json"
        path.write_text(json.dumps({"units": [{"id": "u-pao", "modIds": []}]}))
        calls = account["record"]([QUEUED])
        argv = ["--unit", "SCORCH", "--dump", os.devnull, "--restore", str(path)]
        assert main(argv) == 0
        assert len(calls) == 1

    def test_a_rejected_restore_is_a_non_zero_exit(self, account):
        path = account["tmp"] / "restore.json"
        path.write_text(json.dumps({"units": []}))
        account["record"]([{"responseCode": 2, "errorMessage": "session expired"}])
        assert main(account["argv"] + ["--restore", str(path)]) == 1
