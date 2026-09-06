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
  xy=$("$PY" scripts/cq_step.py --scan 2>/dev/null \
       | awk -F'[(),]' '/ring j=/ {print $2, $3; exit}')
  if [ -z "$xy" ]; then
    echo "[$i/$N] no reachable ring in view; stopping"
    exit 0
  fi
  echo "[$i/$N] node $xy"
  # cq_grind.play() owns the screen sequence: it re-arms AUTO up to three times, clears
  # the "squad is not full" modal, tells a half-drawn REWARDS card from a real defeat,
  # and returns a verdict. A hand-rolled tap chain does none of that and walked a run
  # into the Conquest inventory and then the EA Help chat on 2026-09-06.
  out=$("$PY" scripts/cq_grind.py --node $xy --runs 1 2>&1 | tail -2)
  echo "  $out"
  # cq_grind prints a per-node verdict AND a "wins=n/m" tally, and `*win*` matches the
  # tally, so a run of straight losses looked like a run of wins. Test the tally.
  case "$out" in *"wins=0/"*) echo "  stopping: not a win"; exit 1 ;; esac
done
