#!/usr/bin/env python3
"""
generate_hotutils.py — turn data/gac_result.json into deliverables.

Outputs (into output/):
  hotutils_5v5_defense.json / _5v5_offense / _3v3_defense / _3v3_offense   (4 squad groups)
  hotutils_fleets_defense.json / _offense.json                             (full fleets)
  upload_payload.json   (compact, consumed by the HotUtils API uploader — see browser_recipes.md)
  playbook.html         (human-readable, Aptos/NBG-style)

Squad HotUtils category = "GAC <fmt> - <Defense|Offense>"  -> 4 distinct groups.
Fleet category         = "GAC Fleet - <Defense|Offense>".
Fleets are FULL lineups (capital + up to 7 owned faction ships), no ship reused across fleets.
"""
import json, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
OUT = os.path.join(ROOT, "output")
os.makedirs(OUT, exist_ok=True)

res = json.load(open(os.path.join(DATA, "gac_result.json")))
roster = json.load(open(os.path.join(DATA, "roster", "swgoh_roster_fresh_20260731.json")))
info = {u["b"]: u for u in roster["units"]}
name = {u["b"]: u["n"] for u in roster["units"]}
gp = roster["meta"]["gp"]


def relic(b):
    u = info.get(b)
    if not u:
        return "?"
    rt = u.get("rt") or 0
    return f"R{rt-2}" if rt >= 3 else f"G{u['g']}"


LBL = {"STRANGER": "The Stranger", "GLREY": "GL Rey", "LORDVADER": "Lord Vader", "CASSIANUNDERCOVER": "Cassian UC",
       "BAYLANSKOLL": "Baylan", "EMPERORPALPATINE": "Palpatine EP", "JABBATHEHUTT": "Jabba", "SATELESHAN": "Satele",
       "MAJORPARTAGAZ": "Partagaz ISB", "GLAHSOKATANO": "GL Ahsoka", "FINN": "Resistance Finn", "QUEENAMIDALA": "Queen Amidala",
       "GLLEIA": "GL Leia", "SUPREMELEADERKYLOREN": "SLKR", "JEDIMASTERKENOBI": "JMK", "DARTHTRAYA": "Sith Triumvirate",
       "DARTHNIHILUS": "Nihilus Triumvirate", "DARTHMALGUS": "Malgus", "DOCTORAPHRA": "Aphra", "BOSSNASS": "Gungans",
       "SITHPALPATINE": "SEE", "DARTHBANE": "Bane", "GRANDMASTERLUKE": "JML", "GENERALSKYWALKER": "GAS 501st",
       "MANDALORBOKATAN": "Bo-Katan Mandos", "GREATMOTHERS": "Great Mothers", "WAMPA": "Wampa", "ADMIRALRADDUS": "Raddus",
       "DASHRENDAR": "Dash BAM", "CEREJUNDA": "Cere", "DARTHREVAN": "Darth Revan", "STORMTROOPERLUKE": "Endor Luke"}


def lbl(b):
    return LBL.get(b, name.get(b, b))


WHY = {
    "STRANGER": "#1 wall in the game; holds a full battle vs most attackers", "GLREY": "Strong hold vs non-GL & mirrors",
    "LORDVADER": "Clone-Vader wall; culls squishies, punishes TM", "CASSIANUNDERCOVER": "Rising Andor wall; strong vs droids/rebels/GL",
    "BAYLANSKOLL": "Thorny Ronin wall; punishes greedy attacks", "EMPERORPALPATINE": "Imperial staller; anti-Jedi, drags games long",
    "JABBATHEHUTT": "Sticky cartel; huge health pool", "SATELESHAN": "Tanky Jedi/Old-Rep wall; board depth",
    "MAJORPARTAGAZ": "ISB wall; strong vs droids & rebels", "GLAHSOKATANO": "Most-used 5v5 wall; punishes AoE & isolation",
    "FINN": "Resistance staller; last-node filler", "QUEENAMIDALA": "Anti-Sith / anti-DOT staller",
    "DARTHREVAN": "Sith stall vs squishy 3v3 attackers", "STORMTROOPERLUKE": "Endor Rebel wall; cheap 3v3 depth",
    "GREATMOTHERS": "Revive spam; eats poorly-built attackers",
    "GLLEIA": "#1 attacker (95-96% win); beats almost anything incl. most GLs", "SUPREMELEADERKYLOREN": "Solo-smash isolated leads / squishy GLs",
    "JEDIMASTERKENOBI": "Premier hammer; beats most metas incl. many GLs", "GRANDMASTERLUKE": "Tanky cleaner; Rebels & Jedi mirrors",
    "SITHPALPATINE": "Anti-GL; drains & bursts (1-2 unit clears in 3v3)", "DARTHBANE": "Unit-efficient 2-man cleaner",
    "DARTHMALGUS": "Anti-Jedi / anti-tank Sith burst", "DARTHTRAYA": "Sith Triumvirate; anti-tank / anti-Jedi",
    "DARTHNIHILUS": "Triumvirate burst; one-shots big-health leads", "DOCTORAPHRA": "Droid burst; great vs GL Ahsoka / clones",
    "BOSSNASS": "Gungan wall-breaker; strong vs many metas", "GENERALSKYWALKER": "Clone hammer; punishes non-burst teams",
    "MANDALORBOKATAN": "vs Nightsisters / DOT / droids", "WAMPA": "1-unit cheese; clears a weak node for free",
    "ADMIRALRADDUS": "Rebel fleet-on-ground burst", "DASHRENDAR": "Scoundrel burst", "CEREJUNDA": "JKL-team counter / Jedi burst"}


