#!/usr/bin/env python3
"""
gac_score.py — the Grand Arena scoring model, in banners.

WHY THIS FILE EXISTS
--------------------
The board used to be optimised on `Hold% + Win%`. Those are two different
quantities added together as if they were one, and neither is the thing a GAC
round is decided on. A round is decided on BANNERS, and banners come from two
places, not one:

    battle banners      earned per squad you defeat
    territory banners   earned ONLY for conquering a whole territory

Territory banners are 47% of the total (909 of a 1915 ceiling in Kyber 5v5), and
they are all-or-nothing. That single fact reorders everything: one surviving
defensive squad in a front territory is worth far more than its own hold, and one
unbeaten enemy squad on offense forfeits a whole territory plus the lane behind it.

SOURCES
-------
Banner table and territory formulas: swgoh.wiki "Grand Arena Championships"
(raw wikitext, fetched 2026-08-16), corroborated by an itemised EA-forum victory
screen and by the independent constants in KrisKamweru/GAC.Calculator.

Zone topology and the lane-gating rule: read LIVE off Astra's own board via the
HotUtils `gac/get` API on 2026-08-16 (season 82, map 4zone_5v5_ga2_c3s1_82a), and
cross-checked against the wiki text. The gating rule was then verified against six
of Astra's past matches — in every one, a phase-2 zone scored exactly 0 whenever
the phase-1 zone in the same lane still had a squad standing. That is a
measurement, not a reading.

WHAT IS *NOT* IN HERE
---------------------
There are no per-territory stat modifiers in GAC. (Territory Battles have them;
GAC does not.) Do not add any.
Defenders earn no banners for placing a squad. The widely-copied
`setSquadDefenceBanners = 90` community constant is wrong — at Kyber it would add
1,290 banners for merely setting a board, which Astra's own 966-banner round
arithmetically disproves. Defense contributes to the scoreline only by denial.
"""

# --- per-battle banners (VERIFIED) ------------------------------------------
BANNER = {
    "victory": 15,
    "first_attempt": 30,       # 10 on the second attempt, 0 on the third and after
    "second_attempt": 10,
    "surviving_unit": 1,
    "unused_slot": 4,          # this is why undersizing pays on OFFENSE
    "full_health_unit": 1,
    "full_protection_unit": 1,
    "defeated_enemy": 1,       # "includes unset" — an empty defensive slot still pays it
    "first_attack": 10,        # once per round, not per battle
}

# Slots the ATTACKER may bring, and the enemy units they can kill, per format.
FORMAT_SLOTS = {"5v5": 5, "3v3": 3, "fleet": 7}


def battle_banners(fmt, team_size=None, survivors=None, full_hp=None,
                   full_prot=None, enemies=None, attempt=1):
    """Banners for one won battle. Defaults describe a perfect first-attempt clear.

    `team_size` is how many units the ATTACKER brought; bringing fewer is worth a
    net +1 each (you lose 3 for the missing survivor/health/protection credits and
    gain 4 for the unused slot).
    """
    slots = FORMAT_SLOTS[fmt]
    n = slots if team_size is None else team_size
    survivors = n if survivors is None else survivors
    full_hp = survivors if full_hp is None else full_hp
    full_prot = survivors if full_prot is None else full_prot
    enemies = slots if enemies is None else enemies
    attempt_bonus = (BANNER["first_attempt"] if attempt == 1 else
                     BANNER["second_attempt"] if attempt == 2 else 0)
    return (BANNER["victory"] + attempt_bonus
            + survivors * BANNER["surviving_unit"]
            + (slots - n) * BANNER["unused_slot"]
            + full_hp * BANNER["full_health_unit"]
            + full_prot * BANNER["full_protection_unit"]
            + enemies * BANNER["defeated_enemy"])


# Best possible single battle, which is also what an UNSET defensive slot hands
# the attacker for free: 5v5 69 · 3v3 59 · fleet 79 (solo clear, first attempt).
MAX_BATTLE = {f: battle_banners(f, team_size=1) for f in FORMAT_SLOTS}
# Reference value for a normal full-size first-attempt clear — the yardstick the
# published swgoh.gg "Banners" column is measured against.
REF_BATTLE = {f: battle_banners(f) for f in FORMAT_SLOTS}


# --- territory conquest banners (VERIFIED) ----------------------------------
def territory_banners(kind, slots):
    """Conquering a whole territory. All-or-nothing: one survivor pays nothing."""
    if kind == "fleet":
        return 120 + 33 * slots
    if kind == "5v5":
        return 120 + 30 * slots
    if kind == "3v3":
        return 120 + 28 * slots
    raise ValueError(kind)


