#!/usr/bin/env python3
"""rote_peek.py — tap a RotE map point and save ONLY the crops worth looking at.

Screenshots are the session's real budget and the limit is BYTES, not tokens (see CLAUDE.md).
A full 1920x1080 screencap is ~2.7MB; the planet header is ~15KB. When all you need is "which
planet did I just open, and what does its side panel say", crop before you look.

usage: rote_peek.py X Y [--wait SEC] [--name TAG] [--full]
  --full   also save the whole frame (only when a crop genuinely is not enough)
"""
import argparse
import os
import subprocess
import time

from PIL import Image

OUT = "/tmp/rote"
HEADER = (0, 0, 1150, 190)        # planet name, phase, timer
PANEL = (1060, 130, 1920, 1080)   # the right-hand mission/territory panel
ADB = "/opt/homebrew/bin/adb"


def cap(serial):
    raw = subprocess.run([ADB, "-s", serial, "exec-out", "screencap", "-p"],
                         capture_output=True, check=True).stdout
    tmp = f"{OUT}/_raw.png"
    with open(tmp, "wb") as f:
        f.write(raw)
    return Image.open(tmp)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("x", type=int)
    ap.add_argument("y", type=int)
    ap.add_argument("--serial", default="127.0.0.1:5555")
    ap.add_argument("--wait", type=float, default=6.0)
    ap.add_argument("--name", default="peek")
    ap.add_argument("--full", action="store_true")
    ap.add_argument("--notap", action="store_true")
    args = ap.parse_args()

    os.makedirs(OUT, exist_ok=True)
    if not args.notap:
        subprocess.run([ADB, "-s", args.serial, "shell", "input", "tap",
                        str(args.x), str(args.y)], check=True)
        time.sleep(args.wait)

    im = cap(args.serial)
    for tag, box in (("head", HEADER), ("panel", PANEL)):
        p = f"{OUT}/{args.name}_{tag}.png"
        im.crop(box).save(p)
        print(f"{p}  {os.path.getsize(p)//1024}KB")
    if args.full:
        p = f"{OUT}/{args.name}_full.png"
        im.save(p)
        print(f"{p}  {os.path.getsize(p)//1024}KB")


if __name__ == "__main__":
    main()
