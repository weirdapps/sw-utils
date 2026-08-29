#!/usr/bin/env python3
"""
tw_place.py — set Territory War defensive SQUADS from the in-game preset tab.

Places the tw_wall.py bank (output/tw_wall.json, pushed in-game as the
"TW 5v5 - Wall" tab by push_ingame_presets.py --wall). There is no API for TW
placement — HotUtils' own /tw/* pages are Patreon-gated — so this drives the
device through the real UI.

Start with the device on the PVP MISSION screen of one territory (the allied
squads list with the green SET DEFENSIVE SQUAD button). Per squad:

  SET DEFENSIVE SQUAD -> [REMEMBER TO SAVE UNITS gate] -> SELECT SQUAD
    -> [scroll the browser to the squad] -> tap its HEADER row -> SET

and it re-reads ALLIED SQUADS n/39 to confirm the squad actually landed before
moving to the next one. A territory holds 39 squads GUILD-wide, first-come; the
39th raises "Max Capacity Reached" and you must move to another territory.

  python3 scripts/tw_place.py W02 W03 W04
  python3 scripts/tw_place.py --from 2 --to 22
"""
import argparse
import json
import os
import re
import subprocess
import time
import unicodedata

from PIL import Image

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHOT = REPO + '/farmbot/halts/_devtool.png'
WORK = os.path.join(REPO, 'output')

BTN_SET_DEF = (960, 992)      # green "SET DEFENSIVE SQUAD" on PVP MISSION
BTN_SELECT = (1208, 1008)     # "SELECT SQUAD" on SELECT DEFENSIVE SQUAD
BTN_SET = (1670, 1008)        # "SET" on SELECT DEFENSIVE SQUAD
# Once enough of the roster is committed, SET DEFENSIVE SQUAD first raises
# "REMEMBER TO SAVE UNITS - units do not refresh". It is only a gate to the same
# screen; its SET continues. It did NOT appear for the first four placements.
POPUP_SET = (1184, 710)
LIST_SWIPE = (960, 900, 960, 320, 420)   # one screenful up in the squad list


def tap(x, y, wait=2.5):
    subprocess.run(['python3', '-m', 'farmbot.devtool', 'tap', str(x), str(y)],
                   cwd=REPO, capture_output=True)
    time.sleep(wait)


def swipe(down=True, wait=2.6):
    """down=True scrolls the list toward HIGHER Wnn (content moves up)."""
    x1, y1, x2, y2, ms = LIST_SWIPE
    args = (x1, y1, x2, y2, ms) if down else (x1, y2, x2, y1, ms)
    subprocess.run(['python3', '-m', 'farmbot.devtool', 'swipe',
                    *map(str, args)], cwd=REPO, capture_output=True)
    time.sleep(wait)


CROP = (430, 140, 1150, 1080)   # squad-name column of the browser, below the tabs


def _header_rows(thresh=140):
    """[(label, y_centre, raw_text)] for the squad headers currently on screen.

    tesseract needs the light-on-dark UI inverted to a hard black-on-white before
    it reads anything at all, and the TSV line grouping is what gives the y to
    tap. The label here is unreliable (see wall_order) — the TEXT is the payload.
    """
    im = Image.open(SHOT).convert('L').crop(CROP)
    im = im.resize((im.width * 2, im.height * 2), Image.LANCZOS)
    im = im.point(lambda p: 0 if p > thresh else 255)
    p = os.path.join(WORK, '_rows.png')
    im.save(p)
    tsv = subprocess.run(['tesseract', p, '-', '--psm', '6', 'tsv'],
                         capture_output=True, text=True).stdout
    lines = {}
    for ln in tsv.splitlines()[1:]:
        f = ln.split('\t')
        if len(f) < 12 or not f[11].strip():
            continue
        key = (f[2], f[3], f[4])                       # block, par, line
        lines.setdefault(key, []).append((int(f[6]), int(f[7]), int(f[9]), f[11]))
    out = []
    for ws in lines.values():
        ws.sort()
        txt = ' '.join(w[3] for w in ws)
        m = re.search(r'\bW\s?([O0-9oO]{2,3})\b', txt)   # OCR renders 0 as O
        if not m:
            continue
        num = m.group(1).replace('O', '0').replace('o', '0')
        top = sum(w[1] for w in ws) / len(ws)
        h = sum(w[2] for w in ws) / len(ws)
        out.append((f"W{int(num):02d}", int(CROP[1] + (top + h / 2) / 2), txt))
    return sorted(out, key=lambda r: r[1])


def _norm(s):
    return re.sub(r'[^a-z0-9]', '', s.lower())


