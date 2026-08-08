#!/usr/bin/env python3
"""
invest_plan.py — turn the stated priority order into one ranked queue per resource.

THE INSIGHT THIS MODULE ENCODES
-------------------------------
"Arena first, then Grand Arena, then Rise of the Empire" sounds like a rule about
squads. It is not one. Those modes do not lock units from each other: the same
Galactic Legend can hold a Squad Arena rank overnight, clear a GAC 5v5 zone at
noon and be assigned to a RotE operation the same evening. Nothing about mode A's
line-up constrains mode B's. (The no-repeat rule this repo enforces elsewhere is
INSIDE one GAC format — defense locks, each unit attacks once — not across modes.)

Where the order actually bites is on the SHARED FINITE RESOURCES, because every
one of them is one-way:

  * a MOD sits on exactly one character at a time, so equipping it somewhere is
    unequipping it everywhere else — it is rival, permanently;
  * RELIC materials, GEAR and ability materials (zeta/omicron) are spent, not
    lent: poured into a unit, they never come back out.

So the priority order collapses to a single global ORDERING OVER UNITS, and every
resource queue is that one ordering filtered by what the resource can improve:

    relic materials -> owned characters below the relic target
    gear            -> owned characters below G13
    mods            -> characters only (ships take no mods at all)
    zeta / omicron  -> whatever a researched catalogue names, re-sorted

Rank once, filter many times. That is the whole module. Nothing here re-optimises
a squad; build_board.py already did that. This decides who eats first.

Run:  .venv/bin/python scripts/invest_plan.py
      -> output/invest_plan.json, output/invest_plan.md, output/mod_priority.txt
"""
import json
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import swgoh_data                      # noqa: E402

try:
    from zoneinfo import ZoneInfo
    _TODAY = datetime.now(ZoneInfo("Europe/Athens")).strftime("%Y-%m-%d")
except Exception:                       # pragma: no cover - tz db absent
    _TODAY = datetime.now().strftime("%Y-%m-%d")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
OUT = os.path.join(ROOT, "output")

ALLYCODE = "145357294"
ROSTER_FALLBACK = os.path.join(DATA, "roster", "swgoh_roster_fresh_20260805.json")
BOARD_RESULT = os.path.join(DATA, "board_result.json")      # build_board.py
ARENA_RESULT = os.path.join(OUT, "arena_result.json")       # arena_board.py (may not exist)
ROTE_PLAN = os.path.join(OUT, "rote_plan.json")             # rote_ops.py   (may not exist)
ABILITY_TARGETS = os.path.join(DATA, "ability_targets.json")
SHIP_CREW = os.path.join(DATA, "ship_crew.json")            # ships take no mods; their crew does
MOD_PRIORITY_TXT = os.path.join(OUT, "mod_priority.txt")

