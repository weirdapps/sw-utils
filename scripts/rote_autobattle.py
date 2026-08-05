#!/usr/bin/env python3
"""rote_autobattle.py — run ONE Rise of the Empire mission from an already-approved squad screen.

Starts AFTER the squad has been eyeballed. Each RotE mission is a single attempt and the game's
auto-fill will happily spend a gated unit (it put Jabba into the Qi'ra special, which would have
cost the 200K Jabba mission), so choosing the squad stays a human/agent decision. Everything from
"this squad is right" onward is identical every time, which is the part worth automating.

Why this replaces the bash version: that one tapped AUTO and the speed control on a fixed 12s
delay after BATTLE. The battle screen takes longer than that to load, so the taps were swallowed
by the loading screen and the fight ran at 1X — it still won 2/2 waves, but it overran the poll
window and the blind dismiss taps then wandered into a different planet. So:

  * wait for the battle HUD to actually exist (poll for the AUTO toggle) before touching it;
  * verify AUTO went green rather than assuming, since tapping an already-on AUTO turns it OFF;
  * the game REMEMBERS the speed setting, so match the 4X template and only tap if it isn't 4X
    (blind-cycling 1X->2X->4X->1X can land you slower than you started);
  * only tap CONTINUE once a result is actually on screen — never blind-tap to dismiss.

usage: rote_autobattle.py [--serial S] [--max-wait SEC] [--label TEXT]
"""
import argparse
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from farmbot import vision                                         # noqa: E402
from farmbot.adb import ADB                                        # noqa: E402

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
TEMPLATES = os.path.join(ROOT, "farmbot", "templates")

SQUAD_BATTLE = (1707, 1008)
AUTO_BTN = (281, 66)
SPEED_BTN = (390, 55)
CONTINUE_BTN = (960, 682)
AUTO_RING = (250, 35, 315, 100)      # crop around the AUTO toggle; green ring == engaged
RESULT_MARKERS = ("rote_results", "victory", "celebration_continue")


def grab(dev):
    return vision.to_gray(dev.screencap().convert("RGB"))


def matches(screen, tpls, name):
    if name not in tpls:
        return 0.0
    m = vision.find(screen, tpls[name], threshold=0.0)
    return m.confidence if m else 0.0


def auto_is_on(dev):
    """The AUTO ring renders green when engaged and blue when idle.

    Grayscale template matching cannot tell those apart, so this reads colour directly.
    Measured live: 0.000 green when off, 0.487 when on — the 0.12 gate is nowhere near either.
    """
    im = dev.screencap().convert("RGB").crop(AUTO_RING)
    px = list(im.get_flattened_data() if hasattr(im, "get_flattened_data") else im.getdata())
    green = sum(1 for r, g, b in px if g > 110 and g > b + 25 and r < g)
    return green > len(px) * 0.12


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--serial", default="127.0.0.1:5555")
    ap.add_argument("--max-wait", type=float, default=480.0)
    ap.add_argument("--label", default="mission")
    ap.add_argument("--no-start", action="store_true",
                    help="battle is already running; skip the squad-screen BATTLE tap")
    args = ap.parse_args()

    dev = ADB(args.serial)
    tpls = vision.load_templates(TEMPLATES)

    if args.no_start:
        print(f"[{args.label}] attaching to a battle already in progress")
    else:
        print(f"[{args.label}] BATTLE (squad screen)")
        dev.tap(*SQUAD_BATTLE)

    # 1. wait for the battle HUD to exist. A result marker here would mean the fight was
    #    already over (shouldn't happen), so watch for both.
    deadline = time.time() + 120
    hud = False
    while time.time() < deadline:
        time.sleep(4)
        s = grab(dev)
        # Either chrome marker proves the battle screen is up. battle_speed is needed for the
        # --no-start path: re-attaching to a fight that already has AUTO engaged never matches
        # battle_auto (captured off), so checking it alone reported "no-battle-screen" for two
        # solid minutes while the fight was visibly on screen.
        if any(matches(s, tpls, n) >= 0.85 for n in ("battle_auto", "battle_speed")):
            hud = True
            break
        if any(matches(s, tpls, n) >= 0.90 for n in RESULT_MARKERS):
            print(f"[{args.label}] result already on screen")
            hud = True
            break
    if not hud:
        print(f"[{args.label}] RESULT=no-battle-screen")
        return 2
    print(f"[{args.label}] battle HUD up")

    # 2. AUTO on, verified (tapping an already-on AUTO would turn it off and stall the fight)
    for _ in range(3):
        if auto_is_on(dev):
            break
        dev.tap(*AUTO_BTN)
        time.sleep(1.5)
    print(f"[{args.label}] auto={auto_is_on(dev)}")

    # 3. speed to 4X, verified. The setting persists between battles, so usually a no-op.
    for _ in range(4):
        if matches(grab(dev), tpls, "battle_speed") >= 0.85:
            break
        dev.tap(*SPEED_BTN)
        time.sleep(1.2)
    print(f"[{args.label}] speed4x={matches(grab(dev), tpls, 'battle_speed') >= 0.85}")

    # 4. poll for the result
    outcome, waited, hud_gone = "timeout", 0.0, 0
    while waited < args.max_wait:
        time.sleep(10)
        waited += 10
        s = grab(dev)
        if matches(s, tpls, "defeat") >= 0.90:
            outcome = "defeat"
            break
        if any(matches(s, tpls, n) >= 0.90 for n in RESULT_MARKERS):
            outcome = "win"
            break
        # The RotE results banner is not reliably matchable and the game advances past it on its
        # own (measured live on the Lord Vader mission: won 2/2 waves, credited 200K TP, yet every
        # result marker stayed below threshold for the full 300s). So also treat "the battle HUD
        # has vanished" as the fight being over. Three consecutive misses, because the HUD also
        # blinks out during a wave transition — that never lasts 30s.
        #
        # The marker is the 4X SPEED chip, NOT the AUTO toggle: battle_auto was captured with AUTO
        # off, so it stops matching the instant step 2 turns AUTO green. Using it here called a
        # live 2-wave fight "ended" at 30s while Jabba was still swinging. Speed is set once and
        # never changes mid-battle, so the chip is present for exactly as long as the fight is.
        if matches(s, tpls, "battle_speed") < 0.85:
            hud_gone += 1
            if hud_gone >= 3:
                outcome = "ended"
                break
        else:
            hud_gone = 0
        if int(waited) % 60 == 0:
            print(f"[{args.label}]   {int(waited)}s ...")

    print(f"[{args.label}] outcome={outcome} after {int(waited)}s")

    # 5. dismiss ONLY on a real result, and stop as soon as the banner is gone. The previous
    #    version's unconditional second tap landed on the galaxy map and opened another planet.
    if outcome in ("win", "defeat"):
        for _ in range(4):
            dev.tap(*CONTINUE_BTN)
            time.sleep(4)
            s = grab(dev)
            if not any(matches(s, tpls, n) >= 0.90 for n in RESULT_MARKERS + ("defeat",)):
                break
    # "ended" gets no CONTINUE taps: the banner is already gone, and blind-tapping the map is how
    # an earlier version wandered into a different planet.
    print(f"RESULT={outcome}")
    return 0 if outcome in ("win", "ended") else 1


if __name__ == "__main__":
    sys.exit(main())
