#!/bin/bash
# adb_r.sh: resilient adb for BlueStacks Air, which drops to "offline" constantly.
# Reconnects, then retries the command until the device answers.
#   ./scripts/adb_r.sh shell pm list packages -3
ADB=/opt/homebrew/bin/adb
SERIAL="${ANDROID_SERIAL:-emulator-5554}"

ensure() {
  local st
  st=$("$ADB" -s "$SERIAL" get-state 2>&1 | tr -d '\r')
  if [ "$st" != "device" ]; then
    "$ADB" connect 127.0.0.1:5555 >/dev/null 2>&1
    "$ADB" reconnect offline >/dev/null 2>&1
    sleep 3
  fi
}

for i in $(seq 1 12); do
  ensure
  out=$("$ADB" -s "$SERIAL" "$@" 2>&1)
  rc=$?
  if ! printf '%s' "$out" | grep -q 'device offline\|device .* not found\|no devices'; then
    printf '%s\n' "$out" | tr -d '\r'
    exit $rc
  fi
  sleep 3
done
echo "adb_r: gave up after 12 attempts: $out" >&2
exit 1