# =============================================================================
# THE PRIORITY LADDER — the judgement layer. Same bar as board_config.py: every
# rung carries the reason it sits where it does, and rejected alternatives are
# recorded so they are not retried.
#
# 1-3  ARENA. Squad Arena and Fleet Arena are the only modes that pay a ranked
#      reward EVERY DAY, and the payout compounds: crystals bought today raise
#      the farming rate that defends the rank tomorrow. Astra sits at Squad
#      Arena #10 and Fleet Arena #6, i.e. inside the band where one rank is real
#      money. GAC pays once a round; RotE once a phase.
#      1 before 2: the arena DEFENSE squad is on duty for the ~23 hours a day
#      nobody is playing, and it is what every attacker must beat. The climb
#      squads run five attempts and then stop. Same reasoning as 4-before-5.
#      3 after 1-2: a fleet cannot absorb the three biggest queues at all (see
#      the fleet note below), so its rung only decides ability materials.
#
# 4-9  GRAND ARENA, then TERRITORY WAR. GAC before TW because GAC is solo and
#      moves the player's OWN league (the repo's standing goal, Kyber 3 -> 2),
#      while TW defensive slots come from a guild-wide first-come pool where one
#      wall is one of ~150 and the result is not yours to determine.
#      DEFENSE before OFFENSE inside every mode, for the reason already recorded
#      in board_config.py: defense is the side you cannot adapt. It is set once
#      and then met by whoever turns up, so an under-invested wall gets found and
#      exploited. On offense you choose the matchup, so a shortfall is routed
#      around by sending a different squad.
#      5v5 before 3v3 is the WEAKEST claim on this ladder and is flagged as such.
#      The formats alternate seasons, so neither dominates, and 73 of Astra's 148
#      GAC units are on BOTH boards — for those the best-tier-wins rule makes the
#      ordering moot. It only decides format-unique units, and 5v5 goes first
#      because a 5-unit squad's rate depends on all five members while a 3v3
#      squad leans on its leader, so a weak support costs more in 5v5.
#
# 10   GAC FLEETS, below TW. This looks wrong and is not: ships take NO mods, NO
#      gear and NO relic materials, so the three heavy queues cannot touch them
#      wherever they sit. The one lever they do have is star-ups (MG-100 5*,
#      Raven's Claw 6*), which is shard farming — advisor.farm_priority's queue,
#      not this one. Fleet ARENA is the exception and sits at 3, because it pays
#      daily crystals.
#
# 11   RotE units — operations first, then combat missions. The player put Rise of
#      the Empire third. Its own gate is relic depth (operations demand
#      "Relic 6+", i.e. rt >= 8), which the relic queue already serves for every
#      unit that is also on a GAC board; RotE-ONLY units are the ones this rung
#      actually orders, and they eat last.
#
# 12   Everything else owned. Kept in the list on purpose: the insight above says
#      the order is a GLOBAL ordering over units, so the tail has to exist for
#      that claim to be true, and ability_queue uses membership here as the
#      ownership test. It is excluded from the mod list (see MOD_LIST_MAX_TIER).
#
# REJECTED: weighting the tiers into a single numeric score (e.g. arena x3) and
# sorting on score x rate. It re-mixes exactly what the player separated — a 96%
# GAC attacker would outrank a 30% arena wall, which inverts the stated order —
# and the weights would be invented. A strict lexicographic ladder cannot do that.
# =============================================================================

# arena_board.py writes {"meta", "defense": [...], "climb": {...}}. Alternative key
# names are accepted so a hand-written stand-in also loads.
ARENA_DEFENSE_KEYS = ("defense", "def", "wall")
ARENA_CLIMB_KEYS = ("climb", "offense", "off", "attack")
ARENA_CLIMB_SQUADS_KEY = "squads"
# Squad Arena has exactly ONE defensive slot. See _arena_roles for why that number
# has to be enforced here rather than assumed of the input.
ARENA_DEFENSE_SLOTS = 1

BOARD_ROLES = (
    (4, ("5v5", "defense"), "GAC 5v5 defense"),
    (5, ("5v5", "offense"), "GAC 5v5 offense"),
    (6, ("3v3", "defense"), "GAC 3v3 defense"),
    (7, ("3v3", "offense"), "GAC 3v3 offense"),
    (8, ("tw", "defense"), "TW defense"),
    (9, ("tw", "offense"), "TW offense"),
)

# board_result.json already carries the arena fleet as its own category, so when
# output/arena_result.json is missing the tier-3 rung still fills itself.
ARENA_FLEET_CATEGORY = "Fleet - Arena"
ARENA_FLEET_TIER = 3
GAC_FLEET_TIER = 10

# rote_ops.py's plan() writes {"operations", "missions", "deploy", ...}. "deploy" is
# deliberately absent from this list: the deploy list IS the leftover roster, which
# the ladder already calls tier 12, and reading it would flatten the whole tail into
# tier 11.
ROTE_SOURCES = (("operations", "RotE operations"),
                ("missions", "RotE combat mission"),
                ("assignments", "RotE operations"),
                ("units", "RotE"))
ROTE_TIER = 11
RESIDUAL_TIER = 12

# Grandivory assigns mods to the characters you SELECT. Adding the ~180 residual
# units would not "also improve them" — it would let the optimiser move good mods
# onto units that are never fielded. So the pasted list stops at 11.
MOD_LIST_MAX_TIER = 11

# --- the relic encoding, in one place ----------------------------------------
# The roster `rt` field is NOT the relic level the game prints on the unit tile.
# Device-verified: JML reads R10 where the file says rt 12; the Geonosians at
# rt 8/8/8/7/7 show R6/R6/R6/R5/R5 and were REJECTED by a "Relic 7+" RotE
# mission. So displayed = rt - 2, "Relic 6+" is rt >= 8 and "Relic 7+" is rt >= 9.
# Every relic number in this module is either a `*_rt` or a `*_displayed`; the
# two scales meet only in the two functions below.
RELIC_FIELD_OFFSET = 2
DEFAULT_TARGET_DISPLAYED_RELIC = 7


