#!/usr/bin/env python3
"""
rote_ops.py — Rise of the Empire (RotE) Territory Battle planner.

WHY THIS EXISTS
---------------
RotE is the one game mode where a single careless tap costs eight figures of
Territory Points, and it already has. On 2026-08-05 (memory/notes.md, "OPERATIONS
ARE THE PLATOONS") Astra deployed 10,283,960 unallocated GP to Felucia *before*
opening an Operation. Felucia Op1 was sitting at 14/15 and needed exactly one unit
he owned. Deploying is irreversible and makes a unit permanently ineligible for
operations, so that single ordering mistake burned >=22,000,000 TP.

This module exists so the allocation is decided on paper, in the right order,
before anything is tapped.

THE MEASURED ECONOMICS (on-device, phase 2; these numbers drive everything below)
---------------------------------------------------------------------------------
  * A combat mission deploys the squad's POWER immediately, win or lose. A WIN
    adds a flat 250,000 on top (fleet missions 500,000); a LOSS adds nothing
    further. Bracca 34,991,556 -> 35,453,904 on a 212,348-power win is exactly
    212,348 + 250,000.
    => Attempting is never worse than deploying, so every mission gets the
       strongest squad that is still free. There is no reason to "save" a GL.
  * OPERATIONS are the platoons: 6 per planet, 15 slots each, +11,000,000 TP per
    COMPLETED operation. Each slot names one SPECIFIC unit and gates it at
    Relic 6+ (characters) or 7 stars (ships). Quota: 10 assigned units per player
    per operation area.
    => ~733,000 TP per unit in an operation vs ~40,000 for deploying it. ~18x.
  * A DEPLOYED unit is PERMANENTLY INELIGIBLE for operations.

  Correct order every phase:
      Special missions -> Combat missions -> OPERATIONS -> deploy the remainder.
  The plan this module prints leads with OPERATIONS anyway, because the operations
  assignment is the RESERVATION LIST: it is the set of units that must survive the
  mission phase untouched. Compute it first, act on it in the order above.

THE ONE MODELLING DECISION WORTH ARGUING ABOUT
----------------------------------------------
The 11,000,000 pays on COMPLETION, and completion is GUILD-WIDE. Astra can fill at
most 10 of 15 slots, so he cannot complete an operation alone and it would be a lie
to credit him 11M for filling one slot. See GUILD_SLOT_FILL_P for the model, the
number, and the alternatives that were rejected.

WHAT IT EXPOSES
---------------
  eligible(roster, gate)                    owned units meeting a slot gate
  assign_operations(roster, areas, ...)     exact ILP (scipy/HiGHS), max expected TP
  readiness_gaps(roster, areas, within=2)   near-miss units, ranked -> what to farm
  mission_squads(roster, missions, ...)     strongest legal squad per mission
  plan(...) / main()                        output/rote_plan.json + printed plan

DATA SCHEMAS
------------
data/rote/operations_<phase>.json  (scraped from the operation panels):
    {"phase": 2, "captured": "2026-08-05",
     "areas": [{"planet": "Felucia", "operation": 1,
                "slots_total": 15,
                "slots_filled": 14,          # GUILD-WIDE fill count (the "14/15" badge)
                "slots": [{"unit": "KYLORENUNMASKED", "filled": false,
                           "gate": {"relic": 6}}, ...]}, ...]}

data/rote/missions_<phase>.json  (optional; drives mission_squads):
    {"phase": 2,
     "missions": [{"planet": "Bracca", "mission": "special", "kind": "special",
                   "slots": 2, "gate": {"relic": 7},
                   "required": ["CEREJUNDA", "JEDIKNIGHTCAL"]},
                  {"planet": "Geonosis", "mission": "g4", "kind": "combat",
                   "slots": 5, "gate": {"relic": 6},
                   "align": ["Dark Side", "Neutral"]},
                  {"planet": "Geonosis", "mission": "fleet", "kind": "fleet",
                   "slots": 8, "gate": {"stars": 7},
                   "pool": ["EXECUTOR", "..."]}]}

Run:  python3 scripts/rote_ops.py --phase 2
"""
import argparse
import json
import os
import sys
from collections import defaultdict

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import datacron_exposure as dx      # noqa: E402  (only for load_units(): the unit catalog)
import swgoh_data                   # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
ROTE = os.path.join(DATA, "rote")
OUT = os.path.join(ROOT, "output")
ROSTER_FILE = swgoh_data.latest_roster_file()

# --- measured constants (memory/notes.md, 2026-08-05 phase-2 session) -----------
OPERATION_TP = 11_000_000     # per COMPLETED operation, guild-wide
OPERATION_SLOTS = 15          # slots per operation area
QUOTA_PER_AREA = 10           # units one player may assign to one operation area
COMBAT_WIN_TP = 250_000       # flat bonus on a ground-mission win
FLEET_WIN_TP = 500_000        # flat bonus on a fleet-mission win

