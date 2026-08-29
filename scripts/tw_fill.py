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

  python3 scripts/tw_fill.py <first_index> <last_index> [--tab FRONT|MID|BACK]
  python3 scripts/tw_fill.py --idx 1,4,10 [--tab MID]
      --idx places exactly those 0-based rows, which is what the guild's
      per-territory notes need: 'Lord V-Rey' in Trenches is rows 1 and 4 of
      the FRONT tab and nothing in between.
"""
import json
import os
import subprocess
import sys
import time

sys.path.insert(0, os.path.expanduser("~/SourceCode/sw-utils/scripts"))
os.chdir(os.path.expanduser("~/SourceCode/sw-utils"))

import tw_place as tp                                              # noqa: E402
import swgoh_data as sd                                            # noqa: E402

ADB = ["/opt/homebrew/bin/adb", "-s", "127.0.0.1:5555"]
# Left-nav tab rows in the SELECT SQUAD browser. The 2026-08-26 rebuild replaced
# the two TW tabs with four banded ones, so the old TAB_DEF/TAB_WALL pair is gone.
# Order below the four GAC tabs: FRONT, MID, BACK, then Offense off the bottom.
TABS = {"FRONT": (183, 878), "MID": (183, 967), "BACK": (183, 1056)}
ROW_Y = 340
ROW_PITCH = 318       # measured: headers sit at 314, 640, 958
VIS = 3               # squad rows on screen at once
Y_LAST = 805          # header of the LAST row once the list is scrolled to its end
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


LOOSE = False       # set by --loose
SPAN = 3            # how far a mis-registered swipe could have slipped
TIGHT = 1000        # below the 1,208 GP minimum gap between adjacent rows
DRIFT = 2500        # roster file vs live: gear/mod changes since the last pull


def board_rows():
    """{tab: [(preset name, expected squad power) per row]}.

    Read from the same files the presets were pushed from, so the expectation
    and the device cannot drift apart by construction.

    Power, not the name, is the check. Paging is 'one 320px swipe per row', so a
    single mis-registered swipe shifts every later index by one and SET is
    irreversible, but OCR of the name bar is not good enough to catch it: the
    header for 'B13 Geonosian Br' came back as 'R12 Gaeanacian Re por ENE',
    which fuzzy-matched to B15. Squad Power is a large clean numeral that
    squad_power() already reads reliably, and adjacent rows differ by at least
    1,208 GP, so nearest-of-the-neighbours identifies the row unambiguously.
    """
    import push_ingame_presets as pip                              # noqa: PLC0415
    board = json.load(open("data/tw_board.json"))
    gp = {u["b"]: u["gp"] for u in
          json.load(open(sd.latest_roster_file()))["units"]}
    def row(s):
        return (pip.ascii_name(f"{s['id']} {s['name']}"),
                sum(gp[u] for u in s["units"]))
    out = {band: [row(s) for s in board["defense"] if s.get("band") == band]
           for band, _tab in pip.TW_BOARD_TABS}
    out["OFFENSE"] = [row(s) for s in board["offense"]]
    return out


def row_matches(rows, idx, power):
    """Is the squad that just loaded the one at `idx`, or did paging slip?"""
    if LOOSE:
        # Both remaining destinations are free back territories, so a one-row
        # slip just swaps two squads that were going to the same place, and the
        # skipped one is re-run afterwards. Only catch a gross failure here:
        # the roster file is days old and the mod optimiser moves 1,000+ mods,
        # so per-unit power drifts by ~2,000 in BOTH directions and no tight
        # threshold can separate M09 (145,043) from M11 (144,737) anyway.
        off = abs(rows[idx][1] - power)
        return off <= 12000, f"{rows[idx][0]!r} power {power:,} (loose)"
    off = abs(rows[idx][1] - power)
    # Adjacent rows differ by at least 1,208 GP, so a hit inside TIGHT identifies
    # the row on its own. Checking the neighbours FIRST rejected a correct load:
    # F14 read 159,927 against a stale-roster 160,527, and F11 (159,541, three
    # rows away and already placed) was nearer.
    if off <= TIGHT:
        return True, f"{rows[idx][0]!r} power {power:,}"
    near = [i for i in range(idx - SPAN, idx + SPAN + 1) if 0 <= i < len(rows)]
    best = min(near, key=lambda i: abs(rows[i][1] - power))
    if best != idx:
        return False, (f"power {power:,} is closer to {rows[best][0]!r} "
                       f"({rows[best][1]:,}) than to {rows[idx][0]!r} "
                       f"({rows[idx][1]:,})")
    if off > DRIFT:
        return False, (f"power {power:,} is {off:,} off {rows[idx][0]!r} "
                       f"({rows[idx][1]:,})")
    return True, f"{rows[idx][0]!r} power {power:,}"


def one(idx, tab, expect=None):
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

    # The left-hand TAB list scrolls too, and it keeps its position between
    # visits. Rewind it to the top or TABS' coordinates point at the wrong tab:
    # after scrolling down to reach 'TW 4 Offense', (183, 878) is TW 3, not TW 1.
    for _ in range(3):
        subprocess.run(ADB + ["shell", "input", "swipe", "183", "420",
                              "183", "1000", "500"], capture_output=True)
        time.sleep(0.5)
    tp.tap(*tab, wait=2.6)
    for _ in range(7):
        swipe(300, 900, 300)
        time.sleep(0.5)
    time.sleep(1.0)
    # The list stops scrolling once the last row is on screen, so the final
    # VIS-1 rows can never be brought to the top slot. Scroll as far as the list
    # allows, then tap the slot the row actually landed in. Without this, idx 12
    # and 13 of the 14-row FRONT tab re-tapped row 11 and came back RESTRICTED.
    total = len(expect) if expect else idx + VIS
    if idx <= total - VIS:
        steps, y = idx, ROW_Y
    else:
        # Past that point the list is bottom-anchored: over-scroll and index
        # UP from the last row, whose header always lands at the same y.
        steps, y = total + 3, Y_LAST - ROW_PITCH * (total - 1 - idx)
    for _ in range(steps):
        swipe(800, 480, 900)
        time.sleep(0.8 if steps <= VIS + 2 else 0.45)
    time.sleep(1.0)

    tp.tap(640, y, wait=3.0)
    # The RESTRICTED popup can lag the tap, so look twice before believing the
    # squad loaded cleanly — a single check raced it and reported "nothing
    # loaded", leaving the dialog up to poison the next pass.
    if clear_popup() or (time.sleep(2.0) or clear_popup()):
        back_to_pvp()
        return "skip", f"idx {idx}: already committed"
    power = tp.squad_power()
    if not power:
        back_to_pvp()
        return "skip", f"idx {idx}: nothing loaded"
    if expect:
        good, why = row_matches(expect, idx, power)
        if not good:
            back_to_pvp()          # loaded but NOT set; nothing is committed yet
            # A skip, not a fatal: paging drifts by a row at high indices, so one
            # bad row must not abandon the other twenty in the batch. Re-sweep the
            # tab afterwards and RESTRICTED will report whatever already landed.
            return "skip", f"idx {idx}: WRONG SQUAD LOADED, {why}"
    tp.tap(*tp.BTN_SET, wait=4.5)
    after = tp.allied_count()
    if after is None:
        return "fatal", f"idx {idx}: lost PVP ({tp.screen_title()!r})"
    if before is not None and after <= before:
        return "skip", f"idx {idx}: count stuck at {after}"
    return "ok", f"idx {idx} -> allied {after}"


def main():
    global LOOSE
    argv = sys.argv[1:]
    if "--loose" in argv:
        LOOSE = True
        argv.remove("--loose")
    name = "FRONT"
    if "--tab" in argv:
        i = argv.index("--tab")
        name = argv[i + 1].upper()
        del argv[i:i + 2]
    tab = TABS[name]
    if "--idx" in argv:
        i = argv.index("--idx")
        rows = [int(v) for v in argv[i + 1].split(",")]
    else:
        rows = list(range(int(argv[0]), int(argv[1]) + 1))
    rowdefs = board_rows().get(name, [])
    print(f"tab {name} rows {rows} -> "
          + ", ".join(rowdefs[i][0] if i < len(rowdefs) else "?" for i in rows),
          flush=True)
    clear_popup()
    ok = 0
    for idx in rows:
        st, msg = one(idx, tab, rowdefs or None)
        print(("  OK   " if st == "ok" else "  --   ") + msg, flush=True)
        if st == "ok":
            ok += 1
        elif st == "fatal":
            break
    print(f"\nplaced {ok}")


if __name__ == "__main__":
    main()
