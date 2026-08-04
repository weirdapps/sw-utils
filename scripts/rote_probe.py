#!/usr/bin/env python3
"""rote_probe.py — tap a RotE map marker, wait for the side panel to settle, save panel + map crops.

The mission markers are only selectable when the previous tap has fully landed: a 3s gap between
taps left the green selection cursor where it was and re-read the SAME panel six times, which
looked like "every mission has identical requirements" rather than "no tap registered". Verify the
cursor moved instead of trusting the delay: the panel is only meaningful if the selection changed.

usage: rote_probe.py NAME X Y [--wait SEC]
"""
import argparse
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from farmbot.adb import ADB                                         # noqa: E402

PANEL = (1060, 150, 1900, 700)     # the right-hand mission panel
MAP = (250, 250, 1010, 920)        # the planet, where the green selection cursor lives
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

    im = dev.screencap()
    im.save(f"{OUT}/{args.name}_full.png")
    im.crop(PANEL).save(f"{OUT}/{args.name}_panel.png")
    im.crop(MAP).resize((1140, 1005)).save(f"{OUT}/{args.name}_map.png")
    print(f"{OUT}/{args.name}_panel.png")


if __name__ == "__main__":
    sys.exit(main())
