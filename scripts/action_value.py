#!/usr/bin/env python3
"""Price every action against the one thing that is actually scarce.

WHY THIS EXISTS. Until now the repo priced exactly one mode well: GAC, in banners
(`gac_score.py`). Everything else was decided from prose — which pool to drain, which
node to sit on, which token to spend. Nothing priced energy at all. That is how ~464
energy got spent on 2026-08-17 in an order taken on faith, and how 98.4K Galactic War
tokens came to sit stranded with nobody able to say whether they were worth anything.

THE MODEL. A relic upgrade is a FIXED BASKET of materials (`data/economy.json`,
sourced from swgoh.wiki). You cannot convert one unit from R7 to R9 without all of it.
So throughput is not the average of your stock — it is the MINIMUM over materials of
(stock / need). That single fact does the work:

  * the binding material is the argmin, and it alone sets your rate;
  * a material you hold in surplus has a shadow price of ~0, so farming it is waste
    however good the node looks;
  * a material with no purchase route cannot be fixed by tokens at ANY price, which
    promotes the events that drop it from "optional" to "mandatory".

Two such hard gates fall out of the data rather than out of opinion:
  * SIGNAL DATA is cantina-energy-only. No store sells it for a raid token. It is also
    the largest quantity in the basket (100 Flawed per R7->R9), which is why the
    community calls it the endgame bottleneck.
  * DROID BRAIN has no repeatable token route at all — Assault Battles, Endor
    Escalation, Knightfall, Coven of Shadows, or crystals. Raid tickets cannot buy it.

Everything else in the R7->R9 basket is purchasable with Mk III / Mk II raid tokens,
and raid tokens come from raid throughput, which is gated by 600 tickets/day, which is
1 ticket per energy. That is the whole value chain, and it is why the ticket cap is the
single highest-leverage daily habit:

    energy -> tickets -> raid score -> Mk III tokens -> relic mats -> R9

Usage:
    python3 scripts/action_value.py                 # full report
    python3 scripts/action_value.py --from 7 --to 9 # a different conversion band
    python3 scripts/action_value.py --units 10      # plan for 10 conversions
"""
import argparse
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ECONOMY = os.path.join(ROOT, "data", "economy.json")

# The roster stores relic as `rt`, offset by 2: rt=9 is Relic 7. Getting this wrong is
# not hypothetical — it is the 2026-08-17 raid-tier error, and advisor.py carried the
# same bug in the opposite direction (commit 02e6842).
RT_OFFSET = 2

# Spending these is forbidden by standing owner rule, so routes denominated in them are
# priced but never recommended.
FORBIDDEN = {"crystals"}


def load_economy(path=ECONOMY):
    with open(path) as f:
        return json.load(f)


def basket(economy, from_level, to_level):
    """Materials consumed converting ONE unit from `from_level` to `to_level`.

    Sums the per-step recipes, so R7->R9 is the 7->8 step plus the 8->9 step.
    """
    if to_level <= from_level:
        raise ValueError(f"to_level {to_level} must exceed from_level {from_level}")
    total = {}
    for lvl in range(from_level, to_level):
        step = economy["relic_recipe"].get(str(lvl))
        if step is None:
            raise KeyError(f"no recipe for relic level {lvl} in economy.json")
        for mat, qty in step.items():
            if mat.startswith("_"):
                continue
            total[mat] = total.get(mat, 0) + qty
    return total


def unit_costs(economy):
    """Cheapest unit price per (material, currency), from the researched route table.

    Stores sell in lots (2 for 530, 3 for 795); the per-unit rate is what compares.
    """
    out = {}
    for mat, routes in economy["routes"].items():
        if mat.startswith("_"):
            continue
        best = {}
        for r in routes:
            cur, per = r["currency"], r["cost"] / r["qty"]
            if cur not in best or per < best[cur]["unit_cost"]:
                best[cur] = {"unit_cost": per, "store": r["store"],
                             "qty": r["qty"], "cost": r["cost"]}
        out[mat] = best
    return out


def basket_cost(bask, costs, currency):
    """Cost of one conversion in `currency`, and which materials that currency cannot buy.

    `unbuyable` is the interesting half of the return value: it names the hard gates.
    """
    total, breakdown, unbuyable = 0.0, {}, []
    for mat, qty in bask.items():
        if mat == "credits":
            continue
        route = costs.get(mat, {}).get(currency)
        if route is None:
            unbuyable.append(mat)
            continue
        spend = qty * route["unit_cost"]
        breakdown[mat] = spend
        total += spend
    return total, breakdown, unbuyable


