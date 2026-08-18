#!/usr/bin/env python3
"""
rote_missions.py — the Rise of the Empire mission MAP, phases 1-6, as data.

WHY THIS EXISTS
---------------
rote_ops.py can already pick the strongest legal squad for a mission, but it had
nothing to pick against: data/rote/ did not exist, so every RotE phase was played
by opening a panel and improvising. That is expensive in a mode where a mission is
ONE attempt and the game's auto-fill will happily spend a gated unit on a mission
that did not need it.

RotE missions are STATIC — "unlike previous Territory Battles, encounters are
static: you face the same enemies in each encounter every time" — so the whole map
can be written down once and reused every rotation. That is what this file is.

SOURCE, and how to re-check it
------------------------------
Every row below is transcribed from swgoh.wiki's Zone Information table:
  https://swgoh.wiki/wiki/Rise_of_the_Empire/Zone_Information
Cross-checked against https://swgoh.wiki/wiki/Rise_of_the_Empire for the phase
relic floors and the bonus-planet unlock rules. Re-fetch that page before editing
a row, and update SOURCE_VERIFIED.

Two transcription rules that are easy to get wrong:
  * A "Dark Side" territory accepts Dark Side OR NEUTRAL characters, and a "Light
    Side" one accepts Light Side or Neutral (gaming-fans' phase-1 walkthrough spells
    this out: "five Dark Side or Neutral characters at Relic 5+"). Only ONE owned
    unit is Neutral — Hondo Ohnaka — so this matters exactly once, but encoding it
    wrong would silently drop him.
  * A "Mixed" territory takes anything, so those rows carry NO `align` key at all.
    That is deliberate and not an omission: _mission_pool skips any unit it cannot
    find in the category catalog whenever `align` is set, and the catalog is 340
    units against a 398-unit roster. Omitting the key keeps the uncatalogued ones
    eligible, which is correct for a territory with no alignment rule.

WHY FLEETS ARE A SEPARATE LIST
------------------------------
Fleet missions are recorded under "fleets", which rote_ops does NOT read (it takes
only "missions"). This is on purpose. Ship power in this repo is a stars-only proxy,
so every owned 7* ship ties and the solver would return eight arbitrary ships that
are not a fleet — a confident, useless answer. The real decision is which of the
nine hand-built in-game presets to bring, so each row names the required ship and
the preset instead. See build_fleets.FLEET_LINEUPS.

Run:  python3 scripts/rote_missions.py --write     # -> data/rote/missions_1..6.json
      python3 scripts/rote_missions.py --phase 3   # print one phase
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROTE = os.path.join(ROOT, "data", "rote")

SOURCE = "https://swgoh.wiki/wiki/Rise_of_the_Empire/Zone_Information"
SOURCE_VERIFIED = "2026-08-18"

DS = ["Dark Side", "Neutral"]
LS = ["Light Side", "Neutral"]
SQUAD = 5

# Phase -> (relic floor, [territory, ...]). A territory is
#   (planet, alignment, [mission, ...], [fleet mission, ...])
# and a mission is a dict merged onto {"kind": "combat", "slots": 5, "gate": {...}}.
#
# `n` repeats an identical mission n times (the wiki prints "Combat x2"); the
# generator expands it into separate rows with a numeric suffix, because they are
# separate attempts that each need their own squad.
PHASES = {
    1: {"relic": 5, "territories": [
        ("Mustafar", "dark", [
            {"id": "ds", "align": DS, "n": 3},
            {"id": "vader", "align": DS, "required": ["LORDVADER"]},
        ], [{"id": "fleet", "required": [], "preset": "Leviathan"}]),
        ("Corellia", "mixed", [
            {"id": "mixed"},
            {"id": "jabba", "required": ["JABBATHEHUTT"]},
            {"id": "aphra", "required": ["DOCTORAPHRA"]},
            {"id": "special", "kind": "special", "required": ["QIRA", "YOUNGHAN"],
             "reward": "800 Mk III Guild Event Tokens"},
        ], [{"id": "fleet", "required": ["MILLENNIUMFALCONPRISTINE"], "preset": "Raddus",
             "why": "Lando's Millennium Falcon is already in the Raddus lineup."}]),
        ("Coruscant", "light", [
            {"id": "ls", "align": LS, "n": 2},
            {"id": "jedi", "align": LS, "faction": "Jedi"},
            {"id": "jedi_named", "align": LS, "faction": "Jedi",
             "required": ["MACEWINDU", "KITFISTO"]},
        ], [{"id": "fleet", "required": ["OUTRIDER"], "preset": "Home One",
             "why": "Outrider is in no built lineup — bring it inside the best Rebel "
                    "fleet and fill from Fleets > Main."}]),
    ]},
    2: {"relic": 6, "territories": [
        ("Geonosis", "dark", [
            {"id": "ds", "align": DS, "n": 3},
            {"id": "geonosians", "align": DS,
             "required": ["GEONOSIANBROODALPHA", "GEONOSIANSOLDIER", "GEONOSIANSPY",
                          "POGGLETHELESSER", "SUNFAC"]},
        ], [{"id": "fleet", "required": [], "preset": "Malevolence",
             "why": "Separatist/Geonosian fleet, all 7*."}]),
        ("Felucia", "mixed", [
            {"id": "mixed"},
            {"id": "younglando", "required": ["YOUNGLANDO"]},
            {"id": "jabba", "required": ["JABBATHEHUTT"]},
            {"id": "special", "kind": "special", "required": ["HONDO"]},
        ], [{"id": "fleet", "required": [], "preset": "Executor"}]),
        ("Bracca", "light", [
            {"id": "ls", "align": LS, "n": 4},
            {"id": "jedi", "align": LS, "faction": "Jedi"},
            # The one row on the whole map with a relic floor ABOVE its phase.
            {"id": "unlock_zeffo", "kind": "special", "slots": 2, "relic": 7,
             "required": ["CEREJUNDA", "JEDIKNIGHTCAL"],
             "reward": "2,500 Mk III tokens; 30 guild clears unlock ZEFFO (phase 3)"},
        ], [{"id": "fleet", "required": [], "preset": "Negotiator"}]),
    ]},
    3: {"relic": 7, "territories": [
        ("Dathomir", "dark", [
            {"id": "ds", "align": DS, "n": 2},
            {"id": "empire", "align": DS, "faction": "Empire"},
            {"id": "aphra", "align": DS, "required": ["DOCTORAPHRA"]},
            {"id": "special", "kind": "special", "align": DS, "faction": "Nightsister",
             "required": ["MERRIN"], "reward": "2,500 Mk II tokens"},
        ], []),
        ("Tatooine", "mixed", [
            {"id": "mixed"},
            {"id": "jabba", "required": ["JABBATHEHUTT"]},
            {"id": "fennec", "required": ["FENNECSHAND"]},
            # ⭐ The Third Sister farm. 1 Reva shard per guild victory, capped at 50.
            {"id": "special_reva", "kind": "special", "faction": "Inquisitorius",
             "required": ["GRANDINQUISITOR"],
             "reward": "1 Third Sister (Reva) shard per guild win, max 50"},
            {"id": "unlock_mandalore", "kind": "special", "faction": "Mandalorian",
             "required": ["MANDALORBOKATAN", "THEMANDALORIANBESKARARMOR"],
             "reward": "2,500 Mk II tokens; 25 guild clears unlock MANDALORE (phase 4)"},
        ], [{"id": "fleet", "required": ["CAPITALEXECUTOR"], "preset": "Executor"}]),
        ("Kashyyyk", "light", [
            {"id": "wookiee", "align": LS, "faction": "Wookiee"},
            {"id": "ls", "align": LS, "n": 2},
            {"id": "special", "kind": "special", "align": LS, "faction": "Rebel Fighter",
             "required": ["SAWGERRERA"], "reward": "2,500 Mk II tokens"},
        ], [{"id": "fleet", "required": ["CAPITALPROFUNDITY"], "preset": "(none — Profundity unowned)"}]),
        ("Zeffo", "light", [
            {"id": "ls", "align": LS},
            {"id": "force", "align": LS, "faction": "Unaligned Force User"},
            {"id": "cal", "align": LS, "required": ["JEDIKNIGHTCAL"]},
            {"id": "special", "kind": "special", "align": LS, "faction": "Clone Trooper",
             "reward": "2,500 Mk II tokens"},
        ], [{"id": "fleet", "required": ["CAPITALNEGOTIATOR"], "preset": "Negotiator"}],
         "BONUS — locked until Bracca's unlock special clears 30x in phase 2"),
    ]},
    4: {"relic": 8, "territories": [
        ("Medical Station", "dark", [
            {"id": "ds", "align": DS, "n": 4},
            {"id": "special", "kind": "special", "align": DS, "faction": "Inquisitorius",
             "required": ["THIRDSISTER"], "reward": "1,000 Mk III tokens"},
        ], []),
        ("Kessel", "mixed", [
            {"id": "mixed", "n": 2},
            {"id": "jabba", "required": ["JABBATHEHUTT"]},
            {"id": "special", "kind": "special", "required": ["QIRA", "L3_37"],
             "reward": "1,000 Mk III tokens"},
        ], [{"id": "fleet", "required": ["GHOST"], "preset": "Home One",
             "why": "Ghost is already in the Home One lineup."}]),
        ("Lothal", "light", [
            {"id": "jedi", "align": LS, "faction": "Jedi"},
            {"id": "phoenix", "align": LS, "faction": "Phoenix"},
            {"id": "ls", "align": LS},
        ], [{"id": "fleet", "required": [], "preset": "Home One"}]),
        ("Mandalore", "mixed", [
            {"id": "bokatan", "relic": 9, "required": ["MANDALORBOKATAN"]},
            {"id": "gideon", "required": ["MOFFGIDEONS3"]},
            {"id": "mixed"},
        ], [{"id": "fleet", "required": ["GAUNTLETSTARFIGHTER"], "preset": "Executor"}],
         "BONUS — locked until Tatooine's unlock special clears 25x in phase 3"),
    ]},
    5: {"relic": 9, "territories": [
        ("Malachor", "dark", [
            {"id": "ds", "align": DS, "n": 3},
            {"id": "inquisitors", "align": DS,
             "required": ["EIGHTHBROTHER", "FIFTHBROTHER", "SEVENTHSISTER"]},
        ], []),
        ("Vandor", "mixed", [
            {"id": "mixed", "n": 2},
            {"id": "jabba", "required": ["JABBATHEHUTT"]},
            {"id": "special", "kind": "special",
             "required": ["YOUNGHAN", "YOUNGCHEWBACCA"], "reward": "1,000 Mk III tokens"},
        ], [{"id": "fleet", "required": [], "preset": "Leviathan"}]),
        ("Ring of Kafrene", "light", [
            {"id": "ls", "align": LS, "n": 3},
            {"id": "rogueone", "align": LS, "required": ["CASSIANANDOR", "K2SO"]},
        ], [{"id": "fleet", "required": [], "preset": "Raddus"}]),
    ]},
    6: {"relic": 9, "territories": [
        ("Death Star", "dark", [
            {"id": "ds", "align": DS, "n": 2},
            {"id": "iden", "align": DS, "required": ["IDENVERSIOEMPIRE"]},
            {"id": "vader", "align": DS, "required": ["VADER"]},
        ], [{"id": "fleet", "required": ["TIEFIGHTERIMPERIAL"], "preset": "Chimaera",
             "why": "Imperial TIE Fighter is already in the Chimaera lineup."}]),
        ("Hoth", "mixed", [
            {"id": "mixed", "n": 2},
            {"id": "jabba", "required": ["JABBATHEHUTT"]},
            {"id": "special", "kind": "special",
             "required": ["DOCTORAPHRA", "BT1", "TRIPLEZERO"]},
        ], [{"id": "fleet", "required": [], "preset": "Executor"}]),
        ("Scarif", "light", [
            {"id": "ls", "align": LS, "n": 2},
            {"id": "rogueone_a", "align": LS,
             "required": ["BAZEMALBUS", "CHIRRUTIMWE", "SCARIFREBEL"]},
            {"id": "rogueone_b", "align": LS,
             "required": ["CASSIANANDOR", "PAO", "K2SO"]},
        ], [{"id": "fleet", "required": ["CAPITALPROFUNDITY"],
             "preset": "(none — Profundity unowned)"}]),
    ]},
}


def build(phase):
    """Expand one phase into the schema rote_ops.mission_squads() consumes."""
    spec = PHASES[phase]
    missions, fleets = [], []
    for terr in spec["territories"]:
        planet, align_kind, ground, fleet_rows = terr[0], terr[1], terr[2], terr[3]
        note = terr[4] if len(terr) > 4 else None
        for m in ground:
            for i in range(m.get("n", 1)):
                row = {"planet": planet, "alignment": align_kind,
                       "mission": m["id"] + (f"_{i + 1}" if m.get("n", 1) > 1 else ""),
                       "kind": m.get("kind", "combat"),
                       "slots": m.get("slots", SQUAD),
                       "gate": {"relic": m.get("relic", spec["relic"])}}
                for k in ("align", "faction", "required", "reward"):
                    if m.get(k):
                        row[k] = m[k]
                if note:
                    row["territory_note"] = note
                missions.append(row)
        for f in fleet_rows:
            fleets.append({"planet": planet, "mission": f["id"], "kind": "fleet",
                           "gate": {"stars": 7}, "required": f.get("required") or [],
                           "preset": f.get("preset"), "why": f.get("why")})
    return {"phase": phase, "relic_floor": spec["relic"], "source": SOURCE,
            "verified": SOURCE_VERIFIED, "missions": missions, "fleets": fleets}


def gaps(roster):
    """Every NAMED unit a mission requires that cannot currently meet its gate.

    This is the list that turns RotE from a wall into a farming plan. Only named
    `required` units are checked: a generic "5x Dark Side R9+" row is short because
    the whole roster is short, which is the relic queue's problem, not a unit gap.

    Sorted by how many relic levels away it is, because the account's shape makes
    that the whole story — 157 characters sit at exactly R7, so most locked missions
    are one or two upgrades from opening, not a farm from scratch.
    """
    import swgoh_data as sd
    own = {u["b"]: u for u in roster.get("units", [])}
    seen, out = {}, []
    for phase in sorted(PHASES):
        doc = build(phase)
        for m in doc["missions"]:
            need = (m.get("gate") or {}).get("relic")
            for base in m.get("required") or ():
                u = own.get(base)
                have = sd.displayed_relic(u) if u else None
                if u is not None and (need is None or have >= need):
                    continue
                key = (base, need)
                if key in seen:                      # same unit gates several rows
                    seen[key]["missions"].append(f"P{phase} {m['planet']}/{m['mission']}")
                    continue
                row = {"unit": base, "owned": u is not None, "have": have, "need": need,
                       "short": None if (u is None or need is None) else max(0, need - have),
                       "phase": phase,
                       "missions": [f"P{phase} {m['planet']}/{m['mission']}"]}
                seen[key] = row
                out.append(row)
    out.sort(key=lambda r: (not r["owned"], r["short"] if r["short"] is not None else 99,
                            r["phase"], r["unit"]))
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description="RotE mission map, phases 1-6")
    ap.add_argument("--write", action="store_true", help="write data/rote/missions_N.json")
    ap.add_argument("--phase", type=int, help="print one phase instead")
    ap.add_argument("--gaps", action="store_true",
                    help="which required units cannot meet their gate, cheapest first")
    args = ap.parse_args(argv)

    if args.gaps:
        import swgoh_data as sd
        roster = json.load(open(sd.latest_roster_file()))
        rows = gaps(roster)
        print(f"RotE named-unit gate gaps — roster {roster['meta'].get('pulled')}\n")
        print(f"{'unit':26s} {'have':>5} {'need':>5} {'short':>6}   unlocks")
        for r in rows:
            have = "—" if not r["owned"] else f"R{r['have']}"
            short = "UNOWNED" if not r["owned"] else f"{r['short']}"
            print(f"{r['unit']:26s} {have:>5} {'R' + str(r['need']):>5} {short:>6}   "
                  + ", ".join(r["missions"]))
        cheap = [r for r in rows if r["owned"] and r["short"] == 1]
        print(f"\n{len(cheap)} unit(s) are ONE relic level from opening a mission: "
              + ", ".join(r["unit"] for r in cheap))
        return 0

    if args.phase:
        print(json.dumps(build(args.phase), indent=1))
        return 0

    os.makedirs(ROTE, exist_ok=True)
    for phase in sorted(PHASES):
        doc = build(phase)
        ground = sum(1 for m in doc["missions"] if m["kind"] == "combat")
        special = sum(1 for m in doc["missions"] if m["kind"] == "special")
        print(f"phase {phase}  relic {doc['relic_floor']}+  "
              f"{ground:>2} combat · {special} special · {len(doc['fleets'])} fleet")
        if args.write:
            with open(os.path.join(ROTE, f"missions_{phase}.json"), "w") as f:
                json.dump(doc, f, indent=1)
    if args.write:
        print(f"\nwrote data/rote/missions_1..{max(PHASES)}.json")
    else:
        print("\n(dry run — pass --write to emit the JSON)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