# THE RELIC ENCODING TRAP. The roster's `rt` is NOT the relic level the game shows.
# Device-verified: JML's tile reads R10 where the file says rt=12, and the
# Geonosians at rt 8/8/8/7/7 render R6/R6/R6/R5/R5 and were REJECTED by a
# "5x Geonosians (Relic 7+)" mission. So DISPLAYED = rt - 2:
#   "Relic 6+" is rt >= 8,  "Relic 7+" is rt >= 9.
# Units with no relic have rt = None; locked / pre-G13 units have rt = 1 (both
# floor to displayed 0). Every relic comparison in this file goes through
# displayed_relic() precisely because reading `rt` raw has burned this repo before.
RELIC_DISPLAY_OFFSET = 2


# --- the judgement layer --------------------------------------------------------
# GUILD_SLOT_FILL_P — the probability that a slot Astra leaves open is filled by
# somebody else before the phase ends.
#
# It exists because the 11,000,000 pays on COMPLETION and completion is GUILD-WIDE.
# Astra's quota is 10 of 15, so he can never complete an operation alone, and any
# model that credits him the whole prize for one slot is fiction. What he actually
# earns is the CAUSAL part: how much his k slots raise P(this operation completes).
#
# Model: treat each still-open slot as filled by the rest of the guild with
# probability p, independently. With R slots open,
#       P(complete | Astra fills k) = p ** (R - k)
#       value(k) = OPERATION_TP * (p**(R-k) - p**R)
# value(k) is CONVEX in k: the slot that finishes an operation is worth far more
# than the first slot of an empty one, which is exactly the "close to complete"
# behaviour the mode rewards. assign_operations() encodes it exactly (not as an
# approximation) with prefix-ordered step variables.
#
# p = 0.75 is measured-ish, not invented. In phase 2 the guild had driven Felucia
# Op1 to 14/15 and Op4 to 13/15 — most slots do get filled by someone — but those
# operations were still OPEN when Astra looked, because the slots that survive are
# by selection the ones few rosters cover. 0.75 keeps a 14/15 slot dominant
# (2.75M expected) while still valuing a fresh operation at ~246K/unit, i.e. well
# above the ~40K a deployment pays.
#
# REJECTED, do not retry:
#   p = 1.0  ("the guild always finishes")  -> every marginal value collapses to 0
#            and the objective is degenerate. Also empirically false: the two
#            operations we have hard numbers for did NOT finish.
#   p = 0.0  ("Astra completes it alone")   -> any operation with more than 10 open
#            slots is worth exactly zero, so the plan would say "skip every
#            operation early in a phase". Wrong: slots are first-come and progress
#            banks guild-wide.
#   Flat "11M x filled/15 pro-rata"         -> linear, so it cannot distinguish
#            14/15 from 0/15 at all. That indifference is the exact mistake that
#            cost 22M TP; a pro-rata model would have re-made it.
GUILD_SLOT_FILL_P = 0.75

# Reserving a unit for an operation means NOT deploying it, and deployment pays the
# unit's power. So the true price of an operation slot is the deployment TP forgone
# — which is also why `expected_tp` is reported net as well as gross. Set False to
# see the gross-only ranking.
COUNT_DEPLOY_OPPORTUNITY_COST = True

# The power proxy (used when the roster carries no per-unit `gp`) moved to
# swgoh_data.py on 2026-08-18, when the comlink loader became the only roster source
# and tw_wall.py needed the same fallback. Constants, provenance and unit_power()
# all live there now; this module delegates.

# The cats tag that marks a Galactic Legend in data/meta/raw_unit_categories_*.json.
# ONLY ONE GL PER SQUAD is permitted by the game; mission_squads enforces it from
# this tag rather than from a hardcoded list of the nine Astra owns, so a tenth GL
# needs no code change.
GL_TAG = "Galactic Legend"


# --- gates ----------------------------------------------------------------------
def displayed_relic(unit):
    """The relic level the GAME shows, from the roster's `rt`. See RELIC_DISPLAY_OFFSET.

    rt None (no relic) and rt 1 (locked / pre-G13) both floor to 0.
    """
    rt = unit.get("rt")
    if rt is None:
        return 0
    return max(0, rt - RELIC_DISPLAY_OFFSET)


