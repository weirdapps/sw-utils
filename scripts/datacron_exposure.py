#!/usr/bin/env python3
"""
datacron_exposure.py — which of a squad's rate is rented, and for how long.

swgoh.gg's Hold%/Win% is a record of last season, played under the datacrons that
were live then. Datacron sets EXPIRE, and when one does its bonus is simply gone -
so a squad whose rate leans on an expiring set will not repeat that number.

Live sets (each offers exactly two choices at each level; only the role/faction tiers
discriminate between squads, because the Light Side / Dark Side tiers apply to everyone):

  set 31  For Old Times        expires 2026-09-03  L6: Old Republic | Separatist
  set 32  Necessary Means      expires 2026-10-01  L3: Healer | Tank   L6: Attacker | Support
  set 33  Supremacy Directive  expires 2026-10-29  L6: Resistance | First Order

⚠ EXPIRY IS A DATE, NOT A COUNTDOWN (fixed 2026-08-17). This table used to carry a
hardcoded `days` field read off swgoh.gg on 2026-08-05, which meant it was wrong the
next morning and every morning after: by 2026-08-17 it still listed set 30 as live
with "1 day" left when the set had lapsed eleven days earlier, so every Sith and
Galactic Republic squad was being handed a phantom expiry haircut. Dates are read
once and stay true; `days_left()` derives the countdown from today.

⚠ THIS LIST STILL NEEDS A HUMAN. Since Jan 2026 datacrons release MONTHLY and live
THREE months, so exactly three sets are live at a time and a new one lands roughly
every 28 days — the next is due ~2026-08-26. `live_sets()` will correctly drop each
set as it expires, but it cannot invent the replacement: re-read swgoh.gg/datacrons
when a set lapses. Dates below came from the in-game datacron screen on 2026-08-12
and are corroborated by the 28-day spacing.

Consequence worth acting on: no live set grants a Sith or a Galactic Republic faction
bonus. Those factions have no datacron support at all right now.

`exposure()` scores each squad by how much of it is covered by each live affix,
weighted by the days that affix has left. Coverage is a proxy - a datacron sits on
one character and buffs matching allies - but it separates "half this squad is
Galactic Republic and the GR cron dies tomorrow" from "one member happens to be a
Healer".
"""
import json
import os
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CATS = os.path.join(ROOT, "data", "meta", "raw_unit_categories_20260805.json")

# `expires` stays an ISO STRING, not a date object: build_board.py dumps this table
# straight into board_result.json's meta block, and a date is not JSON-serializable.
SETS = [
    {"id": 31, "name": "For Old Times", "expires": "2026-09-03",
     "affixes": [("faction", "Old Republic"), ("faction", "Separatist")]},
    {"id": 32, "name": "Necessary Means", "expires": "2026-10-01",
     "affixes": [("role", "Healer"), ("role", "Tank"),
                 ("role", "Attacker"), ("role", "Support")]},
    {"id": 33, "name": "Supremacy Directive", "expires": "2026-10-29",
     "affixes": [("faction", "Resistance"), ("faction", "First Order")]},
]


def days_left(s, today=None):
    """Whole days until set `s` lapses. Negative once it has."""
    return (date.fromisoformat(s["expires"]) - (today or date.today())).days


def live_sets(today=None):
    """Sets that have not lapsed yet. An expired set grants nothing, so it must not
    contribute either a haircut or a 'leans on' note."""
    return [s for s in SETS if days_left(s, today) > 0]

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


def exposure(units, unit_map, min_coverage=0.0, today=None):
    """Return the affixes this squad is exposed to, best coverage first.

    Each entry: {set, name, days, kind, tag, coverage}. `today` is injectable so the
    result is reproducible in tests; it defaults to the real date.
    """
    have = [tags(unit_map[b]) for b in units if b in unit_map]
    if not have:
        return []
    out = []
    for s in live_sets(today):
        for kind, tag in s["affixes"]:
            if kind == "role":
                k = sum(1 for u in have if u["role"] == tag)
            else:
                k = sum(1 for u in have if tag in u["factions"])
            cov = k / len(have)
            if cov > min_coverage:
                out.append({"set": s["id"], "name": s["name"], "days": days_left(s, today),
                            "kind": kind, "tag": tag, "coverage": round(cov, 2)})
    out.sort(key=lambda x: (-x["coverage"], x["days"]))
    return out


def verdict(units, unit_map, today=None):
    """(multiplier, reason) for a squad, or (1.0, None) if nothing is expiring.

    Only an IMMINENT expiry is priced in. A month-out set is reported but not
    discounted: the board is rebuilt every season, so a 30-day risk will be
    re-optimised before it lands, and pricing it in would give up real value now.

    The haircut is CONTINUOUS in coverage rather than gated behind a threshold.
    A threshold produced a perverse result: solo SEE (1/1 Sith) took the full
    penalty while SEE + Wat Tambor (1/2 Sith) took none, even though it is the
    same Sith unit carrying the same datacron in both.
    """
    exp = exposure(units, unit_map, today=today)
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