def rt_for_displayed_relic(displayed):
    """Roster `rt` value that corresponds to a relic level the game displays."""
    return displayed + RELIC_FIELD_OFFSET


def displayed_relic(rt):
    """Relic level the game displays for a roster `rt` value (None stays None)."""
    return None if rt is None else rt - RELIC_FIELD_OFFSET


DEFAULT_TARGET_RT = rt_for_displayed_relic(DEFAULT_TARGET_DISPLAYED_RELIC)  # 9


# --- tolerant plan readers ---------------------------------------------------
# The sub-node shapes below are read from the real producers (arena_board.py,
# rote_ops.py, build_board.py), but the readers stay tolerant of the other obvious
# spellings so a hand-written stand-in, or a producer that renames a key, degrades
# to "that rung contributed nothing" instead of a KeyError mid-plan.
_UNIT_KEYS = ("units", "slots", "assignments")
_ID_KEYS = ("unit", "b", "baseId", "id")
_RATE_KEYS = ("rate", "score", "win")


def _base_ids(seq):
    """baseIds out of a list that may hold plain strings or slot dicts."""
    out = []
    for x in seq or []:
        if isinstance(x, str):
            out.append(x)
        elif isinstance(x, dict):
            for k in _ID_KEYS:
                if isinstance(x.get(k), str):
                    out.append(x[k])
                    break
    return out


def _squads(node):
    """Pull [(rate, [baseId, ...]), ...] out of a loosely-shaped plan node.

    Accepts a squad dict {"units": [...], "rate": n}, a list of those, a bare
    list of baseIds, a list of slot dicts, or a dict of named squads. Absent or
    unrecognised input yields nothing rather than raising, because a missing
    upstream file must degrade to "that mode contributed no units", not a crash.

    It is a LEAF reader: callers point it at one documented sub-node. It is never
    turned loose on a whole plan file, because these files also carry OTHER
    PLAYERS' squads (arena_board's climb.opponents) and recursing into those would
    tier a shard rival's roster as if it were Astra's.
    """
    if node is None:
        return []
    if isinstance(node, dict):
        for key in _UNIT_KEYS:
            if key in node:
                members = _base_ids(node[key])
                if members:
                    rate = next((node[k] for k in _RATE_KEYS if node.get(k)), 0)
                    return [(float(rate), members)]
        out = []
        for v in node.values():
            if isinstance(v, (dict, list)):
                out += _squads(v)
        return out
    if isinstance(node, list):
        if node and all(isinstance(x, str) for x in node):
            return [(0.0, list(node))]
        out = []
        for v in node:
            out += _squads(v)
        return out
    return []


def _first(node, keys):
    for k in keys:
        if isinstance(node, dict) and k in node:
            return node[k]
    return None


def _reason(label, rate):
    return f"{label} ({rate:.0f}%)" if rate else label


def _arena_roles(arena):
    """Yield the Squad Arena rungs, read from arena_board.py's actual output.

    That file has two traps, both recorded here so this reader cannot fall in:

      * `defense` is candidate_defenses() — EVERY fieldable wall, ranked — not the
        one squad you park. Arena has a single defensive slot, so only the top
        entry earns tier 1. The rest are alternatives and keep whatever tier their
        other roles give them; promoting all of them would put a hundred units
        above the GAC board and empty the ladder of meaning.
      * `climb.opponents[*].defense` and `[*].attack` describe the SHARD, i.e.
        other players. Only `climb.squads` — the distinct lineups Astra owns — may
        be read. This is why _squads is never pointed at `climb` itself.
    """
    if not arena:
        return
    # An OBSERVED deployment beats a modelled one. arena_result.deployed is read
    # straight off the shard capture, i.e. the squad actually sitting on defense
    # right now — and that is the squad whose mods matter tonight, whatever the
    # model would have chosen. It also dodges a known bias: `defense` is ranked on
    # GAC Hold%, which overstates omicron-heavy walls in a mode where omicrons do
    # not fire, so the modelled #1 can be a squad you would never field.
    deployed = [u for u in (arena.get("deployed") or []) if u]
    if deployed:
        yield 1, "Squad Arena defense (deployed)", 0.0, deployed
    else:
        walls = _squads(_first(arena, ARENA_DEFENSE_KEYS))[:ARENA_DEFENSE_SLOTS]
        for rate, members in walls:
            yield 1, "Squad Arena defense", rate, members

    climb = _first(arena, ARENA_CLIMB_KEYS)
    if isinstance(climb, dict):
        climb = climb.get(ARENA_CLIMB_SQUADS_KEY)
    for rate, members in _squads(climb):
        yield 2, "Squad Arena climb", rate, members