def meets_gate(unit, gate):
    """Does one owned unit satisfy an operation-slot / mission gate?

    The gate KEY implies the combat type, because that is how the game states the
    requirement: "Assign Characters (Relic 6+) and Ships (7-Star)". So
    {"relic": N} is a character gate and {"stars": N} a ship gate, and a character
    can never satisfy a star gate however many stars it has.

    An unrecognised key raises rather than passing everything: a typo in a scraped
    requirements file must fail loudly, not silently make the whole roster eligible.
    """
    unknown = set(gate) - {"relic", "stars"}
    if unknown:
        raise ValueError(f"unknown gate key(s): {sorted(unknown)}")
    if "relic" in gate:
        if unit.get("ct", 1) != 1:
            return False
        if displayed_relic(unit) < gate["relic"]:
            return False
    if "stars" in gate:
        if unit.get("ct", 1) != 2:
            return False
        if (unit.get("r") or 0) < gate["stars"]:
            return False
    return True


def eligible(roster, gate):
    """The owned units meeting a slot gate, strongest first.

    Returns the roster unit dicts (not just baseIds) so callers can rank by power
    without a second lookup. Ordering is (power desc, baseId) so it is stable.
    """
    units = [u for u in roster.get("units", []) if meets_gate(u, gate)]
    units.sort(key=lambda u: (-unit_power(u), u["b"]))
    return units


def unit_power(unit):
    """Deployed power for one unit: the real `gp` when the roster carries it, else
    the documented proxy (see PROXY_* above).

    Delegates to swgoh_data so the proxy constants have ONE home — the comlink
    roster carries no `gp` at all, so every consumer needs this and a second copy
    would drift.
    """
    return swgoh_data.unit_power(unit)


# --- operation requirements ------------------------------------------------------
def operations_path(phase, root=ROTE):
    return os.path.join(root, f"operations_{phase}.json")


def load_operations(path):
    """Read a scraped operations file and normalise the two counts it may omit.

    `slots_filled` is the guild-wide badge ("14/15") and is authoritative when
    present, because a scrape can miss individual slot rows but the badge is one
    number on screen. When it is absent it is derived from the slot rows.
    """
    with open(path) as f:
        doc = json.load(f)
    for a in doc.get("areas", []):
        a.setdefault("slots_total", OPERATION_SLOTS)
        if "slots_filled" not in a:
            a["slots_filled"] = sum(1 for s in a.get("slots", []) if s.get("filled"))
    return doc


def remaining_slots(area):
    """Slots still open guild-wide in one operation area."""
    return max(0, area.get("slots_total", OPERATION_SLOTS) - area.get("slots_filled", 0))


def area_value(remaining, k, guild_fill_p=GUILD_SLOT_FILL_P):
    """Expected TP credited to a player for filling k of `remaining` open slots.

    OPERATION_TP * (p**(remaining-k) - p**remaining) — the rise in P(completed)
    that the player caused. See GUILD_SLOT_FILL_P.
    """
    k = max(0, min(k, remaining))
    p = guild_fill_p
    return OPERATION_TP * (p ** (remaining - k) - p ** remaining)


def _marginals(remaining, cap, guild_fill_p):
    """[value of the 1st slot, of the 2nd, ...] up to cap. Increasing by construction."""
    p = guild_fill_p
    return [OPERATION_TP * (p ** (remaining - k)) * (1.0 - p) for k in range(1, cap + 1)]


