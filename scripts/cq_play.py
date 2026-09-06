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
import subprocess
import sys
import time

from PIL import Image

import autofight
import cq_grind as G

PANEL_BATTLE = (900, 573)
BONUS_BATTLE = (995, 573)      # a repeatable bonus node grows a MULTI SIM button,
SQUAD_BATTLE = (925, 577)      # which pushes its BATTLE to the right


DISK_1 = (898, 203)            # first offer in a Data Disk Stockpile panel
SHOP_COMMIT = (900, 569)       # the Wandering Scavenger's own COMMIT
MOVE_COMMIT = (679, 398)       # COMMIT on the "you will advance" modal


def green(pt):
    return G.greenish(G.box(G.grab(), *pt))


def panel_title():
    """OCR the right-hand panel's header. The two blockers look nothing alike in
    behaviour and identical in pixels, so branch on the words."""
    im = Image.open(G.SHOT).crop((int(680 * G.K), int(80 * G.K),
                                  int(1080 * G.K), int(120 * G.K)))
    im = im.resize((im.width * 2, im.height * 2), Image.LANCZOS)
    im.save("/tmp/cqtitle.png")
    out = subprocess.run(["/opt/homebrew/bin/tesseract", "/tmp/cqtitle.png", "stdout",
                          "--psm", "7"], capture_output=True, timeout=30)
    return out.stdout.decode("utf-8", "replace").strip()


def find_move_commit():
    """Centre of the green COMMIT on the "you will advance" modal, or None.

    Its Y MOVES: a bare "MOVE TO SCAVENGER" puts it around y=398, and the same modal
    with a data-disk card in it around y=532. A fixed coordinate misses one of them
    and the runner then stalls on the blocker it was written to clear.
    """
    im = G.grab()
    rows = {}
    for y in range(370, 580, 4):
        xs = [x for x in range(450, 950, 10) if G.greenish(G.px(im, x, y))]
        if len(xs) >= 8:
            rows[y] = xs
    if not rows:
        return None
    y = sorted(rows)[len(rows) // 2]
    return (sum(rows[y]) // len(rows[y]), y)


def pass_blocker():
    """Walk the token through a stockpile or a scavenger, taking nothing that costs.

    ⛔ Conquest Credits and crystals are both off limits (owner, 2026-09-03), so the
    scavenger is passed by pressing its own COMMIT with NOTHING selected. A stockpile
    is free, so take its first offer rather than skip a disk for no reason.
    ⚠ Never tap a card on the scavenger panel: selecting an item and then committing
    is a purchase.
    """
    for _ in range(4):
        G.grab()
        title = panel_title().lower()
        if "scavenger" in title:
            G.tap(*SHOP_COMMIT, wait=3)
        elif "disk" in title or "stockpile" in title:
            G.tap(*DISK_1, wait=3)
        hit = find_move_commit()
        if hit:
            G.tap(*hit, wait=5)
            G.tap(150, 480, wait=3)     # dismiss whatever panel the move opened
            return True
        time.sleep(2)
    return False


def main():
    if len(sys.argv) != 3:
        sys.exit("usage: cq_play.py X Y   (1100-space)")
    G.tap(int(sys.argv[1]), int(sys.argv[2]), wait=4)

    im = G.grab()
    if not (G.greenish(G.box(im, *PANEL_BATTLE))
            or G.greenish(G.box(im, *BONUS_BATTLE))):
        # Not a fight. A Data Disk Stockpile or a Wandering Scavenger can be the ONLY
        # way forward, and each throws a "you will advance and be unable to select a
        # different path" modal that no vision runner recognises, so the grind stalls
        # replaying the last node forever. Walk through it.
        if pass_blocker():
            print("moved")
            return 0
        print("no battle here")
        return 1
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
