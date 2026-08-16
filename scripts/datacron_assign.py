#!/usr/bin/env python3
"""
datacron_assign.py — match Astra's OWNED datacrons to GAC defence squads.

Why this exists: every earlier pass modelled datacrons as a *market* effect (how much of
a published hold% is rented from a cron somebody else was running). That is the
`durability.py` correction and it is still right. This script answers the *other* half,
which the repo has never asked: given the crons THIS account actually owns, which of our
own walls should carry which one.

A datacron has three tiers of effect (see memory/notes.md, 2026-08-08):
  L1-3  stat affixes + an ability, scoped to an ALIGNMENT (sets 31/33) or a ROLE (set 32)
  L4-6  stat affixes + an ability, scoped to a FACTION (or the second role)
  L7-9  stat affixes + an ability, scoped to ONE NAMED CHARACTER
So a cron is only worth carrying if the squad actually contains its faction and,
ideally, its named character.

Reads  : data/board_result.json, data/roster/*.json, data/unit_tags.json
Writes : output/datacron_plan.json  (+ a human table on stdout)
"""
import itertools
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
OUT = os.path.join(ROOT, "output")

# ---------------------------------------------------------------------------
# Astra's 14 owned datacrons, re-read live from HotUtils account/data/all ->
# datacrons[] on 2026-08-16. affix[].targetRule is the ground truth and `lvl` is the
# LENGTH of the affix array, which is exactly the cron's level (one affix per level;
# the scoped ones land on tiers 3/6/9, and on 3/6/9/12/15 for a focused cron).
#
# Corrections against the previous hand-typed copy of this table, all from the live
# pull: the raccoon FDC is at level 15 (MAX), not 9 — so the #1 defensive datacron in
# the game is already fully built; its member is RACCOON (Rotta the Hutt's baseId),
# not "ROTTA"; the bishop FDC's second member is GOPHERANTS (Grogu & Anzellans); the
# two set-33 stubs are level 3, not 1; and two crons were missing entirely.
#
# ⚠ SET 31 EXPIRES 2026-09-03. Three of the eight level-9 crons are set 31, and two
# of those three are Old Republic (Bastila Shan and Satele Shan) — i.e. built for the
# Satele wall. Use them now; they are worthless in 18 days.
# ---------------------------------------------------------------------------
OWNED = [
    dict(id="_aCmHy14", set=31, lvl=9, l3=("align", "Light Side"),
         l6=("cat", "Old Republic"), l9="BASTILASHAN"),
    dict(id="Vv6-WgS8", set=31, lvl=9, l3=("align", "Dark Side"),
         l6=("cat", "Separatist"), l9="JANGOFETT"),
    dict(id="E6Vv-i2f", set=31, lvl=9, l3=("align", "Light Side"),
         l6=("cat", "Old Republic"), l9="SATELESHAN"),
    dict(id="ubRPvm5a", set=32, lvl=9, l3=("role", "Healer"),
         l6=("role", "Attacker"), l9="TUSKENSHAMAN"),
    dict(id="O8VpcHRH", set=32, lvl=9, l3=("role", "Tank"),
         l6=("role", "Support"), l9="JARJARBINKS"),
    dict(id="Lj_hRktR", set=33, lvl=15, focused="raccoon", l3=None, l6=None, l9=None,
         members=["RACCOON", "HUMANTHUG", "GREEDO", "GAMORREANGUARD", "CADBANE"]),
    dict(id="3CGBb-Af", set=33, lvl=9, l3=("align", "Light Side"),
         l6=("cat", "Resistance"), l9="GLREY"),
    dict(id="C9xVm3l3", set=33, lvl=9, l3=("align", "Dark Side"),
         l6=("cat", "First Order"), l9="KYLORENUNMASKED"),
    dict(id="HZ5tOF3T", set=33, lvl=4, l3=("align", "Dark Side"), l6=None, l9=None),
    dict(id="bpkoYMAG", set=33, lvl=7, focused="bishop", l3=None, l6=None, l9=None,
         members=["GOPHERANTS", "CARSONTEVA"]),
    dict(id="X09cqmfA", set=32, lvl=4, l3=("role", "Tank"), l6=None, l9=None),
    dict(id="_bf0z47Y", set=33, lvl=3, l3=("align", "Light Side"), l6=None, l9=None),
    dict(id="og2nbKpD", set=33, lvl=3, l3=("align", "Dark Side"), l6=None, l9=None),
    dict(id="JfaLCYhl", set=33, lvl=3, focused="snowtroopercommander",
         l3=None, l6=None, l9=None, members=["TIEFIGHTERPILOT"]),
]

# Multiplicative uplift on a wall's hold%, by how much of the squad the cron covers.
# Anchored on this repo's own measured no-datacron baselines (durability.py):
# a well-matched cron moved Cassian UC 12.4 -> 25.1 (x2.02) and The Stranger
# 43.5 -> 49.5 (x1.14). So a full character+faction match is worth ~x1.6 at the top of
# the range and a bare alignment match almost nothing. Deliberately conservative.
UPLIFT_L9 = 0.30          # named character present
UPLIFT_L6_PER_UNIT = 0.055  # each unit covered by the faction/role tier
UPLIFT_L3_PER_UNIT = 0.018  # each unit covered by the alignment/role tier only
CAP = 1.65


