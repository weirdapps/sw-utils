"""Tests for scripts/invest_plan.py.

The module's whole claim is that the stated priority order ("Arena, then Grand
Arena, then Rise of the Empire") is a GLOBAL ORDERING OVER UNITS, and that each
resource queue is that ordering filtered. So the tests pin the ordering rules
(tier assignment, best-tier-wins, in-tier tie-break), the one place the two relic
scales meet, and the fact that a missing upstream file thins the plan instead of
breaking it.

Fixtures are inline synthetic dicts, matching test_advisor.py. tests/fixtures/ is
gitignored in this repo, so a committed test must not depend on a file there.
"""
import json

import invest_plan as ip


def _roster(*units):
    """Roster in the swgoh_data.load_roster() shape: {b, n, ct, g, r, rt}."""
    out = []
    for u in units:
        d = {"b": u[0], "n": u[0].title(), "ct": 1, "g": 13, "r": 7, "rt": 12}
        d.update(u[1] if len(u) > 1 else {})
        out.append(d)
    return {"meta": {"pulled": "2026-08-08", "source": "test"}, "units": out}


def _board(**kw):
    """board_result.json skeleton; pass e.g. _board(**{"5v5": {...}})."""
    b = {"5v5": {"defense": [], "offense": []},
         "3v3": {"defense": [], "offense": []},
         "tw": {"defense": [], "offense": []},
         "fleets": {}}
    b.update(kw)
    return b


def _sq(rate, *units):
    return {"rate": rate, "units": list(units)}


# --- tier assignment ---------------------------------------------------------
def test_tiers_follow_the_stated_order():
    board = _board(**{"5v5": {"defense": [_sq(50, "WALL")], "offense": [_sq(96, "ATK")]},
                      "tw": {"defense": [_sq(40, "TWWALL")], "offense": []}})
    arena = {"defense": _sq(0, "ARENADEF"), "offense": [_sq(0, "ARENAOFF")]}
    rote = {"operations": [{"units": ["ROTEONLY"]}]}
    roster = _roster(("WALL",), ("ATK",), ("TWWALL",), ("ARENADEF",),
                     ("ARENAOFF",), ("ROTEONLY",), ("IDLE",))

    tiers = {e["unit"]: e["tier"] for e in ip.priority_units(roster, board, arena, rote)}
    assert tiers == {"ARENADEF": 1, "ARENAOFF": 2, "WALL": 4, "ATK": 5,
                     "TWWALL": 8, "ROTEONLY": 11, "IDLE": 12}


def test_only_the_top_arena_wall_is_tier_1():
    # arena_board.candidate_defenses() ranks EVERY fieldable wall. Only one squad
    # can be parked, so only the top entry may take tier 1.
    arena = {"defense": [{"units": ["BEST_L", "BEST_2"], "score": 40},
                         {"units": ["ALT_L", "ALT_2"], "score": 38}]}
    roster = _roster(("BEST_L",), ("BEST_2",), ("ALT_L",), ("ALT_2",))
    tiers = {e["unit"]: e["tier"] for e in ip.priority_units(roster, arena=arena)}
    assert tiers == {"BEST_L": 1, "BEST_2": 1, "ALT_L": 12, "ALT_2": 12}


def test_arena_climb_reads_squads_and_never_the_opponent_shard():
    # climb.opponents holds OTHER PLAYERS' rosters. Astra owns some of those units
    # too, so reading them would silently promote units he never fields in arena.
    arena = {"climb": {"squads": [["MINE_L", "MINE_2"]],
                       "opponents": [{"rank": 3, "defense": ["RIVALS"],
                                      "attack": {"units": ["MINE_L"], "win": 90}}]}}
    roster = _roster(("MINE_L",), ("MINE_2",), ("RIVALS",))
    tiers = {e["unit"]: e["tier"] for e in ip.priority_units(roster, arena=arena)}
    assert tiers == {"MINE_L": 2, "MINE_2": 2, "RIVALS": 12}