def assign_operations(roster, areas, already_deployed=frozenset(),
                      guild_fill_p=GUILD_SLOT_FILL_P, quota=QUOTA_PER_AREA):
    """Exact ILP: which owned unit goes into which operation slot.

    Maximises expected Territory Points subject to the rules the mode actually
    enforces:
      * each unit assigned at most once ACROSS EVERYTHING (a unit named by slots in
        three different operations can still only be spent once);
      * at most `quota` (10) units per player per operation AREA;
      * a unit may only fill a slot that NAMES it and whose gate it meets;
      * already-deployed units are excluded entirely — deployment is irreversible.

    Formulation (same scipy.optimize.milp / HiGHS pattern as optimize_board.py):
      x_j   binary, one per fillable slot.
      y_a,k binary, "area a receives at least k units", k = 1..cap_a.
    The per-area value is CONVEX in the number of slots filled (the completing slot
    is worth the most), and a convex maximum is not something an LP will find on its
    own, so it is encoded exactly: y_a,k carries the k-th marginal, the y's are
    forced into a prefix by y_a,k <= y_a,k-1, and sum(x in a) == sum(y in a) ties the
    count to the slots. The solver therefore banks marginals 1..k, never the top k.

    x_j additionally carries the unit's deployment power as a COST
    (COUNT_DEPLOY_OPPORTUNITY_COST): a unit reserved for an operation is a unit not
    deployed. A useful side effect is that when two units could fill the same
    count of slots, the solver spends the WEAKER one and leaves the stronger free
    for a combat mission.

    Returns {"assignments", "areas", "reserved", "expected_tp", "forgone_deploy_tp",
             "net_tp", "guild_fill_p", "assumption"}.
    """
    owned = {u["b"]: u for u in roster.get("units", [])}
    deployed = set(already_deployed)

    cand, per_area = [], defaultdict(list)
    for ai, area in enumerate(areas):
        if remaining_slots(area) <= 0:
            continue                                   # already complete: nothing to buy
        for slot in area.get("slots", []):
            if slot.get("filled"):
                continue
            base = slot.get("unit")
            unit = owned.get(base)
            if unit is None or base in deployed:
                continue
            if not meets_gate(unit, slot.get("gate") or {}):
                continue
            per_area[ai].append(len(cand))
            cand.append({"area": ai, "unit": base, "name": unit.get("n", base),
                         "gate": slot.get("gate") or {}, "power": unit_power(unit)})

    if not cand:
        return _empty_assignment(areas, guild_fill_p)

    n_x = len(cand)
    caps, y_col = {}, {}
    cols = n_x
    for ai, js in sorted(per_area.items()):
        caps[ai] = min(quota, remaining_slots(areas[ai]), len(js))
        for k in range(1, caps[ai] + 1):
            y_col[(ai, k)] = cols
            cols += 1

    cost = np.zeros(cols)                              # milp minimises
    if COUNT_DEPLOY_OPPORTUNITY_COST:
        for j, e in enumerate(cand):
            cost[j] = e["power"]
    for ai, cap in caps.items():
        for k, w in enumerate(_marginals(remaining_slots(areas[ai]), cap, guild_fill_p), 1):
            cost[y_col[(ai, k)]] = -w

    rows, lb, ub = [], [], []

    def add(coeffs, lo, hi):
        rows.append(coeffs)
        lb.append(lo)
        ub.append(hi)

    by_unit = defaultdict(list)
    for j, e in enumerate(cand):
        by_unit[e["unit"]].append(j)
    for js in by_unit.values():                        # each unit spent at most once
        if len(js) > 1:
            v = [0.0] * cols
            for j in js:
                v[j] = 1.0
            add(v, 0, 1)

    for ai, js in sorted(per_area.items()):
        v = [0.0] * cols                               # count == prefix length
        for j in js:
            v[j] = 1.0
        for k in range(1, caps[ai] + 1):
            v[y_col[(ai, k)]] = -1.0
        add(v, 0, 0)

        v = [0.0] * cols                               # the 10-per-area quota, explicit
        for j in js:
            v[j] = 1.0
        add(v, 0, quota)

        for k in range(2, caps[ai] + 1):               # y must be a prefix
            v = [0.0] * cols
            v[y_col[(ai, k)]] = 1.0
            v[y_col[(ai, k - 1)]] = -1.0
            add(v, -1, 0)

    res = milp(c=cost,
               constraints=LinearConstraint(np.array(rows, dtype=float),
                                            np.array(lb, dtype=float),
                                            np.array(ub, dtype=float)),
               integrality=np.ones(cols),
               bounds=Bounds(0, 1))
    if not res.success:
        raise RuntimeError(f"ILP failed: {res.message}")
    pick = res.x > 0.5

    chosen = defaultdict(list)
    assignments = []
    for j, e in enumerate(cand):
        if not pick[j]:
            continue
        chosen[e["area"]].append(e)
        assignments.append({"planet": areas[e["area"]].get("planet"),
                            "operation": areas[e["area"]].get("operation"),
                            "unit": e["unit"], "name": e["name"],
                            "gate": e["gate"], "power": e["power"]})

    out_areas, gross, forgone = [], 0.0, 0.0
    for ai, area in enumerate(areas):
        picked = chosen.get(ai, [])
        rem = remaining_slots(area)
        tp = area_value(rem, len(picked), guild_fill_p)
        gross += tp
        forgone += sum(e["power"] for e in picked)
        if picked or rem <= 0:
            out_areas.append({
                "planet": area.get("planet"), "operation": area.get("operation"),
                "remaining_before": rem, "assign": [e["unit"] for e in picked],
                "names": [e["name"] for e in picked],
                "completes": bool(picked) and len(picked) == rem,
                "expected_tp": round(tp)})
    out_areas.sort(key=lambda a: -a["expected_tp"])

    return {"guild_fill_p": guild_fill_p,
            "assumption": _ASSUMPTION.format(p=guild_fill_p),
            "assignments": assignments, "areas": out_areas,
            "reserved": sorted({a["unit"] for a in assignments}),
            "expected_tp": round(gross),
            "forgone_deploy_tp": round(forgone),
            "net_tp": round(gross - forgone)}


_ASSUMPTION = (
    "Operation completion is GUILD-WIDE and Astra's quota is 10 of 15 slots, so he "
    "cannot complete one alone. Each slot he leaves open is modelled as filled by "
    "the rest of the guild with p={p}; a slot is credited only with the rise in "
    "P(completed) that it causes. Near-complete operations therefore dominate.")


