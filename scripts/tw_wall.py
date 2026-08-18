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

WHAT IT WILL NOT DO. The attack-only Galactic Legends stay off the wall
(board_config.ATTACK_ONLY_BY_FORMAT["5v5"]): a unit on TW defense cannot attack,
and JMK is worth more as an attacker than as a 2.7%-hold Kyber wall. Units already
placed on defense, and the reserved TW offense squads, are locked out the same way.

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
import swgoh_data                   # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
OUT = os.path.join(ROOT, "output")

BANNERS_PER_SQUAD = 30    # "Set Defense: +30 Banners", read off the territory panel
FLEET_BANNERS = 34        # Airspace: "Set Defensive Fleet (+34 Banners per Fleet)"
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


def leader_candidates(used, chars, cmap, rates):
    """Idle leaders to try, best-evidenced first.

    TIER 2 is every leader swgoh.gg ranks on 5v5 defense, by hold%.
    TIER 3 is the rest of the idle "Leader"-tagged roster by GP — no hold number
    exists for them, so they are ordered by raw strength and used only as BACK-
    line filler. A filler wall still banks the same flat +30 and still costs the
    attacker a squad, but it must never take a front-line slot (see notes.md).
    """
    ranked = sorted((b for b in rates if b not in used and b in chars),
                    key=lambda b: -rates[b]["all"])
    out = [(b, rates[b]["name"], rates[b]["all"], rates[b]["kd1"],
            rates[b]["battles"], "leader-tier-list") for b in ranked]
    rest = [b for b in chars
            if b not in used and b not in rates
            and "Leader" in cmap.get(b, {}).get("cats", [])]
    rest.sort(key=lambda b: -swgoh_data.unit_power(chars[b]))
    out += [(b, cmap.get(b, {}).get("n", b), None, None, None, "unranked-leader")
            for b in rest]
    return out


def build_wall(locked, chars, cmap, size, rates, ltable):
    """Greedy: best idle leader first, each takes its four best faction-mates."""
    used = set(locked)
    squads = []
    for lead, lead_name, rate, kd1, battles, source in leader_candidates(
            used, chars, cmap, rates):
        if lead in used:
            continue
        lead_cats = cmap[lead]["cats"]
        scored = []
        for b, u in chars.items():
            if b in used or b == lead:
                continue
            aff, shared = affinity(lead_cats, cmap.get(b, {}).get("cats", []), size)
            if aff <= 0:
                continue                      # no shared faction => not a team
            scored.append((aff, swgoh_data.unit_power(u), b, shared))
        scored.sort(reverse=True)
        allies = scored[:SQUAD_SIZE - 1]
        if len(allies) < SQUAD_SIZE - 1:
            continue                          # cannot field a full squad: skip
        units = [lead] + [a[2] for a in allies]
        power = sum(swgoh_data.unit_power(chars[b]) for b in units)
        if power < POWER_MINIMUM:
            continue
        _, note = la.ratio(ltable, lead_name, "5v5")
        squads.append({
            "lead": lead,
            "lead_name": lead_name,
            "rate": rate,
            "kd1": kd1,
            "battles": battles,
            "units": units,
            "names": [cmap.get(b, {}).get("n", b) for b in units],
            "power": power,
            "factions": sorted(set.intersection(*[set(a[3]) for a in allies]))
                        if allies else [],
            "source": source,
            "note": note,
        })
        used.update(units)
    return squads, used


def filler_squads(used, chars, cmap, locked, limit):
    """TIER 4: the bodies no other tier can use, five at a time, strongest first.

    Tiers 1-3 all need a LEADER — a ranked lineup, a tier-list leader, or at least a
    unit carrying the "Leader" tag with four faction-mates. After they run, ~28 G13
    characters are left that satisfy none of those and would otherwise idle.

    They are still worth setting, and the reason is the flat rate: "Set Defense:
    +30 Banners" does not read the squad. Five idle G13 bodies clear the 6,000-power
    minimum roughly 25x over, bank the same +30 as a 28% wall, and still cost the
    attacker a battle they must win to take the territory.

    ⚠ BACK-LINE ONLY, and this is the rule the 2026-08-11 war broke at a cost. The
    39-slot territory cap is GUILD-WIDE and first-come, so a filler squad in a FRONT
    territory is a slot no guildmate can spend on a real wall. These sort last in the
    placement order for exactly that reason — see notes.md "TW PLACEMENT DOCTRINE".
    """
    idle = sorted((b for b in chars if b not in used and b not in locked),
                  key=lambda b: -swgoh_data.unit_power(chars[b]))
    out = []
    for i in range(0, len(idle) - SQUAD_SIZE + 1, SQUAD_SIZE):
        if len(out) >= limit:
            break
        units = idle[i:i + SQUAD_SIZE]
        names = [cmap.get(b, {}).get("n", b) for b in units]
        out.append({"lead": units[0], "lead_name": names[0], "rate": None, "kd1": None,
                    "battles": None, "units": units, "names": names,
                    "power": sum(swgoh_data.unit_power(chars[b]) for b in units),
                    "factions": [], "source": "filler", "back_only": True,
                    "note": "no shared faction — flat +30 only; BACK territories only"})
        used.update(units)
    return out, used


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


