#!/bin/bash
# d.sh — tiny ADB driver for the BlueStacks SWGOH device.
#   ./scripts/d.sh tap X Y [sleep]     tap then screencap to /tmp/d.png
#   ./scripts/d.sh cap [name]          screencap only
#   ./scripts/d.sh swipe X1 Y1 X2 Y2 [ms]
#   ./scripts/d.sh back | home
export ANDROID_SERIAL="${ANDROID_SERIAL:-127.0.0.1:5555}"
ADB=/opt/homebrew/bin/adb
shot() { $ADB exec-out screencap -p > "/tmp/${1:-d}.png" && echo "cap /tmp/${1:-d}.png"; }
case "$1" in
  tap)   $ADB shell input tap "$2" "$3"; sleep "${4:-4}"; shot "${5:-d}" ;;
  cap)   shot "${2:-d}" ;;
  swipe) $ADB shell input swipe "$2" "$3" "$4" "$5" "${6:-400}"; sleep "${7:-3}"; shot "${8:-d}" ;;
  back)  $ADB shell input keyevent 4; sleep "${2:-3}"; shot "${3:-d}" ;;
  *) echo "usage: d.sh tap X Y [sleep] [name] | cap [name] | swipe x1 y1 x2 y2 [ms] [sleep] [name] | back" ;;
esac
