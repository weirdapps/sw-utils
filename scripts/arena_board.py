#!/usr/bin/env python3
"""
arena_board.py — Squad Arena: the ONE defense squad, and the climb (offense) plan.

WHY THIS IS NOT build_board.py
------------------------------
The GAC board is a weighted set-packing problem: many squads, each unit usable
once, solved exactly in optimize_board.py. Squad Arena breaks all three of those
premises and reusing the GAC framing here would be wrong:

  * You set exactly ONE 5-unit defense squad. There is nothing to pack — the
    answer is an argmax over fieldable squads, not an ILP.
  * There is NO no-repeat rule. The squad that defends may also attack, and the
    same attack squad may be used against every opponent on the ladder. Forcing
    disjointness would throw away the single best attacker for no reason.
  * Defense is AI-played and attacked repeatedly by a FIXED ~50-player shard,
    not by a fresh league-wide opponent each round. That is why the shard file
    (below) beats every aggregate rate this repo has.

THE PROXY, STATED HONESTLY
--------------------------
swgoh.gg publishes GAC rates, not arena rates. Arena has no published stats
anywhere (same finding as the Fleet Arena work — memory/notes.md 2026-08-05).
So this module scores with:

    5v5 DEFENSE pool Hold%  ->  proxy for arena defense strength
    5v5 OFFENSE pool Win%   ->  proxy for arena climb strength

Both are proxies and both are BIASED IN A KNOWN DIRECTION. GAC hold% is measured
against an attacker pool that is crippled by the no-repeat rule: a GAC attacker
must spend its units across eleven battles, so most walls are hit by the 4th-best
counter, not the best one. An arena attacker has no such constraint and can throw
its single best squad at you every single time. Real arena hold is therefore
LOWER than every number printed here.

That bias is roughly uniform across candidates, so it moves the LEVEL and not the
RANKING — which is why it is reported and not applied. (One thing GAC hold% does
already price in correctly: it is itself measured against AI-played defense, so
"this kit is worse on auto" is inside the proxy, not missing from it. See
AUTO_PENALTY.)

⚠️ THE ONE BIAS THAT IS *NOT* UNIFORM, AND IT BREAKS THE RANKING
----------------------------------------------------------------
OMICRONS DO NOT FIRE IN SQUAD ARENA. Omicron abilities are mode-tagged to Grand
Arena / Territory War / Territory Battle / Conquest / Raids / Galactic
Challenges, and Squad Arena is on none of those lists (CG's 2026-04-27 Community
Update states it outright while describing Training Mode: "Omicrons will not be
present (similar to current Squad Arena)"). Confirmed independently against
HotUtils `gamedata/units`: every omicron in the 410-unit catalogue carries a
mode of 7/8/9/11/14/15 (TB / TW / GAC / Conquest / GAC-family) and NO mode maps
to Squad Arena.

DATACRONS, by contrast, DO apply in Squad Arena (levels 3/6/9, same as TW/GAC).

This bias is proportional to how omicron-dependent a squad is, so unlike the
no-repeat bias it reorders the ranking rather than shifting it. Concretely, on
this roster the top GAC wall — The Stranger / Luminara / Maul (Hate-Fueled) /
Starkiller / Visas Marr, 57% hold, the #1 wall in Kyber-D1 — carries 9-10
applied omicrons and is a BAD arena defense, while Rotta the Hutt's leader
ability "A Legacy Reforged" (+50 Speed and 200% Defense to Hutt Cartel) is a
base ability that loses nothing.

It is REPORTED, not applied, for the usual reason: the direction is sourced but
the per-squad magnitude is not measured, and this repo has already been burned
by an unsourced haircut (see AUTO_PENALTY note 2). The right fix is a shard
capture — the ladder measures arena directly and needs no omicron correction at
all. Astra's own shard confirms the effect: ranks 1, 2, 3, 5 and 9 all run Rotta
lead, and no one runs the Stranger wall.

WHAT MAKES IT GROUNDED INSTEAD OF GUESSED
-----------------------------------------
Two optional files replace the aggregate with a measurement, and the module says
in its output which one it used:

  data/arena/shard_<YYYYMMDD>.json   the ACTUAL ladder
      {"captured": "2026-08-08T13:00:00Z", "mode": "squad",
       "player_rank": 10,                       # optional extension, see load_shard
       "opponents": [{"rank": 1, "name": "...", "gp": 14000000,
                      "squad": ["BASEID", ...]}, ...]}

  data/meta/squad_counters.json      MEASURED attacker-vs-defender rates
      {"<defending leader baseId>": [{"attacker": ["BASEID", ...],
                                      "win": 0.0-1.0, "n": int}, ...]}

Absent both, everything falls back to the aggregate rates and says so.

UNITS: every rate in this module is a PERCENT (0-100), matching swgoh.gg and the
rest of the repo. The counters file's 0-1 `win` is converted on load.

Run:  python3 scripts/arena_board.py [player_rank]
"""
import glob
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import board_config as cfg          # noqa: E402
import swgoh_data                   # noqa: E402
import swgoh_meta                   # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
META = os.path.join(DATA, "meta")
ARENA = os.path.join(DATA, "arena")
OUT = os.path.join(ROOT, "output")
ALLY = "145357294"

