#!/usr/bin/env python3
"""potency_build.py — what potency can Scorch and CX-2 actually reach, and at whose expense?

The "Beset on all Sides" Legendary (Jedi Master Mace Windu) is lost on one stat. Both
gating units are already 7★ G13 R7, well past the event's R5 floor, but Scorch reads
36.0% potency and CX-2 37.5% against a ~90-100% community target — because Scorch wears
four Defense-set mods with a Defense% cross and not one potency secondary, and CX-2 wears
six Health-set mods. Neither has ever been modded for the stat.

The arithmetic below was measured off the live HotUtils dump, not assumed:

    stats.potency = baseStats[17]*100 + sum(mod potency)/100 + 15 * completed_potency_sets

  * `statValueDecimal` for a percentage stat is the percentage ×100. Flat stats use a
    different scale (×10000), which is why speed reads 140000 for +14 — counting the wrong
    stat id would report +1400pp and look like a triumph.
  * A completed potency set is 2 mods and worth exactly +15.00pp. Measured across seven
    units; PAO carries four such mods and reads +30.01pp.
  * Verified end to end: CX-2 base 0.34 + statEffects 0.03457 = 37.46, and his mods carry
    potency secondaries of 162 + 183 = 3.45pp. Mace Windu base 0.46 + 0.45604 = 91.60,
    where his mods give 30.60pp and the missing 15.00 is exactly one set bonus.

⚠️ Donor safety is the whole risk here. Ships take no mods — a fleet's strength is its
CREW's mods — so a protected set built from the literal ids in board_result.json misses
every crew member. Darth Maul holds the roster's ONLY 6-dot 30pp potency cross and crews
the Sith Infiltrator in 'Fleet - Arena'; without the crew expansion this script would
happily recommend stripping the #1 fleet. This repo has made that exact mistake before
(see memory/notes.md, "Ships take no mods — rank the CREW").
"""
import argparse
import json
import os
import re
import time

POTENCY_STAT_ID = 17          # unitStatId for Potency %
POTENCY_SET_ID = 7            # setId for the Potency set
SET_BONUS_PP = 15.0           # percentage points per completed set (2 mods, level 15)
SET_SIZE = 2
PERCENT_SCALE = 100.0         # statValueDecimal -> percentage points
MOD_SLOTS = (2, 3, 4, 5, 6, 7)
CROSS_SLOT = 7                # the only slot that can carry a potency PRIMARY

# A unit/ship baseId: upper-case letters, digits and underscores, at least three chars.
# ⚠️ The leading character MUST allow a digit: `4LOM` and `50RT` are real baseIds, and
# `4LOM` flies on 5v5 defense. An `^[A-Z]` anchor drops him from the protected set and
# the solver then reports "no squads touched" while stripping a live board squad.
# The cost of allowing a leading digit is that the board's formatted counts ("29K",
# "120K") come along too — harmless, since nothing wears mods under those names, and
# `known_ids` removes them exactly when the caller has the roster to hand.
_ID = re.compile(r"^[A-Z0-9][A-Z0-9_]{2,}$")


def potency_of(mod):
    """Potency percentage points this one mod contributes (primary + secondaries).

    Set bonuses are NOT included — they depend on the whole loadout, not one mod.
    """
    total = 0.0
    primary = mod["primaryStat"]["stat"]
    if primary["unitStatId"] == POTENCY_STAT_ID:
        total += primary["statValueDecimal"] / PERCENT_SCALE
    for secondary in mod.get("secondaryStat", []):
        if secondary["stat"]["unitStatId"] == POTENCY_STAT_ID:
            total += secondary["stat"]["statValueDecimal"] / PERCENT_SCALE
    return total


def _collect_ids(node, out):
    """Every unit-id-shaped string anywhere in the structure.

    Deliberately broad: the three source files disagree on shape (squads under a
    `units` key, bare id lists, squads nested under `opponents[].attack`), and
    over-protecting only costs candidate mods, of which there are plenty.
    """
    if isinstance(node, str):
        if _ID.match(node):
            out.add(node)
    elif isinstance(node, dict):
        for value in node.values():
            _collect_ids(value, out)
    elif isinstance(node, (list, tuple)):
        for value in node:
            _collect_ids(value, out)


