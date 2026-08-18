#!/usr/bin/env python3
"""swgoh_data.py — comlink-backed data backbone (A0).

Replaces the fragile in-session swgoh.gg browser scrape with structured pulls
from a self-hosted swgoh-comlink instance.

`get_roster(allycode)` pulls the live roster and maps it to the
`{"units":[{b,n,ct,g,r,rt}]}` shape that compute_teams.py consumes.
`map_roster()` is the pure mapping (unit-tested offline); `get_roster()` adds
the network fetch.

comlink returns baseId + gear/rarity/relic but NOT display names or combatType,
so those are enriched from data/name_type_map.json (seeded from a roster pull;
refreshable from comlink game data once a live server is available).

Run comlink locally first, e.g.:
    docker run -d --name comlink -p 3000:3000 \
        -e APP_NAME=astra ghcr.io/swgoh-utils/swgoh-comlink:latest
Then:  COMLINK_URL=http://localhost:3000 python3 scripts/swgoh_data.py 145357294
"""
import json
import os
import re
from datetime import datetime

try:
    from zoneinfo import ZoneInfo
    _TODAY = datetime.now(ZoneInfo("Europe/Athens")).strftime("%Y-%m-%d")
except Exception:
    _TODAY = datetime.now().strftime("%Y-%m-%d")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_MAP = os.path.join(ROOT, "data", "name_type_map.json")
DEFAULT_COMLINK_URL = os.environ.get("COMLINK_URL", "http://localhost:3000")


def _relic_tier(unit):
    """comlink relic.currentTier verbatim (matches the swgoh.gg `rt` field, verified
    live against the 397-unit roster); None when the unit has no relic object."""
    relic = unit.get("relic")
    if not relic:
        return None
    return relic.get("currentTier")


# --- unit power ------------------------------------------------------------------
# ⚠ THE COMLINK ROSTER HAS NO PER-UNIT `gp`. The HotUtils-sourced rosters through
# 2026-08-12 carried `gp` (and `o`/`z`) on every unit; comlink's /player rosterUnit
# does not — GP is a derived stat and only comes back from a unit-stats call. When
# map_roster() replaced the HotUtils pull on 2026-08-18 the field vanished silently
# and tw_wall.py died on KeyError('gp') mid-run.
#
# So every consumer must go through unit_power(), never through unit["gp"]. The
# proxy is deliberately coarse: it is used for ORDERING (which filler leader is
# strongest) and for a 6,000-power floor that a G13 unit clears ~4x over on its own,
# so rank order is all that has to survive. It is NOT accurate enough to report as
# a GP number to the player.
#
# Coefficients are medians off data/roster/swgoh_roster_fresh_20260805.json, the
# last roster that carried real per-unit GP (moved here from rote_ops.py):
#   no relic:  g7 ~5.9K, g10 ~9.0K, g11 ~18.4K   -> ~1,500 / gear tier
#   G13:       R5 22.8K, R6 26.2K, R7 28.9K, R8 32.9K, R9 34.6K
#              -> ~20,000 base + ~2,800 / displayed relic tier
#   ships:     7-star median 73.6K, 6-star 56.8K -> ~9,000 / star
PROXY_PER_GEAR = 1_500      # sub-G13 characters, per gear tier
PROXY_G13_BASE = 20_000     # a bare G13 with no relic
PROXY_PER_RELIC = 2_800     # per DISPLAYED relic level on top of G13
PROXY_PER_STAR = 9_000      # ships, per star
RELIC_DISPLAY_OFFSET = 2    # roster `rt` is two higher than the level the game prints


def displayed_relic(unit):
    """The relic level the GAME shows, from the roster's `rt`.

    rt None (no relic) and rt 1 (locked / pre-G13) both floor to 0. See the
    RELIC_DISPLAY_OFFSET note — reading `rt` raw has burned this repo twice.
    """
    rt = unit.get("rt")
    if rt is None:
        return 0
    return max(0, rt - RELIC_DISPLAY_OFFSET)


def unit_power(unit):
    """Deployed power for one unit: the real `gp` when the roster carries it, else
    the documented proxy above. Never raises on a roster missing `gp`."""
    gp = unit.get("gp")
    if gp:
        return float(gp)
    if unit.get("ct", 1) == 2:
        return float(PROXY_PER_STAR * (unit.get("r") or 0))
    gear = unit.get("g") or 0
    if gear < 13:
        return float(PROXY_PER_GEAR * gear)
    return float(PROXY_G13_BASE + PROXY_PER_RELIC * displayed_relic(unit))


