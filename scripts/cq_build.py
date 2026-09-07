#!/usr/bin/env python3
"""Build a Conquest squad by name, from the SELECT SQUAD screen.

Nine of the ten boss/mini-boss feats in Conquest 24 are composition-locked ("win with
Maul (Hate-Fueled) in your squad", "a full squad of Bad Batch", "no Attacker units"), so
every one of them needs a hand-built squad. Scrolling a 398-unit roster two portraits at
a time to find one character is what makes that expensive; the filter panel's TEXT SEARCH
makes it four taps, and this wraps those four taps.

    python3 scripts/cq_build.py --clear stranger "maul (hate" starkiller barriss visas

Each term is typed into SELECT FILTER's text box, and the FIRST portrait of the filtered
grid is added to the next empty slot. So the term must be specific enough that the wanted
unit sorts first: "barriss" returns Barriss Offee and Inquisitor Barriss, "maul" returns
three. Grid order is by power descending, which is why `--pick N` exists.

⚠ The squad PERSISTS between Conquest battles and is only committed by pressing BATTLE.
Backing out of this screen discards it (memory/notes.md 2026-09-03).
"""
import argparse
import subprocess
import sys
import time

import cq_grind as G

ADB = "/opt/homebrew/bin/adb"
SERIAL = "127.0.0.1:5555"

FILTER_DROP = (145, 235)      # the "ALL" / "TEXT SEARCH" dropdown
FILTER_TEXT = (360, 549)      # "Enter Text Here"
CLEAR_SQUAD = (428, 575)
# The filtered roster grid: two columns, rows every ~125px in 1100-space.
GRID = [(65, 330), (215, 330), (65, 455), (215, 455), (65, 580), (215, 580)]


def sh(*args):
    subprocess.run([ADB, "-s", SERIAL, "shell", *args], capture_output=True)


def search(term):
    """Open SELECT FILTER, replace whatever is in the box with `term`, apply."""
    G.tap(*FILTER_DROP, wait=2.5)
    G.tap(*FILTER_TEXT, wait=1.5)
    # The box keeps the previous term. Ctrl-A then DEL is one round trip; 40 backspaces
    # is not, and a leftover prefix silently filters to an empty grid.
    sh("input", "keyevent", "--longpress", "KEYCODE_A")
    sh("input", "keyevent", "123")          # MOVE_END
    for _ in range(24):
        sh("input", "keyevent", "67")       # DEL
    sh("input", "text", term.replace(" ", "%s"))
    time.sleep(0.6)
    sh("input", "keyevent", "66")           # ENTER, closes the soft keyboard
    time.sleep(1.5)
    G.tap(855, 548, wait=3)                 # CONFIRM


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("terms", nargs="+")
    ap.add_argument("--clear", action="store_true")
    ap.add_argument("--pick", type=int, nargs="*", default=None,
                    help="1-based grid position per term (default 1 for all)")
    a = ap.parse_args()

    picks = a.pick or [1] * len(a.terms)
    if len(picks) != len(a.terms):
        print("--pick must give one index per term")
        return 1

    if a.clear:
        G.tap(*CLEAR_SQUAD, wait=3)

    for term, k in zip(a.terms, picks):
        search(term)
        G.tap(*GRID[k - 1], wait=3)
        print(f"added {term!r} (grid {k})", flush=True)

    print(G.state(G.grab()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