def _empty_assignment(areas, guild_fill_p):
    return {"guild_fill_p": guild_fill_p,
            "assumption": _ASSUMPTION.format(p=guild_fill_p),
            "assignments": [], "areas": [], "reserved": [],
            "expected_tp": 0, "forgone_deploy_tp": 0, "net_tp": 0}


# --- what to farm ------------------------------------------------------------------
def readiness_gaps(roster, areas, within=2, guild_fill_p=GUILD_SLOT_FILL_P):
    """Units Astra OWNS that miss an operation-slot gate by <= `within` tiers/stars.

    This is the actionable farming output: an operation slot is worth ~733K TP and
    a relic tier is a few days of farming, so "two relics off a slot" is a far
    better use of gear than most of the board. Only near misses are listed —
    a unit five relics short is not a plan, it is a wish.

    Ranked by how many operation slots the upgrade unlocks (the spec'd ordering),
    then by the smallest shortfall (cheapest first), then by TP. `tp` values each
    unlocked slot at that area's FIRST marginal, which is the conservative reading:
    it assumes the slot is the only one Astra adds there.

    Returns [{unit, name, kind, have, need, short, slots, areas, tp}].
    """
    owned = {u["b"]: u for u in roster.get("units", [])}
    agg = {}
    for area in areas:
        rem = remaining_slots(area)
        if rem <= 0:
            continue
        slot_tp = _marginals(rem, 1, guild_fill_p)[0]
        for slot in area.get("slots", []):
            if slot.get("filled"):
                continue
            unit = owned.get(slot.get("unit"))
            if unit is None:
                continue                                # unowned: that is farm_priority's job
            gate = slot.get("gate") or {}
            if meets_gate(unit, gate):
                continue                                # already fields it
            if "relic" in gate and unit.get("ct", 1) == 1:
                kind, have, need = "relic", displayed_relic(unit), gate["relic"]
            elif "stars" in gate and unit.get("ct", 1) == 2:
                kind, have, need = "stars", unit.get("r") or 0, gate["stars"]
            else:
                continue                                # wrong combat type: not a near miss
            short = need - have
            if short <= 0 or short > within:
                continue
            e = agg.setdefault(unit["b"], {
                "unit": unit["b"], "name": unit.get("n", unit["b"]), "kind": kind,
                "have": have, "need": need, "short": short, "slots": 0,
                "areas": [], "tp": 0.0})
            e["need"] = max(e["need"], need)
            e["short"] = max(e["short"], short)
            e["slots"] += 1
            e["areas"].append(f"{area.get('planet')} Op{area.get('operation')}")
            e["tp"] += slot_tp
    out = sorted(agg.values(), key=lambda e: (-e["slots"], e["short"], -e["tp"]))
    for e in out:
        e["tp"] = round(e["tp"])
    return out


# --- combat / special / fleet missions ----------------------------------------------
def load_catalog():
    """{baseId: {n, role, align, cats}} — the same swgoh.gg category dump
    datacron_exposure reads. It is CHARACTERS ONLY, which is why a fleet mission
    should carry an explicit `pool` instead of an `align` filter."""
    return dx.load_units()


def _mission_pool(roster, mission, catalog, blocked):
    """Owned units that could legally take a slot in one mission."""
    gate = mission.get("gate") or {}
    want_ct = 2 if "stars" in gate else 1
    aligns = mission.get("align")
    faction = mission.get("faction")
    pool_ids = set(mission.get("pool") or ())
    out = []
    for u in roster.get("units", []):
        b = u["b"]
        if b in blocked or u.get("ct", 1) != want_ct:
            continue
        if not meets_gate(u, gate):
            continue
        if pool_ids and b not in pool_ids:
            continue
        if aligns or faction:
            info = catalog.get(b)
            if info is None:
                continue        # cannot prove it matches -> do not field it
            if aligns and info.get("align") not in aligns:
                continue
            if faction and faction not in (info.get("cats") or ()):
                continue
        out.append(u)
    out.sort(key=lambda u: (-unit_power(u), u["b"]))
    return out


def _is_gl(base, catalog):
    return GL_TAG in ((catalog.get(base) or {}).get("cats") or ())


# Tags that are not a faction and so carry no squad synergy: a raid-eligibility
# list, a rarity class, a role and a ship-crew slot. Same list tw_wall.py uses.
NON_FACTION = {"Leader", "Order 66 Raid", "Galactic Legend", "Fleet Commander"}