# Squad Arena is played on the 5v5 map, so the 5v5 pools are the right proxy.
# Same four files build_board.load_pools() reads, minus the 3v3 half.
META_MAIN = {"def": "meta_5v5_defense_s80.json", "off": "meta_off5v5.txt"}
META_DEEP = {"def": "meta_def5v5_deep.txt", "off": "meta_off5v5_deep.txt"}

# =============================================================================
# JUDGEMENT LAYER — things the data cannot tell you. board_config.py style:
# every constant carries its reason, and rejected alternatives are recorded so
# they are not retried.
# =============================================================================

# Game rule, not a tuning knob: an arena squad is exactly five characters.
SQUAD_SIZE = 5

# Game rule: the client refuses a squad with two Galactic Legends. Any plan that
# assumes two is dead on arrival, so this is a hard filter, not a penalty.
MAX_GALACTIC_LEGENDS = 1

# Game rule: the client also refuses a squad with two LARGE units, with
# "Large Unit Limit - Your squad already contains the maximum number of large
# units." Device-verified 2026-08-08 trying to put Jabba next to Rotta.
#
# This one is NOT derivable from any data source we have: HotUtils'
# gamedata/units carries affiliation/role/profession/species/omicron but no size
# flag, and swgoh.gg does not publish one either. So the set below is hand-kept
# and DELIBERATELY holds only what the game has actually rejected for this
# account. Add a unit when the client refuses it, not when it looks big.
#
# It matters: the obvious "best Hutt Cartel five" is Rotta + Jabba + the three
# next-best bodies, and the game will not let you field it. Both external
# research and a power-ranked pick proposed exactly that illegal squad.
LARGE_UNITS = frozenset({"JABBATHEHUTT", "RACCOON"})   # RACCOON == Rotta the Hutt
MAX_LARGE_UNITS = 1

# --- AUTO_PENALTY: deliberately EMPTY. ---------------------------------------
# {baseId: fraction of a squad's DEFENSIVE rate lost because the kit needs manual
# play}. Applied multiplicatively to defense scores only (_auto_multiplier) —
# offense is played by the player by hand, so nothing about auto behaviour applies
# to the climb.
#
# The effect is real — arena defense is AI-played, so kits that need precise
# ability ordering or manual target selection underperform, and kits that are
# strong on auto overperform. It is seeded empty anyway, for two reasons:
#
#  1. THE PROXY ALREADY CONTAINS MOST OF IT. GAC hold% is ALSO measured on
#     AI-played defense. A kit that flops on auto already holds badly in the
#     source data. Discounting it again double-counts.
#  2. THIS REPO HAS ALREADY REJECTED ONE PERVASIVE UNSOURCED HAIRCUT. The
#     faction-tag datacron proxy at 20% stopped ranking and started scrambling
#     (JMK's 95% squad fell below a 78% filler); turning it down far enough to
#     stop the damage made it change nothing. See board_config.py DURABILITY and
#     memory/notes.md 2026-08-05. An unsourced magic number is worse than no
#     adjustment.
#
# EVIDENCE THAT WOULD JUSTIFY AN ENTRY (either is sufficient):
#  (a) A published rate split by auto vs manual play, or an arena-specific hold
#      rate from any source. swgoh.gg publishes neither today (verified for
#      Fleet Arena, memory/notes.md; the squad side is the same GAC-only data).
#  (b) An A/B on this account: hold squad X for a full payout cycle, count
#      attacks survived from the shard, swap to Y, repeat. Roughly 30 logged
#      attacks per arm before a 10pp difference is readable — which is one to
#      two weeks per pair, so only worth running on a genuine two-way tie.
#
# What is NOT evidence: a kit description, a YouTube tier list, or the intuition
# that "the AI wastes her ultimate". Those produce exactly the unsourced number
# this repo already threw out once.
AUTO_PENALTY = {}

