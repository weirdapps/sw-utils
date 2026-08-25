#!/usr/bin/env python3
"""tw_fill.py — place Territory War defensive squads, one tab, index order.

This is what finally worked after tw_place.py's name-seek could not. It places
from the in-game preset tabs written by push_ingame_presets.py, and on
2026-08-25 it filled Trenches Fortification from 13/37 to 37/37 unattended.

THE DESIGN, and why each piece is the way it is:

* NO name OCR and NO colour detection of "is this squad spent". Both were tried
  and both failed. THE GAME ITSELF IS THE ORACLE: tapping a squad whose units
  are already committed to this war raises RESTRICTED CHARACTERS, so CANCEL and
  move to the next index. Anything that loads with non-zero Squad Power is
  placeable, so SET it.
* Colour detection failed twice for instructive reasons. A placed squad does
  turn its power-label chips maroon (140,80,97) against navy (16,33,50) — but
  sampling the PORTRAIT row instead catches dark-side units' RED ALIGNMENT
  RINGS and reports every squad as spent, and the chip row sits at header+250
  which drifts ~16px between exact scroll-top and post-swipe.
* Paging is deterministic: rewind to top, then ONE SLOW 320px SWIPE PER ROW
  (measured). Tap the header at y=340, which is inside the bar both at exact
  scroll-top (314) and after swipes (330). A 314 tap missed after swiping.

THREE BUGS THIS COST, all now guarded:
1. ⛔ tp.ocr() reads the LAST SAVED screenshot; it does NOT capture one.
   screen_title() calls shot() internally, ocr() does not. Without an explicit
   tp.shot() the popup check reads a stale frame and never fires — which
   presented as "nothing loaded" while the dialog sat there poisoning the next
   pass.
2. ⛔ The SELECT SQUAD browser opens on ITS OWN last-used tab, observed to be
   'TW 5v5 - Offense' every time, and that state is NOT shared with the
   Inventory > Squads screen. The tab must be tapped every single pass.
3. ⛔ After CANCEL you are left in the browser, not on PVP MISSION. Walk back
   before the next pass or everything after it fails.

⚠ tp.screen_title() OCRs the builder title as garbage often enough to matter
(observed 'BS' for 'SELECT DEFENSIVE SQUAD'), so squad_power() is the gate for
"a preset actually loaded", never the title.

Start on the PVP MISSION screen of the target territory:
  map -> tap territory -> ENTER (1497, 985)

  python3 scripts/tw_fill.py <first_index> <last_index> [--wall]
      --wall uses the 'TW 5v5 - Wall' tab instead of 'TW 5v5 - Defense'
"""
import os
import subprocess
import sys
import time

sys.path.insert(0, os.path.expanduser("~/SourceCode/sw-utils/scripts"))
os.chdir(os.path.expanduser("~/SourceCode/sw-utils"))

import tw_place as tp                                              # noqa: E402

ADB = ["/opt/homebrew/bin/adb", "-s", "127.0.0.1:5555"]
TAB_DEF, TAB_WALL = (183, 878), (183, 1052)
ROW_Y = 340
CANCEL, POPUP_X = (730, 710), (1385, 340)


def swipe(y1, y2, ms):
    subprocess.run(ADB + ["shell", "input", "swipe", "960", str(y1), "960",
                          str(y2), str(ms)], capture_output=True)


def clear_popup():
    # ⛔ tp.ocr() reads the LAST SAVED screenshot; it does not capture one.
    # screen_title() calls shot() internally, ocr() does not — so without this
    # the popup check was reading a stale frame and never fired.
    tp.shot()
    if "RESTRICTED" in tp.ocr((450, 315, 1500, 385), thresh=170, psm="7").upper():
        tp.tap(*CANCEL, wait=2.2)
        return True
    return False


def back_to_pvp(tries=4):
    """After CANCEL we are left in the browser, not on PVP MISSION. Walk back."""
    for _ in range(tries):
        if "PVP" in tp.screen_title():
            return True
        subprocess.run(ADB + ["shell", "input", "keyevent", "4"],
                       capture_output=True)
        time.sleep(3.0)
    return "PVP" in tp.screen_title()


def one(idx, tab):
    t = tp.screen_title()
    if "PVP" not in t:
        return "fatal", f"not on PVP ({t!r})"
    before = tp.allied_count()

    tp.tap(*tp.BTN_SET_DEF, wait=3.0)
    if "SELECT" not in tp.screen_title():
        tp.tap(*tp.POPUP_SET, wait=3.0)
    for _ in range(3):
        if "INVENTORY" in tp.screen_title():
            break
        tp.tap(*tp.BTN_SELECT, wait=3.5)
    else:
        return "fatal", "browser would not open"

    tp.tap(*tab, wait=2.6)
    for _ in range(7):
        swipe(300, 900, 300)
        time.sleep(0.5)
    time.sleep(1.0)
    for _ in range(idx):
        swipe(800, 480, 900)
        time.sleep(0.8)
    time.sleep(0.8)

    tp.tap(640, ROW_Y, wait=3.0)
    # The RESTRICTED popup can lag the tap, so look twice before believing the
    # squad loaded cleanly — a single check raced it and reported "nothing
    # loaded", leaving the dialog up to poison the next pass.
    if clear_popup() or (time.sleep(2.0) or clear_popup()):
        back_to_pvp()
        return "skip", f"idx {idx}: already committed"
    if not tp.squad_power():
        back_to_pvp()
        return "skip", f"idx {idx}: nothing loaded"
    tp.tap(*tp.BTN_SET, wait=4.5)
    after = tp.allied_count()
    if after is None:
        return "fatal", f"idx {idx}: lost PVP ({tp.screen_title()!r})"
    if before is not None and after <= before:
        return "skip", f"idx {idx}: count stuck at {after}"
    return "ok", f"idx {idx} -> {after}/37"


def main():
    lo, hi = int(sys.argv[1]), int(sys.argv[2])
    tab = TAB_WALL if "--wall" in sys.argv else TAB_DEF
    clear_popup()
    ok = 0
    for idx in range(lo, hi + 1):
        st, msg = one(idx, tab)
        print(("  OK   " if st == "ok" else "  --   ") + msg, flush=True)
        if st == "ok":
            ok += 1
        elif st == "fatal":
            break
    print(f"\nplaced {ok}")


if __name__ == "__main__":
    main()
