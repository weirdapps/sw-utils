"""Tests for the A0 comlink data backbone mapper (scripts/swgoh_data.py).

map_roster() is the pure mapping from a comlink /player response to the
{"units":[{b,n,ct,g,r,rt}]} shape compute_teams.py consumes. It is exercised
offline with synthetic comlink units built from the authoritative openapi
`Unit` schema (definitionId, currentTier, currentRarity, relic.currentTier).
"""
import json

import swgoh_data as sd

# baseId -> {name, combatType}; combatType 1=character, 2=ship
NAME_TYPE_MAP = {
    "GRANDMASTERLUKE": {"n": "Grand Master Luke Skywalker", "ct": 1},
    "TIEBOMBERIMPERIAL": {"n": "Imperial TIE Bomber", "ct": 2},
}


def _unit(defid, tier=13, rarity=7, relic_tier=None):
    """A comlink rosterUnit using the authoritative openapi field names."""
    u = {"definitionId": defid, "currentTier": tier, "currentRarity": rarity,
         "currentLevel": 85, "skill": []}
    if relic_tier is not None:
        u["relic"] = {"currentTier": relic_tier}
    return u


def test_maps_core_identity_and_gear():
    player = {"name": "Astra", "allyCode": 145357294,
              "rosterUnit": [_unit("GRANDMASTERLUKE:SEVENSTAR", tier=13, rarity=7)]}
    u = sd.map_roster(player, NAME_TYPE_MAP)["units"][0]
    assert u["b"] == "GRANDMASTERLUKE"
    assert u["n"] == "Grand Master Luke Skywalker"
    assert u["ct"] == 1
    assert u["g"] == 13
    assert u["r"] == 7


def test_relic_tier_is_raw_current_tier():
    # file convention (verified live vs 397-unit roster): rt == comlink
    # relic.currentTier verbatim, no offset.
    player = {"rosterUnit": [_unit("GRANDMASTERLUKE:SEVENSTAR", relic_tier=12)]}
    assert sd.map_roster(player, NAME_TYPE_MAP)["units"][0]["rt"] == 12


def test_locked_relic_kept_as_tier_one():
    # pre-G13 units report relic.currentTier == 1 (locked); the file keeps it.
    player = {"rosterUnit": [_unit("GRANDMASTERLUKE:SEVENSTAR", tier=7, relic_tier=1)]}
    assert sd.map_roster(player, NAME_TYPE_MAP)["units"][0]["rt"] == 1


def test_ship_has_no_relic_level():
    player = {"rosterUnit": [_unit("TIEBOMBERIMPERIAL:SEVENSTAR", tier=1, rarity=7)]}
    u = sd.map_roster(player, NAME_TYPE_MAP)["units"][0]
    assert u["ct"] == 2
    assert u["rt"] is None


def test_unknown_baseid_falls_back_to_character():
    player = {"rosterUnit": [_unit("NEWUNIT99:SEVENSTAR")]}
    u = sd.map_roster(player, NAME_TYPE_MAP)["units"][0]
    assert u["n"] == "NEWUNIT99"
    assert u["ct"] == 1


def test_meta_carries_name_and_count():
    player = {"name": "Astra", "allyCode": 145357294,
              "rosterUnit": [_unit("GRANDMASTERLUKE:SEVENSTAR"),
                             _unit("TIEBOMBERIMPERIAL:SEVENSTAR")]}
    meta = sd.map_roster(player, NAME_TYPE_MAP)["meta"]
    assert meta["name"] == "Astra"
    assert meta["count"] == 2


def test_meta_carries_total_gp_from_profile_stat():
    # build_board.py reads roster["meta"]["gp"] and died with KeyError('gp') on
    # every fresh comlink pull — it only ever worked because the saved 08-18 file
    # happened to carry the key. comlink does not give PER-UNIT gp, but it does
    # give the account total in profileStat, so meta.gp is recoverable.
    player = {"name": "Astra", "allyCode": 145357294,
              "rosterUnit": [_unit("GRANDMASTERLUKE:SEVENSTAR")],
              "profileStat": [
                  {"nameKey": "STAT_CHARACTER_GALACTIC_POWER_ACQUIRED_NAME", "value": "9692684"},
                  {"nameKey": "STAT_GALACTIC_POWER_ACQUIRED_NAME", "value": "14569091"},
                  {"nameKey": "STAT_SHIP_GALACTIC_POWER_ACQUIRED_NAME", "value": "4876407"}]}
    meta = sd.map_roster(player, NAME_TYPE_MAP)["meta"]
    assert meta["gp"] == 14569091          # the TOTAL, not the character subtotal
    assert meta["gp_char"] == 9692684
    assert meta["gp_ship"] == 4876407


def test_meta_carries_gac_skill_rating_and_division():
    # The primary goal is a GAC division climb, so the skill rating is the single
    # number that measures it. It is in the player payload and was being dropped.
    player = {"rosterUnit": [],
              "playerRating": {"playerSkillRating": {"skillRating": 3165},
                               "playerRankStatus": {"leagueId": "KYBER", "divisionId": 15}}}
    meta = sd.map_roster(player, NAME_TYPE_MAP)["meta"]
    assert meta["skill_rating"] == 3165
    assert meta["league"] == "KYBER"
    assert meta["division_id"] == 15


def test_meta_gp_is_absent_not_zero_when_profile_stat_is_missing():
    # A missing stat must not read as "this account has 0 GP" — a zero would sail
    # through every downstream comparison and silently mis-rank the whole board.
    meta = sd.map_roster({"rosterUnit": []}, NAME_TYPE_MAP)["meta"]
    assert meta.get("gp") is None
    assert meta.get("skill_rating") is None


def test_load_roster_prefers_comlink(monkeypatch):
    sentinel = {"meta": {"source": "comlink"}, "units": [{"b": "Y"}]}
    monkeypatch.setattr(sd, "get_roster", lambda *a, **k: sentinel)
    assert sd.load_roster("145357294", fallback_file="/nonexistent") is sentinel


def test_load_roster_falls_back_to_file_when_comlink_down(monkeypatch, tmp_path):
    def boom(*a, **k):
        raise ConnectionError("comlink unreachable")
    monkeypatch.setattr(sd, "get_roster", boom)
    f = tmp_path / "roster.json"
    f.write_text(json.dumps({"meta": {}, "units": [{"b": "X", "n": "X", "ct": 1, "g": 13}]}))
    out = sd.load_roster("145357294", fallback_file=str(f))
    assert out["units"][0]["b"] == "X"
    assert out["meta"]["source"] == "file-fallback"


def test_parse_localization_splits_on_first_pipe_only():
    text = "# comment line\nUNIT_TS_NAME|Third Sister\nQUOTE|a|b|c\n\n"
    m = sd._parse_localization(text)
    assert m["UNIT_TS_NAME"] == "Third Sister"
    assert m["QUOTE"] == "a|b|c"          # only the first pipe separates key from value
    assert all(not k.startswith("#") for k in m)


def test_name_map_from_localization_extracts_unit_names():
    loc = {"UNIT_THIRDSISTER_NAME": "Third Sister",
           "UNIT_GLHONDO_NAME": "Pirate King Hondo Ohnaka",
           "SOME_OTHER_KEY": "ignore me",
           "UNIT_BLANK_NAME": ""}
    m = sd.name_map_from_localization(loc)
    assert m["THIRDSISTER"]["n"] == "Third Sister"
    assert m["GLHONDO"]["n"] == "Pirate King Hondo Ohnaka"
    assert "BLANK" not in m                   # empty names skipped
    assert all("UNIT_" not in b for b in m)   # baseId extracted, not the raw key