def wall_order():
    """[(label, normalised lead name)] in list order — the whole defensive board.

    Matching rows by NAME, not by the 'Fnn/Mnn/Bnn' prefix: the squad icon left of
    the name OCRs as a digit often enough that 'W21' comes back as 'W221', which
    made a number-based seek believe it had overshot and oscillate forever.

    ⭐ Reads data/tw_board.json since 2026-08-26. That file replaced tw_wall.py's
    generated overflow, and it holds the ENTIRE board — graded bank and bench in one
    front-to-back order — so graded_order() is no longer a separate special case.
    The labels it yields are the in-game preset names (`F01`, `M14`, `B27`), which
    push_ingame_presets.build_tw_board() writes from the same file, so the strings
    match on the device by construction rather than by hope. Falls back to the old
    tw_wall.json only if the board file is missing.
    """
    board = os.path.join(REPO, 'data', 'tw_board.json')
    if os.path.exists(board):
        src = json.load(open(board))
        out = []
        for s in src['defense']:
            nm = unicodedata.normalize('NFKD', s['name']).encode('ascii', 'ignore').decode()
            out.append((s['id'], _norm(nm)[:9]))
        return out
    src = json.load(open(os.path.join(REPO, 'output', 'tw_wall.json')))
    out = []
    for i, s in enumerate(src['wall'], 1):
        nm = unicodedata.normalize('NFKD', s['lead_name']).encode('ascii', 'ignore').decode()
        out.append((f'W{i:02d}', _norm(nm)[:9]))
    return out


def graded_order():
    """[(label, normalised lead name)] for the GRADED bank — the strong 22 that live
    in the 'TW 5v5 - Defense' tab.

    ⛔ Why this exists: wall_order() reads tw_wall.json['wall'], which is ONLY the
    33-squad overflow, so `tw_place.py D01` died with "D01 is not in tw_wall.json"
    and the STRONGEST squads — the ones front-load doctrine puts in T1/B1 — were the
    one thing this script could not place. They had to go in by hand.

    Names are derived from output/upload_payload.json, the same file
    push_ingame_presets.build() writes the tab from, so the strings match in-game
    by construction rather than by hope.
    """
    pay = json.load(open(os.path.join(REPO, 'output', 'upload_payload.json')))
    out = []
    for p in pay:
        if p.get('cat') != 'TW 5v5 - Defense':
            continue
        m = re.search(r'\b(D\d{2})\s+(.+?)\s*\d*%?$', p.get('n', ''))
        if not m:
            continue
        nm = unicodedata.normalize('NFKD', m.group(2)).encode('ascii', 'ignore').decode()
        out.append((m.group(1), _norm(nm)[:9]))
    return sorted(out)


def _exists(*parts):
    return os.path.exists(os.path.join(REPO, *parts))


ORDER = (wall_order() if _exists('data', 'tw_board.json') or _exists('output', 'tw_wall.json')
         else [])

# Tab rows in the SELECT SQUAD browser's left rail, device coords. Measured off a
# live capture: the rail listed Recommended / PROG / GAC 5v5 Def / GAC 5v5 Off /
# GAC 3v3 Def / GAC 3v3 Off / TW 5v5 Def / TW 5v5 Off / TW 5v5 Wall, ~88px apart.
#
# ⛔ STALE AS OF 2026-08-26 AND NOT RE-MEASURED. The three TW tabs those coordinates
# point at were deleted and replaced by FOUR — `TW 1 Def FRONT`, `TW 2 Def MID`,
# `TW 3 Def BACK`, `TW 4 Offense` — so the rail is one row longer and everything
# below the GAC block has moved. These y-values now select the WRONG TAB, and the
# failure is silent: the browser opens, OCR finds no matching squad name, and the
# seek looks like a scroll problem rather than a wrong tab. **Re-measure against a
# live capture before the next placement run** (~88px apart, first TW row is the
# 7th). Left in place rather than guessed at: a guessed coordinate that is nearly
# right is worse than one that is obviously stale.
TAB_TW_DEFENSE = (183, 878)
TAB_TW_WALL = (183, 1052)
TAB = None


def read_rows(retries=2):
    """[(index, label, y)] for the visible header rows, matched on squad name."""
    for _ in range(retries + 1):
        shot()
        found = _header_rows()
        hits = []
        for _label, y, txt in found:
            t = _norm(txt)
            for i, (label, nm) in enumerate(ORDER):
                if nm and nm in t:
                    hits.append((i, label, y))
                    break
        if hits:
            return sorted(hits)
        time.sleep(1.2)
    return []


def shot():
    subprocess.run(['python3', '-m', 'farmbot.devtool', 'shot'], cwd=REPO,
                   capture_output=True)


def ocr(box, thresh=140, psm='6'):
    im = Image.open(SHOT).convert('L').crop(box)
    im = im.resize((im.width * 2, im.height * 2), Image.LANCZOS)
    im = im.point(lambda p: 0 if p > thresh else 255)
    p = os.path.join(WORK, '_ocr.png')
    im.save(p)
    return subprocess.run(['tesseract', p, '-', '--psm', psm],
                          capture_output=True, text=True).stdout.strip()


