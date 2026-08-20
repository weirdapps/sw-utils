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
#
# ⭐ REBALANCED 2026-08-18 to MAX-DEFENSE on the owner's explicit call, with the
# conquest risk stated and accepted. The economics that justify it, read off the
# live territory panel (notes.md 2026-08-11): defense banks a FLAT +30 per squad,
# guaranteed, the moment it is set; an offense win pays only +6-20 and only if the
# attack is actually played. This account converts ~37% of its available attacks,
# so a marginal G13 body is worth strictly more walling than benched for an attack
# that statistically does not happen.
#
# `def` 23 is not a preference, it is the CEILING of the well-sampled lineup table:
# with off=8 reserved, the ILP is feasible at 23 and infeasible at 24 (measured —
# HiGHS returns status 8). Everything past 23 has to come from a coarser source,
# which is what tw_wall.py is for. TW_TOTAL_DEF is the real target and tw_wall.py
# fills the gap from the leader tier list and then from unranked-leader filler.
#
# `off` 8 is the owner's chosen floor. The cost is real and was flagged before the
# choice: 8 squads cannot clear a full enemy map, so territory conquest (+840 each)
# is largely forfeited. Those 8 are therefore spent on COHERENT GL squads only —
# notes.md 2026-08-12 measured that a GL with filler bodies goes 0-for-5 into a GL
# wall while a coherent GL squad wins, so a thin attack bank must not be diluted.
TW = {"def": 23, "off": 8, "off_weight": 0.75}

# Total TW defensive squads to field, graded bank + tw_wall.py tiers combined.
# 317 G13 characters / 5 = 63 disjoint squads; 8 offense squads spend 40 units, so
# 55 defense squads (275 units) very nearly exhausts the roster. The map itself is
# not the constraint (10 territories x 39 slots = 390, guild-wide first-come).
TW_TOTAL_DEF = 55
TW_FLEETS = {"def": 5, "off": 1}

# --- doctrine: which Galactic Legends may wall ---------------------------------
# HISTORY, kept because it is the reasoning that got superseded and the next person
# will otherwise re-derive it. This used to be four "pure-attack" GLs (JMK, JML, SEE,
# SLKR) on the argument that GLs are poor defenders and that walling one strands its
# supports. Both halves are shakier than they sound: SLKR's squad measures 47% hold
# at Kyber, and a GL whose wall and attack squad share the same four supports strands
# nothing. GL Leia was then treated as a genuine 5v5 tie (1240 def vs 1239 off) broken
# toward offense, and as a wall in 3v3. The measurement below replaces all of it.
#
# ⭐ THE RULE, MEASURED (set 2026-08-16, REVISED 2026-08-17 after the owner pushed
# back that too much was going on defense — he was right):
#
#   EVERY GL THAT HAS AN OFFENSE ROLE ATTACKS. A GL WALLS ONLY IF IT HAS NONE.
#
# scripts/gac_doctrine.py settles this by simulating whole rounds, both sides,
# against two real opponent boards, under six doctrines. Net banners, 5v5:
#
#   A  SLKR released to defense .................. -523
#   B  the classic 5 attack-GLs are attack-only ... -503
#   C  only Lord Vader + Jabba may wall .......... -483
#   D  no GL walls at all ........................ -472
#   E  every GL WITH an offense role attacks ..... -425   <- this one
#   F  E but SLKR walls too ...................... -471
#
# E leads by 65-87 banners at every value of the one free parameter (gac_place
# ATTEMPTS, swept 1.5 -> 4.0) in 5v5, and at every realistic value in 3v3. The
# absolute numbers are negative because "conceded" is measured against your ceiling
# and "earned" against theirs; only the ORDERING carries meaning.
#
# WHY DEFENSE LOSES THIS ARGUMENT, in one line: a defensive squad earns nothing and
# denies only against an opponent who would otherwise have taken those banners —
# and Astra's live board was cleared 14/14, so it denied zero. An offense squad
# earns its banners AND can be the one that conquers a territory, which pays 210-240
# more and unlocks the entire gated lane behind it.
#
# The exception is not a judgement call, it is a fact about the data: GL REY HAS NO
# OFFENSE ROW IN EITHER FORMAT. Not a weak one — none, in any meta file. Forcing her
# to offense (doctrine D) just strands five G13 units, which is why D loses to E by
# 47. SLKR was the closest call and was walled in the first cut of this file: the
# simulation says attack (F trails E by 46), because SLKR/Dark Rey is a 96% TWO-unit
# clear in 3v3 and 90% in 5v5, and freeing him deepens the bank that conquers lanes.
ATTACK_ONLY_GLS_WITH_OFFENSE = ["JEDIMASTERKENOBI", "GRANDMASTERLUKE", "SITHPALPATINE",
                                "SUPREMELEADERKYLOREN", "GLLEIA", "GLAHSOKATANO",
                                "LORDVADER", "JABBATHEHUTT"]
ATTACK_ONLY_BY_FORMAT = {
    "5v5": ATTACK_ONLY_GLS_WITH_OFFENSE,
    "3v3": ATTACK_ONLY_GLS_WITH_OFFENSE,
}

# Units defense may never claim, because they are the irreplaceable fifth of an
# attack squad the board cannot do without. A banner-sum objective cannot see
# MATCHUP COVERAGE — it will trade a 90% clear for a wall worth two more banners and
# never notice that the roster then has no answer to a specific enemy squad.
RESERVE_OFF_UNITS = {
    "5v5": {
        # ⚠ CORRECTED 2026-08-17. This was first justified as "Mace is the fifth of
        # JMK's 79% answer to The Stranger". That is WRONG and the counter corpus
        # says so plainly: the 79% row (n=403) is the GENERAL KENOBI variant, and the
        # MACE variant reads 43% into the same wall (n=440). Astra has no good answer
        # to The Stranger at all — the best well-sampled one is SLKR at 76% (n=2,769).
        #
        # The reservation survives anyway, on a plainer reason that was measured:
        # JMK / Ahsoka / Commander Ahsoka / MACE / Padme is a 90% attacker worth 55.6
        # banners (n=29.1K), and Mace is the ONLY fifth still available for it —
        # General Kenobi is committed to GL Rey's wall, which is the one wall doctrine
        # E keeps. Drop the reservation and the ILP spends Mace on the Queen Amidala
        # wall, JMK falls off the offense board entirely, and the round is 67 net
        # banners worse (measured with gac_doctrine's simulator).
        "MACEWINDU": "the last available fifth for JMK's 90% attacker; without him JMK "
                     "has no fieldable 5v5 squad and the board loses 67 net banners",
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

# Lineups allowed into the CORE pool despite sitting under MIN_SEEN. Empty since the
# SLKR-wall entry was retired with the doctrine change above; the sampling argument
# for MIN_SEEN is still right in general and there is no exception earning its keep.
CORE_ALLOW = {}

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