def _disambiguate(names, bases):
    """Append the baseId to any DISPLAY NAME that repeats inside one squad.

    Two owned units are both called "Rey" — GLREY (the Galactic Legend) and REY —
    so a printed squad can read "Rey, Rey, Rey (Jedi Training)" and look like a bug
    or, worse, get the wrong one picked on the device. The baseIds are distinct and
    no unit is ever used twice; only the label collides.
    """
    dupes = {n for n in names if names.count(n) > 1}
    return [f"{n} [{b}]" if n in dupes else n for n, b in zip(names, bases)]


def _tag_sizes(catalog):
    size = {}
    for v in catalog.values():
        for c in v.get("cats") or ():
            size[c] = size.get(c, 0) + 1
    return size


def _affinity(anchor_cats, base, catalog, size):
    """Rarity-weighted count of faction tags shared with the squad's anchor.

    A shared "Phoenix" (7 units) is worth far more than a shared "Rebel" (52),
    because the small tag is the one a leader ability actually keys on.
    """
    cats = set((catalog.get(base) or {}).get("cats") or ()) - NON_FACTION
    return sum(1.0 / size.get(c, 1) for c in (cats & anchor_cats))


def _fill_coherently(pool, squad, free, catalog, size, has_gl):
    """Fill a squad's free slots with faction-mates of its anchor, not just the
    five strongest bodies on the roster.

    WHY, and it is measured on this account rather than assumed: a leader ability
    only benefits units of the matching faction, so five unrelated G13s field one
    working leader and four bystanders. notes.md 2026-08-12 recorded the same squad
    shape losing 0-for-5 in Territory War at 193,800 power while a coherent GL squad
    at similar power won — "a GL with filler bodies loses ... high squad power is a
    mirage".

    The ANCHOR is whatever the squad already has: its required units if the mission
    names any, otherwise the strongest legal unit, which is added first so that a
    mission with no requirements still leads with its best available unit (several
    tests pin that ordering). Power remains the tie-break, so among equally
    unrelated candidates this degrades to the old strongest-first behaviour.
    """
    if free > 0 and not squad:
        for u in pool:                                   # anchor = strongest legal
            if _is_gl(u["b"], catalog) and has_gl:
                continue
            squad.append(u)
            has_gl = has_gl or _is_gl(u["b"], catalog)
            free -= 1
            break
    anchor = set()
    for u in squad:
        anchor |= set((catalog.get(u["b"]) or {}).get("cats") or ())
    anchor -= NON_FACTION

    chosen = {u["b"] for u in squad}
    ranked = sorted((u for u in pool if u["b"] not in chosen),
                    key=lambda u: (-_affinity(anchor, u["b"], catalog, size),
                                   -unit_power(u), u["b"]))
    for u in ranked:
        if free <= 0:
            break
        if _is_gl(u["b"], catalog):
            if has_gl:
                continue
            has_gl = True
        squad.append(u)
        free -= 1
    return squad


