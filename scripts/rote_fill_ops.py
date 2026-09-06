#!/usr/bin/env python3
"""Fill a RotE Operation's open slots with every unit the account may legally place.

The operation popup is a 5x3 grid of slots. A slot the player can fill reads
UNDEPLOYED; a slot whose unit is owned but already spent elsewhere answers with a
"cannot be used here" dialog when tapped, and an unowned slot does nothing. Rather
than OCR the labels (the portraits are noisy and the label is 10px tall), this just
probes every cell: tap it, and read two pixels.

    ASSIGN bright cyan  -> a real selection was made, commit it
    green OK dialog     -> "cannot be used here", dismiss and move on
    neither             -> unowned slot, nothing happened

The per-account cap ("Assigned Units: n/10") is enforced by the game, so the loop
stops as soon as ASSIGN stops lighting up.

    python3 scripts/rote_fill_ops.py --op 5      # left column 1-3, right column 4-6
"""
import argparse
import subprocess
import time

from PIL import Image

ADB = "/opt/homebrew/bin/adb"
SERIAL = "127.0.0.1:5555"
K = 1920 / 1100.0

# Everything below is in the 1100-wide space the rest of the repo uses.
OP_BUTTON = {1: (89, 230), 2: (89, 366), 3: (89, 502),
             4: (1010, 230), 5: (1010, 366), 6: (1010, 502)}
COLS = (360, 455, 550, 645, 740)
ROWS = (230, 350, 462)
ASSIGN = (680, 566)
CLOSE = (427, 566)
OK_DLG = (550, 385)
COUNTER = (830, 20, 1010, 55)


def tap(x, y, wait=1.5):
    subprocess.run([ADB, "-s", SERIAL, "shell", "input", "tap",
                    str(int(x * K)), str(int(y * K))], capture_output=True)
    time.sleep(wait)


def grab():
    p = subprocess.run([ADB, "-s", SERIAL, "exec-out", "screencap", "-p"],
                       capture_output=True, timeout=60)
    with open("/tmp/rfo.png", "wb") as fh:
        fh.write(p.stdout)
    return Image.open("/tmp/rfo.png").convert("RGB")


def box(im, x, y, w=40, h=14):
    x0, y0 = int((x - w / 2) * K), int((y - h / 2) * K)
    x1, y1 = int((x + w / 2) * K), int((y + h / 2) * K)
    return im.crop((x0, y0, x1, y1)).resize((1, 1), Image.BOX).getpixel((0, 0))


def assign_lit(c):
    r, g, b = c
    return g > 165 and b > 175 and b > r


def ok_dialog(c):
    r, g, b = c
    return g > r + 50 and g > b + 50


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--op", type=int, required=True, choices=sorted(OP_BUTTON))
    a = ap.parse_args()

    tap(*OP_BUTTON[a.op], wait=3)
    placed = 0
    for row in ROWS:
        for col in COLS:
            tap(col, row, wait=1.2)
            im = grab()
            if ok_dialog(box(im, *OK_DLG)):
                tap(*OK_DLG, wait=1.2)
                continue
            if assign_lit(box(im, *ASSIGN)):
                tap(*ASSIGN, wait=2.5)
                placed += 1
    im = grab()
    print(f"op {a.op}: placed {placed}")
    tap(*CLOSE, wait=2)


if __name__ == "__main__":
    main()
