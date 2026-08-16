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
# `def` must match the map exactly — see scripts/gac_score.py ZONES. An unfilled
# defensive slot is not a small loss: it hands the attacker the MAXIMUM banners for
# that slot (69 in 5v5) with no battle and no risk, and it opens the territory.
#
# `off` is the number of enemy squads you must beat to conquer everything: 11
# squads + 3 fleets in 5v5, 15 + 3 in 3v3. `bench` is retry and matchup depth on
# top of that, and it used to be 6 — which is why Astra kept running out. Astra's
# own record shows a mean of 731 banners left in zones that were OPEN and simply
# never attacked, so depth here is worth more than any refinement to the core list.
BOARD = {
    "5v5": {"def": 11, "off": 11, "bench": 12},
    "3v3": {"def": 15, "off": 15, "bench": 12},
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
#
# ⭐ SLKR IS NO LONGER ATTACK-ONLY IN 5v5 (changed 2026-08-16, evidence below).
# The blanket "GLs are poor defenders" line is false for this one. On swgoh.gg's
# S80 Kyber (all-divisions) 5v5 defense tier list, SLKR / Rey (Dark Side Vision) /
# Sith Trooper / General Hux / Kylo Ren (Unmasked) is the **#2 wall in the game at
# 47.0% hold over 7,200 battles**, behind only The Stranger. The second half of the
# old reasoning — that walling a GL strands its attackers — does not apply here
# either: the SLKR wall and the SLKR attack squad are the same four supports, so
# nothing is stranded. Astra owns all five at G13 and has never walled with them.
# The cost is real and is named: SLKR is the best owned answer to an enemy Stranger
# (76%). That job passes to JMK (79%, the best counter in the game), which is
# exactly why the Queen Amidala override below matters — it frees Mace Windu.
ATTACK_ONLY_BY_FORMAT = {
    "5v5": ["JEDIMASTERKENOBI", "GRANDMASTERLUKE", "SITHPALPATINE", "GLLEIA"],
    "3v3": ATTACK_ONLY_GLS,
}

# Units defense may never claim, because they are the irreplaceable fifth of an
# attack squad the board cannot do without. A banner-sum objective cannot see
# MATCHUP COVERAGE — it will trade a 90% clear for a wall worth two more banners and
# never notice that the roster then has no answer to a specific enemy squad.
RESERVE_OFF_UNITS = {
    "5v5": {
        # JMK / Ahsoka / Commander Ahsoka / MACE WINDU / Padme is 90% (n=29.1K) and,
        # more to the point, JMK is the best answer in the game to The Stranger at
        # 79% (n=403). With The Stranger, SLKR and Satele Shan all walling, JMK is
        # the ONLY good answer Astra has left to an enemy Stranger — which is the
        # most common hard wall at Kyber. Mace is the fifth of that squad and the
        # solver kept spending him on the Queen Amidala wall instead.
        "MACEWINDU": "fifth of JMK's 90% squad, Astra's only 79% answer to The Stranger",
    },
    "3v3": {},
}

# --- datacron-driven walls -----------------------------------------------------
# swgoh.gg publishes these on the DATACRON tier list, not the squad list, so they
# never appear in data/meta/* and the board has never been able to pick them. They
# are not a curiosity: a FOCUSED datacron (FDC) is the strongest defensive item in
# the game right now, and Astra owns two of them outright.
#
# ⭐ NO RELIC PENALTY. FDCs have no relic gate at all (L1-L15 require only Gear 1
# rising to Gear 5, unlike base crons which gate L6 at Relic 4 and L7-9 at Relic 6).
# The published hold comes from the cron, not the build, so the population Astra is
# compared against is running the same low relics he is. Applying relic_factor here
# would be double-counting a gap that is not there.
DATACRON_SQUADS = {
    "5v5": [
        {"units": ["RACCOON", "GAMORREANGUARD", "GREEDO", "CADBANE", "HUMANTHUG"],
         "rate": 41, "seen": "128", "seenN": 128.0, "cron": "Lj_hRktR",
         "no_relic_penalty": True,
         "why": "Rotta the Hutt FDC — the #1 defensive datacron in the game, 41.3% "
                "hold at Kyber Div 1 (swgoh.gg datacron tier list, S81). Astra owns "
                "the cron AT MAX (level 15/15) and all five units at G13. It already "
                "took 2 successful defends on the live S82 board."},
    ],
    "3v3": [],
}

# Lineups allowed into the CORE pool despite sitting under MIN_SEEN, each with the
# reason. This exists so a single well-evidenced exception does not force MIN_SEEN
# down for everything — the sampling argument above is still right in general.
CORE_ALLOW = {
    frozenset(["SUPREMELEADERKYLOREN", "DARKREY", "FOSITHTROOPER", "GENERALHUX",
               "KYLORENUNMASKED"]):
        "Kyber #2 wall at 47.0% hold on 7,200 Kyber battles (swgoh.gg S80 defense "
        "tier list, Kyber all-divisions). The all-league LINEUP row reads n=4,591 "
        "only because that view splits builds; the squad is not thinly sampled.",
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

# The bench is held to a lower bar on purpose. A core pick has to be trustworthy
# because the board is built on it; a bench squad only has to be better than not
# attacking at all, and Astra's record shows a mean of 731 banners per round sitting
# in zones that were OPEN and never touched. At MIN_SEEN the fieldable 5v5 pool runs
# dry after ~16 unit-disjoint offense squads, which is two spare attacks for
# fourteen required wins. That is the binding constraint, not the roster.
BENCH_MIN_SEEN = 800

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
DURABILITY_BY_SQUAD = {
    # The board's long-standing #2 wall. Two independent reasons to cut it, both
    # dated and sourced, which is the bar this table is supposed to clear:
    #  1. DATACRON DEATH. Its 37% was measured while the Mace Windu L9 focused
    #     datacron was live; that cron belonged to Set 30 "Peace & Power", which
    #     expired 2026-08-06. Mace was one of the four best S80 defensive datacrons
    #     at Kyber and there is no replacement — no live set grants Galactic
    #     Republic. Astra's live S82 board shows this squad carrying no cron at all.
    #  2. POPULATION. At Kyber Div 1 the Mace variant reads 23.8% (n=344), and the
    #     well-sampled Kyber build is the SHAAK TI fifth, not Mace, at 25.3%
    #     (n=10,300). 23.8/37 = 0.64.
    # Consequence, and the reason this is worth doing: Mace is the fifth in JMK's
    # 90% attack squad, which is also the best owned answer to an enemy Stranger.
    # Holding him on a rented wall was costing that squad.
    frozenset(["QUEENAMIDALA", "GRANDMASTERYODA", "MACEWINDU", "MASTERQUIGON",
               "PADAWANOBIWAN"]):
        (0.65, "Set 30 Mace datacron expired 2026-08-06; Kyber-D1 reads 23.8% vs 37% "
               "all-league"),
}

_dx = None
_unit_map = None


def _exposure_mod():
    global _dx, _unit_map
    if _dx is None:
        import datacron_exposure as dx
        _dx = dx
        _unit_map = dx.load_units()
    return _dx, _unit_map


# --- build quality: the relic gap ---------------------------------------------
# swgoh.gg's Hold%/Win%/Banners are population averages: what the squad did in the
# hands of everyone who ran it. Astra's copy of a squad is often BELOW that
# population. Measured against the live S82 round-2 opponent, total relic
# investment is near identical (2,213 levels vs 2,189) but the SHAPE is not:
# Astra has 27 units at R9+ and 156 parked at R7; the opponent has 60 at R9+.
# So a published 43% wall that Astra fields with three R7s is not a 43% wall.
#
# Nothing in the pipeline saw this before. The correction is deliberately mild and
# ONE-SIDED — a squad above baseline gets no bonus, because upside ratios are the
# direction that selection bias already pushes (see the league_adjust note above).
RELIC_BASELINE = 8          # the Kyber-D1 norm for a meta unit
RELIC_PER_LEVEL = 0.045     # multiplicative haircut per relic level below baseline, per unit
RELIC_FLOOR = 0.55          # never discount a squad by more than 45%


def relic_factor(units, relics):
    """Multiplier on a squad's published rate for how far below Kyber norm it is.

    `relics` maps baseId -> displayed relic level. Missing units count as baseline
    rather than as zero, so a data gap cannot silently delete a squad.
    """
    f = 1.0
    for u in units:
        gap = RELIC_BASELINE - relics.get(u, RELIC_BASELINE)
        if gap > 0:
            f *= (1.0 - RELIC_PER_LEVEL * gap)
    return max(RELIC_FLOOR, f)


# --- the objective, in banners -------------------------------------------------
# The old objective was `SUM Hold% + SUM Win%`. Those are different quantities and
# adding them is meaningless; worse, it cannot see territory conquest, which is 47%
# of a GAC score. Everything is now priced in banners (see scripts/gac_score.py):
#
#   an offense squad is worth   the banners it EARNS      (swgoh.gg avg banners)
#   a defense squad is worth    the banners it DENIES     (max - avg conceded)
#                             + its share of keeping a territory unconquered
#
# GATE_WEIGHT linearises that second term. The true value is
# P(zone survives) x (zone conquest + everything gated behind it), which saturates
# and cannot go in an ILP as-is; scripts/gac_place.py computes it exactly once the
# squads are chosen.
#
# MEASURED, not guessed. `python3 scripts/build_board.py --sweep` rebuilds the board
# at each weight and scores it as (banners my best 14 offense squads earn) minus
# (banners gac_place says my defense concedes):
#
#     GATE_W   off(top14)  conceded    net
#       0.0        697       1416     -719
#       1.0-2.0    663       1382     -719     <- flat optimum
#       2.5+       649       1379     -730     <- over-buys defense
#
# 1.5 sits in the flat region. The tie between 0 and 2 is broken toward defense on
# something the arithmetic cannot see: denial happens whether or not the owner logs
# in, while offense banners are only realised if the attacks are actually played —
# and this account converts 37% of them.
GATE_WEIGHT = 1.5


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
