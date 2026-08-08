"""Tests for scripts/arena_board.py (Squad Arena defense + climb plan).

Arena is not GAC: one defense squad, no no-repeat rule, a fixed ladder. The tests
below pin the parts where that difference actually bites — the hard game-rule
filters (size / owned-G13 / one Galactic Legend), the three scoring bases
(aggregate -> counters -> shard, best last), and the fact that the climb plan is
allowed to recommend the SAME squad against every opponent.

Everything is handmade and offline: tiny pools built in-file, plus the two example
data files under tests/fixtures/.
"""
import json
import os

import pytest

import arena_board as ab

# The two example data files. tests/fixtures/ is gitignored in this repo, so the
# tests that read them skip rather than fail on a fresh clone — every behaviour
# they cover is ALSO covered by a tmp_path test that always runs. What these two
# add is a check that the committed EXAMPLE files really match the schema the
# module documents, which is the thing that rots silently.
FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")
SHARD_FILE = os.path.join(FIXTURES, "arena_shard_20260808.json")
COUNTERS_FILE = os.path.join(FIXTURES, "arena_squad_counters.json")
needs_examples = pytest.mark.skipif(
    not (os.path.exists(SHARD_FILE) and os.path.exists(COUNTERS_FILE)),
    reason="tests/fixtures/ is gitignored; the example arena files are local-only")

# Two make-believe Galactic Legends, passed explicitly so no test touches the
# swgoh.gg category dump on disk.
GLS = frozenset({"GL_A", "GL_B"})


def _roster(extra=()):
    """Owned G13 roster: A1-A5, B1-B5, O2-O5, P1-P5 and both GLs.

    `extra` adds (baseId, gear, rt) triples for the ownership/relic tests. `rt` is
    the RAW roster field, so rt=9 is a unit the game displays as Relic 7.
    """
    base = [(b, 13, 9) for b in
            ["A1", "A2", "A3", "A4", "A5", "B1", "B2", "B3", "B4", "B5",
             "O2", "O3", "O4", "O5", "P1", "P2", "P3", "P4", "P5", "GL_A", "GL_B"]]
    return {"units": [{"b": b, "n": b, "ct": 1, "g": g, "r": 7, "rt": rt}
                      for b, g, rt in list(base) + list(extra)]}


def _sq(rate, units, seenN=10000):
    return {"rate": rate, "seen": f"{seenN // 1000}K", "seenN": seenN,
            "ban": 0.0, "units": list(units)}


WALL_HI = _sq(50, ["GL_A", "A2", "A3", "A4", "A5"])
WALL_LO = _sq(30, ["B1", "B2", "B3", "B4", "B5"])
ATK_HI = _sq(90, ["GL_B", "O2", "O3", "O4", "O5"])
ATK_LO = _sq(70, ["P1", "P2", "P3", "P4", "P5"])
DEF_POOL = [WALL_HI, WALL_LO]
OFF_POOL = [ATK_HI, ATK_LO]


def _lineups(entries):
    return [tuple(e["units"]) for e in entries]


# --- the relic encoding trap -------------------------------------------------

def test_displayed_relic_is_rt_minus_two():
    # The gate this repo got wrong before: "Relic 6+" is rt>=8, "Relic 7+" is rt>=9.
    assert ab.displayed_relic(8) == 6
    assert ab.displayed_relic(9) == 7
    assert ab.displayed_relic(None) is None
    assert ab.displayed_relic(1) == 0          # pre-G13/locked, never negative


# --- hard game-rule filters --------------------------------------------------

def test_rejects_squads_with_two_galactic_legends():
    two_gl = _sq(99, ["GL_A", "GL_B", "A3", "A4", "A5"])
    out = ab.candidate_defenses(_roster(), [two_gl] + DEF_POOL, gls=GLS)
    assert tuple(two_gl["units"]) not in _lineups(out)   # highest rate, still illegal
    assert _lineups(out) == [tuple(WALL_HI["units"]), tuple(WALL_LO["units"])]


def test_rejects_unowned_and_sub_g13_units():
    unowned = _sq(98, ["NOPE", "A2", "A3", "A4", "A5"])
    g12 = _sq(97, ["C1", "A2", "A3", "A4", "A5"])
    roster = _roster(extra=[("C1", 12, 9)])              # owned but only gear 12
    out = ab.candidate_defenses(roster, [unowned, g12] + DEF_POOL, gls=GLS)
    assert _lineups(out) == [tuple(WALL_HI["units"]), tuple(WALL_LO["units"])]


