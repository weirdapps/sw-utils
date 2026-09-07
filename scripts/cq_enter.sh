#!/bin/bash
# cq_enter.sh: from the cantina hub, walk into a Conquest sector map.
#
#   ./scripts/cq_enter.sh 5      # land on the Sector 5 map
#
# Rediscovering this path costs eight taps and a handful of screenshots every time a
# battle drops you back at the hub (a stray tap on a reward card lands in INVENTORY,
# and backing out of THAT exits Conquest entirely). The cantina is a horizontal strip
# that always reopens at its default pan, so the swipes below are absolute, not relative.
set -e
cd "$(dirname "$0")/.."
D=./scripts/d.sh
N="${1:-5}"

# Pan the cantina to the far right, then back one notch: "Galactic Battles" ends up
# centred at (605,448). Going all the way right leaves it half under the ALLIES buttons.
for _ in 1 2 3; do $D jswipe 900 300 150 300 500 2 _e >/dev/null; done
$D jswipe 300 300 650 300 500 3 _e >/dev/null
$D jtap 605 448 5 _e >/dev/null          # the Galactic Battles table
$D jtap 741 534 7 _e >/dev/null          # CONQUEST / ENTER

# The sector list scrolls; each swipe advances it by about one and a half rows. Sectors
# 1 and 2 are on screen at rest, 3 needs a nudge, 4 and 5 need two.
case "$N" in
  1) $D jtap 645 246 8 _e >/dev/null ;;
  2) $D jtap 645 448 8 _e >/dev/null ;;
  3) $D jswipe 380 500 380 350 400 2 _e >/dev/null; $D jtap 645 489 8 _e >/dev/null ;;
  4) $D jswipe 380 500 380 150 500 2 _e >/dev/null; $D jtap 645 459 8 _e >/dev/null ;;
  5) $D jswipe 380 500 380 150 500 2 _e >/dev/null
     $D jswipe 380 500 380 200 500 2 _e >/dev/null; $D jtap 645 562 8 _e >/dev/null ;;
  *) echo "usage: cq_enter.sh 1|2|3|4|5"; exit 1 ;;
esac
$D cap live
