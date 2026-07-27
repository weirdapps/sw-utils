#!/usr/bin/env python3
"""
calibrate.py — calibrate 6A GAC mods toward Speed via the HotUtils API (no browser).

Calibration (6-dot only) rerolls a chosen secondary's value using Micro Attenuators
(summary.currency id 41, farmed in-game at Mod Battles Map 9). We target Speed (stat 5)
on 6A (6-dot tier-A) mods that carry a speed secondary with headroom, defense-first.

Each attempt: mods/reroll {modId, stat:5} -> preview .mod -> mods/acceptreroll {keepMod}.
We KEEP only if the previewed speed > current (so stats never regress); either way the
attempt spends attenuators (reverting does NOT refund). Cost escalates per-mod: 1st>=15,
2nd>=25, 3rd>=35... so spreading 1 attempt across never-calibrated (rr=0) mods is cheapest.
Self-stops on responseCode 2 / GOHServiceCall Error [40] (attenuators out).

Ranking: importance (DEF<off) -> most headroom (rolls*6 - spd) -> fewest prior rerolls -> most rolls.

Auth (ephemeral — never commit): HU_SID=<sessionId> [HU_UID] [HU_ALLY] python3 scripts/calibrate.py [--max N] [--min-headroom H] [--dry]
"""
import json, os, glob, sys, time, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
API = "https://api.hotutils.com/Production/"
UID = os.environ.get("HU_UID", "898a36a3-948a-4a8a-9798-7a1552b042a8")
SID = os.environ.get("HU_SID", "")
DRY = "--dry" in sys.argv


def arg(flag, default):
    return int(sys.argv[sys.argv.index(flag) + 1]) if flag in sys.argv else default


MAX = arg("--max", 4)
MIN_HR = arg("--min-headroom", 5)


def api(path, body):
    data = json.dumps({**body, "sessionId": SID}).encode()
    req = urllib.request.Request(API + path, data=data, method="POST", headers={
        "content-type": "application/json", "apiuserid": UID,
        "origin": "https://hotutils.com", "referer": "https://hotutils.com/"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode())


def spd_of(mod):
    for s in mod.get("secondaryStat", []):
        if s["stat"]["unitStatId"] == 5:
            return int(round(s["stat"]["statValueDecimal"] / 10000))
    return 0


def main():
    d = json.load(open(sorted(glob.glob(os.path.join(DATA, "mods_full_*.json")))[-1]))
    gac = json.load(open(os.path.join(DATA, "gac_result.json")))
    ros = json.load(open(sorted(glob.glob(os.path.join(DATA, "roster", "swgoh_roster_fresh_*.json")))[-1]))
    nm = {u["b"]: u["n"] for u in ros["units"]}
    defense, offense = set(), set()
    for f in ("5v5", "3v3"):
        for sq in gac[f]["defense"]: defense.update(sq["units"])
        for sq in gac[f]["offense"]: offense.update(sq["units"])

    cand = []
    for m in d["mods"]:
        if not m["b"] or m["dots"] != 6 or m["tier"] != 5: continue
        if m["b"] not in defense and m["b"] not in offense: continue
        if m["spd"] <= 0 or m["spdRolls"] <= 0: continue
        imp = 0 if m["b"] in defense else 1
        hr = m["spdRolls"] * 6 - m["spd"]
        if hr < MIN_HR: continue
        cand.append((imp, hr, m))
    # best order (grounded): defense first -> fewest prior rerolls (cheapest 1st attempts,
    # breadth-first per the slicing guide) -> most headroom -> most rolls.
    cand.sort(key=lambda t: (t[0], t[2]["rr"], -t[1], -t[2]["spdRolls"]))
    targets = cand[:MAX]

    print(f"=== CALIBRATE plan: top {len(targets)} of {len(cand)} eligible (min-headroom {MIN_HR}) ===")
    for imp, hr, m in targets:
        print(f"  [{'DEF' if imp==0 else 'off'}] {nm.get(m['b'],m['b'])[:26]:26} spd{m['spd']:>3} rolls{m['spdRolls']} headroom{hr:>3} rr{m['rr']}  {m['id']}")
    if DRY:
        print("\n[dry run — no API calls made]")
        return
    if not SID:
        sys.exit("\nERROR: set HU_SID env var to execute.")

    print("\n=== EXECUTING (keep only if speed improves) ===")
    kept = reverted = 0
    for imp, hr, m in targets:
        name = nm.get(m["b"], m["b"])
        r = api("mods/reroll", {"modId": m["id"], "stat": 5})
        rc = r.get("responseCode")
        preview = r.get("mod")
        if rc != 1 or not preview:
            print(f"  STOP {name}: rc={rc} {r.get('errorMessage') or r.get('responseMessage')}")
            break
        new = spd_of(preview)
        keep = new > m["spd"]
        api("mods/acceptreroll", {"keepMod": keep})
        if keep:
            kept += 1
            print(f"  KEPT   [{'DEF' if imp==0 else 'off'}] {name[:26]:26} spd {m['spd']} -> {new}  (+{new-m['spd']})")
        else:
            reverted += 1
            print(f"  revert [{'DEF' if imp==0 else 'off'}] {name[:26]:26} spd {m['spd']} -> {new}  (miss, kept {m['spd']})")
        time.sleep(0.5)
    print(f"\nDONE: kept {kept}, reverted {reverted} of {len(targets)} attempts.")


if __name__ == "__main__":
    main()
