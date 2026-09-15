#!/bin/bash
# ocr.sh - screencap a region of the BlueStacks device and OCR it locally.
#
# Exists because the Read tool's image budget is the real constraint in a long
# device session (30MB of base64 kills the API call, and a full 1100px JPEG is
# ~130KB of it). Tesseract reads the numbers that actually matter, the RESULTS
# banner, the territory point counter, the activity feed, for zero budget.
#
#   ./scripts/ocr.sh                 whole screen
#   ./scripts/ocr.sh panel           the right-hand territory panel
#   ./scripts/ocr.sh result          the centre RESULTS banner
#   ./scripts/ocr.sh head            planet name + phase timer
#   ./scripts/ocr.sh X Y W H         an arbitrary region, device pixels
#
# Device is 1920x1080. sips crop args are: -c HEIGHT WIDTH --cropOffset Y X.
set -uo pipefail
S="${ANDROID_SERIAL:-127.0.0.1:5555}"
ADB=/opt/homebrew/bin/adb

case "${1:-full}" in
  panel)  X=1060; Y=140; W=860;  H=920 ;;
  result) X=400;  Y=380; W=1150; H=440 ;;
  head)   X=0;    Y=0;   W=760;  H=250 ;;
  full)   X=0;    Y=0;   W=1920; H=1080 ;;
  *)      X="$1"; Y="$2"; W="$3"; H="$4" ;;
esac

$ADB -s "$S" exec-out screencap -p > "$HOME"/Downloads/ocr_src.png || exit 1
sips -c "$H" "$W" --cropOffset "$Y" "$X" "$HOME"/Downloads/ocr_src.png --out "$HOME"/Downloads/ocr_crop.png >/dev/null 2>&1
# Upscale: tesseract is much better on large glyphs, and the game font is thin.
sips -Z $((W * 2)) "$HOME"/Downloads/ocr_crop.png --out "$HOME"/Downloads/ocr_big.png >/dev/null 2>&1
tesseract "$HOME"/Downloads/ocr_big.png - --psm 6 2>/dev/null | grep -v '^[[:space:]]*$'