# A measured counter rate needs a sample before it outranks the aggregate.
# 200 battles is +-3.5pp standard error at p=0.5, and adjacent defense candidates
# on this board differ by more than that. durability.py uses 1000, but that floor
# guards a LEADER-level row pooled over hundreds of lineups; a counters row is a
# single attacker-vs-defender pair, so each battle carries far more information.
MIN_COUNTER_N = 200

# REPORTING ONLY — never used for ordering. Labels which rung of the ladder the
# plan calls "reachable". You get several attacks per payout cycle, so one shot
# need not be near-certain: at 65% two attempts clear ~88%, which is where aiming
# at the top rung beats settling for a safer lower one. Moving this number
# changes a label in the output and nothing else.
CONFIDENT_WIN = 65

# The player is rank 10 and wants rank 1. Beating an opponent takes their rank
# outright, so the whole plan is "how high can one attack reach".
TARGET_RANK = 1

# Rejected: carrying over GAC's two rate corrections (durability.py's
# no-datacron baseline and league_adjust.py's Kyber-D1 ratio). Both correct an
# all-league GAC population toward the opponents Astra actually meets. Arena
# opposition is not a league population at all — it is a fixed ~50-player shard,
# and the shard file measures it directly. Stacking a GAC population correction
# on top of a shard measurement would correct twice in the same direction. The
# manual-override hook in board_config.adjust() is still honoured, because that
# is where a deliberate one-off call belongs.

# Cache of the Galactic Legend list, which IS data-driven: swgoh.gg's
# /api/characters/ dump tags every GL with the "Galactic Legend" category. This
# frozenset is only the fallback for when that file is missing — the one-GL rule
# is a hard game rule and must survive a missing data file rather than silently
# producing illegal squads. Snapshot taken from the file on 2026-08-08 (10 GLs;
# Astra owns 9, GLHONDO is the known gap).
_GL_FALLBACK = frozenset({
    "GLAHSOKATANO", "GLHONDO", "GLLEIA", "GLREY", "GRANDMASTERLUKE",
    "JABBATHEHUTT", "JEDIMASTERKENOBI", "LORDVADER", "SITHPALPATINE",
    "SUPREMELEADERKYLOREN"})
_CATEGORIES = os.path.join(META, "raw_unit_categories_20260805.json")
_gls_cache = None


# =============================================================================
# roster helpers
# =============================================================================

def displayed_relic(rt):
    """Turn the roster's `rt` field into the relic level the GAME DISPLAYS.

    THE TRAP THIS EXISTS FOR: `rt` is comlink's relic.currentTier verbatim and it
    is TWO HIGHER than the number on the unit tile. Device-verified 2026-08-05 —
    a roster reading rt:12 shows R10 in game, and units at rt:8/7 were rejected by
    a "Relic 7+" mission because they are really R6/R5. So a Relic 6+ requirement
    is rt >= 8 and Relic 7+ is rt >= 9. This repo has been burned by it before.

    None for units with no relic object (ships, unowned). Pre-G13 / locked units
    carry rt = 1, which would map to a negative level, so the floor is 0.
    """
    if rt is None:
        return None
    return max(0, rt - 2)


def owned_g13(roster):
    """baseIds owned as G13+ CHARACTERS. Same rule the GAC board uses."""
    return {u["b"] for u in roster.get("units", [])
            if u.get("ct") == 1 and (u.get("g") or 0) >= 13}


def relic_index(roster):
    """{baseId: displayed relic level}, skipping units with no relic data."""
    out = {}
    for u in roster.get("units", []):
        r = displayed_relic(u.get("rt"))
        if r is not None:
            out[u["b"]] = r
    return out


def galactic_legends(path=None):
    """The GL baseIds, read from swgoh.gg's unit-category dump when present.

    Data-driven on purpose: the list grows every few months and a hand-kept one
    goes stale silently. The dump also corrects guesses — Great Mothers reads as
    a Nightsister Leader there, NOT a Galactic Legend.
    """
    global _gls_cache
    if path is None and _gls_cache is not None:
        return _gls_cache
    src = path or _CATEGORIES
    gls = _GL_FALLBACK
    try:
        raw = json.load(open(src))
        if isinstance(raw, str):
            raw = json.loads(raw)
        found = frozenset(b for b, v in (raw.get("map") or {}).items()
                          if "Galactic Legend" in (v.get("cats") or []))
        if found:
            gls = found
    except (OSError, ValueError):
        pass
    if path is None:
        _gls_cache = gls
    return gls


# =============================================================================
# data loading
# =============================================================================

