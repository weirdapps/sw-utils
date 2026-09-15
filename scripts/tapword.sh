#!/bin/bash
# tapword.sh - find a word on the device screen by OCR and tap it (or just report it).
#
# Written after three failed attempts to hit a faction checkbox in SWGOH's
# SELECT FILTER dialog by dead reckoning: the list scrolls by a variable amount,
# so a hardcoded y is wrong as often as it is right. Tesseract's TSV output
# carries bounding boxes, so the label can be located instead of guessed.
#
#   ./scripts/tapword.sh REBEL              tap the word REBEL
#   ./scripts/tapword.sh REBEL --dx -60     tap 60px LEFT of it (checkboxes sit left of their label)
#   ./scripts/tapword.sh REBEL --dry        print where it is, tap nothing
#   ./scripts/tapword.sh --list             dump every word found, with coordinates
#
# Matching is case-insensitive and exact on the whole word, so REBEL does not
# match REBEL FIGHTER's second token. Prints "not found" and exits 1 on a miss,
# which is the signal to scroll and retry rather than tap blind.
set -uo pipefail
S="${ANDROID_SERIAL:-127.0.0.1:5555}"
ADB=/opt/homebrew/bin/adb
D="$HOME/Downloads"
SCALE=2

WORD="${1:-}"; shift || true
DX=0; DY=0; DRY=0
while [ $# -gt 0 ]; do
  case "$1" in
    --dx) DX="$2"; shift 2 ;;
    --dy) DY="$2"; shift 2 ;;
    --dry) DRY=1; shift ;;
    --checkbox) CHECKBOX=1; shift ;;
    *) shift ;;
  esac
done

$ADB -s "$S" exec-out screencap -p > "$D/tw_src.png" || exit 1
sips -Z $((1920 * SCALE)) "$D/tw_src.png" --out "$D/tw_big.png" >/dev/null 2>&1
tesseract "$D/tw_big.png" "$D/tw_out" --psm 6 tsv >/dev/null 2>&1

if [ "$WORD" = "--list" ]; then
  awk -F'\t' -v s="$SCALE" 'NR>1 && $12!="" && $11>40 {printf "%-22s %5d %5d  conf=%s\n", $12, ($7+$9/2)/s, ($8+$10/2)/s, $11}' "$D/tw_out.tsv"
  exit 0
fi

read -r X Y < <(awk -F'\t' -v w="$WORD" -v s="$SCALE" '
  NR>1 && $12!="" {
    t=toupper($12); gsub(/[^A-Z0-9]/,"",t)
    u=toupper(w);   gsub(/[^A-Z0-9]/,"",u)
    if (t==u && $11>40) { printf "%d %d\n", ($7+$9/2)/s, ($8+$10/2)/s; exit }
  }' "$D/tw_out.tsv")

if [ -z "${X:-}" ]; then echo "not found: $WORD"; exit 1; fi
# --checkbox: SWGOH's SELECT FILTER lays labels out in three columns whose
# checkboxes sit at fixed x. Snap to the column so a two-word label (LIGHT SIDE,
# SITH EMPIRE) is hit on its box rather than wherever the matched token landed.
if [ "${CHECKBOX:-0}" = "1" ]; then
  if   [ "$X" -lt 600 ];  then X=145
  elif [ "$X" -lt 1150 ]; then X=719
  else                         X=1292
  fi
fi
X=$((X + DX)); Y=$((Y + DY))
echo "$WORD at $X,$Y"
[ "$DRY" = "1" ] && exit 0
$ADB -s "$S" shell input tap "$X" "$Y"
sleep 2
