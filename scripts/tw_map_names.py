#!/usr/bin/env python3
"""Name every shield on the zoomed-OUT Territory War map, position by position.

Selecting a territory pans and zooms the map, so the zoomed-out coordinates are
only valid for the FIRST tap after the map is drawn. This resets the view
between every probe (back to the TW summary, then ENTER) and therefore costs
about 25s per territory, which is the price of a reading that is actually
trustworthy: two placements in an earlier war went into the wrong territory
because a coordinate was reused after the map had moved.

    python3 scripts/tw_map_names.py           -> output/tw_map_names.json
"""
import json
import os
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tw_place as tp                                              # noqa: E402
import tw_goto as tg                                               # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(REPO, "output", "tw_map_names.json")
BACK = (68, 65)
ENTER_SUMMARY = (1656, 984)

# Shield centres read off a zoomed-out capture, in device pixels, with the
# lane/column each one sits in. x rises toward the enemy disc, so higher x is
# closer to the front.
SHIELDS = [
    ("top",    255, 265),
    ("top",    452, 265),
    ("top",    595, 305),
    ("top",    789, 326),
    ("mid",    120, 419),
    ("mid",    391, 419),
    ("mid",    763, 602),
    ("bottom", 120, 655),
    ("bottom", 316, 690),
    ("bottom", 532, 655),
]


def reset_map():
    subprocess.run(tg.ADB + ["shell", "input", "tap", *map(str, tg.EMPTY)],
                   capture_output=True)
    time.sleep(1.5)
    subprocess.run(tg.ADB + ["shell", "input", "tap", *map(str, BACK)],
                   capture_output=True)
    time.sleep(6)
    subprocess.run(tg.ADB + ["shell", "input", "tap",
                             *map(str, ENTER_SUMMARY)], capture_output=True)
    time.sleep(11)


def main():
    found = []
    for lane, x, y in SHIELDS:
        reset_map()
        tg.tap(x, y, wait=3.4)
        tp.shot()
        title = tg.panel(tg.TITLE_BOX)
        note = tg.panel(tg.LABEL_BOX)
        found.append({"lane": lane, "x": x, "y": y,
                      "title": title, "note_ocr": note})
        print(f"{lane:6s} ({x:4d},{y:4d})  {title!r}", flush=True)
    with open(OUT, "w") as fh:
        json.dump(found, fh, indent=2)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