def test_rote_reads_operations_and_missions_but_not_the_deploy_remainder():
    # rote_ops.plan(): operations.assignments are the platoon slots, missions are
    # the combat squads, and deploy is the leftover roster -> already tier 12.
    rote = {"operations": {"assignments": [{"unit": "PLATOON", "planet": "Felucia"}],
                           "reserved": ["PLATOON"]},
            "missions": [{"units": ["COMBAT"], "power": 200000}],
            "deploy": {"units": 180, "top": ["LEFTOVER"]}}
    roster = _roster(("PLATOON",), ("COMBAT",), ("LEFTOVER",))
    out = {e["unit"]: (e["tier"], e["reason"]) for e in ip.priority_units(roster, rote=rote)}
    assert out["PLATOON"] == (11, "RotE operations")
    assert out["COMBAT"] == (11, "RotE combat mission")
    assert out["LEFTOVER"][0] == 12


def test_board_arena_fleet_category_fills_tier_3_without_an_arena_file():
    # arena_result.json is missing; board_result.json's own "Fleet - Arena"
    # category is the documented fallback for the fleet-arena rung.
    board = _board(fleets={"Fleet - Arena": [{"name": "Leviathan", "units": ["CAPLEV"]}],
                           "GAC Fleet - Defense": [{"name": "Chimaera", "units": ["CAPCHI"]}]})
    roster = _roster(("CAPLEV", {"ct": 2, "g": 1, "rt": None}),
                     ("CAPCHI", {"ct": 2, "g": 1, "rt": None}))
    tiers = {e["unit"]: e["tier"] for e in ip.priority_units(roster, board)}
    assert tiers == {"CAPLEV": ip.ARENA_FLEET_TIER, "CAPCHI": ip.GAC_FLEET_TIER}


def test_best_tier_wins_when_a_unit_fills_several_roles():
    # Same unit walls in GAC 5v5 (tier 4), attacks in 3v3 (tier 7) and defends
    # in Squad Arena (tier 1). It must take the arena tier and keep both others
    # visible, and its rate must be the arena rate, not the 96% 3v3 clear.
    board = _board(**{"5v5": {"defense": [_sq(50, "GL")], "offense": []},
                      "3v3": {"defense": [], "offense": [_sq(96, "GL")]}})
    arena = {"defense": _sq(31, "GL")}
    out = ip.priority_units(_roster(("GL",)), board, arena)
    assert out[0]["tier"] == 1
    assert out[0]["rate"] == 31
    assert sorted(out[0]["roles"]) == ["GAC 3v3 offense", "GAC 5v5 defense",
                                       "Squad Arena defense"]


def test_ties_inside_a_tier_break_on_the_strongest_squad_at_that_tier():
    board = _board(**{"5v5": {"defense": [_sq(20, "LOW"), _sq(50, "HIGH")], "offense": []}})
    out = [e["unit"] for e in ip.priority_units(_roster(("LOW",), ("HIGH",)), board)]
    assert out == ["HIGH", "LOW"]


def test_squad_mates_keep_squad_order_so_the_leader_sorts_first():
    # Squad-mates share a rate exactly, so slot is the only non-arbitrary
    # tie-break left; swgoh.gg puts the leader in units[0].
    board = _board(**{"5v5": {"defense": [_sq(50, "ZLEADER", "AFILLER")], "offense": []}})
    out = [e["unit"] for e in ip.priority_units(_roster(("ZLEADER",), ("AFILLER",)), board)]
    assert out == ["ZLEADER", "AFILLER"]      # not alphabetical


def test_units_named_by_a_plan_but_not_owned_are_dropped_and_reported():
    board = _board(**{"5v5": {"defense": [_sq(50, "OWNED", "GHOST")], "offense": []}})
    roster = _roster(("OWNED",))
    assert [e["unit"] for e in ip.priority_units(roster, board)] == ["OWNED"]
    assert ip.unowned_in_plans(roster, board) == ["GHOST"]


