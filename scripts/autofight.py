#!/usr/bin/env python3
"""Arm AUTO + max speed on a live battle and block until it ends.

Every mode in this game drops you into the same HUD once a fight starts, so the
one thing worth factoring out is "make it play itself, then tell me when it is
over". Used by the arena, Coliseum and RotE flows.

    python3 scripts/autofight.py             # wait up to 7 minutes
    python3 scripts/autofight.py --timeout 900

⚠ AUTO reads BLUE when off and YELLOW-GREEN when on, and yellow-green fails a
plain "is it green" test (r=176 vs g=199), so the probe compares red against
blue. A battle left on manual burns the full timer and lands on DEFEAT.
"""
import argparse
import subprocess
import time

from PIL import Image

ADB = "/opt/homebrew/bin/adb"
SERIAL = "127.0.0.1:5555"
K = 1920 / 1100.0
AUTO = (158, 36)
SPEED = (226, 36)


def tap(x, y, wait=1.5):
    subprocess.run([ADB, "-s", SERIAL, "shell", "input", "tap",
                    str(int(x * K)), str(int(y * K))], capture_output=True)
    time.sleep(wait)


def grab():
    p = subprocess.run([ADB, "-s", SERIAL, "exec-out", "screencap", "-p"],
                       capture_output=True, timeout=60)
    with open("/tmp/autofight.png", "wb") as fh:
        fh.write(p.stdout)
    return Image.open("/tmp/autofight.png").convert("RGB")


def hud(im):
    x, y = AUTO
    x0, y0 = int((x - 8) * K), int((y - 5) * K)
    return im.crop((x0, y0, int((x + 8) * K), int((y + 5) * K))).resize(
        (1, 1), Image.BOX).getpixel((0, 0))


def speed_label():
    """OCR the multiplier printed beside the SPEED button, e.g. 'x4'."""
    im = Image.open("/tmp/autofight.png")
    box = im.crop((int(238 * K), int(20 * K), int(275 * K), int(52 * K)))
    box = box.resize((box.width * 4, box.height * 4), Image.LANCZOS)
    box.save("/tmp/afspeed.png")
    # tesseract writes non-UTF8 bytes to stderr on some builds, which makes text=True
    # raise UnicodeDecodeError before the caller ever sees stdout. Decode by hand.
    out = subprocess.run(["/opt/homebrew/bin/tesseract", "/tmp/afspeed.png", "stdout",
                          "--psm", "7", "-c", "tessedit_char_whitelist=x1234"],
                         capture_output=True, timeout=30)
    return out.stdout.decode("utf-8", "replace").strip()


def set_speed_4x():
    """Cycle the speed button up to 4x. The owner asks for 4x on every fight, and it is
    sticky between battles, so this normally costs one screenshot and no taps."""
    for _ in range(5):
        grab()
        if "4" in speed_label():
            return True
        tap(*SPEED, wait=1.2)
    return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--timeout", type=int, default=420)
    a = ap.parse_args()
    run(a.timeout)


def run(timeout=420):
    # Wait for the HUD, THEN arm. Giving up early is the expensive bug: the fight runs
    # on manual, nobody acts, the 5-minute clock expires and it lands on DEFEAT looking
    # exactly like "the squad was too weak". Two Conquest nodes were lost that way on
    # 2026-09-06 before the cause was found.
    for _ in range(14):
        c = hud(grab())
        if sum(c) <= 180:          # cinematic, or the battle has not started yet
            time.sleep(5)
            continue
        if c[0] > c[2]:            # already armed
            break
        tap(*AUTO, wait=2)
    else:
        print("never saw the battle HUD")
        return
    set_speed_4x()

    deadline = time.time() + timeout
    misses = 0
    while time.time() < deadline:
        time.sleep(12)
        if sum(hud(grab())) <= 180:
            misses += 1
            if misses >= 2:        # two consecutive, so a cinematic is not a win
                print("battle ended")
                return
        else:
            misses = 0
    print("timeout")


if __name__ == "__main__":
    main()