def why(b):
    return WHY.get(b, "Meta pick")


# ---------- FULL FLEETS (capital + owned faction ships; no ship reused across fleets) ----------
# Grounded: capital + Hold% from swgoh.gg /gac/ship-counters (Season 80). swgoh.gg publishes only
# capital + starting-3, so reinforcement ships are standard faction-fleet meta from the owned roster.
FLEETS = {
    "GAC Fleet - Defense": [
        ("Fleet D1 Leviathan (82%)", ["CAPITALLEVIATHAN", "SCYTHE", "TIESILENCER", "EMPERORSSHUTTLE",
                                       "COMMANDSHUTTLE", "TIEFIGHTERFOSF", "TIEFIGHTERFIRSTORDER", "SITHFIGHTER"]),
        ("Fleet D2 Negotiator (90%)", ["CAPITALNEGOTIATOR", "JEDISTARFIGHTERAHSOKATANO", "JEDISTARFIGHTERANAKIN",
                                       "BLADEOFDORIN", "JEDISTARFIGHTERCONSULAR", "ARC170REX", "ARC170CLONESERGEANT", "YWINGCLONEWARS"]),
        ("Fleet D3 Home One (91%)", ["CAPITALMONCALAMARICRUISER", "BWINGREBEL", "XWINGRED3", "XWINGRED2",
                                     "GHOST", "PHANTOM2", "YWINGREBEL", "XWINGRESISTANCE"]),
    ],
    "GAC Fleet - Offense": [
        ("Fleet O1 Executor", ["CAPITALEXECUTOR", "TIEADVANCED", "TIEINTERCEPTOR", "TIEDEFENDER",
                               "TIEREAPER", "TIEDAGGER", "TIEFIGHTERIMPERIAL", "TIEBOMBERIMPERIAL"]),
        ("Fleet O2 Malevolence", ["CAPITALMALEVOLENCE", "VULTUREDROID", "HYENABOMBER",
                                  "GEONOSIANSTARFIGHTER1", "GEONOSIANSTARFIGHTER3", "GEONOSIANSTARFIGHTER2"]),
        ("Fleet O3 Raddus", ["CAPITALRADDUS", "ROGUEONESHIP", "UWINGSCARIF", "UWINGROGUEONE",
                             "MILLENNIUMFALCON", "OUTRIDER", "HOUNDSTOOTH", "XWINGBLACKONE"]),
    ],
}

BOILER = {"hasOmicron": False, "hasZeta": False, "hasUltimate": False,
          "filters": {"minGP": 1000, "gear": 0, "relic": 0, "stars": 2}, "subsPriority": "order"}


def squad_obj(nm, cat, units, combat):
    return {"id": 0, "name": nm, "size": len(units), "combatType": combat, "category": [cat],
            "contents": [{"id": i, "characterId": b, "characterName": name.get(b, b), "requirements": BOILER}
                         for i, b in enumerate(units)]}


# ---------- build squad group files + collect upload payload ----------
payload = []   # compact: {n,sz,ct,cat,u:[[baseid,name]]}
files = {}
PFX = {"defense": "D", "offense": "O"}
for fmt in ("5v5", "3v3"):
    for persp in ("defense", "offense"):
        cat = f"GAC {fmt} - {persp.capitalize()}"
        arr = []
        for i, sq in enumerate(res[fmt][persp], 1):
            lead = sq["units"][0]
            nm = f"{fmt} {PFX[persp]}{i:02d} {lbl(lead)} {sq['rate']}%"
            arr.append(squad_obj(nm, cat, sq["units"], 1))
            payload.append({"n": nm, "sz": len(sq["units"]), "ct": 1, "cat": cat,
                            "u": [[b, name.get(b, b)] for b in sq["units"]]})
        fn = f"hotutils_{fmt}_{persp}.json"
        json.dump(arr, open(os.path.join(OUT, fn), "w"), indent=1)
        files[(fmt, persp)] = (fn, len(arr))