def load_pools(meta_dir=META):
    """(defense_pool, offense_pool) for 5v5, merged exactly as build_board does.

    Main + deep views are deduped on lineup keeping the bigger sample, then cut at
    board_config.MIN_SEEN. The cutoff is REUSED rather than re-tuned: it comes from
    the same swgoh.gg tables and was chosen by measurement (n>=5000 keeps every
    pick well-sampled and verifiable; the risk it guards is selection bias, which
    is identical here).
    """
    main = swgoh_meta.load_meta(META_MAIN, meta_dir)
    deep = swgoh_meta.load_meta(META_DEEP, meta_dir)
    pools = {}
    for side in ("def", "off"):
        merged = {}
        for s in main[side] + deep[side]:
            k = tuple(s["units"])
            if k not in merged or s["seenN"] > merged[k]["seenN"]:
                merged[k] = s
        out = []
        for s in merged.values():
            if s["seenN"] < cfg.MIN_SEEN:
                continue
            s = dict(s)
            adj, why = cfg.adjust(s)          # manual-override hook only (see above)
            s["raw_rate"], s["rate"], s["discount"] = s["rate"], adj, why
            out.append(s)
        pools[side] = out
    return pools["def"], pools["off"]


def load_shard(path=None, arena_dir=ARENA):
    """Newest data/arena/shard_<YYYYMMDD>.json, or None when there is no capture.

    Returns None (rather than raising) for a missing file, unparseable JSON, or a
    non-squad capture, so every caller degrades to the aggregate path. The schema
    is the one in the module docstring; `player_rank` is an OPTIONAL extension —
    the ladder alone cannot say where the player sits on it, and knowing that is
    what turns "who can I beat" into "who is worth beating".
    """
    if path is None:
        hits = sorted(glob.glob(os.path.join(arena_dir, "shard_*.json")))
        if not hits:
            return None
        path = hits[-1]
    try:
        shard = json.load(open(path))
    except (OSError, ValueError):
        return None
    if not isinstance(shard, dict) or not shard.get("opponents"):
        return None
    if shard.get("mode", "squad") != "squad":
        return None                            # a fleet-arena capture is not this board
    return shard


def load_counters(path=None):
    """squad_counters.json as {leader: [{attacker, win_pct, n}]}, or None.

    The file stores `win` as 0-1; it is converted to percent here so the rest of
    the module has one unit. Rows below MIN_COUNTER_N are dropped at load, so a
    thin file degrades to "no counters" instead of to a confident wrong number.
    """
    src = path or os.path.join(META, "squad_counters.json")
    try:
        raw = json.load(open(src))
    except (OSError, ValueError):
        return None
    if not isinstance(raw, dict):
        return None
    out = {}
    for leader, rows in raw.items():
        keep = []
        for r in rows or []:
            n = r.get("n") or 0
            if n < MIN_COUNTER_N or r.get("win") is None or not r.get("attacker"):
                continue
            keep.append({"attacker": list(r["attacker"]), "win": float(r["win"]) * 100.0,
                         "n": n})
        if keep:
            out[leader] = keep
    return out or None


# =============================================================================
# the matchup model
# =============================================================================
# One Bradley-Terry style function serves both directions. Squad strengths are
# log-odds of their published rates:
#
#     t_A = logit(win% of attacker A)      s_D = logit(hold% of defense D)
#     P(A clears D) = sigmoid(t_A - s_D + C)
#     P(D holds  A) = 1 - P(A clears D)          <- true by construction
#
# C is CALIBRATED FROM THE POOLS, not chosen. Two constraints pin it:
#   * against an average attacker, a defense should score its published hold  -> C = -mean(t)
#   * against an average defense, an attacker should score its published win  -> C =  mean(s)
# Those agree only if mean(hold) == 1 - mean(win). On the live pools they nearly
# do (18.0% mean hold vs 16.3% implied by an 83.7% mean win — 0.12 apart in
# log-odds), the residual being that the two tables are separately-sampled top-N
# lists. C is the MIDPOINT, so neither side is privileged and both directions stay
# a single self-consistent function.
#
# This is a MODEL, not a measurement. It is used only where nothing was measured;
# a counters row always wins. Its one job is to answer "how does THIS wall do
# against THAT specific squad", which no aggregate rate can answer at all.

_EPS = 0.5          # rates are integers 3..96; clamp keeps logit finite


def _logit(pct):
    p = min(max(float(pct), _EPS), 100.0 - _EPS) / 100.0
    return math.log(p / (1.0 - p))


def _sigmoid(x):
    return 100.0 / (1.0 + math.exp(-x))