def protected_units(board, arena, ship_crew, targets=(), known_ids=None):
    """Units whose mods must NOT be taken, with fleet ships expanded to their crew.

    `known_ids` (the real roster plus the crew map's ship ids) turns the id pattern
    from a guess into an exact filter. Omit it and the pattern stands alone, which
    over-collects harmlessly.
    """
    found = set()
    _collect_ids(board, found)
    _collect_ids(arena, found)

    crew_map = ship_crew.get("crew", {}) if isinstance(ship_crew, dict) else {}
    if known_ids is not None:
        found &= set(known_ids) | set(crew_map)

    for ship in list(found):
        for member in crew_map.get(ship, []):
            unit = member.get("unit") if isinstance(member, dict) else member
            if unit:
                found.add(unit)

    return found - set(targets)


def best_loadout(mods, exclude=()):
    """The highest-potency level-15 POTENCY-SET mod available in each slot.

    Restricted to `setId == POTENCY_SET_ID` deliberately. Swapping in an off-set mod
    breaks a pair and forfeits 15pp; no secondary roll in this inventory comes close
    to paying that back, so an off-set mod can only ever lose. Documented rather than
    searched, because the exhaustive version would be a lot of machinery for a choice
    that is never close.

    `exclude` holds `id()`s already claimed — Scorch and CX-2 draw from one pool.
    """
    blocked = set(exclude)
    chosen = {}
    for slot in MOD_SLOTS:
        candidates = [m for m in mods
                      if m["slot"] == slot
                      and int(m["setId"]) == POTENCY_SET_ID
                      and m.get("level") == 15
                      and id(m) not in blocked]
        if candidates:
            chosen[slot] = max(candidates, key=potency_of)
    return chosen


