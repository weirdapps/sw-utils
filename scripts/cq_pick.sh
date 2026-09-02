#!/bin/bash
# cq_pick.sh: put one character into one slot on the Conquest SELECT SQUAD screen.
#   ./scripts/cq_pick.sh <slot 1-5> <search text>
# Slot 1 is the leader. The search box is the only sane way in: the roster list is
# 398 units of 40px icons, and the filter checkboxes cannot isolate a single name.
# Coordinates are in the 1100px-wide JPEG space that d.sh jtap uses.
set -e
export ANDROID_SERIAL="${ANDROID_SERIAL:-127.0.0.1:5555}"
ADB=/opt/homebrew/bin/adb
D="$(dirname "$0")/d.sh"

slot="$1"; shift
name="$*"

case "$slot" in
  1) sx=430; sy=196 ;;
  2) sx=694; sy=196 ;;
  3) sx=953; sy=196 ;;
  4) sx=430; sy=425 ;;
  5) sx=694; sy=425 ;;
  *) echo "slot must be 1-5"; exit 1 ;;
esac

"$D" jtap "$sx" "$sy" 1 _p >/dev/null      # focus the slot
"$D" jtap 150 235 1 _p >/dev/null          # open SELECT FILTER
"$D" jtap 300 549 1 _p >/dev/null          # focus the text box
$ADB shell input keyevent 123 >/dev/null 2>&1          # MOVE_END
# 40, not 24: a 24-char name like "Dark Trooper Moff Gideon" leaves a prefix behind and
# the next search then silently matches nothing.
for _ in $(seq 1 40); do $ADB shell input keyevent 67 >/dev/null 2>&1; done  # DEL
$ADB shell input text "${name// /%s}"
sleep 1
"$D" jtap 1053 582 1 _p >/dev/null         # OK, dismiss the IME
"$D" jtap 855 549 1 _p >/dev/null          # CONFIRM the filter
"$D" jtap 85 320 2 "${OUT:-pick}"          # first search result