def _wmean_logit(pool):
    tw = sum(s.get("seenN") or 0 for s in pool)
    if not pool:
        return None
    if tw <= 0:                                # unweighted fallback for handmade pools
        return sum(_logit(s["rate"]) for s in pool) / len(pool)
    return sum(_logit(s["rate"]) * (s.get("seenN") or 0) for s in pool) / tw


def calibration(def_pool, off_pool):
    """The C above. None when either pool is empty (then nothing is modelled)."""
    s_bar, t_bar = _wmean_logit(def_pool), _wmean_logit(off_pool)
    if s_bar is None or t_bar is None:
        return None
    return (s_bar - t_bar) / 2.0


def p_clear(win_pct, hold_pct, cal):
    """P(an attacker rated win_pct clears a defense rated hold_pct), percent."""
    return _sigmoid(_logit(win_pct) - _logit(hold_pct) + cal)


def rate_index(pool):
    """{frozenset(units): rate} — look up a lineup's published rate."""
    return {frozenset(s["units"]): s["rate"] for s in pool}


# =============================================================================
# counters lookup
# =============================================================================

def counter_rows(counters, defense_units):
    """Measured attacks logged against this defense's LEADER (units[0]), or []."""
    if not counters or not defense_units:
        return []
    return counters.get(defense_units[0], [])


def measured_matchup(counters, defense_units, attacker_units):
    """(attacker win%, n, how) for a specific pair, or None if nothing was logged.

    Exact lineup first; failing that, the attacker's LEADER, pooled by sample.
    A leader match is weaker evidence than a lineup match and says so in `how`,
    but it is still a measurement of the thing that decides most arena battles.
    """
    rows = counter_rows(counters, defense_units)
    if not rows:
        return None
    want = frozenset(attacker_units)
    for r in rows:
        if frozenset(r["attacker"]) == want:
            return r["win"], r["n"], "lineup"
    lead = attacker_units[0] if attacker_units else None
    same = [r for r in rows if r["attacker"] and r["attacker"][0] == lead]
    if same:
        n = sum(r["n"] for r in same)
        return sum(r["win"] * r["n"] for r in same) / n, n, "leader"
    return None


def counters_hold(counters, defense_units):
    """(hold%, n, n_lineups) for a defense against EVERYTHING logged against it.

    1 - the sample-weighted mean attacker win rate. This is the measured answer to
    "how often does this wall survive", with no model in it at all.
    """
    rows = counter_rows(counters, defense_units)
    if not rows:
        return None
    n = sum(r["n"] for r in rows)
    if n < MIN_COUNTER_N:
        return None
    return 100.0 - sum(r["win"] * r["n"] for r in rows) / n, n, len(rows)


# =============================================================================
# defense
# =============================================================================

def _auto_multiplier(units):
    """Product of (1 - AUTO_PENALTY) over the squad. 1.0 while the dict is empty."""
    m = 1.0
    for u in units:
        m *= (1.0 - AUTO_PENALTY.get(u, 0.0))
    return m


def _fieldable(pool, owned, gls, size=SQUAD_SIZE):
    """Squads Astra can legally set: right size, all owned at G13+, <=1 GL, <=1 large."""
    out = []
    for s in pool:
        units = s["units"]
        if len(units) != size or len(set(units)) != size:
            continue
        if any(u not in owned for u in units):
            continue
        if sum(1 for u in units if u in gls) > MAX_GALACTIC_LEGENDS:
            continue
        if sum(1 for u in units if u in LARGE_UNITS) > MAX_LARGE_UNITS:
            continue
        out.append(s)
    return out


def _shard_defense_score(squad, shard, counters, off_rates, cal):
    """(mean hold%, why) for one defense against the ACTUAL ladder.

    Each ladder opponent is scored with a measured counters row when one exists
    and with the model otherwise. The model needs the attacker's published win
    rate, so an opponent whose lineup is not in the offense pool (or an off-meta
    one) is treated as an AVERAGE attacker, which reduces that term to the
    aggregate hold — the honest answer when the ladder tells you nothing.

    ASSUMPTION, and it is the load-bearing one: a shard capture shows each
    opponent's DEFENSE squad, because that is what the ladder displays. This
    treats it as a proxy for what they will ATTACK you with. Top-shard players
    usually run their strongest squad on defense, but a player who defends with a
    wall and attacks with a different clear will be mis-scored.
    """
    holds, measured = [], 0
    for opp in shard["opponents"]:
        atk = list(opp.get("squad") or [])
        m = measured_matchup(counters, squad["units"], atk) if atk else None
        if m:
            holds.append(100.0 - m[0])
            measured += 1
            continue
        win = off_rates.get(frozenset(atk)) if atk else None
        if win is None or cal is None:
            holds.append(float(squad["rate"]))          # unknown attacker == average
        else:
            holds.append(100.0 - p_clear(win, squad["rate"], cal))
    if not holds:
        return float(squad["rate"]), "shard capture had no usable opponents"
    mean = sum(holds) / len(holds)
    return mean, (f"{mean:.0f}% mean hold across the {len(holds)} ladder opponents "
                  f"({measured} measured, {len(holds) - measured} modelled from "
                  f"{squad['rate']}% GAC hold)")


