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


def latest_season_file(meta_dir, prefix, fallback=None):
    """Newest `<prefix>_s<N>.txt` in meta_dir, by the SEASON NUMBER in the name.

    The same trap latest_roster_file() closes for rosters, which this repo had
    already been bitten by once: build_board.py pinned "meta_def5v5_s80.txt" by
    hand, so a fresh S82 scrape landed in data/meta/ and was silently ignored
    while the board kept planning against a two-season-old meta.

    Sort on the season number, never on mtime — re-saving an old season must not
    make it look current. Returns `fallback` when nothing matches, so a caller
    can keep an undated legacy file working.
    """
    best = None
    pat = re.compile(re.escape(prefix) + r"_s(\d+)\.txt$")
    for fn in os.listdir(meta_dir):
        m = pat.match(fn)
        if m and (best is None or int(m.group(1)) > best[0]):
            best = (int(m.group(1)), fn)
    return best[1] if best else fallback


def load_meta(meta_files, meta_dir):
    """meta_files: {(fmt, persp): filename}. Returns {(fmt, persp): [team, ...]}."""
    meta = {}
    for key, fn in meta_files.items():
        p = os.path.join(meta_dir, fn)
        meta[key] = parse_json_def(p) if fn.endswith(".json") else parse_txt(p)
    return meta
