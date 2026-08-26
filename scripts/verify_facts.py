#!/usr/bin/env python3
"""Check the repo's prose against the live roster, and answer roster questions directly.

WHY THIS EXISTS. Facts enter this repo by observation and then never get re-checked.
On 2026-08-17 `memory/order66-raid-mechanics.md` asserted a raid squad was "gear 5-7,
zero relics". The roster said `g=13, rt=7` — Relic 5. That wrong fact chose the raid
difficulty, the run capped a tier below where it could have, and it was the last of
five attempts for the cycle. Nothing in the repo could have caught it, because nothing
compared a written claim to the data sitting in `data/roster/`.

Two modes, both cheap enough to run before acting:

    python3 scripts/verify_facts.py                  # validate data/claims.json
    python3 scripts/verify_facts.py --unit IMAGUNDI  # ground truth for one unit

The oracle mode is the one that would actually have prevented the error: it costs a
second, and it prints the number the character card is ambiguous about.

Exits non-zero when any claim fails, so it can gate a pipeline run.
"""
import argparse
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLAIMS = os.path.join(ROOT, "data", "claims.json")
ROSTER_DIR = os.path.join(ROOT, "data", "roster")

# Roster stores relic offset by 2: rt=9 is Relic 7, rt<=2 means no relic at all.
RT_OFFSET = 2


def latest_roster_path(directory=ROSTER_DIR):
    files = sorted(f for f in os.listdir(directory) if f.endswith(".json"))
    if not files:
        raise FileNotFoundError(f"no roster json in {directory}")
    return os.path.join(directory, files[-1])


def load_roster(path):
    with open(path) as f:
        d = json.load(f)
    units = _unit_list(d)
    return {u["b"]: u for u in units if u.get("b")}


def _unit_list(d):
    """The roster ships in a few shapes: a bare list, or wrapped under a key."""
    if isinstance(d, list):
        return d
    if isinstance(d, dict):
        for key in ("roster", "units"):
            if isinstance(d.get(key), list):
                return d[key]
        for value in d.values():
            if isinstance(value, list):
                return value
    raise ValueError("no unit list found in roster file")


def relic_of(unit):
    rt = unit.get("rt")
    return rt - RT_OFFSET if isinstance(rt, int) and rt > RT_OFFSET else 0


def describe(base_id, unit):
    if unit is None:
        return f"{base_id}: NOT OWNED"
    rel = relic_of(unit)
    return (f"{base_id}: gear {unit.get('g', '?')} · "
            f"relic {rel if rel else 'none'} (rt={unit.get('rt')}) · "
            f"{unit.get('r', '?')}★ · gp {unit.get('gp', '?')}")


def _check_unit(claim, base_id, roster, failures):
    """Validate the per-unit fields of a claim against one roster entry."""
    unit = roster.get(base_id)
    if unit is None:
        failures.append(f"{base_id} is not on the roster")
        return
    if "owned" in claim and not claim["owned"]:
        failures.append(f"{base_id} is owned but the claim says it is not")
    if "gear" in claim and unit.get("g") != claim["gear"]:
        failures.append(f"{base_id} gear is {unit.get('g')}, claim says {claim['gear']}")
    if "stars" in claim and unit.get("r") != claim["stars"]:
        failures.append(f"{base_id} stars is {unit.get('r')}, claim says {claim['stars']}")
    rel = relic_of(unit)
    if "relic" in claim and rel != claim["relic"]:
        failures.append(f"{base_id} relic is R{rel}, claim says R{claim['relic']}")
    if "min_relic" in claim and rel < claim["min_relic"]:
        failures.append(f"{base_id} relic is R{rel}, claim needs at least R{claim['min_relic']}")
    # `o` is a COUNT of applied omicrons and says nothing about their MODE. It is still
    # the only omicron fact the roster can prove, and "this omicron has NOT been bought"
    # is exactly the claim a watch item needs: the day it is bought, the check fails and
    # forces someone to re-read why it was being watched.
    # ⚠ Added 2026-08-26 WITH its first claim. An unknown key is silently ignored by this
    # function, so adding `"omicrons": N` to claims.json without this branch produces a
    # claim that always passes while verifying nothing — a false green, and worse than
    # no claim at all.
    if "omicrons" in claim and unit.get("o") != claim["omicrons"]:
        failures.append(f"{base_id} has {unit.get('o')} omicrons applied, "
                        f"claim says {claim['omicrons']}")


def check_claim(claim, roster):
    """Return (ok, list_of_failure_strings) for one claim."""
    failures = []
    targets = claim.get("all_units") or ([claim["unit"]] if "unit" in claim else [])
    for base_id in targets:
        _check_unit(claim, base_id, roster, failures)

    if "relic_count" in claim:
        tier = claim["relic_count"]
        actual = sum(1 for u in roster.values() if relic_of(u) == tier)
        tol = claim.get("tolerance", 0)
        if abs(actual - claim["value"]) > tol:
            failures.append(f"units at exactly R{tier} is {actual}, "
                            f"claim says {claim['value']} (tolerance {tol})")

    if "min_relic_count" in claim:
        tier = claim["min_relic_count"]
        actual = sum(1 for u in roster.values() if relic_of(u) >= tier)
        tol = claim.get("tolerance", 0)
        if abs(actual - claim["value"]) > tol:
            failures.append(f"units at R{tier}+ is {actual}, "
                            f"claim says {claim['value']} (tolerance {tol})")

    return (not failures), failures


def run(claims, roster):
    passed, failed = [], []
    for claim in claims:
        ok, why = check_claim(claim, roster)
        (passed if ok else failed).append((claim, why))
    return passed, failed


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--unit", help="print ground truth for a base id and exit")
    ap.add_argument("--roster", default=None)
    ap.add_argument("--claims", default=CLAIMS)
    ap.add_argument("--quiet", action="store_true", help="only report failures")
    args = ap.parse_args()

    roster_path = args.roster or latest_roster_path()
    roster = load_roster(roster_path)

    if args.unit:
        key = args.unit.upper()
        if key in roster:
            print(describe(key, roster[key]))
            return 0
        near = sorted(b for b in roster if key in b)
        if not near:
            print(f"{key}: NOT OWNED (and no base id contains that string)")
            return 1
        for b in near:
            print(describe(b, roster[b]))
        return 0

    with open(args.claims) as f:
        claims = json.load(f)["claims"]

    passed, failed = run(claims, roster)
    print(f"roster: {os.path.basename(roster_path)} ({len(roster)} units)")
    if not args.quiet:
        for claim, _ in passed:
            print(f"  ok    {claim['id']:28} [{claim['source']}]")
    for claim, why in failed:
        print(f"  FAIL  {claim['id']:28} [{claim['source']}]")
        for line in why:
            print(f"          {line}")
        if claim.get("note"):
            print(f"          note: {claim['note']}")
    print(f"\n{len(passed)} passed, {len(failed)} failed")
    if failed:
        print("A failing claim means a file in this repo is telling you something untrue.")
        print("Fix the FILE, not this checker.")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
