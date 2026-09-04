#!/usr/bin/env python3
"""Conquest sector runner: walk a sector map on its own, node after node.

`cq_grind.py` plays ONE node repeatedly, which is right for a repeatable bonus node
and useless for a sector, where every win moves you and the next fight is somewhere
else on the map. This finds the next thing to do by looking at the map:

  * a combat node is a bright RING (dim rings are unreachable), and the side panel
    tells you whether its three stars are already banked;
  * a data-disk pile or a scavenger is a bright GREEN HEX, which has no BATTLE
    button and has to be committed through instead.

    .venv/bin/python scripts/cq_auto.py --runs 12          # play up to 12 nodes
    .venv/bin/python scripts/cq_auto.py --scan             # just print what it sees

Disk piles are auto-committed on the FIRST option unless --no-disk is passed; the
choice matters much less than not stalling the run, and Pass+ makes swapping free.
"""
import argparse
import math
import sys
import time

import numpy as np


import cq_grind as G

K = G.K  # 1920 / 1100

# Star pips on the Combat Details panel, in 1100-space. Yellow means banked.
STARS = [(786, 182), (812, 182), (838, 182)]
# The map area, in device pixels: below the title bar, above the reward bar.
MAP_TOP, MAP_BOT, MAP_LEFT, MAP_RIGHT = 260, 870, 60, 1900


def dev(x, y):
    return int(x * K), int(y * K)


def undev(x, y):
    return int(x / K), int(y / K)


def bright_mask(a):
    return a.min(axis=2) > 140


def green_mask(a):
    r, g, b = a[:, :, 0].astype(int), a[:, :, 1].astype(int), a[:, :, 2].astype(int)
    return (g > 140) & (g - r > 35) & (g - b > 35)


def ring_hits(mask, cx, cy, r, step=20):
    hits = 0
    n = 0
    h, w = mask.shape
    for ang in range(0, 360, step):
        x = cx + int(r * math.cos(math.radians(ang)))
        y = cy + int(r * math.sin(math.radians(ang)))
        if 0 <= x < w and 0 <= y < h:
            n += 1
            hits += bool(mask[y, x])
    return hits, n