def placement_order(graded, wall, cmap):
    """Merge the graded bank and the wall into ONE front-to-back placement order.

    Doctrine step 3 (notes.md, learned the expensive way): the graded bank outranks
    everything in the wall, so the two must be sorted TOGETHER before placing —
    otherwise a 42% wall ends up behind a 4% one. Strongest goes FRONT, because the
    front territory gates the map and absorbs the opponent's freshest squads.

    Squads with no published rate sort last regardless of power: an unranked filler
    must never outrank a measured wall, and `back_only` is carried through so the
    placement step can refuse to put one in a front territory.
    """
    rows = []
    for s in graded:
        rows.append({"rate": s.get("rate"), "units": s["units"],
                     "names": [cmap.get(b, {}).get("n", b) for b in s["units"]],
                     "source": "graded-board", "back_only": False,
                     "note": s.get("discount")})
    for s in wall:
        rows.append({"rate": s.get("rate"), "units": s["units"],
                     "names": s.get("names") or s["units"], "source": s["source"],
                     "back_only": bool(s.get("back_only")), "note": s.get("note")})
    rows.sort(key=lambda r: (r["back_only"], -(r["rate"] if r["rate"] is not None else -1)))
    band_n = max(1, len(rows) // 3)
    for i, r in enumerate(rows):
        r["slot"] = f"P{i + 1:02d}"
        r["band"] = "BACK" if r["back_only"] else ("FRONT" if i < band_n
                                                   else "MID" if i < 2 * band_n else "BACK")
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--total-def", type=int, default=cfg.TW_TOTAL_DEF,
                    help="total TW defensive squads to field, graded bank + wall")
    ap.add_argument("--placed", type=int, default=None,
                    help="squads already on the map (default: len of the TW defense bank)")
    ap.add_argument("--roster", default=swgoh_data.latest_roster_file(),
                    help="default: the newest data/roster/*.json")
    args = ap.parse_args()

    roster = json.load(open(args.roster))
    chars = {u["b"]: u for u in roster["units"] if u["ct"] == 1 and u["g"] >= 13}
    board = json.load(open(os.path.join(DATA, "board_result.json")))
    graded = board["tw"]["defense"]
    placed = args.placed if args.placed is not None else len(graded)

    cmap, size = load_categories()
    rates = load_leader_rates()
    ltable = la.load().get(("5v5", "def"), {})

    # Locked: on the map already, reserved for the attack phase, or attack-only GL.
    locked = {u for s in board["tw"]["defense"] + board["tw"]["offense"] for u in s["units"]}
    locked |= set(cfg.ATTACK_ONLY_BY_FORMAT["5v5"])
    locked &= set(chars) | locked

    tier1, used = leftover_lineups(locked, board, cmap)
    tier2, used = build_wall(used, chars, cmap, size, rates, ltable)
    tier4, used = filler_squads(used, chars, cmap, locked,
                                limit=max(0, args.total_def - placed - len(tier1) - len(tier2)))
    wall = tier1 + tier2 + tier4

    print(f"on the map: {placed} graded squads = {placed * BANNERS_PER_SQUAD} banners · "
          f"target {args.total_def} total")
    by_src = {}
    for s in wall:
        by_src[s["source"]] = by_src.get(s["source"], 0) + 1
    print(f"wall adds {len(wall)}: " + " + ".join(f"{v} {k}" for k, v in by_src.items()) + "\n")
    for i, s in enumerate(wall, 1):
        kd = f" kyber {s['kd1']}%" if s.get("kd1") is not None else ""
        nm = s.get("names") or s["units"]
        rate = f"{s['rate']:5.1f}%" if s.get("rate") is not None else "    -"
        print(f"W{i:02d}  {rate}{kd:14s} n={str(s['battles']):>7} "
              f"[{s['source'][:7]}] {', '.join(nm)}")
        if s.get("note"):
            print(f"        {s['note']}")

    order = placement_order(graded, wall, cmap)
    idle = [b for b in chars if b not in used and b not in locked]
    squads = placed + len(wall)
    print(f"\nwall complete: {placed} graded + {len(wall)} wall = {squads} squads "
          f"= {squads * BANNERS_PER_SQUAD} banners (+ fleets at {FLEET_BANNERS} each)")
    print(f"units still idle after the wall: {len(idle)}")

    os.makedirs(OUT, exist_ok=True)
    json.dump({"placed": placed, "total_def": args.total_def,
               "banners_per_squad": BANNERS_PER_SQUAD, "fleet_banners": FLEET_BANNERS,
               "squads": squads, "squad_banners": squads * BANNERS_PER_SQUAD,
               "wall": wall, "placement_order": order, "idle_after": sorted(idle)},
              open(os.path.join(OUT, "tw_wall.json"), "w"), indent=1)

    sheet = [f"TERRITORY WAR — DEFENSIVE PLACEMENT ORDER ({squads} squads, "
             f"{squads * BANNERS_PER_SQUAD} banners)",
             "Place P01 first into the FRONT-most territory with room, then work back.",
             "A BACK-only filler must NEVER take a front slot — the 39/territory cap is",
             "guild-wide and first-come, so that slot is one a guildmate cannot use.", ""]
    for r in order:
        rate = f"{r['rate']:5.1f}%" if r["rate"] is not None else "  n/a"
        # " · " not ", ": unit names CONTAIN commas ("Mara Jade, the Emperor's Hand"),
        # so a comma-joined line reads as six units in a five-unit squad.
        sheet.append(f"{r['slot']} {r['band']:<5} {rate} [{r['source'][:12]:<12}] "
                     f"{' · '.join(r['names'])}  ({len(r['units'])})")
    dst = os.path.join(OUT, "tw_placement_sheet.txt")
    open(dst, "w").write("\n".join(sheet) + "\n")
    print(f"wrote output/tw_wall.json and {os.path.relpath(dst, ROOT)}")


if __name__ == "__main__":
    main()
