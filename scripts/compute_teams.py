#!/usr/bin/env python3
"""
compute_teams.py — grounded GAC team builder.

Reads a roster pull + swgoh.gg meta snapshots, then for each format (5v5, 3v3):
  1. reserves the pure-attack GLs for offense (so defense doesn't strand their support),
  2. fills DEFENSE first by swgoh.gg Hold% (owned, G13+, no unit repeats within the format),
  3. builds the OFFENSE bank by Win% from the remaining units,
  4. records gaps (top meta teams you cannot field).

Output: data/gac_result.json  (consumed by generate_hotutils.py)

Board counts + reserve list are CONFIG below — update when your league/board changes.
Everything is data-driven; no hardcoded teams.
"""
import json, os, shutil
import swgoh_data
import swgoh_meta
from datetime import datetime
try:
    from zoneinfo import ZoneInfo
    _TODAY = datetime.now(ZoneInfo("Europe/Athens")).strftime("%Y-%m-%d")
except Exception:
    _TODAY = datetime.now().strftime("%Y-%m-%d")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
META = os.path.join(DATA, "meta")

# ---- CONFIG (update per league/board; read live from HotUtils GAC Planning) ----
BOARD = {"5v5": {"def": 11, "off": 16}, "3v3": {"def": 15, "off": 18}}
# Pure attack GLs: reserved for offense before defense claims units (weak defenders anyway).
RESERVE = ["JEDIMASTERKENOBI", "GRANDMASTERLUKE", "SITHPALPATINE", "SUPREMELEADERKYLOREN"]
ROSTER_FILE = os.path.join(DATA, "roster", "swgoh_roster_fresh_20260731.json")
ALLYCODE = "145357294"  # Astra — live roster via comlink; ROSTER_FILE = offline fallback
# meta files: (format, perspective) -> filename in data/meta/
META_FILES = {
    ("5v5", "def"): "meta_5v5_defense_s80.json",   # JSON (rows[].hold/units) from swgoh.gg
    ("5v5", "off"): "meta_off5v5.txt",             # "rate%|seen|banners|CSVunits" per line
    ("3v3", "def"): "meta_def3v3.txt",
    ("3v3", "off"): "meta_off3v3.txt",
}

# ---- roster (live comlink via swgoh_data; falls back to ROSTER_FILE if comlink is down) ----
r = swgoh_data.load_roster(ALLYCODE, fallback_file=ROSTER_FILE)
print(f"roster source: {r.get('meta', {}).get('source', '?')}  units={len(r['units'])}")
units = r["units"]
# names: full unit map (resolves UNOWNED gap units) overlaid with current roster names
name = {b: v["n"] for b, v in swgoh_data.load_name_type_map().items()}
name.update({u["b"]: u["n"] for u in units})
owned_g13 = {u["b"] for u in units if u["ct"] == 1 and u["g"] >= 13}


meta = swgoh_meta.load_meta(META_FILES, META)


def fieldable(sq):
    return all(b in owned_g13 for b in sq["units"])


def missing(sq):
    return [b for b in sq["units"] if b not in owned_g13]


result = {}
for fmt in ("5v5", "3v3"):
    used = set()
    off = []
    # 1) reserve pure-attack GLs for offense
    for lead in RESERVE:
        cands = [s for s in meta[(fmt, "off")] if s["units"][0] == lead and fieldable(s)
                 and not any(b in used for b in s["units"])]
        if cands:
            best = max(cands, key=lambda x: (x["rate"], x["seenN"]))
            off.append(best); used.update(best["units"])
    # 2) defense-first by Hold%
    dfn = []
    for sq in sorted(meta[(fmt, "def")], key=lambda x: (-x["rate"], -x["seenN"])):
        if len(dfn) >= BOARD[fmt]["def"]:
            break
        if fieldable(sq) and not any(b in used for b in sq["units"]):
            dfn.append(sq); used.update(sq["units"])
    # 3) fill offense by Win%
    for sq in sorted(meta[(fmt, "off")], key=lambda x: (-x["rate"], -x["seenN"])):
        if len(off) >= BOARD[fmt]["off"]:
            break
        if fieldable(sq) and not any(b in used for b in sq["units"]):
            off.append(sq); used.update(sq["units"])
    off.sort(key=lambda x: (-x["rate"], -x["seenN"]))
    # 4) gaps
    gaps = {}
    for persp in ("def", "off"):
        g = []
        for sq in sorted(meta[(fmt, persp)], key=lambda x: (-x["rate"], -x["seenN"])):
            miss = missing(sq)
            if miss:
                g.append({"rate": sq["rate"], "leader": name.get(sq["units"][0], sq["units"][0]),
                          "missing": [name.get(b, b) for b in miss]})
        gaps[persp] = g[:8]
    result[fmt] = {"defense": dfn, "offense": off, "gaps": gaps,
                   "unique_units": len(used)}

out_path = os.path.join(DATA, "gac_result.json")
json.dump(result, open(out_path, "w"), indent=1)

# archive this run so delta_check.py can compare seasons
hist_dir = os.path.join(DATA, "history", _TODAY)
os.makedirs(hist_dir, exist_ok=True)
shutil.copy(out_path, os.path.join(hist_dir, "gac_result.json"))

for fmt in ("5v5", "3v3"):
    print(f"{fmt}: defense {len(result[fmt]['defense'])}/{BOARD[fmt]['def']}  "
          f"offense {len(result[fmt]['offense'])}  unique units {result[fmt]['unique_units']}")
print(f"wrote data/gac_result.json  (archived to data/history/{_TODAY}/)")
