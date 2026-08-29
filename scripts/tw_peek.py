#!/usr/bin/env python3
"""Read the ALLIED SQUADS list of the current TW territory at legible size.

Identifying a guildmate's squad matters now that placement follows the guild's
per-territory notes: you have to see WHICH team they stacked. At native capture
scale a portrait is ~96px and the Read pipeline downsamples to 1100px wide, so
five portraits come back at ~55px and are guesswork. This crops the portrait
strip of each squad row and upscales it, four rows to a sheet.

    python3 scripts/tw_peek.py            # first sheet, no scrolling
    python3 scripts/tw_peek.py --page 2   # scroll two screenfuls first
"""
import os
import subprocess
import sys
import time

from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tw_place as tp                                              # noqa: E402

ADB = ["/opt/homebrew/bin/adb", "-s", "127.0.0.1:5555"]
OUT = os.path.expanduser("~/Downloads/tw_peek.png")
# Squad row geometry on PVP MISSION, device pixels. Row 1 header sits at y=274.
ROW0, PITCH, ROWS = 250, 292, 3
STRIP = (60, 0, 1010, 250)      # name bar + the five portraits, relative to row top
SCALE = 1.15


def main():
    page = 1
    if "--page" in sys.argv:
        page = int(sys.argv[sys.argv.index("--page") + 1])
    for _ in range(page - 1):
        subprocess.run(ADB + ["shell", "input", "swipe", "960", "800",
                              "960", "800 - 0"], capture_output=True)
    for _ in range((page - 1) * ROWS):
        subprocess.run(ADB + ["shell", "input", "swipe", "960", "800",
                              "960", "508", "700"], capture_output=True)
        time.sleep(0.7)
    time.sleep(1.2)

    tp.shot()
    im = Image.open(tp.SHOT)
    tiles = []
    for i in range(ROWS):
        top = ROW0 + i * PITCH
        box = (STRIP[0], top + STRIP[1], STRIP[2], top + STRIP[3])
        if box[3] > im.height:
            break
        t = im.crop(box)
        tiles.append(t.resize((int(t.width * SCALE), int(t.height * SCALE))))
    if not tiles:
        print("nothing to crop")
        return
    w = max(t.width for t in tiles)
    sheet = Image.new("RGB", (w, sum(t.height + 6 for t in tiles)), (0, 0, 0))
    y = 0
    for t in tiles:
        sheet.paste(t, (0, y)); y += t.height + 6
    sheet.save(OUT)
    print("wrote", OUT, sheet.size)


if __name__ == "__main__":
    main()
