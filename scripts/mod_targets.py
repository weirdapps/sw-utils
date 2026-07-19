#!/usr/bin/env python3
"""mod_targets.py — clean grounded per-unit mod TARGET plan for GAC units (from swgoh.gg mod-meta).
Output: output/mod_targets.md, grouped by team, current season (3v3) first. Reliable (no current-mod decode)."""
import json, os
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D=os.path.join(ROOT,"data")
tgt={}
for line in open(os.path.join(D,"meta","mod_meta_report.txt")):
    line=line.rstrip("\n")
    if not line or line.startswith("#"): continue
    p=line.split("|")
    if len(p)<6: continue
    tgt[p[0]]={"sets":p[1],"arrow":p[2],"tri":p[3],"circ":p[4],"cross":p[5]}
res=json.load(open(os.path.join(D,"gac_result.json")))
name={}
try:
    ro=json.load(open(os.path.join(D,"roster","swgoh_roster_fresh_20260718.json")))
    name={u["b"]:u["n"] for u in ro["units"]}
except: pass

GROUPS=[("3v3 DEFENSE (current season)","3v3","defense"),("3v3 OFFENSE","3v3","offense"),
        ("5v5 DEFENSE","5v5","defense"),("5v5 OFFENSE","5v5","offense")]
seen=set()
md=["# Grounded Mod Targets — GAC (swgoh.gg mod-meta, July 2026)","",
    "For every unit: **set combo** + **primary per variable slot** (Square=Offense%, Diamond=Defense% always). "
    "**Speed is the #1 secondary on every unit** — chase speed secondaries + a Speed arrow wherever the arrow isn't a fixed stat. "
    "Grounded from swgoh.gg's most-used builds. Current season is **3v3** → do those first.",""]
for title,fmt,persp in GROUPS:
    md.append(f"## {title}")
    md.append("| # | Unit | Sets | Arrow | Triangle | Circle | Cross |")
    md.append("|---|---|---|---|---|---|---|")
    i=0
    for sq in res[fmt][persp]:
        for b in sq["units"]:
            key=(fmt,b)
            if b in seen and fmt!="3v3": continue  # list each unit once per season-priority
            # actually list per group but avoid dup within group
        # list leader-first squad members once each in this group
    # simpler: unique units in this group in order
    ug=[]
    for sq in res[fmt][persp]:
        for b in sq["units"]:
            if b not in ug: ug.append(b)
    for b in ug:
        i+=1
        t=tgt.get(b,{})
        nm=name.get(b,b)
        md.append(f"| {i} | {nm} | {t.get('sets','?')} | {t.get('arrow','?')} | {t.get('tri','?')} | {t.get('circ','?')} | {t.get('cross','?')} |")
    md.append("")
open(os.path.join(ROOT,"output","mod_targets.md"),"w").write("\n".join(md))
print("wrote output/mod_targets.md")
# counts
for title,fmt,persp in GROUPS:
    ug=set()
    for sq in res[fmt][persp]:
        ug.update(sq["units"])
    print(f"  {title}: {len(ug)} units")
