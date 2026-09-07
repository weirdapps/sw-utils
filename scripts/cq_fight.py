#!/usr/bin/env python3
"""Press BATTLE from the SELECT SQUAD screen, auto-fight, and clear the result cards.

`cq_farm.py` owns the whole loop (re-pan, tap node, fight, repeat) and is right when the
squad is already correct and the same node is being replayed. Feat farming is the other
shape: a hand-built squad, one node, one battle. This is that half of cq_farm, callable
on its own so the squad built by `cq_build.py` is not thrown away by re-entering the node.

    python3 scripts/cq_fight.py            # -> win | defeat | win-noreward
"""
import argparse
import sys

import autofight
import cq_farm as F
import cq_grind as G


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--timeout", type=int, default=420)
    a = ap.parse_args()

    st = G.state(G.grab())
    if st != "squad":
        print(f"not on the squad screen ({st})")
        return 1
    G.tap(*F.SQUAD_BATTLE, wait=8)
    autofight.run(a.timeout)
    print(F.dismiss())
    return 0


if __name__ == "__main__":
    sys.exit(main())
