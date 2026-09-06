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
# A repeatable bonus node adds a MULTI SIM button, which pushes BATTLE to the right.
P_BONUS_BATTLE = (995, 573)
P_SQUAD_BATTLE = (953, 575)    # green BATTLE on the squad screen
P_SQUAD_CLEAR = (428, 575)     # teal CLEAR SQUAD, only on the squad screen
P_CONTINUE = (550, 535)        # the wide green CONTINUE on the REWARDS card
P_AUTO = (158, 37)             # AUTO toggle: blue when off, green when on
P_STORE = (1014, 535)          # CONQUEST STORE button, only on the sector map
P_PANEL = (900, 103)           # "Combat Details" panel header, only with a node open
P_RETREAT = (100, 36)          # retreat square; its colour depends on the battle
                               # BACKGROUND, so it is no longer used to detect a fight

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
    # VIEW COLLECTION (green) sits directly above HELP (teal) on the defeat card, and
    # nothing else in Conquest stacks those two. Testing the green button alone
    # matched half-drawn REWARDS cards and cost real battles to sort out.
    if greenish(box(im, 550, 499)) and tealish(box(im, 550, 561)) \
            and not greenish(box(im, 780, 535)):
        return "defeat"
    if greenish(box(im, *P_CONTINUE)) and greenish(box(im, 780, 535)):
        return "rewards"
    # Both screens carry a green BATTLE and the buttons overlap, so CLEAR SQUAD is the tell.
    if greenish(box(im, *P_SQUAD_BATTLE)) and tealish(box(im, *P_SQUAD_CLEAR)):
        return "squad"
    if tealish(box(im, *P_PANEL)) and (greenish(box(im, *P_COMBAT_BATTLE))
                                       or greenish(box(im, *P_BONUS_BATTLE))):
        return "combat_details"
    # In-battle tell: the AUTO button. It is a big LIT circle (white arrow on blue when
    # off, white arrow on green when on) and nothing else in Conquest puts anything
    # bright at that spot -- the sector map has the "Ends: 9d 16h" subtitle there, which
    # measures ~(34,45,51).
    #
    # The previous tell was "the retreat square is green", and it was wrong: that box
    # straddles the edge of the retreat circle, so what it actually measured was the
    # BATTLE BACKGROUND showing through. On a sand-coloured Tatooine floor it read
    # green and the runner worked; on a dark interior it read blue, the runner never
    # saw a battle at all, never switched AUTO on, and the squad stood still until it
    # died. That cost four straight "losses" with squads that should not lose.
    c = box(im, *P_AUTO, w=16, h=16)
    if max(c) > 110:
        return "battle_auto" if c[1] > c[2] else "battle_manual"
    # The full-screen "DEFEAT! / Tap anywhere to continue" splash has no HUD at all, so
    # everything above passes it through as "map" -- and a loss then reads as the
    # no-reward win that a replayed 3/3 node produces. The red banner is the tell.
    d = box(im, 550, 300, w=200, h=30)
    if d[0] > 90 and d[0] > d[1] + 45 and d[0] > d[2] + 45:
        return "defeat"
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
        tap(*(P_BONUS_BATTLE if greenish(box(im, *P_BONUS_BATTLE)) else P_COMBAT_BATTLE),
            wait=4)
        st, im = wait_for({"squad"}, timeout=40, poll=3)
    if st == "squad":
        tap(*P_SQUAD_BATTLE, wait=6)
        # A squad of fewer than five raises "you are attempting to enter battle with a
        # squad that is not full", which is a modal and eats the BATTLE press. Solo runs
        # (the Sector-2 boss feat wants The Stranger alone) hit it every time.
        # Two different modals can eat the BATTLE press, and BOTH dim the squad screen
        # enough that `state` no longer calls it "squad": "squad is not full" (any solo
        # or short lineup) and "large unit ... prevents summoning" (Jabba plus Aphra).
        # So the test is "we are not in a battle yet", not "we are still on the squad
        # screen", and the OK button is in the same place for both.
        if state(grab()) not in ("battle_manual", "battle_auto"):
            tap(550, 396, wait=4)        # OK
        st, im = wait_for({"battle_manual", "battle_auto", "rewards"}, timeout=90, poll=5)
    if st == "battle_manual":
        # A battle left on manual never acts, and the clock still runs, so the whole
        # node reads as a timeout loss. Confirm the toggle actually took.
        for _ in range(3):
            tap(*P_AUTO, wait=3)
            st = state(grab())
            if st != "battle_manual":
                break
    if st in ("battle_auto", "battle_manual"):
        # 4x on every fight (owner, 2026-09-06). Sticky between battles, so this is
        # normally one screenshot and no taps, and it roughly halves a long grind.
        try:
            import autofight
            autofight.set_speed_4x()
        except Exception:
            pass
        # A node that is already 3/3 pays nothing, so its win shows the VICTORY splash
        # and drops straight back to the map with no REWARDS card at all. The splash
        # itself also reads as "map" (it is a full-screen render with no HUD), so treat
        # a map that is still a map five seconds later as the end of the fight.
        # Wait for the end of the fight. "map" is NOT a reliable end marker on its own:
        # a full-screen ability animation hides the AUTO button for a frame or two and
        # reads exactly like the map, so require it three polls running. It has to be
        # accepted eventually, because a node that is already 3/3 pays nothing and its
        # win goes VICTORY -> map with no REWARDS card at all.
        end = time.time() + 420
        maps = 0
        st = "battle_auto"
        while time.time() < end:
            st = state(grab())
            if st in ("rewards", "defeat"):
                break
            maps = maps + 1 if st in ("map", "combat_details") else 0
            if maps >= 3:
                return "win-noreward"
            time.sleep(6)
    if st == "defeat":
        # The REWARDS card animates in, and for a frame or two its CONTINUE bar is
        # only half drawn, which reads exactly like the defeat card. Re-sample before
        # believing it: a real defeat costs a five-minute retry to discover.
        time.sleep(5)
        im = grab()
        st = state(im)
    if st == "defeat":
        # One back tap leaves the upgrade-offer card and lands on the sector map. A
        # second tap leaves the SECTOR, which is how a losing run kept ending up on the
        # chooser with the next node three navigations away.
        # Two different screens can be showing: the "DEFEAT! tap anywhere" splash, which
        # wants a tap in the middle, and the "you have upgrades available" card, which
        # wants the back arrow. Alternate, and stop the moment the map is back -- a
        # second back tap from the map leaves the SECTOR.
        for i in range(4):
            tap(550, 300, wait=3) if i % 2 == 0 else tap(33, 33, wait=4)
            if state(grab()) in ("map", "combat_details"):
                break
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
