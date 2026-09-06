#!/bin/bash
# cq_node.sh: play ONE Conquest node from an open Combat Details panel, on auto at 4x.
#
#   ./scripts/cq_node.sh            # panel already open
#   ./scripts/cq_node.sh 776 275    # tap the node first, in 1100-space
#
# Deliberately dumb and coordinate-driven. cq_step.py tries to find the frontier by
# vision and lost it twice on sector 4 (`stuck:map`), which also walked the run out of
# the sector; a caller that reads the map itself and passes coordinates never does.
#
# ⚠ The squad PERSISTS between Conquest battles, so the squad screen is one BATTLE tap.
# Never navigate away from it: backing out discards the squad and every later fight
# silently runs the previous one (memory/notes.md 2026-09-03).
# ⚠ Never blind-tap to dismiss the reward card. (549,536) is the CONTINUE button but it
# is also the guild-chat bar one screen later, and a stray pair of taps walked a run
# into the EA Help support chat. Poll for the green button instead.
set -e
cd "$(dirname "$0")/.."
D=./scripts/d.sh
PY="${SWPY:-$HOME/Downloads/swvenv/bin/python}"

[ $# -eq 2 ] && $D jtap "$1" "$2" 4 _n >/dev/null

$D jtap 900 573 6 _n >/dev/null      # panel BATTLE
$D jtap 925 577 8 _n >/dev/null      # squad screen BATTLE
"$PY" scripts/autofight.py

# Dismiss whatever card the fight ended on, but only while a green button is really there.
for _ in 1 2 3 4 5 6; do
  sleep 3
  $D cap _n >/dev/null
  hit=$("$PY" - <<'EOF'
from PIL import Image
K = 1920 / 1100.0
im = Image.open('/tmp/_n.png').convert('RGB')
for y in range(500, 560, 6):
    for x in range(430, 680, 10):
        r, g, b = im.getpixel((int(x * K), int(y * K)))
        if g > 150 and g > r + 50 and g > b + 50:
            print(f"{x} {y}"); raise SystemExit
print("")
EOF
)
  [ -z "$hit" ] && break
  $D jtap ${hit% *} ${hit#* } 3 _n >/dev/null
done