def screen_title():
    """Top-left screen name: 'PVP MISSION' / 'SELECT DEFENSIVE SQUAD' / 'INVENTORY'."""
    shot()
    return ocr((90, 10, 520, 70), thresh=170, psm='7').upper()


def allied_count():
    """'ALLIED SQUADS 21/39' -> 21, or None if not on the PVP MISSION screen."""
    shot()
    txt = ocr((700, 150, 1250, 205), psm='7')
    m = re.search(r'(\d+)\s*/\s*(\d+)', txt)
    return int(m.group(1)) if m else None


def squad_power():
    """'Squad Power: 125,988' on the SELECT DEFENSIVE SQUAD screen.

    Take EVERY digit after the label, not the first `[\\d.,]{4,}` run: tesseract
    renders the thousands separator as a comma, a period or a space more or less
    at random, and on a space it returned 116 for 116,650 -- fine as a truthy
    'a squad loaded' test, useless once the number itself is the check.
    """
    txt = ocr((0, 155, 520, 215), psm='7')
    tail = txt.split(':')[-1] if ':' in txt else txt
    digits = re.sub(r'\D', '', tail)
    return int(digits) if digits else None


def place_one(label, max_scrolls=12):
    before = allied_count()
    if before is None:
        return False, 'not on PVP MISSION screen'
    tap(*BTN_SET_DEF, wait=3.2)
    if 'SELECT' not in screen_title():
        tap(*POPUP_SET, wait=3.2)              # "REMEMBER TO SAVE UNITS" gate
    title = screen_title()
    if 'SELECT' not in title:
        return False, f'{label}: stuck on {title!r} after SET DEFENSIVE SQUAD'
    for _ in range(3):                         # the tap that opens the browser
        if 'INVENTORY' in screen_title():      # misfires often enough to matter
            break
        tap(*BTN_SELECT, wait=3.5)
    else:
        return False, f'{label}: squad browser would not open'

    # ⛔ The browser opens on ITS OWN last-used tab, and that state is NOT shared
    # with the Inventory > Squads screen — selecting the tab there and navigating
    # back does nothing. Observed: it lands on 'TW 5v5 - Offense' every time, so a
    # D-label seek scrolls the wrong list forever and dies "not found in list".
    # Tap the tab we actually want, every time, before seeking.
    if TAB:
        tap(*TAB, wait=2.5)

    want = [i for i, (lab, _) in enumerate(ORDER) if lab == label]
    if not want:
        return False, f'{label} is not in tw_wall.json'
    want = want[0]
    target = None
    for _ in range(max_scrolls):
        found = read_rows()
        hit = [r for r in found if r[0] == want]
        if hit:
            target = hit[0]
            break
        idx = [r[0] for r in found]
        if not idx:
            swipe(down=True)                    # blank read: nudge and re-look
        elif min(idx) > want:
            swipe(down=False)                   # overshot — come back up
        else:
            swipe(down=True)
    if not target:
        return False, f'{label} not found in list'

    tap(640, target[2], wait=3.0)
    shot()
    power = squad_power()
    if not power or power < 6000:
        return False, f'{label} loaded with power={power}'
    tap(*BTN_SET, wait=4.5)

    shot()
    after = allied_count()
    if after is None:
        return False, f'{label}: SET did not return to PVP MISSION'
    if after <= before:
        return False, f'{label}: count {before} -> {after} (did not grow)'
    # NB: guildmates fill the same territory concurrently, so the jump can be >1.
    # Authoritative check is STATS -> Total Banners / 30 at the end.
    return True, f'{label} set  power={power:,}  territory {after}/39'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('labels', nargs='*')
    ap.add_argument('--from', dest='lo', type=int)
    ap.add_argument('--to', dest='hi', type=int)
    ap.add_argument('--graded', action='store_true',
                    help="place the strong 'TW 5v5 - Defense' bank (D01-D22) instead "
                         "of the tw_wall overflow (W01-W33). Front territories want "
                         "these; the wall is for the back.")
    a = ap.parse_args()

    global ORDER, TAB
    ORDER = graded_order() if a.graded else ORDER
    TAB = TAB_TW_DEFENSE if a.graded else TAB_TW_WALL
    prefix = 'D' if a.graded else 'W'
    labels = a.labels or [f'{prefix}{i:02d}' for i in range(a.lo, a.hi + 1)]

    known = {lab for lab, _nm in ORDER}
    unknown = [x for x in labels if x not in known]
    if unknown:
        print(f"not in the {'graded' if a.graded else 'wall'} bank: {', '.join(unknown)}")
        print(f"available: {', '.join(lab for lab, _ in ORDER)}")
        return

    shot()
    ok = 0
    for lab in labels:
        good, msg = place_one(lab)
        print(('  OK  ' if good else '  FAIL ') + msg, flush=True)
        if not good:
            print('stopping — device left mid-flow, inspect before continuing')
            break
        ok += 1
    print(f'\nplaced {ok}/{len(labels)}')


if __name__ == '__main__':
    main()
