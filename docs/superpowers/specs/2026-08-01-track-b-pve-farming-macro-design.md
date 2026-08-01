# Track B — PvE Farming Execution Macro (Design)

- **Date:** 2026-08-01 · **Repo:** sw-utils
- **⚠️ Risk:** ToS violation / ban risk. Runs on Astra's Mac only. Owner has given informed consent.
- **Parent:** `2026-08-01-swgoh-automation-roadmap-design.md`

## Scope

- **IN:** automate execution of Astra's **own PvE farming** — sim 3-starred nodes
  (normal / hard / cantina / fleet energy), Galactic War auto-battle, daily energy dump,
  energy-refresh handling.
- **OUT (hard):** PvP combat (Squad/Fleet Arena, GAC, TW), any purchase / real-money action,
  anything played against human opponents.

## Environment (chosen)

Android **emulator on the Mac** — BlueStacks Air or MuMu Player (Apple Silicon), controlled via
**ADB**.
- *Alternatives considered:* spare real Android via USB+ADB (more reliable, real-device
  fingerprint, but needs a spare device); iOS (no ADB — rejected). Final emulator pick
  (BlueStacks Air vs MuMu) decided at setup; both expose ADB.

## Architecture

Python controller → **ADB** (`adb exec-out screencap`, `adb shell input tap/swipe`) →
**OpenCV template matching** on screenshots to detect UI state → per-task **state machine**.

**Modules** (`farmbot/`):
- `adb.py` — screencap + input wrappers
- `vision.py` — template matching (detect buttons/screens from reference PNGs)
- `tasks.py` — state machines per farm type (sim node, GW, energy dump)
- `run.py` — orchestrator; reads A3 advisor output for *what* to farm; standalone fallback = a
  manual node list in config
- `templates/` — reference UI screenshots (versioned per game build)

## Supervision (default)

**Supervised batch runs:** Astra launches a defined batch (e.g. "dump cantina energy on node X"),
it executes and **stops**. NOT 24/7 unattended — this reduces recklessness and limits damage if it
misbehaves. Human-like randomized delays between actions ("don't be obviously robotic / don't be
reckless" — **not** anti-cheat evasion).
- *Override:* Astra may opt into longer/unattended runs, accepting higher exposure — noted, not
  recommended.

## Failure handling (fail-safe)

Unknown/unexpected screen → **STOP + save a screenshot**. Never blind-tap. Kill-switch
(keypress or file flag). Hard cap on actions per run.

## Risk (blunt, restated)

ToS violation; detectable in principle (EA anti-cheat can read processes/RAM); game updates break
templates (needs re-capture → ongoing maintenance); **account loss is possible**. Accepted by the
owner. Fully isolated to the user's machine and account; **no third party affected** (PvE only).

## Dependencies

A3 (what to farm) preferred; standalone with a manual node list otherwise. A0 (roster) to know
farm targets.

## Success criteria

Astra launches a run and the day's PvE sims/energy get spent without manual tapping; unknown
states halt safely with a screenshot.
