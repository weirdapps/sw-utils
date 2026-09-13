#!/usr/bin/env python3
"""build_current_mods.py: regenerate data/current_mods.json from the newest mods pull.

Why this exists: `data/current_mods.json` is the ONLY input `mod_analysis.py` has for
"what is actually equipped", and until 2026-09-12 nothing in the repo wrote it. It had
been hand-built on 2026-09-04 and was silently 8 days stale, so the gap report was
grading a roster that no longer existed and every slicing session made it staler.

    python3 scripts/build_current_mods.py            # newest data/mods_full_*.json
    python3 scripts/build_current_mods.py <file>

`speed` is the SUM OF MOD SPEED SECONDARIES on the unit's equipped mods. It is not the
unit's total speed and it does not include the +10% Speed-set bonus, which is a
percentage of base speed and therefore not comparable across units.
"""
import glob
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = os.path.join(ROOT, "data")

# swgoh set ids -> (name, pieces needed for the bonus)
SETS = {
    "1": ("Health", 2), "2": ("Offense", 4), "3": ("Defense", 2), "4": ("Speed", 4),
    "5": ("CritChance", 2), "6": ("CritDamage", 4), "7": ("Potency", 2),
    "8": ("Tenacity", 2),
}
NEED = {name: n for name, n in SETS.values()}


def newest_pull():
    files = sorted(glob.glob(os.path.join(D, "mods_full_*.json")))
    if not files:
        sys.exit("no data/mods_full_*.json, run scripts/pull_mods.py first")
    return files[-1]


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else newest_pull()
    raw = json.load(open(src))
    mods = raw["mods"]

    by_unit = {}
    for m in mods:
        b = m.get("b")
        if not b:
            continue                       # unequipped
        by_unit.setdefault(b, []).append(m)

    units = {}
    for b, ms in by_unit.items():
        counts = {}
        for m in ms:
            nm, _ = SETS.get(str(m.get("set")), ("Unknown", 2))
            counts[nm] = counts.get(nm, 0) + 1
        # Report only COMPLETE sets, the way the target strings are written; a 4-piece
        # set worn as 2 pieces grants nothing, so counting it would overstate the build.
        parts = []
        for nm, c in sorted(counts.items(), key=lambda kv: -kv[1]):
            whole = (c // NEED.get(nm, 2)) * NEED.get(nm, 2)
            if whole:
                parts.append(f"{nm}x{whole}")
        units[b] = {
            "mods": len(ms),
            "sets": ",".join(parts),
            "speed": sum(int(m.get("spd") or 0) for m in ms),
            "minLvl": min(int(m.get("lvl") or 0) for m in ms),
            "minRar": min(int(m.get("dots") or 0) for m in ms),
            "sixDot": sum(1 for m in ms if int(m.get("dots") or 0) >= 6),
            "spdArrow": any(m.get("spdArrow") for m in ms),
        }

    out = {
        "unitsWithMods": len(units),
        "validate": {"source": os.path.basename(src),
                     "gameDataAgeUtc": raw.get("gameDataAgeUtc"),
                     "mods": len(mods)},
        "units": units,
    }
    dst = os.path.join(D, "current_mods.json")
    json.dump(out, open(dst, "w"), indent=1)
    print(f"wrote {dst} from {os.path.basename(src)} | {len(units)} units, {len(mods)} mods")
    spd = sorted(v["speed"] for v in units.values())
    n = len(spd)
    print(f"mod-speed per unit: min {spd[0]} | p25 {spd[n//4]} | median {spd[n//2]} "
          f"| p75 {spd[3*n//4]} | max {spd[-1]}")


if __name__ == "__main__":
    main()
