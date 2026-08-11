#!/usr/bin/env python3
"""
push_ingame_presets.py — write the board into the GAME's squad-preset tabs.

HotUtils squads (upload_hotutils.py) live on the website. This pushes the same
board into the in-game preset manager (Inventory -> Squads), which is what you
actually tap during a GAC or TW round.

    HU_SID=<live session> python3 scripts/push_ingame_presets.py --dry-run
    HU_SID=<live session> python3 scripts/push_ingame_presets.py --push

Hard limits of `squads/game/set`, learned the hard way - do not re-discover:
  * FLEETS CANNOT BE PUSHED. combatType 2 is rejected with "Currently only
    character squad presets are supported". The 3 GAC defense fleets, 3 offense
    fleets and the arena fleet must be set by hand in-game.
  * PRESET NAMES ARE ~16 CHARS. Longer returns INVALID_SQUAD_PRESET_NAME_LENGTH_KEY.
    The tab already carries the format and phase, so names here are just
    "D01 <short leader>".
  * `id: null` ALWAYS CREATES A NEW TAB - there is no dedup by name. Push the same
    new tab twice and you get two of them. Existing tabs must be updated BY ID, so
    this script re-reads squads/game/get every run and matches on name.
  * A tab is deleted with {id, name, unique, combatType, void: true, squads: []}.
"""
import argparse
import json
import os
import sys
import time
import unicodedata
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

API = "https://api.hotutils.com/Production/"
APIUSERID = "898a36a3-948a-4a8a-9798-7a1552b042a8"
NAME_MAX = 16

# HotUtils category -> in-game tab name, in the order the tabs should appear.
# Fleet categories are deliberately absent: the API rejects combatType 2.
CATEGORY_TO_TAB = [("GAC 5v5 - Defense", "GAC 5v5 - Defense"),
                   ("GAC 5v5 - Offense", "GAC 5v5 - Offense"),
                   ("GAC 3v3 - Defense", "GAC 3v3 - Defense"),
                   ("GAC 3v3 - Offense", "GAC 3v3 - Offense"),
                   ("TW 5v5 - Defense", "TW 5v5 - Defense"),
                   ("TW 5v5 - Offense", "TW 5v5 - Offense")]

WALL_TAB = "TW 5v5 - Wall"


def api(path, body, sid, tries=4):
    payload = dict(body)
    payload["sessionId"] = sid
    data = json.dumps(payload).encode()
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(
                API + path, data=data,
                headers={"content-type": "application/json", "apiuserid": APIUSERID})
            with urllib.request.urlopen(req, timeout=120) as r:
                return json.load(r)
        except Exception as e:                     # noqa: BLE001 - retry anything transient
            last = e
            time.sleep(1.5 * (i + 1))
    raise RuntimeError(f"{path} failed: {last}")


def preset_name(payload_name):
    """'5v5 D01 The Stranger 57%' -> 'D01 The Strang' (<= NAME_MAX).

    Derived from the HotUtils name so the two surfaces cannot drift apart. The
    format tag and the percentage are dropped: the tab already says the format,
    and a percentage is noise on a button you tap mid-round.
    """
    parts = payload_name.split()
    slot, label = parts[1], " ".join(parts[2:-1])
    return f"{slot} {label}"[:NAME_MAX].rstrip()


def build():
    payload = json.load(open(os.path.join(ROOT, "output", "upload_payload.json")))
    by_cat = {}
    for p in payload:
        by_cat.setdefault(p["cat"], []).append(p)
    out = []
    for cat, tab in CATEGORY_TO_TAB:
        squads = [{"name": preset_name(p["n"]), "unitBaseIds": [u[0] for u in p["u"]]}
                  for p in by_cat.get(cat, [])]
        if squads:
            out.append({"tab": tab, "squads": squads})
    return out


def build_wall(limit=None):
    """The tw_wall.py overflow bank as its own tab, one tap per +30 banners.

    Kept out of CATEGORY_TO_TAB because it has a different provenance (see
    tw_wall.py) and a different life: it is rebuilt per war, not per season.
    """
    src = json.load(open(os.path.join(ROOT, "output", "tw_wall.json")))
    wall = src["wall"][:limit] if limit else src["wall"]
    squads = [{"name": ascii_name(f"W{i:02d} {s['lead_name']}"),
               "unitBaseIds": s["units"]}
              for i, s in enumerate(wall, 1)]
    return [{"tab": WALL_TAB, "squads": squads}] if squads else []


def ascii_name(s):
    """NAME_MAX is enforced on the server and the server is not known to be
    unicode-safe, so fold accents and drop quotes before truncating: 'Padme',
    not 'Padmé', and CC-2224 without the nickname quotes."""
    flat = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    return "".join(c for c in flat if c not in '"\'')[:NAME_MAX].rstrip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--push", action="store_true")
    ap.add_argument("--delete-tab", action="append", default=[],
                    help="tab NAME to remove (e.g. a stale duplicate)")
    ap.add_argument("--wall", action="store_true",
                    help="push output/tw_wall.json as the %r tab INSTEAD of the "
                         "season board (the board tabs are already in-game)" % WALL_TAB)
    ap.add_argument("--wall-limit", type=int, default=None)
    a = ap.parse_args()

    sid = os.environ.get("HU_SID")
    if not sid:
        sys.exit("set HU_SID to a live HotUtils session id")

    plan = build_wall(a.wall_limit) if a.wall else build()
    live = api("squads/game/get", {}, sid)
    by_name = {t["name"]: t for t in live.get("tabs", [])}
    print("live tabs: " + ", ".join(
        "{!r} ({} squads)".format(t["name"], len(t.get("squads") or []))
        for t in live.get("tabs", [])))

    over = [s["name"] for p in plan for s in p["squads"] if len(s["name"]) > NAME_MAX]
    if over:
        sys.exit(f"names over {NAME_MAX} chars: {over}")

    for p in plan:
        ex = by_name.get(p["tab"])
        verb = f"UPDATE id={ex['id']}" if ex else "CREATE (new tab)"
        print(f"\n{p['tab']}: {verb}  {len(p['squads'])} squads")
        for s in p["squads"][:3]:
            print(f"    {s['name']!r:18} {len(s['unitBaseIds'])} units")
        if len(p["squads"]) > 3:
            print(f"    ... +{len(p['squads']) - 3} more")
    for name in a.delete_tab:
        t = by_name.get(name)
        print(f"\nDELETE tab {name!r}: " + (f"id={t['id']} ({len(t['squads'])} squads)" if t else "NOT FOUND"))

    if a.dry_run or not a.push:
        print("\n(dry run — nothing sent)")
        return

    for p in plan:
        ex = by_name.get(p["tab"])
        tab = {"id": ex["id"] if ex else None, "name": p["tab"], "unique": True,
               "combatType": 1, "squads": p["squads"]}
        r = api("squads/game/set", {"tabs": [tab]}, sid)
        print(f"{p['tab']}: rc={r.get('responseCode')} {r.get('responseMessage')} "
              f"{r.get('errorMessage') or ''}")
        time.sleep(0.6)

    for name in a.delete_tab:
        t = by_name.get(name)
        if not t:
            continue
        r = api("squads/game/set", {"tabs": [{"id": t["id"], "name": name,
                                              "unique": t.get("unique", False),
                                              "combatType": 1, "void": True,
                                              "squads": []}]}, sid)
        print(f"delete {name!r}: rc={r.get('responseCode')} {r.get('responseMessage')}")
        time.sleep(0.6)


if __name__ == "__main__":
    main()
