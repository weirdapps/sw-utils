#!/usr/bin/env python3
"""Sweep the TW map and capture every territory's TITLE bar + officer NOTE bar.

OCR of the gold note bar is unreliable (tw_goto --scan returned "Jaba",
"eee SO EEE"), so this crops the two bands and stacks them into ONE image for
a human/vision read instead of trusting tesseract.

    python3 scripts/tw_scan_notes.py                 # tw_goto.CANDS, 10 wanted
    python3 scripts/tw_scan_notes.py --dense         # add a full grid sweep
    python3 scripts/tw_scan_notes.py --skip A,B      # ignore these first words
"""
import os
import re
import sys

from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tw_place as tp                                              # noqa: E402
import tw_goto as tg                                               # noqa: E402

OUT = os.path.expanduser("~/Downloads/tw_notes.png")
TITLE = (1050, 150, 1910, 220)
NOTE = (1055, 865, 1905, 950)
# The map disc drifts and re-centres on every panel open, so a fixed candidate
# list misses territories. The grid is the fallback: slow, but exhaustive.
GRID = [(x, y) for y in range(230, 960, 130) for x in range(110, 1560, 150)]


def grab():
    tp.shot()
    im = Image.open(tp.SHOT)
    return im.crop(TITLE), im.crop(NOTE)


def main():
    skip = set()
    if "--skip" in sys.argv:
        skip = {s.strip().lower()
                for s in sys.argv[sys.argv.index("--skip") + 1].split(",")}
    cands = tg.CANDS + (GRID if "--dense" in sys.argv else [])

    seen, bands = {}, []
    for xy in cands:
        title, _ = tg.probe(xy)      # probe() waits 3.4s and re-thresholds at 150
        if "ortification" not in title:
            continue
        # OCR sprinkles quotes/colons around the title, and a leading stray
        # token made a naive split()[0] key come back empty.
        flat = re.sub(r"[^a-z]", "", title.lower())
        key = flat.replace("fortification", "").replace("lon", "ion")
        if not key or key in seen or any(s in key for s in skip):
            continue
        t, n = grab()
        seen[key] = title
        bands.append((t, n))
        print(f"{len(seen):2d}. {title}   @{xy}", flush=True)
        if len(seen) >= int(os.environ.get("TW_WANT", "10")):
            break

    if not bands:
        print("no NEW territories found")
        return
    w = max(b[0].width for b in bands)
    h = sum(b[0].height + b[1].height + 8 for b in bands)
    sheet = Image.new("RGB", (w, h), (0, 0, 0))
    y = 0
    for t, n in bands:
        sheet.paste(t, (0, y)); y += t.height
        sheet.paste(n, (0, y)); y += n.height + 8
    sheet.save(OUT)
    print("wrote", OUT, sheet.size)


if __name__ == "__main__":
    main()