def projected_potency(base_pp, loadout):
    """Base potency plus the loadout's own potency plus its completed set bonuses."""
    mods = list(loadout.values())
    from_mods = sum(potency_of(m) for m in mods)
    potency_mods = sum(1 for m in mods if int(m["setId"]) == POTENCY_SET_ID)
    return base_pp + from_mods + SET_BONUS_PP * (potency_mods // SET_SIZE)


def equip_payload(unit_id, loadout):
    """One entry of `mods/task/equip`'s `units` array: `{id, modIds}`.

    Shape read off the HotUtils bundle, where `backupCurrentBaseline` builds exactly
    `{id: e.id, modIds: e.mods.map(m => m.id)}` — `id` is the unit's UUID (not baseId)
    and each modId is the mod's UUID. Slot order is pinned so a payload diff is readable.
    """
    return {"id": unit_id,
            "modIds": [loadout[slot]["id"] for slot in sorted(loadout)]}


def is_noop_response(response):
    """Did the server say "nothing to do"? The write path's safety interlock.

    Two spellings, because the answer is version-dependent. The shipped HotUtils
    bundle branches on `taskId === 0 && responseMessage === "TASK SKIPPED"`, but the
    live server answers `responseCode 2 / errorMessage "No mod actions to perform!"`.
    Only the second was ever observed (2026-08-10); trusting the bundle's string alone
    rejects a payload the server understood perfectly.

    An unresolvable payload looks different and must NOT pass — a bogus unit id comes
    back as `Unit '<id>' not found on player`, which is the case this guard exists for.
    """
    message = " ".join(str(response.get(k) or "")
                       for k in ("responseMessage", "errorMessage")).upper()
    return "TASK SKIPPED" in message or "NO MOD ACTIONS TO PERFORM" in message


def equipped_on(mod):
    """The baseId wearing this mod, or None. The `unit` field is a dict, not a string."""
    unit = mod.get("unit")
    if isinstance(unit, dict):
        return unit.get("baseId")
    return unit or None


def base_potency(unit):
    """The unit's potency in percentage points with NO mods equipped."""
    for entry in unit.get("baseStats", []):
        if entry["stat"] == POTENCY_STAT_ID:
            return entry["amount"] * 100.0
    return 0.0


def _load(path, default=None):
    try:
        with open(path, encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, ValueError):
        return {} if default is None else default


API = "https://api.hotutils.com/Production/"


def api(path, body, sid, uid):
    """POST to the HotUtils API. Auth is ephemeral — HU_SID rotates every session."""
    import urllib.request
    data = json.dumps({**body, "sessionId": sid}).encode()
    request = urllib.request.Request(
        API + path, data=data, method="POST",
        headers={"content-type": "application/json", "apiuserid": uid})
    with urllib.request.urlopen(request, timeout=120) as response:
        return json.loads(response.read().decode())


def current_loadout(unit, mods):
    """What a unit wears right now, as {slot: mod} — the restore point."""
    return {m["slot"]: m for m in mods if equipped_on(m) == unit["baseId"]}


def main(argv=None):
    parser = argparse.ArgumentParser(description="Best reachable potency, and at whose expense.")
    parser.add_argument("--unit", action="append", default=[],
                        help="baseId to solve for (repeatable); default SCORCH + OPERATIVE")
    parser.add_argument("--dump", default="output/hu_account_fresh.json")
    parser.add_argument("--board", default="data/board_result.json")
    parser.add_argument("--arena", default="output/arena_result.json")
    parser.add_argument("--crew", default="data/ship_crew.json")
    parser.add_argument("--target-potency", type=float, default=90.0,
                        help="the bar to clear (default 90, the community figure)")
    parser.add_argument("--fetch", action="store_true",
                        help="pull a fresh account/data/all into --dump first "
                             "(⚠️ account/refresh kicks the live game client)")
    parser.add_argument("--apply", action="store_true",
                        help="WRITE: equip the solved loadouts via mods/task/equip")
    parser.add_argument("--restore", metavar="PATH",
                        help="WRITE: re-equip the loadouts saved in a restore file")
    args = parser.parse_args(argv)

    sid, uid = os.environ.get("HU_SID", ""), os.environ.get(
        "HU_UID", "898a36a3-948a-4a8a-9798-7a1552b042a8")
    if (args.fetch or args.apply or args.restore) and not sid:
        parser.error("HU_SID is required for --fetch/--apply/--restore")

    if args.restore:
        saved = _load(args.restore)
        print(f"restoring {len(saved['units'])} units from {args.restore} "
              f"(captured {saved.get('captured')})")
        result = api("mods/task/equip",
                     {"units": saved["units"], "getAllData": True, "simulation": False},
                     sid, uid)
        print(json.dumps({k: result.get(k) for k in
                          ("responseCode", "responseMessage", "taskId", "errorMessage")}))
        return 0 if result.get("responseCode") == 1 else 1

    if args.fetch:
        print("account/refresh … (the live game client will drop to CONNECTION LOST)")
        api("account/refresh", {}, sid, uid)
        time.sleep(5)
        fresh = api("account/data/all", {}, sid, uid)
        with open(args.dump, "w", encoding="utf-8") as handle:
            json.dump(fresh, handle)
        age = fresh["data"]["summary"].get("gameDataAgeUtc") or "?"
        print(f"wrote {args.dump} (gameDataAge {age})\n")

    targets = args.unit or ["SCORCH", "OPERATIVE"]
    data = _load(args.dump)["data"]
    all_mods = data["mods"]["mods"]
    units = {u["baseId"]: u for u in data["units"]["units"]}
    blocked = protected_units(_load(args.board), _load(args.arena), _load(args.crew),
                              targets=targets, known_ids=set(units))

    pool = [m for m in all_mods if (equipped_on(m) or None) not in blocked]
    free = sum(1 for m in pool if equipped_on(m) is None)
    print(f"protected units : {len(blocked)} (board squads + arena + fleet crew)")
    print(f"donor pool      : {len(pool)} mods, of which {free} unassigned\n")

    claimed, verdicts, plans = set(), [], {}
    for base_id in targets:
        unit = units.get(base_id)
        if unit is None:
            print(f"{base_id}: NOT OWNED\n")
            continue
        loadout = best_loadout(pool, exclude=claimed)
        claimed |= {id(m) for m in loadout.values()}
        plans[base_id] = loadout
        now = unit["stats"]["potency"]
        projected = projected_potency(base_potency(unit), loadout)
        verdicts.append((base_id, now, projected))

        print(f"{base_id}: {now:.1f}%  ->  {projected:.1f}%   "
              f"({len(loadout)}/6 slots, {sum(1 for m in loadout.values() if int(m['setId']) == POTENCY_SET_ID) // SET_SIZE} sets)")
        for slot in MOD_SLOTS:
            mod = loadout.get(slot)
            if mod is None:
                print(f"    slot {slot}: — no potency-set mod available")
                continue
            holder = equipped_on(mod) or "FREE"
            tag = "primary+secondaries" if slot == CROSS_SLOT else "secondaries"
            print(f"    slot {slot}: {potency_of(mod):5.2f}pp  {tag:20s} from {holder}")
        print()

    print("verdict:")
    for base_id, now, projected in verdicts:
        ok = "CLEARS" if projected >= args.target_potency else "SHORT OF"
        print(f"  {base_id:10s} {now:5.1f}% -> {projected:5.1f}%  {ok} the {args.target_potency:.0f}% bar")
    donors = sorted({h for h in (equipped_on(m) for m in all_mods if id(m) in claimed) if h})
    print(f"\ndonors ({len(donors)}), none of them on a board, arena or fleet-crew squad:")
    print("  " + (", ".join(donors) if donors else "none — unassigned mods covered it"))

    if not args.apply:
        return 0

    # --- WRITE PATH ------------------------------------------------------------
    # Every unit that loses or gains a mod, so the restore point is complete.
    touched = sorted(set(targets) | set(donors))
    restore = {"captured": data["summary"].get("gameDataAgeUtc"),
               "note": "pre-potency-build loadouts; replay with --restore",
               "units": [equip_payload(units[b]["id"], current_loadout(units[b], all_mods))
                         for b in touched if b in units]}
    restore_path = "output/potency_restore.json"
    with open(restore_path, "w", encoding="utf-8") as handle:
        json.dump(restore, handle, indent=1)
    print(f"\nrestore point: {restore_path} ({len(restore['units'])} units)")

    # Shape check with a guaranteed no-op: re-equip a target's CURRENT mods. The API
    # answers "TASK SKIPPED" when the requested configuration already matches the game,
    # so a correct payload cannot change anything and a wrong one fails loudly here
    # rather than halfway through the real write.
    probe_unit = units[targets[0]]
    probe = equip_payload(probe_unit["id"], current_loadout(probe_unit, all_mods))
    checked = api("mods/task/equip",
                  {"units": [probe], "getAllData": False, "simulation": False}, sid, uid)
    print(f"payload shape check -> rc={checked.get('responseCode')} "
          f"taskId={checked.get('taskId')} msg={checked.get('errorMessage') or checked.get('responseMessage')!r}")
    if not is_noop_response(checked):
        print("ABORT: the no-op probe did not report TASK SKIPPED, so the payload shape "
              "is not confirmed. Nothing further was sent.")
        return 1

    payload = [equip_payload(units[b]["id"], plans[b]) for b in targets if b in plans]
    print(f"equipping {len(payload)} units …")
    result = api("mods/task/equip",
                 {"units": payload, "getAllData": True, "simulation": False}, sid, uid)
    print(json.dumps({k: result.get(k) for k in
                      ("responseCode", "responseMessage", "taskId", "errorMessage")}))
    return 0 if result.get("responseCode") == 1 else 1


if __name__ == "__main__":
    raise SystemExit(main())