def candidate_defenses(roster, pool, counters=None, shard=None, off_pool=None,
                       gls=None):
    """Rank every defense squad Astra can legally set for Squad Arena.

    Returns [{"units", "score", "basis", "why", ...}] best first, where
    basis is:
        "shard"     — scored against the actual ladder (best; needs the capture)
        "counters"  — scored against everything measured vs this wall
        "aggregate" — the raw 5v5 GAC hold%, i.e. the league-average proxy

    Hard filters (all three are game rules, not preferences): exactly SQUAD_SIZE
    distinct units, every one owned at G13+, at most one Galactic Legend.

    `off_pool` is optional and only feeds the matchup model. Without it a shard is
    still used — measured counters rows still bite — but unmatched opponents fall
    back to the average attacker, so the score collapses toward the aggregate.
    `score` is a percent and, whatever the basis, means the same thing: how often
    this squad is expected to survive an attack.

    Ties break on relic depth (deeper relics win the speed race that decides who
    moves first) and then on sample size. Relic is a TIE-BREAK ONLY — turning
    relic depth into a score multiplier would be exactly the unsourced number this
    repo rejected once already.
    """
    gls = galactic_legends() if gls is None else gls
    owned = owned_g13(roster)
    relics = relic_index(roster)
    fieldable = _fieldable(pool, owned, gls)
    if not fieldable:
        return []

    off_pool = off_pool or []
    off_rates = rate_index(off_pool)
    cal = calibration(pool, off_pool)
    use_shard = bool(shard and shard.get("opponents"))

    out = []
    for s in fieldable:
        if use_shard:
            score, why = _shard_defense_score(s, shard, counters, off_rates, cal)
            basis = "shard"
        else:
            ch = counters_hold(counters, s["units"])
            if ch:
                score, basis = ch[0], "counters"
                why = (f"{ch[0]:.0f}% measured hold over {ch[1]:,} logged attacks "
                       f"from {ch[2]} attacker lineup(s)")
            else:
                score, basis = float(s["rate"]), "aggregate"
                why = (f"{s['rate']}% GAC 5v5 hold (n={s['seen']}) — league-average "
                       f"proxy, no shard capture and nothing measured vs this wall")
        auto = _auto_multiplier(s["units"])
        if auto != 1.0:
            score *= auto
            why += f"; AUTO_PENALTY x{auto:.2f}"
        depth = [relics[u] for u in s["units"] if u in relics]
        out.append({"units": list(s["units"]), "score": round(score, 1), "basis": basis,
                    "why": why, "gac_hold": s["rate"], "seen": s.get("seen"),
                    "relic": round(sum(depth) / len(depth), 1) if depth else None})
    out.sort(key=lambda e: (-e["score"], -(e["relic"] or 0), -_seen(e)))
    return out


def _seen(entry):
    return swgoh_meta.seen_num(entry.get("seen") or 0)


# =============================================================================
# offense / climb
# =============================================================================

def best_attack(squads, opponent_squad, counters=None, def_rates=None, cal=None):
    """Best owned attack squad against one opponent, as {units, win, basis, why}.

    `squads` are already filtered to what Astra can field. basis is:
        "counters"  — a logged attacker-vs-this-defender rate
        "modelled"  — their wall's published hold vs this squad's published win
        "aggregate" — their wall is not in the meta pool, so the raw win% stands

    WORTH KNOWING BEFORE READING THE OUTPUT: p_clear is monotone in win%, so
    WITHOUT counters the same top squad wins every matchup and the plan needs
    exactly one lineup. That is not the model failing — it is the honest statement
    that an aggregate win rate carries no per-opponent information. A counters
    file is what makes per-opponent squad choice possible, and that is the main
    reason to build one.

    Returns None when there is nothing to field.
    """
    def_rates = def_rates or {}
    best = None
    for s in squads:
        m = measured_matchup(counters, opponent_squad, s["units"]) if opponent_squad else None
        match = None
        if m:
            win, basis, match = m[0], "counters", m[2]
            why = f"{win:.0f}% measured over {m[1]:,} logged attacks ({m[2]} match)"
        else:
            hold = def_rates.get(frozenset(opponent_squad or []))
            if hold is None or cal is None:
                win, basis = float(s["rate"]), "aggregate"
                why = (f"{s['rate']}% GAC 5v5 win (n={s.get('seen')}) — their wall is "
                       f"not in the meta pool, so no matchup correction")
            else:
                win, basis = p_clear(s["rate"], hold, cal), "modelled"
                why = (f"{win:.0f}% — {s['rate']}% GAC win vs their {hold}% wall")
        cand = {"units": list(s["units"]), "win": round(win, 1), "basis": basis,
                "why": why, "match": match, "gac_win": s["rate"], "seen": s.get("seen")}
        # Ties go to the better-evidenced squad first (an exact lineup match beats
        # a leader match beats a model), then to the bigger sample.
        if best is None or _attack_key(cand) > _attack_key(best):
            best = cand
    return best