# ---------- build fleet files ----------
for cat, fleets in FLEETS.items():
    persp = "defense" if "Defense" in cat else "offense"
    arr = []
    for nm, units in fleets:
        arr.append(squad_obj(nm, cat, units, 2))
        payload.append({"n": nm, "sz": len(units), "ct": 2, "cat": cat,
                        "u": [[b, name.get(b, b)] for b in units]})
    fn = f"hotutils_fleets_{persp}.json"
    json.dump(arr, open(os.path.join(OUT, fn), "w"), indent=1)
    files[("fleet", persp)] = (fn, len(arr))

json.dump(payload, open(os.path.join(OUT, "upload_payload.json"), "w"), separators=(",", ":"))

# ---------- playbook.html ----------
def cells(units):
    parts = []
    for j, b in enumerate(units):
        s = "<b>" if j == 0 else ""; e = "</b>" if j == 0 else ""
        parts.append(f"{s}{name.get(b,b)} <span style='color:#8a8a8a'>{relic(b)}</span>{e}")
    return " &#8226; ".join(parts)


def table(title, picks, ratehdr, whyhdr):
    h = (f"<div style='font-size:15pt;font-weight:bold;color:#16324f;margin:22px 0 8px 0;"
         f"border-bottom:2px solid #16324f;padding-bottom:3px;'>{title}</div>"
         "<table style='border-collapse:collapse;width:100%;font-size:10.5pt;'><tr>")
    for c in ["#", "Team", ratehdr, whyhdr]:
        h += (f"<th style='background:#d9f2d0;color:#404040;text-align:left;padding:6px 9px;"
              f"border:1px solid #bcdcb0;font-weight:bold;'>{c}</th>")
    h += "</tr>"
    for i, sq in enumerate(picks, 1):
        rate = sq.get("rate", "")
        seen = sq.get("seen", "")
        why_txt = why(sq["units"][0]) if "units" in sq else ""
        h += (f"<tr><td style='padding:6px 9px;border:1px solid #d9d9d9;text-align:center;vertical-align:top;'>{i}</td>"
              f"<td style='padding:6px 9px;border:1px solid #d9d9d9;vertical-align:top;'>{cells(sq['units'])}</td>"
              f"<td style='padding:6px 9px;border:1px solid #d9d9d9;text-align:center;vertical-align:top;white-space:nowrap;'>"
              f"<b>{rate}%</b><br><span style='color:#8a8a8a;font-size:9pt;'>seen {seen}</span></td>"
              f"<td style='padding:6px 9px;border:1px solid #d9d9d9;vertical-align:top;'>{why_txt}</td></tr>")
    h += "</table>"
    return h


def fleet_table(title, fleets):
    h = (f"<div style='font-size:15pt;font-weight:bold;color:#16324f;margin:22px 0 8px 0;"
         f"border-bottom:2px solid #16324f;padding-bottom:3px;'>{title}</div>"
         "<table style='border-collapse:collapse;width:100%;font-size:10.5pt;'><tr>")
    for c in ["Fleet", "Full lineup (capital first)"]:
        h += (f"<th style='background:#d9f2d0;color:#404040;text-align:left;padding:6px 9px;"
              f"border:1px solid #bcdcb0;font-weight:bold;'>{c}</th>")
    h += "</tr>"
    for nm, units in fleets:
        h += (f"<tr><td style='padding:6px 9px;border:1px solid #d9d9d9;vertical-align:top;white-space:nowrap;'><b>{nm}</b></td>"
              f"<td style='padding:6px 9px;border:1px solid #d9d9d9;vertical-align:top;'>{cells(units)}</td></tr>")
    h += "</table>"
    return h


def gap_html(fmt):
    g = res[fmt]["gaps"]
    rows = ""
    for persp, label in [("def", "DEFENSE"), ("off", "OFFENSE")]:
        for it in g[persp][:5]:
            rows += (f"<tr><td style='padding:4px 9px;border:1px solid #d9d9d9;'>{label}</td>"
                     f"<td style='padding:4px 9px;border:1px solid #d9d9d9;text-align:center;'>{it['rate']}%</td>"
                     f"<td style='padding:4px 9px;border:1px solid #d9d9d9;'>{it['leader']}</td>"
                     f"<td style='padding:4px 9px;border:1px solid #d9d9d9;'>{', '.join(it['missing'])}</td></tr>")
    return rows