def test_rejects_wrong_squad_size():
    short = _sq(96, ["A1", "A2", "A3"])
    dup = _sq(95, ["A1", "A1", "A3", "A4", "A5"])        # five slots, four units
    out = ab.candidate_defenses(_roster(), [short, dup] + DEF_POOL, gls=GLS)
    assert _lineups(out) == [tuple(WALL_HI["units"]), tuple(WALL_LO["units"])]


def test_empty_pool_returns_empty_list():
    assert ab.candidate_defenses(_roster(), [], gls=GLS) == []
    assert ab.candidate_defenses(_roster(), [], counters={}, shard=None, gls=GLS) == []


# --- scoring bases -----------------------------------------------------------

def test_aggregate_basis_when_no_shard_and_no_counters():
    out = ab.candidate_defenses(_roster(), DEF_POOL, gls=GLS)
    assert [e["basis"] for e in out] == ["aggregate", "aggregate"]
    assert [e["score"] for e in out] == [50.0, 30.0]     # straight GAC hold%
    assert "league-average proxy" in out[0]["why"]


def test_shard_scores_below_aggregate_when_the_ladder_is_elite():
    # Every opponent on this ladder attacks with the 90% squad, which is far above
    # the pool-average attacker the 50% GAC hold was measured against.
    shard = {"mode": "squad", "opponents": [
        {"rank": 1, "squad": ATK_HI["units"]},
        {"rank": 2, "squad": ATK_HI["units"]}]}
    out = ab.candidate_defenses(_roster(), DEF_POOL, shard=shard,
                                off_pool=OFF_POOL, gls=GLS)
    assert [e["basis"] for e in out] == ["shard", "shard"]
    assert out[0]["score"] < WALL_HI["rate"]
    assert "modelled" in out[0]["why"]


def test_shard_without_offense_pool_degrades_to_the_aggregate_number():
    # No attacker strengths available -> every opponent is an average attacker, so
    # the score collapses back to the published hold. It must not crash or invent.
    shard = {"mode": "squad", "opponents": [{"rank": 1, "squad": ATK_HI["units"]}]}
    out = ab.candidate_defenses(_roster(), DEF_POOL, shard=shard, gls=GLS)
    assert out[0]["basis"] == "shard"
    assert out[0]["score"] == float(WALL_HI["rate"])


def test_counters_basis_overrides_the_aggregate_ranking():
    # B1's wall is measured surviving 90% of 1,000 logged attacks, so it beats a
    # squad whose only evidence is a 50% all-league GAC hold.
    counters = {"B1": [{"attacker": ATK_HI["units"], "win": 10.0, "n": 1000}]}
    out = ab.candidate_defenses(_roster(), DEF_POOL, counters=counters, gls=GLS)
    assert out[0]["units"] == WALL_LO["units"]
    assert out[0]["basis"] == "counters" and out[0]["score"] == 90.0
    assert out[1]["basis"] == "aggregate"    # nothing logged against GL_A's wall


def test_shard_prefers_a_measured_row_over_the_model():
    counters = {"GL_A": [{"attacker": ATK_HI["units"], "win": 1.0, "n": 5000}]}
    shard = {"mode": "squad", "opponents": [{"rank": 1, "squad": ATK_HI["units"]}]}
    out = ab.candidate_defenses(_roster(), [WALL_HI], counters=counters, shard=shard,
                                off_pool=OFF_POOL, gls=GLS)
    assert out[0]["score"] == 99.0           # 100 - the measured 1% attacker win
    assert "1 measured, 0 modelled" in out[0]["why"]


def test_relic_depth_only_breaks_ties():
    deep = _sq(40, ["A1", "A2", "A3", "A4", "A5"])
    shallow = _sq(40, ["B1", "B2", "B3", "B4", "B5"])
    roster = {"units": (
        [{"b": b, "n": b, "ct": 1, "g": 13, "r": 7, "rt": 11} for b in
         ["A1", "A2", "A3", "A4", "A5"]]                       # displayed relic 9
        + [{"b": b, "n": b, "ct": 1, "g": 13, "r": 7, "rt": 9} for b in
           ["B1", "B2", "B3", "B4", "B5"]])}                   # displayed relic 7
    out = ab.candidate_defenses(roster, [shallow, deep], gls=GLS)
    assert [e["relic"] for e in out] == [9.0, 7.0]
    assert [e["score"] for e in out] == [40.0, 40.0]           # relic changed order, not score


