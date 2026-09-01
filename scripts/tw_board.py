#!/usr/bin/env python3
"""
tw_board.py — validate and emit the RESEARCHED Territory War board.

WHY THIS REPLACES tw_wall.py's OUTPUT. tw_wall.py built the deep bench by
*shared-faction-tag affinity*: take an idle leader, give it the four roster units
with the rarest tag in common. That is not a team. It produced lineups like
"Ugnaught / General Syndulla / Kuiil / Darth Sidious / Poe Dameron" and
"Tarfful / Zaalbar / Yoda & Chewie / Veteran Smuggler Chewbacca / Vandor
Chewbacca" — five units that share a string, with no leader ability that reaches
them and no mechanic that survives contact with an attacker.

It also imported a GAC rule it had no business importing. `ATTACK_ONLY_BY_FORMAT`
is doctrine E, measured by gac_doctrine.py on GAC rounds where a wall only pays if
it denies banners the opponent would otherwise take. Territory War does not work
that way: **defense banks a flat +30 the moment it is set**, win or lose, and there
is no per-player cap. Under that rule a Galactic Legend left on the bench earns
zero and denies zero. Eight of nine GLs were benched, and two of them — JMK and
SEE — had no TW squad of any kind.

So the source of truth here is a hand-curated, researched file, not a solver:

    data/tw_board.json     every squad, with WHY it holds and WHERE it goes

and this script's only jobs are to prove the file is fieldable and to turn it into
the two artefacts that get used:

    output/tw_upload_payload.json   HotUtils squad definitions (upload_hotutils.py)
    output/tw_placement_sheet.txt   the front-to-back order you place from

The checks are the point. A squad that fails one is a bug in the DATA FILE:
  * every unit is owned, is a character, and clears the gear floor;
  * no unit appears twice anywhere on the board — a unit set on TW defense cannot
    attack, and a unit already placed cannot be placed again;
  * squads are the declared size;
  * every band is a real band, and the order is strongest-front.

Run:
    python3 scripts/tw_board.py                 # validate + report + write
    python3 scripts/tw_board.py --check         # validate only, non-zero on failure
    python3 scripts/tw_board.py --idle          # what is still on the bench
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import swgoh_data                                            # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
OUT = os.path.join(ROOT, "output")
BOARD_FILE = os.path.join(DATA, "tw_board.json")

# Read off the live territory panel (notes.md 2026-08-11), not from a wiki.
BANNERS_PER_SQUAD = 30
FLEET_BANNERS = 34
POWER_MINIMUM = 6000

# Front-to-back. The front territory gates the map and absorbs the attacker's
# freshest squads, so it takes the strongest walls; BACK sees leftovers.
BANDS = ["FRONT", "MID", "BACK"]

GEAR_FLOOR = 13

# HotUtils categories become filter groups in the app, and the in-game preset tabs
# mirror them. Defense is split by BAND rather than kept as one 50-row list, because
# the question you answer at the map is "does this squad go in a front territory or a
# back one" — a single list cannot tell you where to stop. Every category starts with
# "TW " so `upload_hotutils.py --categories "TW "` scopes the destructive half to
# Territory War and cannot touch the GAC board.
CATEGORY = {"FRONT": "TW - Def FRONT", "MID": "TW - Def MID", "BACK": "TW - Def BACK",
            "offense": "TW - Offense",
            "fleet_def": "TW Fleet - Defense", "fleet_off": "TW Fleet - Offense"}


def load_roster(path=None):
    """{baseId: unit} for everything owned, characters and ships alike."""
    roster = json.load(open(path or swgoh_data.latest_roster_file()))
    return {u["b"]: u for u in roster["units"]}, roster.get("meta", {})


def relic(unit):
    """Displayed relic level. The API's `rt` is offset by 2 (rt 9 == R7)."""
    return unit.get("rt", 2) - 2


def squads_of(board):
    """Every character squad on the board, defense then offense, in file order."""
    return ([dict(s, side="defense") for s in board.get("defense", [])] +
            [dict(s, side="offense") for s in board.get("offense", [])])


