#!/usr/bin/env python3
"""daily_brief.py — A1 daily brief.

Assembles a single "what to do today" brief from the grounded board
(data/gac_result.json) and the A3 advisor's farm ranking, and renders it to the
terminal plus output/brief_<date>.html (same spirit as playbook.html).

Sections that plug in later: mod-material status (needs a live HotUtils session)
and event countdowns (A4). Kept out of v1 so the brief runs with zero secrets.

Usage:  python3 scripts/daily_brief.py
"""
import glob
import json
import os
from datetime import datetime

import advisor
import events
import reddit_swgoh
import swgoh_data

try:
    from zoneinfo import ZoneInfo
    _TODAY = datetime.now(ZoneInfo("Europe/Athens")).strftime("%Y-%m-%d")
except Exception:
    _TODAY = datetime.now().strftime("%Y-%m-%d")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GAC_RESULT = os.path.join(ROOT, "data", "gac_result.json")
OUT_DIR = os.path.join(ROOT, "output")


def brief_sections(gac_result, farm_ranked, events_list=None, relic_list=None, top_n=8,
                   chatter=None):
    """Pure assembly: fold board summary + farm targets + events + relic priority."""
    board = {}
    for fmt, d in gac_result.items():
        board[fmt] = {
            "def_count": len(d.get("defense", [])),
            "off_count": len(d.get("offense", [])),
            "unique": d.get("unique_units"),
        }
    return {"board": board, "farm": farm_ranked[:top_n],
            "events": events_list or [], "relic": relic_list or [],
            "chatter": chatter or []}


def _farm_line(e):
    sole = e["sole_blocker_of"]
    if sole:
        best = max(sole, key=lambda s: s["rate"])
        return (f"{e['unit']}  —  SOLE-BLOCKER of {best['rate']}% "
                f"{best['fmt']} {best['persp']} ({best['leader']}); in {e['also_needed_in']} gap-teams")
    return f"{e['unit']}  —  in {e['also_needed_in']} gap-teams, best {e['best_rate']}%"


def render_terminal(sections):
    lines = [f"SWGOH daily brief — {_TODAY}", ""]
    lines.append("GAC board:")
    for fmt, b in sections["board"].items():
        lines.append(f"  {fmt}: defense {b['def_count']} · offense {b['off_count']} · unique units {b['unique']}")
    lines.append("")
    lines.append("Farm priority (unlock the most board):")
    for e in sections["farm"]:
        lines.append(f"  • {_farm_line(e)}")
    if sections.get("events"):
        lines.append("")
        lines.append("Upcoming events:")
        for e in sections["events"][:10]:
            star = " ⭐" if events.is_notable(e) else ""
            lines.append(f"  {events.fmt_date(e.get('date'))}  {e.get('name', '?')}  [{e.get('category', '?')}]{star}")
    if sections.get("relic"):
        lines.append("")
        lines.append("Relic priority (reinforce your best board units):")
        for e in sections["relic"][:8]:
            lines.append(f"  {e['unit']} (relic R{e['relic']}) — best team {e['best_rate']}%, in {e['in_teams']} board teams")
    lines.append("")
    lines.append("Board chatter (r/SWGalaxyOfHeroes)")
    if sections.get("chatter"):
        for e in sections["chatter"][:6]:
            lines.append(f"  [{','.join(e['units'])}] {e['title'][:70]}")
    else:
        lines.append("  no board-relevant chatter")
    return "\n".join(lines)


def render_html(sections, date=_TODAY):
    rows = []
    for fmt, b in sections["board"].items():
        rows.append(f"<tr><td>{fmt}</td><td>{b['def_count']}</td><td>{b['off_count']}</td><td>{b['unique']}</td></tr>")
    farm = []
    for e in sections["farm"]:
        sole = e["sole_blocker_of"]
        if sole:
            best = max(sole, key=lambda s: s["rate"])
            tag = f"<b>SOLE-BLOCKER</b> of {best['rate']}% {best['fmt']} {best['persp']} ({best['leader']})"
        else:
            tag = f"in {e['also_needed_in']} gap-teams, best {e['best_rate']}%"
        farm.append(f"<li><b>{e['unit']}</b> — {tag}</li>")
    evs = []
    for e in sections.get("events", []):
        star = " ⭐" if events.is_notable(e) else ""
        evs.append(f"<li>{events.fmt_date(e.get('date'))} — {e.get('name', '?')} <i>[{e.get('category', '?')}]</i>{star}</li>")
    events_html = f"<h2>Upcoming events</h2><ul>{''.join(evs)}</ul>" if evs else ""
    relic = []
    for e in sections.get("relic", []):
        relic.append(f"<li><b>{e['unit']}</b> (relic R{e['relic']}) — best team {e['best_rate']}%, in {e['in_teams']} board teams</li>")
    relic_html = f"<h2>Relic priority</h2><ul>{''.join(relic)}</ul>" if relic else ""
    chatter_items = []
    for e in sections.get("chatter", [])[:6]:
        chatter_items.append(f"<li><a href=\"{e['link']}\">[{','.join(e['units'])}] {e['title'][:70]}</a></li>")
    if chatter_items:
        chatter_html = f"<h2>Board chatter (r/SWGalaxyOfHeroes)</h2><ul>{''.join(chatter_items)}</ul>"
    else:
        chatter_html = "<h2>Board chatter (r/SWGalaxyOfHeroes)</h2><p>no board-relevant chatter</p>"
    return f"""<!doctype html><html><head><meta charset="utf-8">
<title>SWGOH daily brief {date}</title>
<style>body{{font-family:-apple-system,Segoe UI,Arial,sans-serif;color:#333;max-width:760px;margin:2rem auto;padding:0 1rem}}
h1{{font-size:1.3rem}}table{{border-collapse:collapse}}td,th{{border:1px solid #ddd;padding:4px 10px;text-align:left}}
li{{margin:.25rem 0}}</style></head><body>
<h1>SWGOH daily brief — {date}</h1>
<h2>GAC board</h2>
<table><tr><th>format</th><th>defense</th><th>offense</th><th>unique units</th></tr>{''.join(rows)}</table>
<h2>Farm priority (unlock the most board)</h2>
<ul>{''.join(farm)}</ul>
{relic_html}
{events_html}
{chatter_html}
<p style="color:#999;font-size:.85rem">Pending: mod-material status (needs live HotUtils session).</p>
</body></html>"""


def main():
    gac = json.load(open(GAC_RESULT))
    farm = advisor.farm_priority(gac)
    try:
        evs = events.upcoming_events()
    except Exception as exc:
        evs = []
        print(f"(events unavailable: {exc})")
    try:
        rosters = sorted(glob.glob(os.path.join(ROOT, "data", "roster", "*.json")))
        roster = swgoh_data.load_roster(fallback_file=rosters[-1] if rosters else None)
        relic = advisor.relic_priority(gac, roster)
    except Exception as exc:
        relic = []
        print(f"(relic priority unavailable: {exc})")
    try:
        chatter = reddit_swgoh.load_board_chatter()
    except Exception as exc:  # network, throttle, or feed removed
        print(f"  (chatter unavailable: {exc})")
        chatter = []
    sections = brief_sections(gac, farm, evs, relic, chatter=chatter)
    print(render_terminal(sections))
    os.makedirs(OUT_DIR, exist_ok=True)
    out = os.path.join(OUT_DIR, f"brief_{_TODAY}.html")
    with open(out, "w") as f:
        f.write(render_html(sections))
    print(f"\nwrote {os.path.relpath(out, ROOT)}")


if __name__ == "__main__":
    main()
