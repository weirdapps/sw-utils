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
from datetime import datetime

try:
    from zoneinfo import ZoneInfo
    _TODAY = datetime.now(ZoneInfo("Europe/Athens")).strftime("%Y-%m-%d")
except Exception:
    _TODAY = datetime.now().strftime("%Y-%m-%d")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_MAP = os.path.join(ROOT, "data", "name_type_map.json")
DEFAULT_COMLINK_URL = os.environ.get("COMLINK_URL", "http://localhost:3000")


def _relic_level(unit):
    """comlink relic.currentTier is the displayed relic level + 2 (None if unset)."""
    relic = unit.get("relic")
    if not relic:
        return None
    tier = relic.get("currentTier")
    if tier is None:
        return None
    level = tier - 2
    return level if level > 0 else None


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
            "rt": _relic_level(u),
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


def get_roster(allycode, url=None, name_type_map=None):
    """Live: fetch the roster from a self-hosted comlink and map it."""
    from swgoh_comlink import SwgohComlink
    client = SwgohComlink(url=url or DEFAULT_COMLINK_URL)
    player = client.get_player(allycode)
    return map_roster(player, name_type_map or load_name_type_map())


if __name__ == "__main__":
    import sys
    ally = sys.argv[1] if len(sys.argv) > 1 else "145357294"
    r = get_roster(ally)
    print(f"{r['meta']['name']}  units={r['meta']['count']}  pulled={r['meta']['pulled']}")
