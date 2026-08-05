#!/usr/bin/env python3
"""
league_adjust.py — correct all-league rates to Astra's actual opposition.

THE PROBLEM. /gac/squads/ (the only LINEUP-level source, and what the board is
built from) is all-league: its 36K-120K battle counts pool Carbonite players with
Kyber players. Attackers in the lower leagues are much worse, so every wall looks
better than it will against the opponents Astra actually draws. The league filter
is NOT supported there - verified, `?league=kyber-d1` returns byte-identical rows
to a bogus league value.

The LEADER-level tier lists DO support it (`/tier-list/gac/?league=kyber-d1`, and
the same for 3v3). So the correction available is per-leader:

    league_ratio = kyber_d1_rate / all_league_rate

WHAT IT SHOWS, and why it is applied to 3v3 but barely moves 5v5:

  5v5 - the board is VALIDATED. The Stranger is #1 all-league and #1 in Kyber-D1
        (40.3%, n=6,288). Nearly every other pick RISES in rank in the correct
        population: Partagaz +16, Ahsoka +16, Jabba +13, Palpatine +10, Queen
        Amidala +9, Baylan +9, Satele +8. Nothing meaningful falls.

  3v3 - two picks genuinely collapse, on samples big enough to believe:
        Rey          rank  5 -> 19   33.2% -> 10.3%  (n=5,222)
        The Stranger rank 13 -> 28   25.2% ->  5.0%  (n=3,888)
        and one is badly underrated:
        Boss Nass    rank 48 ->  8   10.7% -> 18.1%  (n=2,579)

Absolute rates are NOT comparable across populations (everything holds less
against better attackers); the rank shift is the signal, and the ratio is how it
gets applied.

Ratios compose with the datacron durability ratio, so the product is clamped:
each factor is a noisy estimate and 0.5 x 0.5 would over-correct.
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "data", "meta", "raw_tierlist_kyberd1_20260805.json")

MIN_N = 1000          # Kyber-D1 samples run 70-13K; below this it is noise
CLAMP = (0.30, 1.30)  # bound on league_ratio x durability_ratio combined
_KEY = {("5v5", "def"): "d5", ("3v3", "def"): "d3"}


def _n(s):
    s = str(s).replace(",", "")
    try:
        if s.endswith("K"):
            return float(s[:-1]) * 1e3
        if s.endswith("M"):
            return float(s[:-1]) * 1e6
        return float(s)
    except ValueError:
        return 0.0


def load():
    """{(fmt,'def'): {leader: {all, kd1, n, ratio}}}"""
    raw = json.load(open(SRC))
    if isinstance(raw, str):
        raw = json.loads(raw)
    out = {}
    for key, k in _KEY.items():
        allx = {r["leader"]: r for r in raw.get(k, []) if r.get("rate") is not None}
        kd1 = {r["leader"]: r for r in raw.get(k + "_k1", []) if r.get("rate") is not None}
        t = {}
        for leader, a in allx.items():
            b = kd1.get(leader)
            if not b or not a["rate"] or _n(b["battles"]) < MIN_N:
                continue
            t[leader] = {"all": a["rate"], "kd1": b["rate"], "n": b["battles"],
                         "ratio": b["rate"] / a["rate"]}
        out[key] = t
    return out


# ---------------------------------------------------------------------------
# WHY THE GLOBAL RE-WEIGHTING WAS BUILT AND THEN SWITCHED OFF
#
# league_ratio = kyber_d1_leader_avg / all_league_leader_avg confounds two things:
#   (1) population skill  - what we want
#   (2) BUILD MIX         - what we do not
# The all-league "Rey" row in 5v5 averages 531 DIFFERENT BUILDS over 15.2K battles
# and reads 9.6%; the Kyber-D1 row averages 57 builds and reads 20.9%. Rey does not
# get better against better opponents - the low-league average is simply dragged
# down by hundreds of junk Rey builds nobody at Kyber plays. Applying that 2.18x to
# one specific good lineup (Rey/50R-T/Ben Solo/Cal/GK, measured at 31%) made it the
# #1 wall on the board off pure artifact.
#
# It cannot be repaired by normalising, because the board is LINEUP-level and every
# available league-filtered number is LEADER-level. So the global multiplier is off.
# What survives is an explicit allow-list: cases where the Kyber-D1 signal is large,
# well-sampled, in the expected direction (walls hold WORSE against better
# attackers), and CORROBORATED by a second independent line of evidence.
APPLY_GLOBAL = False

KYBER_OVERRIDES = {
    # (fmt, leader): (ratio, note)
    ("3v3", "Rey"): (
        0.31,
        "Kyber-D1 10.3% vs 33.2% all-league (n=5,222) — and the build's Luminara "
        "Unduli carries a Set 30 FOCUSED datacron expiring 2026-08-06. Two "
        "independent reasons this wall does not hold at Astra's level."),
}


def median_ratio(table):
    """Population prior for leaders with no trustworthy Kyber-D1 sample."""
    vals = sorted(e["ratio"] for e in table.values())
    if not vals:
        return 1.0
    m = len(vals) // 2
    return vals[m] if len(vals) % 2 else (vals[m - 1] + vals[m]) / 2


def ratio(table, leader_name, fmt=None):
    """(league_ratio, note).

    Only the explicit KYBER_OVERRIDES bite. Everything else returns 1.0 with a
    note, so the Kyber-D1 divergence is still REPORTED in the playbook without a
    confounded multiplier reordering the board.
    """
    if (fmt, leader_name) in KYBER_OVERRIDES:
        return KYBER_OVERRIDES[(fmt, leader_name)]
    e = table.get(leader_name)
    if not e:
        return 1.0, None
    if e["ratio"] < 0.75:
        return 1.0, (f"⚠ Kyber-D1 only {e['kd1']}% vs {e['all']}% all-league "
                     f"(n={e['n']}) — expect under the number shown")
    return 1.0, None


def combine(league_ratio, durability_ratio):
    return max(CLAMP[0], min(CLAMP[1], league_ratio * durability_ratio))
