#!/usr/bin/env python3
"""swgoh_meta.py — parse swgoh.gg GAC meta snapshots.

Shared by compute_teams.py (board builder) and scout.py (opponent scouting) so
the meta-file parsing lives in one place. Meta files live in data/meta/:
  - *.json  : swgoh.gg 5v5 defense export ({rows:[{hold,seen,banners,units}]})
  - *.txt   : "rate%|seen|banners|CSV,of,baseIds" per line
"""
import json
import os
import re


def seen_num(s):
    """Normalize a '12.3K' / '1.2M' seen count to a float for sorting."""
    s = str(s).replace(",", "").strip()
    m = re.match(r"([\d.]+)([KM]?)", s)
    if not m:
        return 0
    v = float(m.group(1))
    return v * 1e6 if m.group(2) == "M" else v * 1e3 if m.group(2) == "K" else v


def parse_txt(path):
    out = []
    for line in open(path):
        line = line.strip()
        if not line or line.startswith("ROWS="):
            continue
        rate, seen, ban, csv = line.split("|")
        out.append({"rate": int(rate.replace("%", "")), "seen": seen, "seenN": seen_num(seen),
                    "ban": float(ban), "units": csv.split(",")})
    return out


def parse_json_def(path):
    d = json.load(open(path))
    return [{"rate": int(x["hold"].replace("%", "")), "seen": x["seen"], "seenN": seen_num(x["seen"]),
             "ban": float(x["banners"]), "units": x["units"]} for x in d["rows"]]


def load_meta(meta_files, meta_dir):
    """meta_files: {(fmt, persp): filename}. Returns {(fmt, persp): [team, ...]}."""
    meta = {}
    for key, fn in meta_files.items():
        p = os.path.join(meta_dir, fn)
        meta[key] = parse_json_def(p) if fn.endswith(".json") else parse_txt(p)
    return meta
