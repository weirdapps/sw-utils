#!/usr/bin/env python3
"""mod_analysis.py — grounded current-vs-best-mods gap analysis for GAC units.
Inputs: data/meta/mod_meta_report.txt (targets), data/current_mods.json (current), data/gac_result.json (which teams).
Output: output/mod_plan.md (prioritized per-unit plan) + console summary.
"""
import json, os
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D=os.path.join(ROOT,"data")
FOUR={"Speed","Offense","CritDamage"}  # 4-mod sets; rest are 2-mod

# targets
tgt={}
for line in open(os.path.join(D,"meta","mod_meta_report.txt")):
    line=line.rstrip("\n")
    if not line or line.startswith("#"): continue
    p=line.split("|")
    if len(p)<6: continue
    bid,sets,arrow,tri,circ,cross=p[0],p[1],p[2],p[3],p[4],p[5]
    tgt[bid]={"sets":sets,"arrow":arrow,"tri":tri,"circ":circ,"cross":cross}

cur=json.load(open(os.path.join(D,"current_mods.json")))["units"]
res=json.load(open(os.path.join(D,"gac_result.json")))

# unit -> best (highest priority) team label; current season is 3v3
PRI=[("3v3","defense","3v3-DEF"),("3v3","offense","3v3-OFF"),("5v5","defense","5v5-DEF"),("5v5","offense","5v5-OFF")]
unit_team={}
for fmt,persp,lab in PRI:
    for sq in res[fmt][persp]:
        for b in sq["units"]:
            unit_team.setdefault(b, lab)  # first (highest pri) wins

def pieces(sets_str, sep):
    d={}
    for s in [x.strip() for x in sets_str.replace("+",sep).split(sep) if x.strip()]:
        # current form "Speedx4"
        if "x" in s and s.split("x")[-1].isdigit():
            name,n=s.split("x"); d[name]=d.get(name,0)+int(n)
        else:
            d[s]=d.get(s,0)+(4 if s in FOUR else 2)
    return d

rows=[]
for b,lab in sorted(unit_team.items(), key=lambda kv:(PRI_index(kv[1]) if False else 0)):
    pass

def prio_rank(lab):
    order={"3v3-DEF":0,"3v3-OFF":1,"5v5-DEF":2,"5v5-OFF":3}
    return order.get(lab,9)

units=sorted(unit_team.keys(), key=lambda b:(prio_rank(unit_team[b]), b))
n_ok=n_set=n_lvl=n_dot=n_arrow=n_nomods=0
lines=[]
for b in units:
    lab=unit_team[b]
    t=tgt.get(b)
    c=cur.get(b)
    issues=[]
    if not c or c.get("mods",0)==0:
        issues.append("NO MODS"); n_nomods+=1
    else:
        # set check
        if t and t["sets"]:
            want=pieces(t["sets"],"+"); have=pieces(c["sets"],",")
            # compare 4-mod set presence primarily
            want4=[s for s in want if s in FOUR]; have4=[s for s in have if s in FOUR]
            if want!=have:
                # flag if the key 4-set differs or 2-set differs
                issues.append(f"set have[{c['sets']}] want[{t['sets']}]"); n_set+=1
        # arrow speed
        if t and t["arrow"].startswith("Speed") and not c.get("arrowSpeed"):
            issues.append("no Speed arrow"); n_arrow+=1
        # quality
        if c.get("minLvl",15)<15: issues.append(f"unleveled(min L{c['minLvl']})"); n_lvl+=1
        if c.get("sixDot",6)<6: issues.append(f"only {c['sixDot']}/6 six-dot"); n_dot+=1
    if not issues: n_ok+=1; status="OK"
    else: status="; ".join(issues)
    spd=c.get("speed","?") if c else "?"
    lines.append(f"| {lab} | {b} | {(c or {}).get('sets','-')} | {(t or {}).get('sets','?')} | {spd} | {status} |")

md=["# Grounded Mod Plan — GAC units (current vs swgoh.gg best-mods)","",
    f"Units analysed: {len(units)}  |  OK: {n_ok}  |  need set change: {n_set}  |  unleveled mods: {n_lvl}  |  not full 6-dot: {n_dot}  |  missing Speed arrow: {n_arrow}  |  no mods: {n_nomods}","",
    "Priority order: current season is **3v3**, so 3v3-DEF > 3v3-OFF > 5v5-DEF > 5v5-OFF.","",
    "| Team | Unit | Current sets | Target sets | Mod-speed | Action |","|---|---|---|---|---|---|"]
md+=lines
open(os.path.join(ROOT,"output","mod_plan.md"),"w").write("\n".join(md))
print(f"units={len(units)} OK={n_ok} setChange={n_set} unleveled={n_lvl} not6dot={n_dot} noSpeedArrow={n_arrow} noMods={n_nomods}")
print("wrote output/mod_plan.md")
# top-priority problem units (3v3 first)
print("\nTop 3v3 units needing work:")
shown=0
for b in units:
    if unit_team[b] not in ("3v3-DEF","3v3-OFF"): continue
    c=cur.get(b); t=tgt.get(b)
    iss=[]
    if not c or c.get('mods',0)==0: iss.append('NO MODS')
    else:
        if t and pieces(t['sets'],'+')!=pieces(c['sets'],','): iss.append(f"set→{t['sets']}")
        if t and t['arrow'].startswith('Speed') and not c.get('arrowSpeed'): iss.append('no spd arrow')
        if c.get('minLvl',15)<15: iss.append(f"L{c['minLvl']}")
        if c.get('sixDot',6)<6: iss.append(f"{c['sixDot']}/6dot")
    if iss and shown<25:
        print(f"  [{unit_team[b]}] {b:22} spd{(c or {}).get('speed','?'):>4}  {'; '.join(iss)}"); shown+=1
