#!/usr/bin/env python3
"""rote_open.py — select a RotE mission marker and open its squad screen.

Two taps that always go together: the map marker (which swaps the right-hand panel to that
mission) and the panel's BATTLE button. Kept separate from rote_autobattle.py because the squad
still wants a human/agent look before the fight starts — the game's auto-fill will spend a gated
unit on a mission that did not need it.

usage: rote_open.py NAME X Y [--wait SEC]
"""
import argparse
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from farmbot.adb import ADB                                         # noqa: E402

BATTLE_BTN = (1470, 1006)      # the panel's BATTLE button, same slot for every mission type
OUT = "/tmp/rote"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("name")
    ap.add_argument("x", type=int)
    ap.add_argument("y", type=int)
    ap.add_argument("--serial", default="127.0.0.1:5555")
    ap.add_argument("--wait", type=float, default=6.0)
    args = ap.parse_args()

    os.makedirs(OUT, exist_ok=True)
    dev = ADB(args.serial)
    dev.tap(args.x, args.y)
    time.sleep(args.wait)
    dev.tap(*BATTLE_BTN)
    time.sleep(args.wait + 2)

    dev.screencap().save(f"{OUT}/sq_{args.name}.png")
    print(f"{OUT}/sq_{args.name}.png")


if __name__ == "__main__":
    sys.exit(main())
