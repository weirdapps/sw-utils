#!/usr/bin/env python3
"""rote_squads.py — turn the researched RotE per-node teams into a pushable squad tab.

WHY
---
`rote_missions.TACTICS` knows which squad to bring to every planned RotE node, but that
knowledge only helped if an agent happened to read the file mid-phase. In practice the
in-game squad picker was reached instead, and the game's auto-fill — which power-sorts and
routinely offers five different factions under a leader that buffs none of them — got used.
Measured 2026-08-20: preset squads cleared RotE missions in 50-330s; the one auto-fill squad
(219,948 power, five factions) took ~13 minutes and only survived because a GL soloed a wave.

So emit the plans as real saved squads, in the same envelope `upload_hotutils.py` already
speaks. Then the phase is played by opening SELECT SQUAD and taking "P3 Tatooine fennec",
which is the owner's standing instruction: *"we already have ready made tw-tb squads why not
use them?"*

ORDER MATTERS, and the sheet encodes it
---------------------------------------
Gated rows are played FIRST. The auto-fill will spend a gated unit on a row that did not need
it — it put Jabba into two Felucia missions while Jabba's own mission sat unplayed — and once
that happens the gated row is dead for the phase. Specials, then unit-gated combat, then
faction-gated, then the free rows.

Run:  python3 scripts/rote_squads.py                 # all phases -> output/rote_squads.json
      python3 scripts/rote_squads.py --phase 3       # one phase, and print its play order
      HU_SID=<live> python3 scripts/upload_hotutils.py --sync \\
          --payload output/rote_squads.json
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import rote_missions as rm                                          # noqa: E402
import swgoh_data as sd                                             # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "output")

# In-game preset tabs stop accepting squads somewhere around 15 (TW 5v5 - Defense ends at
# D15), so the category is per PHASE rather than one giant "TB RotE" tab.
CATEGORY = "TB RotE - P{phase}"


def _priority(mission):
    """Play order inside a phase. Lower goes first.

    A gated row can only ever be played by the unit that gates it, so it is the row most
    easily lost to a careless auto-fill elsewhere. Free rows can be filled from whatever
    survives, so they go last.
    """
    if mission["kind"] == "special":
        return 0
    if mission.get("required"):
        return 1
    if mission.get("faction"):
        return 2
    return 3


def plan(phase, name_map=None):
    """[(mission, tactics, display_name)] for one phase, in play order."""
    names = name_map if name_map is not None else sd.load_name_type_map()
    rows = []
    for m in rm.build(phase)["missions"]:
        tac = m.get("tactics")
        if not tac or not tac.get("squad"):
            continue
        marks = ""
        if m.get("auto") is False:
            marks += " MANUAL"
        if tac.get("aspirational"):
            marks += " [aspir]"
        rows.append((m, tac, f"P{phase} {m['planet']} {m['mission']}{marks}"))
    rows.sort(key=lambda r: (_priority(r[0]), r[0]["planet"], r[0]["mission"]))
    return rows, names


def definitions(phases=range(1, 7), name_map=None):
    """upload_hotutils.py's envelope: {n, sz, ct, cat, u:[[baseId, name], ...]}."""
    out, names = [], name_map if name_map is not None else sd.load_name_type_map()
    for phase in phases:
        rows, _ = plan(phase, names)
        for _mission, tac, label in rows:
            squad = tac["squad"]
            out.append({
                "n": label,
                "sz": len(squad),
                "ct": 1,
                "cat": CATEGORY.format(phase=phase),
                "u": [[b, (names.get(b) or {}).get("n", b)] for b in squad],
            })
    return out


def sheet(phase, name_map=None):
    rows, names = plan(phase, name_map)
    if not rows:
        return f"RotE phase {phase} — no planned squads yet.\n"
    floor = rm.PHASES[phase]["relic"]
    lines = [f"ROTE PHASE {phase} — PLAY ORDER (relic floor R{floor}+)",
             "Gated rows first: the auto-fill will spend a gated unit on a row that did not",
             "need it, and that kills the gated row for the whole phase.", ""]
    for i, (mission, tac, _label) in enumerate(rows, 1):
        who = " · ".join((names.get(b) or {}).get("n", b) for b in tac["squad"])
        tag = {0: "SPECIAL", 1: "GATED  ", 2: "FACTION", 3: "free   "}[_priority(mission)]
        lines.append(f"{i:>2}. [{tag}] {mission['planet']} / {mission['mission']}")
        lines.append(f"      {who}")
        if mission.get("required"):
            lines.append(f"      requires: {', '.join(mission['required'])}")
        if mission.get("reward"):
            lines.append(f"      reward: {mission['reward']}")
        if tac.get("aspirational"):
            lines.append("      ⚠ ASPIRATIONAL — not fillable on the current roster")
        lines.append("")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--phase", type=int, help="print one phase's play order")
    ap.add_argument("--write", action="store_true", default=True)
    args = ap.parse_args()

    if args.phase:
        print(sheet(args.phase))

    defs = definitions()
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, "rote_squads.json")
    with open(path, "w") as f:
        json.dump(defs, f, separators=(",", ":"))
    by_cat = {}
    for d in defs:
        by_cat[d["cat"]] = by_cat.get(d["cat"], 0) + 1
    print(f"wrote {path}: {len(defs)} squads")
    for cat, n in sorted(by_cat.items()):
        print(f"  {n:>3}  {cat}")
    if defs:
        print("\npush with:  HU_SID=<live> python3 scripts/upload_hotutils.py --sync "
              "--payload output/rote_squads.json")


if __name__ == "__main__":
    main()