def _rote_roles(rote):
    """Yield the Rise of the Empire rung, read from rote_ops.py's plan().

    `operations` is the prize — the 11M-TP platoon slots, worth ~733K TP per unit
    against ~40K for deploying the same unit. `missions` are the combat squads.
    `deploy` is deliberately not read; see ROTE_SOURCES.
    """
    for key, label in ROTE_SOURCES:
        for rate, members in _squads((rote or {}).get(key)):
            yield ROTE_TIER, label, rate, members


def load_ship_crew(path=SHIP_CREW):
    """{shipBaseId: [crew character baseId, ...]} from data/ship_crew.json.

    Missing file is not an error — the ladder just keeps listing ships that no
    mod queue can act on, which is the pre-2026-08-08 behaviour.
    """
    if not os.path.exists(path):
        return {}
    with open(path) as f:
        doc = json.load(f)
    crew = doc.get("crew") if isinstance(doc, dict) else doc
    return {ship: [c["unit"] for c in members] for ship, members in (crew or {}).items()}


def _roles(board, arena, rote):
    """Yield (tier, label, rate, [baseId, ...]) for every rung of the ladder.

    Member order is preserved: swgoh.gg lists a squad's LEADER first (build_board
    reads `units[0]` as the lead), and that order is the last tie-break below.
    """
    yield from _arena_roles(arena)

    board = board or {}
    for tier, (fmt, side), label in BOARD_ROLES:
        for rate, members in _squads((board.get(fmt) or {}).get(side)):
            yield tier, label, rate, members

    # FLEETS RESOLVE TO THEIR CREW, and that is the whole point of this block.
    #
    # Ships take no mods. A fleet's strength comes from the mods on the CREW
    # characters flying it, so yielding the ship baseIds alone puts entries in the
    # ladder that no mod, relic or gear queue can ever act on — every downstream
    # consumer filters to ct==1 and silently drops them.
    #
    # The bug that exposed this: Fleet Arena is the only arena that still pays
    # crystals (rank 1 ~400/day vs ~200 at rank 6), so it is near the top of the
    # priority ladder — yet Darth Revan, who IS the Leviathan, sorted ~89th in the
    # mod order and would have been handed leftovers.
    #
    # The ship is still yielded alongside the crew: it costs nothing (ships are
    # filtered out downstream) and it keeps the ladder readable as a board.
    crew_map = load_ship_crew()
    for cat, arr in (board.get("fleets") or {}).items():
        tier = ARENA_FLEET_TIER if cat == ARENA_FLEET_CATEGORY else GAC_FLEET_TIER
        for f in arr or []:
            ships = _base_ids(f.get("units"))
            crew = []
            for s in ships:
                for c in crew_map.get(s, []):
                    if c not in crew:
                        crew.append(c)
            label = f"{cat}: {f.get('name', '?')}"
            yield tier, label, 0.0, ships
            if crew:
                yield tier, f"{label} (crew)", 0.0, crew

    yield from _rote_roles(rote)


def _development(u):
    """Sort key for the tier-12 tail: most-developed first.

    No rate exists down here, so "how far along is it already" is the only signal
    the roster carries. gear/relic/stars only — `gp` is present in some saved
    roster files but NOT in the swgoh_data.map_roster shape, so it cannot be
    relied on.
    """
    return (-(u.get("g") or 0), -(u.get("rt") or 0), -(u.get("r") or 0), u["b"])


