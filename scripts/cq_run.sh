#!/bin/bash
# cq_run.sh: scan the Conquest sector for the next playable node and play it, N times.
#
#   ./scripts/cq_run.sh 8
#
# The split matters: cq_step.py's own runner both FINDS and PLAYS, and when its vision
# lost the frontier it kept navigating and walked out of the sector. Here `--scan` is
# used for what it is good at (naming the reachable rings) and nothing else, and
# cq_node.sh plays a coordinate. If the scan finds nothing the run stops where it is,
# on the map, with the sector intact.
set -e
cd "$(dirname "$0")/.."
PY="${SWPY:-$HOME/Downloads/swvenv/bin/python}"
N="${1:-5}"

for i in $(seq 1 "$N"); do
  # Only rings ADJACENT to the token. `cq_step.py --scan` lists every bright ring on
  # screen and its order repeatedly put an unreachable far-edge node first, which stalls
  # the run with "screen was not where the script expected"; the map does not recentre
  # after a probe, so "nearest the middle" is no better. cq_next.py measures from the
  # token itself.
  xy=$("$PY" scripts/cq_next.py --first 2>/dev/null)
  if [ -z "$xy" ]; then
    echo "[$i/$N] no reachable ring in view; stopping"
    exit 0
  fi
  echo "[$i/$N] node $xy"
  out=$(cd scripts && "$PY" cq_play.py $xy 2>&1 | tail -1)
  echo "  $out"
  case "$out" in win*) ;; *) echo "  stopping: $out"; exit 1 ;; esac
done
