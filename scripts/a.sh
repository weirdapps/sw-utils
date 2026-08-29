#!/bin/zsh
# a.sh: one-liner ADB helper for the BlueStacks SWGOH device.
#   ./scripts/a.sh tap X Y [sleep]
#   ./scripts/a.sh swipe X1 Y1 X2 Y2 [ms] [sleep]
#   ./scripts/a.sh cap [outfile]      (default ~/Downloads/tw_now.png)
#   ./scripts/a.sh back
# Exists because inlining `A="adb -s ..."` into a compound command makes zsh
# treat the whole string as one filename.
ADB=(/opt/homebrew/bin/adb -s 127.0.0.1:5555)
case "$1" in
  tap)   $ADB shell input tap "$2" "$3"; sleep "${4:-3}" ;;
  swipe) $ADB shell input swipe "$2" "$3" "$4" "$5" "${6:-400}"; sleep "${7:-2}" ;;
  cap)   $ADB exec-out screencap -p > "${2:-$HOME/Downloads/tw_now.png}" ;;
  back)  $ADB shell input keyevent 4; sleep "${2:-3}" ;;
  *)     echo "usage: a.sh tap X Y [s] | swipe x1 y1 x2 y2 [ms] [s] | cap [f] | back [s]"; exit 1 ;;
esac
