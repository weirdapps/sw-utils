#!/bin/bash
# turn.sh — one-shot battle-state inspector for driving SWGOH fights by hand.
#   ./scripts/turn.sh            just look
#   ./scripts/turn.sh X Y [wait] tap, wait, then look
# Stacks the three regions that actually matter into ONE image, so a manual turn
# costs one Read instead of three: score/boss-debuff HUD, squad bars, ability bar.
export ANDROID_SERIAL="${ANDROID_SERIAL:-127.0.0.1:5555}"
ADB=/opt/homebrew/bin/adb
if [ -n "$2" ]; then $ADB shell input tap "$1" "$2"; sleep "${3:-4}"; fi
$ADB exec-out screencap -p > /tmp/turn_raw.png
python3 - <<'PY'
from PIL import Image
im = Image.open('/tmp/turn_raw.png')
# (label, box) — HUD carries score + the boss's debuff row; bars show who is alive
# and who has turn meter; the ability bar names the acting unit via its portraits.
regions = [((900, 0, 1920, 210), 1.10),      # score / % / boss buff-debuff icons
           ((300, 620, 1300, 800), 1.10),    # squad health + turn-meter bars
           ((1080, 900, 1920, 1070), 1.10)]  # ability bar (right-aligned)
crops = []
for box, s in regions:
    c = im.crop(box)
    crops.append(c.resize((int(c.width * s), int(c.height * s)), Image.LANCZOS))
W = max(c.width for c in crops)
H = sum(c.height for c in crops) + 8 * (len(crops) - 1)
sheet = Image.new('RGB', (W, H), (12, 12, 16))
y = 0
for c in crops:
    sheet.paste(c, (0, y)); y += c.height + 8
sheet.save('/tmp/turn.png')
print('turn.png', sheet.size)
PY