def mission_squads(roster, missions, reserved=frozenset(), catalog=None):
    """Assign the strongest still-free squad to each mission.

    Rules, all of them load-bearing:
      * ONE GALACTIC LEGEND PER SQUAD — the game permits no more, so a plan with two
        is dead on arrival. Read from the catalog's "Galactic Legend" tag, not from
        a list of the nine Astra happens to own.
      * A unit `reserved` for an operation is untouchable. Committing a squad
        DEPLOYS it, and a deployed unit can never fill an operation slot again.
      * A unit is used by at most one mission.
      * Alignment / faction / relic-or-star gates come from the mission row.
      * A `required` unit's slot is LOCKED to that unit and cannot be substituted.
        The Bracca special ("Cere Junda R7+ + any Cal Kestis R7+") is 2 slots and
        both are named, so it fielded 66,739 power and lost — and no selection could
        have changed that. Free slots = slots - len(required); a required unit you
        cannot field leaves the squad short rather than pulling in a stranger.

    ORDERING is the measured lesson, not a detail. The in-game auto-fill produces
    good squads but will happily spend a gated unit on a mission that did not need
    it (it put Jabba into a special that Jabba was not required for), so:
      1. every unit named in any mission's `required` is pre-reserved from all the
         missions that do NOT require it;
      2. missions are then solved TIGHTEST-FIRST (least slack = candidates for the
         FREE slots, minus the number of free slots).
    A joint ILP over all missions was rejected: the squad's power is deployed win or
    lose, so total deployed power is the SAME whatever the allocation. The only
    thing selection moves is the flat 250K/500K win bonus, which is a step function
    of "is this squad strong enough", not linear in power. Maximising summed power
    would therefore optimise a quantity that does not vary. What does vary is
    whether a gated mission is left unfillable, and tightest-first is exactly the
    rule that protects it.

    Returns one row per mission, in the ORDER THEY SHOULD BE PLAYED:
      {planet, mission, kind, slots, units, names, power, win_tp, fillable,
       short, note}
    """
    catalog = load_catalog() if catalog is None else catalog
    size = _tag_sizes(catalog)
    blocked = set(reserved)
    required_anywhere = {b for m in missions for b in (m.get("required") or ())}

    ranked = []
    for idx, m in enumerate(missions):
        # Slack is measured over the FREE slots only, against a pool that excludes
        # every required unit anywhere: those are placed by name, not competed for.
        free = m.get("slots", 5) - len(m.get("required") or ())
        pool = _mission_pool(roster, m, catalog, blocked | required_anywhere)
        ranked.append((len(pool) - free, idx, m))
    ranked.sort(key=lambda t: (t[0], t[1]))

    used, rows = set(), []
    for _slack, _idx, m in ranked:
        own_required = list(m.get("required") or ())
        free = m.get("slots", 5) - len(own_required)

        squad, has_gl, notes = [], False, []
        named = {u["b"]: u for u in _mission_pool(roster, m, catalog, blocked | used)}
        for base in own_required:
            u = named.get(base)
            if u is None:
                notes.append(f"required unit {base} unavailable "
                             f"(unowned, gated, or already used)")
                continue
            if _is_gl(base, catalog) and has_gl:
                notes.append(f"required unit {base} is a second Galactic Legend "
                             f"— not legal")
                continue
            squad.append(u)
            has_gl = has_gl or _is_gl(base, catalog)

        pool = _mission_pool(roster, m, catalog, blocked | used | required_anywhere)
        _fill_coherently(pool, squad, free, catalog, size, has_gl)

        used.update(u["b"] for u in squad)
        short = m.get("slots", 5) - len(squad)
        win_tp = FLEET_WIN_TP if m.get("kind") == "fleet" else COMBAT_WIN_TP
        rows.append({"planet": m.get("planet"), "mission": m.get("mission"),
                     "kind": m.get("kind", "combat"), "slots": m.get("slots", 5),
                     "units": [u["b"] for u in squad],
                     "names": _disambiguate([u.get("n", u["b"]) for u in squad],
                                            [u["b"] for u in squad]),
                     "power": round(sum(unit_power(u) for u in squad)),
                     "win_tp": win_tp, "fillable": short <= 0,
                     "short": max(0, short), "note": "; ".join(notes) or None})
    return rows


# --- whole-phase plan ---------------------------------------------------------------
def plan(roster, areas, missions=(), already_deployed=frozenset(), catalog=None,
         guild_fill_p=GUILD_SLOT_FILL_P):
    """Operations -> missions -> deploy the remainder, in that dependency order.

    Operations are solved FIRST even though missions are PLAYED first, because the
    operations assignment is the reservation list the mission solver must respect.
    """
    ops = assign_operations(roster, areas, already_deployed=already_deployed,
                            guild_fill_p=guild_fill_p)
    reserved = set(ops["reserved"])
    squads = mission_squads(roster, missions, reserved=reserved | set(already_deployed),
                            catalog=catalog)

    spent = reserved | set(already_deployed) | {b for s in squads for b in s["units"]}
    remainder = [u for u in roster.get("units", []) if u["b"] not in spent]
    remainder.sort(key=lambda u: (-unit_power(u), u["b"]))
    deploy_tp = round(sum(unit_power(u) for u in remainder))

    return {
        "meta": {"gp": roster.get("meta", {}).get("gp"),
                 "pulled": roster.get("meta", {}).get("pulled"),
                 "source": roster.get("meta", {}).get("source")},
        "order": ["special missions", "combat missions", "OPERATIONS",
                  "deploy the remainder"],
        "operations": ops,
        "missions": squads,
        "deploy": {"units": len(remainder), "tp": deploy_tp,
                   "top": [u["b"] for u in remainder[:10]]},
        "readiness_gaps": readiness_gaps(roster, areas, guild_fill_p=guild_fill_p),
        "totals": {"operations_tp": ops["expected_tp"],
                   "mission_win_tp": sum(s["win_tp"] for s in squads if s["fillable"]),
                   "mission_power_tp": sum(s["power"] for s in squads),
                   "deploy_tp": deploy_tp},
    }