def tags():
    t = json.load(open(os.path.join(DATA, "unit_tags.json")))
    return t


def covers(scope, unit, T):
    """Does `unit` fall inside this affix scope?"""
    if scope is None:
        return False
    kind, want = scope
    u = T.get(unit)
    if not u:
        return False
    if kind == "align":
        return u.get("a") == want
    if kind == "role":
        return u.get("r") == want
    return want in (u.get("c") or [])


def score(cron, units, T):
    """Uplift multiplier for putting `cron` on a squad of `units`."""
    if cron["lvl"] < 3:
        return 1.0, "unbuilt (Lvl 1) — no affixes"
    if cron.get("focused"):
        hit = [u for u in units if u in (cron.get("members") or [])]
        if not hit:
            return 1.0, f"focused/{cron['focused']} — none of its five in this squad"
        return min(CAP, 1 + UPLIFT_L9 * len(hit) / 5 + 0.05 * len(hit)), \
            f"focused/{cron['focused']} covers {len(hit)}"
    n3 = sum(covers(cron["l3"], u, T) for u in units)
    n6 = sum(covers(cron["l6"], u, T) for u in units) if cron["lvl"] >= 6 else 0
    has9 = cron["lvl"] >= 9 and cron.get("l9") in units
    # a unit covered by the L6 tier is also covered by L3; do not double-count it
    mult = 1 + UPLIFT_L3_PER_UNIT * max(0, n3 - n6) + UPLIFT_L6_PER_UNIT * n6 + (UPLIFT_L9 if has9 else 0)
    why = f"L3 {n3}/5"
    if cron["lvl"] >= 6:
        why += f", L6 {n6}/5"
    if cron["lvl"] >= 9:
        why += f", L9 {'HIT ' + cron['l9'] if has9 else 'miss'}"
    return min(CAP, mult), why


def best_assignment(squads, crons, T):
    """Exact max-weight matching (<=12 crons, <=11 squads → brute force over crons)."""
    S = len(squads)
    usable = [c for c in crons if c["lvl"] >= 3]
    M = [[score(c, s["units"], T)[0] * s["rate"] - s["rate"] for s in squads] for c in usable]
    best = (None, -1)
    idx = range(S)
    for perm in itertools.permutations(idx, min(len(usable), S)):
        tot = sum(M[i][j] for i, j in enumerate(perm) if M[i][j] > 0)
        if tot > best[1]:
            best = (perm, tot)
    perm = best[0]
    out = {}
    for i, j in enumerate(perm):
        if M[i][j] > 1e-9:
            out[j] = usable[i]
    return out, best[1]


def main():
    T = tags()
    B = json.load(open(os.path.join(DATA, "board_result.json")))
    squads = B["5v5"]["defense"]
    names = {b: (T.get(b, {}).get("n") or b) for s in squads for b in s["units"]}

    print("=" * 100)
    print("DATACRON FIT MATRIX — uplift multiplier on each wall's hold%")
    print("=" * 100)
    hdr = f"{'wall':<26}{'hold':>6}  " + "".join(f"{c['id'][:8]:>10}" for c in OWNED if c["lvl"] >= 3)
    print(hdr)
    for i, s in enumerate(squads, 1):
        lead = names.get(s["units"][0], s["units"][0])[:22]
        row = f"D{i:02d} {lead:<22}{s['rate']:>5.1f}  "
        for c in OWNED:
            if c["lvl"] < 3:
                continue
            m, _ = score(c, s["units"], T)
            row += f"{m:>10.2f}" if m > 1.001 else f"{'-':>10}"
        print(row)

    assign, gain = best_assignment(squads, OWNED, T)
    print()
    print("=" * 100)
    print(f"OPTIMAL ASSIGNMENT — total expected hold% added: +{gain:.1f} points")
    print("=" * 100)
    plan = []
    for i, s in enumerate(squads):
        c = assign.get(i)
        lead = names.get(s["units"][0], s["units"][0])
        if c:
            m, why = score(c, s["units"], T)
            eff = s["rate"] * m
            print(f"D{i+1:02d} {lead:<24} {s['rate']:>5.1f}% -> {eff:>5.1f}%   "
                  f"cron {c['id']} set{c['set']} L{c['lvl']}  ({why})")
        else:
            eff = s["rate"]
            print(f"D{i+1:02d} {lead:<24} {s['rate']:>5.1f}% -> {eff:>5.1f}%   (no cron)")
        plan.append(dict(slot=i + 1, lead=lead, units=s["units"], base=s["rate"],
                         effective=round(eff, 1),
                         cron=(c["id"] if c else None), cron_set=(c["set"] if c else None)))
    tot0 = sum(s["rate"] for s in squads)
    tot1 = sum(p["effective"] for p in plan)
    print(f"\nBOARD SUM  {tot0:.0f}%  ->  {tot1:.0f}%   (+{tot1-tot0:.0f} points of expected hold)")
    unused = [c["id"] for c in OWNED if c["lvl"] >= 3 and c not in assign.values()]
    print(f"Unused crons: {', '.join(unused) if unused else 'none'}")
    os.makedirs(OUT, exist_ok=True)
    json.dump(plan, open(os.path.join(OUT, "datacron_plan.json"), "w"), indent=1)
    print("wrote output/datacron_plan.json")


if __name__ == "__main__":
    sys.exit(main())