# --- the Kyber board --------------------------------------------------------
# Read live from HotUtils gac/get. `lane` pairs a FRONT zone with the BACK zone it
# gates: both front zones are open from the first second of the attack phase, and a
# back zone stays invisible AND unattackable until every squad in its own lane's
# front zone is dead.
#
#   lane "top"     front 4 squads   ->   back = the FLEET territory (3 fleets)
#   lane "bottom"  front 4 squads   ->   back = 3 squads
#
# ⚠ Which lane carries the fleets is the one thing not settled by a first-party
# source. HotUtils labels it "Top Back (Ships)" and Astra's live board agrees, but
# check it at the start of an attack phase before trusting it for offense routing.
ZONES = {
    "5v5": [
        {"key": "front_top",    "zone_id": "4zone_phase01_conflict01_duel01",
         "phase": 1, "lane": "top",    "fleet": False, "slots": 4},
        {"key": "front_bottom", "zone_id": "4zone_phase01_conflict02_duel01",
         "phase": 1, "lane": "bottom", "fleet": False, "slots": 4},
        {"key": "back_fleet",   "zone_id": "4zone_phase02_conflict01_duel01",
         "phase": 2, "lane": "top",    "fleet": True,  "slots": 3},
        {"key": "back_bottom",  "zone_id": "4zone_phase02_conflict02_duel01",
         "phase": 2, "lane": "bottom", "fleet": False, "slots": 3},
    ],
    "3v3": [
        {"key": "front_top",    "zone_id": "4zone_phase01_conflict01_duel01",
         "phase": 1, "lane": "top",    "fleet": False, "slots": 5},
        {"key": "front_bottom", "zone_id": "4zone_phase01_conflict02_duel01",
         "phase": 1, "lane": "bottom", "fleet": False, "slots": 5},
        {"key": "back_fleet",   "zone_id": "4zone_phase02_conflict01_duel01",
         "phase": 2, "lane": "top",    "fleet": True,  "slots": 3},
        {"key": "back_bottom",  "zone_id": "4zone_phase02_conflict02_duel01",
         "phase": 2, "lane": "bottom", "fleet": False, "slots": 5},
    ],
}


def zone(fmt, key):
    return next(z for z in ZONES[fmt] if z["key"] == key)


def zone_conquest(fmt, z):
    return territory_banners("fleet" if z["fleet"] else fmt, z["slots"])


def zone_battles(fmt, z):
    """Battle banners an attacker collects for clearing every squad in this zone."""
    return z["slots"] * MAX_BATTLE["fleet" if z["fleet"] else fmt]


def zone_total(fmt, z):
    return zone_conquest(fmt, z) + zone_battles(fmt, z)


def lane_value(fmt, key):
    """What ONE surviving squad in this zone denies the opponent.

    A front zone denies its own conquest bonus, the remaining battles in it, AND
    everything in the back zone of the same lane, which never even becomes visible.
    A back zone denies only itself. In Kyber 5v5 that is 765 vs 279 — a 2.7x
    difference, and the whole reason placement is not just a ranked list.
    """
    z = zone(fmt, key)
    v = zone_conquest(fmt, z)
    if z["phase"] == 1:
        for other in ZONES[fmt]:
            if other["phase"] == 2 and other["lane"] == z["lane"]:
                v += zone_total(fmt, other)
    return v


def ceiling(fmt):
    """Perfect score: every territory conquered, every battle a solo first-attempt
    clear, plus the one-off first-attack bonus. Kyber 5v5 1915 · 3v3 2131.

    The 3v3 number is the check that this whole model is right: HotUtils' GAC page
    printed "Your max: 2131" for Astra's S81 3v3 round, independently.
    """
    return sum(zone_total(fmt, z) for z in ZONES[fmt]) + BANNER["first_attack"]


if __name__ == "__main__":
    for fmt in ("5v5", "3v3"):
        print(f"=== {fmt} (Kyber) — ceiling {ceiling(fmt)} banners ===")
        conq = sum(zone_conquest(fmt, z) for z in ZONES[fmt])
        print(f"  territory conquest {conq}  ({conq / ceiling(fmt):.0%} of everything)")
        for z in ZONES[fmt]:
            print(f"  {z['key']:<13} phase{z['phase']} lane={z['lane']:<6} slots={z['slots']}  "
                  f"conquest {zone_conquest(fmt, z):>3}  battles {zone_battles(fmt, z):>3}  "
                  f"| one hold here denies {lane_value(fmt, z['key']):>3}")
        print(f"  max per battle: squad {MAX_BATTLE[fmt]} (full-size {REF_BATTLE[fmt]}), "
              f"fleet {MAX_BATTLE['fleet']}\n")
