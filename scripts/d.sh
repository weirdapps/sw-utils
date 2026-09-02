#!/bin/bash
# d.sh — tiny ADB driver for the BlueStacks SWGOH device.
#   ./scripts/d.sh tap X Y [sleep]     tap then screencap to /tmp/d.png
#   ./scripts/d.sh cap [name]          screencap only
#   ./scripts/d.sh swipe X1 Y1 X2 Y2 [ms]
#   ./scripts/d.sh back | home
export ANDROID_SERIAL="${ANDROID_SERIAL:-127.0.0.1:5555}"
ADB=/opt/homebrew/bin/adb
# Writes the native PNG (for the vision/OCR scripts) plus a 1100px q55 JPEG, which is
# what a Read should point at: the API cap is 30MB of BYTES, and a raw cap is ~1.9MB.
shot() {
  local n="${1:-d}"
  $ADB exec-out screencap -p > "/tmp/${n}.png" || return 1
  sips -Z 1100 "/tmp/${n}.png" --out "/tmp/${n}.jpg" -s format jpeg -s formatOptions 55 >/dev/null 2>&1
  echo "cap /tmp/${n}.jpg"
}
case "$1" in
  tap)   $ADB shell input tap "$2" "$3"; sleep "${4:-4}"; shot "${5:-d}" ;;
  # jtap: same, but in the coordinates of the 1100px-wide JPEG that shot() writes,
  # which is what gets Read. 1920/1100 = 1.745454...
  jtap)  x=$(awk "BEGIN{printf \"%d\", $2*1.7454545}"); y=$(awk "BEGIN{printf \"%d\", $3*1.7454545}")
         $ADB shell input tap "$x" "$y"; sleep "${4:-4}"; shot "${5:-d}" ;;
  jswipe) x1=$(awk "BEGIN{printf \"%d\", $2*1.7454545}"); y1=$(awk "BEGIN{printf \"%d\", $3*1.7454545}")
          x2=$(awk "BEGIN{printf \"%d\", $4*1.7454545}"); y2=$(awk "BEGIN{printf \"%d\", $5*1.7454545}")
          $ADB shell input swipe "$x1" "$y1" "$x2" "$y2" "${6:-400}"; sleep "${7:-3}"; shot "${8:-d}" ;;
  cap)   shot "${2:-d}" ;;
  swipe) $ADB shell input swipe "$2" "$3" "$4" "$5" "${6:-400}"; sleep "${7:-3}"; shot "${8:-d}" ;;
  back)  $ADB shell input keyevent 4; sleep "${2:-3}"; shot "${3:-d}" ;;
  *) echo "usage: d.sh tap X Y [sleep] [name] | cap [name] | swipe x1 y1 x2 y2 [ms] [sleep] [name] | back" ;;
esac