def priority_units(roster, board=None, arena=None, rote=None):
    """The single global ordering over units that every queue below is built from.

    Returns [{"unit": baseId, "name", "ct", "tier", "rate", "reason", "roles"}]
    sorted best-first. A unit filling several roles takes its BEST (lowest) tier;
    `rate` is then the strongest squad it appears in AT THAT TIER, which is what
    breaks ties inside a tier. Deliberately not the strongest squad at ANY tier:
    tiers mix hold% with win%, so a 30% wall and a 96% clear are not comparable
    numbers, but two walls in the same tier are.

    Last tie-break is the unit's SLOT in that squad, which puts the leader ahead
    of its fillers. Squad-mates share a rate exactly, so without it the order
    inside every squad would be alphabetical — arbitrary, and wrong for the one
    consumer that cares (Grandivory hands the best mods to whoever is listed
    first).

    Units named by a plan file but not owned are dropped — unlocking them is
    advisor.farm_priority's queue, not an investment queue.
    """
    owned = {u["b"]: u for u in roster.get("units", [])}
    best = {}
    for tier, label, rate, members in _roles(board, arena, rote):
        for slot, b in enumerate(members):
            if b not in owned:
                continue
            key = (tier, -rate, slot)
            e = best.get(b)
            if e is None:
                e = best[b] = {"unit": b, "roles": [], "key": key, "tier": tier,
                               "rate": rate, "reason": _reason(label, rate)}
            if label not in e["roles"]:
                e["roles"].append(label)
            if key < e["key"]:
                e["key"] = key
                e["tier"], e["rate"], e["reason"] = tier, rate, _reason(label, rate)

    ranked = sorted(best.values(), key=lambda e: (e["key"], e["unit"]))
    for e in ranked:
        del e["key"]
    ranked += [{"unit": u["b"], "tier": RESIDUAL_TIER, "rate": 0.0,
                "reason": "not on any board", "roles": []}
               for u in sorted((owned[b] for b in owned if b not in best), key=_development)]
    for e in ranked:
        u = owned[e["unit"]]
        e["name"] = u.get("n", e["unit"])
        e["ct"] = u.get("ct", 1)
    return ranked


def unowned_in_plans(roster, board=None, arena=None, rote=None):
    """baseIds the plan files name that the roster does not have — reported, not
    silently swallowed, because a typo'd baseId in a hand-written plan file would
    otherwise vanish without trace."""
    owned = {u["b"] for u in roster.get("units", [])}
    return sorted({b for _t, _l, _r, members in _roles(board, arena, rote)
                   for b in members if b not in owned})


def relic_queue(roster, priority, target_rt=DEFAULT_TARGET_RT):
    """Board units below a relic target, in priority order.

    `target_rt` is on the ROSTER scale, not the displayed one — pass
    rt_for_displayed_relic(7) rather than 7. The default is displayed relic 7.

    WHY THIS IS NOT advisor.relic_priority(): that one answers a different
    question and must keep answering it. It reads data/gac_result.json (GAC only),
    sorts by best_rate, and returns display NAMES in its `unit` field. This one
    spans every mode the ladder covers and sorts by the PLAYER'S order, which
    deliberately puts a 25%-hold arena wall above a 96% GAC attacker — re-sorting
    by rate would destroy the one thing this module exists to encode. It also
    returns baseIds in `unit`, with the display name in `name`. Two functions,
    two questions; the shared part is only the relic threshold test.

    Skips rt None (ships, and characters with no relic at all — the latter are
    still pre-G13, so they belong to gear_queue) and anything off the board.
    """
    rt_by_b = {u["b"]: u.get("rt") for u in roster.get("units", [])}
    out = []
    for e in priority:
        if e["tier"] >= RESIDUAL_TIER or e.get("ct", 1) != 1:
            continue
        rt = rt_by_b.get(e["unit"])
        if rt is None or rt >= target_rt:
            continue
        out.append({"unit": e["unit"], "name": e["name"], "tier": e["tier"],
                    "rt": rt, "relic": displayed_relic(rt),
                    "levels_to_go": target_rt - rt, "reason": e["reason"]})
    return out


def gear_queue(roster, priority):
    """Owned units below G13 that appear on the board, in priority order.

    Normally EMPTY, and that is a real answer rather than a broken one: every
    squad the board offers is filtered to G13+ before selection, so a non-empty
    result means a plan file (arena or RotE) is asking for a unit the GAC board
    would have refused. Gap units that are not owned at all are a different
    queue — advisor.farm_priority.
    """
    g_by_b = {u["b"]: u.get("g") for u in roster.get("units", [])}
    out = []
    for e in priority:
        if e["tier"] >= RESIDUAL_TIER or e.get("ct", 1) != 1:
            continue
        g = g_by_b.get(e["unit"])
        if g is None or g >= 13:
            continue
        out.append({"unit": e["unit"], "name": e["name"], "tier": e["tier"],
                    "gear": g, "tiers_to_go": 13 - g, "reason": e["reason"]})
    return out


