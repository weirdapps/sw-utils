#!/usr/bin/env python3
"""
board_config.py — the judgement layer that sits on top of the raw swgoh.gg rates.

Everything in build_board.py is data-driven. This file is where the things the
data CANNOT tell you live, each with the reason it is here:

  DURABILITY  — swgoh.gg reports what a squad did LAST season. A squad carried by
                a datacron that is about to rotate will not repeat that number.
                Multipliers below discount those squads before the optimiser runs,
                so a temporary spike cannot buy a permanent defensive slot.
  FLEETS      — swgoh.gg has no "fleet squad" table; lineups are reconstructed
                from /gac/ship-counters battle data (see build_fleets.py notes).
  DOCTRINE    — which Galactic Legends are attack-only.

Rates are integers (percent). A multiplier of 0.8 means "treat a 50% hold as 40%".
"""

# --- board sizes -------------------------------------------------------------
# Kyber, 4-zone map (mapId 4zone_{fmt}_ga2_c3s1_*, read live from HotUtils gac/list).
BOARD = {
    "5v5": {"def": 11, "off": 11, "bench": 6},
    "3v3": {"def": 15, "off": 15, "bench": 6},
}

# Territory War: the map allows far more squads than GAC and the opponent guild
# has a FINITE pool of attempts, so a wall that merely eats attempts is worth
# more than in GAC. Sizes are generous on purpose — set them top-down until your
# TW map runs out of slots.
TW = {"def": 15, "off": 15, "off_weight": 0.75}

# Pure-attack Galactic Legends: never place on defense. They are poor defenders
# and, worse, a defensive placement strands the support units their offense needs.
ATTACK_ONLY_GLS = ["JEDIMASTERKENOBI", "GRANDMASTERLUKE", "SITHPALPATINE",
                   "SUPREMELEADERKYLOREN"]

# GL Leia in 5v5 is the one placement the optimiser will not settle: her best wall
# (31% hold) and her best attack (96% win, the highest in the game) score within
# 1 point of each other across the whole board - 1240 vs 1239, i.e. a tie.
# Offense wins the tie-break on three things the linear model cannot see:
#   * on offense YOU choose the matchup, so a 96% clear can be aimed at their
#     hardest squad; a wall takes whatever comes;
#   * 96% is near-certain, 31% is a coin flip you lose two times in three;
#   * a hold rate measured across all leagues decays against Kyber opponents,
#     while a top attacker does not.
# In 3v3 there is no tie: forcing her to offense costs 13 points, so she walls.
ATTACK_ONLY_BY_FORMAT = {
    "5v5": ATTACK_ONLY_GLS + ["GLLEIA"],
    "3v3": ATTACK_ONLY_GLS,
}

# Minimum battles behind a rate before it is trusted. swgoh.gg's cutoff=0 view
# returns rows with n<10 showing 100%, so some floor is mandatory; the level is a
# judgement call and was measured rather than guessed:
#
#   n>=2000  -> 5v5 board scores 1283, but anchors on n~3,000 variants
#   n>=5000  -> 1240, and every pick is a well-sampled team (the #1 wall returns
#               to The Stranger + Luminara at n=29.8K)
#   n>=10000 -> 1225, and genuinely better rare variants get thrown away
#
# 5000 gives up ~3% of theoretical board value to avoid anchoring the board on
# thin rows. Sampling error at n=3,000 is only ~1 point, so the real risk is
# SELECTION bias: an unusual variant is played by unusual (stronger) players, and
# that edge does not transfer. It also keeps the board verifiable - the player can
# still find these squads on swgoh.gg.
MIN_SEEN = 5000

# --- durability ----------------------------------------------------------------
# The FACTION-TAG proxy that used to live here is OFF, and stays off. It failed
# twice over: it could not see FOCUSED datacrons at all (a focused cron keys off ONE
# named character, not a faction), and its haircut was so pervasive that it stopped
# ranking and started scrambling - JMK's 95% 3v3 team fell below a 78% filler.
DURABILITY_ENABLED = False

# What replaced it is not a proxy. swgoh.gg's squad tier lists publish, per leader,
# the rate measured in the battles where NO L9 datacron applied - an actual
# counterfactual. durability.py turns that into ratio = baseline / headline.
#
# Applied to DEFENSE ONLY, and that is an evidence-based choice, not a hedge:
# measured OFFENSE ratios all land between 0.87 and 1.04, because an attacker
# already winning 90% is not being carried by its datacron. DEFENSE ratios run 0.35
# to 1.15 - a wall at 25% can be more than half rented. Defense is also the side you
# cannot adapt: it is set once per round and then attacked by whoever turns up.
#
# WHY NOW: Season 81 closed 2026-07-31 and Set 30 "Peace & Power" expires
# 2026-08-06, so the very next season is played without it - including the four
# FOCUSED datacrons on Cassian Andor (Undercover), Darth Revan, Dedra Meero and
# Luminara Unduli. Three of those four sit on this board.
DEFENSE_DURABILITY = True

# Correct all-league rates to Astra's real opposition. /gac/squads/ - the only
# LINEUP-level source - is all-league and does NOT honour a league filter
# (verified: ?league=kyber-d1 returns identical rows to a bogus value). The
# LEADER-level tier lists do, so league_adjust.py applies a per-leader ratio.
# It validates the 5v5 board (The Stranger is #1 in both populations; most other
# picks RISE in rank at Kyber-D1) and fixes two real 3v3 errors.
LEAGUE_ADJUST = True

# Manual overrides still win, if a specific call ever needs to be forced.
DURABILITY_BY_LEADER = {}
DURABILITY_BY_SQUAD = {}

_dx = None
_unit_map = None


def _exposure_mod():
    global _dx, _unit_map
    if _dx is None:
        import datacron_exposure as dx
        _dx = dx
        _unit_map = dx.load_units()
    return _dx, _unit_map


def adjust(squad):
    """Return (adjusted_rate, reason or None) for one meta squad."""
    key = frozenset(squad["units"])
    if key in DURABILITY_BY_SQUAD:
        mult, why = DURABILITY_BY_SQUAD[key]
        return squad["rate"] * mult, why
    lead = squad["units"][0]
    if lead in DURABILITY_BY_LEADER:
        mult, why = DURABILITY_BY_LEADER[lead]
        return squad["rate"] * mult, why
    if DURABILITY_ENABLED:
        dx, um = _exposure_mod()
        mult, why = dx.verdict(squad["units"], um)
        if mult != 1.0:
            return squad["rate"] * mult, why
    return float(squad["rate"]), None
