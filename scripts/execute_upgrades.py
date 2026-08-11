#!/usr/bin/env python3
"""
execute_upgrades.py — slice/promote equipped mods via the HotUtils API (no browser).

Reusable executor for the mod-upgrade pipeline. Reads the latest
data/mods_full_<date>.json and drives the HotUtils mods/tier endpoint one tier-step
at a time, in the owner's stated priority order, until each binding material is
exhausted or the plan is complete.

Auth (ephemeral — never commit): pass the live session id via env:
    HU_SID=<sessionId>  [HU_UID=<apiuserid>]  python3 scripts/execute_upgrades.py [--dry]

ORDERING — one ladder, not a local guess. Importance comes from
output/invest_plan.json's `mod_priority`, i.e. Arena -> Grand Arena -> Territory
Battles -> Territory War -> fleets. The earlier version of this file rebuilt a
three-bucket defense/offense/other importance out of gac_result.json, which had two
faults: it could not see TW units at all (they are not in gac_result.json), and it
duplicated a judgement invest_plan.py already owns. Rank once, filter many times.

Plan policy (material-efficient, priority-first):
  - 6-DOT SLICE toward 6A. Each step burns the per-tier T06_0x salvage AND 10x
    T05_06, so T05_06 usually binds the whole phase. Highest value per step: 6A is
    the terminal state and the only tier calibration can touch.
  - 5-DOT SLICE toward 5A. Each step burns only its own T05_0x tier, so the four
    tiers are INDEPENDENT budgets and a mod chains through them as far as it can.
    This phase is normally wide open while the 6-dot phase is starved.
  - PROMOTE 5A->6E while T05_06 (76 each) and PROMO allow — usually zero, because
    the 6-dot phase and the promote phase compete for the same T05_06.
  - Never touches unequipped mods or filler chars. Never calibrates (see calibrate.py).

Material recipe (per one tier-step, from live diffs in memory/notes.md):
  6-dot step from tier t -> T06_0t salvage + 10x T05_06
  5-dot step from tier t -> T05_0t salvage (credits only beyond that)
  5A->6E promote         -> 76x T05_06 (binding) + 27x PROMO_T5_T6
The per-step salvage amounts below are ESTIMATES used only to size the plan. The
server is the source of truth: every call checks responseCode, and a material-out
(rc 2 / "Not enough player currency!" / GOHServiceCall Error [40]) retires just that
tier's budget and lets the other tiers keep going.
"""
import json, os, glob, sys, time, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
API = "https://api.hotutils.com/Production/"
UID = os.environ.get("HU_UID", "898a36a3-948a-4a8a-9798-7a1552b042a8")
SID = os.environ.get("HU_SID", "")
DRY = "--dry" in sys.argv

# ⚠️ A 6-DOT STEP IS A BUNDLE, NOT ONE TIER'S SALVAGE. Measured 2026-08-11 on a live
# before/after diff of a single successful step (Cad Bane 6C->6B). The earlier per-tier
# model ("a step from tier t costs T06_0t") planned two affordable runs that the server
# refused outright, because it never counted the T06_02 that EVERY step consumes.
# One data point, so treat the shape as firm and the exact counts as approximate.
STEP6_BUNDLE = {"T06_01": 10, "T06_02": 20, "T06_03": 10, "T05_05": 10, "T05_06": 10}
# 5-dot: grounded 2026-08-11 at ~22 salvage of the tier being LEFT, per step
# (512/499/514/535 of T05_01..04 bought 89 steps and drained all four).
STEP5_SALVAGE = {1: ("T05_01", 22), 2: ("T05_02", 22), 3: ("T05_03", 22), 4: ("T05_04", 22)}
STEP6_T0506 = 10      # T05_06 per 6-dot tier-step (also consumes master binding)
PROMO_T0506 = 76      # T05_06 per 5A->6E promote (binding; grounded 2026-07-27 diff)
PROMO_PROMO = 27      # PROMO_T5_T6 per promote (grounded)
MARGIN = float(os.environ.get("HU_MARGIN", "0.90"))   # plan up to this share of a binding
                      # material. 0.90 leaves slack so a mid-batch miscount cannot strand a
                      # call; set HU_MARGIN=1 on a final sweep to spend the remainder, which
                      # is safe because every call checks responseCode and stops on Error[40].