def mod_priority_order(priority):
    """The flat list of character baseIds to select, in order, in Grandivory.

    This REPLACES the optimizer's "Auto-generate List" button. Auto-generate
    sorts GLs and generic meta walls to the top, which is a good answer to
    "who is strong" and the wrong answer to "who does Astra field first" — it
    knows nothing about this account's arena squad, its TW bank or its priority
    order. Characters only: ships take no mods.
    """
    seen, out = set(), []
    for e in priority:
        if e["tier"] > MOD_LIST_MAX_TIER or e.get("ct", 1) != 1:
            continue
        if e["unit"] in seen:
            continue
        seen.add(e["unit"])
        out.append(e["unit"])
    return out


def write_mod_priority(priority, path=MOD_PRIORITY_TXT):
    """One DISPLAY NAME per line — Grandivory's selection UI is searched by name,
    so the baseId list is useless to the human doing the pasting."""
    by_b = {e["unit"]: e for e in priority}
    names = [by_b[b]["name"] for b in mod_priority_order(priority)]
    with open(path, "w") as f:
        f.write("\n".join(names) + "\n")
    return names


def load_catalogue(path=ABILITY_TARGETS):
    """Load data/ability_targets.json.

    Accepts either a bare list of entries or {"targets": [...]}. The shipped file
    uses the object form only because JSON has no comments and the header has to
    live somewhere; both shapes are equally valid input.
    """
    if not os.path.exists(path):
        return []
    with open(path) as f:
        doc = json.load(f)
    if isinstance(doc, dict):
        return doc.get("targets") or []
    return doc or []


def ability_queue(priority, catalogue):
    """Researched zeta/omicron targets, re-sorted into the priority order.

    NOTHING here is invented. The catalogue is sourced from live research (an
    omicron's mode matters more than its unit: the same ability can be a Territory
    War monster and a dead zeta in Grand Arena), so this function only orders and
    filters it. Entries naming a unit that is not owned are dropped — priority is
    roster-complete down to tier 12, so absence from it IS the ownership test.
    """
    rank = {e["unit"]: i for i, e in enumerate(priority)}
    by_b = {e["unit"]: e for e in priority}
    out = []
    for i, entry in enumerate(catalogue):
        b = entry.get("unit")
        if b not in rank:
            continue
        e = by_b[b]
        out.append(dict(entry, name=e["name"], tier=e["tier"], reason=e["reason"],
                        _order=(rank[b], i)))
    out.sort(key=lambda x: x.pop("_order"))
    return out


# --- driver -------------------------------------------------------------------
def _load_json(path):
    try:
        with open(path) as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def load_inputs(board_path=BOARD_RESULT, arena_path=ARENA_RESULT, rote_path=ROTE_PLAN):
    """Read the three optional plan files. Returns (board, arena, rote, missing)
    where `missing` names the ones that were absent or unreadable, so the report
    can say what it did not know instead of quietly producing a thinner plan."""
    paths = {"board_result.json": board_path, "arena_result.json": arena_path,
             "rote_plan.json": rote_path}
    loaded = {k: _load_json(v) for k, v in paths.items()}
    missing = sorted(k for k, v in loaded.items() if v is None)
    return (loaded["board_result.json"], loaded["arena_result.json"],
            loaded["rote_plan.json"], missing)


def build(roster, board=None, arena=None, rote=None, catalogue=None, missing=()):
    """Assemble the whole plan from already-loaded inputs (pure, testable)."""
    priority = priority_units(roster, board, arena, rote)
    return {
        "meta": {"generated": _TODAY,
                 "roster": {"count": len(roster.get("units", [])),
                            "pulled": (roster.get("meta") or {}).get("pulled"),
                            "source": (roster.get("meta") or {}).get("source")},
                 "missing_inputs": list(missing),
                 "target_displayed_relic": DEFAULT_TARGET_DISPLAYED_RELIC,
                 "target_rt": DEFAULT_TARGET_RT,
                 "unowned_in_plans": unowned_in_plans(roster, board, arena, rote)},
        "priority": priority,
        "relic_queue": relic_queue(roster, priority),
        "gear_queue": gear_queue(roster, priority),
        "mod_priority": mod_priority_order(priority),
        "ability_queue": ability_queue(priority, catalogue or []),
    }


