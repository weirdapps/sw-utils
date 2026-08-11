#!/usr/bin/env bash
# One-command mod session: spend whatever materials have arrived, in ladder order.
#
#   HU_SID=<live sessionId> ./scripts/mods_session.sh [--dry]
#
# Run this after every farming trip. It is idempotent and self-limiting: when a material
# is out the executors stop cleanly, so running it on an empty stock costs two API reads
# and changes nothing. Nothing here spends crystals.
#
# Capturing HU_SID (it rotates every session — never commit it):
#   browser_recipes.md §4. With Playwright MCP the Discord silent-SSO does NOT work
#   (that profile has no Discord session), so log in by hand once in the visible window,
#   then read the sessionId out of any api.hotutils.com XHR request body.
#
# Order is deliberate:
#   1. refresh the LADDER first  — invest_plan.py owns Arena -> GAC -> TB -> TW, and all
#      three mod scripts key off its output. A stale ladder spends materials in the wrong
#      order, which is unrecoverable once the salvage is gone.
#   2. slice/promote BEFORE calibrate — slicing raises a random secondary for salvage,
#      calibration re-rolls one for attenuators; they draw on different stocks, but a mod
#      must be 6A before calibration will touch it, so slicing can only add targets.
#   3. re-pull and re-score at the end so the delta is measured, not assumed.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
PY=.venv/bin/python
DRY=""
[ "${1:-}" = "--dry" ] && DRY="--dry"

if [ -z "${HU_SID:-}" ]; then
  echo "ERROR: set HU_SID to a live HotUtils sessionId (see the header of this file)." >&2
  exit 1
fi

echo "· refreshing the priority ladder…"
$PY scripts/invest_plan.py | tail -2

echo "· pulling live mods + materials…"
$PY scripts/pull_mods.py | tail -2

if [ -z "$DRY" ]; then
  echo "· reading mod score (before)…"
  $PY scripts/mod_score.py > /tmp/modscore_before.json
  cat /tmp/modscore_before.json
fi

echo
echo "· slicing / promoting…"
$PY scripts/execute_upgrades.py $DRY | tail -25

echo
echo "· calibrating (only mods that rolled BELOW expectation)…"
$PY scripts/calibrate.py --max 12 $DRY | tail -18

if [ -z "$DRY" ]; then
  echo
  echo "· re-pulling and re-scoring…"
  $PY scripts/pull_mods.py | tail -2
  $PY scripts/mod_score.py > /tmp/modscore_after.json
  $PY - <<'PY'
import json
b = json.load(open('/tmp/modscore_before.json'))
a = json.load(open('/tmp/modscore_after.json'))
print(f"\n{'metric':12} {'before':>14} {'after':>14} {'delta':>10}")
for k in ("modScore", "plusSpeed", "speed25", "speed20", "speed15", "mod6Dot",
          "credits", "attenuators"):
    x, y = b.get(k), a.get(k)
    if x is None or y is None:
        continue
    d = round(y - x, 2)
    print(f"{k:12} {x:>14,} {y:>14,} {d:>+10,}" if isinstance(x, int)
          else f"{k:12} {x:>14} {y:>14} {d:>+10}")
PY
fi

echo
echo "· refreshing the human queue view…"
$PY scripts/slice_plan.py | sed -n '12,22p'

echo
$PY scripts/execute_upgrades.py --dry --needs 20 | sed -n '/SHOPPING LIST/,$p'