html = f"""<div style="font-family:'Aptos','Segoe UI',Arial,sans-serif;font-size:12pt;color:#404040;max-width:960px;">
<div style='font-size:19pt;font-weight:bold;color:#16324f;'>SWGOH Grand Arena Playbook &nbsp;|&nbsp; Kyber 3 &#8594; Kyber 2</div>
<div style='color:#6a6a6a;margin:4px 0 14px 0;'>Player <b>Astra</b> &#8226; ally 145357294 &#8226; {gp:,} GP &#8226; 9 Galactic Legends<br>
<b>Grounded:</b> swgoh.gg live GAC meta (5v5 Season 80 / latest-3v3 Season 79, ranked by Hold%/Win%) + ship meta (/gac/ship-counters) + live Kyber board + live roster. All units owned, G13+, no unit repeats within a format.</div>
<div style='background:#f4f7f4;border:1px solid #d9e6d4;border-radius:6px;padding:10px 14px;margin-bottom:8px;'>
<b>Board:</b> 5v5 = 11 def squads + 3 fleets &nbsp;|&nbsp; 3v3 = 15 def squads + 3 fleets. Offense mirror-clears the same counts.<br>
<b>GL split:</b> JMK/JML/SEE/SLKR reserved for offense; GL Leia offense in 5v5; Vader/Rey/Ahsoka/Jabba on defense.<br>
<b>Four squad groups</b> map 1:1 to HotUtils categories: GAC 5v5/3v3 - Defense/Offense. Fleets = GAC Fleet - Defense/Offense (full lineups).</div>
"""
html += table("5v5 &#9679; DEFENSE (set 11) &#8212; cat: GAC 5v5 - Defense", res["5v5"]["defense"], "Hold%", "Why it holds")
html += table(f"5v5 &#9679; OFFENSE ({len(res['5v5']['offense'])}) &#8212; cat: GAC 5v5 - Offense", res["5v5"]["offense"], "Win%", "Use for")
html += table("3v3 &#9679; DEFENSE (set 15) &#8212; cat: GAC 3v3 - Defense", res["3v3"]["defense"], "Hold%", "Why it holds")
html += table(f"3v3 &#9679; OFFENSE ({len(res['3v3']['offense'])}) &#8212; cat: GAC 3v3 - Offense", res["3v3"]["offense"], "Win%", "Use for")
html += fleet_table("Fleets &#9679; DEFENSE (set 3) &#8212; cat: GAC Fleet - Defense", FLEETS["GAC Fleet - Defense"])
html += fleet_table("Fleets &#9679; OFFENSE (3) &#8212; cat: GAC Fleet - Offense", FLEETS["GAC Fleet - Offense"])
html += ("<div style='font-size:15pt;font-weight:bold;color:#16324f;margin:22px 0 8px 0;border-bottom:2px solid #16324f;padding-bottom:3px;'>"
         "Gap analysis &#8212; what you can't field</div>"
         "<div style='color:#404040;'><b>Squad GL gap: GL Hondo</b> (leads the #1 3v3 wall, 38% hold). "
         "<b>Fleet gap: Profundity</b> (77% = #1 defensive fleet). Both are your biggest upgrades.<br>"
         "<b>Non-GL walls missing:</b> Third Sister (highest unfielded wall).</div>"
         "<table style='border-collapse:collapse;width:100%;font-size:10pt;margin-top:8px;'>"
         "<tr><th style='background:#d9f2d0;padding:4px 9px;border:1px solid #bcdcb0;text-align:left;'>Fmt/Phase</th>"
         "<th style='background:#d9f2d0;padding:4px 9px;border:1px solid #bcdcb0;'>Rate</th>"
         "<th style='background:#d9f2d0;padding:4px 9px;border:1px solid #bcdcb0;text-align:left;'>Leader</th>"
         "<th style='background:#d9f2d0;padding:4px 9px;border:1px solid #bcdcb0;text-align:left;'>Missing</th></tr>")
html += "<tr><td colspan=4 style='padding:3px 9px;background:#eef;font-weight:bold;'>5v5</td></tr>" + gap_html("5v5")
html += "<tr><td colspan=4 style='padding:3px 9px;background:#eef;font-weight:bold;'>3v3</td></tr>" + gap_html("3v3")
html += "</table></div>"

open(os.path.join(OUT, "playbook.html"), "w").write(html)

total = sum(n for _, n in files.values())
print("wrote", len(files), "group files +", total, "squads +", "upload_payload.json + playbook.html")
for k, (fn, n) in files.items():
    print(f"  {fn}: {n}")