def test_auto_penalty_hook_is_wired_but_seeded_empty(monkeypatch):
    assert ab.AUTO_PENALTY == {}, "AUTO_PENALTY must ship empty — see the comment"
    monkeypatch.setattr(ab, "AUTO_PENALTY", {"GL_A": 0.5})
    out = ab.candidate_defenses(_roster(), DEF_POOL, gls=GLS)
    assert out[0]["units"] == WALL_LO["units"]                 # 50 * 0.5 = 25 < 30
    penalised = [e for e in out if e["units"] == WALL_HI["units"]][0]
    assert penalised["score"] == 25.0 and "AUTO_PENALTY x0.50" in penalised["why"]


# --- the matchup model -------------------------------------------------------

def test_calibration_reproduces_the_published_rates_at_pool_average():
    # A single-squad pool on each side makes that squad the average, so the model
    # must return exactly its published number in both directions.
    cal = ab.calibration([_sq(20, ["d1", "d2", "d3", "d4", "d5"])],
                         [_sq(80, ["a1", "a2", "a3", "a4", "a5"])])
    assert round(ab.p_clear(80, 20, cal), 6) == 80.0
    assert round(100 - ab.p_clear(80, 20, cal), 6) == 20.0


def test_calibration_is_none_when_a_pool_is_empty():
    assert ab.calibration([], OFF_POOL) is None
    assert ab.calibration(DEF_POOL, []) is None


def test_measured_matchup_falls_back_to_the_attacking_leader():
    counters = {"B1": [{"attacker": ["GL_B", "X", "Y", "Z", "W"], "win": 60.0, "n": 400}]}
    exact = ab.measured_matchup(counters, ["B1"], ["GL_B", "X", "Y", "Z", "W"])
    assert exact == (60.0, 400, "lineup")
    lead = ab.measured_matchup(counters, ["B1"], ATK_HI["units"])   # same leader only
    assert lead == (60.0, 400, "leader")
    assert ab.measured_matchup(counters, ["B1"], ATK_LO["units"]) is None


# --- climb plan --------------------------------------------------------------

def _shard(opponents, player_rank=10):
    return {"mode": "squad", "player_rank": player_rank, "opponents": opponents}


def test_climb_plan_orders_by_expected_rank_gain():
    shard = _shard([
        {"rank": 9, "name": "Near", "squad": WALL_LO["units"]},
        {"rank": 1, "name": "Top", "squad": WALL_HI["units"]}])
    plan = ab.climb_plan(_roster(), OFF_POOL, shard, def_pool=DEF_POOL, gls=GLS)
    # Nine ranks at a decent chance beats one rank at a slightly better chance.
    assert [o["rank"] for o in plan["opponents"]] == [1, 9]
    assert plan["opponents"][0]["rank_gain"] == 9
    assert plan["player_rank"] == 10 and plan["target_rank"] == 1


def test_climb_plan_reorders_when_counters_say_the_top_rung_is_unwinnable():
    # Same ladder, but every owned squad is measured losing to rank 1's wall.
    counters = {"GL_A": [{"attacker": u["units"], "win": 2.0, "n": 900}
                         for u in (ATK_HI, ATK_LO)]}
    shard = _shard([
        {"rank": 9, "name": "Near", "squad": WALL_LO["units"]},
        {"rank": 1, "name": "Top", "squad": WALL_HI["units"]}])
    plan = ab.climb_plan(_roster(), OFF_POOL, shard, counters=counters,
                         def_pool=DEF_POOL, gls=GLS)
    assert [o["rank"] for o in plan["opponents"]] == [9, 1]
    assert plan["basis"] == "counters"


def test_climb_plan_repeats_one_squad_and_says_so():
    # No no-repeat rule: the best attacker is correct against everyone, and the
    # plan must report that it needs exactly one lineup rather than fake variety.
    shard = _shard([{"rank": r, "squad": WALL_LO["units"]} for r in (1, 2, 3)])
    plan = ab.climb_plan(_roster(), OFF_POOL, shard, def_pool=DEF_POOL, gls=GLS)
    assert plan["distinct_squads"] == 1
    assert plan["squads"] == [ATK_HI["units"]]
    assert all(o["attack"]["units"] == ATK_HI["units"] for o in plan["opponents"])


