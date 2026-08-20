#!/bin/bash
# tw_attack.sh — drive ONE Territory War offense battle, from the enemy list to the result banner.
#
# Split into three stops because two of them are genuine decisions the screen has to answer:
# which enemy squad (only "Battles: 0" rows carry the +10 first-attempt bonus) and which saved
# preset still has all five units unused. Everything between those is identical every time.
#
#   ./scripts/tw_attack.sh list        dismiss any result banner, shoot the enemy-squad list
#   ./scripts/tw_attack.sh target Y    tap the enemy row at Y, open SELECT SQUAD, shoot the presets
#   ./scripts/tw_attack.sh go Y        load the preset at Y, then BATTLE -> AUTO -> wait -> result
#
# `go` refuses to fire if BATTLE never goes green: that is what a preset whose units are already
# spent looks like (the game raises RESTRICTED CHARACTERS and leaves the squad empty), and blind-
# tapping past it would attack with whatever was staged before.
set -uo pipefail
export ANDROID_SERIAL="${ANDROID_SERIAL:-127.0.0.1:5555}"
ADB=/opt/homebrew/bin/adb
PY=/opt/homebrew/bin/python3

SELECT_SQUAD=(1210 1007)
BATTLE=(1660 1007)
AUTO=(281 66)

tap()  { $ADB shell input tap "$1" "$2" >/dev/null; sleep "${3:-3}"; }
shot() { $ADB exec-out screencap -p > "$1"; }

# green? FILE x0 y0 x1 y1 -> prints 1 when that crop is dominated by the UI's green "enabled" tint
green() {
  $PY - "$@" <<'PY'
import sys
from PIL import Image
f, x0, y0, x1, y1 = sys.argv[1], *map(int, sys.argv[2:6])
px = Image.open(f).convert("RGB").crop((x0, y0, x1, y1)).getdata()
hits = sum(1 for r, g, b in px if g > r + 30 and g > b + 30)
print(1 if hits > 0.18 * len(px) else 0)
PY
}

# hud? FILE -> 1 while the in-battle HUD is up. The settings gear sits in a bright blue disc in the
# top-left of every fight and nowhere else, so losing it means the battle ended. This is the probe
# the result poll keys off: the AUTO toggle blanks during ability animations and reinforcement
# cut-aways, so "AUTO went away" reads as "finished" while the fight is still running.
hud() {
  $PY - "$1" <<'PY'
import sys
from PIL import Image
px = Image.open(sys.argv[1]).convert("RGB").crop((40, 40, 95, 95)).getdata()
hits = sum(1 for r, g, b in px if b > 120 and b > r + 30)
print(1 if hits > 0.15 * len(px) else 0)
PY
}

case "${1:-}" in
list)
  tap 960 540 12                     # dismissing the banner reloads the list; 3s lands on "Loading ..."
  shot /tmp/tw_list.png
  echo "enemy list -> /tmp/tw_list.png"
  ;;

target)
  tap 960 "${2:?need a row Y}" 4
  tap "${SELECT_SQUAD[@]}" 4
  shot /tmp/tw_presets.png
  echo "presets -> /tmp/tw_presets.png"
  ;;

go)
  tap 600 "${2:?need a preset Y}" 4
  shot /tmp/tw_staged.png
  # RESTRICTED CHARACTERS: the preset holds a unit already spent on TW defense or an earlier
  # attack. Its CONTINUE would stage a SHORT squad, so cancel out and leave the browser usable.
  if [ "$(green /tmp/tw_staged.png 1000 685 1390 740)" = "1" ]; then
    tap 730 710 3
    echo "ABORT: RESTRICTED CHARACTERS — that preset has spent units. Cancelled; pick another."
    exit 1
  fi
  if [ "$(green /tmp/tw_staged.png 1580 985 1740 1030)" != "1" ]; then
    echo "ABORT: BATTLE is not green — the preset did not load. See /tmp/tw_staged.png"; exit 1
  fi
  exec "$0" fire
  ;;

fire)
  echo "==> BATTLE"
  tap "${BATTLE[@]}" 12
  # The first taps land while the fight is still loading and are swallowed, so keep tapping until
  # the toggle actually reads green. Tapping blind is worse than useless: an even number of taps
  # that DO register leaves AUTO off, and an unattended fight just burns its clock down to a loss.
  auto=0
  for _ in 1 2 3 4 5; do
    tap "${AUTO[@]}" 3
    shot /tmp/tw_auto.png
    [ "$(green /tmp/tw_auto.png 250 35 315 100)" = "1" ] && { auto=1; break; }
    echo "    AUTO not engaged yet, retrying"
    sleep 5
  done
  if [ "$auto" = "1" ]; then
    echo "==> AUTO on, waiting for the result"
  else
    echo "==> WARNING: AUTO never went green — the fight is running MANUALLY and will time out."
    echo "    Drive it with scripts/turn.sh, or tap ${AUTO[*]} by hand. Still polling."
  fi
  waited=0; off=0
  while [ "$waited" -lt 480 ]; do
    sleep 10; waited=$((waited + 10))
    shot /tmp/tw_poll.png
    if [ "$(hud /tmp/tw_poll.png)" = "1" ]; then
      off=0
    else
      off=$((off + 1))                # HUD gone for 3 straight polls == fight is genuinely over
      [ "$off" -ge 3 ] && break       # (2 was not enough: animations blank it for one poll)
    fi
  done
  sleep 3
  shot /tmp/tw_result.png
  echo "result after ${waited}s -> /tmp/tw_result.png"
  ;;

*) sed -n '2,12p' "$0" ;;
esac
