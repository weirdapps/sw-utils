#!/usr/bin/env python3
"""
build_board.py — one pass: roster + swgoh.gg meta -> the whole competitive board.

Produces, all unit-disjoint within each mode:
  GAC 5v5 - Defense / Offense      (Kyber 4-zone board)
  GAC 3v3 - Defense / Offense
  TW 5v5  - Defense / Offense      (deeper bench; defense weighted up)
  GAC Fleet - Defense / Offense    (no ship reused across the six)
  Fleet - Arena                    (separate mode, no sharing rule)

Selection is an exact ILP (see optimize_board.py) over squads that Astra can
actually field, maximising expected net banners. Judgement inputs — datacron
durability, fleet lineups, attack-only GLs — live in board_config.py and
build_fleets.py so this file stays mechanical.

Run:  python3 scripts/build_board.py
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import board_config as cfg          # noqa: E402
import build_fleets as fleets       # noqa: E402
import datacron_exposure as dx      # noqa: E402
import durability as du             # noqa: E402
import gac_score as gs              # noqa: E402
import league_adjust as la          # noqa: E402
import optimize_board as ob         # noqa: E402
import swgoh_data                   # noqa: E402
import swgoh_meta                   # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
META = os.path.join(DATA, "meta")
OUT = os.path.join(ROOT, "output")
ROSTER_FILE = swgoh_data.latest_roster_file()

# main = swgoh.gg's own significance cutoff; deep = cutoff=0 sorted by usage, which
# is where the Territory War bench comes from.
# Season pairing (re-checked 2026-08-18 against the live /gac/squads/ dropdown):
# swgoh.gg's DEFAULT page is the newest season with data, and that is S81 = 3v3
# (3 units per row). S82 is still in progress so it has no table yet. The newest
# EVEN (5v5) season with data is therefore S80. Do not "upgrade" the 5v5 files to
# an odd season id — you will silently load 3v3 rows into the 5v5 board.
META_MAIN = {("5v5", "def"): "meta_def5v5_s80.txt", ("5v5", "off"): "meta_off5v5.txt",
             ("3v3", "def"): "meta_def3v3.txt", ("3v3", "off"): "meta_off3v3.txt"}
# ⚠ 2026-08-18: the /gac/squads/ table is HARD-CAPPED AT 100 ROWS and is always
# ordered by Seen descending, so `cutoff=0` returns exactly the same 100 rows as
# `cutoff=0.1`. The main/deep split therefore collapses — pointing DEEP at the
# stale Aug-5 *_deep.txt files only mixed a two-week-old meta into the TW bench.
# Both tiers now read the same fresh scrape; re-split this only if swgoh.gg ever
# paginates past 100.
META_DEEP = META_MAIN


def load_pools():
    roster = json.load(open(ROSTER_FILE))
    chars = {u["b"]: u for u in roster["units"] if u["ct"] == 1}
    ships = {u["b"]: u for u in roster["units"] if u["ct"] == 2}
    g13 = {b for b, u in chars.items() if u["g"] >= 13}
    # displayed relic = rt - 2 (device-verified); a unit with no relic reads 0
    relics = {b: max(0, (u.get("rt") or 0) - 2) for b, u in chars.items()}

    main = swgoh_meta.load_meta(META_MAIN, META)
    deep = swgoh_meta.load_meta(META_DEEP, META)
    names = {b: v["n"] for b, v in json.load(open(os.path.join(DATA, "name_type_map.json"))).items()}
    names.update({u["b"]: u["n"] for u in roster["units"]})
    dtables = du.load() if cfg.DEFENSE_DURABILITY else {}
    ltables = la.load() if cfg.LEAGUE_ADJUST else {}

    pools = {}
    for key in META_MAIN:
        merged = {}
        for s in main[key] + deep[key]:          # dedup on lineup, keep the bigger sample
            k = tuple(s["units"])
            if k not in merged or s["seenN"] > merged[k]["seenN"]:
                merged[k] = s
        out = []
        for s in merged.values():
            if s["seenN"] < cfg.BENCH_MIN_SEEN:
                continue
            s = dict(s)
            s["thin"] = (s["seenN"] < cfg.MIN_SEEN
                         and frozenset(s["units"]) not in cfg.CORE_ALLOW)
            s["missing"] = [b for b in s["units"] if b not in g13]
            adj, why = cfg.adjust(s)
            # DEFENSE ONLY: correct to (a) no-datacron baseline and (b) Kyber-D1
            # opposition. Both are per-leader ratios; their product is clamped
            # because each is a noisy estimate.
            if key[1] == "def":
                lead = names.get(s["units"][0], s["units"][0])
                dr, note = (du.squad_ratio(dtables[key], lead,
                                           [names.get(b, b) for b in s["units"]])
                            if key in dtables else (1.0, None))
                lr, lnote = (la.ratio(ltables[key], lead, key[0]) if key in ltables else (1.0, None))
                combined = la.combine(lr, dr)
                if abs(combined - 1.0) > 1e-9:
                    adj *= combined
                    s["dc_ratio"], s["lg_ratio"] = round(dr, 2), round(lr, 2)
                    why = " | ".join(x for x in (note, lnote) if x)
                elif note or lnote:
                    why = " | ".join(x for x in (note, lnote) if x)
            s["raw_rate"], s["rate"], s["discount"] = s["rate"], adj, why
            price(s, key[0], key[1], relics)
            out.append(s)
        if key[1] == "def":
            out += datacron_walls(key[0], g13, relics)
        pools[key] = out
    return roster, chars, ships, g13, pools


def datacron_walls(fmt, g13, relics):
    """Walls that exist only because of a focused datacron, so swgoh.gg files them
    on the datacron tier list and data/meta/* has never contained them."""
    out = []
    for d in cfg.DATACRON_SQUADS[fmt]:
        missing = [u for u in d["units"] if u not in g13]
        s = dict(d, ban=BAN_FROM_HOLD(fmt, d["rate"]), missing=missing, thin=False,
                 raw_rate=d["rate"], discount=None, dc_ratio=None, lg_ratio=None)
        price(s, fmt, "def", relics)
        out.append(s)
    return out


def BAN_FROM_HOLD(fmt, hold):
    """Estimate banners conceded from Hold% when swgoh.gg only publishes the hold.

    Fitted on this repo's own 5v5 defense rows, where the relationship is close to
    linear: 57%->25.2, 37%->40.3, 31%->42.4, 19%->48.3 gives ban ~ REF - 0.70*hold.
    Flagged as an estimate wherever it is used.
    """
    return round(gs.REF_BATTLE[fmt] - 0.70 * hold, 2)


def price(s, fmt, persp, relics):
    """Convert a meta row into BANNERS, which is the only currency GAC pays in.

    Adds three fields and leaves the originals alone so the playbook can still show
    the published numbers next to the corrected ones:
      relic_f  how far below the Kyber norm Astra's copy of this squad is built
      ban_eff  banners earned (offense) / conceded (defense) after that correction
      value    what the optimiser maximises
    """
    ref = gs.REF_BATTLE[fmt]
    rf = 1.0 if s.get("no_relic_penalty") else cfg.relic_factor(s["units"], relics)
    s["relic_f"] = round(rf, 3)
    s["rate"] = s["rate"] * rf
    if persp == "off":
        s["ban_eff"] = round(s["ban"] * rf, 2)
        s["value"] = s["ban_eff"]
    else:
        # a weaker build concedes more: the DENIAL shrinks, not the concession
        s["ban_eff"] = round(ref - (ref - s["ban"]) * rf, 2)
        s["value"] = (ref - s["ban_eff"]) + cfg.GATE_WEIGHT * s["rate"]
    return s


def fieldable(pool, thin=False):
    """Squads Astra can actually field. `thin=True` also returns the lightly-sampled
    rows, which are good enough for a bench attack but never for a core pick."""
    return [s for s in pool if not s["missing"] and (thin or not s["thin"])]


def annotate(squads, unit_map):
    """Tag each chosen squad with its live-datacron exposure.

    Not priced into selection (see board_config.DURABILITY_ENABLED) - this is so
    the playbook can say WHICH squads rent their rate and WHEN the rent is due.
    """
    for s in squads:
        exp = dx.exposure(s["units"], unit_map, min_coverage=0.32)
        s["datacron"] = exp[:2]
        s["expiring"] = [e for e in exp if e["days"] <= dx.IMMINENT and e["coverage"] >= 0.5]
    return squads


def build():
    roster, _chars, ships, _g13, pools = load_pools()
    unit_map = dx.load_units()
    result = {"meta": {"gp": roster["meta"]["gp"], "pulled": roster["meta"]["pulled"],
                       "season_5v5": "S80", "season_3v3": "S81",
                       "datacron_sets": dx.SETS}}

    # ---- GAC, per format -----------------------------------------------------
    for fmt in ("5v5", "3v3"):
        b = cfg.BOARD[fmt]
        D, O = fieldable(pools[(fmt, "def")]), fieldable(pools[(fmt, "off")])
        cd, co = ob.solve(D, O, b["def"], b["off"],
                          forced_off_leaders=cfg.ATTACK_ONLY_BY_FORMAT[fmt],
                          reserved_off_units=cfg.RESERVE_OFF_UNITS[fmt])
        bench = ob.add_bench(cd, co, fieldable(pools[(fmt, "off")], thin=True), b["bench"])
        slots = sum(z["slots"] for z in gs.ZONES[fmt] if not z["fleet"])
        if len(cd) != slots:
            raise SystemExit(f"{fmt}: solver returned {len(cd)} defense squads for "
                             f"{slots} map slots. Every slot must be filled — an unset "
                             f"one is a free {gs.MAX_BATTLE[fmt]} banners to the opponent.")
        cd.sort(key=lambda s: (-s["rate"], -s["seenN"]))
        co.sort(key=lambda s: (-s["value"], -s["seenN"]))
        result[fmt] = {"defense": annotate(cd, unit_map),
                       "offense": annotate(co + bench, unit_map),
                       "core_off": len(co), "gaps": gaps(pools, fmt)}

    # ---- Territory War (5v5, deeper, defense weighted up) --------------------
    D = fieldable(pools[("5v5", "def")])
    O = [dict(s, value=s["value"] * cfg.TW["off_weight"]) for s in fieldable(pools[("5v5", "off")])]
    td, to = ob.solve(D, O, cfg.TW["def"], cfg.TW["off"],
                      forced_off_leaders=cfg.ATTACK_ONLY_BY_FORMAT["5v5"])
    for s in to:                                   # undo the weighting for display
        s["value"] = s["value"] / cfg.TW["off_weight"]
    td.sort(key=lambda s: (-s["rate"], -s["seenN"]))
    to.sort(key=lambda s: (-s["value"], -s["seenN"]))
    result["tw"] = {"defense": annotate(td, unit_map), "offense": annotate(to, unit_map)}

    # ---- fleets --------------------------------------------------------------
    result["fleets"] = {
        cat: [{"name": nm, "units": fleets.FLEET_LINEUPS[key], "note": note,
               "missing": [s for s in fleets.FLEET_LINEUPS[key] if s not in ships],
               "understarred": [f"{ships[s]['n']} {ships[s]['r']}*"
                                for s in fleets.FLEET_LINEUPS[key]
                                if s in ships and ships[s]["r"] < 7]}
              for nm, key, note in items]
        for cat, items in fleets.ASSIGNMENT.items()}
    return result


def gaps(pools, fmt):
    """Top meta squads that cannot be fielded, and exactly what is missing."""
    out = {}
    for persp in ("def", "off"):
        rows = []
        for s in sorted(pools[(fmt, persp)], key=lambda x: (-x["raw_rate"], -x["seenN"])):
            if not s["missing"]:
                continue
            rows.append({"rate": s["raw_rate"], "seen": s["seen"], "units": s["units"],
                         "missing": s["missing"]})
            if len(rows) >= 8:
                break
        out[persp] = rows
    return out


def sweep():
    """Calibrate GATE_WEIGHT by measuring, not by feel.

    For each candidate weight: rebuild the board, place it exactly with
    gac_place.solve (which computes the gated lane value properly instead of
    linearising it), and score

        net = banners my best 14 offense squads earn  -  banners my defense concedes

    14 is not arbitrary: it is exactly how many enemy squads+fleets stand between
    Astra and a full clear in Kyber 5v5, so squads beyond the 14th are retry depth
    and do not add to the headline. Higher net is better.
    """
    import gac_place as gp
    print(f"{'GATE_W':>7} {'off(top14)':>11} {'conceded':>9} {'net':>8}   defense leaders")
    for gw in (0.0, 1.0, 2.0, 2.5, 3.0, 4.0, 6.0):
        cfg.GATE_WEIGHT = gw
        res = build()
        for fmt in ("5v5",):
            d, o = res[fmt]["defense"], res[fmt]["offense"]
            off = sum(s["ban_eff"] for s in sorted(o, key=lambda x: -x["ban_eff"])[:14])
            placed, conceded, _ = gp.solve(fmt, sorted(d, key=lambda s: -s["rate"]),
                                           res["fleets"].get("GAC Fleet - Defense", []))
            leads = ", ".join(s["units"][0][:11] for s in d[:4])
            print(f"{gw:>7.1f} {off:>11.0f} {conceded:>9.0f} {off - conceded:>8.0f}   {leads}")


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    if "--sweep" in sys.argv:
        sweep()
        raise SystemExit(0)
    res = build()
    json.dump(res, open(os.path.join(DATA, "board_result.json"), "w"), indent=1)
    for fmt in ("5v5", "3v3"):
        d, o = res[fmt]["defense"], res[fmt]["offense"]
        print(f"GAC {fmt}: defense {len(d)} (sum {sum(s['rate'] for s in d):.0f}%)  "
              f"offense {len(o)} ({res[fmt]['core_off']} core + {len(o) - res[fmt]['core_off']} bench)")
    print(f"TW 5v5 : defense {len(res['tw']['defense'])}  offense {len(res['tw']['offense'])}")
    for cat, arr in res["fleets"].items():
        print(f"{cat}: " + ", ".join(f["name"] for f in arr))
    print("wrote data/board_result.json")