def _by_tier(entries):
    """Group a priority list by tier, preserving order inside each tier."""
    out = {}
    for e in entries:
        out.setdefault(e["tier"], []).append(e)
    return out


def render_markdown(result):
    m = result["meta"]
    L = [f"# Investment plan — {m['generated']}", "",
         f"Roster {m['roster']['count']} units (pulled {m['roster']['pulled']}, "
         f"source {m['roster']['source']}). Relic target = displayed R"
         f"{m['target_displayed_relic']} (rt >= {m['target_rt']}).", ""]
    if m["missing_inputs"]:
        L += [f"> Missing inputs: {', '.join(m['missing_inputs'])} — those rungs of the "
              "ladder contributed nothing.", ""]
    if m["unowned_in_plans"]:
        L += [f"> Plan files name {len(m['unowned_in_plans'])} unowned unit(s), skipped: "
              f"{', '.join(m['unowned_in_plans'][:10])}", ""]

    L += ["## Priority ladder", "", "| tier | units | leading unit |", "|---|---|---|"]
    for tier, entries in sorted(_by_tier(result["priority"]).items()):
        head = entries[0]
        L.append(f"| {tier} | {len(entries)} | {head['name']} — {head['reason']} |")

    L += ["", f"## Relic queue ({len(result['relic_queue'])})", ""]
    if result["relic_queue"]:
        L += ["| # | unit | relic | to go | tier | why |", "|---|---|---|---|---|---|"]
        L += [f"| {i} | {e['name']} | R{e['relic']} | +{e['levels_to_go']} | "
              f"{e['tier']} | {e['reason']} |"
              for i, e in enumerate(result["relic_queue"], 1)]
    else:
        L.append("Every board unit is already at the relic target.")

    L += ["", f"## Gear queue ({len(result['gear_queue'])})", ""]
    if result["gear_queue"]:
        L += ["| # | unit | gear | tier | why |", "|---|---|---|---|---|"]
        L += [f"| {i} | {e['name']} | G{e['gear']} | {e['tier']} | {e['reason']} |"
              for i, e in enumerate(result["gear_queue"], 1)]
    else:
        L.append("No board unit is below G13.")

    L += ["", f"## Mod optimizer list ({len(result['mod_priority'])} characters)", "",
          "Paste `output/mod_priority.txt` into Grandivory's selection in this order "
          "instead of pressing **Auto-generate List**.", ""]

    L += [f"## Ability materials ({len(result['ability_queue'])})", ""]
    if result["ability_queue"]:
        L += ["| # | unit | ability | kind | mode | tier | note |",
              "|---|---|---|---|---|---|---|"]
        L += [f"| {i} | {e['name']} | {e.get('ability', '')} | {e.get('kind', '')} | "
              f"{e.get('mode', '')} | {e['tier']} | {e.get('note', '')} |"
              for i, e in enumerate(result["ability_queue"], 1)]
    else:
        L.append("`data/ability_targets.json` is empty — it is populated from research, "
                 "never guessed. No zeta/omicron recommendation is made here.")
    return "\n".join(L) + "\n"


def main():
    os.makedirs(OUT, exist_ok=True)
    roster = swgoh_data.load_roster(ALLYCODE, fallback_file=ROSTER_FALLBACK)
    board, arena, rote, missing = load_inputs()
    result = build(roster, board, arena, rote, load_catalogue(), missing)

    with open(os.path.join(OUT, "invest_plan.json"), "w") as f:
        json.dump(result, f, indent=1)
    with open(os.path.join(OUT, "invest_plan.md"), "w") as f:
        f.write(render_markdown(result))
    write_mod_priority(result["priority"])

    if missing:
        print(f"missing inputs: {', '.join(missing)}")
    counts = {t: len(v) for t, v in sorted(_by_tier(result["priority"]).items())}
    print("priority tiers: " + " ".join(f"T{t}={n}" for t, n in counts.items()))
    print(f"relic queue {len(result['relic_queue'])} · gear queue {len(result['gear_queue'])} · "
          f"mod list {len(result['mod_priority'])} · abilities {len(result['ability_queue'])}")
    print("wrote output/invest_plan.json, output/invest_plan.md, output/mod_priority.txt")


if __name__ == "__main__":
    main()
