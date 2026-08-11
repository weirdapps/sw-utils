#!/usr/bin/env python3
"""
calibrate.py — calibrate 6A GAC mods toward Speed via the HotUtils API (no browser).

Calibration (6-dot only) rerolls a chosen secondary's value using Micro Attenuators
(summary.currency id 41, farmed in-game at Mod Battles Map 9). We target Speed (stat 5)
on 6A (6-dot tier-A) mods whose speed secondary rolled BELOW expectation, highest priority first.

Each attempt: mods/reroll {modId, stat:5} -> preview .mod -> mods/acceptreroll {keepMod}.
We KEEP only if the previewed speed > current (so stats never regress); either way the
attempt spends attenuators (reverting does NOT refund). Cost escalates per-mod: 1st>=15,
2nd>=25, 3rd>=35... so spreading 1 attempt across never-calibrated (rr=0) mods is cheapest.
Self-stops on responseCode 2 / GOHServiceCall Error [40] (attenuators out).

⚠️ TARGET THE UNLUCKY MOD, NOT THE GOOD ONE (measured 2026-08-11, after 0 hits in 18 attempts).
A reroll RE-SAMPLES the secondary, so it regresses to the mean: the expected speed of a mod is
about ROLL_MEAN per roll, and rerolling a mod already above that expectation loses on average.
The old metric, headroom = rolls*6 - spd, measured distance from the MAXIMUM, which selects
high-roll mods — and a high-roll mod is usually an already-lucky one. Every one of the 7 mods
rerolled on 2026-08-11 sat at or above expectation, and all 7 came back lower (23->20, 24->19,
25->21, 19->14, 23->18, 18->12, 24->18). The metric that matters is the DEFICIT below expectation,
and only 9 of this account's 76 eligible 6A mods have one.

Ranking: ladder rank -> fewest prior rerolls -> biggest deficit (rolls*ROLL_MEAN - spd) -> most rolls.
Importance is invest_plan.py's `mod_priority` (Arena -> GAC -> TB -> TW -> fleets), the same
ordering execute_upgrades.py uses. It previously came from gac_result.json alone, which left
the Squad/Fleet Arena units — the ones paying a ranked reward EVERY day, and the top of the
stated ladder — completely ineligible for calibration.

Auth (ephemeral — never commit): HU_SID=<sessionId> [HU_UID] [HU_ALLY] python3 scripts/calibrate.py [--max N] [--min-deficit D] [--dry]
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
# A 6-dot speed roll lands in 3..6, so an unbiased mod averages 4.5 per roll. A mod is only
# worth rerolling when it sits BELOW that line; the default of 1 keeps the sweep to mods that
# are at least a full point unlucky. Raise it to be stricter, or pass 0 to include break-evens.
ROLL_MEAN = 4.5
MIN_DEFICIT = arg("--min-deficit", 1)


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
    ip = json.load(open(os.path.join(ROOT, "output", "invest_plan.json")))
    rank = {b: i for i, b in enumerate(ip["mod_priority"])}
    nm = {e["unit"]: e["name"] for e in ip["priority"]}

    cand = []
    for m in d["mods"]:
        if not m["b"] or m["dots"] != 6 or m["tier"] != 5: continue
        if m["b"] not in rank: continue
        if m["spd"] <= 0 or m["spdRolls"] <= 0: continue
        deficit = m["spdRolls"] * ROLL_MEAN - m["spd"]
        if deficit < MIN_DEFICIT: continue
        cand.append((rank[m["b"]], deficit, m))
    # best order (grounded): ladder rank -> fewest prior rerolls (a 1st attempt costs 15
    # attenuators and a 3rd costs 35, so breadth beats depth) -> biggest deficit -> most rolls.
    cand.sort(key=lambda t: (t[0], t[2]["rr"], -t[1], -t[2]["spdRolls"]))
    targets = cand[:MAX]

    print(f"=== CALIBRATE plan: top {len(targets)} of {len(cand)} eligible (min-deficit {MIN_DEFICIT}) ===")
    for r, deficit, m in targets:
        print(f"  r{r:<4}{nm.get(m['b'],m['b'])[:26]:26} spd{m['spd']:>3} rolls{m['spdRolls']} "
              f"deficit{deficit:>5.1f} rr{m['rr']}  {m['id']}")
    if DRY:
        print("\n[dry run — no API calls made]")
        return
    if not SID:
        sys.exit("\nERROR: set HU_SID env var to execute.")

    print("\n=== EXECUTING (keep only if speed improves) ===")
    kept = reverted = 0
    for rk, _deficit, m in targets:
        name = nm.get(m["b"], m["b"])
        resp = api("mods/reroll", {"modId": m["id"], "stat": 5})
        rc = resp.get("responseCode")
        preview = resp.get("mod")
        if rc != 1 or not preview:
            print(f"  STOP {name}: rc={rc} {resp.get('errorMessage') or resp.get('responseMessage')}")
            break
        new = spd_of(preview)
        keep = new > m["spd"]
        api("mods/acceptreroll", {"keepMod": keep})
        if keep:
            kept += 1
            print(f"  KEPT   r{rk:<4}{name[:26]:26} spd {m['spd']} -> {new}  (+{new-m['spd']})")
        else:
            reverted += 1
            print(f"  revert r{rk:<4}{name[:26]:26} spd {m['spd']} -> {new}  (miss, kept {m['spd']})")
        time.sleep(0.5)
    print(f"\nDONE: kept {kept}, reverted {reverted} of {len(targets)} attempts.")


if __name__ == "__main__":
    main()
