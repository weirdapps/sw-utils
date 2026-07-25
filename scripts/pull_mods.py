#!/usr/bin/env python3
"""
pull_mods.py — pull live mods + materials from HotUtils into the pipeline schema (no browser).

Calls account/refresh (forces a fresh CG->HotUtils sync, i.e. "Fetch my data") then
account/data/all, and writes data/mods_full_<YYYYMMDD>.json = {gameDataAgeUtc, pulledCount,
mats{...}, mods[{id,b,dots,tier,lvl,set,slot,spd,spdRolls,spdArrow,rr}]}.

Auth (ephemeral — never commit): HU_SID=<sessionId> [HU_UID=<apiuserid>] python3 scripts/pull_mods.py
Capture HU_SID from a live api.hotutils.com XHR (browser_recipes.md §4) — it rotates each session.
"""
import json, os, sys, time, datetime, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
API = "https://api.hotutils.com/Production/"
UID = os.environ.get("HU_UID", "898a36a3-948a-4a8a-9798-7a1552b042a8")
SID = os.environ.get("HU_SID", "")
NO_REFRESH = "--no-refresh" in sys.argv

MAT_MAP = {
    "T05_01": "MOD_SLICING_SALVAGE_TIER05_01", "T05_02": "MOD_SLICING_SALVAGE_TIER05_02",
    "T05_03": "MOD_SLICING_SALVAGE_TIER05_03", "T05_04": "MOD_SLICING_SALVAGE_TIER05_04",
    "T05_05": "MOD_SLICING_SALVAGE_TIER05_05", "T05_06": "MOD_SLICING_SALVAGE_TIER05_06",
    "PROMO_T5_T6": "MOD_SLICING_PROMOTION_MATERIAL_T5_TO_T6",
    "T06_01": "MOD_SLICING_SALVAGE_TIER06_01", "T06_02": "MOD_SLICING_SALVAGE_TIER06_02",
    "T06_03": "MOD_SLICING_SALVAGE_TIER06_03", "T06_04": "MOD_SLICING_SALVAGE_TIER06_04",
}


def api(path, body):
    data = json.dumps({**body, "sessionId": SID}).encode()
    req = urllib.request.Request(API + path, data=data, method="POST", headers={
        "content-type": "application/json", "apiuserid": UID,
        "origin": "https://hotutils.com", "referer": "https://hotutils.com/"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read().decode())


def spd(m):
    for s in m.get("secondaryStat", []):
        if s["stat"]["unitStatId"] == 5:
            return int(round(s["stat"]["statValueDecimal"] / 10000)), s["statRolls"]
    return 0, 0


def main():
    if not SID:
        sys.exit("ERROR: set HU_SID env var (see browser_recipes.md §4).")
    r = {}
    if not NO_REFRESH:
        r = api("account/refresh", {})
        print("account/refresh:", r.get("responseMessage"),
              "| gameDataAgeUtc:", r.get("player", {}).get("gameDataAgeUtc"))
        time.sleep(2)
    d = api("account/data/all", {})
    dd = d["data"]
    mats_raw = {m["id"]: m["quantity"] for m in dd["material"]["material"]}
    cur = {c["currency"]: c["quantity"] for c in dd["summary"]["currency"]}
    mats = {k: mats_raw.get(v, 0) for k, v in MAT_MAP.items()}
    mats["credits"] = cur.get(1, 0)
    mats["attenuators"] = cur.get(41, 0)
    mods = []
    for m in dd["mods"]["mods"]:
        sv, sr = spd(m)
        mods.append({
            "id": m["id"], "b": (m["unit"]["baseId"] if m.get("unit") else None),
            "dots": m["rarity"], "tier": m["tier"], "lvl": m["level"],
            "set": str(m["setId"]), "slot": m["slot"], "spd": sv, "spdRolls": sr,
            "spdArrow": m.get("primaryStat", {}).get("stat", {}).get("unitStatId") == 5,
            "rr": m.get("rerolledCount", 0),
        })
    date = datetime.datetime.now().strftime("%Y%m%d")
    out = {"gameDataAgeUtc": r.get("player", {}).get("gameDataAgeUtc") if not NO_REFRESH else None,
           "pulledCount": len(mods), "mats": mats, "mods": mods}
    fn = os.path.join(DATA, f"mods_full_{date}.json")
    json.dump(out, open(fn, "w"))
    sixA = sum(1 for m in mods if m["dots"] == 6 and m["tier"] == 5)
    print(f"wrote {os.path.relpath(fn, ROOT)} | {len(mods)} mods | 6A={sixA} 6dot={sum(1 for m in mods if m['dots']==6)}")
    print("mats:", {k: mats[k] for k in ("T06_02", "T05_06", "T05_03", "T05_04", "PROMO_T5_T6", "attenuators")})


if __name__ == "__main__":
    main()