def validate(board, own):
    """Return (errors, warnings). An error means the board cannot be fielded."""
    errors, warnings = [], []
    seen = {}
    ids = set()

    for s in squads_of(board):
        sid = s.get("id", "?")
        if sid in ids:
            errors.append(f"{sid}: duplicate squad id")
        ids.add(sid)

        units = s.get("units") or []
        size = s.get("size", 5)
        if len(units) != size:
            errors.append(f"{sid} {s.get('name')}: {len(units)} units, declared size {size}")
        if len(set(units)) != len(units):
            errors.append(f"{sid} {s.get('name')}: repeats a unit inside the squad")

        for b in units:
            u = own.get(b)
            if u is None:
                errors.append(f"{sid} {s.get('name')}: {b} is NOT OWNED")
                continue
            if u["ct"] != 1:
                errors.append(f"{sid} {s.get('name')}: {b} is a ship, not a character")
                continue
            if b in seen:
                errors.append(f"{sid} {s.get('name')}: {b} ({u['n']}) already used by "
                              f"{seen[b]} — a TW unit is single-use")
            seen[b] = f"{sid} {s.get('name')}"
            if u["g"] < GEAR_FLOOR:
                warnings.append(f"{sid} {s.get('name')}: {u['n']} is G{u['g']} "
                                f"(below G{GEAR_FLOOR})")

        if s["side"] == "defense":
            band = s.get("band")
            if band not in BANDS:
                errors.append(f"{sid} {s.get('name')}: band {band!r} not in {BANDS}")
            power = sum(own[b].get("gp", 0) for b in units if b in own)
            if power and power < POWER_MINIMUM:
                errors.append(f"{sid} {s.get('name')}: {power} GP is under the "
                              f"{POWER_MINIMUM} territory minimum")

    # Defense must be ordered strongest-front: FRONT before MID before BACK.
    rank = {b: i for i, b in enumerate(BANDS)}
    order = [rank.get(s.get("band"), 99) for s in board.get("defense", [])]
    if order != sorted(order):
        errors.append("defense is not in band order — the file IS the placement "
                      "order, so FRONT rows must come before MID before BACK")

    for f in board.get("fleets", {}).get("defense", []) + \
            board.get("fleets", {}).get("offense", []):
        for b in f.get("units", []):
            if b not in own:
                errors.append(f"fleet {f.get('name')}: {b} is NOT OWNED")
            elif own[b]["ct"] == 1:
                errors.append(f"fleet {f.get('name')}: {b} is a character, not a ship")
    return errors, warnings, seen


def payload(board, own):
    """HotUtils definitions, in upload_hotutils.py's {n,sz,ct,cat,u} shape."""
    out = []
    for s in board.get("defense", []):
        out.append({"n": s["hu_name"], "sz": len(s["units"]), "ct": 1,
                    "cat": CATEGORY[s["band"]],
                    "u": [[b, own[b]["n"]] for b in s["units"]]})
    for s in board.get("offense", []):
        out.append({"n": s["hu_name"], "sz": len(s["units"]), "ct": 1,
                    "cat": CATEGORY["offense"],
                    "u": [[b, own[b]["n"]] for b in s["units"]]})
    for side, key in (("defense", "fleet_def"), ("offense", "fleet_off")):
        for f in board.get("fleets", {}).get(side, []):
            out.append({"n": f["hu_name"], "sz": len(f["units"]), "ct": 2,
                        "cat": CATEGORY[key],
                        "u": [[b, own[b]["n"]] for b in f["units"]]})
    return out


