#!/usr/bin/env python3
"""scout.py — A2 GAC opponent scouting.

Given an opponent's ally code, pull their roster (live comlink) and report which
top meta DEFENSE teams they can field (own every unit at G13+) — i.e. the walls
to expect. Run per GAC round once matchmaking assigns the opponent.

Usage:  COMLINK_URL=http://localhost:3999 .venv/bin/python scripts/scout.py <ally> [5v5|3v3]
"""
import glob
import os
import sys

import swgoh_data
import swgoh_meta

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
META = os.path.join(ROOT, "data", "meta")
_DEF_GLOB = {"5v5": "*5v5*def*.json", "3v3": "*def*3v3*.txt"}


def owned_g13_set(roster):
    """baseIds the player owns as G13+ characters (mirrors compute_teams' rule)."""
    return {u["b"] for u in roster.get("units", [])
            if u.get("ct") == 1 and (u.get("g") or 0) >= 13}


def fieldable_defenses(opponent_owned_g13, meta_def):
    """Meta defense teams the opponent can field (owns all units), Hold%-desc."""
    ownable = [t for t in meta_def
               if all(u in opponent_owned_g13 for u in t.get("units", []))]
    return sorted(ownable, key=lambda t: (-t["rate"], -t.get("seenN", 0)))


def _load_meta_def(fmt):
    hits = sorted(glob.glob(os.path.join(META, _DEF_GLOB[fmt])))
    if not hits:
        return []
    path = hits[-1]
    return swgoh_meta.parse_json_def(path) if path.endswith(".json") else swgoh_meta.parse_txt(path)


def scout_opponent(opp_ally, fmt="5v5", url=None):
    roster = swgoh_data.get_roster(opp_ally, url=url)
    walls = fieldable_defenses(owned_g13_set(roster), _load_meta_def(fmt))
    return {"opponent": roster["meta"].get("name"), "fmt": fmt, "walls": walls}


def main():
    if len(sys.argv) < 2:
        print("usage: scout.py <ally_code> [5v5|3v3]")
        return
    ally = sys.argv[1]
    fmt = sys.argv[2] if len(sys.argv) > 2 else "5v5"
    res = scout_opponent(ally, fmt)
    nm = swgoh_data.load_name_type_map()
    name = lambda b: nm.get(b, {}).get("n", b)  # noqa: E731
    print(f"Opponent {res['opponent']} — {fmt} defenses they can field (top walls to expect):\n")
    for t in res["walls"][:15]:
        print(f"  {t['rate']}% hold  {name(t['units'][0])}  ({', '.join(name(u) for u in t['units'])})")


if __name__ == "__main__":
    main()
