#!/usr/bin/env python3
"""Play the next reachable Conquest node, without ever leaving the sector map.

`cq_auto.py` pans the map looking for a frontier and, when it loses it, backs out
of a node panel -- which leaves the sector, lands on the chooser, and from there it
has walked into the wrong sector and into the Wandering Scavenger's shop. This is
the same loop with the wandering removed: it only ever taps rings that the current
view already shows, and if none of them is a playable node it stops and says so
rather than navigating.

    python3 scripts/cq_step.py --runs 6              # gold branch first
    python3 scripts/cq_step.py --runs 6 --prefer any
    python3 scripts/cq_step.py --scan                # what it can see right now

A node panel left open is harmless (it only covers the right third of the map), so
the escape from a wrong probe is another probe, never a back tap.
"""
import argparse
import sys
import time

import numpy as np

import cq_auto as A
import cq_grind as G

# Rings anywhere on the map are fair game. An earlier version capped this at 760 to
# keep the boss portrait out of the candidate list, and that silently cut off the whole
# right-hand side -- which is exactly where the frontier lives, because a sector runs
# left to right. Probing the boss is harmless: its panel is a normal Combat Details.
PROBE_MAX_X = 1060


def candidates(im, prefer="gold"):
    rings = [r for r in A.find_rings(im) if A.undev(r[0], r[1])[0] <= PROBE_MAX_X]
    rings.sort(key=lambda t: (t[0] - 990) ** 2 + (t[1] - 560) ** 2)
    if prefer == "gold":
        rings.sort(key=lambda t: not A.is_gold(im, t[0], t[1]))
    return rings


def close_panel(im):
    """Dismiss an open Combat Details panel by tapping empty map, never with back."""
    if G.state(im) == "combat_details":
        G.tap(150, 480, wait=2)
        return G.grab()
    return im


def pan(direction):
    """Slide the map one screen, in the MAP band.

    cq_auto pans at y=560, which on this layout is under the Combat Details panel and
    over the reward bar, so the swipe is swallowed and the runner concludes the map has
    no more nodes. y=250 is clear of both.
    """
    a, b = (200, 700) if direction == "left" else (700, 200)
    G.adb("shell", "input", "swipe", str(int(a * G.K)), str(int(250 * G.K)),
          str(int(b * G.K)), str(int(250 * G.K)), "400")
    time.sleep(2)


def player_marker(im):
    """Centre of the four cyan chevrons that mark where the token is, in device px.

    Ring brightness alone cannot tell the frontier from a node three screens back, and
    "nearest the centre of the screen" only holds right after a win. The chevrons are
    the one thing on the map that is always the player: a saturated cyan that no node
    ring, no keycard label and no hex uses.
    """
    a = np.asarray(im).astype(int)
    r, g, b = a[:, :, 0], a[:, :, 1], a[:, :, 2]
    m = (b > 170) & (g > 170) & (r < 130)
    m[:A.MAP_TOP] = False
    m[A.MAP_BOT:] = False
    ys, xs = np.nonzero(m)
    if len(xs) < 40:
        return None
    return int(xs.mean()), int(ys.mean())


def probe_view(prefer):
    im = close_panel(G.grab())
    cands = candidates(im, prefer)
    here = player_marker(im)
    if here:
        cands.sort(key=lambda t: (t[0] - here[0]) ** 2 + (t[1] - here[1]) ** 2)
        if prefer == "gold":
            cands.sort(key=lambda t: not A.is_gold(im, t[0], t[1]))
    for cx, cy, _ in cands:
        j = A.undev(cx, cy)
        G.tap(*j, wait=3)
        probe = G.grab()
        if G.state(probe) == "combat_details" and A.stars_banked(probe) < 3:
            return j
        close_panel(probe)
    return None


def pick(prefer):
    if G.state(G.grab()) == "squad":
        return "squad", None
    # Chase the player marker, not the screen centre. A probe tap does not recentre the
    # map, so a blind left/right sweep drifts away from the frontier and the runner
    # concludes the sector is finished three screens early.
    for step in range(10):
        im = close_panel(G.grab())
        if player_marker(im) is None:
            pan("right")          # a sector runs left to right; the token is ahead
            continue
        j = probe_view(prefer)
        if j:
            return "node", j
        # Marker in view but nothing playable next to it: widen by one screen.
        pan("right" if step % 2 == 0 else "left")
    return "none", None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", type=int, default=1)
    ap.add_argument("--prefer", choices=("gold", "any"), default="gold")
    ap.add_argument("--scan", action="store_true")
    a = ap.parse_args()

    if a.scan:
        im = G.grab()
        print("state:", G.state(im))
        for cx, cy, s in candidates(im, a.prefer):
            print(f"  ring j={A.undev(cx, cy)} score={s:.0f} gold={A.is_gold(im, cx, cy)}")
        return

    wins = 0
    for i in range(1, a.runs + 1):
        kind, target = pick(a.prefer)
        if kind == "none":
            print("no playable node in view; stopping", file=sys.stderr)
            break
        t0 = time.time()
        out = G.play(target or (0, 0))
        wins += out == "win"
        label = target if target else "pre-built squad"
        print(f"[{i}/{a.runs}] {out} at {label} in {time.time() - t0:.0f}s", flush=True)
        if out != "win":
            print("stopping: " + out, file=sys.stderr)
            break
    print(f"wins={wins}")


if __name__ == "__main__":
    main()