def map_roster(player, name_type_map):
    """Pure mapping: a comlink /player dict -> {"meta":..., "units":[...]}.

    Each unit: b(baseId), n(name), ct(combatType 1=char/2=ship), g(gear tier),
    r(rarity/stars), rt(relic level or None).

    ⚠ No per-unit `gp`/`o`/`z` — comlink does not return them. Use unit_power()
    for power; zetas/omicrons are simply not available from this source.
    """
    units = []
    for u in player.get("rosterUnit", []):
        base = u.get("definitionId", "").split(":")[0]
        info = name_type_map.get(base) or {"n": base, "ct": 1}
        units.append({
            "b": base,
            "n": info.get("n", base),
            "ct": info.get("ct", 1),
            "g": u.get("currentTier"),
            "r": u.get("currentRarity"),
            "rt": _relic_tier(u),
        })
    return {
        "meta": {
            "name": player.get("name"),
            "allyCode": player.get("allyCode"),
            "pulled": _TODAY,
            "count": len(units),
            "source": "comlink",
        },
        "units": units,
    }


def load_name_type_map(path=DEFAULT_MAP):
    with open(path) as f:
        return json.load(f)


def latest_roster_file():
    """Newest data/roster/swgoh_roster_fresh_<YYYYMMDD>.json, by the DATE IN THE NAME.

    Added 2026-08-18 because eight scripts each hardcoded a different roster date
    (20260718 / 20260731 / 20260805 / 20260810 / 20260812), so a fresh pull only
    reached whichever file someone remembered to edit and the rest silently kept
    planning against a two-to-four-week-old roster. Sort on the filename rather than
    mtime: re-saving an old pull must not make it look current.
    """
    import glob
    import re
    pat = os.path.join(ROOT, "data", "roster", "swgoh_roster_fresh_*.json")
    dated = []
    for f in glob.glob(pat):
        m = re.search(r"_(\d{8})\.json$", f)
        if m:
            dated.append((m.group(1), f))
    if not dated:
        raise FileNotFoundError(pat)
    return max(dated)[1]


def get_roster(allycode, url=None, name_type_map=None):
    """Live: fetch the roster from a self-hosted comlink and map it."""
    from swgoh_comlink import SwgohComlink
    client = SwgohComlink(url=url or DEFAULT_COMLINK_URL)
    player = client.get_player(allycode)
    return map_roster(player, name_type_map or load_name_type_map())


def load_roster(allycode="145357294", fallback_file=None, url=None):
    """Prefer a fresh comlink pull; fall back to a saved roster file if comlink is
    unreachable (or its client/lib is unavailable). Lets the pipeline keep running
    offline while always preferring live data when a comlink server is up."""
    try:
        return get_roster(allycode, url=url)
    except Exception:
        if not fallback_file:
            raise
        with open(fallback_file) as f:
            data = json.load(f)
        data.setdefault("meta", {})["source"] = "file-fallback"
        return data


def _parse_localization(text):
    """Parse a comlink Loc_*.txt bundle (`KEY|text` per line) into {key: text}."""
    out = {}
    for line in text.split("\n"):
        if not line or line.startswith("#") or "|" not in line:
            continue
        key, _, val = line.partition("|")
        out[key] = val
    return out


_UNIT_NAME_RE = re.compile(r"^UNIT_(.+)_NAME$")


def name_map_from_localization(loc):
    """Build {baseId: {n, ct}} from a localization map via the UNIT_<baseId>_NAME
    convention (verified live: UNIT_THIRDSISTER_NAME -> 'Third Sister'). combatType
    is unknowable from names alone and defaults to 1; refresh_name_map restores the
    real ct for owned units from the previous map."""
    m = {}
    for key, val in loc.items():
        mo = _UNIT_NAME_RE.match(key)
        if mo and val:
            m[mo.group(1)] = {"n": val, "ct": 1}
    return m


def refresh_name_map(url=None, path=DEFAULT_MAP, locale="Loc_ENG_US.txt"):
    """Rebuild data/name_type_map.json for ALL units (owned + unowned) from comlink
    localization, so gap units resolve to real names instead of baseIds. Localization
    carries no combatType, so the real ct for owned units is preserved from the
    existing map."""
    from swgoh_comlink import SwgohComlink
    c = SwgohComlink(url=url or DEFAULT_COMLINK_URL)
    md = c.get_metadata()
    bundle = c.get_localization(localization_id=md["latestLocalizationBundleVersion"], unzip=True)
    loc = _parse_localization(bundle[locale])
    m = name_map_from_localization(loc)
    if os.path.exists(path):  # preserve real combatType for owned units
        for base, info in load_name_type_map(path).items():
            if base in m and "ct" in info:
                m[base]["ct"] = info["ct"]
            elif base not in m:
                m[base] = info
    with open(path, "w") as f:
        json.dump(m, f, indent=0, sort_keys=True)
    return m


if __name__ == "__main__":
    import sys
    ally = sys.argv[1] if len(sys.argv) > 1 else "145357294"
    r = get_roster(ally)
    print(f"{r['meta']['name']}  units={r['meta']['count']}  pulled={r['meta']['pulled']}")