SKIP5 = "--no-5dot" in sys.argv       # 6-dot + promote only (the pre-2026-08-11 behaviour)
NEEDS = int(sys.argv[sys.argv.index("--needs") + 1]) if "--needs" in sys.argv else 0

# Where each binding material actually comes from (grounded, memory/notes.md 2026-07-27).
# Printed with the shopping list so the farming target is on the same screen as the shortfall.
FARM = {
    "T06_01": "Mod Battles Sector 9 · Guild Store · Episode Shipments",
    "T06_02": "Mod Battles Sector 9 · Guild Store · Episode Shipments",
    "T06_03": "Mod Battles Sector 9 · Guild Store · Episode Shipments",
    "T06_04": "Mod Battles Sector 9 · Guild Store · Episode Shipments",
    "T05_05": "Mod Battles Sector 9 · Guild Store · Episode Shipments",
    "T05_06": "Mod Battles Sector 9 · Guild Store · Episode Shipments (MASTER GATE)",
    "T05_01": "Mod Battles (low sectors)", "T05_02": "Mod Battles (low sectors)",
    "T05_03": "Mod Battles (low sectors)", "T05_04": "Mod Battles (low sectors)",
    "PROMO_T5_T6": "Mod Battles Sector 9 · Guild Store",
    "attenuators": "Smuggler's Run 2 (needs Jabba — owned; BEST) · Mod Battles 9 · GET3",
}


