#!/usr/bin/env python3
"""Play one RotE combat mission end to end, unattended.

    territory map -> [tap marker] -> BATTLE -> squad screen -> BATTLE
        -> force AUTO on -> wait for VICTORY -> tap through -> galaxy map

The squad is whatever the game auto-fills. That is deliberate for the mixed
missions, which have no gated unit and no researched comp: everything on the
account clears a phase-4 wave at 220k. Do NOT use this for a mission with a
`required` unit in data/rote/missions_*.json -- auto-fill will spend a gated unit
on the wrong row, which is the failure recorded in memory/notes.md 2026-08-19.

    python3 scripts/rote_play.py --planet 628 240 --marker 461 246
"""
import argparse
import subprocess
import time

from PIL import Image

ADB = "/opt/homebrew/bin/adb"
SERIAL = "127.0.0.1:5555"
K = 1920 / 1100.0

PANEL_BATTLE = (843, 575)     # the mission panel's BATTLE button
SQUAD_BATTLE = (955, 575)     # the squad screen's BATTLE button
AUTO = (158, 36)              # HUD, 1100-space. Blue = off, yellow-green = on.
SPEED = (226, 36)
BACK = (38, 37)
TAP_THROUGH = (550, 500)


def tap(x, y, wait=2.0):
    subprocess.run([ADB, "-s", SERIAL, "shell", "input", "tap",
                    str(int(x * K)), str(int(y * K))], capture_output=True)
    time.sleep(wait)


def grab():
    p = subprocess.run([ADB, "-s", SERIAL, "exec-out", "screencap", "-p"],
                       capture_output=True, timeout=60)
    with open("/tmp/rplay.png", "wb") as fh:
        fh.write(p.stdout)
    return Image.open("/tmp/rplay.png").convert("RGB")


def box(im, x, y, w=16, h=10):
    x0, y0 = int((x - w / 2) * K), int((y - h / 2) * K)
    x1, y1 = int((x + w / 2) * K), int((y + h / 2) * K)
    return im.crop((x0, y0, x1, y1)).resize((1, 1), Image.BOX).getpixel((0, 0))


def auto_on(im):
    """AUTO reads yellow-green when armed, which fails a plain 'is it green' test
    (r=176 vs g=199). Compare red against blue instead."""
    c = box(im, *AUTO)
    return c[0] > c[2]


def in_battle(im):
    """The HUD row only exists during a fight; off it, those pixels are dark."""
    c = box(im, *AUTO)
    return sum(c) > 180


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--planet", nargs=2, type=int, required=True)
    ap.add_argument("--marker", nargs=2, type=int, required=True)
    ap.add_argument("--timeout", type=int, default=420)
    a = ap.parse_args()

    tap(*a.planet, wait=5)
    tap(*a.marker, wait=4)
    tap(*PANEL_BATTLE, wait=6)

    # The squad screen can take well over the panel's own animation to appear, and
    # a BATTLE tap that lands early hits the mission panel behind it -- which is
    # how a run ends parked on SELECT EVENT SQUAD having fought nothing. Wait for
    # the screen's own green BATTLE button before pressing it.
    for _ in range(10):
        c = box(grab(), *SQUAD_BATTLE)
        if c[1] > 120 and c[1] > c[0] + 30 and c[1] > c[2] + 30:
            break
        time.sleep(3)
    else:
        raise SystemExit("squad screen never appeared")
    tap(*SQUAD_BATTLE, wait=12)

    for _ in range(3):
        im = grab()
        if not in_battle(im):
            time.sleep(4)
            continue
        if auto_on(im):
            break
        tap(*AUTO, wait=2)
    tap(*SPEED, wait=1)
    tap(*SPEED, wait=1)

    deadline = time.time() + a.timeout
    while time.time() < deadline:
        time.sleep(15)
        if not in_battle(grab()):
            break
    time.sleep(6)
    for _ in range(3):
        tap(*TAP_THROUGH, wait=3)
    print("done")


if __name__ == "__main__":
    main()
