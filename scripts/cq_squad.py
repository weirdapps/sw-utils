#!/usr/bin/env python3
"""Answer Conquest composition questions from the roster + unit tag table.

Nine of the ten Conquest boss/mini-boss nodes carry composition-locked feats
("win with no Tanks", "only Dark Side", "a full Bad Batch squad", "no Jedi, Sith or
Unaligned Force Users"). Guessing a role costs a whole battle: Kylo Ren (Unmasked)
looks like an attacker and is a Tank, which is exactly how the Sector 1 "Unguarded"
feat was missed.

    python3 scripts/cq_squad.py --category "First Order" --not-role Tank
    python3 scripts/cq_squad.py --align "Dark Side" --top 10
    python3 scripts/cq_squad.py --who SUPREMELEADERKYLOREN KYLOREN
    python3 scripts/cq_squad.py --not-category Jedi Sith "Unaligned Force User"
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import swgoh_data as sd  # noqa: E402

TAGS = json.load(open(os.path.join(HERE, "..", "data", "unit_tags.json")))


def roster():
    d = json.load(open(sd.latest_roster_file()))
    out = {}
    for u in d["units"]:
        rt = u.get("rt")
        out[u["b"]] = {
            "n": u["n"],
            "g": u.get("g") or 0,
            "relic": max(0, rt - 2) if isinstance(rt, int) else -1,
            "stars": u.get("r") or 0,
            "gp": u.get("gp") or 0,
        }
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--category", action="append", default=[],
                    help="must carry this category (repeatable, AND)")
    ap.add_argument("--not-category", nargs="*", default=[],
                    help="must carry none of these categories")
    ap.add_argument("--role", action="append", default=[], help="must be one of these roles")
    ap.add_argument("--not-role", action="append", default=[], help="must not be these roles")
    ap.add_argument("--align", help="Light Side / Dark Side / Neutral")
    ap.add_argument("--min-gear", type=int, default=13)
    ap.add_argument("--top", type=int, default=15)
    ap.add_argument("--who", nargs="*", help="just print these base ids")
    a = ap.parse_args()

    ros = roster()

    if a.who:
        for b in a.who:
            t, r = TAGS.get(b), ros.get(b)
            if not t:
                print(f"{b:<26} NOT IN TAG TABLE")
                continue
            own = f"G{r['g']} R{r['relic']} {r['stars']}*" if r else "NOT OWNED"
            print(f"{t['n']:<30} {t['r']:<8} {t['a']:<10} {own}  {t['c']}")
        return

    rows = []
    for b, t in TAGS.items():
        r = ros.get(b)
        if not r or r["g"] < a.min_gear:
            continue
        cats = set(t["c"])
        if any(c not in cats for c in a.category):
            continue
        if any(c in cats for c in a.not_category):
            continue
        if a.role and t["r"] not in a.role:
            continue
        if t["r"] in a.not_role:
            continue
        if a.align and t["a"] != a.align:
            continue
        rows.append((r["relic"], r["gp"], t["n"], t["r"], b))

    rows.sort(reverse=True)
    print(f"{len(rows)} owned units match (gear >= {a.min_gear}), best relic first:")
    for relic, gp, name, role, b in rows[:a.top]:
        print(f"  {name:<32} {role:<8} R{relic:<2} {gp:>6}  {b}")


if __name__ == "__main__":
    main()
