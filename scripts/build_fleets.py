#!/usr/bin/env python3
"""
build_fleets.py — grounded fleet lineups.

swgoh.gg publishes no "fleet squad" table, but /gac/ship-counters/<CAPITAL>/ lists
every observed battle as [attacker ships ...] + [defender ships ...] with Seen and
Win%. `analyse_counters()` splits those rows, so a lineup here is not a guess: it is
the ship set the meta actually flies under that capital, ordered by how often each
ship appeared (weighted by battles).

WHY THESE SIX (derived from that data — see output/fleet_matrix.txt):

  Hold (attacker win%, LOWER is better) for capitals Astra owns:
      Leviathan 82 · Executor 87 · Negotiator 89 · Chimaera 90 · Home One 90
      Endurance 92 · Executrix 92 · Raddus 94 · Malevolence 95 · Finalizer 98
      (Profundity 77 is the best in the game and is NOT owned.)

  Attack, vs the capitals people actually defend with:
      Leviathan  97% overall — 99 vs Profundity, 96 mirror, 94 vs Executor, 100 vs
                 Home One. The ONLY owned fleet that answers Profundity or a Sith
                 mirror, on 51k battles. Therefore it cannot sit on defense.
      Executor   94% — 98 vs Negotiator (11.1k) and Home One (5.2k); weak into
                 Leviathan (80) and its own mirror (72).
      Negotiator 99 vs Malevolence/Raddus, 100 vs Finalizer. NEVER point it at
                 Home One: 20% on 215 battles.

  Those three attackers cover all 11 defendable capitals with a >=94% answer, so
  offense takes them and defense takes the best of the rest. Fleets cannot share a
  ship, and the packages are faction-disjoint anyway (Chimaera and Executrix draw
  the same Imperial TIEs; Negotiator and Endurance the same Jedi/Clone ships).
"""
import collections
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CAPITALS = ["CAPITALMONCALAMARICRUISER", "CAPITALNEGOTIATOR", "CAPITALEXECUTOR",
            "CAPITALMALEVOLENCE", "CAPITALRADDUS", "CAPITALLEVIATHAN",
            "CAPITALSTARDESTROYER", "CAPITALPROFUNDITY", "CAPITALFINALIZER",
            "CAPITALCHIMAERA", "CAPITALJEDICRUISER"]

_TXT = re.compile(r"Seen ([\d.,KM]+) Win % (\d+)% Avg ([\d.]+)")


def seen_num(s):
    s = str(s).replace(",", "").strip()
    m = re.match(r"([\d.]+)([KM]?)", s)
    if not m:
        return 0.0
    v = float(m.group(1))
    return v * 1e6 if m.group(2) == "M" else v * 1e3 if m.group(2) == "K" else v


def analyse_counters(counters):
    """counters: {defending_capital: [{txt, ships}]} from /gac/ship-counters/<cap>/.

    Each row's ship list is the attacking fleet followed by the defending fleet;
    the split point is where the defending capital reappears (index > 0, so a
    mirror match splits at the second occurrence, not the first).

    Returns (matrix, atk_comp, def_comp) where matrix[(atk,def)] = {seen, win}.
    """
    matrix = collections.defaultdict(lambda: {"seen": 0.0, "wsum": 0.0})
    atk = collections.defaultdict(lambda: {"seen": 0.0, "ships": collections.Counter()})
    dfn = collections.defaultdict(lambda: {"seen": 0.0, "ships": collections.Counter()})
    for defcap, panels in counters.items():
        for p in panels:
            m = _TXT.search(p["txt"])
            if not m:
                continue
            seen, win = seen_num(m.group(1)), int(m.group(2))
            ships = p["ships"]
            split = next((i for i, x in enumerate(ships) if x == defcap and i > 0), None)
            if split is None:
                continue
            a, b = ships[:split], ships[split:]
            if not a:
                continue
            c = matrix[(a[0], defcap)]
            c["seen"] += seen
            c["wsum"] += seen * win
            atk[a[0]]["seen"] += seen
            for s in a:
                atk[a[0]]["ships"][s] += seen
            dfn[defcap]["seen"] += seen
            for s in b:
                dfn[defcap]["ships"][s] += seen
    for c in matrix.values():
        c["win"] = c["wsum"] / c["seen"] if c["seen"] else 0.0
    return matrix, atk, dfn


