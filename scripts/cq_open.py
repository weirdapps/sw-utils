#!/usr/bin/env python3
"""Open the SELECT SQUAD screen for one Conquest node, verifying every step.

Hand-driving this costs three screenshots and lands in the Conquest INVENTORY about
one time in three, because the map re-centres on whatever was tapped last and the node
coordinate from the previous frame is then wrong. This re-pans from a stop (idempotent),
taps the node, checks a green BATTLE is actually there before pressing it, and stops
with a named state instead of walking somewhere unexpected.

    python3 scripts/cq_open.py --pan 3 --node 260 270      # -> squad screen, ready
    python3 scripts/cq_open.py --pan 3 --node 260 270 --panel-only
"""
import argparse
import sys
import time

import cq_farm as F
import cq_grind as G


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pan", type=int, default=0)
    ap.add_argument("--anchor", choices=("left", "right"), default="left")
    ap.add_argument("--node", type=int, nargs=2, required=True, metavar=("X", "Y"))
    ap.add_argument("--panel-only", action="store_true")
    a = ap.parse_args()

    for attempt in range(1, 7):
        F.recentre(a.pan, a.anchor)
        G.tap(*a.node, wait=4)
        im = G.grab()
        bonus = G.greenish(G.box(im, *F.BONUS_BATTLE))
        if bonus or G.greenish(G.box(im, *F.PANEL_BATTLE)):
            break
        print(f"no BATTLE at {a.node} (try {attempt})", flush=True)
        time.sleep(5)
    else:
        print("unreachable")
        return 1

    if a.panel_only:
        print("panel")
        return 0

    G.tap(*(F.BONUS_BATTLE if bonus else F.PANEL_BATTLE), wait=7)
    st = G.state(G.grab())
    print(st)
    return 0 if st == "squad" else 2


if __name__ == "__main__":
    sys.exit(main())
