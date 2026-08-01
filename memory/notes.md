# Notes — durable facts (update when they change)

## Player
- Astra · ally 145357294 · Kyber 3 (→ Kyber 2) · ~14M GP · 326 chars (314 G13+), 69 ships (10 capitals).
- 9 GLs: JMK, JML, SEE, SLKR, GL Leia, Lord Vader, GL Rey, Jabba, GL Ahsoka.

## Gaps (biggest upgrades)
- **Squad GL: GL Hondo** — leads #1 3v3 defensive wall (38% hold) + several top-4 3v3 walls. Not owned.
- **Fleet: Profundity** (CAPITALPROFUNDITY) — #1 defensive fleet (77% attacker win). Not owned. (Owns Raddus, a different ship.)
- **Non-GL wall: Third Sister** — highest-Hold% team you can't field.

## Board (Kyber, 2026-07)
- 5v5: 11 def squads + 3 fleets. 3v3: 15 def squads + 3 fleets.

## swgoh.gg season alternation
- Even season = 5v5, odd = 3v3. As of **2026-07-31: S80=5v5 (current, unchanged), S81=latest 3v3 (rolled from S79)**.
- **Re-scrape BOTH each session** — a 3v3 roll (S79→S81) moved Baylan/Marrok/Shin Hati from a 22% def wall to a 9% def wall (now a 82%-win OFFENSE team). Stale board would've left a 9%-hold wall = near-free clear.

