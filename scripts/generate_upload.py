#!/usr/bin/env python3
"""
generate_upload.py — data/board_result.json -> HotUtils payload + playbook.

Outputs into output/:
  upload_payload.json   compact [{n,sz,ct,cat,u:[[baseId,name],...]}] for upload_hotutils.py
  playbook.html         the human-readable plan

HotUtils categories become filter groups in the app, so they are the unit of
organisation the player actually sees:
  GAC 5v5 - Defense/Offense · GAC 3v3 - Defense/Offense
  TW 5v5 - Defense/Offense · GAC Fleet - Defense/Offense · Fleet - Arena
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import swgoh_data  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
OUT = os.path.join(ROOT, "output")

res = json.load(open(os.path.join(DATA, "board_result.json")))
roster = json.load(open(swgoh_data.latest_roster_file()))
placement = json.load(open(os.path.join(OUT, "gac_placement.json")))
_dcplan = json.load(open(os.path.join(OUT, "datacron_plan.json")))
# datacron_plan.json is now keyed by format; each entry lists one row per
# defensive slot in board order.
crons = {(f, tuple(r["units"])): r for f, rows in _dcplan.items() for r in rows}

# Which map zone each defensive squad belongs in. A defense list is useless without
# this: the board is two gated lanes, not eleven interchangeable slots, and the name
# is the only thing the player sees while placing in-game.
ZONE_TAG = {"front_top": "FT", "front_bottom": "FB", "back_bottom": "BB", "back_fleet": "SHIP"}
ZONE_OF = {}
for _fmt in ("5v5", "3v3"):
    for _zk, _sqs in placement[_fmt]["zones"].items():
        if _zk == "back_fleet":
            continue
        for _i, _s in enumerate(_sqs, 1):
            ZONE_OF[(_fmt, tuple(_s["units"]))] = f"{ZONE_TAG[_zk]}{_i}"
info = {u["b"]: u for u in roster["units"]}
namemap = json.load(open(os.path.join(DATA, "name_type_map.json")))


def name(b):
    u = info.get(b)
    return u["n"] if u else namemap.get(b, {}).get("n", b)


def relic(b):
    """Displayed relic level. The roster's `rt` is two tiers above what the game
    shows (device-verified), so R-level = rt - 2."""
    u = info.get(b)
    if not u:
        return "?"
    rt = u.get("rt") or 0
    if u.get("ct") == 2:
        return f"{u['r']}★"
    return f"R{rt - 2}" if rt >= 3 else f"G{u['g']}"


# short leader labels for squad names (HotUtils lists get long fast)
LBL = {"STRANGER": "The Stranger", "GLREY": "GL Rey", "LORDVADER": "Lord Vader",
       "CASSIANUNDERCOVER": "Cassian UC", "BAYLANSKOLL": "Baylan", "EMPERORPALPATINE": "Palpatine",
       "JABBATHEHUTT": "Jabba", "SATELESHAN": "Satele", "MAJORPARTAGAZ": "Partagaz ISB",
       "GLAHSOKATANO": "GL Ahsoka", "FINN": "Res Finn", "QUEENAMIDALA": "Q Amidala",
       "GLLEIA": "GL Leia", "SUPREMELEADERKYLOREN": "SLKR", "JEDIMASTERKENOBI": "JMK",
       "DARTHTRAYA": "Triumvirate", "DARTHNIHILUS": "Nihilus", "DARTHMALGUS": "Malgus",
       "DOCTORAPHRA": "Aphra", "BOSSNASS": "Gungans", "SITHPALPATINE": "SEE",
       "DARTHBANE": "Bane", "GRANDMASTERLUKE": "JML", "GENERALSKYWALKER": "GAS 501st",
       "MANDALORBOKATAN": "Bo-Katan Mandos", "GREATMOTHERS": "Great Mothers", "WAMPA": "Wampa",
       "ADMIRALRADDUS": "Raddus", "DASHRENDAR": "Dash BAM", "CEREJUNDA": "Cere",
       "DARTHREVAN": "Darth Revan", "STORMTROOPERLUKE": "Endor Luke", "JANGOFETT": "Jango BH",
       "MONMOTHMA": "Mon Mothma", "SAWGERRERA": "Saw Rebels", "GRANDMOFFTARKIN": "Tarkin",
       "MOFFGIDEONS3": "DT Gideon", "COMMANDERLUKESKYWALKER": "CLS", "HERASYNDULLA": "Hera Ghost",
       "OMEGAS3": "Bad Batch", "GENERALGRIEVOUS": "Grievous Droids", "CAPTAINENOCH": "Enoch",
       "UGNAUGHT": "Ugnaught", "PADMEAMIDALA": "Padme", "JEDIKNIGHTLUKE": "JKL",
       "MASTERQUIGON": "Master Qui-Gon"}


def lbl(b):
    return LBL.get(b, name(b))


WHY = {
    "STRANGER": "The #1 wall in the game — holds a full battle against most attackers",
    "GLREY": "Strong hold vs non-GL squads and mirrors", "LORDVADER": "Culls squishies, punishes turn meter",
    "CASSIANUNDERCOVER": "Andor wall; strong vs droids, rebels and GLs",
    "BAYLANSKOLL": "Thorny Ronin wall; punishes greedy attacks",
    "EMPERORPALPATINE": "Imperial staller; anti-Jedi, drags the clock",
    "JABBATHEHUTT": "Sticky cartel; enormous health pool", "SATELESHAN": "Tanky Jedi/Old-Republic wall",
    "MAJORPARTAGAZ": "ISB wall; strong vs droids and rebels",
    "GLAHSOKATANO": "Punishes AoE and isolation", "FINN": "Resistance staller; cheap last-node filler",
    "QUEENAMIDALA": "Anti-Sith / anti-DoT staller", "DARTHREVAN": "Sith stall vs squishy attackers",
    "STORMTROOPERLUKE": "Endor Rebel wall; cheap depth", "GREATMOTHERS": "Revive spam; eats weak attackers",
    "JANGOFETT": "Bounty Hunter wall; contract pressure", "MONMOTHMA": "Rebel-leader staller",
    "SAWGERRERA": "Rebel Fighter wall", "GENERALGRIEVOUS": "Droid wall; endless respawn",
    "MANDALORBOKATAN": "Mandalorian wall vs Nightsisters/DoT",
    "GLLEIA": "The #1 attacker in the game — beats almost anything, GLs included",
    "SUPREMELEADERKYLOREN": "Solo-smashes isolated leads and squishy GLs",
    "JEDIMASTERKENOBI": "Premier hammer; beats most metas including many GLs",
    "GRANDMASTERLUKE": "Tanky cleaner; Rebels and Jedi mirrors",
    "SITHPALPATINE": "Anti-GL; drains and bursts — clears 3v3 nodes almost solo",
    "DARTHBANE": "Unit-efficient 2-man cleaner", "DARTHMALGUS": "Anti-Jedi / anti-tank Sith burst",
    "DARTHTRAYA": "Sith Triumvirate; anti-tank / anti-Jedi",
    "DOCTORAPHRA": "Droid burst; excellent into GL Ahsoka and clones",
    "BOSSNASS": "Gungan wall-breaker", "GENERALSKYWALKER": "Clone hammer; punishes non-burst teams",
    "WAMPA": "One-unit cheese; takes a weak node for free",
    "ADMIRALRADDUS": "Rebel burst", "DASHRENDAR": "Scoundrel burst",
    "CEREJUNDA": "Jedi burst; the JKL-team counter", "JEDIKNIGHTLUKE": "Jedi cleaner",
    "MOFFGIDEONS3": "Imperial Remnant burst", "COMMANDERLUKESKYWALKER": "Classic Rebel cleaner",
    "HERASYNDULLA": "Ghost-crew clear", "OMEGAS3": "Bad Batch clear", "UGNAUGHT": "Cheap 3-unit clear",
    "PADMEAMIDALA": "Galactic Republic stall-and-burn", "CAPTAINENOCH": "Night Trooper clear",
    "GRANDMOFFTARKIN": "Imperial clear",
}


def why(sq):
    base = WHY.get(sq["units"][0], "Meta pick")
    if sq.get("discount"):
        base += f" &#8212; &#9888; {sq['discount']}"
    return base


def durability(sq):
    """A short 'is this rate rented?' cell for each squad."""
    exp = sq.get("expiring") or []
    if exp:
        e = exp[0]
        return (f"<span style='color:#b45309;font-weight:bold;'>RENTED</span><br>"
                f"<span style='font-size:9pt;color:#6a6a6a;'>{int(e['coverage'] * 100)}% "
                f"{e['tag']} &#8212; cron gone in ~{e['days']}d</span>")
    lean = [e for e in (sq.get("datacron") or []) if e["coverage"] >= 0.5]
    if lean:
        e = lean[0]
        return (f"<span style='color:#2f6f3e;'>holds ~{e['days']}d</span><br>"
                f"<span style='font-size:9pt;color:#6a6a6a;'>{int(e['coverage'] * 100)}% {e['tag']}</span>")
    return "<span style='color:#2f6f3e;'>OWNED</span><br><span style='font-size:9pt;color:#6a6a6a;'>no cron lean</span>"


BOILER = {"hasOmicron": False, "hasZeta": False, "hasUltimate": False,
          "filters": {"minGP": 1000, "gear": 0, "relic": 0, "stars": 2},
          "subsPriority": "order"}

payload = []


def add(nm, cat, units, combat):
    payload.append({"n": nm, "sz": len(units), "ct": combat, "cat": cat,
                    "u": [[b, name(b)] for b in units]})


SECTIONS = [("5v5", "GAC 5v5"), ("3v3", "GAC 3v3"), ("tw", "TW 5v5")]
for key, prefix in SECTIONS:
    for persp, p in (("defense", "D"), ("offense", "O")):
        cat = f"{prefix} - {persp.capitalize()}"
        for i, sq in enumerate(res[key][persp], 1):
            tag = "3v3" if key == "3v3" else ("TW" if key == "tw" else "5v5")
            zone = ZONE_OF.get((key, tuple(sq["units"])))
            slot = zone if (persp == "defense" and zone) else f"{p}{i:02d}"
            nm = f"{tag} {slot} {lbl(sq['units'][0])} {sq['rate']:.0f}%"
            # A wall without its datacron is a different wall. Carry the cron in the
            # name so the right one gets attached at placement time — Astra shipped
            # 7 of 11 walls with no cron at all while the opponent ran 8 of 8.
            c = crons.get((key, tuple(sq["units"])))
            if persp == "defense" and c and c.get("cron"):
                nm += f" [s{c['cron_set']}]"
            add(nm, cat, sq["units"], 1)

for cat, arr in res["fleets"].items():
    for i, f in enumerate(arr, 1):
        p = "D" if "Defense" in cat else ("O" if "Offense" in cat else "A")
        nm = f"Fleet {p}{i} {f['name']}" if p != "A" else f"Arena Fleet {f['name']}"
        add(nm, cat, f["units"], 2)

os.makedirs(OUT, exist_ok=True)
json.dump(payload, open(os.path.join(OUT, "upload_payload.json"), "w"), separators=(",", ":"))

# ---------------------------------------------------------------- playbook ---
H = "font-family:'Aptos','Segoe UI',Arial,sans-serif;color:#404040;"


def cells(units):
    out = []
    for j, b in enumerate(units):
        s, e = ("<b>", "</b>") if j == 0 else ("", "")
        out.append(f"{s}{name(b)} <span style='color:#8a8a8a'>{relic(b)}</span>{e}")
    return " &#8226; ".join(out)


def table(title, rows, ratehdr, sub=""):
    h = (f"<div style='font-size:15pt;font-weight:bold;color:#16324f;margin:22px 0 4px 0;"
         f"border-bottom:2px solid #16324f;padding-bottom:3px;'>{title}</div>")
    if sub:
        h += f"<div style='color:#6a6a6a;font-size:10pt;margin-bottom:8px;'>{sub}</div>"
    h += "<table style='border-collapse:collapse;width:100%;font-size:10.5pt;'><tr>"
    for c in ["#", "Squad (leader first)", ratehdr, "Durability", "Why"]:
        h += (f"<th style='background:#d9f2d0;color:#404040;text-align:left;padding:6px 9px;"
              f"border:1px solid #bcdcb0;font-weight:bold;'>{c}</th>")
    h += "</tr>"
    for i, sq in enumerate(rows, 1):
        h += (f"<tr><td style='padding:6px 9px;border:1px solid #d9d9d9;text-align:center;vertical-align:top;'>{i}</td>"
              f"<td style='padding:6px 9px;border:1px solid #d9d9d9;vertical-align:top;'>{cells(sq['units'])}</td>"
              f"<td style='padding:6px 9px;border:1px solid #d9d9d9;text-align:center;vertical-align:top;white-space:nowrap;'>"
              f"<b>{sq['rate']:.0f}%</b><br><span style='color:#8a8a8a;font-size:9pt;'>n={sq['seen']}</span></td>"
              f"<td style='padding:6px 9px;border:1px solid #d9d9d9;vertical-align:top;white-space:nowrap;'>{durability(sq)}</td>"
              f"<td style='padding:6px 9px;border:1px solid #d9d9d9;vertical-align:top;'>{why(sq)}</td></tr>")
    return h + "</table>"


def fleet_table(title, arr, sub=""):
    h = (f"<div style='font-size:15pt;font-weight:bold;color:#16324f;margin:22px 0 4px 0;"
         f"border-bottom:2px solid #16324f;padding-bottom:3px;'>{title}</div>")
    if sub:
        h += f"<div style='color:#6a6a6a;font-size:10pt;margin-bottom:8px;'>{sub}</div>"
    h += "<table style='border-collapse:collapse;width:100%;font-size:10.5pt;'><tr>"
    for c in ["Fleet", "Capital &#8594; 3 starters &#8594; reinforcements (in order)", "How to use it"]:
        h += (f"<th style='background:#d9f2d0;text-align:left;padding:6px 9px;"
              f"border:1px solid #bcdcb0;font-weight:bold;'>{c}</th>")
    h += "</tr>"
    for f in arr:
        warn = ""
        if f["understarred"]:
            warn = (f"<br><span style='color:#b45309;font-size:9pt;'>&#9888; under-starred: "
                    f"{', '.join(f['understarred'])}</span>")
        u = f["units"]
        line = (f"<b>{name(u[0])}</b> &#8594; " + " &#8226; ".join(name(b) for b in u[1:4])
                + " &#8594; " + " &#8226; ".join(name(b) for b in u[4:]))
        h += (f"<tr><td style='padding:6px 9px;border:1px solid #d9d9d9;vertical-align:top;white-space:nowrap;'><b>{f['name']}</b></td>"
              f"<td style='padding:6px 9px;border:1px solid #d9d9d9;vertical-align:top;'>{line}{warn}</td>"
              f"<td style='padding:6px 9px;border:1px solid #d9d9d9;vertical-align:top;'>{f['note']}</td></tr>")
    return h + "</table>"


def gap_table(fmt):
    rows = ""
    for persp, label in (("def", "DEFENSE"), ("off", "OFFENSE")):
        for it in res[fmt]["gaps"][persp][:6]:
            rows += (f"<tr><td style='padding:4px 9px;border:1px solid #d9d9d9;'>{fmt} {label}</td>"
                     f"<td style='padding:4px 9px;border:1px solid #d9d9d9;text-align:center;'>{it['rate']}%</td>"
                     f"<td style='padding:4px 9px;border:1px solid #d9d9d9;'>{name(it['units'][0])}</td>"
                     f"<td style='padding:4px 9px;border:1px solid #d9d9d9;color:#b45309;'>"
                     f"{', '.join(name(b) for b in it['missing'])}</td></tr>")
    return rows


m = res["meta"]
html = f"""<div style="{H}font-size:12pt;max-width:1040px;">
<div style='font-size:20pt;font-weight:bold;color:#16324f;'>SWGOH Competitive Board &#8212; Astra</div>
<div style='color:#6a6a6a;margin:4px 0 14px 0;'>ally 145357294 &#8226; {m['gp']:,} GP &#8226; 9 Galactic Legends
&#8226; Kyber 3 &#8594; Kyber 2 &#8226; built {m['pulled']}<br>
<b>Grounded in:</b> live comlink roster + swgoh.gg GAC meta (5v5 {m['season_5v5']} / 3v3 {m['season_3v3']},
Hold% and Win%) + /gac/ship-counters battle data. Every unit owned and G13+; no unit repeats within a mode.</div>
<div style='background:#f4f7f4;border:1px solid #d9e6d4;border-radius:6px;padding:10px 14px;margin-bottom:8px;'>
<b>How the squads were chosen.</b> Not "best Hold% first". A GAC round is decided on net banners, so the board
maximises <i>&Sigma;&nbsp;P(defense holds) + &Sigma;&nbsp;P(offense clears)</i> as one exact optimisation over
every squad you can field, with no unit used twice. That is what stops an 18%-hold wall from eating the units
of a 90%-win attacker.<br>
<b>Defense vs offense split of the 9 GLs:</b> JMK, JML, SEE and SLKR are attack-only (they defend poorly and a
defensive placement strands their support). The rest are placed by the optimiser.</div>

