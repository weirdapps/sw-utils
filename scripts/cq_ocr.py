#!/usr/bin/env python3
"""OCR the live device screen, so a run can read the game without the Read tool.

Every other script here identifies a screen by pixel probes, which is enough to
drive the state machine but tells you nothing about *what* is on it -- which feat
is at 39/50, which unit landed in slot 3, whether the panel says VICTORY. This
fills that gap: grab a frame, optionally crop a region, upscale it and hand it to
tesseract.

Coordinates are in the same 1100-wide space as d.sh/cq_grind.py, so a region read
off a screenshot can be pasted straight in.

    python3 scripts/cq_ocr.py                      # whole screen
    python3 scripts/cq_ocr.py --region 0 90 810 600   # the feat list
    python3 scripts/cq_ocr.py --file /tmp/d.png --region 300 90 1100 300
"""
import argparse
import os
import subprocess
import tempfile

from PIL import Image

ADB = "/opt/homebrew/bin/adb"
SERIAL = os.environ.get("ANDROID_SERIAL", "127.0.0.1:5555")
K = 1920 / 1100.0


def grab(path):
    p = subprocess.run([ADB, "-s", SERIAL, "exec-out", "screencap", "-p"],
                       capture_output=True, timeout=60)
    if p.returncode != 0 or len(p.stdout) < 10000:
        raise RuntimeError("screencap failed")
    with open(path, "wb") as fh:
        fh.write(p.stdout)
    return path


def ocr(im, psm=6):
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as fh:
        tmp = fh.name
    im.save(tmp)
    out = subprocess.run(["/opt/homebrew/bin/tesseract", tmp, "stdout", "--psm", str(psm)],
                         capture_output=True, text=True, timeout=120)
    os.unlink(tmp)
    return out.stdout


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", help="read this image instead of the device")
    ap.add_argument("--region", nargs=4, type=int, metavar=("X0", "Y0", "X1", "Y1"),
                    help="crop box in 1100-space")
    ap.add_argument("--scale", type=float, default=2.0)
    ap.add_argument("--psm", type=int, default=6)
    ap.add_argument("--invert", action="store_true",
                    help="dark-on-light; SWGOH is mostly light-on-dark so this is the default off")
    a = ap.parse_args()

    path = a.file or grab("/tmp/cq_ocr.png")
    im = Image.open(path).convert("RGB")
    if a.region:
        x0, y0, x1, y1 = (int(v * K) for v in a.region)
        im = im.crop((x0, y0, x1, y1))
    w, h = im.size
    im = im.resize((int(w * a.scale), int(h * a.scale)), Image.LANCZOS).convert("L")
    if not a.invert:
        im = im.point(lambda v: 255 - v)   # tesseract wants dark text on light
    print(ocr(im, a.psm).strip())


if __name__ == "__main__":
    main()