# --- the relic encoding trap -------------------------------------------------
def test_displayed_relic_7_means_rt_9():
    # DISPLAYED = rt - 2. This is the assertion that stops the two scales from
    # ever being confused again.
    assert ip.rt_for_displayed_relic(7) == 9
    assert ip.rt_for_displayed_relic(6) == 8          # RotE operations "Relic 6+"
    assert ip.displayed_relic(12) == 10
    assert ip.displayed_relic(None) is None
    assert ip.DEFAULT_TARGET_RT == 9


def test_relic_queue_uses_the_roster_scale_and_keeps_priority_order():
    board = _board(**{"5v5": {"defense": [_sq(50, "WALL")], "offense": [_sq(96, "ATK")]}})
    arena = {"defense": _sq(0, "ARENADEF")}
    roster = _roster(("WALL", {"rt": 8}),        # displayed R6 -> below target
                     ("ATK", {"rt": 9}),         # displayed R7 -> AT target, excluded
                     ("ARENADEF", {"rt": 7}))    # displayed R5 -> below, and tier 1
    priority = ip.priority_units(roster, board, arena)
    q = ip.relic_queue(roster, priority, ip.rt_for_displayed_relic(7))
    assert [e["unit"] for e in q] == ["ARENADEF", "WALL"]   # arena before GAC
    assert q[0]["relic"] == 5 and q[0]["levels_to_go"] == 2
    assert q[1]["rt"] == 8 and q[1]["relic"] == 6


def test_relic_queue_skips_ships_residual_units_and_relicless_units():
    board = _board(**{"5v5": {"defense": [_sq(50, "WALL")], "offense": []}},
                   fleets={"GAC Fleet - Defense": [{"name": "F", "units": ["SHIP"]}]})
    roster = _roster(("WALL", {"rt": 8}),
                     ("SHIP", {"ct": 2, "g": 1, "rt": None}),   # ships have no relic
                     ("PREG13", {"g": 11, "rt": None}),         # no relic object yet
                     ("BENCH", {"rt": 3}))                      # owned but tier 12
    priority = ip.priority_units(roster, board)
    assert [e["unit"] for e in ip.relic_queue(roster, priority)] == ["WALL"]


# --- gear + mods -------------------------------------------------------------
def test_gear_queue_lists_only_sub_g13_board_characters_in_priority_order():
    board = _board(**{"5v5": {"defense": [_sq(50, "WALL")], "offense": []}})
    arena = {"defense": _sq(0, "ARENADEF")}
    roster = _roster(("WALL", {"g": 11}), ("ARENADEF", {"g": 12}),
                     ("FULL", {"g": 13}), ("BENCH", {"g": 9}))
    priority = ip.priority_units(roster, board, arena)
    q = ip.gear_queue(roster, priority)
    assert [e["unit"] for e in q] == ["ARENADEF", "WALL"]
    assert q[1]["tiers_to_go"] == 2


def test_mod_priority_order_is_a_duplicate_free_character_only_ordering():
    board = _board(**{"5v5": {"defense": [_sq(50, "GL"), _sq(30, "WALL")],
                              "offense": [_sq(96, "ATK")]},
                      "3v3": {"defense": [], "offense": [_sq(96, "GL")]}},
                   fleets={"Fleet - Arena": [{"name": "Lev", "units": ["SHIP"]}]})
    roster = _roster(("GL",), ("WALL",), ("ATK",),
                     ("SHIP", {"ct": 2, "g": 1, "rt": None}), ("BENCH",))
    order = ip.mod_priority_order(ip.priority_units(roster, board))
    assert order == ["GL", "WALL", "ATK"]      # tier 4 by rate, then tier 5
    assert len(order) == len(set(order))       # GL is on two boards, listed once
    assert "SHIP" not in order                 # ships take no mods
    assert "BENCH" not in order                # tier 12 is not pasted into Grandivory


def test_write_mod_priority_writes_display_names_one_per_line(tmp_path):
    board = _board(**{"5v5": {"defense": [_sq(50, "WALL")], "offense": []}})
    roster = _roster(("WALL",), ("BENCH",))
    path = tmp_path / "mod_priority.txt"
    ip.write_mod_priority(ip.priority_units(roster, board), str(path))
    assert path.read_text().splitlines() == ["Wall"]


