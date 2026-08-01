"""Tests for the A0 comlink data backbone mapper (scripts/swgoh_data.py).

map_roster() is the pure mapping from a comlink /player response to the
{"units":[{b,n,ct,g,r,rt}]} shape compute_teams.py consumes. It is exercised
offline with synthetic comlink units built from the authoritative openapi
`Unit` schema (definitionId, currentTier, currentRarity, relic.currentTier).
"""
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
