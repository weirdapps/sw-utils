#!/usr/bin/env python3
"""Replay ONE Conquest node N times to farm sector feats, with the squad already built.

    python3 scripts/cq_farm.py --pan 1 --node 630 435 --runs 6

Why a separate runner from `cq_play.py`: that one ADVANCES the token, which is what you
want while a sector is unexplored. Once a sector is walked out, its remaining keycards
are all FEATS, and a feat progresses on any battle in that sector, win or lose, on a
node that is already 3/3 and pays nothing. Confirmed live 2026-09-06: two LOSSES on the
Sector-3 boss closed `Stunning Tactics` and `Maximum Output` for 20 keycards, because
both are "attempt"/"gain" feats that do not care about the result.

⚠ The map does not recentre after a battle, so the node coordinate is only stable if the
pan is. Each run re-pans from the right-hand edge by a fixed number of notches before it
taps, which makes the coordinate reproducible instead of hopeful.
⚠ The squad PERSISTS between Conquest battles and is only committed by pressing BATTLE.
This never touches the squad screen except to press it (memory/notes.md 2026-09-03).
"""
import argparse
import subprocess
import sys
import time

import autofight
import cq_grind as G

PANEL_BATTLE = (900, 573)
BONUS_BATTLE = (995, 573)
SQUAD_BATTLE = (925, 577)


def jswipe(x1, y1, x2, y2, ms=500, wait=2):
    subprocess.run(["/opt/homebrew/bin/adb", "-s", "127.0.0.1:5555", "shell",
                    "input", "swipe", str(int(x1 * G.K)), str(int(y1 * G.K)),
                    str(int(x2 * G.K)), str(int(y2 * G.K)), str(ms)],
                   capture_output=True)
    time.sleep(wait)


def recentre(pan, anchor="right"):
    """Slam the map to one stop, then pan `pan` notches back toward the other.

    Swiping to a stop first is what makes this idempotent: a relative pan from an
    unknown position is a different position every time.

    Anchor from the LEFT when the target is early in the sector. Enemy stat bonuses
    rise "further down the Sector", so the softest node is the first one, and counting
    notches to it from the right-hand stop is both longer and less stable.
    """
    # Ten, not four. Four is enough coming back from a battle, where the map has not
    # moved, and NOT enough coming back from the feats panel or the inventory, which
    # reopen the map centred. An over-swipe at the stop is free.
    if anchor == "left":
        for _ in range(10):
            jswipe(200, 300, 850, 300, 400, 1)
        for _ in range(pan):
            jswipe(800, 300, 300, 300, 500, 2)
    else:
        for _ in range(10):
            jswipe(850, 300, 200, 300, 400, 1)
        for _ in range(pan):
            jswipe(300, 300, 800, 300, 500, 2)


def dismiss():
    """Clear whatever card the fight ended on, by state, never by blind tapping.

    A blind tap at the CONTINUE coordinate is the guild-chat bar one screen later, and
    a stray pair once walked a run into the EA Help chat.
    """
    outcome = "unknown"
    for _ in range(16):
        st = G.state(G.grab())
        if st == "rewards":
            outcome = "win" if outcome == "unknown" else outcome
            G.tap(*G.P_CONTINUE, wait=3)
        elif st == "defeat":
            # ⛔ Do NOT press the middle of this card. (550,499) is VIEW COLLECTION and
            # it drops you into the roster INVENTORY, whose own back button then exits
            # Conquest to the cantina. The back arrow is the only safe exit: it returns
            # to the "DEFEAT! tap anywhere" splash, which any centre press clears.
            outcome = "defeat"
            G.tap(37, 25, wait=3)
            G.tap(550, 400, wait=3)
        elif st == "map":
            return outcome if outcome != "unknown" else "win-noreward"
        else:
            # FEAT REWARDS and the tap-anywhere DEFEAT splash are neither; both clear
            # on a press in the middle of the card.
            G.tap(550, 536, wait=3)
        time.sleep(2)
    return outcome


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pan", type=int, default=1, help="notches back from the anchored stop")
    ap.add_argument("--anchor", choices=("left", "right"), default="right")
    ap.add_argument("--node", type=int, nargs=2, required=True, metavar=("X", "Y"))
    ap.add_argument("--runs", type=int, default=5)
    ap.add_argument("--timeout", type=int, default=420)
    a = ap.parse_args()

    for i in range(1, a.runs + 1):
        # Retry the approach before giving up: a card that was still animating when the
        # previous run returned eats the first recentre, and the node tap then lands on
        # empty map. One clean retry costs four seconds and saves the whole batch.
        # ⛔ There was a `clear_connection_error()` call here and the function was never
        # written, so this file had never run past its first iteration (NameError). It is
        # gone rather than guessed: the modal has never been captured on device, and a
        # blind press at an invented coordinate is what once walked a run into the EA Help
        # chat. Capture the dialog first, then handle it.
        for attempt in range(1, 7):
            recentre(a.pan, a.anchor)
            G.tap(*a.node, wait=4)
            im = G.grab()
            bonus = G.greenish(G.box(im, *BONUS_BATTLE))
            if bonus or G.greenish(G.box(im, *PANEL_BATTLE)):
                break
            print(f"[{i}/{a.runs}] no BATTLE at {a.node} (try {attempt})", flush=True)
            time.sleep(6)
        else:
            print(f"[{i}/{a.runs}] node unreachable; stopping")
            return 1
        G.tap(*(BONUS_BATTLE if bonus else PANEL_BATTLE), wait=6)
        G.tap(*SQUAD_BATTLE, wait=8)
        autofight.run(a.timeout)
        print(f"[{i}/{a.runs}] {dismiss()}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