# --- graceful degradation ----------------------------------------------------
def test_missing_plan_files_are_named_not_fatal(tmp_path):
    board, arena, rote, missing = ip.load_inputs(
        str(tmp_path / "board_result.json"), str(tmp_path / "arena_result.json"),
        str(tmp_path / "rote_plan.json"))
    assert (board, arena, rote) == (None, None, None)
    assert missing == ["arena_result.json", "board_result.json", "rote_plan.json"]


def test_roster_only_still_produces_a_complete_ordering():
    roster = _roster(("A", {"g": 13}), ("B", {"g": 11}))
    out = ip.priority_units(roster)
    assert [e["tier"] for e in out] == [12, 12]
    assert [e["unit"] for e in out] == ["A", "B"]        # most-developed first
    assert ip.relic_queue(roster, out) == []
    assert ip.gear_queue(roster, out) == []
    assert ip.mod_priority_order(out) == []


def test_build_reports_missing_inputs_and_renders():
    roster = _roster(("A",))
    result = ip.build(roster, missing=["arena_result.json"])
    assert result["meta"]["missing_inputs"] == ["arena_result.json"]
    assert result["meta"]["target_displayed_relic"] == 7
    md = ip.render_markdown(result)
    assert "Missing inputs: arena_result.json" in md


# --- ability catalogue -------------------------------------------------------
def test_ability_queue_drops_unowned_units_and_sorts_by_priority():
    board = _board(**{"5v5": {"defense": [_sq(50, "WALL")], "offense": []}})
    arena = {"defense": _sq(0, "ARENADEF")}
    roster = _roster(("WALL",), ("ARENADEF",), ("BENCH",))
    priority = ip.priority_units(roster, board, arena)
    catalogue = [
        {"unit": "WALL", "ability": "W1", "kind": "zeta", "mode": "grand-arena"},
        {"unit": "GHOST", "ability": "G1", "kind": "omicron", "mode": "territory-war"},
        {"unit": "BENCH", "ability": "B1", "kind": "omicron", "mode": "territory-war"},
        {"unit": "ARENADEF", "ability": "A1", "kind": "zeta", "mode": "squad-arena"},
    ]
    out = ip.ability_queue(priority, catalogue)
    assert [e["unit"] for e in out] == ["ARENADEF", "WALL", "BENCH"]  # GHOST unowned
    assert out[0]["tier"] == 1 and out[0]["name"] == "Arenadef"
    assert out[0]["mode"] == "squad-arena"           # catalogue fields survive


def test_ability_queue_keeps_catalogue_order_for_two_abilities_on_one_unit():
    roster = _roster(("A",))
    priority = ip.priority_units(roster)
    catalogue = [{"unit": "A", "ability": "first"}, {"unit": "A", "ability": "second"}]
    assert [e["ability"] for e in ip.ability_queue(priority, catalogue)] == ["first", "second"]


def test_shipped_catalogue_is_well_formed_and_loads():
    # The catalogue is DERIVED (board role mode x unapplied omicron), never guessed,
    # so the invariant worth pinning is its shape and provenance — not that it is
    # empty. It shipped empty until 2026-08-08; asserting emptiness would now just
    # forbid the module from ever having an answer.
    entries = ip.load_catalogue()
    assert isinstance(entries, list)
    for e in entries:
        assert e["unit"] and e["ability"]
        assert e["kind"] in {"zeta", "omicron"}
        assert e["mode"] in {"squad-arena", "grand-arena", "territory-war",
                             "territory-battle", "conquest"}
    with open(ip.ABILITY_TARGETS) as f:
        assert "_README" in json.load(f)


def test_load_catalogue_accepts_a_bare_list(tmp_path):
    p = tmp_path / "c.json"
    p.write_text(json.dumps([{"unit": "A", "ability": "x"}]))
    assert ip.load_catalogue(str(p)) == [{"unit": "A", "ability": "x"}]


def test_load_catalogue_missing_file_is_empty(tmp_path):
    assert ip.load_catalogue(str(tmp_path / "nope.json")) == []
