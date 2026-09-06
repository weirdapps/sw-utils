#!/usr/bin/env python3
"""Play one Conquest node from the sector map, on auto at 4x, and report the outcome.

`cq_grind.play()` has the better screen IDENTIFICATION but its `wait_for({"squad"})`
kept timing out on sector 4 and halting runs that a hand-driven BATTLE press finished
every time. This keeps `cq_grind.state()` and drops the waiting: tap the node, tap the
two BATTLE buttons, hand off to autofight, then dismiss whatever card the fight ended
on by asking `state()` what is on screen rather than blind-tapping (a blind tap walked
one run into the Conquest inventory and then the EA Help chat).

    python3 scripts/cq_play.py 107 227      # prints win | defeat | <state>
"""
import sys
import time

import autofight
import cq_grind as G

PANEL_BATTLE = (900, 573)
BONUS_BATTLE = (995, 573)      # a repeatable bonus node grows a MULTI SIM button,
SQUAD_BATTLE = (925, 577)      # which pushes its BATTLE to the right


def main():
    if len(sys.argv) != 3:
        sys.exit("usage: cq_play.py X Y   (1100-space)")
    G.tap(int(sys.argv[1]), int(sys.argv[2]), wait=4)

    im = G.grab()
    G.tap(*(BONUS_BATTLE if G.greenish(G.box(im, *BONUS_BATTLE)) else PANEL_BATTLE),
          wait=6)
    G.tap(*SQUAD_BATTLE, wait=8)
    if G.state(G.grab()) not in ("battle_manual", "battle_auto"):
        G.tap(550, 396, wait=4)               # OK on the "squad is not full" modal
        G.tap(*SQUAD_BATTLE, wait=8)

    autofight.run(700)                        # bosses get a 10-minute timer, not 5

    # ⚠ The VICTORY splash is a full-screen render with no HUD, so `state()` calls it
    # "map" for several seconds BEFORE the REWARDS card animates in. Declaring on the
    # first "map" reports win-noreward on a node that was about to pay, so require the
    # map twice running.
    outcome, maps = "unknown", 0
    for _ in range(14):
        time.sleep(4)
        st = G.state(G.grab())
        if st == "rewards":
            outcome, maps = "win", 0
            G.tap(*G.P_CONTINUE, wait=3)
        elif st == "defeat":
            outcome, maps = "defeat", 0
            G.tap(550, 300, wait=3)
        elif st == "map":
            maps += 1
            if maps >= 2:
                # A node already at 3/3 pays nothing: VICTORY -> map, no card at all.
                print(outcome if outcome != "unknown" else "win-noreward")
                return 0
        else:
            break
    print(outcome)
    return 0


if __name__ == "__main__":
    sys.exit(main())