def api(path, body):
    data = json.dumps({**body, "sessionId": SID}).encode()
    req = urllib.request.Request(API + path, data=data, method="POST", headers={
        "content-type": "application/json", "apiuserid": UID,
        "origin": "https://hotutils.com", "referer": "https://hotutils.com/"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode())


def mode_of(tier):
    """Label the ladder rung a unit sits on, for the printed plan only."""
    return ("ARENA" if tier <= 3 else "GAC" if tier <= 7 else
            "TB" if tier == 8 else "TW" if tier <= 10 else "fleet")


def load():
    d = json.load(open(sorted(glob.glob(os.path.join(DATA, "mods_full_*.json")))[-1]))
    # invest_plan.py owns the ladder (Arena -> GAC -> TB -> TW -> fleets) and writes it
    # as an ORDERED list of baseIds. Its index is the only importance signal we need.
    ip = json.load(open(os.path.join(ROOT, "output", "invest_plan.json")))
    rank = {b: i for i, b in enumerate(ip["mod_priority"])}
    name = {e["unit"]: e["name"] for e in ip["priority"]}
    mode = {e["unit"]: mode_of(e["tier"]) for e in ip["priority"]}
    return d, rank, name, mode


def build_plan(d, rank, name, mode):
    """Greedy, priority-first walk: each mod climbs as far as materials allow.

    Returns (slice6, slice5, promote) where each plan entry is
    (mod, [tier_being_left, ...]) so the executor knows which material each call
    will burn and can retire exactly that budget when the server says no.
    """
    mats = d["mats"]
    mods = [m for m in d["mods"] if m["b"] and m["b"] in rank]
    for m in mods:
        m["rank"], m["name"] = rank[m["b"]], name.get(m["b"], m["b"])
        m["mode"] = mode.get(m["b"], "?")
    order = lambda seq: sorted(seq, key=lambda m: (m["rank"], -m["spd"], -m["tier"]))
    budget = {k: int(v * MARGIN) for k, v in mats.items() if isinstance(v, int)}

    def take(key, n):
        if budget.get(key, 0) < n:
            return False
        budget[key] -= n
        return True

    # --- 6-dot -> 6A. Burns the per-tier T06_0x AND the shared T05_06. ------------
    # ALL-OR-NOTHING, unlike the 5-dot phase below. T05_06 is the scarcest material on
    # the account (10 per step, and a step is unaffordable at 49 in hand), so a partial
    # run buys one random secondary bump and then STRANDS the material in a mod that
    # still cannot be calibrated — 6A is the only tier calibration accepts. Skipping a
    # mod we cannot finish and banking the remainder for the next farm strictly beats
    # that. Measured on this plan: greedy spent 4 steps for ONE 6A, all-or-nothing
    # spends the same 4 for TWO.
    slice6 = []
    for m in order(x for x in mods if x["dots"] == 6 and x["tier"] < 5):
        steps = list(range(m["tier"], 5))
        need = {k: v * len(steps) for k, v in STEP6_BUNDLE.items()}
        if any(budget.get(k, 0) < v for k, v in need.items()):
            continue
        for k, v in need.items():
            take(k, v)
        slice6.append((m, steps))

    # --- 5A -> 6E promote. Competes with the 6-dot phase for T05_06, and loses:
    # a promote costs 76 where a slice step costs 10, so slicing is planned first.
    promote = []
    for m in order(x for x in mods if x["dots"] == 5 and x["tier"] == 5):
        if take("T05_06", PROMO_T0506) and take("PROMO_T5_T6", PROMO_PROMO):
            promote.append((m, [5]))
        else:
            break

    # --- 5-dot -> 5A. Four INDEPENDENT budgets, so this phase runs even when the
    # 6-dot phase is starved on T05_06 (the usual state of this account).
    slice5 = []
    if not SKIP5:
        for m in order(x for x in mods if x["dots"] == 5 and x["tier"] < 5):
            steps = []
            for t in range(m["tier"], 5):
                key, cost = STEP5_SALVAGE[t]
                if not take(key, cost):
                    break
                steps.append(t)
            if steps:
                slice5.append((m, steps))
    return slice6, slice5, promote


def _show(title, plan, tail):
    print(f"\n=== {title}  ({len(plan)} mods, {sum(len(s) for _, s in plan)} steps) ===")
    for m, steps in plan[:25]:
        print(f"  [{m['mode']:5}] r{m['rank']:<4}{m['name'][:26]:26} spd{m['spd']:>3} "
              f"{m['dots']}dot t{m['tier']}->{tail}  ({len(steps)} steps)")
    if len(plan) > 25:
        print(f"  … +{len(plan)-25} more")


def budget_key(m, t):
    """Which budget a step draws on — the unit the executor retires on a material-out.

    The 5-dot tiers are four INDEPENDENT budgets, so running out of T05_03 must not stop
    the T05_04 work. A 6-dot step draws on one shared BUNDLE (see STEP6_BUNDLE), so the
    first refusal ends the whole 6-dot phase and there is nothing finer to retire.
    """
    if m["dots"] == 6:
        return "6dot-bundle"
    return "T05_06" if t == 5 else STEP5_SALVAGE[t][0]


def run(plan, label):
    """Execute one phase, retiring a budget as narrowly as that budget is really shared."""
    keys = {budget_key(m, t) for m, steps in plan for t in steps}
    dead, done, steps_done = set(), 0, 0
    for m, steps in plan:
        if keys <= dead:
            print("  -- every budget this phase draws on is exhausted, stopping --")
            break
        for t in steps:
            if budget_key(m, t) in dead:
                break
            r = api("mods/tier", {"modIds": [m["id"]], "getAllData": False})
            if r.get("responseCode") != 1:
                # The server does NOT name the short material — "Not enough player
                # currency!" is all we get — so report the budget, never guess the item.
                print(f"  OUT [{budget_key(m, t)}] {m['name'][:24]:24} t{t}: "
                      f"{r.get('errorMessage') or r.get('responseMessage')}")
                dead.add(budget_key(m, t))
                break
            steps_done += 1
            time.sleep(0.4)
        else:
            done += 1
            print(f"  ok  [{m['mode']:5}] {m['name'][:26]:26} {label} ({len(steps)} steps)")
    return done, steps_done


CREDITS_PER_STEP = 41_700       # measured 2026-08-11: 3,753,000 credits over 90 tier-steps


def mod_cost(m):
    """Materials to take one mod all the way to its next terminal state (6A, or 6E for
    a 5A promote, or 5A for a 5-dot). Ignores what is in stock — this is the ASK."""
    need = {}
    if m["dots"] == 6:
        steps = 5 - m["tier"]
        for k, v in STEP6_BUNDLE.items():
            need[k] = v * steps
    elif m["tier"] == 5:
        steps = 1
        need = {"T05_06": PROMO_T0506, "PROMO_T5_T6": PROMO_PROMO}
    else:
        steps = 5 - m["tier"]
        for t in range(m["tier"], 5):
            key, cost = STEP5_SALVAGE[t]
            need[key] = need.get(key, 0) + cost
    return steps, need


def needs_report(d, rank, name, mode, n):
    """The shopping list: what to farm so the NEXT n mods in ladder order can be done.

    Written for the farming trip, not the executor — it deliberately ignores the current
    stock when sizing the ask, then subtracts it at the end so the shortfall is explicit.
    """
    mods = [m for m in d["mods"] if m["b"] and m["b"] in rank and
            not (m["dots"] == 6 and m["tier"] == 5)]
    for m in mods:
        m["rank"], m["name"] = rank[m["b"]], name.get(m["b"], m["b"])
        m["mode"] = mode.get(m["b"], "?")
    mods.sort(key=lambda m: (m["rank"], -m["spd"], -m["dots"], -m["tier"]))
    head = mods[:n]

    total, steps_total, by_action = {}, 0, {}
    for m in head:
        steps, need = mod_cost(m)
        steps_total += steps
        act = ("6-dot -> 6A" if m["dots"] == 6 else
               "5A -> 6E promote" if m["tier"] == 5 else "5-dot -> 5A")
        by_action[act] = by_action.get(act, 0) + 1
        for k, v in need.items():
            total[k] = total.get(k, 0) + v

    print(f"\n=== SHOPPING LIST — next {len(head)} mods in ladder order "
          f"({steps_total} tier-steps) ===")
    print("  " + " · ".join(f"{v}× {k}" for k, v in sorted(by_action.items())))
    print(f"\n  {'material':14} {'need':>7} {'have':>7} {'SHORT':>7}   farm at")
    for k in sorted(total, key=lambda k: -(total[k] - d["mats"].get(k, 0))):
        have, short = d["mats"].get(k, 0), max(0, total[k] - d["mats"].get(k, 0))
        flag = f"{short:>7,}" if short else f"{'ok':>7}"
        print(f"  {k:14} {total[k]:>7,} {have:>7,} {flag}   {FARM.get(k,'') if short else ''}")
    print(f"  {'credits':14} {steps_total*CREDITS_PER_STEP:>7,} {d['mats']['credits']:>7,} "
          f"{'ok' if d['mats']['credits'] > steps_total*CREDITS_PER_STEP else 'SHORT':>7}")
    print("\n  Re-run `scripts/mods_session.sh` after farming — it spends whatever has arrived.")


def main():
    d, rank, name, mode = load()
    slice6, slice5, promote = build_plan(d, rank, name, mode)
    mats = d["mats"]

    print("=== MATERIALS ===")
    print("  " + "  ".join(f"{k}={mats[k]}" for k in
                           ("T06_01", "T06_02", "T06_03", "T06_04", "T05_06", "PROMO_T5_T6")))
    print("  " + "  ".join(f"{k}={mats[k]}" for k in ("T05_01", "T05_02", "T05_03", "T05_04")))
    print(f"  credits={mats['credits']:,}  attenuators={mats.get('attenuators')}")
    _show("SLICE 6-dot -> 6A", slice6, "6A")
    _show("PROMOTE 5A -> 6E", promote, "6E")
    _show("SLICE 5-dot -> 5A", slice5, "5A")
    six_a = sum(1 for m in d["mods"] if m["dots"] == 6 and m["tier"] == 5)
    full6 = sum(1 for m, s in slice6 if m["tier"] + len(s) == 5)
    print(f"\nProjected 6A: {six_a} -> {six_a + full6}   "
          f"5A completions: {sum(1 for m, s in slice5 if m['tier'] + len(s) == 5)}")

    if NEEDS:
        needs_report(d, rank, name, mode, NEEDS)

    if DRY:
        print("\n[dry run — no API calls made]")
        return
    if not SID:
        print("\nERROR: set HU_SID env var to the live sessionId to execute.")
        sys.exit(1)

    totals = {}
    for label, plan in (("->6A", slice6), ("->6E", promote), ("->5A", slice5)):
        if not plan:
            continue
        print(f"\n=== EXECUTING {label} ===")
        totals[label] = run(plan, label)
    print("\nDONE: " + " · ".join(f"{k} {v[0]} mods / {v[1]} steps" for k, v in totals.items()))


if __name__ == "__main__":
    main()