def find_rings(im):
    """Bright node rings on the map, as (x, y) device centres, left to right.

    Hough voting rather than sampling a fixed radius: an available node is a THIN
    bright circle and a cleared one a thick amber one, so any single-radius probe
    finds one and misses the other.
    """
    a = np.asarray(im)
    mask = bright_mask(a)
    mask[:MAP_TOP] = False
    mask[MAP_BOT:] = False
    mask[:, :MAP_LEFT] = False
    mask[:, MAP_RIGHT:] = False
    ys, xs = np.nonzero(mask)
    if not len(xs):
        return []
    h, w = mask.shape
    acc = np.zeros((h // 4 + 1, w // 4 + 1), dtype=np.int32)
    for r in (34, 38, 42, 46):
        for ang in range(0, 360, 15):
            dx = int(r * math.cos(math.radians(ang)))
            dy = int(r * math.sin(math.radians(ang)))
            cy = (ys + dy) // 4
            cx = (xs + dx) // 4
            ok = (cy >= 0) & (cy < acc.shape[0]) & (cx >= 0) & (cx < acc.shape[1])
            np.add.at(acc, (cy[ok], cx[ok]), 1)
    peaks = np.argwhere(acc > 260)
    found = [(int(cx * 4), int(cy * 4), int(acc[cy, cx])) for cy, cx in peaks]
    return suppress(found)


def find_hexes(im):
    """Bright green stockpile/scavenger hexes, as (x, y) device centres."""
    a = np.asarray(im)
    mask = green_mask(a)
    found = []
    for cy in range(MAP_TOP, MAP_BOT, 10):
        for cx in range(MAP_LEFT, MAP_RIGHT, 10):
            blob = mask[cy - 20:cy + 20, cx - 24:cx + 24]
            if blob.size and blob.mean() > 0.35:
                found.append((cx, cy, blob.mean()))
    return suppress(found)


def suppress(found, radius=70):
    """Keep the strongest candidate in each radius, then order left to right."""
    kept = []
    for cx, cy, score in sorted(found, key=lambda t: -t[2]):
        if all((cx - x) ** 2 + (cy - y) ** 2 > radius ** 2 for x, y, _ in kept):
            kept.append((cx, cy, score))
    return sorted(kept, key=lambda t: t[0])


def stars_banked(im):
    return sum(1 for x, y in STARS if G.box(im, x, y, w=10, h=10)[0] > 150)


def is_gold(im, cx, cy):
    """Challenge-Path nodes ring amber; ordinary ones ring cyan."""
    a = np.asarray(im)
    patch = a[max(0, cy - 46):cy + 46, max(0, cx - 46):cx + 46].reshape(-1, 3).astype(int)
    lit = patch[(patch.max(axis=1) > 110) & (patch.min(axis=1) < 200)]
    if not len(lit):
        return False
    return lit[:, 0].mean() - lit[:, 2].mean() > 10


def pan(direction, ms=350):
    """Slide the sector map one screen. "left" means show more of the map's start."""
    a, b = ("500", "1450") if direction == "left" else ("1450", "500")
    G.adb("shell", "input", "swipe", a, "560", b, "560", str(ms))
    time.sleep(2)


def on_sector_list(im):
    """The chooser has a green ENTER per unlocked sector; the map has none there."""
    return G.greenish(G.box(im, 648, 246)) or G.greenish(G.box(im, 648, 448))


def back_to_map(tries=3):
    """Get back to the sector map WITHOUT over-backing into the sector chooser.

    The back arrow on a node panel leaves the sector entirely, and the chooser also
    carries a CONQUEST STORE button, so a naive "am I on the map" probe reads true
    there and the runner then taps a sector portrait and walks into the wrong sector.
    An open node panel is harmless: it only hides the right third of the map.
    """
    for _ in range(tries):
        im = G.grab()
        if on_sector_list(im):
            raise SystemExit("backed out into the sector chooser; re-enter by hand")
        if G.state(im) == "squad":
            G.tap(33, 33, wait=3)
            continue
        return im
    return G.grab()


def take_disk(pick=1):
    """Commit the Nth option of a stockpile, then back out of the inventory.

    Verifies the MOVE TO ... confirmation actually appeared: tapping a hex that has
    already been spent does nothing, and blind-tapping COMMIT afterwards walks the
    session into the reward-track screen.
    """
    G.tap(900, 100 + pick * 90, wait=2)
    im = G.grab()
    if not G.greenish(G.box(im, 718, 531)):
        return False
    G.tap(718, 531, wait=6)        # COMMIT drops you into the Conquest inventory
    G.tap(33, 33, wait=5)
    return True


def play_at(node):
    out = G.play(node)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", type=int, default=1)
    ap.add_argument("--scan", action="store_true")
    ap.add_argument("--no-disk", action="store_true")
    ap.add_argument("--prefer", choices=("gold", "any"), default="gold")
    a = ap.parse_args()

    if a.scan:
        im = G.grab()
        print("state:", G.state(im))
        for cx, cy, s in find_rings(im):
            print(f"  ring  dev=({cx},{cy}) j={undev(cx, cy)} score={s:.2f} "
                  f"gold={is_gold(im, cx, cy)}")
        for cx, cy, s in find_hexes(im):
            print(f"  hex   dev=({cx},{cy}) j={undev(cx, cy)} fill={s:.2f}")
        return

    played = 0
    for i in range(1, a.runs + 1):
        # A squad you assemble is only committed by pressing BATTLE. Backing out of
        # the squad screen throws it away, so if a hand-built squad is sitting there,
        # fight with it rather than navigating past it.
        if G.state(G.grab()) == "squad":
            t0 = time.time()
            out = G.play((0, 0))
            played += out == "win"
            print(f"[{i}] {out} (pre-built squad) in {time.time() - t0:.0f}s", flush=True)
            if out.startswith("stuck") or out == "loss":
                break
            continue

        target = None
        took_disk = False
        # Sweep the whole sector left to right rather than trusting the view to be
        # centred on the player: it is right after a win, and is not after a probe
        # tap or a stockpile, and a runner that panned once could never find its way
        # back to the frontier.
        for attempt in range(10):
            im = back_to_map()
            if attempt == 1:
                # Lost the frontier: rewind to the sector's start and sweep right.
                for _ in range(5):
                    pan("left")
                im = G.grab()
            elif attempt > 1:
                pan("right")
                im = G.grab()
            rings = find_rings(im)
            # The map recentres on the player after every win, so the frontier is the
            # cluster nearest the middle of the screen. Sorting by raw x sent the
            # runner off to unreachable nodes at the sector's far end.
            rings.sort(key=lambda t: (t[0] - 990) ** 2 + (t[1] - 560) ** 2)
            if a.prefer == "gold":
                rings.sort(key=lambda t: not is_gold(im, t[0], t[1]))
            for cx, cy, _ in rings:
                j = undev(cx, cy)
                G.tap(*j, wait=3)
                probe = G.grab()
                if G.state(probe) == "combat_details" and stars_banked(probe) < 3:
                    target = j
                    break
                # A stockpile hex glows brightly enough to read as a ring. Its panel is
                # titled like a node's but carries no BATTLE, so commit through it.
                if not a.no_disk and G.tealish(G.box(probe, 900, 103)) \
                        and G.state(probe) != "combat_details" and take_disk():
                    took_disk = True
                    break
            if target or took_disk:
                break
            time.sleep(3)
        if took_disk:
            print(f"[{i}] took a stockpile", flush=True)
            continue
        if target is None:
            took = False
            if not a.no_disk:
                for hx, hy, _ in reversed(find_hexes(back_to_map())):
                    G.tap(*undev(hx, hy), wait=3)
                    if G.tealish(G.box(G.grab(), 900, 103)) and take_disk():
                        print(f"[{i}] took a stockpile at {undev(hx, hy)}", flush=True)
                        took = True
                        break
                    back_to_map()
            if took:
                continue
            print("no playable node found; stopping", file=sys.stderr)
            break

        t0 = time.time()
        out = play_at(target)
        played += out == "win"
        print(f"[{i}] {out} at {target} in {time.time() - t0:.0f}s", flush=True)
        if out.startswith("stuck"):
            break
        if out == "loss":
            print("lost; the squad needs rethinking", file=sys.stderr)
            break
    print(f"cleared={played}/{a.runs}")


if __name__ == "__main__":
    main()