def test_climb_plan_counts_distinct_squads_when_counters_split_the_matchups():
    # Only measured rows can make one squad right for one wall and wrong for
    # another — the aggregate model is monotone in win%, so it always picks the
    # same attacker. This is the case the counters file exists for.
    counters = {"GL_A": [{"attacker": ATK_HI["units"], "win": 95.0, "n": 800},
                         {"attacker": ATK_LO["units"], "win": 5.0, "n": 800}],
                "B1": [{"attacker": ATK_HI["units"], "win": 2.0, "n": 800},
                       {"attacker": ATK_LO["units"], "win": 99.0, "n": 800}]}
    shard = _shard([{"rank": 1, "squad": WALL_HI["units"]},
                    {"rank": 2, "squad": WALL_LO["units"]}])
    plan = ab.climb_plan(_roster(), OFF_POOL, shard, counters=counters,
                         def_pool=DEF_POOL, gls=GLS)
    assert plan["distinct_squads"] == 2
    assert sorted(plan["squads"]) == sorted([ATK_HI["units"], ATK_LO["units"]])


def test_climb_plan_sinks_opponents_already_below_the_player():
    shard = _shard([{"rank": 20, "name": "Below", "squad": WALL_LO["units"]},
                    {"rank": 3, "name": "Above", "squad": WALL_LO["units"]}])
    plan = ab.climb_plan(_roster(), OFF_POOL, shard, def_pool=DEF_POOL, gls=GLS)
    assert [o["rank"] for o in plan["opponents"]] == [3, 20]
    assert plan["opponents"][1]["rank_gain"] == -10
    assert plan["distinct_squads"] == 1        # only the reachable rung is counted


def test_climb_plan_without_a_shard_is_graceful():
    plan = ab.climb_plan(_roster(), OFF_POOL, None, def_pool=DEF_POOL, gls=GLS)
    assert plan["opponents"] == [] and plan["distinct_squads"] == 0
    assert plan["basis"] == "none" and "no shard capture" in plan["note"]


def test_climb_plan_with_no_fieldable_attacker_is_graceful():
    unowned = _sq(95, ["NOPE1", "NOPE2", "NOPE3", "NOPE4", "NOPE5"])
    shard = _shard([{"rank": 1, "squad": WALL_LO["units"]}])
    plan = ab.climb_plan(_roster(), [unowned], shard, def_pool=DEF_POOL, gls=GLS)
    assert plan["opponents"][0]["attack"] is None
    assert plan["distinct_squads"] == 0 and "no fieldable attack squad" in plan["note"]


def test_climb_plan_without_a_player_rank_orders_by_win_rate():
    shard = {"mode": "squad", "opponents": [
        {"rank": 5, "squad": WALL_HI["units"]},      # tougher wall -> lower win
        {"rank": 6, "squad": WALL_LO["units"]}]}
    plan = ab.climb_plan(_roster(), OFF_POOL, shard, def_pool=DEF_POOL, gls=GLS)
    assert plan["player_rank"] is None
    assert [o["rank"] for o in plan["opponents"]] == [6, 5]
    assert all(o["rank_gain"] is None for o in plan["opponents"])


def test_best_attack_breaks_ties_toward_the_better_evidenced_squad():
    # Same measured 60%: one from this exact lineup, one only from a shared leader.
    counters = {"B1": [{"attacker": ATK_HI["units"], "win": 60.0, "n": 400},
                       {"attacker": ["GL_B", "Q1", "Q2", "Q3", "Q4"],
                        "win": 60.0, "n": 400}]}
    other = _sq(70, ["GL_B", "O2", "O3", "O4", "P5"], seenN=99000)   # bigger sample
    atk = ab.best_attack([other, ATK_HI], WALL_LO["units"], counters=counters)
    assert atk["units"] == ATK_HI["units"] and atk["match"] == "lineup"


def test_shard_opponent_with_no_listed_squad_is_handled():
    shard = _shard([{"rank": 3, "name": "Unscouted"}])
    plan = ab.climb_plan(_roster(), OFF_POOL, shard, def_pool=DEF_POOL, gls=GLS)
    assert plan["opponents"][0]["defense"] == []
    assert plan["opponents"][0]["attack"]["basis"] == "aggregate"
    out = ab.candidate_defenses(_roster(), DEF_POOL, shard=shard, off_pool=OFF_POOL,
                                gls=GLS)
    assert out[0]["score"] == float(WALL_HI["rate"])   # unknown attacker == average


