#!/usr/bin/env python3
"""Navigate the Territory War map to a NAMED territory, then ENTER it.

Why this exists: the map re-centres itself every time an info panel opens or
closes, so a coordinate that hit "Forward Turrets" one minute hits "Infirmary"
the next. Two placements went into the wrong territory that way. So never trust
a coordinate — tap it, OCR the panel title, and only ENTER on a name match.

    python3 scripts/tw_goto.py "Forward Turrets"
    python3 scripts/tw_goto.py --scan          # report every territory + label
"""
import os
import re
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tw_place as tp                                              # noqa: E402

ADB = ["/opt/homebrew/bin/adb", "-s", "127.0.0.1:5555"]
# Sweep positions over the whole map disc. Deliberately more than ten: the disc
# drifts, so redundant probes cost a second each and buy reliability.
CANDS = [# zoomed-OUT view (both discs on screen)
         (265, 274), (452, 305), (602, 305), (780, 314),
         (183, 415), (398, 419), (765, 576),
         (119, 655), (311, 655), (532, 649),
         # zoomed-IN view (our disc fills the frame)
         (843, 279), (1009, 258), (1173, 300), (1340, 271),
         (813, 419), (1009, 419), (1173, 440), (1340, 430),
         (813, 672), (1030, 681), (1236, 655), (1445, 594),
         # Jakku, 2026-08-29: these five were unreachable from the list above.
         # tw_scan_notes.py --dense found them on a plain grid sweep.
         (560, 620), (260, 360), (110, 750), (110, 490), (410, 490)]
EMPTY = (400, 500)          # dead console area — deselects without opening chat
ENTER = (1497, 985)
TITLE_BOX = (1050, 158, 1910, 216)
LABEL_BOX = (1060, 880, 1900, 940)


def tap(x, y, wait=2.0):
    subprocess.run(ADB + ["shell", "input", "tap", str(x), str(y)],
                   capture_output=True)
    time.sleep(wait)


def panel(box):
    return re.sub(r"\s+", " ", tp.ocr(box, thresh=150, psm="7")).strip()


def probe(xy):
    """Select the territory at xy. Returns (title, label) as read off the panel."""
    tap(*EMPTY, wait=1.6)
    tap(*xy, wait=3.4)
    tp.shot()
    return panel(TITLE_BOX), panel(LABEL_BOX)


# The map keeps whatever zoom and pan the last panel left it at, and there is no
# ADB gesture for pinch-to-zoom, so a fixed candidate list goes stale mid-session.
# This grid is the fallback sweep: slower, but it does not care where the disc is.
GRID = [(x, y) for y in range(230, 960, 130) for x in range(110, 1560, 150)]


def goto(name, enter=True):
    want = re.sub(r"[^a-z]", "", name.lower())
    for xy in CANDS + GRID:
        title, label = probe(xy)
        flat = re.sub(r"[^a-z]", "", title.lower())
        if want and want in flat:
            print(f"found {title!r}  label={label!r}  at {xy}")
            if enter:
                tap(*ENTER, wait=8.0)
                print("screen:", tp.screen_title(), "allied:", tp.allied_count())
            return True
    print(f"NOT FOUND: {name!r}")
    return False


def scan():
    seen = {}
    for xy in CANDS:
        title, label = probe(xy)
        if title and title not in seen:
            seen[title] = label
            print(f"{title:46s} | {label}")
    return seen


if __name__ == "__main__":
    if "--scan" in sys.argv:
        scan()
    else:
        sys.exit(0 if goto(sys.argv[1], "--no-enter" not in sys.argv) else 1)
