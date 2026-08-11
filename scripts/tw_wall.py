#!/usr/bin/env python3
"""
tw_wall.py — extend the Territory War defensive wall past the 15-squad graded bank.

WHY THIS EXISTS. build_board.py picks a TW defense bank out of swgoh.gg's
LINEUP table (/gac/squads/). That table is a top-100-by-usage list, so after the
best 15 walls and the 15 reserved attackers are carved out of it, only FOUR
unit-disjoint lineups remain — while 171 G13 characters sit idle. On a GAC board
that is correct (11 slots, and an idle unit is a reserve). In Territory War it is
pure waste: the map holds 390 defensive squads against a guild-wide, first-come
pool, there is no per-player cap, and **every squad that clears the territory's
6,000-power minimum banks a flat +30 banners** whatever it is made of.

So the wall has two tiers, and they use different grounded sources:

  TIER 1  leftover LINEUP-level walls  — swgoh.gg /gac/squads/ rows that survived
          the board solve. Same provenance as the main bank; simply the next ones
          down. Rare, but the best available.

  TIER 2  LEADER-level walls — swgoh.gg's defense tier list ranks 100 leaders by
          hold%, and 45 of them are idle here. A ranked leader plus its own
          faction is a real team, not a hand-pick: the leader order comes from
          the tier list and the four allies come from swgoh.gg's category tags,
          rarity-weighted so that a shared "Phoenix" (7 units) outranks a shared
          "Rebel" (52). Nothing in this file names a squad.

WHAT IT WILL NOT DO. The four attack-only Galactic Legends stay off the wall
(board_config.ATTACK_ONLY_GLS): a unit on TW defense cannot attack, and JMK is
worth more as an attacker than as a 2.7%-hold Kyber wall. Units already placed on
defense, and the 15 reserved TW offense squads, are locked out the same way.

Run:  python3 scripts/tw_wall.py [--target-banners 1000] [--placed 15]
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import board_config as cfg          # noqa: E402
import build_board as bb            # noqa: E402
import league_adjust as la          # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
OUT = os.path.join(ROOT, "output")

BANNERS_PER_SQUAD = 30    # "Set Defense: +30 Banners", read off the territory panel
POWER_MINIMUM = 6000      # "6000 Power Minimum", same panel

# Tags that are not a faction and so carry no squad synergy: a raid-eligibility
# list, a rarity class, and a ship-crew role.
NON_FACTION = {"Leader", "Order 66 Raid", "Galactic Legend", "Fleet Commander"}

SQUAD_SIZE = 5


def load_categories():
    """{baseId: {n, role, align, cats}} plus how rare each tag is."""
    src = json.load(open(os.path.join(DATA, "meta", "raw_unit_categories_20260805.json")))
    cmap = src["map"]
    size = {}
    for v in cmap.values():
        for c in v["cats"]:
            size[c] = size.get(c, 0) + 1
    return cmap, size


def load_leader_rates():
    """{baseId: {name, all, kd1, n}} for every leader ranked on 5v5 defense."""
    cmap, _ = load_categories()
    name2id = {v["n"]: b for b, v in cmap.items()}
    raw = json.load(open(os.path.join(DATA, "meta", "raw_tierlist_kyberd1_20260805.json")))
    if isinstance(raw, str):
        raw = json.loads(raw)
    kd1 = {r["leader"]: r for r in raw.get("d5_k1", []) if r.get("rate") is not None}
    out = {}
    for r in raw.get("d5", []):
        if r.get("rate") is None:
            continue
        bid = name2id.get(r["leader"])
        if not bid:
            continue
        k = kd1.get(r["leader"])
        out[bid] = {"name": r["leader"], "all": r["rate"], "battles": r.get("battles"),
                    "kd1": k["rate"] if k else None, "kd1_n": k["battles"] if k else None}
    return out


def affinity(lead_cats, ally_cats, size):
    """Rarity-weighted count of shared faction tags. 0 means 'no shared faction'."""
    shared = (set(lead_cats) & set(ally_cats)) - NON_FACTION
    return sum(1.0 / size.get(c, 1) for c in shared), shared


def build_wall(locked, chars, cmap, size, rates, ltable):
    """Greedy: best ranked idle leader first, each takes its four best faction-mates."""
    used = set(locked)
    squads = []
    order = sorted((b for b in rates if b not in used and b in chars),
                   key=lambda b: -rates[b]["all"])
    for lead in order:
        if lead in used:
            continue
        if "Leader" not in cmap.get(lead, {}).get("cats", []):
            continue
        lead_cats = cmap[lead]["cats"]
        scored = []
        for b, u in chars.items():
            if b in used or b == lead:
                continue
            aff, shared = affinity(lead_cats, cmap.get(b, {}).get("cats", []), size)
            if aff <= 0:
                continue                      # no shared faction => not a team
            scored.append((aff, u["gp"], b, shared))
        scored.sort(reverse=True)
        allies = scored[:SQUAD_SIZE - 1]
        if len(allies) < SQUAD_SIZE - 1:
            continue                          # cannot field a full squad: skip
        units = [lead] + [a[2] for a in allies]
        power = sum(chars[b]["gp"] for b in units)
        if power < POWER_MINIMUM:
            continue
        _, note = la.ratio(ltable, rates[lead]["name"], "5v5")
        squads.append({
            "lead": lead,
            "lead_name": rates[lead]["name"],
            "rate": rates[lead]["all"],
            "kd1": rates[lead]["kd1"],
            "battles": rates[lead]["battles"],
            "units": units,
            "names": [cmap.get(b, {}).get("n", b) for b in units],
            "power": power,
            "factions": sorted(set.intersection(*[set(a[3]) for a in allies]))
                        if allies else [],
            "source": "leader-tier-list",
            "note": note,
        })
        used.update(units)
    return squads, used


def leftover_lineups(locked, board, cmap):
    """TIER 1: lineup-level walls the board solve left on the table."""
    saved = cfg.MIN_SEEN
    cfg.MIN_SEEN = 0                 # bench tier: a thinner sample still banks +30
    try:
        pools = bb.load_pools()[4]
    finally:
        cfg.MIN_SEEN = saved
    used = set(locked)
    placed = {tuple(s["units"]) for s in board["tw"]["defense"]}
    out = []
    for s in sorted(bb.fieldable(pools[("5v5", "def")]),
                    key=lambda x: (-x["rate"], -x["seenN"])):
        if tuple(s["units"]) in placed or any(u in used for u in s["units"]):
            continue
        names = [cmap.get(b, {}).get("n", b) for b in s["units"]]
        out.append({"lead": s["units"][0], "lead_name": names[0], "rate": s["rate"],
                    "kd1": None, "battles": s["seen"], "units": s["units"],
                    "names": names, "source": "lineup-table", "note": s.get("discount")})
        used.update(s["units"])
    return out, used


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--target-banners", type=int, default=1000)
    ap.add_argument("--placed", type=int, default=None,
                    help="squads already on the map (default: len of the TW defense bank)")
    ap.add_argument("--roster", default=os.path.join(DATA, "roster",
                                                     "swgoh_roster_fresh_20260810.json"))
    args = ap.parse_args()

    roster = json.load(open(args.roster))
    chars = {u["b"]: u for u in roster["units"] if u["ct"] == 1 and u["g"] >= 13}
    board = json.load(open(os.path.join(DATA, "board_result.json")))
    placed = args.placed if args.placed is not None else len(board["tw"]["defense"])

    cmap, size = load_categories()
    rates = load_leader_rates()
    ltable = la.load().get(("5v5", "def"), {})

    # Locked: on the map already, reserved for the attack phase, or attack-only GL.
    locked = {u for s in board["tw"]["defense"] + board["tw"]["offense"] for u in s["units"]}
    locked |= set(cfg.ATTACK_ONLY_GLS)
    locked &= set(chars) | locked

    tier1, used = leftover_lineups(locked, board, cmap)
    tier2, used = build_wall(used, chars, cmap, size, rates, ltable)
    wall = tier1 + tier2

    have = placed * BANNERS_PER_SQUAD
    need = max(0, -(-(args.target_banners - have) // BANNERS_PER_SQUAD))

    print(f"on the map: {placed} squads = {have} banners · target {args.target_banners}")
    print(f"need {need} more squads; wall has {len(wall)} "
          f"({len(tier1)} lineup-table + {len(tier2)} leader-tier-list)\n")
    for i, s in enumerate(wall, 1):
        flag = "<<" if i == need else "  "
        kd = f" kyber {s['kd1']}%" if s.get("kd1") is not None else ""
        nm = s.get("names") or s["units"]
        print(f"W{i:02d} {flag} {s['rate']:5.1f}%{kd:14s} n={str(s['battles']):>7} "
              f"[{s['source'][:7]}] {', '.join(nm)}")
        if s.get("note"):
            print(f"        {s['note']}")

    idle = [b for b in chars if b not in used and b not in locked]
    total = (placed + len(wall)) * BANNERS_PER_SQUAD
    print(f"\nwall complete: {placed}+{len(wall)} squads = {total} banners")
    print(f"units still idle after the wall: {len(idle)}")

    os.makedirs(OUT, exist_ok=True)
    dst = os.path.join(OUT, "tw_wall.json")
    json.dump({"placed": placed, "need": need, "banners_per_squad": BANNERS_PER_SQUAD,
               "target": args.target_banners, "wall": wall, "idle_after": sorted(idle)},
              open(dst, "w"), indent=1)
    print(f"wrote {os.path.relpath(dst, ROOT)}")


if __name__ == "__main__":
    main()
