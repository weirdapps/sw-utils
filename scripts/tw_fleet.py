#!/usr/bin/env python3
"""
tw_fleet.py — set Territory War defensive FLEETS from the in-game preset tab.

Start on the PVP MISSION screen of the AIRSPACE territory — that is the only
fleet territory on the map, and on the zoomed-out map its slot count hides
behind the "Setup Phase" HUD text, which is how it got missed for a whole war.
Fleets pay +34 banners each, against +30 for a character squad.

Fleet presets CANNOT be pushed by push_ingame_presets.py (squads/game/set
rejects combatType 2), so the "Fleets > Main" tab it reads from is whatever was
built by hand in-game.

Flow per fleet, all of it discovered live:
  SET DEFENSIVE FLEET
    -> ["REMEMBER TO SAVE UNITS" gate]
    -> "SELECT YOUR CAPITAL SHIP" modal: pick ANY capital, the preset overrides it
    -> SELECT FLEET -> [scroll to the named preset] -> tap header
    -> SET -> ["not full" warning -> OK -> SET again]

  python3 scripts/tw_fleet.py Executrix Finalizer Endurance "Home One" Raddus
"""
import argparse
import os
import re
import subprocess
import sys
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORK = os.path.join(REPO, 'output')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tw_place as P                                    # noqa: E402

CAPITAL_SELECT = (356, 964)    # SELECT under the left-most capital card
BTN_SELECT_FLEET = (1208, 1008)
BTN_SET = (1670, 1008)
WARN_OK = (960, 692)


def _norm(s):
    return re.sub(r'[^a-z0-9]', '', s.lower())


def fleet_rows():
    """[(normalised name, y)] for visible preset rows in the fleet browser."""
    from PIL import Image
    P.shot()
    im = Image.open(P.SHOT).convert('L').crop((430, 140, 1150, 1080))
    im = im.resize((im.width * 2, im.height * 2), Image.LANCZOS)
    im.point(lambda p: 0 if p > 140 else 255).save(WORK + '/_f.png')
    im_txt = subprocess.run(['tesseract', WORK + '/_f.png', '-', '--psm', '6', 'tsv'],
                            capture_output=True, text=True).stdout
    lines = {}
    for ln in im_txt.splitlines()[1:]:
        f = ln.split('\t')
        if len(f) < 12 or not f[11].strip():
            continue
        lines.setdefault((f[2], f[3], f[4]), []).append(
            (int(f[6]), int(f[7]), int(f[9]), f[11]))
    out = []
    for ws in lines.values():
        ws.sort()
        txt = ' '.join(w[3] for w in ws)
        if 'Power' not in txt:
            continue
        top = sum(w[1] for w in ws) / len(ws)
        h = sum(w[2] for w in ws) / len(ws)
        out.append((_norm(txt.split('Power')[0]), int(140 + (top + h / 2) / 2), txt))
    return sorted(out, key=lambda r: r[1])


def fleet_power():
    txt = P.ocr((0, 155, 520, 215), thresh=140, psm='7')
    m = re.search(r'([\d.,]{5,})', txt)
    return int(re.sub(r'[.,]', '', m.group(1))) if m else None


def open_fleet_builder(tries=6):
    """Get from PVP MISSION to the fleet builder, whatever is currently on screen.

    The builder — not the capital modal — is the goal: a loaded preset replaces
    the capital anyway. Detected by its own SELECT FLEET button, because the
    capital modal overlays the builder and both report the same screen title.
    Written as react-to-what-is-there because the first tap on a freshly drawn
    screen intermittently does not register.
    """
    for _ in range(tries):
        P.shot()
        if 'FLEET' in P.ocr((1090, 985, 1345, 1032), thresh=150, psm='7').upper():
            return True
        if 'CAPITAL' in P.ocr((600, 30, 1340, 105), thresh=170, psm='7').upper():
            P.tap(*CAPITAL_SELECT, wait=3.5)       # any capital; the preset wins
        elif 'REMEMBER' in P.ocr((560, 320, 1400, 390), thresh=150, psm='7').upper():
            P.tap(*P.POPUP_SET, wait=3.5)
        else:
            P.tap(*P.BTN_SET_DEF, wait=3.5)
    return False


def place_fleet(name, max_scrolls=14):
    want = _norm(name)
    before = P.allied_count()
    if before is None:
        return False, 'not on PVP MISSION screen'

    if not open_fleet_builder():
        return False, f'{name}: could not reach the fleet builder'

    P.tap(*BTN_SELECT_FLEET, wait=3.8)
    target = None
    for _ in range(max_scrolls):
        rows = fleet_rows()
        hit = [r for r in rows if want in r[0] or r[0] in want]
        if hit:
            target = hit[0]
            break
        if not rows:
            P.swipe(down=True)
            continue
        P.swipe(down=True)
    if not target:
        return False, f'{name}: preset not found'

    P.tap(640, target[1], wait=3.2)
    P.shot()
    pw = fleet_power()
    if not pw or pw < 50000:
        return False, f'{name}: loaded power={pw} (ship conflict?)'

    P.tap(*BTN_SET, wait=4.0)
    if 'PVP' not in P.screen_title():
        P.tap(*WARN_OK, wait=3.0)                 # "squad is not full" warning
        P.tap(*BTN_SET, wait=4.5)

    after = P.allied_count()
    if after is None:
        return False, f'{name}: SET did not return to PVP MISSION'
    if after <= before:
        return False, f'{name}: count {before} -> {after} (did not grow)'
    return True, f'{name} set  power={pw:,}  airspace {after}/39'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('names', nargs='+')
    a = ap.parse_args()
    ok = 0
    for n in a.names:
        good, msg = place_fleet(n)
        print(('  OK  ' if good else '  FAIL ') + msg, flush=True)
        if not good:
            print('stopping — inspect device')
            break
        ok += 1
    print(f'\nplaced {ok}/{len(a.names)} fleets')


if __name__ == '__main__':
    main()
