#!/bin/bash
# h.sh: host-level driver for the BlueStacks window (used when `adb shell` is blocked).
# The Mac's logical screen is 1408x881, which is exactly a `sips -Z 1408` shrink of
# `screencapture`, so image coordinates and click coordinates are the same numbers.
#   ./scripts/h.sh cap [name]              screenshot -> /tmp/<name>.jpg
#   ./scripts/h.sh tap X Y [sleep] [name]  click then screenshot
#   ./scripts/h.sh dtap X Y [sleep] [name] double-click then screenshot
#   ./scripts/h.sh drag X1 Y1 X2 Y2 [sleep] [name]
#   ./scripts/h.sh key <keyname> [sleep]   cliclick kp:<keyname>
#   ./scripts/h.sh type "text"
CL=/opt/homebrew/bin/cliclick
Q="${H_Q:-45}"

shot() {
  local n="${1:-h}"
  screencapture -x /tmp/_raw.png 2>/dev/null
  sips -Z 1408 /tmp/_raw.png --out "/tmp/${n}.jpg" -s format jpeg -s formatOptions "$Q" >/dev/null 2>&1
  echo "cap /tmp/${n}.jpg"
}

case "$1" in
  cap)  shot "${2:-h}" ;;
  tap)  $CL "m:$2,$3" "c:$2,$3"; sleep "${4:-2}"; shot "${5:-h}" ;;
  dtap) $CL "m:$2,$3" "dc:$2,$3"; sleep "${4:-2}"; shot "${5:-h}" ;;
  drag) $CL "m:$2,$3" "dd:$2,$3" "m:$4,$5" "du:$4,$5"; sleep "${6:-2}"; shot "${7:-h}" ;;
  key)  $CL "kp:$2"; sleep "${3:-2}"; shot "${4:-h}" ;;
  type) $CL -w 20 "t:$2"; sleep "${3:-1}"; shot "${4:-h}" ;;
  *) echo "usage: h.sh cap|tap|dtap|drag|key|type ..." ;;
esac
