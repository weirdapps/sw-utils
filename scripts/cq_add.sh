#!/bin/bash
# cq_add.sh: add one character to the first EMPTY slot on the Conquest squad screen.
#   ./scripts/cq_add.sh <search text> [result index 1-8]
# Units always land in the first empty slot, whichever slot you tapped, so slot order
# is just the order you call this in: slot 1 (the leader) is the first call.
# The search box matches ABILITY TEXT as well as names ("Partagaz" returns Emperor
# Palpatine first), which is why the result index is a parameter and not always 1.
set -e
export ANDROID_SERIAL="${ANDROID_SERIAL:-127.0.0.1:5555}"
ADB=/opt/homebrew/bin/adb
D="$(dirname "$0")/d.sh"

name="$1"
idx="${2:-1}"
# Two per row in the left-hand result strip.
col=$(( (idx - 1) % 2 ))
row=$(( (idx - 1) / 2 ))
rx=$(( 85 + col * 105 ))
ry=$(( 320 + row * 100 ))

"$D" jtap 150 235 1 _p >/dev/null          # open SELECT FILTER
"$D" jtap 300 549 1 _p >/dev/null          # focus the text box
$ADB shell input keyevent 123 >/dev/null 2>&1          # MOVE_END
for _ in $(seq 1 40); do $ADB shell input keyevent 67 >/dev/null 2>&1; done  # DEL
$ADB shell input text "${name// /%s}"
sleep 1
"$D" jtap 1053 582 1 _p >/dev/null         # OK, dismiss the IME
"$D" jtap 855 549 1 _p >/dev/null          # CONFIRM the filter
"$D" jtap "$rx" "$ry" 2 "${OUT:-add}"      # the chosen search result