_MATCH_QUALITY = {"lineup": 2, "leader": 1}


def _attack_key(cand):
    return (cand["win"], _MATCH_QUALITY.get(cand.get("match"), 0), _seen(cand))


def climb_plan(roster, off_pool, shard, counters=None, def_pool=None,
               player_rank=None, gls=None):
    """Who to hit, with what, in what order.

    Beating an opponent takes their rank outright, so the value of an attack is
    the rank it wins times the chance of winning it. Entries are ordered by that
    product, which puts "the highest rung you can actually reach" first and drops
    opponents already below the player to the bottom (their gain is negative).
    Without a known player rank the order falls back to win% then rank.

    ARENA HAS NO NO-REPEAT RULE, so the same squad may be recommended against
    every opponent and that is correct, not a bug. What matters operationally is
    how many DIFFERENT squads the plan needs — you have to mod and position them
    all — so `distinct_squads` and the lineups themselves are reported.

    Returns {"opponents", "distinct_squads", "squads", "player_rank",
             "target_rank", "best_reachable_rank", "basis", "note"}.
    """
    gls = galactic_legends() if gls is None else gls
    owned = owned_g13(roster)
    squads = _fieldable(off_pool or [], owned, gls)
    if not shard or not shard.get("opponents"):
        return {"opponents": [], "distinct_squads": 0, "squads": [],
                "player_rank": player_rank, "target_rank": TARGET_RANK,
                "best_reachable_rank": None, "basis": "none",
                "note": "no shard capture — there is no ladder to plan against. "
                        "Drop data/arena/shard_<YYYYMMDD>.json in place."}

    if player_rank is None:
        player_rank = shard.get("player_rank")
    def_rates = rate_index(def_pool or [])
    cal = calibration(def_pool or [], off_pool or [])

    rows = []
    for opp in shard["opponents"]:
        atk = best_attack(squads, list(opp.get("squad") or []), counters, def_rates, cal)
        gain = (player_rank - opp["rank"]) if player_rank is not None else None
        rows.append({
            "rank": opp["rank"], "name": opp.get("name"), "gp": opp.get("gp"),
            "defense": list(opp.get("squad") or []),
            "attack": atk,
            "rank_gain": gain,
            "expected_gain": (round(gain * atk["win"] / 100.0, 2)
                              if gain is not None and atk else None),
        })

    if player_rank is None:
        rows.sort(key=lambda r: (-(r["attack"]["win"] if r["attack"] else -1), r["rank"]))
    else:
        rows.sort(key=lambda r: (-(r["expected_gain"] if r["expected_gain"] is not None
                                   else -1e9), r["rank"]))

    targets = [r for r in rows if r["rank_gain"] is None or r["rank_gain"] > 0]
    lineups, seen_keys = [], set()
    for r in targets:
        if not r["attack"]:
            continue
        k = tuple(r["attack"]["units"])
        if k not in seen_keys:
            seen_keys.add(k)
            lineups.append(list(k))
    reachable = [r["rank"] for r in targets
                 if r["attack"] and r["attack"]["win"] >= CONFIDENT_WIN]
    bases = {r["attack"]["basis"] for r in rows if r["attack"]}
    return {"opponents": rows, "distinct_squads": len(lineups), "squads": lineups,
            "player_rank": player_rank, "target_rank": TARGET_RANK,
            "best_reachable_rank": min(reachable) if reachable else None,
            "basis": ("counters" if "counters" in bases
                      else "modelled" if "modelled" in bases
                      else "aggregate" if bases else "none"),
            "note": None if squads else
                    "no fieldable attack squad in the offense pool (owned + G13+, <=1 GL)"}