<div style='background:#fff7ed;border:1px solid #fed7aa;border-radius:6px;padding:10px 14px;margin-bottom:8px;'>
<div style='font-weight:bold;color:#b45309;font-size:13pt;margin-bottom:4px;'>&#9888; Read this before you trust any percentage: what is rented and what is owned</div>
Every Hold%/Win% on this page was measured <i>last season, under the datacrons that were live then</i>.
Four sets are live right now (swgoh.gg/datacrons, read 2026-08-05). Only the faction and role tiers tell
squads apart — the Light Side / Dark Side tiers apply to everyone:
<table style='border-collapse:collapse;margin:8px 0;font-size:10pt;'>
<tr><th style='text-align:left;padding:3px 10px 3px 0;'>Set</th><th style='text-align:left;padding:3px 10px 3px 0;'>Expires</th><th style='text-align:left;padding:3px 0;'>Who it buffs</th></tr>
<tr><td style='padding:2px 10px 2px 0;'>30 &nbsp;Peace &amp; Power</td><td style='padding:2px 10px 2px 0;color:#b45309;font-weight:bold;'>~1 DAY</td><td>Sith &nbsp;|&nbsp; Galactic Republic</td></tr>
<tr><td style='padding:2px 10px 2px 0;'>31 &nbsp;For Old Times</td><td style='padding:2px 10px 2px 0;'>~4 weeks</td><td>Old Republic &nbsp;|&nbsp; Separatist</td></tr>
<tr><td style='padding:2px 10px 2px 0;'>32 &nbsp;Necessary Means</td><td style='padding:2px 10px 2px 0;'>~1 month</td><td>Healer &nbsp;|&nbsp; Tank &nbsp;|&nbsp; Attacker &nbsp;|&nbsp; Support</td></tr>
<tr><td style='padding:2px 10px 2px 0;'>33 &nbsp;Supremacy Directive</td><td style='padding:2px 10px 2px 0;'>~2 months</td><td>Resistance &nbsp;|&nbsp; First Order</td></tr>
</table>
<b>Finding 1 — the faction tiers.</b> When set 30 lapses, no live set grants a Sith or Galactic Republic
<i>faction</i> bonus. They keep the Light/Dark Side tier (set 33 carries it) and set 32's role tiers, so it is
one tier lost, not a blackout.<br><br>
<b>Finding 2 — the one that actually moved this board: FOCUSED datacrons.</b> Set 30 also carries four
<i>character-specific</i> datacrons, verified from its variant list:
<b>Cassian Andor (Undercover) · Darth Revan · Dedra Meero · Luminara Unduli</b> — all expiring 2026-08-06,
non-rerollable. A focused cron keys off one named character, so no faction or role heuristic can see it.
Three of those four sit on this roster's board.<br><br>
<b>How much of each rate is rented — measured, not guessed.</b> swgoh.gg's squad tier lists publish, per
leader, the rate from the battles where <i>no L9 datacron applied</i>. That is a real counterfactual, and
ratio = baseline ÷ headline says how much of a rate is owned. Worked example:
<b>Cassian Andor (Undercover) reads 25.1% in 5v5 and 28.9% in 3v3, but his no-datacron baselines are 12.4%
and 7.8%</b> — ratios of 0.49 and 0.27, agreeing across two independent formats. His wall was dropped from
the 5v5 board as a result. By contrast <b>Queen Amidala's baseline (30.8%) is HIGHER than her headline
(25.3%)</b>, so her wall was promoted.<br><br>
<b>Applied to defense only, on evidence.</b> Measured offense ratios all land between 0.87 and 1.04 — an
attacker already winning 90% is not being carried by a datacron. Defense ratios run 0.35 to 1.15. Defense is
also the side you cannot adapt: it is set once and then attacked by whoever turns up.
<i>(An earlier faction-tag version of this correction was tried and thrown away — it could not see focused
crons at all, and its haircut scrambled the board rather than ranking it.)</i><br><br>
<b>One more population caveat, reported not priced in.</b> The lineup-level source
(<code>/gac/squads/</code>) is <i>all-league</i> and does not honour a league filter — it pools Carbonite
players with Kyber ones, and weaker attackers make every wall look better than it will for you. The
leader-level tier lists <i>can</i> be filtered to Kyber-D1, and where that says a wall does materially worse
it is flagged <b>⚠ Kyber-D1</b> in the Why column below. It is not applied as a multiplier because the ratio
confounds population skill with <i>build mix</i>: the all-league "Rey" 5v5 row averages 531 different builds
and reads 9.6%, the Kyber-D1 row averages 57 and reads 20.9% — Rey does not improve against better players,
the low-league average is just full of junk builds. One exception is applied, where two independent lines of
evidence agree: the <b>3v3 Rey / Ben Solo / Luminara</b> wall reads 10.3% at Kyber-D1 (n=5,222) <i>and</i>
loses Luminara's focused datacron tomorrow. It was demoted from #2 to #13.</div>
"""
html += table("GAC 5v5 &#9679; DEFENSE &#8212; set all 11",
              res["5v5"]["defense"], "Hold%",
              "Category <code>GAC 5v5 - Defense</code>. Hold% = share of attacks this squad survives.")
html += table("GAC 5v5 &#9679; OFFENSE", res["5v5"]["offense"], "Win%",
              f"Category <code>GAC 5v5 - Offense</code>. First {res['5v5']['core_off']} are the core "
              f"(one per enemy defensive squad); the rest are bench alternatives.")
html += table("GAC 3v3 &#9679; DEFENSE &#8212; set all 15", res["3v3"]["defense"], "Hold%",
              "Category <code>GAC 3v3 - Defense</code>.")
html += table("GAC 3v3 &#9679; OFFENSE", res["3v3"]["offense"], "Win%",
              f"Category <code>GAC 3v3 - Offense</code>. First {res['3v3']['core_off']} are the core.")
html += table("TERRITORY WAR &#9679; DEFENSE", res["tw"]["defense"], "Hold%",
              "Category <code>TW 5v5 - Defense</code>. Set top-down until your TW map runs out of slots. "
              "TW defense is worth more than GAC defense: the enemy guild has a finite pool of attempts and "
              "a territory pays nothing unless it is fully cleared, so a wall that merely eats attempts scores.")
html += table("TERRITORY WAR &#9679; OFFENSE", res["tw"]["offense"], "Win%",
              "Category <code>TW 5v5 - Offense</code>. Unit-disjoint from the TW defense list above, so you "
              "can set defense and still field every one of these.")
html += fleet_table("FLEETS &#9679; GAC OFFENSE", res["fleets"]["GAC Fleet - Offense"],
                    "Category <code>GAC Fleet - Offense</code>. These three answer all 11 defendable capitals "
                    "at &ge;94%.")
html += fleet_table("FLEETS &#9679; GAC DEFENSE", res["fleets"]["GAC Fleet - Defense"],
                    "Category <code>GAC Fleet - Defense</code>. Ship-disjoint from the offense fleets.")
html += fleet_table("FLEET ARENA", res["fleets"]["Fleet - Arena"],
                    "Category <code>Fleet - Arena</code>. Separate mode, so it may reuse GAC ships.")
html += ("<div style='font-size:15pt;font-weight:bold;color:#16324f;margin:22px 0 8px 0;"
         "border-bottom:2px solid #16324f;padding-bottom:3px;'>Gaps &#8212; the meta squads you cannot field</div>"
         "<table style='border-collapse:collapse;width:100%;font-size:10pt;'>"
         "<tr><th style='background:#d9f2d0;padding:4px 9px;border:1px solid #bcdcb0;text-align:left;'>Mode</th>"
         "<th style='background:#d9f2d0;padding:4px 9px;border:1px solid #bcdcb0;'>Rate</th>"
         "<th style='background:#d9f2d0;padding:4px 9px;border:1px solid #bcdcb0;text-align:left;'>Leader</th>"
         "<th style='background:#d9f2d0;padding:4px 9px;border:1px solid #bcdcb0;text-align:left;'>Missing</th></tr>"
         + gap_table("5v5") + gap_table("3v3") + "</table></div>")

open(os.path.join(OUT, "playbook.html"), "w").write(html)

from collections import Counter  # noqa: E402
c = Counter(p["cat"] for p in payload)
print(f"upload_payload.json: {len(payload)} definitions")
for k, v in sorted(c.items()):
    print(f"  {v:3}  {k}")
print("playbook.html written")
