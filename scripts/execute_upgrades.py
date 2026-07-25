#!/usr/bin/env python3
"""
execute_upgrades.py — slice/promote equipped mods via the HotUtils API (no browser).

Reusable executor for the mod-upgrade pipeline. Reads the latest
data/mods_full_<date>.json (+ gac_result.json + roster) and drives the
HotUtils mods/tier endpoint one mod at a time, defense-first by speed, until
each binding material is exhausted or the plan is complete.

Auth (ephemeral — never commit): pass the live session id via env:
    HU_SID=<sessionId>  [HU_UID=<apiuserid>]  python3 scripts/execute_upgrades.py [--dry]

Plan policy (GAC value, material-efficient):
  - SLICE already-6-dot defense mods (speed desc) fully to 6A while T06_02 allows a full finish;
    then spill remaining T06_02 onto closest-to-6A offense mods (steps asc, speed desc).
  - PROMOTE defense 5A mods (speed desc) 5A->6E while T05_06 & PROMO allow.
  - Never touches filler (non-squad) chars. Never calibrates (attenuators saved).

Material recipe (per one tier-step, from live diffs in memory/notes.md):
  6-dot slice step  -> ~20x T06_02 (binding)
  5A->6E promote    -> ~50x T05_06 (binding) + ~20x PROMO_T5_T6
Sizing keeps spend under a safety margin; every call also checks responseCode and
stops cleanly on GOHServiceCall Error [40] (material out).
"""
import json, os, glob, sys, time, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
API = "https://api.hotutils.com/Production/"
UID = os.environ.get("HU_UID", "898a36a3-948a-4a8a-9798-7a1552b042a8")
SID = os.environ.get("HU_SID", "")
DRY = "--dry" in sys.argv

STEP6_T0602 = 20      # T06_02 per 6-dot tier-step (binding)
PROMO_T0506 = 50      # T05_06 per 5A->6E promote (binding)
PROMO_PROMO = 20      # PROMO_T5_T6 per promote
MARGIN = 0.90         # only plan up to 90% of a binding material


