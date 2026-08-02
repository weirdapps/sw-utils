# Track B — Energy-Dump MVP (Design)

- **Date:** 2026-08-02 · **Repo:** sw-utils
- **⚠️ Risk:** ToS violation / ban risk. Runs on Astra's Mac only. Owner has given informed consent.
- **Parent:** `2026-08-01-track-b-pve-farming-macro-design.md` (overview)
- **Relationship:** This spec is the **first concrete slice (B1-MVP)** of the Track B overview. It
  narrows the overview's `farmbot/` architecture to a single, well-bounded task — **energy dump
  (sim 3★ nodes)** — to prove the full pipeline (screencap → detect → tap → verify → loop →
  safe-stop) end-to-end before generalizing to GW / challenges / A3-driven farming.

## Goal

Remove the single largest daily grind — spending the day's energy by hand — by driving native
in-game **sim** of already-3★ nodes through an Android emulator, safely and supervised. Success =
Astra launches one run, the day's current energy gets spent without manual tapping, and any unknown
state halts safely with a screenshot.

## Decisions locked (from brainstorming, 2026-08-02)

| Decision | Choice | Rationale |
|----------|--------|-----------|
| MVP task | **Energy dump** (sim 3★ nodes) | Biggest daily grind; safest (pure menu taps, native sim — no combat-input simulation); node-stable day to day. |
| Perception/nav | **Vision-guided state machine** (Approach A) | Only option honoring "never blind-tap, halt-on-unknown"; the vision + state-machine layer is reused by every later task. Coordinate-replay (B) rejected as blind/unsafe; hybrid (C) is the fallback if template work proves heavy. |
| Emulator | **BlueStacks Air** (Apple Silicon); MuMu = fallback | User had no preference. Controller is ADB-based, so emulator-agnostic; templates + setup bind to one. |
| Crystal refresh | **Never** — dump current energy only, then stop | Keeps the macro away from premium currency; smaller, safer MVP. |
| A3 integration | **Deferred** — MVP uses a hand-authored node config | Energy dump is node-stable, not unit-driven; matches the overview's "standalone fallback = manual node list." |

## Scope

- ✅ **IN:** energy dump only (sim 3★ nodes across the campaigns the user lists); BlueStacks Air +
  ADB; vision-guided state machine; halt-on-unknown + action cap + kill-switch; supervised batch run
  that stops when done; randomized human-like delays.
- ⛔ **OUT (v2+):** Galactic War auto, daily challenges, A3-driven shard farming, energy auto-refresh
  (crystals), collecting scheduled free-energy grants, anything PvP (Arena / GAC / TW), any
  real-money / purchase action, any account-credential handling.

## Prerequisite (user's manual, one-time)

Not code — a setup section the user performs on their own machine and account:

1. Install **BlueStacks Air** (Apple Silicon).
2. Install SWGOH inside it; **log in as Astra** (the agent never touches game credentials).
3. Enable ADB (BlueStacks: Settings → Advanced → Android Debug Bridge) and note the
   `device_serial` (e.g. `emulator-5554` or the `127.0.0.1:<port>` shown).
4. Verify `adb devices` lists the emulator from a terminal (install platform-tools if `adb` is not
   on PATH — it currently is not).

Bootstrapping the templates + node list (supervised, one-time, code-assisted) is a separate step
described under Config and `capture`.

## Architecture

New package `farmbot/`. All device I/O is isolated behind `adb.py` + `vision.py` so everything else
is deterministically unit-testable without a live device.

| Module | Responsibility | Depends on |
|--------|----------------|------------|
| `adb.py` | ADB wrappers: `screencap()` → PIL/numpy image, `tap(x,y)`, `swipe(...)`, `device_ready()`. Thin layer over `subprocess`. | `adb` binary |
| `vision.py` | OpenCV template matching: `find(tpl, screen)` → `(location, confidence)` \| `None`; `wait_for(tpl, timeout)` polls fresh screencaps until match or timeout; relative-tap helpers. Loads reference PNGs from `templates/`. | `adb`, `templates/` |
| `tasks.py` | `EnergyDumpTask` — the sim-node flow as an explicit state machine. Consumes injected `screen_provider` + `tapper` interfaces (not concrete `adb`/`vision`) so it is fully testable. | vision/adb *interfaces* |
| `run.py` | CLI/orchestrator: parse args (`--dump`, `--capture`, `--dry-run`), load config, connect ADB, run the task, enforce caps + kill-switch, print summary, set exit code. | all of the above |
| `capture.py` (or `run.py --capture`) | Interactive template capture: screencap the emulator → user crops/labels a region → save PNG to `templates/`. Bootstrapping helper. | `adb` |
| `templates/` | Reference UI PNGs, **versioned per game build** (game updates → re-capture). | — |
| `config.json` | Node list + settings (caps, delays, match threshold, device serial). Hand-authored in the MVP. | — |
| `halts/` | Screenshots + logs written when a run halts on an unknown state. | — |

