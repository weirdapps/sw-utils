#!/usr/bin/env python3
"""
pull_gac.py: save HotUtils `gac/get` (both boards) to output/gac_current_<stamp>.json.

    python3 scripts/pull_gac.py            # refresh:true, the live board
    python3 scripts/pull_gac.py --cached   # refresh:false, whatever HotUtils last saw

Credentials come from $HU_SID / $HU_UID, else output/_hu_sid.json ({"sid", "uid"}),
which is gitignored. The uid is the APIUserId header the gac/* endpoints require
(browser_recipes.md §6); without it the API answers "Invalid API Request Header Values".

⚠ refresh:true logs HotUtils into the game account and KICKS the BlueStacks client
("Your session has expired"). Never run it while the farmbot or a battle is live.
⚠ The first pull after a round flips can still return the OLD match. Check
`currentRound` / `currentMatchId` in the printout and re-pull if they did not move.
"""
import argparse
import datetime
import json
import os
import sys
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
API = "https://api.hotutils.com/Production/"


def creds():
    sid, uid = os.environ.get("HU_SID"), os.environ.get("HU_UID")
    if sid and uid:
        return sid, uid
    path = os.path.join(ROOT, "output", "_hu_sid.json")
    if not os.path.exists(path):
        sys.exit("set HU_SID and HU_UID, or write output/_hu_sid.json")
    d = json.load(open(path))
    return d["sid"], d["uid"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cached", action="store_true", help="refresh:false (does not kick the client)")
    a = ap.parse_args()
    sid, uid = creds()
    body = {"refresh": not a.cached, "tournamentEventId": None, "currentMatchId": None,
            "sessionId": sid}
    req = urllib.request.Request(API + "gac/get", data=json.dumps(body).encode(),
                                 headers={"content-type": "application/json", "APIUserId": uid})
    with urllib.request.urlopen(req, timeout=120) as r:
        d = json.load(r)
    if d.get("responseCode") != 1:
        sys.exit(f"gac/get failed: {d.get('responseCode')} {d.get('responseMessage')}")
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M")
    out = os.path.join(ROOT, "output", f"gac_current_{stamp}.json")
    json.dump(d, open(out, "w"))
    g = d["gac"]
    print(f"saved {out}")
    print(f"map={g.get('tournamentMapId')} round={g.get('currentRound')} "
          f"match={g.get('currentMatchId')} opponent={g['away']['player'].get('name')}")
    for side in ("home", "away"):
        for z in g[side]["zones"]:
            print(f"  {side:4} {z['zoneId']:34} state={z.get('state')} "
                  f"squads={len(z.get('squads', []))}/{z['squadCapacity']} "
                  f"defeated={z.get('defeatedSquadCount', 0)} score={z.get('score')}")


if __name__ == "__main__":
    main()
