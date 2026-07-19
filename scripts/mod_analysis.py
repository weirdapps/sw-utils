#!/usr/bin/env python3
"""mod_analysis.py — accurate current-vs-best-mods gap for GAC units (decode validated: SLKR=115)."""
import json, os
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D=os.path.join(ROOT,"data")
FOUR={"Speed","Offense","CritDamage"}
tgt={}
for line in open(os.path.join(D,"meta","mod_meta_report.txt")):
    line=line.rstrip("\n")
    if not line or line.startswith("#"): continue
    p=line.split("|")
    if len(p)<6: continue
    tgt[p[0]]={"sets":p[1],"arrow":p[2]}
cur=json.load(open(os.path.join(D,"current_mods.json")))["units"]
res=json.load(open(os.path.join(D,"gac_result.json")))
try: name={u["b"]:u["n"] for u in json.load(open(os.path.join(D,"roster","swgoh_roster_fresh_20260718.json")))["units"]}
except: name={}
PRI=[("3v3","defense","3v3-DEF"),("3v3","offense","3v3-OFF"),("5v5","defense","5v5-DEF"),("5v5","offense","5v5-OFF")]
rank={"3v3-DEF":0,"3v3-OFF":1,"5v5-DEF":2,"5v5-OFF":3}
unit_team={}
for fmt,persp,lab in PRI:
    for sq in res[fmt][persp]:
        for b in sq["units"]: unit_team.setdefault(b,lab)
def pieces(s,sep):
    d={}
    for x in [q.strip() for q in s.replace("+",sep).split(sep) if q.strip()]:
        if "x" in x and x.split("x")[-1].isdigit(): nm,n=x.split("x"); d[nm]=d.get(nm,0)+int(n)
        else: d[x]=d.get(x,0)+(4 if x in FOUR else 2)
    return d
units=sorted(unit_team, key=lambda b:(rank[unit_team[b]], b))
n=dict(setw=0,arrow=0,lvl=0,dot=0,slow=0,ok=0)
lines=[]
for b in units:
    lab=unit_team[b]; t=tgt.get(b,{}); c=cur.get(b)
    act=[]
    if not c or c.get("mods",0)==0: act.append("**NO MODS EQUIPPED**")
    else:
        if t.get("sets") and pieces(t["sets"],"+")!=pieces(c["sets"],","):
            act.append(f"set→{t['sets']} (have {c['sets']})"); n["setw"]+=1
        if t.get("arrow","").startswith("Speed") and not c.get("spdArrow"):
            act.append("add Speed arrow"); n["arrow"]+=1
        if c.get("speed",0)<180: act.append(f"low speed ({c.get('speed')})"); n["slow"]+=1
        if c.get("minLvl",15)<15: act.append(f"level mods (min L{c['minLvl']})"); n["lvl"]+=1
        if c.get("sixDot",6)<6: act.append(f"slice to 6-dot ({c['sixDot']}/6)"); n["dot"]+=1
    if not act: n["ok"]+=1; act=["OK"]
    lines.append((lab,b,c,t,act))
md=["# Accurate Mod Gap Report — GAC (current vs swgoh.gg best-mods)","",
    f"Units: {len(units)} | fully OK: {n['ok']} | wrong set: {n['setw']} | missing Speed arrow: {n['arrow']} | low speed(<180): {n['slow']} | unleveled: {n['lvl']} | not full 6-dot: {n['dot']}","",
    "Priority: current season **3v3** first. 'Action' lists what to fix, most-impactful first.","",
    "| Team | Unit | Speed | Current sets | Action |","|---|---|---|---|---|"]
for lab,b,c,t,act in lines:
    md.append(f"| {lab} | {name.get(b,b)} | {(c or {}).get('speed','-')} | {(c or {}).get('sets','-')} | {'; '.join(act)} |")
open(os.path.join(ROOT,"output","mod_plan.md"),"w").write("\n".join(md))
print(f"OK={n['ok']} wrongSet={n['setw']} noSpeedArrow={n['arrow']} lowSpeed={n['slow']} unleveled={n['lvl']} not6dot={n['dot']}  (of {len(units)})")
print("\n=== 3v3 DEFENSE (current season) — priority fixes ===")
for lab,b,c,t,act in lines:
    if lab!="3v3-DEF" or act==["OK"]: continue
    print(f"  {name.get(b,b)[:24]:24} spd{(c or {}).get('speed','?'):>4}  {'; '.join(act)}")
