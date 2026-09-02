#!/usr/bin/env python3
"""Conquest node driver: play one node, N times, unattended.

Conquest is the one mode with no SIM, so every keycard and every feat tick is a real
battle that has to be clicked through. A sector is ~20 nodes and several feats need
10-20 wins with a named unit, so the run is measured in hundreds of battles. This
walks the fixed screen sequence for one node and reports what it saw.

    map -> [tap node] -> combat details -> BATTLE -> squad -> BATTLE -> fight
        -> AUTO -> ... -> REWARDS -> CONTINUE -> map

State is read off pixel probes rather than template matching: the screens differ by
whole coloured buttons in fixed places, which survives JPEG noise and needs no assets.

    python3 scripts/cq_grind.py --probe                 # dump the probe colours
    python3 scripts/cq_grind.py --node 566 285 --runs 3 # play a node 3 times
"""
import argparse
import os
import subprocess
import sys
import time

from PIL import Image

ADB = "/opt/homebrew/bin/adb"
SERIAL = os.environ.get("ANDROID_SERIAL", "127.0.0.1:5555")
SHOT = "/tmp/cq_state.png"

# The screenshots this repo reads are 1100px wide; the device is 1920x1080. Everything
# below is in 1100-space so it matches what is on screen in a Read, and is scaled once.
K = 1920 / 1100.0


def dev(x, y):
    return int(x * K), int(y * K)


def adb(*args, timeout=30):
    return subprocess.run([ADB, "-s", SERIAL, *args], capture_output=True,
                          text=True, timeout=timeout)


def tap(x, y, wait=2.0):
    dx, dy = dev(x, y)
    adb("shell", "input", "tap", str(dx), str(dy))
    time.sleep(wait)


def grab():
    for _ in range(3):
        p = subprocess.run([ADB, "-s", SERIAL, "exec-out", "screencap", "-p"],
                           capture_output=True, timeout=60)
        if p.returncode == 0 and len(p.stdout) > 10000:
            with open(SHOT, "wb") as fh:
                fh.write(p.stdout)
            return Image.open(SHOT).convert("RGB")
        time.sleep(2)
    raise RuntimeError("screencap failed three times; device probably dropped")


def px(im, x, y):
    return im.getpixel(dev(x, y))


def box(im, x, y, w=18, h=8):
    """Mean RGB of a small box, in 1100-space. One pixel is too noisy for thin UI text."""
    x0, y0 = dev(x - w / 2, y - h / 2)
    x1, y1 = dev(x + w / 2, y + h / 2)
    return im.crop((x0, y0, x1, y1)).resize((1, 1), Image.BOX).getpixel((0, 0))


def greenish(c, lo=90):
    r, g, b = c
    return g > lo and g > r + 30 and g > b + 30


def tealish(c):
    """The squad screen's CLEAR SQUAD button. Bright enough to rule out map background."""
    r, _, b = c
    return b > 60 and b > r + 25


# Probe points, in 1100-space.
P_COMBAT_BATTLE = (895, 573)   # green BATTLE on the Combat Details side panel
P_SQUAD_BATTLE = (953, 575)    # green BATTLE on the squad screen
P_SQUAD_CLEAR = (428, 575)     # teal CLEAR SQUAD, only on the squad screen
P_CONTINUE = (550, 535)        # the wide green CONTINUE on the REWARDS card
P_AUTO = (163, 32)             # AUTO toggle, green once running
P_STORE = (1014, 535)          # CONQUEST STORE button, only on the sector map
P_PANEL = (900, 103)           # "Combat Details" panel header, only with a node open
P_RETREAT = (118, 32)          # green retreat square, only while a battle is running

PROBES = {
    "combat_battle": P_COMBAT_BATTLE,
    "squad_battle": P_SQUAD_BATTLE,
    "squad_clear": P_SQUAD_CLEAR,
    "continue": P_CONTINUE,
    "continue_r": (780, 535),
    "auto": P_AUTO,
    "store": P_STORE,
    "panel": P_PANEL,
}