def test_best_attack_uses_the_raw_win_rate_for_an_off_meta_wall():
    atk = ab.best_attack([ATK_HI, ATK_LO], ["UNKNOWN1", "UNKNOWN2"],
                         def_rates=ab.rate_index(DEF_POOL),
                         cal=ab.calibration(DEF_POOL, OFF_POOL))
    assert atk["basis"] == "aggregate" and atk["win"] == 90.0


# --- file loaders ------------------------------------------------------------

def test_load_shard_picks_the_newest_capture_in_the_directory(tmp_path):
    for day, rank in (("20260807", 12), ("20260808", 10)):
        (tmp_path / f"shard_{day}.json").write_text(json.dumps(
            {"captured": f"2026-08-{day[-2:]}T13:00:00Z", "mode": "squad",
             "player_rank": rank,
             "opponents": [{"rank": 1, "name": "A", "gp": 1,
                            "squad": WALL_HI["units"]}]}))
    shard = ab.load_shard(arena_dir=str(tmp_path))
    assert shard["player_rank"] == 10 and shard["captured"].startswith("2026-08-08")


def test_load_counters_percent_conversion_and_thin_row_drop(tmp_path):
    src = tmp_path / "squad_counters.json"
    src.write_text(json.dumps({"B1": [
        {"attacker": ATK_HI["units"], "win": 0.6, "n": 1000},
        {"attacker": ATK_LO["units"], "win": 0.9, "n": 5}]}))     # n=5 is noise
    counters = ab.load_counters(str(src))
    assert [r["win"] for r in counters["B1"]] == [60.0]           # 0-1 -> percent
    assert ab.counters_hold(counters, WALL_LO["units"]) == (40.0, 1000, 1)


@needs_examples
def test_load_shard_reads_the_documented_schema():
    shard = ab.load_shard(SHARD_FILE)
    assert shard["mode"] == "squad" and shard["captured"].endswith("Z")
    assert shard["player_rank"] == 10
    first = shard["opponents"][0]
    assert set(first) >= {"rank", "name", "gp", "squad"}
    assert len(first["squad"]) == ab.SQUAD_SIZE


def test_load_shard_returns_none_for_missing_fleet_or_empty_captures(tmp_path):
    assert ab.load_shard(arena_dir=str(tmp_path)) is None          # no capture at all
    fleet = tmp_path / "shard_20260808.json"
    fleet.write_text(json.dumps({"mode": "fleet", "opponents": [{"rank": 1}]}))
    assert ab.load_shard(str(fleet)) is None                       # wrong mode
    empty = tmp_path / "shard_20260809.json"
    empty.write_text(json.dumps({"mode": "squad", "opponents": []}))
    assert ab.load_shard(str(empty)) is None
    assert ab.load_shard(str(tmp_path / "nope.json")) is None      # unreadable


@needs_examples
def test_load_counters_converts_to_percent_and_drops_thin_rows():
    counters = ab.load_counters(COUNTERS_FILE)
    stranger = counters["STRANGER"]
    assert [r["win"] for r in stranger] == [72.0, 41.0]            # 0-1 -> percent
    assert all(r["n"] >= ab.MIN_COUNTER_N for r in stranger)       # the n=12 row is gone
    hold = ab.counters_hold(counters, ["STRANGER", "X", "Y", "Z", "W"])
    assert round(hold[0], 1) == round(100 - (72 * 1840 + 41 * 960) / 2800, 1)
    assert hold[1] == 2800 and hold[2] == 2


def test_load_counters_returns_none_when_absent_or_all_thin(tmp_path):
    assert ab.load_counters(str(tmp_path / "nope.json")) is None
    thin = tmp_path / "c.json"
    thin.write_text(json.dumps({"STRANGER": [{"attacker": ["A"], "win": 0.5, "n": 3}]}))
    assert ab.load_counters(str(thin)) is None


def test_galactic_legends_comes_from_the_category_dump(tmp_path):
    src = tmp_path / "cats.json"
    src.write_text(json.dumps({"map": {
        "GLLEIA": {"n": "Leia Organa", "cats": ["Galactic Legend", "Leader"]},
        "GREATMOTHERS": {"n": "Great Mothers", "cats": ["Leader", "Nightsister"]}}}))
    gls = ab.galactic_legends(str(src))
    assert gls == frozenset({"GLLEIA"})            # the dump corrects the guess
    # A missing dump must not disable a hard game rule.
    assert "GLLEIA" in ab.galactic_legends(str(tmp_path / "nope.json"))
