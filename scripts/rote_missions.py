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
            # ⚠ The wiki files this under "Special"; the in-game panel reads
            # "Combat Mission — 5x characters (Relic 6+), Hondo Ohnaka" and it pays
            # Territory Points, not tokens (device-verified 2026-08-19). It is
            # therefore COMBAT and auto-battleable, which is how it was won.
            {"id": "special", "required": ["HONDO"]},
        ], [{"id": "fleet", "required": [], "preset": "Leviathan",
             "why": "Felucia is Mixed, so no alignment filter — Leviathan is legal "
                    "here and is the strongest owned fleet. Device-verified win."}]),
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


# ⭐ TACTICS — how a mission is actually PLAYED, which the requirements table does
# not tell you. Added 2026-08-19 after the Bracca Zeffo special was thrown away on
# AUTO: the requirements were right, the squad was right, and it still lost, because
# that mission cannot be auto-battled at all.
#
# THE RULE THIS TABLE ENCODES:
#   COMBAT missions  -> AUTO is fine. The community consensus for phase 2 is
#                       "mostly auto" and this account went 3-for-3 on auto.
#   SPECIAL missions -> MANUAL, always. They are fewer waves but far harder, they
#                       are ONE attempt, and they turn on ability TIMING that auto
#                       will not do. Gaming-Fans' guild ran 2-for-14 on Bracca
#                       without the turn plan below; with it, ~90.9%.
#
# `auto` is therefore keyed off `kind` in build(), and a mission only needs an entry
# here when there is a researched composition or a turn plan worth carrying.
# Sources are per-entry; re-fetch before trusting one that looks stale.
TACTICS = {
    (1, "Corellia", "special"): {
        "squad": ["QIRA", "REY", "YOUNGCHEWBACCA", "L3_37", "YOUNGHAN"],
        "note": "Qi'ra leads. starwars-fans.com/rote-special-missions/",
    },
    (2, "Felucia", "special"): {
        # The wiki files this under "Special" but it pays TERRITORY POINTS, not
        # tokens, and gaming-fans calls it a Combat Mission. Treat it as combat.
        "squad": ["BOSSK", "BOBAFETT", "FENNECSHAND", "HONDO", "EMBO"],
        "note": "Bossk-led Bounty Hunters. Get Bossk taunting and reach PAYOUT fast. "
                "Enemies have RETRIBUTION — do not AoE until it drops. Save the "
                "taunt-dispel for the Stormtrooper's taunt, dispel with Boba, then "
                "Bossk's special to mass-attack the weakest for Payout. Fennec's "
                "Armor Shred kills the Range Trooper and Recon Stormtrooper; Hondo's "
                "Captive on the Imperial Officer. A Han/Chewie/L3/Dash scoundrel "
                "lineup FAILED badly — do not use it. "
                "⚠ Hondo fills 8 platoon slots across phases 1,3,4,5,6, and Fennec "
                "has her own phase-3 combat mission: check operations before spending "
                "either. gaming-fans.com 2022/12 Phase 2 Neutral CM with Hondo.",
    },
    (2, "Bracca", "unlock_zeffo"): {
        "squad": ["CEREJUNDA", "JEDIKNIGHTCAL"],
        "manual": True,
        "note": "⛔ NEVER AUTO — measured, this repo lost the 2026-08-19 attempt to it. "
                "Waves: W1 two Purge Troopers, then an Imperial Probe Droid appears "
                "MID-WAVE and taunts; W2 Second Sister + Purge Trooper + IPD. "
                "TURN PLAN: hold the AoE dispel for the IPD taunt — do not spend it on "
                "the Purge Troopers. Stay defensive for the first 2-3 moves and use "
                "Protection Up immediately; the enemy focuses CERE and she must not "
                "drop below max protection, which is the usual failure point. Armor "
                "Shred one PT early, Cal's insta-kill on the stronger one, finish the "
                "other patiently. W2: keep boosting Cere's protection, Cal's basic "
                "dispel on the PT, stack Cal to 30 charges then ultimate the Second "
                "Sister. JKCK omicrons on BOTH the leader ability and Impetuous "
                "Assault are the difference between ~2/14 and ~90.9%. "
                "gaming-fans.com 2023/11 Unlocking Zeffo.",
    },
    (3, "Kashyyyk", "wookiee"): {
        "squad": ["TARFFUL", "CHEWBACCALEGENDARY", "CLONEWARSCHEWBACCA",
                  "C3POCHEWBACCA", "ZAALBAR"],
        "note": "5x Light Side Wookiees R7+. ⚠ The published lineup uses VANDOR CHEWBACCA, and "
                "Astra's is R5 — below the phase-3 floor, so that squad is unfillable as printed. "
                "CLONE WARS CHEWBACCA (R9) is the substitute. Caught by test_tactics_squads_are_"
                "fillable, which is why that test exists. starwars-fans.com",
    },
    (3, "Kashyyyk", "ls_1"): {
        "squad": ["GLREY", "50RT", "BENSOLO", "CALKESTIS", "GENERALKENOBI"],
        "note": "No faction gate, just 5x Light Side/Neutral R7+. Take the coherent GL Rey wall "
                "(this is TW preset D03) rather than letting auto-fill power-sort five factions.",
    },
    (3, "Kashyyyk", "ls_2"): {
        "squad": ["QUEENAMIDALA", "GRANDMASTERYODA", "MASTERQUIGON", "PADAWANOBIWAN", "SHAAKTI"],
        "note": "No faction gate. Coherent Galactic Republic/Jedi under Queen Amidala. Kept clear "
                "of JMK and GL Rey so those stay free for the other Light Side rows.",
    },
    (3, "Tatooine", "mixed"): {
        "squad": ["EMPERORPALPATINE", "GRANDADMIRALTHRAWN", "MARAJADE", "ROYALGUARD",
                  "VADERDUELSEND"],
        "note": "No gate at all on this row, so take a coherent Empire core (this is the GAC "
                "front_top #4 wall). ⚠ Do NOT reuse the Great Mothers Nightsisters here even "
                "though Dathomir looks unreachable — they are Dathomir/special's only fillable "
                "comp, and a unit can be spent once per phase. Caught by "
                "test_no_unit_is_double_booked_inside_one_phase.",
    },
    (3, "Tatooine", "jabba"): {
        "squad": ["JABBATHEHUTT", "CADBANE", "KRRSANTAN", "RACCOON", "GAMORREANGUARD"],
        "note": "⭐ KEEP BOBA FETT OUT OF THIS ROW. The Jabba and Fennec rows draw on the same "
                "Bounty Hunter/Scoundrel pool, and the published walkthrough deliberately slots "
                "CAD BANE here so Boba stays available for Fennec. These two squads are encoded "
                "DISJOINT, so the order between them no longer matters — but only because of "
                "that split. test_the_jabba_row_keeps_boba_fett_free_for_fennec pins it. "
                "Jabba summons the Rancor. W1 is Pirates opening with a Bruiser taunt: land thermal "
                "detonators and heal Krrsantan to reach payout, after which the detonators clear "
                "them one at a time. W2 is led by HONDO — have the Rancor devour him immediately. "
                "(Skiff Guard Lando from the guide is unowned; Rotta the Hutt R10 substitutes.) "
                "gaming-fans.com 2022/12 Phase 3 Neutral CM with Jabba the Hutt.",
    },
    (3, "Tatooine", "fennec"): {
        "squad": ["BOSSK", "BOBAFETT", "FENNECSHAND", "ZAMWESELL", "EMBO"],
        "note": "Bounty Hunter DoT team, 341,250 TP — the biggest single combat row in phase 3. "
                "Bossk leads and TAUNTS to build toward the BH payout; after payout the DoTs "
                "dominate and the fight becomes an outlasting exercise. W2: open with the Bossk "
                "taunt to soak while DoTs stack, kill the SHAMAN to enable another taunt, then the "
                "Brute and the Elder; the two Tusken Raiders finish off from DoT alone. "
                "⚠ R7 Fennec can die before your first turn — she is the gate, so protect her. "
                "⚠ DENGAR is in the published lineup and Astra's is R6, below the floor; ZAM "
                "WESELL and EMBO (both R8) are the substitutes. "
                "gaming-fans.com 2022/12 Phase 3 Neutral CM with Fennec Shand.",
    },
    (3, "Kashyyyk", "special"): {
        "squad": ["SAWGERRERA", "LUTHENRAEL", "CASSIANANDOR", "K2SO", "JYNERSO"],
        "manual": True,
        "note": "starwars-fans.com",
    },
    (3, "Dathomir", "special"): {
        "squad": ["GREATMOTHERS", "MORGANELSBETH", "MERRIN", "NIGHTSISTERSPIRIT",
                  "ASAJVENTRESS"],
        "manual": True,
        "note": "Great Mothers lead is the MODERN clear and the one Astra can field: all "
                "five of these are R7+, while the classic Old Daka / Mother Talzin / "
                "Nightsister Zombie lineup is stranded at R5 and below the phase-3 floor. "
                "MECHANIC: Merrin gains 100% TM the first time a Nightsister ally is "
                "defeated and +15% (+2%/relic) on every later death or revive, so letting "
                "Nightsisters die and come back IS the engine — do not play to keep them "
                "alive. Wave 1 hits hardest: spread Tenacity Down first (Zombie's basic if "
                "he is in), then stack Plague; Talzin is much stronger once Tenacity Down "
                "is out. A revive also grants all allies Instant Defeat Immunity 2 turns. "
                "starwars-fans.com 2024/10 + Xaereth youtube KfcoTSb7oQ4.",
    },
    (3, "Tatooine", "special_reva"): {
        "squad": ["GRANDINQUISITOR", "FIFTHBROTHER", "SEVENTHSISTER", "SECONDSISTER",
                  "MARROK"],
        "manual": True,
        "note": "⭐ THE REVA SHARD FARM — 1 Third Sister shard per guild win, max 50, and "
                "Third Sister is the account's #2 gap. Grand Inquisitor leads. "
                "⚠ The published comp is GI/Ninth Sister/Fifth/Seventh/Eighth Brother, but "
                "Astra's NINTH SISTER is R6 and EIGHTH BROTHER R5 — both BELOW the phase-3 "
                "relic-7 floor, so neither can be deployed. Second Sister and Marrok are "
                "R7 and substitute; Inquisitor Barriss is a third R7 option. "
                "MODS: DoT damage here scales off MAX HEALTH, so run PROTECTION primaries "
                "and de-emphasise health. "
                "W1 Jawas (Chief Nebit): get 6 stacks of Purge on Nebit, get Tenacity Up "
                "BEFORE any AoE, then cleanse with GI's middle ability once you are at "
                "6-9 DoTs — the usual loss is being greedy and holding that cleanse until "
                "the stacked DoTs wipe you at the end of the wave. Open Fifth Brother "
                "basic, Torture Nebit, Ninth/substitute uses her third; once the Jawas "
                "have buffs use Fifth Brother's AoE to dispel, then GI's AoE health-"
                "equaliser on his second turn. Nebit dies first at 10+ DoTs each. "
                "W2 is Jedi Master Kenobi ALONE and is easy if W1 went well: stack Purge "
                "to 6, add Armor Shred, layer Torture. "
                "gaming-fans.com 2022/12 Phase 3 Neutral SM (Third Sister shards).",
    },
    (3, "Tatooine", "unlock_mandalore"): {
        # starwars-fans lists "IG-12, Grogu" as two units; there is no standalone
        # Grogu — IG12 IS "IG-12 & Grogu". Caught by the baseId test.
        "squad": ["MANDALORBOKATAN", "THEMANDALORIANBESKARARMOR", "IG12",
                  "PAZVIZSLA", "CANDEROUSORDO"],
        "manual": True,
        "note": "Bo-Katan (Mand'alor) R8 + Mando (Beskar) R8 are the gate and both clear it; the "
                "remaining slots are free Mandalorians and Paz Vizsla / Canderous Ordo are the "
                "strongest at R8. 25 GUILD clears unlock Mandalore as a phase-4 bonus zone, so "
                "this row is worth running every phase it is open. starwars-fans.com",
    },
    (4, "Kessel", "special"): {
        "squad": ["BAYLANSKOLL", "SHINHATI", "MARROK", "QIRA", "L3_37"],
        "manual": True,
        "aspirational": True,
        "note": "ASPIRATIONAL — not fillable today. Qi'ra + L3-37 R8+ are the gate and both sit "
                "at R7, and the free slot Marrok is R7 against the phase-4 R8 floor too. "
                "Baylan/Shin carry it once those three clear R8. starwars-fans.com",
    },
    (5, "Vandor", "special"): {
        # Deliberately NO squad: the walkthrough every search returns for
        # "Young Han + Young Chewbacca" is the PHASE 1 CORELLIA mission, which is a
        # different fight with a different gate (R5 vs R9). Encoding it here would be
        # exactly the kind of confidently-wrong written fact verify_facts.py exists for.
        "manual": True,
        "note": "⚠ UNRESEARCHED — do not copy the Phase-1 Corellia Qi'ra/Young Han plan "
                "here, it is a different mission. Gate is YOUNGHAN + YOUNGCHEWBACCA at "
                "R9+; Astra is R7 and R5, so it is not fillable yet either way.",
    },
    (6, "Hoth", "special"): {
        "squad": ["DOCTORAPHRA", "BT1", "TRIPLEZERO", "IMPERIALPROBEDROID", "DARKTROOPER"],
        "manual": True,
        "aspirational": True,
        "note": "ASPIRATIONAL — Aphra, BT-1 and 0-0-0 are the gate and all three are R7 against "
                "the phase-6 R9 floor. ⚠ The published comp's fifth is DARTH VADER, dropped here "
                "because Death Star/vader also wants him and a unit is spendable once per phase; "
                "Dark Trooper keeps the squad Dark-Side-Droid pure, which is what actually "
                "matters. PURITY IS THE MECHANIC: Aphra only summons her Hacked Commando Droid if "
                "there is NO Galactic Legend ally and every ally is a Dark Side Scoundrel, "
                "Dark Side Droid, Krrsantan or Darth Vader — one off-faction body silently "
                "removes the summon. BT-1 and 0-0-0 each hand Aphra 50% turn meter at the "
                "start, so bringing both is a free extra opening turn. "
                "OPENER: Aphra's THIRD ability for Doubt on all enemies, which summons the "
                "Commando Droid; then BT-1's middle, then BT-1's third. BT-1's AoE is what "
                "wins it. "
                "FAILURE MODE: Stormtrooper taunts in wave 2 — hold the Imperial Probe "
                "Droid's AoE buff-removal for them rather than spending it early. "
                "⚠ Aphra fills 4 platoon slots in phase 4: check operations before "
                "spending her, losing her forfeits this mission entirely. "
                "gaming-fans.com Aphra CM walkthroughs + swgoh.gg kit.",
    },
    (6, "Death Star", "vader"): {
        "squad": ["VADER"],
        "aspirational": True,
        "note": "ASPIRATIONAL — Darth Vader SOLOS this, but at R9+ and Astra's Vader is R7. "
                "⚠ Vader is also the fifth body in the Hoth special comp; he can only be spent "
                "once in phase 6, so whichever row is played, the other loses him. Decide before "
                "the phase opens. starwars-fans.com",
    },
    (6, "Death Star", "iden"): {
        "squad": ["IDENVERSIOEMPIRE", "SUPREMELEADERKYLOREN", "DARTHMALGUS",
                  "DARTHMALAK", "SITHTROOPER"],
        "aspirational": True,
        "note": "ASPIRATIONAL — Iden is the gate at R9 and is R7; Malgus and Sith Trooper are "
                "R7 free slots against the same R9 floor. starwars-fans.com",
    },
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
                # SPECIALS ARE MANUAL. One attempt, few waves, and they turn on
                # ability timing an auto-battle will not do — see TACTICS.
                tac = TACTICS.get((phase, planet, row["mission"]))
                row["auto"] = not (row["kind"] == "special" or (tac or {}).get("manual"))
                if tac:
                    row["tactics"] = {k: v for k, v in tac.items() if k != "manual"}
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
