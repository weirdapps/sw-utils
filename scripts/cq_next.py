#!/usr/bin/env python3
"""Print the Conquest nodes that are actually adjacent to the player token.

`cq_step.py --scan` lists every bright ring on screen and its ordering repeatedly put
an unreachable node at the far edge first, so a runner built on it stalls with
"screen was not where the script expected". This narrows the list the only way that
matters: rings within one map-step of the four cyan chevrons that mark the token.

    python3 scripts/cq_next.py            # candidates, nearest first
    python3 scripts/cq_next.py --first    # just "X Y" for the best one
"""
import argparse
import sys

import numpy as np

import cq_auto as A
import cq_grind as G

# One map step is ~90px in the 1100-wide space on this layout; 150 leaves room for the
# diagonal branches without reaching the node after next.
STEP = 150


def marker(im):
    """Centre of the cyan chevrons, in DEVICE px. Saturated cyan is unique to the token:
    no node ring, keycard label or hex uses it."""
    a = np.asarray(im).astype(int)
    r, g, b = a[:, :, 0], a[:, :, 1], a[:, :, 2]
    m = (b > 170) & (g > 170) & (r < 130)
    m[:A.MAP_TOP] = False
    m[A.MAP_BOT:] = False
    ys, xs = np.nonzero(m)
    if len(xs) < 40:
        return None
    return int(xs.mean()), int(ys.mean())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--first", action="store_true")
    a = ap.parse_args()

    im = G.grab()
    here = marker(im)
    if here is None:
        print("no token in view", file=sys.stderr)
        return 1
    hx, hy = A.undev(*here)
    out = []
    for cx, cy, score in A.find_rings(im):
        jx, jy = A.undev(cx, cy)
        d = ((jx - hx) ** 2 + (jy - hy) ** 2) ** 0.5
        # Below ~55px the hit is the token's OWN node ring (Hough votes it several
        # times at slightly different centres), which the runner then re-plays forever.
        if 55 < d <= STEP:
            out.append((d, jx, jy, score, A.is_gold(im, cx, cy)))
    out.sort()
    if not out:
        print("no adjacent ring", file=sys.stderr)
        return 1
    if a.first:
        print(f"{out[0][1]} {out[0][2]}")
    else:
        print(f"token j=({hx}, {hy})")
        for d, jx, jy, score, gold in out:
            print(f"  j=({jx}, {jy}) dist={d:.0f} score={score:.0f} gold={gold}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
