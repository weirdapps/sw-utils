#!/usr/bin/env python3
"""Place Territory War defensive FLEETS by row index, the way tw_fill does squads.

tw_fleet.py seeks a preset by OCR of its name; on this UI that OCR is not good
enough to bet an irreversible SET on. Index the rows instead and let the game
arbitrate: a lineup whose ships are already committed raises RESTRICTED, so
CANCEL and move on. Fleets pay +34 banners each against +30 for a squad.

This map (Jakku) has TWO fleet territories, Airspace and Main Base, so the same
sweep is worth running in both.

Start on the PVP MISSION screen of a fleet territory:

    python3 scripts/tw_fleetfill.py 0 8
"""
import os
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tw_place as tp                                              # noqa: E402
import tw_fill as f                                                # noqa: E402

ADB = ["/opt/homebrew/bin/adb", "-s", "127.0.0.1:5555"]
CAPITAL_SELECT = (356, 964)     # SELECT under the left-most capital card
CAPITAL_TITLE = (600, 35, 1360, 100)   # centred 'SELECT YOUR CAPITAL SHIP'
BTN_SELECT_FLEET = (1208, 1008)
WARN_OK = (960, 692)
# Fleet rows carry a REINFORCEMENTS strip, so they are shorter than squad rows.
ROW_Y, ROW_PITCH, VIS = 307, 285, 3


def swipe(y1, y2, ms):
    subprocess.run(ADB + ["shell", "input", "swipe", "960", str(y1), "960",
                          str(y2), str(ms)], capture_output=True)


def one(idx, total):
    t = tp.screen_title()
    if "PVP" not in t:
        return "fatal", f"not on PVP ({t!r})"
    before = tp.allied_count()

    tp.tap(*tp.BTN_SET_DEF, wait=3.2)
    # Branching on ONE screen_title() read cost a wasted pass: the title OCRs as
    # garbage often enough ('BS'), and the fallback tap at POPUP_SET lands on an
    # ability card of the capital-ship picker, which opens an ability popup and
    # wedges the flow. Test the popup band for the gate instead, then react to
    # whatever screen is actually up, retrying the read rather than assuming.
    tp.shot()
    if "REMEMBER" in tp.ocr((450, 315, 1500, 385), thresh=170, psm="7").upper():
        tp.tap(*tp.POPUP_SET, wait=3.2)
    t = ""
    for _ in range(6):
        # 'SELECT YOUR CAPITAL SHIP' is a CENTRED modal title, so screen_title()'s
        # top-left box reads empty and returns 'BS'. Look in the middle for it.
        tp.shot()
        if "CAPITAL" in tp.ocr(CAPITAL_TITLE, thresh=170, psm="7").upper():
            tp.tap(*CAPITAL_SELECT, wait=3.2)    # the preset overrides this pick
            continue
        t = tp.screen_title().upper()
        if "INVENTORY" in t:
            break
        tp.tap(*BTN_SELECT_FLEET, wait=3.5)
    else:
        return "fatal", f"idx {idx}: fleet browser would not open ({t!r})"

    for _ in range(9):
        swipe(300, 900, 300)
        time.sleep(0.45)
    time.sleep(1.0)
    steps = min(idx, max(0, total - VIS))
    for _ in range(steps):
        swipe(800, 515, 900)
        time.sleep(0.7)
    time.sleep(0.8)
    tp.tap(640, ROW_Y + ROW_PITCH * (idx - steps), wait=3.2)

    if f.clear_popup() or (time.sleep(2.0) or f.clear_popup()):
        f.back_to_pvp()
        return "skip", f"idx {idx}: ships already committed"
    power = tp.squad_power()
    if not power:
        f.back_to_pvp()
        return "skip", f"idx {idx}: nothing loaded"

    tp.tap(*tp.BTN_SET, wait=4.0)
    # A lineup shorter than the 8 slots raises "not full"; OK only DISMISSES it,
    # so the SET has to be pressed a second time.
    if tp.allied_count() is None:
        tp.tap(*WARN_OK, wait=2.5)
        tp.tap(*tp.BTN_SET, wait=4.0)
    after = tp.allied_count()
    if after is None:
        return "fatal", f"idx {idx}: lost PVP ({tp.screen_title()!r})"
    if before is not None and after <= before:
        return "skip", f"idx {idx}: count stuck at {after} (power {power:,})"
    return "ok", f"idx {idx} power {power:,} -> allied {after}"


def main():
    lo, hi = int(sys.argv[1]), int(sys.argv[2])
    total = int(sys.argv[3]) if len(sys.argv) > 3 else hi + 1
    ok = 0
    for idx in range(lo, hi + 1):
        st, msg = one(idx, total)
        print(("  OK   " if st == "ok" else "  --   ") + msg, flush=True)
        if st == "ok":
            ok += 1
        elif st == "fatal":
            break
    print(f"\nplaced {ok}")


if __name__ == "__main__":
    main()
