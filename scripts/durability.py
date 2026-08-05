#!/usr/bin/env python3
"""
durability.py — how much of a squad's measured rate survives its datacron.

Earlier this was guessed from faction tags and it was wrong twice over: it missed
FOCUSED datacrons entirely (they key off ONE named character, not a faction), and
its haircut was so pervasive it scrambled the board. This version does not guess.

swgoh.gg's squad tier lists (/tier-list/gac/ and /tier-list/3v3/) break every
leader's rate down by which datacron affix the squad was running, and one of those
rows is:

    L9 – Unactivated affix / "Doesn't apply to this squad's units"   43.5% · 17.5K

That row IS the counterfactual: the same squads, measured in the battles where no
L9 datacron applied. ratio = baseline / headline is therefore a MEASURED estimate
of how much of the headline is owned rather than rented.

Worked example, and the reason this matters right now: Cassian Andor (Undercover)
reads 25.1% in 5v5 and 28.9% in 3v3, but his no-datacron baselines are 12.4% and
7.8% — ratios of 0.49 and 0.27, agreeing across two independent formats. He is one
of the four characters holding a Set 30 FOCUSED datacron, and Set 30 expires
2026-08-06. Roughly half to three-quarters of his wall disappears tomorrow.

Set 30 "Peace & Power" focused datacrons (verified from the variant list at
swgoh.gg/datacrons/30/): Cassian Andor (Undercover) · Darth Revan · Dedra Meero ·
Luminara Unduli. All four expire 2026-08-06T07:00Z, Allow Reroll: False.
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TIER = os.path.join(ROOT, "data", "meta", "raw_tierlist_scoped_20260805.json")

# Characters carrying a Set 30 FOCUSED datacron. A focused cron is character-scoped,
# so a faction/role heuristic cannot see it - this list has to be explicit.
SET30_FOCUSED = ["Cassian Andor (Undercover)", "Darth Revan", "Dedra Meero",
                 "Luminara Unduli"]
SET30_EXPIRY = "2026-08-06"

# A baseline row measured on fewer battles than this is noise (one leader's baseline
# sits on n=12).
MIN_BASELINE_N = 1000
# Ratios are clamped: the tier list is LEADER-level while the board is lineup-level,
# so the ratio is an indicator, not a conversion factor.
CLAMP = (0.35, 1.15)

_KEY = {("5v5", "def"): "d5", ("5v5", "off"): "o5",
        ("3v3", "def"): "d3", ("3v3", "off"): "o3"}


def _n(s):
    s = str(s).replace(",", "")
    try:
        if s.endswith("K"):
            return float(s[:-1]) * 1e3
        if s.endswith("M"):
            return float(s[:-1]) * 1e6
        return float(s)
    except ValueError:
        return 0.0


def load():
    """{(fmt, persp): {leader_name: {rate, baseline, ratio, dcDep, n}}}"""
    raw = json.load(open(TIER))
    if isinstance(raw, str):
        raw = json.loads(raw)
    out = {}
    for key, k in _KEY.items():
        table = {}
        for r in raw.get(k, {}).get("rows", []):
            base = next((a for a in r["affixes"]
                         if a["tier"] == "L9"
                         and ("Unactivated" in a["affix"] or "Doesn't apply" in a["affix"])), None)
            entry = {"rate": r["rate"], "dcDep": r.get("dcDep", False),
                     "baseline": None, "ratio": None, "n": None,
                     "focused": [a["affix"] for a in r["affixes"]
                                 if a["tier"] == "L9" and "Focused" in a["affix"]]}
            if base and r["rate"] and _n(base["n"]) >= MIN_BASELINE_N:
                entry["baseline"] = base["pct"]
                entry["n"] = base["n"]
                entry["ratio"] = max(CLAMP[0], min(CLAMP[1], base["pct"] / r["rate"]))
            table[r["leader"]] = entry
        out[key] = table
    return out


def squad_ratio(table, leader_name, units_names):
    """(ratio, note). ratio 1.0 == nothing measurable to discount."""
    e = table.get(leader_name)
    focused = [u for u in units_names if u in SET30_FOCUSED]
    if e and e["ratio"] is not None:
        note = (f"no-datacron baseline {e['baseline']}% vs {e['rate']}% headline "
                f"(n={e['n']})")
        if focused:
            note += f"; holds a Set 30 FOCUSED cron ({', '.join(focused)}) expiring {SET30_EXPIRY}"
        return e["ratio"], note
    if focused:
        # No published baseline, but the squad contains a character whose focused
        # datacron is expiring. Flag it without inventing a number.
        return 1.0, (f"contains {', '.join(focused)} — Set 30 FOCUSED datacron "
                     f"expires {SET30_EXPIRY}; no published baseline for this leader")
    if e and e.get("dcDep"):
        return 1.0, "swgoh.gg flags this leader 'Datacron dependent' (no baseline published)"
    return 1.0, None