def state(im):
    """Screen identification, most specific first."""
    # A loss lands on the "you have upgrades available" card, whose green VIEW
    # COLLECTION sits higher than the REWARDS card's CONTINUE bar. Without this the
    # runner just waits out the full battle timeout on every defeat.
    if greenish(box(im, 550, 499)) and not greenish(box(im, 780, 535)):
        return "defeat"
    if greenish(box(im, *P_CONTINUE)) and greenish(box(im, 780, 535)):
        return "rewards"
    # Both screens carry a green BATTLE and the buttons overlap, so CLEAR SQUAD is the tell.
    if greenish(box(im, *P_SQUAD_BATTLE)) and tealish(box(im, *P_SQUAD_CLEAR)):
        return "squad"
    if greenish(box(im, *P_COMBAT_BATTLE)) and tealish(box(im, *P_PANEL)):
        return "combat_details"
    # The battle HUD's green retreat square is the only reliable in-battle tell: the
    # map's CONQUEST STORE button and the battle screen's ability tray sit at the same
    # spot and read almost the same colour, which had the runner call a live fight "map".
    if greenish(box(im, *P_RETREAT, w=14, h=14)):
        return "battle_auto" if greenish(box(im, *P_AUTO, w=14, h=14)) else "battle_manual"
    return "map"


def wait_for(want, timeout=300, poll=6):
    end = time.time() + timeout
    last = None
    while time.time() < end:
        im = grab()
        last = state(im)
        if last in want:
            return last, im
        time.sleep(poll)
    return last, None


def play(node):
    """One full pass over a single node. Returns a short outcome string."""
    im = grab()
    st = state(im)
    if st == "map":
        tap(*node, wait=3)
        im = grab()
        st = state(im)
    if st == "combat_details":
        tap(*P_COMBAT_BATTLE, wait=4)
        st, im = wait_for({"squad"}, timeout=40, poll=3)
    if st == "squad":
        tap(*P_SQUAD_BATTLE, wait=12)
        st, im = wait_for({"battle_manual", "battle_auto", "rewards"}, timeout=90, poll=5)
    if st == "battle_manual":
        tap(*P_AUTO, wait=3)
        st = "battle_auto"
    if st in ("battle_auto", "battle_manual"):
        st, im = wait_for({"rewards", "defeat"}, timeout=420, poll=8)
    if st == "defeat":
        tap(33, 33, wait=4)      # out of the upgrade-offer card
        tap(550, 300, wait=5)    # "tap anywhere to continue"
        return "loss"
    if st == "rewards":
        tap(*P_CONTINUE, wait=6)
        # A cleared node can pop an extra card (new disk, feat complete). Clear them.
        for _ in range(4):
            im = grab()
            if state(im) in ("map", "combat_details"):
                return "win"
            tap(*P_CONTINUE, wait=4)
        return "win"
    return f"stuck:{st}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--node", nargs=2, type=int, metavar=("X", "Y"),
                    help="node centre in 1100-space")
    ap.add_argument("--runs", type=int, default=1)
    ap.add_argument("--probe", action="store_true")
    a = ap.parse_args()

    if a.probe:
        im = grab()
        for name, pt in PROBES.items():
            print(f"{name:16} {pt} -> {box(im, *pt)}")
        print("state:", state(im))
        return

    if not a.node:
        ap.error("--node is required unless --probe")

    wins = 0
    for i in range(1, a.runs + 1):
        t0 = time.time()
        out = play(tuple(a.node))
        if out == "win":
            wins += 1
        print(f"[{i}/{a.runs}] {out} in {time.time() - t0:.0f}s", flush=True)
        if out.startswith("stuck"):
            print("halting: screen was not where the script expected", file=sys.stderr)
            break
        if out == "loss":
            print("halting: lost the battle, the squad needs rethinking", file=sys.stderr)
            break
    print(f"wins={wins}/{a.runs}")


if __name__ == "__main__":
    main()