## Data flow (one `run.py --dump`)

1. Load `config.json` (node list + caps); `adb.device_ready()` — else halt.
2. For each configured node, `EnergyDumpTask` steps its state machine:
   `HOME → OPEN_CAMPAIGN → NAVIGATE_TO_NODE → NODE_PANEL → SIM_DIALOG → SET_MAX_QTY → CONFIRM → COLLECT_REWARDS → BACK → (next node)`.
   (Exact screen/button templates are pinned during capture; state names are the contract, not the
   in-game labels.)
3. At every state: `vision.wait_for(expected_template)` on a fresh `screencap()` → tap relative to
   the match → verify the next expected screen appears.
4. **Energy-exhaustion detection:** when the Sim/Confirm control is disabled or a "not enough
   energy" template appears, that energy type is done → move to the next node (of another energy
   type) or stop. Never refresh with crystals.
5. Randomized human-like delay between actions (`action_delay_ms` range).
6. Termination — all nodes done ∥ energy out ∥ action cap hit ∥ kill-switch — prints a **summary**
   (nodes attempted, sims done, halts) and exits with a status code.

## Error handling & safety

- **Halt-on-unknown:** any unexpected screen or state timeout → STOP, save
  `halts/<ts>_<state>.png` + a log line, exit non-zero. Never blind-tap.
- **Gated taps:** every tap is gated by a successful template match (only relative-to-match offsets;
  no hardcoded absolute coordinates).
- **Kill-switch (two mechanisms):** SIGINT (Ctrl-C) instant abort **and** a `farmbot/STOP` file flag
  polled each iteration.
- **Hard action cap:** `max_actions` per run — a runaway-loop backstop.
- **Randomized delays:** human-like pacing — explicitly *not* anti-cheat evasion, just "don't be
  reckless/robotic."
- **ADB resilience:** screencap/device failure → 2–3 retries → else halt.
- **Idempotent by nature:** re-running is safe — sim only spends whatever energy remains; no
  destructive state.

## Config shape (`farmbot/config.json`)

```jsonc
{
  "device_serial": "emulator-5554",
  "caps": { "max_actions": 400, "action_delay_ms": [700, 1800] },
  "vision": { "match_threshold": 0.88 },
  "nodes": [
    { "campaign": "cantina", "node": "5-D", "sim": "max" },
    { "campaign": "dark", "difficulty": "hard", "node": "6-E", "sim": "max" }
  ]
}
```

The node list is hand-authored once (the user's own 3★ nodes). The exact node schema — campaign
taxonomy (`light` / `dark` / `cantina` / `fleet` / …), whether `difficulty` (`normal` / `hard`)
applies, and any navigation hints — is finalized during template capture, since it must match the
real in-game navigation. Templates are captured via `run.py --capture` on the user's emulator — a
supervised bootstrapping step.

## Testing

- `vision.py` — pure and unit-testable: fixtures are saved screenshot+template PNG pairs; assert
  match location/confidence, assert `None` on absence.
- `tasks.py` — drive the state machine with a **fake screen provider + fake tapper**: a scripted
  screen sequence → assert the correct tap sequence and transitions; a separate test asserts an
  unexpected screen → halt.
- `adb.py` — **mock `subprocess.run`** (assert the correct adb command strings) — consistent with
  the repo's existing subprocess-mocking convention.
- `run.py` — arg parsing, config loading, cap/kill-switch logic with fakes.
- Live-emulator integration is **manual and supervised** (a real device is not unit-testable); this
  is precisely why all device I/O is isolated behind `adb.py`/`vision.py`.

## Dependencies

- New Python deps (into `.venv`): OpenCV (`opencv-python`) + Pillow/NumPy for image handling.
- Android platform-tools (`adb`) on PATH.
- A3 advisor: not required for the MVP (deferred).

## Success criteria

- Astra runs `python farmbot/run.py --dump`; the day's current energy is spent via native sim
  across the configured nodes, with no manual tapping.
- An unknown or unexpected screen halts the run safely with a screenshot — nothing blind-tapped.
- `vision`, `tasks`, `adb`, and `run` logic are covered by deterministic unit tests that run with no
  emulator attached.