def sheet(board, own):
    """The front-to-back placement order, as a human reads it during setup."""
    d = board.get("defense", [])
    fleets = board.get("fleets", {}).get("defense", [])
    total = len(d) * BANNERS_PER_SQUAD + len(fleets) * FLEET_BANNERS
    lines = [
        "TERRITORY WAR — DEFENSIVE PLACEMENT ORDER",
        f"{len(d)} squads x{BANNERS_PER_SQUAD} + {len(fleets)} fleets x{FLEET_BANNERS} "
        f"= {total} guaranteed banners",
        "",
        "Place TOP-DOWN. FRONT rows go into the front-most territories (the ones the",
        "enemy must clear first); BACK rows are the last thing you set, and must never",
        "take a front slot — the per-territory cap is GUILD-WIDE and first-come, so a",
        "front slot spent on filler is a slot no guildmate can use.",
        "",
    ]
    band = None
    for s in d:
        if s["band"] != band:
            band = s["band"]
            lines += ["", f"===== {band} =====", ""]
        lines.append(f"{s['id']:<4} {s['name']:<34} {' · '.join(own[b]['n'] for b in s['units'])}")
        if s.get("why"):
            lines.append(f"     ^ {s['why']}")
    if fleets:
        lines += ["", "===== AIRSPACE (fleet territory) =====", ""]
        for f in fleets:
            lines.append(f"{f['id']:<4} {f['name']:<34} "
                         f"{' · '.join(own[b]['n'] for b in f['units'])}")
    off = board.get("offense", [])
    if off:
        lines += ["", "===== HELD BACK FOR OFFENSE (do NOT set on defense) =====", ""]
        for s in off:
            lines.append(f"{s['id']:<4} {s['name']:<34} "
                         f"{' · '.join(own[b]['n'] for b in s['units'])}")
            if s.get("for"):
                lines.append(f"     ^ {s['for']}")
    return "\n".join(lines) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--board", default=BOARD_FILE)
    ap.add_argument("--roster", default=None, help="default: newest data/roster/*.json")
    ap.add_argument("--check", action="store_true", help="validate only; exit 1 on error")
    ap.add_argument("--idle", action="store_true", help="list unused G13+ characters")
    a = ap.parse_args()

    board = json.load(open(a.board))
    own, meta = load_roster(a.roster)
    errors, warnings, used = validate(board, own)

    d, o = board.get("defense", []), board.get("offense", [])
    fd = board.get("fleets", {}).get("defense", [])
    print(f"roster {meta.get('pulled', '?')} · {len(own)} owned")
    print(f"defense {len(d)} squads · offense {len(o)} squads · defensive fleets {len(fd)}")
    print(f"guaranteed banners: {len(d) * BANNERS_PER_SQUAD + len(fd) * FLEET_BANNERS}")
    for b in BANDS:
        n = sum(1 for s in d if s.get("band") == b)
        print(f"  {b:<6} {n:>3} squads")

    g13 = {b for b, u in own.items() if u["ct"] == 1 and u["g"] >= GEAR_FLOOR}
    idle = sorted(g13 - set(used), key=lambda b: -own[b].get("gp", 0))
    print(f"G13+ characters: {len(g13)} · on the board: {len(g13 & set(used))} · idle: {len(idle)}")

    if warnings:
        print(f"\n{len(warnings)} warning(s):")
        for w in warnings:
            print(f"  ~ {w}")
    if errors:
        print(f"\n{len(errors)} ERROR(S) — fix data/tw_board.json:")
        for e in errors:
            print(f"  ! {e}")
    if a.idle:
        print("\nidle G13+ characters:")
        for b in idle:
            print(f"  {b:<32} {own[b]['n']:<38} G{own[b]['g']} R{relic(own[b])}")
    if a.check:
        sys.exit(1 if errors else 0)
    if errors:
        sys.exit("refusing to write an unfieldable board")

    os.makedirs(OUT, exist_ok=True)
    p = os.path.join(OUT, "tw_upload_payload.json")
    json.dump(payload(board, own), open(p, "w"), indent=1)
    s = os.path.join(OUT, "tw_placement_sheet.txt")
    open(s, "w").write(sheet(board, own))
    print(f"\nwrote {os.path.relpath(p, ROOT)} and {os.path.relpath(s, ROOT)}")


if __name__ == "__main__":
    main()