def throughput(bask, stock):
    """How many complete conversions the stock supports, and what stops it.

    The min over (stock/need) IS the answer — a surplus of nine materials buys nothing
    if the tenth is empty. Materials absent from `stock` are treated as unknown, not
    zero, so a partial inventory degrades honestly instead of reporting a false zero.
    """
    ratios, unknown = {}, []
    for mat, need in bask.items():
        if mat == "credits" or need <= 0:
            continue
        if mat not in stock:
            unknown.append(mat)
            continue
        ratios[mat] = stock[mat] / need
    if not ratios:
        return None, [], unknown
    lowest = min(ratios.values())
    binding = sorted(m for m, r in ratios.items() if r == lowest)
    return lowest, binding, unknown


def shortfall(bask, stock, units):
    """Per material: how many more are needed to complete `units` conversions."""
    out = {}
    for mat, need in bask.items():
        if mat == "credits":
            continue
        have = stock.get(mat, 0)
        gap = need * units - have
        if gap > 0:
            out[mat] = gap
    return out


def plan_routes(gap, costs):
    """For each shortfall, every allowed route — and whether a currency is FORCED.

    Deliberately does NOT pick a global "cheapest": 90 scrap points and 250 Mk III
    tokens are different units, and taking a min across them is arithmetic on
    incommensurable quantities. Comparing unit costs is only meaningful *within* a
    currency.

    What IS decidable without an exchange rate is substitutability. A material with
    exactly one allowed currency is a forced draw on it; a material with alternatives
    is discretionary. That yields a real allocation rule with no invented constants:
    spend the contested currency on what forces it, and cover the rest elsewhere.
    """
    rows = []
    for mat, need in sorted(gap.items(), key=lambda kv: -kv[1]):
        options = {c: r for c, r in costs.get(mat, {}).items() if c not in FORBIDDEN}
        rows.append({
            "material": mat,
            "need": need,
            "options": {c: {"spend": need * r["unit_cost"], "store": r["store"]}
                        for c, r in options.items()},
            "forced": next(iter(options)) if len(options) == 1 else None,
            "event_only": not options,
        })
    return rows


def currency_demand(rows, currency):
    """Split demand on one currency into forced (no substitute) and discretionary."""
    forced = {r["material"]: r["options"][currency]["spend"]
              for r in rows if r["forced"] == currency}
    optional = {r["material"]: r["options"][currency]["spend"]
                for r in rows
                if r["forced"] != currency and currency in r["options"]}
    return forced, optional


def relic_of(unit):
    """Relic tier from a roster entry, or 0 for a unit with no relic."""
    rt = unit.get("rt")
    return rt - RT_OFFSET if isinstance(rt, int) and rt > RT_OFFSET else 0


def count_at_relic(roster, tier):
    return [u for u in roster if relic_of(u) == tier]


def load_roster(path):
    with open(path) as f:
        d = json.load(f)
    if isinstance(d, list):
        return d
    for key in ("roster", "units"):
        if isinstance(d.get(key), list):
            return d[key]
    for v in d.values():
        if isinstance(v, list):
            return v
    raise ValueError(f"no unit list found in {path}")


def match_material(name, raw_ids):
    """Map an economy key onto HotUtils' material id by word match.

    HotUtils ids are opaque and undocumented here, so hardcoding them would rot the
    first time CG renames one. Matching on the words instead ("impulse_detector" ->
    an id containing both IMPULSE and DETECTOR) survives prefix and casing changes,
    and returns None rather than guessing when nothing matches cleanly.
    """
    words = [w for w in name.upper().split("_") if w]
    hits = [i for i in raw_ids if all(w in i.upper() for w in words)]
    return min(hits, key=len) if hits else None


def load_stock(path, materials=()):
    """Relic-material stock from a pull, keyed by economy material name.

    Reads `all_mats` (the full material dict `pull_mods.py` now keeps) and falls back
    to an explicit `relic_mats`/`materials` override. A material that cannot be matched
    is simply absent, which `throughput` reports as unknown rather than as zero — a
    false zero would name the wrong binding constraint, which is the whole point.
    """
    if not path or not os.path.exists(path):
        return {}
    with open(path) as f:
        d = json.load(f)
    explicit = d.get("relic_mats") or d.get("materials")
    if explicit:
        return {k: v for k, v in explicit.items() if isinstance(v, (int, float))}
    raw = d.get("all_mats") or {}
    out = {}
    for mat in materials:
        key = match_material(mat, raw)
        if key is not None and isinstance(raw[key], (int, float)):
            out[mat] = raw[key]
    return out


