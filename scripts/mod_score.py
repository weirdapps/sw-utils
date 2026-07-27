#!/usr/bin/env python3
"""
mod_score.py — read the grounded HotUtils account mod score + drivers (no browser).

HotUtils computes an account-wide quality score, returned in the auth/player/login
summary block: modScore (+ gearScore = totalScore). Plus the granular drivers that
move it: mod6Dot (total 6-dot), speed25/20/15/10 (mods with >= that much speed
secondary), plusSpeed (sum of all mod speed secondaries). player.currency carries
Micro Attenuators (id 41) and credits (id 1).

Use before AND after a mod session to report the delta. Prints one JSON line so callers
can diff two runs. Pass --refresh to force a fresh CG->HotUtils sync first.

Auth (ephemeral — never commit): HU_SID=<sessionId> [HU_UID=<apiuserid>] python3 scripts/mod_score.py [--refresh]
"""
import json, os, sys, time, urllib.request

API = "https://api.hotutils.com/Production/"
UID = os.environ.get("HU_UID", "898a36a3-948a-4a8a-9798-7a1552b042a8")
SID = os.environ.get("HU_SID", "")
ALLY = int(os.environ.get("HU_ALLY", "145357294"))
REFRESH = "--refresh" in sys.argv


def api(path, body):
    data = json.dumps({**body, "sessionId": SID}).encode()
    req = urllib.request.Request(API + path, data=data, method="POST", headers={
        "content-type": "application/json", "apiuserid": UID,
        "origin": "https://hotutils.com", "referer": "https://hotutils.com/"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read().decode())


def main():
    if not SID:
        sys.exit("ERROR: set HU_SID env var (see browser_recipes.md §4).")
    if REFRESH:
        r = api("account/refresh", {})
        print("# account/refresh:", r.get("responseMessage"),
              "gameDataAgeUtc:", r.get("player", {}).get("gameDataAgeUtc"))
        time.sleep(2)
    p = api("auth/player/login", {"allyCode": ALLY})
    s = p.get("summary", {})
    cur = {c["currency"]: c["quantity"] for c in p.get("player", {}).get("currency", [])}
    out = {
        "modScore": s.get("modScore"), "gearScore": s.get("gearScore"), "totalScore": s.get("totalScore"),
        "mod6Dot": s.get("mod6Dot"),
        "speed25": s.get("speed25"), "speed20": s.get("speed20"), "speed15": s.get("speed15"),
        "speed10": s.get("speed10"), "plusSpeed": s.get("plusSpeed"),
        "attenuators": cur.get(41), "credits": cur.get(1),
    }
    print(json.dumps(out))


if __name__ == "__main__":
    main()
