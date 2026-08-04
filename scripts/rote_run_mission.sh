#!/usr/bin/env bash
# rote_run_mission.sh — drive ONE already-open Rise of the Empire combat mission to its result.
#
# Assumes the mission's detail panel is on screen (BATTLE (n) visible on the right). Taps through
# BATTLE -> squad screen -> BATTLE -> enables AUTO and max speed -> waits for the RESULTS banner ->
# dismisses it, leaving the territory map showing.
#
# Deliberately NOT part of farmbot/: which icon is a mission moves every phase and every TB, so the
# icon-tapping stays human-driven. Everything after "a mission is open" is identical every time,
# which is exactly the part worth scripting.
#
# A LOSS IS STILL WORTH RUNNING: the squad's galactic power is credited as territory deployment
# either way (device-verified 2026-08-03 — a lost battle logged "Astra: Deployed 152,326 points").
#
# usage: rote_run_mission.sh [serial] [max_wait_seconds]
set -uo pipefail
S="${1:-127.0.0.1:5555}"
MAX_WAIT="${2:-180}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PY="$ROOT/.venv/bin/python"

tap() { adb -s "$S" shell input tap "$1" "$2" >/dev/null; sleep "${3:-2}"; }
shot() { adb -s "$S" exec-out screencap -p > "$1"; }
match() { "$PY" -m farmbot.devtool find "$1" 2>/dev/null | awk '{print $2}' | grep -o '0\.[0-9]*' | head -1; }

echo "==> BATTLE on the mission panel"
tap 1490 1008 6

echo "==> BATTLE on the squad screen (the game pre-fills a themed squad)"
tap 1707 1008 9

echo "==> AUTO on, speed to max"
tap 267 53 2
for _ in 1 2 3; do tap 390 55 1; done      # speed cycles 1X -> 2X -> 4X

echo "==> waiting for the result (up to ${MAX_WAIT}s)"
waited=0
while [ "$waited" -lt "$MAX_WAIT" ]; do
  sleep 10; waited=$((waited + 10))
  shot /tmp/rote_wait.png
  conf=$("$PY" - <<PY
from PIL import Image
from farmbot import vision
s = vision.to_gray(Image.open('/tmp/rote_wait.png').convert('RGB'))
t = vision.load_templates('$ROOT/farmbot/templates')
best = 0.0
for n in ('rote_results', 'victory', 'celebration_continue'):
    if n in t:
        m = vision.find(s, t[n], threshold=0.0)
        best = max(best, m.confidence if m else 0.0)
print(f"{best:.3f}")
PY
)
  echo "    ${waited}s  result-marker conf=${conf}"
  case "$conf" in 0.9*|1.*) break ;; esac
done

echo "==> dismissing the result"
tap 960 540 5
tap 960 540 4
shot /tmp/rote_after_mission.png
echo "done — /tmp/rote_after_mission.png"