def api(path, body):
    data = json.dumps({**body, "sessionId": SID}).encode()
    req = urllib.request.Request(API + path, data=data, method="POST", headers={
        "content-type": "application/json", "apiuserid": UID,
        "origin": "https://hotutils.com", "referer": "https://hotutils.com/"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode())


def load():
    d = json.load(open(sorted(glob.glob(os.path.join(DATA, "mods_full_*.json")))[-1]))
    gac = json.load(open(os.path.join(DATA, "gac_result.json")))
    ros = json.load(open(sorted(glob.glob(os.path.join(DATA, "roster", "swgoh_roster_fresh_*.json")))[-1]))
    nm = {u["b"]: u["n"] for u in ros["units"]}
    defense, offense = set(), set()
    for f in ("5v5", "3v3"):
        for sq in gac[f]["defense"]:
            defense.update(sq["units"])
        for sq in gac[f]["offense"]:
            offense.update(sq["units"])
    return d, nm, defense, offense


def build_plan(d, nm, defense, offense):
    mats = d["mats"]
    mods = [m for m in d["mods"] if m["b"]]
    for m in mods:
        m["imp"] = 0 if m["b"] in defense else (1 if m["b"] in offense else 2)
        m["name"] = nm.get(m["b"], m["b"])

    # --- SLICE plan (T06_02) ---
    t0602_budget = int(mats["T06_02"] * MARGIN)
    slice_plan, spent6 = [], 0
    # defense 6-dot not-6A, speed desc: finish fully to 6A
    dfn = sorted([m for m in mods if m["imp"] == 0 and m["dots"] == 6 and m["tier"] < 5],
                 key=lambda m: (-m["spd"], -m["tier"]))
    for m in dfn:
        steps = 5 - m["tier"]
        if spent6 + steps * STEP6_T0602 <= t0602_budget:
            spent6 += steps * STEP6_T0602
            slice_plan.append((m, steps))
    # offense 6-dot not-6A, closest first, to fill remaining budget
    off = sorted([m for m in mods if m["imp"] == 1 and m["dots"] == 6 and m["tier"] < 5],
                 key=lambda m: (5 - m["tier"], -m["spd"]))
    for m in off:
        steps = 5 - m["tier"]
        if spent6 + steps * STEP6_T0602 <= t0602_budget:
            spent6 += steps * STEP6_T0602
            slice_plan.append((m, steps))

    # --- PROMOTE plan (T05_06 + PROMO) ---
    cap = min(int(mats["T05_06"] * MARGIN) // PROMO_T0506, mats["PROMO_T5_T6"] // PROMO_PROMO)
    da = sorted([m for m in mods if m["imp"] == 0 and m["dots"] == 5 and m["tier"] == 5],
                key=lambda m: -m["spd"])
    promote_plan = da[:cap]
    return mats, slice_plan, promote_plan, spent6, len(promote_plan) * PROMO_T0506


def main():
    d, nm, defense, offense = load()
    mats, slice_plan, promote_plan, spent6, spent506 = build_plan(d, nm, defense, offense)
    role = lambda m: "DEF" if m["imp"] == 0 else "off"

    print("=== MATERIALS ===")
    print(f"T06_02={mats['T06_02']}  T05_06={mats['T05_06']}  PROMO={mats['PROMO_T5_T6']}  "
          f"credits={mats['credits']:,}  attenuators={mats.get('attenuators')}")
    print(f"\n=== SLICE -> 6A  ({len(slice_plan)} mods, ~{spent6} T06_02) ===")
    for m, s in slice_plan:
        print(f"  [{role(m)}] {m['name']:28} spd{m['spd']:>3} {m['dots']}dot t{m['tier']}->6A ({s} steps)  {m['id']}")
    print(f"\n=== PROMOTE 5A->6E  ({len(promote_plan)} mods, ~{spent506} T05_06) ===")
    for m in promote_plan:
        print(f"  [{role(m)}] {m['name']:28} spd{m['spd']:>3} 5A->6E  {m['id']}")
    proj = sum(1 for m in d["mods"] if m["dots"] == 6 and m["tier"] == 5) + len(slice_plan)
    print(f"\nProjected 6A: {sum(1 for m in d['mods'] if m['dots']==6 and m['tier']==5)} -> {proj}")

    if DRY:
        print("\n[dry run — no API calls made]")
        return
    if not SID:
        print("\nERROR: set HU_SID env var to the live sessionId to execute.")
        sys.exit(1)

    print("\n=== EXECUTING ===")
    done6 = done_pr = 0
    # slice: one mod at a time, one tier per call
    for m, steps in slice_plan:
        ok = True
        for i in range(steps):
            r = api("mods/tier", {"modIds": [m["id"]], "getAllData": False})
            rc = r.get("responseCode")
            if rc != 1:
                print(f"  STOP slice {m['name']} step {i+1}/{steps}: rc={rc} {r.get('errorMessage') or r.get('responseMessage')}")
                ok = False
                break
            time.sleep(0.4)
        if ok:
            done6 += 1
            print(f"  sliced->6A  [{role(m)}] {m['name']} ({steps} steps)")
    # promote: one mod at a time
    for m in promote_plan:
        r = api("mods/tier", {"modIds": [m["id"]], "getAllData": False})
        rc = r.get("responseCode")
        if rc != 1:
            print(f"  STOP promote {m['name']}: rc={rc} {r.get('errorMessage') or r.get('responseMessage')}")
            break
        done_pr += 1
        print(f"  promoted->6E  [{role(m)}] {m['name']}")
        time.sleep(0.4)
    print(f"\nDONE: sliced {done6}/{len(slice_plan)} to 6A, promoted {done_pr}/{len(promote_plan)} to 6E")


if __name__ == "__main__":
    main()