def _fmt(n):
    return f"{n:,.0f}"


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--from", dest="src", type=int, default=7)
    ap.add_argument("--to", dest="dst", type=int, default=9)
    ap.add_argument("--units", type=int, default=None,
                    help="how many conversions to plan for (default: the roster's pile "
                         "at the source relic tier)")
    ap.add_argument("--roster", default=None)
    ap.add_argument("--stock", default=None, help="json with a relic_mats/materials dict")
    args = ap.parse_args()

    econ = load_economy()
    bask = basket(econ, args.src, args.dst)
    costs = unit_costs(econ)

    print(f"=== ONE UNIT, RELIC {args.src} -> {args.dst} ===")
    print(f"credits {_fmt(bask.get('credits', 0))}")
    for mat, qty in sorted(bask.items(), key=lambda kv: -kv[1]):
        if mat != "credits":
            print(f"  {mat:26} {qty:>5}")

    print("\n=== COST OF ONE CONVERSION, BY CURRENCY ===")
    for cur in ("mk3_raid_token", "mk2_raid_token", "conquest_credit"):
        total, breakdown, unbuyable = basket_cost(bask, costs, cur)
        if not breakdown:
            continue
        print(f"\n{cur}: {_fmt(total)} buys {len(breakdown)}/{len(bask) - 1} materials")
        for mat, spend in sorted(breakdown.items(), key=lambda kv: -kv[1]):
            print(f"  {mat:26} {_fmt(spend):>9}  ({spend / total * 100:4.1f}%)")

    _, _, unbuyable = basket_cost(bask, costs, "mk3_raid_token")
    hard = [m for m in unbuyable
            if not any(c not in FORBIDDEN for c in costs.get(m, {}))]
    if hard:
        print("\n=== HARD GATES: no token route at any price ===")
        for mat in hard:
            where = econ["event_only"].get(
                mat, econ["event_only"].get("signal_data") if "signal_data" in mat else [])
            print(f"  {mat:26} {'; '.join(where) if where else 'unknown source'}")
        print("  ^ raid tickets cannot buy these. The events above are mandatory,")
        print("    not optional, for progress past this relic band.")

    units = args.units
    roster_path = args.roster
    if roster_path is None:
        rdir = os.path.join(ROOT, "data", "roster")
        files = sorted(f for f in os.listdir(rdir) if f.endswith(".json"))
        roster_path = os.path.join(rdir, files[-1]) if files else None

    if roster_path and os.path.exists(roster_path):
        roster = load_roster(roster_path)
        pile = count_at_relic(roster, args.src)
        print(f"\n=== DEMAND (roster: {os.path.basename(roster_path)}) ===")
        print(f"units sitting at Relic {args.src}: {len(pile)}")
        if units is None:
            units = len(pile)

    if not units:
        return

    print(f"\n=== TOTAL TO CONVERT {units} UNITS ===")
    stock = load_stock(args.stock, [m for m in bask if m != "credits"])
    rate, binding, unknown = throughput(bask, stock)
    if rate is None:
        print("no relic-material stock available — showing gross requirement.")
        print("(pull_mods.py discards relic mats; capture them to get shadow prices.)")
    else:
        print(f"stock supports {rate:.2f} conversions; binding: {', '.join(binding)}")
        if unknown:
            print(f"unknown stock for: {', '.join(sorted(unknown))}")

    gap = shortfall(bask, stock, units)
    rows = plan_routes(gap, costs)

    print(f"\n{'material':26} {'need':>7}  routes (spend in that currency)")
    for row in rows:
        if row["event_only"]:
            print(f"{row['material']:26} {row['need']:>7}  EVENT-FARMED ONLY — unbuyable")
            continue
        opts = "  ".join(f"{c}={_fmt(v['spend'])}" for c, v in
                         sorted(row["options"].items(), key=lambda kv: kv[0]))
        tag = "  [FORCED]" if row["forced"] else ""
        print(f"{row['material']:26} {row['need']:>7}  {opts}{tag}")

    print("\n=== ALLOCATION RULE: spend a contested currency on what forces it ===")
    for cur in ("mk3_raid_token", "mk2_raid_token", "conquest_credit", "scrap_points"):
        forced, optional = currency_demand(rows, cur)
        if not forced and not optional:
            continue
        print(f"\n{cur}")
        if forced:
            print(f"  forced        {_fmt(sum(forced.values())):>12}  "
                  f"({', '.join(sorted(forced))}) — no substitute exists")
        if optional:
            print(f"  discretionary {_fmt(sum(optional.values())):>12}  "
                  f"({', '.join(sorted(optional))}) — cover these elsewhere first")
    print(f"\ncredits: {_fmt(bask.get('credits', 0) * units)}")


if __name__ == "__main__":
    main()