# Lineups: capital first, then the 3 STARTERS, then reinforcements IN CALL ORDER.
# Starters are read straight off the data (they sit at slots 0-2 in 100% of observed
# lineups). Reinforcement ORDER is not something the counter data can settle - see
# the Leviathan note below - so it is set from mechanics.
# A fleet is capital + 3 starters + up to 4 reinforcements = 8 slots.
#
# ⚠ LEVIATHAN REINFORCEMENT ORDER — Scimitar BEFORE Mark VI:
#   1. Scimitar grants allies +30 Speed (15, doubled for Sith) and the stacks SURVIVE
#      its death, so it must land early to win the race to the capital ultimate.
#   2. Mark VI wants to arrive AFTER Sabotage the Hangars, because Leviathan's unique
#      gives it +10 extra Devouring Swarm stacks on its first turn after deployment.
#   Observed GAC lineups mostly call Sith Fighter FIRST (95% of the time it holds the
#   first reinforcement slot, with Mark VI last). That is not a counter-argument, it is
#   the AI's fixed reinforcement priority showing through auto-played battles - Sith
#   Fighter outranks Scimitar on the AI's hidden tier list. It matters little in GAC
#   (Leviathan wins ~97% regardless) and a great deal in Fleet Arena, where a mirror is
#   decided by who reaches the ultimate first.
FLEET_LINEUPS = {
    "Leviathan": ["CAPITALLEVIATHAN", "FURYCLASSINTERCEPTOR", "SITHBOMBER", "TIEDAGGER",
                  "SITHINFILTRATOR", "SITHSUPREMACYCLASS", "SITHFIGHTER"],
    # Arena has no shared-ship rule, so this one can also take Emperor's Shuttle as a
    # 4th reinforcement (Chimaera holds it on the GAC board).
    "Leviathan Arena": ["CAPITALLEVIATHAN", "FURYCLASSINTERCEPTOR", "SITHBOMBER", "TIEDAGGER",
                        "SITHINFILTRATOR", "SITHSUPREMACYCLASS", "SITHFIGHTER", "EMPERORSSHUTTLE"],
    # Ebon Hawk is a thin but real Executor pick (1.8% of observed lineups) and the 8th
    # slot is otherwise empty, so it is filler rather than a recommendation.
    "Executor": ["CAPITALEXECUTOR", "HOUNDSTOOTH", "PUNISHINGONE", "RAZORCREST",
                 "XANADUBLOOD", "SLAVE1", "IG2000", "EBONHAWK"],
    "Negotiator": ["CAPITALNEGOTIATOR", "JEDISTARFIGHTERANAKIN", "BLADEOFDORIN",
                   "JEDISTARFIGHTERAHSOKATANO", "MARAUDER", "UMBARANSTARFIGHTER",
                   "YWINGCLONEWARS", "ARC170REX"],
    "Chimaera": ["CAPITALCHIMAERA", "TIEADVANCED", "TIEDEFENDER", "TIEINTERCEPTOR",
                 "SCYTHE", "TIEFIGHTERIMPERIAL", "EMPERORSSHUTTLE", "TIEBOMBERIMPERIAL"],
    "Home One": ["CAPITALMONCALAMARICRUISER", "UWINGSCARIF", "BWINGREBEL", "RAVENSCLAW",
                 "UWINGROGUEONE", "XWINGRED3", "XWINGRED2", "GHOST"],
    "Raddus": ["CAPITALRADDUS", "MILLENNIUMFALCONEP7", "COMEUPPANCE", "XWINGBLACKONE",
               "MG100STARFORTRESSSF17", "XWINGRESISTANCE", "MILLENNIUMFALCONPRISTINE"],
    # Bench: all 7*, but only 6 ships, so two reinforcement slots go empty.
    "Malevolence": ["CAPITALMALEVOLENCE", "VULTUREDROID", "HYENABOMBER",
                    "GEONOSIANSTARFIGHTER1", "GEONOSIANSTARFIGHTER2", "GEONOSIANSTARFIGHTER3"],
}

# category -> [(display name, lineup key, note)]
ASSIGNMENT = {
    "GAC Fleet - Offense": [
        ("Leviathan", "Leviathan",
         "Universal opener: 99% vs Profundity, 96% mirror, 94% vs Executor. Send at their BEST fleet."),
        ("Executor", "Executor",
         "98% vs Negotiator and Home One. Avoid Sith and BH mirrors (80%/72%)."),
        ("Negotiator", "Negotiator",
         "Mops up Malevolence/Raddus/Finalizer (99-100%). NEVER point at Home One (20%)."),
    ],
    "GAC Fleet - Defense": [
        ("Chimaera", "Chimaera", "Best hold left after offense claims Sith/BH/Jedi: 90% attacker win."),
        ("Home One", "Home One", "90% attacker win. Raven's Claw is 6* - the one weak link."),
        ("Raddus", "Raddus", "94%. MG-100 is 5*; swap in Malevolence (95%, all 7*) if that bothers you. "
                             "Endurance holds slightly better but is NOT available: 7 of its 9 ships are "
                             "the Negotiator's, which is on offense."),
    ],
    "Fleet - Arena": [
        ("Leviathan", "Leviathan Arena",
         "Best owned fleet at BOTH jobs: highest attack (97%) and best hold (82%). Arena has no "
         "shared-ship rule, so it takes Emperor's Shuttle as a 4th reinforcement and does not compete "
         "with the GAC board. CALL ORDER MATTERS HERE: Sabotage Engines - Scimitar - Sabotage Hangars - "
         "Mark VI. On AUTO you do not choose, and the AI calls Sith Fighter ahead of Scimitar, losing "
         "the race - if you auto your arena battles, drop Sith Fighter and fill with TIE Defender / "
         "Scythe / TIE Bomber, which share Scimitar's priority tier."),
    ],
}