def _print(p, phase):
    ops = p["operations"]
    print(f"\nRotE phase {phase} — roster {p['meta'].get('pulled')} "
          f"({p['meta'].get('source')})")
    print("ACT IN THIS ORDER: " + " -> ".join(p["order"]))
    print("Everything in section 1 must survive the mission phase UNDEPLOYED.\n")

    print("=" * 78)
    print("1. OPERATIONS (the platoons) — assign these before you deploy anything")
    print("=" * 78)
    print(f"   {ops['assumption']}")
    for a in ops["areas"]:
        if not a["assign"]:
            continue
        flag = "  COMPLETES IT" if a["completes"] else ""
        print(f"\n   {a['planet']} Op{a['operation']}  "
              f"{a['remaining_before']} of {OPERATION_SLOTS} slots open  "
              f"-> assign {len(a['assign'])}  ~{a['expected_tp']:,} TP{flag}")
        for b, n in zip(a["assign"], a["names"]):
            print(f"       {n}  ({b})")
    print(f"\n   expected {ops['expected_tp']:,} TP gross, "
          f"{ops['net_tp']:,} net of the {ops['forgone_deploy_tp']:,} TP "
          f"these units would have deployed for.")

    print("\n" + "=" * 78)
    print("2. MISSIONS — play the tightest first so auto-fill cannot steal a gated unit")
    print("=" * 78)
    for s in p["missions"]:
        tag = "" if s["fillable"] else f"  UNFILLABLE (short {s['short']})"
        print(f"\n   {s['planet']} {s['mission']} [{s['kind']}] "
              f"power {s['power']:,} +{s['win_tp']:,} on a win{tag}")
        print("       " + ", ".join(s["names"]) if s["names"] else "       (no squad)")
        if s["note"]:
            print(f"       note: {s['note']}")

    print("\n" + "=" * 78)
    print("3. DEPLOY THE REMAINDER — last, and only what is left")
    print("=" * 78)
    print(f"   {p['deploy']['units']} units, ~{p['deploy']['tp']:,} TP")

    print("\n" + "=" * 78)
    print("4. READINESS GAPS — owned units a short farm away from an operation slot")
    print("=" * 78)
    for e in p["readiness_gaps"][:15]:
        print(f"   {e['name']:<28} {e['kind']} {e['have']} -> {e['need']} "
              f"(+{e['short']})  unlocks {e['slots']} slot(s)  ~{e['tp']:,} TP")
    if not p["readiness_gaps"]:
        print("   none within reach")

    t = p["totals"]
    print(f"\nPHASE TOTAL ~{sum(t.values()):,} TP"
          f"  (operations {t['operations_tp']:,} | mission wins {t['mission_win_tp']:,}"
          f" | mission power {t['mission_power_tp']:,} | deploy {t['deploy_tp']:,})")


def main(argv=None):
    ap = argparse.ArgumentParser(description="Rise of the Empire phase planner")
    ap.add_argument("--phase", type=int, default=1)
    ap.add_argument("--operations", help="default data/rote/operations_<phase>.json")
    ap.add_argument("--missions", help="default data/rote/missions_<phase>.json (optional)")
    ap.add_argument("--roster", default=ROSTER_FILE, help="fallback roster file")
    ap.add_argument("--allycode", default="145357294")
    ap.add_argument("--deployed", default="",
                    help="comma-separated baseIds already deployed this phase")
    ap.add_argument("--guild-fill-p", type=float, default=GUILD_SLOT_FILL_P)
    ap.add_argument("--out", default=os.path.join(OUT, "rote_plan.json"))
    args = ap.parse_args(argv)

    # Operations need an on-device scrape; MISSIONS do not — they are static and come
    # from the wiki map (scripts/rote_missions.py). Missing operations therefore
    # degrades to a mission-only plan instead of refusing to run, because "which squad
    # for which battle" is answerable today and was the whole reason the map exists.
    # The reservation list is empty in that mode, so the warning is not cosmetic: with
    # no operations known, nothing is held back and a mission may spend a unit that a
    # platoon slot wanted. Scrape the panels before acting on a plan that matters.
    ops_path = args.operations or operations_path(args.phase)
    if os.path.exists(ops_path):
        doc = load_operations(ops_path)
    else:
        doc = {"phase": args.phase, "captured": None, "areas": []}
        print(f"⚠ no operations file at {os.path.relpath(ops_path, ROOT)} — planning "
              f"MISSIONS ONLY.\n  Nothing is reserved for platoons, so scrape the "
              f"operation panels before committing squads.")

    missions = []
    mpath = args.missions or os.path.join(ROTE, f"missions_{args.phase}.json")
    if os.path.exists(mpath):
        with open(mpath) as f:
            missions = json.load(f).get("missions", [])

    roster = swgoh_data.load_roster(args.allycode, fallback_file=args.roster)
    deployed = {b.strip() for b in args.deployed.split(",") if b.strip()}
    p = plan(roster, doc.get("areas", []), missions=missions,
             already_deployed=deployed, guild_fill_p=args.guild_fill_p)
    p["meta"]["phase"] = doc.get("phase", args.phase)
    p["meta"]["captured"] = doc.get("captured")

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w") as f:
        json.dump(p, f, indent=1)
    _print(p, p["meta"]["phase"])
    print(f"\nwrote {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