# =============================================================================
# CLI
# =============================================================================

def _newest_roster():
    hits = sorted(glob.glob(os.path.join(DATA, "roster", "*.json")))
    return hits[-1] if hits else None


def build(player_rank=None):
    roster = swgoh_data.load_roster(ALLY, fallback_file=_newest_roster())
    def_pool, off_pool = load_pools()
    shard, counters = load_shard(), load_counters()
    defenses = candidate_defenses(roster, def_pool, counters, shard, off_pool=off_pool)
    plan = climb_plan(roster, off_pool, shard, counters, def_pool=def_pool,
                      player_rank=player_rank)
    return {
        "meta": {
            "mode": "squad-arena",
            "roster": roster["meta"].get("pulled"),
            "roster_source": roster["meta"].get("source"),
            "shard": (shard or {}).get("captured"),
            "counters": bool(counters),
            "def_pool": len(def_pool), "off_pool": len(off_pool),
            "proxy": ("swgoh.gg GAC 5v5 Hold%/Win%. GAC attackers are limited by the "
                      "no-repeat rule and arena attackers are not, so real arena hold "
                      "runs BELOW these numbers; the bias is near-uniform so it moves "
                      "the level, not the ranking."),
        },
        # What is ACTUALLY set in-game right now, straight from the shard capture.
        #
        # This is an OBSERVATION, not a recommendation, and it deliberately outranks
        # `defense` for anything downstream that asks "which units must be modded":
        # the deployed squad is the one that will actually defend tonight, whatever
        # the model would have picked. invest_plan.py reads it for tier 1.
        #
        # It matters here because `defense` is scored on GAC Hold%, and that proxy
        # OVERSTATES omicron-heavy walls in a mode where omicrons do not fire (see
        # the module docstring). Astra's real arena squad is an all-Hutt-Cartel
        # Rotta lead whose power is base abilities and zetas; the modelled #1 is the
        # 9-10-omicron Stranger wall. Trusting the model here would point the mod
        # optimiser at the wrong five characters.
        "deployed": list((shard or {}).get("player_squad") or []),
        "defense": defenses,
        "climb": plan,
    }


def main():
    player_rank = int(sys.argv[1]) if len(sys.argv) > 1 else None
    res = build(player_rank)
    nm = swgoh_data.load_name_type_map()
    name = lambda b: nm.get(b, {}).get("n", b)                      # noqa: E731
    line = lambda us: ", ".join(name(u) for u in us)                # noqa: E731

    m = res["meta"]
    print(f"SQUAD ARENA — roster {m['roster']} ({m['roster_source']}), "
          f"{m['def_pool']} defense / {m['off_pool']} offense meta squads")
    if m["shard"]:
        print(f"  ladder: shard captured {m['shard']}"
              + ("  + measured counters" if m["counters"] else ""))
    else:
        print("  ⚠ NO SHARD CAPTURE — scored on all-league GAC averages. "
              "Drop data/arena/shard_<YYYYMMDD>.json in place for real numbers.")
    print(f"  proxy: {m['proxy']}\n")

    print("DEFENSE — set ONE of these (top 5):")
    for e in res["defense"][:5]:
        print(f"  {e['score']:5.1f}%  [{e['basis']}]  {line(e['units'])}")
        print(f"          {e['why']}" + (f"  · relic {e['relic']}" if e["relic"] else ""))
    if not res["defense"]:
        print("  (nothing fieldable — every meta wall needs a unit you do not own at G13+)")

    plan = res["climb"]
    print(f"\nCLIMB — rank {plan['player_rank'] or '?'} -> target {plan['target_rank']}"
          f"   ({plan['distinct_squads']} distinct squad(s) needed)")
    if plan["note"]:
        print(f"  ⚠ {plan['note']}")
    for r in plan["opponents"][:10]:
        a = r["attack"]
        head = f"  #{r['rank']:<3} {(r['name'] or '?')[:18]:<18}"
        if not a:
            print(head + "  (no fieldable attack squad)")
            continue
        gain = f"  +{r['rank_gain']} ranks" if r.get("rank_gain") else ""
        print(head + f"  {a['win']:5.1f}% [{a['basis']}]{gain}")
        print(f"       hit with: {line(a['units'])}")
    if plan["best_reachable_rank"] is not None:
        print(f"\n  Highest rung at >={CONFIDENT_WIN}% : rank {plan['best_reachable_rank']}")

    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, "arena_result.json")
    json.dump(res, open(path, "w"), indent=1)
    print(f"\nwrote {path}")


if __name__ == "__main__":
    main()