## GL allocation (defense-first, but reserve attack GLs)
- Offense always: JMK, JML, SEE, SLKR. 5v5 also GL Leia (96% #1 attacker).
- Defense: Lord Vader, GL Rey, GL Ahsoka, Jabba (+ GL Leia in 3v3).

## Fleets (grounded caps from /gac/ship-counters; reinforcements = faction meta from owned ships)
- Defense: Leviathan (82%), Negotiator (90%), Home One (91%). Offense: Executor, Malevolence, Raddus.
- **Re-verified 2026-07-31** (/gac/ship-counters, current season): owned-capital hold ranking = Leviathan 82 < Executor 87 < Negotiator 90 = Chimaera 90 < Home One 91 < Endurance 92 < Executrix 93 < Raddus 94 < Malevolence 95 < Finalizer 98. Profundity 78 = best (unowned gap). Allocation unchanged: Executor reserved for offense (premier attacker); Chimaera's Imperial ships collide with Executor so Home One stays the 3rd defense (no-ship-reuse).
- All 6 fleets share no ship (single-use). Malevolence fleet = 6 ships (all owned Separatist).

## HotUtils
- API base api.hotutils.com/Production ; squads/list, squads/upsert (create via {definition}, delete via {id,void:true}).
- Categories are free strings → used 6: GAC {5v5,3v3} - {Defense,Offense} + GAC Fleet - {Defense,Offense}.
- Session ids are ephemeral — recapture each session (browser_recipes.md §4).

## Mod optimizer (Grandivory via HotUtils) — DONE 2026-07-19
- Path: HotUtils → GI's Optimizer (/mods/optimizer) → embeds mods-optimizer.swgoh.grandivory.com (or open standalone tab). Priority = selected-character order; use-case = GAC (via Auto-generate List).
- Two views/tabs on the app: "Optimize my mods" is a NAV TAB (no-op for compute); the real run button is "Optimize my mods!" (with `!`) at the bottom of the selection/edit view. Don't confuse them.
- **STALE-DATA GOTCHA:** "Move mods in-game" fails mid-batch with **"Error! Row not found!"** when HotUtils' cached game state is old (a mod isn't where HU thinks). FIX = on the optimizer, "Fetch my data!" → "Fetch with HotUtils" → "Fetch my data" (pulls fresh current inventory into HU AND the optimizer), THEN re-run "Optimize my mods!" (fresh recompute), THEN "Move mods in-game".
- **Partial-apply reality:** a "Row not found" failure applies moves up to the failing row. First attempt implied ~6.39M credits / 1,259 moves; after fresh retry the remaining diff was only **1,710,000 credits** → confirms ~¾ applied on the first (errored) pass. Re-fetch always reflects the true post-partial state, so re-optimizing from there is correct.
- Apply "can take several minutes" and **logs the account out of GoH**; success dialog = "Mods successfully moved". Completed cleanly 2026-07-19 on fresh 2,234-mod inventory.
- **INVENTORY-SPACE GOTCHA (2026-07-31):** "Move mods in-game" **pre-flight-fails** with **"Minimum of 10 available inventory spaces required"** when unequipped-mod capacity is near-full (Astra was **495/500** = 5 free; equipped mods don't count). It's a PRE-CHECK → **nothing moves, no credits spent**. FIX: free ≥10 mod slots, then re-run Fetch→Optimize→Move. This is the binding blocker for placement re-opt, not data-staleness.
- **⚠️ `mods/sell` API DOES NOT WORK (verified 2026-07-31):** POST `mods/sell {modIds,getAllData}` returns rc1 "MODS SOLD" and even shows a decremented count with `getAllData:true`, **but the mods do NOT leave the game** — `account/refresh` (fresh CG sync) restores them every time. Unlike tier/level/reroll/move, sell is not wired to CG. **Freeing mod-inventory space MUST be done in-game** (sell junk mods, or expand mod capacity with crystals). No HotUtils API path frees real slots.
- **Auto-generate List** (GAC/TW/ROTE use case) rebuilds the priority list fast when the GI session resets (SessionID rotates → selected list empties → "Optimize my mods!" disabled). GLs+meta walls sort to top, so board units are prioritized. **After a HotUtils fetch the GI selected-list resets → re-run Auto-generate before Optimize.** 2026-07-31 applied run: +5.04% set value, plusSpeed +1,160.

## Mod upgrade/slice/calibrate via HotUtils API — DONE 2026-07-20
**Browser-free path (2026-07-25):** the API works **server-side via curl/urllib** — no browser cookie needed, just header `apiuserid` + body `sessionId`. This sidesteps the flaky in-session Chrome entirely for ALL reads + slice/promote/level/calibrate. New reusable scripts: `scripts/pull_mods.py` (calls `account/refresh` + `account/data/all` → writes `data/mods_full_<date>.json`) and `scripts/execute_upgrades.py` (defense-first slice/promote via `mods/tier`, self-stops on material-out). Pipeline: `HU_SID=<live> python3 scripts/pull_mods.py && python3 scripts/slice_plan.py && HU_SID=<live> python3 scripts/execute_upgrades.py [--dry]`.
- **`account/refresh` {sessionId} = the API "Fetch my data"** — forces a fresh CG→HotUtils sync (fixes stale `gameDataAgeUtc` / "Row not found"). Returns `player.gameDataAgeUtc` + `profileAgeMinutes` (≈1 right after). ALWAYS refresh before planning: HU cache can be days stale even though API slices are reflected.
- **`"Not enough player currency!"` (rc 2) = salvage-out** (same meaning as `GOHServiceCall Error [40]`).

Endpoints (POST api.hotutils.com/Production/, body has {sessionId,...}; header apiuserid stable 898a36a3-948a-4a8a-9798-7a1552b042a8; sessionId rotates — recapture from a live XHR each session):
- **Slice / promote a tier:** `mods/tier {modIds:[id,...], getAllData:true}` — advances each mod ONE tier (5E→…→5A→6E→…→6A). rc 1 = "MODS TIERED". ⚠️ **`simulation:true` is NOT a dry run — it really slices.** Never trust it; every call is real.
- **Level to 15 ("upgrade"):** `mods/level {modIds:[id,...], requestType:3}` (3=ToMax, 4=SingleLevel). Credits only. **Slicing REQUIRES level 15** — level sub-15 mods first or `mods/tier` errors.
- **Calibrate (6-dot):** `mods/reroll {modId, stat:5}` (stat 5 = Speed) → returns `.mod` preview → `mods/acceptreroll {keepMod:true|false}`. Reverting (false) does NOT refund; EACH reroll attempt spends the calibration material.
  - **Material = Micro Attenuators = `summary.currency` id 41** (NOT in `material.material` — that's why my slicing-only tracker showed "spent:{}" and I wrongly guessed a daily cap). Farmed in-game from **Mod Battles Map 9** only; cannot be acquired via HotUtils API.
  - Rule (`okToCalibrate` in bundle): mod must be 6-dot; **max calibrations = tier+1** (6A=6); cost escalates by attempt — 1st needs ≥15 attenuators, 2nd ≥25, 3rd ≥35, …
  - When attenuators can't cover the next attempt, `mods/reroll` returns `responseCode 2 / "GOHServiceCall Error [40]"` on every mod (persists past pauses — it's material-out, not a timer).
  - Best practice: only calibrate maxed 6A mods, 1–3× each; target FLAT stats → speed (re-rolling speed→speed is only ~25% to hit). `mods/level` and reads are NOT gated by attenuators.
  - This session: had 1000 attenuators → spent ~995 (Rey 23→26 kept; rest reverted/probed) → 5 left = exhausted. Refill via Mod Battles Map 9, then resume the sweep over the 50 never-calibrated 6A mods.
- Data model: `account/data/all` → d.data.mods.mods[] {id, unit.baseId(equipped) , rarity(dots 5/6), tier(1=E..5=A/gold), level, setId(4=Speed set), slot, secondaryStat[].stat.unitStatId(5=Speed, ÷10000)}. Materials at d.data.material.material[] by id.
Material recipe (per tier-step) + binding constraints, CORRECTED from live before/after diffs (2026-07-25):
- **T05_06 is the MASTER binding material** — consumed by BOTH promotes AND 6-dot slice steps. Farm it first.
- 5A→6E promote: **≈ T05_06×76 (BINDS)** + T05_05×54 + PROMO_T5_T6×27 + credits. (Earlier "×50" estimate was low.)
- 6-dot slice-up: per-tier T06_0x salvage **+ T05_06** each step. The 6D→6C step is T06_02-heavy (~80); 6B→6A uses T06_04 (~15).
- 5-dot slice to 5A: **T05_03 (5C→5B) + T05_04 (5B→5A) BIND**; T05_01/02 for the low steps. (Does NOT use T05_06 — but new 5A mods strand unless T05_06 is available to promote them.)
Session result: 72→**81 6A** (+9: Jabba, Rey, Lord Vader, 3×Darth Revan, 2×JKR, Ahsoka), +5 promotes to 6E (Starkiller, Bastila, Ezra, 2×JKR), Rey calibrated 23→26 spd, +15 mods to 5A. Stopped at true material exhaustion (T06_02=3, T05_06=15, T05_03=6, T05_04=27); leftover T05_01/02/05 + PROMO are stranded (need the depleted tiers to complete a chain). ~7M credits spent. Priority = defense-squad chars → offense → rest, by speed secondary (scripts/slice_plan.py → output/slice_queue.json).

## 2026-07-25 audit — full mgmt pass (mods + squads + fleets), browser-free API + Playwright
- **Session capture via Discord silent SSO works** (chrome-devtools → hotutils.com → "Login with Discord" `prompt=none` auto-returns a code → accountselect auto-picks Astra). Grab SID from a live `squads/list` XHR (get_network_request). No credentials handled. Don't navigate away before /callback settles.
- **Mods still FULLY exhausted — no farming since the 03:00 run.** Fresh `account/refresh` (gameDataAgeUtc 2026-07-25T00:09): T05_06=**3**, T06_02=84, PROMO=528, Micro Attenuators=**15**, 6A=86, credits 139.2M. Live `mods/tier` on Baylan 6C→6A → `rc=2 "Not enough player currency!"` (3× T05_06 < one 6-dot step). **T05_06 is THE gate for the whole chain.** 0 sub-15 mods on GAC chars (all 220 sub-15 are 5-dot filler → leveling = wasted credits).
- **Board verified CURRENT — no rebuild.** swgoh.gg still S80(5v5)/S79(3v3), not rolled. Recompute on fresh roster (2026-07-25: +103K GP, +Cobb Vanth filler, 19 relic bumps to units already fielded) + fresh S80/S79 meta ⇒ 5v5 & 3v3 DEFENSE **identical** to the live 62-squad board; offense delta = only junk partial-team reference lines. No new GL/squad-unit; gaps unchanged (Hondo, Third Sister, Profundity).
- **Decisions (user):** SAVE the 15 attenuators for a farmed sweep (1 attempt = coin-flip); DEFER mod-placement re-opt to the next slice session (only ~12 mods changed since the Jul 19 optimize).
- **Next real gains are farming-gated:** farm T05_06 (master binding) + Micro Attenuators (Mod Battles Map 9) in-game → `HU_SID=<live> python3 scripts/pull_mods.py && python3 scripts/slice_plan.py && HU_SID=<live> python3 scripts/execute_upgrades.py` (Baylan 6C→6A = top queued) → calibrate the 6A defense pool → re-run Grandivory placement. ROSTER_FILE in compute_teams.py + generate_hotutils.py now point at 20260725.

## Mod score = HotUtils `summary.modScore` (grounded, inventory-quality) — learned 2026-07-27
- The account "mod score" lives in the **`auth/player/login` response `summary`** block (NOT `account/data/all`):
  `modScore` + `gearScore` = `totalScore` (e.g. 2.37 + 7.78 = 10.16). Plus drivers: `mod6Dot`,
  `speed25/20/15/10` (count of mods with ≥ that speed secondary), `plusSpeed` (Σ equipped mod speed).
  `player.currency` id 41 = Micro Attenuators, id 1 = credits. Reader: **`scripts/mod_score.py`** (run before+after; `--refresh` first).
- **modScore is INVENTORY-quality, NOT placement.** Moving 813 mods (Grandivory re-opt) left modScore
  UNCHANGED (2.37→2.37). Placement value appears in **Grandivory "set value sum" (+%)**, `plusSpeed`, and
  char stats — never in modScore. modScore only rises by slicing/promoting/**calibrating** the inventory.
  ⇒ Report a "mod score delta" as BOTH: modScore (quality) + Grandivory set-value % (placement).

## Precise material recipe (live diff 2026-07-27, supersedes estimates)
- **ONE 6-dot slice step = 10× T05_06 + 20× T06_02 + ~126K credits.** 15 T05_06 buys exactly one step.
  T05_06 is THE master gate for the whole slice+promote chain (T06_02/PROMO/T05_03/04 strand behind it).

## Calibration (`scripts/calibrate.py`) — mechanic confirmed 2026-07-27
- `mods/reroll {modId, stat:5}` **redistributes the roll-weights across all 4 secondaries** biased toward
  the target stat (not a clean speed bump) → `acceptreroll {keepMod}`. Script keeps only if speed improved
  (stats never regress); either way the attempt spends attenuators (~15/1st, escalates). Ranks 6A GAC mods
  by headroom (rolls×6 − spd), defense-first, rr asc. Self-stops on rc2. ~25% hit; budget for a real sweep
  (had 72 → 4 attempts, all missed 0/4 — RNG). Farm attenuators (Mod Battles Map 9) before a big sweep.

## 2026-07-27 session result (TWO batches)
- **Batch 1:** slice Baylan 6C→6B; calibrate 0/4; **Grandivory placement +4.56% set value, 813 mods, 4.05M cr, clean.**
- **Between batches: Plessas farmed the RIGHT material in-game** — T05_06 5→230 (+225), attenuators 12→44, T06_02→94.
- **Batch 2 (best order):** JKR + Baylan sliced→6A; General Kenobi + Great Mothers promoted→6E → **6A 86→88, 6-dot 134→136**.
  Calibrate 0/2 (Ahsoka/JKR spd24→19). **Cumulative calibration 0/6 — stop calibrating decent-speed mods.**
- **Full-day delta:** modScore **2.37→2.37 (coarse/sticky — didn't move despite +2 6A/+2 6-dot + 813 re-placements)**,
  plusSpeed 15048→15097 (+49), 6A +2, 6-dot +2, credits −5.3M, attenuators 72→14 (spent 90, farmed 32).
- **Calibration ROI verdict:** poor on already-decent-speed (~24) mods — redistribution keeps landing lower.
  Slicing bumps speed for free; reserve attenuators for low-speed/high-roll 6A mods only, or skip.
- **`execute_upgrades.py` costs corrected** (grounded): slice step = 20 T06_02 + **10 T05_06**; promote = **76 T05_06** + 27 PROMO;
  build_plan shares the T05_06 budget across slices+promotes. **1 T06_02 gates slicing (~20/step); T05_06 gates promotes (~76).**
- Farming sources (grounded, web): T05_06/salvage → Mod Battles Sector 9 + Guild Store + Episode Shipments (bulk).
  Micro Attenuators → **Smuggler's Run 2 (needs Jabba — owned; BEST)**, Mod Battles 9, GET3, Episode Shipments.

## 2026-07-31 session — season roll (S79→S81 3v3) + full GAC rebuild + mods
- **Season rolled:** re-scraped fresh S80 5v5 + **S81 3v3** (4 views). Roster refreshed → 20260731 (GP 14.31M, +Mara Jade Skywalker G2 filler, no new fieldable meta unit; gaps unchanged: GL Hondo, Third Sister, Profundity).
- **Board rebuilt on HotUtils** (browser-free API): deleted 62 old, created 63 (5v5 def 11 IDENTICAL; **3v3 def: Baylan wall→Boss Nass 13%**, Baylan→3v3 offense 82%; 3v3 off 15→16). Verified 11/15/15/16/3/3, no dups.
  - ⚠️ **Batch squad rebuild THROTTLES/time-outs ~40+ rapid calls** (delete+create = 125). First run died mid-create (network timeout) after deleting 62 + creating 42. Recovered by **resume-create-by-name** (idempotent, no dups). Do it in chunks with per-call retries + ~0.4s pacing, or split delete/create.
- **Mods (materials farmed since 7/27):** T05_06 55→422, attenuators 14→186, T06_02→71. Executed: **Jabba→6A (89 6A), +4 promotes→6E (140 6-dot)**; T06_02 (now 31) is the binding gate. Calibration **0/4 again → 0/10 cumulative** (reverted, spd intact; attenuators 186→86). **Stop calibrating decent-speed (19+) mods.** Credits 146.8M.
- **Placement re-opt APPLIED ✓ +5.04%** — first attempt blocked at 495/500 inventory; Plessas sold 36 junk mods in-game (→459/500, 41 free) → re-fetch (2345 mods) → re-optimize → Move SUCCESS. **plusSpeed 15,276→16,436 (+1,160), modScore 2.35→2.84**, speed15 262→321, 5.5M cr. Credits end 143.45M.

## 2026-08-01 — Automation landscape research + A0 comlink data backbone (Track A)
- **Research (5 parallel agents):** full SWGOH automation map. Key finding: **HotUtils is the ONLY tool that executes in-game actions**; everything else (swgoh-comlink, swgoh.gg API, Crinolo stats) is READ-ONLY. In-game battle-playing (GAC/TW/TB/arena/farming) CANNOT be safely automated (ban risk); only native sim/auto-battle. Specs: `docs/superpowers/specs/2026-08-01-*`.
- **Decision (user):** build the full suite; ALSO automate PvE farming (accepts ban risk — "would quit otherwise"). **Boundary: PvE farming YES, PvP-combat automation NO** (Arena/GAC/TW = real opponents). Tracks: A (safe data) + B (PvE farming macro, Android emulator on Mac).
- **A0 DONE + live-verified:** `scripts/swgoh_data.py` (map_roster / get_roster / load_roster). Tests: `.venv/bin/pytest tests/` = **8/8**. Replaces the swgoh.gg roster browser-scrape with comlink. `compute_teams.py` now sources roster via `load_roster(ALLYCODE=145357294, fallback_file=ROSTER_FILE)` — live comlink OR file fallback (both produce an **identical board**: 5v5 11/11, 3v3 15/15).
- **comlink hosting:** swgoh-comlink **v4.4.1 Linux binary** runs as **systemd service `comlink` on the VPS** (`vps` = 167.233.42.38, `~/comlink/`, APP_NAME=astra-swutils, port 3000, enabled + Restart=on-failure). ufw: default-deny + explicit deny 3000 → **tunnel/localhost-only**. (Mac Docker daemon won't start headless; the macOS binary is a broken pkg/V8 build; the VPS Linux binary works fine.)
- **Use live comlink from the Mac:** `ssh -fN -L 3999:127.0.0.1:3000 vps` then run under the **venv** with `COMLINK_URL=http://localhost:3999` (comlink-python lives only in `.venv`). No tunnel / system python → auto file-fallback. comlink is READ-ONLY (no unequipped mods → **HotUtils still required for mod inventory**).
- **Relic encoding (learned):** file `rt` == comlink `relic.currentTier` verbatim (NO offset; locked/pre-G13 = 1; ships = None).
- **Next (Track A):** A1 daily brief · A3 farm/gear/datacron advisor · A2 GAC opponent scouting · A4 event/GL-readiness (all consume swgoh_data). Then Track B (PvE farming macro).
