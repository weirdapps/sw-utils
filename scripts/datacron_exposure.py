#!/usr/bin/env python3
"""
datacron_exposure.py — which of a squad's rate is rented, and for how long.

swgoh.gg's Hold%/Win% is a record of last season, played under the datacrons that
were live then. Datacron sets EXPIRE, and when one does its bonus is simply gone -
so a squad whose rate leans on an expiring set will not repeat that number.

Live sets, read from swgoh.gg/datacrons on 2026-08-05 (each set offers exactly two
choices at each level; only the role/faction tiers discriminate between squads,
because the Light Side / Dark Side tiers apply to everyone):

  set 30  Peace & Power        expires ~1 DAY    L6: Sith | Galactic Republic
  set 31  For Old Times        expires ~4 weeks  L6: Old Republic | Separatist
  set 32  Necessary Means      expires ~1 month  L3: Healer | Tank   L6: Attacker | Support
  set 33  Supremacy Directive  expires ~2 months L6: Resistance | First Order

The consequence worth acting on: once set 30 lapses, NO live set grants a Sith or a
Galactic Republic faction bonus. Those two factions lose datacron support outright
rather than trading it for something else.

`exposure()` scores each squad by how much of it is covered by each live affix,
weighted by the days that affix has left. Coverage is a proxy - a datacron sits on
one character and buffs matching allies - but it separates "half this squad is
Galactic Republic and the GR cron dies tomorrow" from "one member happens to be a
Healer".
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CATS = os.path.join(ROOT, "data", "meta", "raw_unit_categories_20260805.json")

SETS = [
    {"id": 30, "name": "Peace & Power", "days": 1,
     "affixes": [("faction", "Sith"), ("faction", "Galactic Republic")]},
    {"id": 31, "name": "For Old Times", "days": 28,
     "affixes": [("faction", "Old Republic"), ("faction", "Separatist")]},
    {"id": 32, "name": "Necessary Means", "days": 30,
     "affixes": [("role", "Healer"), ("role", "Tank"),
                 ("role", "Attacker"), ("role", "Support")]},
    {"id": 33, "name": "Supremacy Directive", "days": 60,
     "affixes": [("faction", "Resistance"), ("faction", "First Order")]},
]

# A squad is reported as leaning on an affix at or above this coverage.
LEAN = 0.6
# Days below which an expiring set is "imminent" and gets priced in.
IMMINENT = 7
# Haircut applied to a fully-covered squad losing an imminent affix. Modest on
# purpose: when a set lapses the opponent loses it too, so the effect is partly
# self-cancelling. Its job is to rank squads that OWN their rate above squads
# that RENT it, not to model the absolute drop.
MAX_HAIRCUT = 0.20


def load_units():
    d = json.load(open(CATS))
    return d["map"]


def tags(unit):
    """{'role': ..., 'factions': set()} for one unit entry."""
    return {"role": unit.get("role"), "factions": set(unit.get("cats") or [])}


def exposure(units, unit_map, min_coverage=0.0):
    """Return the affixes this squad is exposed to, best coverage first.

    Each entry: {set, name, days, kind, tag, coverage}.
    """
    have = [tags(unit_map[b]) for b in units if b in unit_map]
    if not have:
        return []
    out = []
    for s in SETS:
        for kind, tag in s["affixes"]:
            if kind == "role":
                k = sum(1 for u in have if u["role"] == tag)
            else:
                k = sum(1 for u in have if tag in u["factions"])
            cov = k / len(have)
            if cov > min_coverage:
                out.append({"set": s["id"], "name": s["name"], "days": s["days"],
                            "kind": kind, "tag": tag, "coverage": round(cov, 2)})
    out.sort(key=lambda x: (-x["coverage"], x["days"]))
    return out


def verdict(units, unit_map):
    """(multiplier, reason) for a squad, or (1.0, None) if nothing is expiring.

    Only an IMMINENT expiry is priced in. A month-out set is reported but not
    discounted: the board is rebuilt every season, so a 30-day risk will be
    re-optimised before it lands, and pricing it in would give up real value now.

    The haircut is CONTINUOUS in coverage rather than gated behind a threshold.
    A threshold produced a perverse result: solo SEE (1/1 Sith) took the full
    penalty while SEE + Wat Tambor (1/2 Sith) took none, even though it is the
    same Sith unit carrying the same datacron in both.
    """
    exp = exposure(units, unit_map)
    if not exp:
        return 1.0, None
    soon = [e for e in exp if e["days"] <= IMMINENT]
    if soon:
        e = soon[0]
        mult = 1.0 - MAX_HAIRCUT * e["coverage"]
        return mult, (f"{int(e['coverage'] * 100)}% {e['tag']} — datacron "
                      f"'{e['name']}' expires in ~{e['days']}d and no live set "
                      f"replaces {e['tag']}")
    lean = [e for e in exp if e["coverage"] >= LEAN]
    if not lean:
        return 1.0, None
    e = lean[0]
    return 1.0, (f"leans on {e['tag']} datacron '{e['name']}' (~{e['days']}d left)")
