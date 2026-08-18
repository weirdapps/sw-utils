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


def map_roster(player, name_type_map):
    """Pure mapping: a comlink /player dict -> {"meta":..., "units":[...]}.

    Each unit: b(baseId), n(name), ct(combatType 1=char/2=ship), g(gear tier),
    r(rarity/stars), rt(relic level or None).
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
