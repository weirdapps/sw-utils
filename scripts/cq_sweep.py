#!/usr/bin/env python3
"""Re-fight a LIST of Conquest nodes once each, to convert dropped stars into keycards.

`cq_farm.py` replays ONE node N times, which is what feat farming wants. Star cleanup is
the other shape: every node that was cleared at 1/3 or 2/3 is worth 1-2 keycards to anyone
who goes back and wins it with the whole squad alive, and there are usually six or eight
of them scattered across the sector. Measured 2026-09-07: a 1/3 node re-fought went to
2/3 and the sector counter moved with it, so the star DELTA is paid on a replay.

    python3 scripts/cq_sweep.py 1:120,285 2:480,280 3:365,225

Each argument is `pan:x,y` in the 1100-wide space, anchored from the LEFT stop. The squad
already on the screen is the one that fights, so build it once with `cq_build.py` first;
it persists between Conquest battles. A node that no longer offers a green BATTLE is
skipped rather than retried forever.
"""
import argparse
import sys
import time

import autofight
import cq_farm as F
import cq_grind as G


def to_map():
    """Back out to the sector map before touching a map coordinate.

    ⛔ Skipping this is what makes a sweep destructive rather than merely useless: run
    from the SELECT SQUAD screen, `recentre`'s swipes and the node tap land on the roster
    grid instead, and the first tap REMOVES the squad leader. Observed 2026-09-07, three
    "unreachable" nodes in a row with the built squad quietly dismantled behind them.
    """
    for _ in range(4):
        # `state()` cannot be used for this. It returns "map" as its FALLBACK, and the
        # squad screen with a greyed-out BATTLE (squad not full) matches none of its
        # earlier tests, so it reads as "map" while sitting on exactly the screen this
        # guard exists to escape. CONQUEST STORE is the positive tell: teal at this spot
        # on a clean sector map, dark on the squad screen and behind an open node panel.
        if G.tealish(G.box(G.grab(), *G.P_STORE)):
            return True
        G.tap(37, 25, wait=3)
    return False


def fight_node(pan, x, y, timeout):
    if not to_map():
        return "not-on-map"
    for _ in range(4):
        F.recentre(pan, "left")
        G.tap(x, y, wait=4)
        im = G.grab()
        bonus = G.greenish(G.box(im, *F.BONUS_BATTLE))
        if bonus or G.greenish(G.box(im, *F.PANEL_BATTLE)):
            break
        time.sleep(5)
    else:
        return "unreachable"
    G.tap(*(F.BONUS_BATTLE if bonus else F.PANEL_BATTLE), wait=6)
    G.tap(*F.SQUAD_BATTLE, wait=8)
    autofight.run(timeout)
    return F.dismiss()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("nodes", nargs="+", help="pan:x,y")
    ap.add_argument("--timeout", type=int, default=420)
    a = ap.parse_args()

    for spec in a.nodes:
        pan, xy = spec.split(":")
        x, y = (int(v) for v in xy.split(","))
        print(f"[{spec}] {fight_node(int(pan), x, y, a.timeout)}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
