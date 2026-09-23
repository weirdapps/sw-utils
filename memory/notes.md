# Notes — durable facts (update when they change)

## Player
- Astra · ally 145357294 · Kyber 3 (→ Kyber 2) · ~14M GP · 326 chars (314 G13+), 69 ships (10 capitals).
- 9 GLs: JMK, JML, SEE, SLKR, GL Leia, Lord Vader, GL Rey, Jabba, GL Ahsoka.

## Gaps (biggest upgrades)
- **Fleet: Profundity** (CAPITALPROFUNDITY) — #1 defensive fleet (77% attacker win). Not owned. (Owns Raddus, a different ship.)
- **Non-GL wall: Third Sister** — highest-Hold% team you can't field.
- ~~Squad GL: GL Hondo~~ — **NO LONGER A GAP.** The old "#1 3v3 wall, 38% hold" was an all-league figure;
  on S81 it reads **3.5% Kyber-D1 / 9.8% Kyber-default** (see 2026-08-05 session notes). Do not spend
  farming on Hondo blockers (Captain Silvo, Vane) on the strength of this line.

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
  - **Material = Micro Attenuators = `summary.currency` id 41** (NOT in `material.material` — that's why my slicing-only tracker showed "spent:{}" and I wrongly guessed a daily cap). Cannot be acquired via HotUtils API. Farmed in-game from **Mod Battles chapter 2** — this was "Map 9" until the 2026-04-27 update cut Mod Battles from 9 tiers to 2 and deleted Mod Challenges; chapter 2 IS the old tier 9, and `farmbot/config.json` already targets `chapter_tab_mod_2`. Two more faucets found 2026-08-17: **GET3 5-for-125** and **Episode currency 16-for-4,000**.
  - Rule (`okToCalibrate` in bundle): mod must be 6-dot; **max calibrations = tier+1** (6A=6); cost escalates by attempt — 1st needs ≥15 attenuators, 2nd ≥25, 3rd ≥35, …
  - When attenuators can't cover the next attempt, `mods/reroll` returns `responseCode 2 / "GOHServiceCall Error [40]"` on every mod (persists past pauses — it's material-out, not a timer).
  - Best practice: only calibrate maxed 6A mods, 1–3× each; target FLAT stats → speed (re-rolling speed→speed is only ~25% to hit). `mods/level` and reads are NOT gated by attenuators.
  - This session: had 1000 attenuators → spent ~995 (Rey 23→26 kept; rest reverted/probed) → 5 left = exhausted. Refill via Mod Battles chapter 2 (see above), then resume the sweep over the 50 never-calibrated 6A mods.
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
  ⚠️ **`rt` is NOT the relic level the game displays — displayed relic = `rt − 2`.** Device-verified 2026-08-05:
  JML's unit tile reads R10 where the file says `rt:12`; the Geonosians (`rt:8/8/8/7/7`) show R6/R6/R6/R5/R5
  and were **rejected** by a "5x Geonosians (Relic 7+)" RotE mission. So `rt>=8` is the R6+ gate and `rt>=9`
  the R7+ gate. Any note quoting a relic level straight off `rt` is two tiers too high.
- **A3 advisor DONE:** `scripts/advisor.py` `farm_priority()` ranks farm targets by board-unlock impact (sole-blocker of a meta team first, by rate; `_sort_key` = tunable heuristic). 3 tests. Real run: THIRDSISTER = sole-blocker of an 86% 5v5 offense; Cobb Vanth 66%; 4-LOM 31% wall.
- **A1 daily brief DONE:** `scripts/daily_brief.py` → terminal + `output/brief_<date>.html` (board summary + farm priority). 2 tests. **Full suite 13/13** (`.venv/bin/pytest tests/`).
- **A4 events DONE:** `scripts/events.py` (parse_ics + filter_upcoming + notable flags) reads swgohevents.com `/ical`; integrated into daily_brief "Upcoming events" section. stdlib-only.
- **name-map DONE:** `swgoh_data.refresh_name_map()` rebuilds `data/name_type_map.json` for ALL **829** units via the **`UNIT_<baseId>_NAME`** localization convention. (comlink game-data `items`/segment API is REJECTED by 4.4.1 — use `get_localization(id, unzip=True)["Loc_ENG_US.txt"]` which is `KEY|text` lines. Localization has no combatType → ct preserved from prior map for owned.) compute_teams uses the full map → gap units show real names.
- **daily.sh DONE:** `./scripts/daily.sh` = one-command driver (tunnel → live board → brief → open HTML).
- **ALL MERGED TO MASTER** (21 tests, `.venv/bin/pytest tests/`). Not pushed to GitHub yet.
- **A2 scouting DONE:** `scripts/scout.py` — `COMLINK_URL=http://localhost:3999 .venv/bin/python scripts/scout.py <opponent_ally> [5v5|3v3]` → meta defenses the opponent can field (Hold%-desc, real names). Run per GAC round. `fieldable_defenses` + `owned_g13_set` tested.
- **A3 v2 DONE:** `advisor.relic_priority(gac, roster, target=9)` → fielded board units below relic 9, ranked by strongest team held; surfaced in the daily brief. (Astra's board relics span 7-12; 14 laggards at relic 7-8, e.g. Mace Windu r8 on a 95% team.)
- **Refactor:** meta parsing extracted to `scripts/swgoh_meta.py` (shared by compute_teams + scout; compute_teams board verified byte-identical; removed now-unused `re`).
- **On PR #3** (`track-a-automation` → master), **30 tests** (`.venv/bin/pytest tests/`). Master pushed via PR (hook blocks direct master push).
- **Remaining:** **kill META scrape** (swgoh.gg API key → compute_teams fully browser-free) · **Track B PvE farming macro** (needs Android emulator on Mac — the grind-killer). Cleanup: `~/Downloads/comlink-macos*` broken binary is junk.

## 2026-08-02 — Track B `farmbot/` — energy-dump/sim macro BUILT + live-validated (READ THIS to continue)
The grind-killer. A supervised PvE macro that drives BlueStacks Air via ADB + OpenCV to **Multi-Sim** 3★ campaign nodes. Merged to master across **PRs #4–#10** (69 tests). **The engine is complete and validated live across every path; what remains is per-node icon capture + config wiring.**

### Run it (from repo root, in `.venv`)
- Prereq: BlueStacks Air running, SWGOH logged in as **Astra**, at a **clean hub** (dismiss popups first). `adb` = `/opt/homebrew/bin/adb`. Device serial **`emulator-5554`** (also `127.0.0.1:5555`; the ADB port is **dynamic** — after a BlueStacks restart re-check Settings→Advanced→ADB and `adb connect 127.0.0.1:<port>`). Screen 1920×1080.
- `.venv/bin/python -m farmbot.run --dry-run` (preview) · `--dump` (farm) · `--capture` (template capture). Kill: Ctrl-C or `touch farmbot/STOP`. No comlink tunnel needed (local emulator).
- Files: `farmbot/{adb,vision,tasks,run,capture}.py`, `farmbot/config.json` (gitignored — the farm list), `farmbot/templates/*.png` (committed, 19), `farmbot/halts/` (safe-stop screenshots), `farmbot/README.md` (runbook), **`farmbot/TARGETS.md` (the complete researched target list)**.

### Engine flow (validated: Cantina Normal sim + Fleet Hard sim + full loop, live)
Per node, starts+ends at hub: `HOME(verify) → tap Campaigns → CAMPAIGNS_MENU(verify) → SELECT_CAMPAIGN(tap title, offset +673 → PLAY; scrollable) → [SELECT_DIFFICULTY tap hard_tab if difficulty:"hard"] → [SELECT_CHAPTER tap chapter_tab_<n>] → SELECT_NODE(tap node icon; scrollable; ensure=multi_sim, re-taps) → OPEN_MULTISIM → CONFIRM_SIM(tap green SIM) → REWARDS(tap CONTINUE) → RETURN_HOME(tap home button)`. Multi-Sim auto-fills to max energy.
- Config node: `{campaign, ["difficulty":"hard"], ["chapter":N], "node":"1-D", "sim":"max"}`. Campaigns menu has **5 cards: LS, DS, Cantina, Mod Battles, Fleet** (Fleet/Mod start off-screen → SELECT_CAMPAIGN scrolls). **Mod Battles is sim-able via the same flow (Mod Energy).**

### Gotchas (hard-won — don't re-learn)
- Campaign card: tapping the **title flips the card**; must tap PLAY via `tap_offset(0,673)` below the matched title (PLAY buttons identical → not matchable directly).
- Node: tapping an **already-selected node closes its panel** → SELECT_NODE `ensure=multi_sim` re-taps until MULTI SIM shows.
- **Energy-out = a "Purchase Energy 💎200" prompt.** `energy_out` template = its **CANCEL** button; macro taps CANCEL, **NEVER PURCHASE** (verified: crystals unchanged). `sim_confirm` proven not to false-match PURCHASE.
- **Hard nodes = 5 attempts/day**; depleted → "1h12m / 💎200" refresh (no MULTI SIM) → macro **safe-halts** at OPEN_MULTISIM (never pays); graceful-skip NOT yet built.
- **Hub is popup-prone** (login/era calendars, GoH newsletter auto-pop) → each safe-halts. `popup_close` (red-circle-X) captured but **auto-dismiss NOT wired** (newsletter uses a different white X).
- Node IDs repeat across campaigns → templates are **campaign-scoped: `node_<campaign>_<id>`**.
- macOS: no `timeout` cmd (`adb.py` has its own subprocess timeout). `ls -t` is `eza` (different flags) — use `/bin/ls`.

### Templates captured (19): home, campaigns_entry, campaigns_menu, campaign_{cantina,light,dark,fleet,mod}, hard_tab, chapter_tab_1, multi_sim, sim_confirm, rewards, home_button, energy_out(=CANCEL), popup_close, node_cantina_1-A, node_light_1-D(Kix), node_fleet_1-E.

### NEXT STEPS (do these next)
1. **Capture the remaining target node icons** (per `TARGETS.md`, live-verified): Cantina **3-B (Vane)**, **6-A (Silvo)**; Fleet Hard **1-A (Ithano)**, **2-A (Brutus)**, **2-D (MG-100)**, **2-E (Raven's Claw)**, **3-D (Quiggold)**; DS Hard **8-B (Hyena Bomber)**; then materials: **Mod Battles Tier 2** (mod salvage/attenuators) + **Cantina Stage 8/9** (zeta/omicron). **Capture recipe:** enter campaign → [tap HARD] → tap chapter tab → **scroll** to the node (early nodes are off-screen; e.g. Cantina ch3 opens on 3-G, 3-B is left) → confirm the **panel header ID** + the **reward icon = the target shard** (node art ≠ shard) → PIL-crop the node hexagon (~190×200) to `farmbot/templates/node_<campaign>_<id>.png`.
2. **Wire `farmbot/config.json`** with the captured targets, grouped by energy (currently only the 2 validated demo nodes: fleet hard 1-E + cantina 1-A).
3. **Optional robustness:** (a) depleted-Hard-node graceful-skip (detect the 1h12m/💎200 refresh → skip like energy-out); (b) popup auto-dismiss (loop-tap `popup_close` before HOME; capture the newsletter's white-X too).
4. **NOT sim-able (skip):** Third Sister, Pirate King Hondo, SM-33, Mace Windu, Profundity, Mara Jade Skywalker — event/shop/Conquest. GW auto-battle = a separate future module (plays battles, not sim).
- Boundary reminder: **PvE only, never PvP; never spend crystals.** Ownership-corrected targets = owned-but-under-7★ units/ships (shards help to 7★), NOT the unowned GAC-wall units.

## 2026-08-02 (session 2) — farmbot: 5 robustness features + live multi-pool validation
Hardened the engine (TDD, 69→**80 tests**), captured Mod/DS/difficulty templates (19→**25**), and validated the full loop across **4 energy pools live**. ALL PvE; **crystals UNCHANGED (3,925) throughout**.

### Engine features (tasks.py, device-free + unit-tested)
- **Generalized skip** (`Step.skip_marker/skip_tap/skip_counter`): energy-out (tap CANCEL) AND depleted-Hard (refresh timer, **never tapped**) skip-to-next-node instead of halting. New `Summary.hard_depleted_nodes`.
- **Popup auto-dismiss** (`_dismiss_popups`, `DEFAULT_POPUP_CLOSERS`): missing expected screen → tap known close-X's (`popup_close` red-circle-X, `newsletter_close` white-X) → re-check before halting. Both captured live (login-rewards + GoH newsletter now auto-dismiss).
- **Optional difficulty** (`Step.optional`, `DIFFICULTY_CAMPAIGNS={light,dark,fleet}`): game REMEMBERS Normal/Hard. SELECT_DIFFICULTY taps the wanted difficulty's *unselected* button if visible, else skips (already correct). Handles Normal too (`normal_tab`). Tapping an already-selected difficulty = harmless no-op.
- **Campaign-scoped tier tabs** (`SCOPED_CHAPTER_CAMPAIGNS={mod}`): Mod Battles tier tabs differ visually → `chapter_tab_mod_<n>`; others share generic `chapter_tab_<n>`. Avoids Mod-tier-2 vs Fleet-ch-2 collision.
- **Chapter-tab scroll** (SELECT_CHAPTER scrollable) for high tabs.

### Live validation (BlueStacks, Astra) — two full `--dump` runs completed clean (reason=complete)
- **Mod Battles Tier 2 (Cargo Ship 2-F)**: 8-battle Multi-Sim → **Mod 144→0**; rewards = T05/T06 slicing salvage + mod droids + credits (the #1 bottleneck, now auto-farmed).
- **Fleet Hard 1-E**: engine multi-sim → **Fleet 74→11** (4 sims).
- **LS Hard 1-D (Kix)**: engine multi-sim → **Normal 144→84** (5 sims).
- Validated: multi-pool sequential nav (cantina→fleet→mod→light), energy-out skips (tap CANCEL never PURCHASE), optional difficulty, chapters, popup dismissal, return-home. No halts.
- **Energy pools by icon colour**: blue=Fleet, green=Mod, red=Cantina, gold=Normal (LS+DS **shared**). Cap 144. Multi-Sim uses Sim Tickets (34.3K) + energy, auto-fills to max.

### Templates captured (+6): node_mod_2-F, chapter_tab_mod_2, chapter_tab_8, node_dark_8-B, normal_tab, newsletter_close; hard_tab re-captured clean (unselected). config.json = 4 VALIDATED daily nodes.

### Research corrections (5-agent workflow) — see farmbot/TARGETS.md
- **Vane NO LONGER sim-able** (→ Chromium packs, Oct 2025); drop old Cantina 3-B.
- **NEW Cantina 2.0 Stage-9 Omicron**: Wampa 9-A, Grievous 9-E, Hermit Yoda 9-G (shards + 0.75% Omicron). Zeta = 8-F.
- **DS Hard 8-B = Taris** = Hyena Bomber ship + Mk3 Stun Cuffs + Comlink in ONE sim (device-confirmed).
- Fleet Hard (wiki-stale, confirm icons): Ithano 1-A, Brutus 2-A, Quiggold 3-D, Raven's Claw 2-E(HARD), MG-100 2-D. Fleet NORMAL 2-E = Mk12 Fusion Furnace. Silvo = Cantina 6-A. Mod T2: T05_06@2-E/2-F, T06_02@2-D.

### Gotchas / next
- **Capture node templates UNSELECTED.** Engine arrives with the last-played node auto-selected; a non-auto-selected target appears unselected, so a selected-state template misses (node_mod_2-F worked only because 2-F is last-played; node_dark_8-B failed until re-captured unselected).
- **hard_depleted NOT captured** → depleted Hard node safe-HALTs (saves halts/<ts>_OPEN_MULTISIM.png). Recipe: run with a depleted Hard node, crop the panel's refresh-timer region (do NOT include only the 💎-refresh button) → templates/hard_depleted.png; skip then works (already unit-tested).
- **DS ch8 nav finicky** (high tab + off-screen node + selection state; engine landed on ch6). Chapter-1 nodes reliable. Tune chapter_tab_8 + ch8 scroll before wiring DS 8-B / the Stage-9 Cantina Omicron nodes.
- **Runs must start at the hub**: a mid-flow halt leaves the game deep in a menu → next run HALTs at HOME. Consider start-of-run home-recovery (tap home_button when HOME missing).

## 2026-08-02 (session 3) — hard_depleted captured + DS 8-B live + daily-modes boundary
- **DS Hard 8-B (Taris) validated live**: dumped Normal 88→8 (4 sims) → Hyena Bomber ship shard + Mk I/III/IV gear + mod droids + 6,240cr. Re-captured `node_dark_8-B` **UNSELECTED at the engine's post-scroll position** — the angled 3D campaign map is perspective-sensitive, so a node captured at one x can miss at another (why the first 8-B capture failed live). config.json now has all 5 daily farms.
- **`hard_depleted` CAPTURED** — from depleted LS Hard 1-D (Kix): the green **"23h 16m 💎25" refresh bar** that replaces MULTI SIM when a Hard node's 5 attempts are used. Cropped the **stable 💎25 chip** (timer digits change), self-match 1.0, and it does NOT match a MULTI-SIM node (0.71). Depleted-Hard skip now fully functional (template + code + tests). Last robustness gap closed.
- **The energy-pool sim-farms ARE the full "sim-able via tickets" scope — and it's DONE.** The other daily modes are NOT ticket-sim:
  - **Coliseum** (e.g. "Zeffo Tomb Guardians") = PvE **boss-score BATTLE** (5 attempts, a BATTLE button, score→milestone+rank rewards). NOT Multi-Sim. Auto-battle possible but "plays battles," score-dependent.
  - **Events / Assault Battles / Raids** = PvE **battles** (auto-battle, not sim); raids guild-gated; each a distinct UI.
  - **Squad/Fleet Arena, GAC, TW = PvP** (real opponents) → **EXCLUDED** (owner's own PvE-only boundary + highest ban risk). Arena DAILY PAYOUT is collectible without battling.
- ⇒ Farming the named modes needs a **separate PvE auto-battle module** (real-time: team-select → start → auto → win/score detect), materially bigger than the sim-macro. Not built this session; flagged for a go/no-go.

## 2026-08-03 — farmbot expansion: "farm ALL dailies" scoped + sub-project E BUILT
User asked to farm Coliseum/arenas/events/raids + all dailies. Decomposed into 5 subsystems and **built the first (E) end-to-end**; the rest are designed-and-deferred. Spec: `docs/superpowers/specs/2026-08-03-farmbot-daily-collectors-design.md`. Plan: `docs/superpowers/plans/2026-08-03-farmbot-daily-collectors.md`.

### Governing decisions (durable)
- **PvE only; arena/GAC/TW = COLLECT-ONLY** — the bot claims arena daily *payout* but **never auto-plays a PvP match** (user-confirmed reversal-guard on the earlier PvE-only boundary; highest ban risk). Consequence: the daily-activities crate's 1 required squad-arena battle stays **manual** (flagged, not botted).
- **Never spend crystals** (unchanged rail). E's principle: automate everything **free-to-collect or Multi-Sim-able**; nothing needing a real-time battle, PvP, or crystals.

### Decomposition (build order E → B → C → A)
- **E** = passive collectors (login/store/inbox/achievements/arena-payout/free-energy) + **Daily Challenges (sim)**. ✅ BUILT.
- **B** = auto-battle engine (Coliseum boss-score, Assault Battles, Events) — real-time start→poll→branch. NOT built (next).
- **C** = Raids (guild-gated). **A** = daily orchestrator (sequences sim-macro + E + B + C, one report). NOT built.

### E — what shipped (PR #13, branch `farmbot-daily-collectors`, stacked on PR #12)
- **One engine, kind-dispatched.** `_steps_for` routes by entry `kind`; `_steps_energy_node` = old body **extracted verbatim** (energy flow byte-for-byte identical). New kinds: **`collect`** (`HOME→nav→CLAIM→dismiss→HOME`, idempotent: absent claim ⇒ `nothing_to_collect`, no halt; only free-claim templates are tap targets so crystal/buy controls are never pressed; `count` for stacked gifts; `counter` books to collected/energy_claimed) and **`challenge_sim`** (Challenges-screen Multi-Sim; `mark="challenges_simmed"` disjoint from energy `sims_done`; not-3★ skips via `challenge_locked` marker, never battles).
- Config: canonical **`routine`** list w/ optional per-entry `kind` (default energy_node); **`nodes` still an alias** (old config + tests untouched); `routine_of()` helper. CLI **`--daily`**; `format_summary` reports per-kind counts. `config.example.json` documents the mixed-kind schema.
- Two additive `Step` fields wire it: `mark` (bump a Summary counter on tap) + `optional_counter` (bump on optional-skip). **Tests 80 → 95**, all green; TDD, device-free.

### NEXT (to make E actually run live — code is done, capture is not)
1. **Capture templates on-device** (unselected where relevant): collect = inbox_entry, login_claim, store_entry, store_free_claim, gift_claim, achievements_claim, arena_entry, squad/fleet_arena_tab, arena_payout_claim, energy_free_claim; challenges = challenges_entry, challenges_menu, the challenge icons, and `challenge_locked` (for graceful not-3★ skip). Uncaptured ⇒ safe-halt, so fill in incrementally.
2. **Wire local `config.json`** (gitignored) with real collect + challenge_sim entries, mirroring `config.example.json`; validate `--dry-run` then `--daily` (crystals unchanged; no PvP battle).
3. Then **sub-project B** (Coliseum/events/raids auto-battle) — the flagged bigger module.
- **Merge order:** PR #12 (sim-macro) first, then PR #13 (E) auto-reduces to E-only.

## 2026-08-03 (session 2) — full daily bot BUILT (B/C/A) + live-validated core
User directive: "capture all free loot, do all PvE tasks, sim-able preferred, auto-battle otherwise,
research what pros do, do at least that. Don't stop, don't ask." Built the rest of the daily bot on
branch `farmbot-full-daily` (off E's tip). Kept the standing rails (PvE only, never PvP battle, never
spend crystals). **Suite 95 → 104.** Research → `docs/swgoh-endgame-daily-2026.md`.

### Engine (all four kinds now, one dispatched state machine)
- **B — `battle` kind** (PvE auto-battle): HOME → nav → per attempt (START → AUTO(optional) → await
  VICTORY on a long per-step timeout; DEFEAT = recorded skip, never retried) → dismiss → home. Added
  `Step.timeout` override, `Summary.battles_won/battles_lost`, shared templates (battle_start/
  battle_auto/victory/defeat), `attempts` (Coliseum ×5). Covers Coliseum, Galactic War (pre-50-sim),
  Assault Battles, Events.
- **C — Raids** = a `battle` config entry (guild→raids nav, raid_deploy start, raid_results victory).
  No separate engine (YAGNI), same pattern as arena→collect / challenges→sim.
- **A — orchestrator resilience**: `--daily` runs `continue_on_halt=True` → a single entry's halt is
  isolated (`halted_entries++`), the engine recovers to hub (dismiss popups + home button) and
  continues instead of aborting. `--dump` keeps abort-on-halt for single-run debugging.
- `config.example.json` = the full 18-entry daily routine (7 collect, 4 energy, 4 challenge, 3 battle).

### Live validation (BlueStacks, Astra, this session) — `python -m farmbot.run --daily`
- **Ran live**: nodes_attempted=5, **sims_done=3**, hard_depleted=1, halted_entries=1, halted=False,
  reason=complete. **Cantina 53→2, Fleet 27→4, Normal 60→47 dumped live; crystals 5,045 UNCHANGED**
  (rail held). **Sub-project A proven on real hardware** — the one halt was isolated, run completed.
- **Findings:** (1) **Mod 2-F showed depleted** (hard_depleted) so Mod energy stayed 213/144 — Mod
  Battles nodes appear attempt-limited like Hard nodes; need another mod node or accept the daily cap.
  (2) **DS Hard 8-B still halts** — engine landed on DS **ch6** (panel on 6-F Yavin 4), couldn't find
  node_dark_8-B → SELECT_NODE halt (the known ch8-nav issue). Chapter-1 nodes reliable; ch8 needs the
  chapter_tab_8 tap + ch8 scroll tuned. macOS has no `timeout` cmd — run the bot directly (its adb.py
  has internal timeouts).

### Remaining (device-gated, iterative — needs care on the live 14M-GP account)
- **Capture collect/challenge/battle templates** (login_claim, store/inbox/arena-payout/energy-free,
  challenges_entry + icons, coliseum_tile, battle_start/auto/victory/defeat, raid_*). Uncaptured ⇒
  safe-halt (and `--daily` isolates it), so it fills in incrementally and never blunders.
- Wire the real `config.json` (gitignored) to the full routine once templates exist; then `--daily`
  runs the whole PvE day. **2 Daily Quests stay manual by design** (open Data Card + buy 3 shipments =
  currency spend) plus **1 arena battle** (PvP) — bot reports these, never does them.
- Tune DS ch8 nav; add a mod node that isn't attempt-capped (or accept Mod cap).

## 2026-08-03 (session 3) — LIVE template capture + dailies executed on Astra
Drove Astra's live BlueStacks via ADB to capture every sim/auto-battle template AND do the dailies.
**Crystals 5,045 UNCHANGED throughout** (rail held). All templates self-match conf=1.0. Branch
`farmbot-full-daily` (PR #14).

### Done live (real loot)
- **Coliseum auto-battle → 100% score (15,000, up from 2,141)**: coliseum_tile → BATTLE(5) →
  team-select deploy → in-battle AUTO + 4X → VICTORY → CONTINUE. Full auto-battle proven end-to-end.
- **All Daily Challenges MULTI-SIM'd** (Events → Challenges → MULTI SIM → 14 battles): gear salvage
  (Mk VIII/IV/V) + challenge crate. One tap sims ALL challenges.
- Earlier: energy dumped (Cantina 53→2, Fleet 27→4, Normal 60→47); 1 Daily Quest claimed (+300 EP).
- Raid (Order 66) + Galactic War: already done today (raid BATTLE greyed / GW "Restart"), so no-op.

### Templates captured + committed (self-match 1.0)
- auto-battle chrome (REUSABLE across modes): `battle_start` (green BATTLE word), `battle_auto`
  (AUTO toggle), `victory` (results CONTINUE).
- Coliseum: `coliseum_tile`. Challenges: `events_entry`, `challenges_tab`, `challenges_menu`,
  `challenges_multisim`, `challenges_sim_confirm`. Raids: `raids_tab`, `raid_active`.
- **`home` recaptured to the player-badge overlay = PAN-INVARIANT** (matches the hub at any pan;
  rejects battle/menu). Fixes HOME-verify halts after a pan.

### Engine change
- `_steps_challenge_sim` rewired to the real bulk flow (Events→Challenges→MULTI SIM→confirm→rewards;
  greyed MULTI SIM ⇒ optional skip). Suite 104 green. config.json (local) += challenge_sim + Coliseum.

### KEY LIMITATION discovered (the next fix) — 3D pannable hub
The cantina hub is a wide horizontal **panorama** (Arenas/Coliseum → Campaigns → Events/Scavenger/GW
→ Raids/Guilds). Persistent OVERLAYS (player badge, left rail, energy, home button, Quests) are
stable, but the 3D game-mode **consoles** (Events, GW) render at **pan-dependent position, scale, AND
tap-target** — so template match + tap is unreliable off the default pan. Energy + Coliseum work
because `coliseum_tile`/`campaigns_entry` live on the DEFAULT pan. **Needed:** a `recenter_hub`
routine (swipe to the left edge for a known pan) run before nav, so Events/GW consoles are always
approached from a fixed pan; then capture their console tap-targets at that fixed pan. Until then,
the challenge_sim entry safe-halts at the Events nav (isolated by `--daily`); energy + Coliseum
entries replay fine. Live-validated: HOME (pan-invariant) ✓, events_entry match ✓, but the console
TAP didn't open Events (offset/scale) → halt at CHALLENGES_TAB.

## 2026-08-03 (session 4) — "automate the WHOLE daily": pan blocker solved, 4 new subsystems, 68 templates
User directive: automate everything a daily SWGOH player does; leave only PvP and anything that
can't be simmed or auto-battled. **Reversal of a standing rail: in-game TOKEN spending is now
ALLOWED** (crystals still absolutely not). Scheduler explicitly declined — manual runs only.

### The hub-pan blocker (the thing that was actually stuck) — SOLVED, three findings
1. **HUD overlays are pan-invariant; 3D consoles are not.** The fix for Events was not to pan at
   all: the **`EVENT ACTIVE` badge on the right rail opens the same Events menu** (Solo /
   Challenges / **Guild Raids** / Guild Events). Raids come for free from the same screen — the
   far-left pan is no longer needed for them either. `events_entry` re-captured as that badge.
2. **A rail label is NOT a hit target — the tap falls THROUGH to the console behind it.** Tapping
   the "COLLECTION" label opened *Select an Arena*. So templates crop the distinctive label and
   `tap_offset` moves the tap onto the icon (hub_anchor −64, events_entry −71, inbox_entry −68).
   Same for `store_entry`: its label sits ~190px RIGHT of the kiosk that is actually tappable.
3. **A submenu round-trip restores the default pan; the home button alone does not** (no-op while
   the hub is showing). Measured: center-band pixel diff 6.5 after a round-trip vs 41.4 panned.
   That is `recenter: true`. `pan: far_left|far_right` swipes into an end stop for the rest.

### Engine (tests 104 -> 139)
- **`sequence` kind** — navigate then press a fixed button order, every tap optional so
  already-done-today is a skip. Covers **Galactic War** (RESTART -> MULTI SIM -> SIM -> rewards)
  and the free Bronzium. Cheaper than a bespoke kind for each.
- **`shop` kind** — token buys. The guard is **structural, not a runtime check**: the purchase
  dialog's BUY button renders the CURRENCY ICON inline, so a confirm template cropped as
  "BUY + <token coin>" (digits excluded, so it survives a price change) **cannot match a
  crystal-priced dialog**. No crystal-currency confirm template exists in the repo. Optional
  second guard: per-entry `forbid` veto -> taps CANCEL, books `blocked_spends`.
- **`_hub_prelude`** (recenter/pan) + **`_nav_steps`** (offset-aware nav, shared by all kinds).
- **`--doctor` preflight** and **`farmbot/report.py`** (per-run markdown incl. the residual MANUAL
  checklist, sourced from the config's `manual` list so routine and checklist can't drift).
- **`farmbot/devtool.py`** — non-interactive capture/find/coverage. `capture.py` needs stdin, which
  made it unusable from a script; this is the same job on argv. `coverage` **asks the engine for
  its real Steps** instead of re-deriving them (the first version mirrored `_steps_for` by hand and
  drifted within the hour), and splits BLOCKING (would halt) from SOFT (degrades safely).

### Done live on Astra (crystals only ever went UP: 5,045 -> 5,340)
- **Galactic War fully simmed in one tap** — RESTART -> MULTI SIM -> "sim the next 12 nodes" ->
  647.2K credits + mod salvage + ship mats. Confirms a 50+-completion account never fights GW.
  Note: `gw_restart` is only *present* when no war is active (it becomes a "Reset War In" timer
  once one is), so tapping it cannot discard an in-progress war — this refutes the research
  agent's caution about blacklisting it.
- **All 3 arena payouts collected from the Inbox** (+270 crystals) with no PvP match played.
- **Free Bronzium claimed** (daily quest) · **daily-activity milestone claimed** (+45 Normal/+45
  Cantina) · purchase dialog captured and **cancelled** without buying.
- **Templates 38 -> 68.** `--doctor` = full blocking coverage on a 16-entry routine.

### Corrections to earlier notes
- **Energy pool -> HUD icon mapping** (read off the Campaigns cards): blue=**Fleet**, teal=**Mod**,
  red=**Cantina**, gold=**Normal**. Earlier sessions had this ordering wrong.
- **Cantina 1-A is "Bracca"**, not Geonosian Soldier, and drops his shards + Mk I-III ability mats.
- The 50-agent research (`docs/swgoh-daily-automation-spec.md`) disputes several config nodes
  (Cantina 1-A, Fleet 1-E as already-7-star; Mod 2-D over 2-F). Its adversarial pass **refuted 35
  of 40 claims it checked**, so it is a hypothesis list, not gospel. Nodes were left as-is with the
  dispute recorded in `config.example.json`; settle Mod 2-D vs 2-F with `pull_mods.py` +
  `slice_plan.py` against live inventory, and the rest by reading reward icons on device.

### Still open
- `calendar_claim`: all 4 login calendars were already CLAIMED today, so the green button could not
  be captured. Wired to reuse `inbox_claim` (scored 0.670 on the greyed button at the right
  position, so it should match when green) — confirm on an unclaimed day.
- `defeat` (soft): needs a lost battle to capture. Its absence turns a graceful loss-skip into a
  halt, which `--daily` isolates.
- `hard_depleted` was cropped from LS Hard's 💎25 refresh chip; **Fleet Hard shows 💎200**, so the
  marker will miss there and that node will halt instead of skipping. Needs a second crop.
- **Fleet Challenge is a separate screen** from character Challenges — the bulk MULTI SIM does not
  satisfy that daily quest.
- Shop `buys` is empty pending per-item template captures.

### Adversarial code review (28-agent workflow) — 11 confirmed, 13 refuted; all 11 fixed
The review measured things I had asserted, and several assertions were wrong.
- **`store_entry` was a featureless texture patch** (grayscale std 20 vs a 58 median): my crop was
  200px right of the word "Store" and caught bar-counter gradient. It false-matched at 0.917 on
  three unrelated screens, and the config's blind `-190` offset would then have tapped x=-154.
  Recaptured on the glyph (std 91) and the offset deleted — the word IS the hit target.
  → **`--doctor` now fails on any in-use template below std 25**, which immediately caught two more:
  `chapter_tab_mod_2` (19) and **`chapter_tab_8` (25)**.
- **`ADB.tap` now refuses off-screen coordinates** instead of shelling them out.
- **`collect`'s `count` loop drained one item per run**: a single trailing rewards-dismiss meant
  claim #2's button stayed covered by claim #1's overlay. Now dismisses after EVERY claim.
- **`battle` halted instead of skipping** once the day's attempts were gone (greyed START), which
  broke the routine's idempotence claim and stranded the app inside the battle screen. New
  `Step.skip_entry`: an absent optional START ends the entry cleanly, and OUTCOME stays REQUIRED so
  a genuinely unreadable result still halts with a screenshot.
- **A malformed entry raised straight out of `run()`**, losing the Summary, the report and every
  later entry — the one failure `--daily` exists to contain. Now booked as that entry's halt.
  Same in `devtool.coverage`, which used to print a traceback and nothing else.
- **`mark` fired before `ensure`**, so a recenter that never moved the camera still reported
  `recentered=1`. Counters are now booked only after the ensure check passes.
- **An optional step skipped without trying to clear a covering popup** — a calendar over the
  Quests screen would have read eight claimable crates as "nothing to collect".
- **`forbid` was classified SOFT in coverage**, so an uncaptured veto template silently disabled
  the crystal guard while `--doctor` said OK. Now blocking.

### THE DS chapter-8 halt — root-caused and FIXED after ~4 sessions
Not navigation at all. The halt screenshot showed the engine **already on chapter 8 with Taris 8-B
selected and MULTI SIM on screen**. Two separate stale-state bugs:
1. `SELECT_CHAPTER` was REQUIRED, but tab templates are captured unselected and the game remembers
   the chapter — so from the second visit on, the tab renders selected and the crop misses. Made
   OPTIONAL, exactly like `SELECT_DIFFICULTY` already was for the same reason.
2. `SELECT_NODE` had the same problem: the map keeps the last-played node selected. Added
   `Step.alt` and an optional `node_<campaign>_<id>_sel` companion crop. Matching THAT node's
   selected icon (rather than just "is a panel open?") is what keeps it from simming whatever node
   someone happened to leave selected.
**Verified live: `sims_done=1, halted_entries=0`** on an isolated DS 8-B run.

### Two screen classes that stranded whole runs (both now popup closers)
- **Coliseum "NEW HIGH SCORE / tap anywhere"** replaces the normal VICTORY screen on a record run.
  One un-dismissed banner cascaded into three following entries failing their HOME check.
  Also wired as `victory_alt` so the win is booked instead of halting.
- **Star-up celebrations** ("Mace Windu 7★") are full-screen with a bottom-right CONTINUE and
  **no home button**, so RETURN_HOME cannot work. Fired live off a bronzium.
- Related: the data-card flow leaves a **"BUY AGAIN 🪙250 / FINISH"** screen behind. `bronzium_skip`
  matches FINISH at 1.000 and **nothing in the template set matches BUY AGAIN** (verified against
  the live capture), so it was safe to promote to a closer.

### Rail verification against live captures (not assertions — measurements)
- `bronzium_claim` / `bronzium_free` score **0.54** against the paid "BUY 🪙250" button (threshold
  0.85) — the free-card templates cannot buy a paid one.
- `inbox_claim` scores **0.752** against a GO/DELETE guild-orders message — cannot mistake it for a claim.
- Crystals across every run this session: **5,045 → 5,340, monotonically up.**
- Suite **104 → 147**.

## 2026-08-04 — dailies-after-reset run + Coliseum/Conquest ground truth (READ BEFORE TOUCHING EITHER MODE)
Full daily executed live on Astra. **Crystals 5,340 → 5,515, only ever up.** Daily quests **6/8**
(remaining: 3 store Shipments = capped-currency spend, reserved to owner; 1 arena battle = PvP, excluded).
Suite **147 → 162**, `--doctor` OK. Nothing committed.

### Loot banked
GW fully simmed (647.2K cr) · Challenges + **Fleet Challenge** · **Smuggler's Run Deadly ×2** (900K cr +
slicing salvage) · **Bespin all 3 tiers** (3 Zeta, 10 Omega, 20 Mk III) · **Mara Jade marquee I–III** (+5
shards) · **LS Normal 8-H ×36** (30 Mk IV, 12 Mk X, 6 gear, 34.5K cr) · 5 login calendars · Episode Track
reward · Conquest Ascension free tier. All 4 energy pools dumped below cap → regen restarted.

### Corrections to earlier notes (device-verified, beat the research agents)
- **Squad Arena is NOT retired.** "Finish 1 Squad Arena or Fleet Arena battle" is live on the Quests
  screen — **8 daily quests, not 7**. A research agent asserted retirement from a Jul-2026 patch note; wrong.
- **The bulk Challenges MULTI SIM DOES satisfy the Fleet Challenge daily** (both showed complete after one
  sim). Contradicts the 2026-08-03 session-4 note claiming Fleet Challenge is a separate unsatisfied screen.
- **Energy-quest GO button navigates straight to the campaign** — cheaper than hub nav.
- **Normal-difficulty campaign nodes have plain icons (no character art)**, so Hard-map `node_*` templates
  never match on Normal. Normal = uncapped attempts, the correct sink for banked/overflow Normal energy.

### Coliseum — read the in-game Event Info, not forums (both research agents got parts wrong)
Authoritative, from Event Info → Feature Info:
- **Only ERA UNITS can be used.** Legacy roster (all 9 GLs, 14.36M GP) is inert here. Loaned units are
  lent at the account-wide **Loaned Unit Era Level** (was 22), raised by the daily *Loaned Unit Era Level
  Increase Calendar*. "Slot unavailable due to slot restrictions" = slot needs an owned Era unit.
  ⇒ **Era investment is the ceiling on this mode**, not squad choice or manual play.
- **4 bosses per Era; WHICH ONE YOU FACE ROTATES DAILY.** Do not pre-build a boss-specific squad.
- **Tier unlock = fully deplete the boss health bar.** All players start Tier 1. There is **NO
  "Full/Partial/Heavily Decreased" era-level penalty table** — an agent invented that from stale forum
  threads and it contradicts its own cited quote. Disregard.
- **Leaderboard RESETS DAILY; placement = your best attempt THAT DAY.** Tier progress + top score persist
  across the Era, but daily rewards need a good run *every* day. ⚠️ Earlier note called the score a
  "high-water mark, pure upside" — that's true of tier progress, **false for the daily payout**.
- Score = **% of boss HP removed**. Leaderboard value = tier faced × score. Highest tier has an overtime
  phase past 100%. Relic-10 mats from the leaderboard: **confirmed** (EA announcement).
- **Jotaz kit (in-game):** Heaving Bulk +250% vs **buffless** targets · Backhand Sweep dispels all and
  gives Jotaz **+2% stacking Offense per buff dispelled** · Rabid Rage **+10% TM per buff lost** · Boulder
  Toss +50% Offense (doubled on kill) · **Roar Of The Crowd: damage dealt rises and damage taken falls as
  points accrue** (built-in diminishing returns — treat "98–99%" community claims sceptically), and after
  **10 consecutive enemy turns** it gains 30% Offense/200 Speed/bonus turn and dispels everything.
  Immune to Ability Block, Buff Disruption, Daze, Distracted, Fear, Health Down, Shock, Stagger, Stun,
  cooldown increase. ⇒ **Blanket-buffing FEEDS it** (offense stacks + turn meter); stalling is punished;
  control comps are dead. Correct play = minimal targeted buffs on the likely Heaving Bulk target only.
  The "just reapply buffs" advice from research is a trap.
- **This session's mistake, recorded:** 5 attempts auto-battled with the pre-filled loaned squad → 51%
  (rank 241→216→222). Attempts are 5/day and the payout is daily, so that was real value spent blind.

### Coliseum engine facts (device-verified)
- **Each attempt needs TWO taps:** Coliseum `BATTLE (n)` → squad select `BATTLE`. `battle_start` matches
  BOTH, so the config's single `start` leaves attempt 2+ stranded on squad select. **Not yet fixed.**
- **Result-screen chain has FOUR classes**, not one: `victory` · `coliseum_highscore` (NEW HIGH SCORE) ·
  **`attempt_over`** (ATTEMPT OVER!, tap anywhere) · **`coliseum_results`** (BATTLE RESULTS + CONTINUE).
  First two were known; last two captured this session. Also seen: **TIER COMPLETE / NEW TIER UNLOCKED**.
- `attempt_over` wired into coliseum `victory_alt`. **`coliseum_results` captured but UNWIRED** — its
  CONTINUE sits ~464px BELOW the cropped title, so it needs an offset-capable popup closer.
- Exhausted attempts turn the button into a **💎250 refresh** — never tap.

### Conquest — located, scouted, NOT played (deliberate)
- **Entry point: the "Galactic Battles" console on the FAR-RIGHT hub pan** → a chooser with **WAR**
  (Galactic War) and **CONQUEST**. It is not in the Events menu and not on the default pan.
- **Conquest 24 = Leia (Jedi Training)**, ~90 shards in the red crate (~620–630 keycards), ends ~Aug 17.
  Sector 1 unstarted, Hard, 0/9 event feats, 230/3500 keycards. Pass+ owned.
- **⚡ 15,649 Conquest energy banked** (cap ~200, 15/battle) ≈ **1,000 battles**. Research says red crate
  is impossible without 3×50-crystal refreshes/day — **that does not apply here.** Red crate is reachable
  with **zero crystals**. The binding constraint is **stamina** (−10%/battle/char, +1%/30min) ⇒ ~2 battles
  per squad per session, twice daily.
- **No SIM in Conquest, ever.** Auto-battle exists inside a fight; every node costs 15 energy every entry,
  including replays. Not farmbot-automatable.
- **Feats are chained** (finishing one grants the data disk the next needs); Pass+ grants **Booming Voice**
  + **Deployable Cooling Systems** outright, satisfying two of them.
- **Roster covers the whole feat plan** (relic levels below CORRECTED −2 on 2026-08-05; they were quoted
  straight off `rt` and were each two tiers too high — see the Relic encoding note above):
  Cassian Undercover R8 + Cassian Andor R8 + Kleya R7 +
  **Vel Sartha R6** + Luthen Rael R7 (one team = Rebel-Fighter kills + Undermine + 20 Vel wins);
  Inquisitorius GI/5th/7th R7 + 8th R5 for Purge×300 (Third Sister still the gap); JML R10 + Satele R8
  (Offense Up ×500, Jedi Lessons S3); Starkiller R8 (Buff Disruption S5); Boba+Jango R8 (S5 10 wins).
  Kaz not owned — Cassian Andor fills slot 5.
- **Disks:** Desolation(2) + Volatile Accelerator(3) + Decay:Turn Meter(1)×2 + Weak Spot(2) + Fortified(3)
  = exactly 12. **Avoid Culling Slash** (4 slots, nullified by the Crit Immunity common on Hard).

### Engine / config changes this session
- **`quests_panel_final`** — a SECOND quests collect pass appended LAST. The first pass runs first so its
  energy grants feed the nodes, which means every quest the bot then *completes* finishes unclaimed. Cost
  4 unclaimed rewards before the fix; `collected=4` after. Keep both passes.
- `login_relic` added (5th calendar); all `login_*` now claim via the new **`calendar_claim`** template
  (was reusing `inbox_claim`). Coliseum `attempts` 1 → 5.
- **GW nav root cause:** the Quests list REORDERS as quests complete — completed rows sort to the top and
  push `quest_gw_row` below the fold, so nav halted at NAV_1 and the GW daily was missed. Agent added
  per-step `scroll_scan` + vertical swipe support (`up`/`down`); config hop now scrolls. **Swipe geometry
  was chosen without a device — needs a live run to confirm.**
- Agent also fixed: `collect` count-loop early-exit via `skip_entry` (22 wasted iterations → ~3),
  `_ensure_hub()` recovery at run start, `skip_marker_alt` for a second `hard_depleted` skin
  (Fleet Hard shows 💎200, the captured crop is LS Hard's 💎25), `tier_complete` as popup closer.
  It edited the gitignored `farmbot/config.json`; backup at
  `~/Downloads/202608040010_farmbot_config_backup.json`.
- **Templates +6:** `calendar_claim`, `cal_tab_relic`, `attempt_over`, `coliseum_results` (this session);
  `tier_complete` + `hard_depleted_200` still uncaptured (soft-missing, degrade safely).

### Open
- Coliseum two-tap-per-attempt flow unfixed; `coliseum_results` needs an offset-capable closer.
- Territory Battle (Mustafar ROTE) Phase 1 was live and **not deployed** — guild-coordinated, owner's call.
- GAC "SET DEFENSES" window expired during the session (PvP, never touched).
- Whether to invest in **Era units** at all is an open strategic decision — it is the sole lever on
  Coliseum, and Coliseum is a confirmed Relic-10 source.

## 2026-08-04 (session 4) — Conquest 24 SCOUTED LIVE + full feat list (supersedes the researched plan)
Walked Conquest end-to-end on device and won one node. **Templates +12.** Nothing committed.

### Navigation (device-verified)
Hub far-right pan → **`galactic_battles`** console ("Galactic Battles / Hard - SECTOR 1") → chooser
**SELECT A GALACTIC BATTLE** (WAR | **`conquest_card`**) → ENTER sits **+704px below the CONQUEST title**
(both ENTERs are pixel-identical ⇒ title-match + offset-tap, NOT an ENTER template) → sector list
(**`conquest_header`**, **`conquest_enter`**, **`conquest_locked`**) → sector map (**`conquest_feats_panel`**).

### Economy, corrected against the device
- **A node costs ⚡20, not 15.** Earlier note said 15. At 15,649 banked that is ~780 battles — energy is a
  non-constraint; **stamina is the only budget** (−10%/battle/char, +1%/30min).
- **Two separate currencies.** Blue slanted card = **keycards**, 3/node, 96/sector, shown per-node as `x/3`.
  Gold stacked card top-bar = the **250/3500** track. One 3-star win moved: node 0/3→3/3, sector 0→3/96,
  top bar 230→**250 (+20)**, Next Reward 0/1→**3/14**. So the two move together but are NOT the same number.
- **Data Capacity 7/12** — Booming Voice(4) + Legendary Consumable Boost(1) + Solid Intel(2). 5 free.
  **Pass+ makes disk swapping free.** Picked-up disks **auto-equip** if capacity allows.
- **Green hex = Data Disk Stockpile: a free one-tap disk, no battle, no energy.** Always take it first.
  Its side panel is **persistent, not a modal** — it does not dismiss on an outside tap; tapping another
  node replaces it. An engine that waits for it to close will hang.

### FEATS — read live. The researched plan was right about EVENT feats and had NO sector feats.
**SECTOR 1 (0/4, 5 keycards each) — all four are new information:**
| Feat | Requirement | At scout |
|---|---|---|
| Super Support | Grant at least 100 buffs | 7/100 |
| Raise da Shield | Gain Retaliate 15 times | 0/15 |
| The Slow Game | Attempt 300 DoT effects with an ability | 0/300 |
| Security Protocol Intact | Win 10 battles with **KX Security Droid** surviving | 0/10 |

**EVENT (0/9, 15 keycards each):** Follow My Lead (Booming Voice assists ×60, **2/60**) · Challenging
Victory (250 kills **on the golden Challenge Path**) · Imperial Inquisition (Purge ×300) · Strategic
Undermining (Undermine ×50) · Mission Above All (**20 wins with Vel Sartha**) · You Must Learn Control
(1 battle with Deployable Cooling Systems) · That'll Leave a Mark (Offense Up ×500) · Striking Back
(50 kills with **Rebel Fighter** units) · Family United (3 wins with **Princess Leia + Kylo Ren + Han Solo**).
⇒ Pass+ pre-satisfies the two disk-gated feats. The prior note's plan matches the EVENT list exactly.

### Roster check vs feats (from swgoh_roster_fresh_20260731.json) — everything needed is OWNED
- **KX Security Droid g13r9** ✓ — sector feat 4 is live, not a gap.
- **Inquisitor Barriss g13r9 completes the Inquisitorius five** (GI r9 · 5th r9 · 7th r9 · 8th r7 · Barriss r9).
  ⚠️ Prior note called **Third Sister the blocker for Purge×300 — she is not needed.** Confirm Barriss
  carries the Inquisitorius tag at squad select.
- Vel Sartha g13r8 · Cassian Undercover r10 · Cassian Andor r10 · Kleya r9 · Luthen r9 · Princess Leia r9 ·
  Kylo Ren r9 · Han Solo r10 · JML r12 · Satele r10 — all present.

### Squad routing (maximise feats per unit of stamina)
- **A · Rebels** (Cassian UC, Cassian, Kleya, **Vel Sartha**, Luthen) = Undermine + Vel-20 + Rebel-kills,
  **three event feats per battle**; on the golden path it also feeds Challenging Victory = **four**.
  Vel's 20 wins is the longest pole ⇒ **A is the default squad on every Light node it clears.**
- **B · Inquisitors** (five above) = Purge ×300, Dark nodes.
- **C · Jedi** JML lead + Satele = Offense Up ×500 and most of Super Support (buffs).
- **D · Family** Princess Leia + Kylo Ren + Han Solo — only 3 wins, cheap, clear it early.
- **E · Filler+KX** — put **KX Security Droid into the filler squad** so feat-irrelevant nodes still bank
  Security Protocol Intact. Jabba/Tarkin/Trench/Partagaz/Baylan (191,603, all 100% stamina) are in **no**
  feat, which is exactly why they were used for the scout battle.
- **F · ISB** (Major Partagaz L · Dedra Meero · Director Krennic · Imperial Probe Droid · KX Security Droid) — all g13r9, all owned, all Dark Side. **Raise da Shield feat:** "Authority Is Brittle" grants Retaliate to all ISB allies at Rank 2+; up to 4 gains per ability use → feat in ~4 uses (2–3 battles). ⚠️ ISB Rank 2 progression speed in Conquest (not GAC) is unverified — in GAC the full ISB team starts at Rank 3; in Conquest they likely start Rank 1. Test: watch for Retaliate icons on Dedra/Krennic when Partagaz uses the ability. **Also feeds Security Protocol Intact** (KX is here, saving the Filler slot).
- **G · Lord Vader Empire** (Lord Vader L · Darth Vader · Grand Admiral Thrawn · Seventh Sister · Darth Nihilus) — all g13, rt8–12, Dark Side. **The Slow Game feat (300 DoT):** "Unshackled Emotions" = 4 DoT × all 5 enemies = **20 applications per use** (unresistible, 5-turn CD). Classic Vader AoE special = 3 DoT × 5 = **15 more**. Community-confirmed top DoT team; 20/use × 15+ sector uses covers 300 with margin. ⚠️ Lord Vader's passive "2 DoT to all enemies at start of each LV turn" is unverified as "with an ability" for feat purposes — not needed regardless.
  - Fallback DoT squad if LV team committed elsewhere: **SEE L · Darth Vader · Bastila Shan (Fallen) · Darth Sion · Darth Nihilus** (all g13, DS Sith). Vader remains the DoT engine (AoE: 15/use).
  - **Darth Vader leader "DoT reapplies when it expires"** is a passive, NOT "with an ability" per EA rulings — do not count it toward the feat.
  - **Wat Tambor clarification:** "Discharge Energy" detonates existing DoTs, does NOT apply new ones — not a feat contributor. His basic applies 2 DoT single-target only (out of turn).
- **Alt Retaliate (Light Side nodes):** Boss Nass L · Gungan Phalanx · Gungan Boomadier · Captain Tarpals · Jar Jar Binks — all g13r9. "Raise da Shield" gives Phalanx Retaliate on self (1 gain per use). Need ~2–3 uses per battle × 7 battles. Slower but reliable and Gungan faction is strong.
- **Scorch (RC-1262 r9)** appears in community DoT team guides but is NOT on the wiki's confirmed DoT character list — treat as unverified; use the LV/DV/Thrawn/7th/Nihilus lineup instead.

### Templates captured (12) + reuse findings
`galactic_battles` `conquest_card` `conquest_header` `conquest_enter` `conquest_locked`
`conquest_feats_panel` `conquest_disk_stockpile` `conquest_disk_obtained` `conquest_combat_details`
`conquest_battle_btn` `conquest_squad_prompt` `conquest_select_squad_btn` `conquest_inventory`
`conquest_feats_screen`.
- **Reuse, do not re-capture:** `battle_speed` matched the Conquest battle at **0.921**; the post-battle
  REWARDS screen matched **`rewards` 0.996 / `victory` 0.995 / `celebration_continue` 0.992** — Conquest's
  result screen is the standard reward chain.
- `battle_auto` only made 0.593 *after* AUTO was tapped (active state differs) — needs an `_on` variant
  or a pre-tap match; do not treat 0.59 as a miss.
- **Two-tap battle start, same trap as Coliseum:** Combat Details `BATTLE ⚡20` → squad-select `BATTLE`.
  One `conquest_battle_btn` template matches BOTH, so a single `start` step strands the run on squad select.

### Session 4 addendum — 2 nodes played, feat deltas MEASURED, squad plan revised
**Battle 2** used a Rebel-Fighter squad (Cassian Andor (Undercover) **lead, "I Have Friends Everywhere"** /
Captain Drogan / Jyn Erso / Saw Gerrera / Captain Rex — all g13, all 100% stamina). One battle moved **four**
feats at once, which is the whole stacking thesis, measured rather than assumed:
`Striking Back 0→5/50` · `Follow My Lead 2→4/60` · `That'll Leave a Mark 0→5/500` · `Super Support 7→26/100`.
Sector 3/96 keycards after 2 nodes.

- **Feat lists RE-SORT as they progress** — feats with progress jump to the top, exactly like the Quests
  screen does (that reorder already cost a missed GW daily once). Any scraper must scroll BOTH ways.
- **Squad build is the expensive UI step, not the battle.** Tapping a roster portrait does nothing until a
  **slot** is selected first ("Tap a slot to add or swap"); after the first slot is picked, each portrait tap
  auto-advances to the next slot. The roster list **re-flows after every add**, so fixed coordinates drift.
  Filter dialog has faction checkboxes **and a free-text search box** — search is the only deterministic way
  to pick a specific unit. `SELECT SQUAD` opens the saved-squad manager (the GAC presets), not a Conquest picker.
- Vel Sartha, Kleya, Luthen and Cassian Andor **are** Rebel Fighters — they just sort below
  Drogan/Jyn/Saw/Rex in the filtered list, which is why the first five picks missed them.

### Retaliate + DoT resolved (research agent, cross-checked vs roster) — REVISES the squad table above
- **⭐ ISB serves TWO sector feats at once.** Major Partagaz (L) / Dedra Meero / Director Krennic / Imperial
  Probe Droid / **KX Security Droid** — all owned **g13 rt9**. Partagaz's *Authority Is Brittle* grants
  Retaliate to Rank 2+ ISB allies, **up to 4 per use** ⇒ `Raise da Shield` (15) in ~2–3 battles. And because
  **KX Security Droid is a native ISB member**, the same squad also banks `Security Protocol Intact`
  (10 wins with KX surviving). **This supersedes the earlier "put KX in the filler squad" idea.**
  ⚠️ UNVERIFIED: ISB starts at Rank 3 in GAC; the starting rank/progression in Conquest is unknown. If they
  start at Rank 1, Partagaz grants 0 Retaliate until Rank 2. Watch the first battle for Retaliate icons.
- **DoT ×300 → Lord Vader.** *Unshackled Emotions* = 4 DoT to ALL enemies, **unresistible** = 20/use.
  Team: Lord Vader (L) r12 / Darth Vader r9 / Thrawn / Seventh Sister / Darth Nihilus. Darth Vader's AoE
  adds 15/use. Backup: Tusken Shaman + Tusken Warrior basics (single-target but very high frequency).
  ⚠️ UNVERIFIED: whether LV's *passive* start-of-turn DoT counts toward "with an ability". Doesn't matter —
  the ability alone clears 300 across the sector.
  ❌ **Wat Tambor does NOT apply DoT** — *Discharge Energy* detonates existing DoTs. Do not slot him for this.
- ⚠️ **Stamina collision:** Seventh Sister and Darth Vader appear in BOTH the Inquisitor (Purge) and Lord
  Vader (DoT) teams. Running both squads in one session double-drains them. Alternate across sessions.

### Session 4 addendum 2 — engine kind landed + three unknowns measured
- **`conquest` entry kind built (TDD, device-free). Suite 162 → 183 green. Coverage 0 missing.** Nothing
  committed. `coliseum_results` is now wired as an offset popup closer at **+464** (still UNMEASURED — it
  came from this file's own "~464" estimate; treat as provisional).
- ⚠️ **Correction to this file:** the earlier note "needs an offset-capable popup closer" implied the engine
  had no offset tap. **Wrong** — `Step.tap_offset` already existed and was used by nav hops (`inbox_entry`
  −68, `quest_gw_row` +646) and `SELECT_CAMPAIGN` (+673). The only bare-centre tap was `_dismiss_popups`.
- **`CONQUEST_ENTER_TAP_OFFSET = (0,704)` is now MEASURED, not guessed:** `conquest_card` crop
  (1155,200)-(1445,262) ⇒ centre (1300,231); ENTER tapped at (1298,934) ⇒ **dy = 703**. Worked on both entries.
- **Data Disk Stockpile confirm resolved:** there is **NO confirm button**. The disk is granted on the node
  tap, the "You obtained this Data Disk" text is part of the **persistent side panel**, an outside tap leaves
  it pixel-identical, and the disk **auto-equips** (Inventory showed Solid Intel equipped, 7/12). The engine's
  `DISK_OK` step must be verify-only (`tap=False`).
- **NEW template `conquest_node_open`** (104×104, the bright ring of an un-cleared combat node). Multi-peak
  NMS against a live map: open **1.000 / 0.973**, cleared **0.663** (selection cursor) and **0.348**,
  background ≤0.34 ⇒ **threshold ~0.85 separates cleanly**, 0.31 margin. Cleared nodes render dim.
- ⚠️ **The cyan arrows are a SELECTION CURSOR, not an availability marker** — a cleared 3/3 node still
  carried them because it was tapped last. Do not use arrows to mean "open".
- **Still open:** which open node to attack is a genuine routing choice (branching paths + a distinct golden
  Challenge Path skin), and Coliseum's own two-tap-per-attempt bug in `_steps_battle` is untouched.

## 2026-08-04 (session 5) — Conquest nav VERIFIED LIVE + two template-decay bugs
Committed the whole session-4 batch (5 scoped commits), then ran the conquest entry on device with
`max_battles: 0` — which verifies the entire risky nav chain at **zero stamina and zero energy cost**.
Final result: `halted_entries=0, halt_state=None`. The chain HOME → HUB_ANCHOR → recenter → pan
far-right → GALACTIC_BATTLES → CHOOSE_CONQUEST(+704) → SECTOR_LIST → ENTER_SECTOR → SECTOR_MAP →
RETURN_HOME is now **device-verified end to end**, including the blind +704 offset and its guard.
Getting there took two template fixes, both the same failure mode.

### ⭐ Hub console labels are 3D SCENE OBJECTS, not flat HUD — templates are pan-specific
`galactic_battles` failed at the far-right end stop (0.318). It was NOT clipping and NOT scale: a
multi-scale sweep found the correct location but capped at **0.469 at best scale**. Stacking the
template over the live pixels showed the live text **sheared** — the baseline tilts down-to-the-right.
The label lies on a plane in the cantina scene and is perspective-projected, so **its skew changes
with camera pan** and a flat template only matches at the pan it was captured at. The old one came
from a mid-pan manual scout; the engine always drives to the end stop.
- **Fix: re-captured AT the far-right end stop.** Safe because `_pan` deliberately over-swipes into
  the stop — two independent pans there agreed at **0.9991** on the label region. New template scores
  **1.000**, cross-validated on a *separate* end-stop capture (0.9999), not just its own source.
- Crop deliberately stops short of the red **"3+" badge** — that is a changing notification count.
- ⇒ **Rule: any hub console label must be captured at the exact pan the engine will use.** Applies to
  every future console template, not just this one.

### ⭐ `home` had decayed to 0.815 — below threshold — and blocked EVERY entry
Second run halted at step 1, `HOME`, while unmistakably on the hub. The old 290×65 crop contained two
things that are not HUD invariants: the **3D scene's orange lamp** (hub background art changes between
episodes) and the literal text **"GP: 14.36"** (the account is now 14.37M). Measured 0.815/0.815/0.814
at far-left / mid / far-right — a constant failure, not a pan effect (the plate region itself is
0.9999 pan-invariant; the *scene art behind it* had changed since capture).
- **Fix: re-cropped to 132×54 — only the `85 Astra / MAX LE` glyphs.** Scores **1.0000** on all five
  captures on hand, including ones taken earlier at other pans.
- ⚠️ **This was a latent whole-routine outage**, not a conquest bug: `home` is step 1 of every entry.
- **`_ensure_hub` could not repair it** — tapping the home button does not restore a panned camera,
  so a run that halted at a non-default pan left the next run stuck too. The gap `_ensure_hub` was
  written to close is still open for the *pan* case; only the template fix made it moot.
- **Never let a template crop contain a counter that grows** (GP, credits, keycards) or 3D scene art.

### Confirmed good (live, free)
- `conquest_squad_prompt` **1.000** — and it crops the SUBTITLE "Tap a slot to add or swap a
  character.", never the title, which reads SELECT **LIGHT/DARK/NEUTRAL** SQUAD and would therefore
  only match a third of nodes. Verified on a NEUTRAL node. Comment added so nobody "improves" it.
- `conquest_battle_btn` 0.965 and `conquest_select_squad_btn` 0.996 on the live squad screen;
  `conquest_combat_details` correctly did NOT match there (0.340) — the two-tap ambiguity is real
  and the templates separate cleanly either side of 0.85.
- Disk step skipped (`collected=0`): the Sector 1 stockpile was already taken in session 4, which is
  the intended optional-skip behaviour rather than a halt.

### Open
- **No conquest BATTLE has ever run through the engine** — nav is verified, the fight path is not.
  `max_battles` is still 2 in the live config; node choice remains arbitrary and therefore manual.
- `coliseum_results` CONTINUE offset **+464 is still an estimate**, never measured on device.
- Sector 1 now shows **🎫22 keycards / 13d 16h left**; Conquest Ascension timer 6d 15h.
- Audit the remaining templates for the same decay: any crop holding scene art or a live counter.

## 2026-08-04 (session 6) — Conquest PLAYED for score: 310 → 410 on the 3500 track
First real scoring session. **6 battles: 5 won, 1 lost.** Sector 1 **22 → 37/96**, track **310 → 410**.
Nodes cleared 4 → 9. Crystals untouched at 240. Four of the five wins were driven **by the engine,
unattended** (`battles_won=4, battles_lost=0, halted_entries=0`) — the conquest kind works end to end.

### ⭐ THE SCORING UNIT IS MEASURED: one 3-star node = +20 track, +3 sector keycards
Confirms the session-4 guess. **Max score 3500 from 410 ⇒ ~155 more node wins.** At 10% stamina per
battle per character against +1%/30min regen (48%/day ⇒ ~4.8 battles/char/day), and with Conquest
ending in 13d 15h, **max score is a full-window daily grind, not a session's work.** Sector 1 is 96
keycards; Sector 2 is 96 and Sector 3 is 118, and 2 more sectors sit behind those, all LOCKED.

### ⭐ ONLY ONE GALACTIC LEGEND PER CONQUEST SQUAD
Hard game rule, discovered by hitting it: "Your squad already contains the maximum number of Galactic
Legends." Any plan that fields 2+ GLs is void. The shape is **1 GL + 4 non-GL**, which is lucky —
it is exactly the feat-stacking shape (a GL to carry, four slots to aim at feats).

### ⭐ SQUAD STRENGTH IS THE WHOLE GAME ON HARD — the ISB squad LOSES
- **ISB (Partagaz L / Probe Droid / Dedra / KX / Krennic), 144,156 power → DEFEAT**, wiped, all five
  enemies still standing, >5 min. Cost 20 energy and 10% stamina for nothing.
- **Lord Vader (L) / Darth Vader / Grand Inquisitor / Seventh Sister / Admiral Piett, 194,424 → WIN
  in 42 SECONDS.** Same node. 35% more power, ~8× faster.
- ⇒ **Do not run feat-optimal-but-weak squads on Hard.** A loss scores zero and still burns the
  resources. Win first, stack feats within a winning squad.
- Squads **persist between Conquest battles**, which is what lets the engine grind: build once by
  hand, then let `max_battles` run. This is the single most useful operational fact here.

### ⭐ DEFEAT IS A TWO-SCREEN STACK — and `defeat` cannot see the top one
A lost battle shows **`defeat_upsell`** ("Did you know you have upgrades available?") layered ON TOP
of the DEFEAT screen. Measured: `defeat` = **0.376** against the upsell, **0.968** once cleared.
The upsell has **no close X and no CONTINUE** — the back arrow at (65,65) is the only exit.
- **Fixed:** `defeat_upsell` wired as an offset popup closer, `(-891,-39)` from its match centre
  (956,104). Test added; suite 192 → 193; the template left "unused" since capture is now used.
- Still open: `_steps_conquest` OUTCOME waits the full `battle_timeout` before halting on a loss.
  Now that defeat is detectable it should short-circuit — a loss means the squad is too weak, so the
  remaining queued battles should skip rather than feed more nodes to a losing squad.

### ⚠️ CRYSTAL HAZARD: the Wandering Scavenger node
A green hex on the map is **not always a free Data Disk Stockpile**. Sector 1 has a **Wandering
Scavenger** shop node behind an identical green hex, selling:
`Overcharged Critical Chance Booster` **15 keycards** · `Overcharged Offense Booster` **75 CRYSTALS**
· `Overcharged Health Medpac`. One green **COMMIT** button for all of them — the same
mixed-currency-behind-one-green-button trap as Shipments.
- **`conquest_disk_stockpile` correctly did NOT match it** (no match at 0.4), so the engine's disk
  step is safe today. That is luck confirmed, not a guarantee: never widen that template.
- Backed out via an empty-map tap; crystals verified unchanged at 240.
- **The boss path runs THROUGH this node**, so advancing Sector 1 past node 9 needs a human decision.

### Engine gaps found while grinding
- **Boss nodes need their own template.** The Sector 1 boss (General Hux + Kylo Ren + 3 First Order
  elites, 10m timer, **7 keycards**) renders as a character portrait in a red double-ring;
  `conquest_node_open` does not match it (0.763 < 0.85). The engine skipped it as
  `battles_unavailable` — correct, not a crash, but it means bosses stay manual.
- A boss template keyed on the portrait will not generalise (each sector has a different boss); the
  red double-ring frame is the only invariant, and it is hard to crop without the portrait.
- `conquest_node_open` matched **0.992** on ordinary open nodes mid-grind, so the 0.85 threshold and
  the open/cleared separation both hold in the field.

### Feat state (device-read)
**SECTOR 1 — 2/4 done:** `Raise da Shield` ✅ · `Super Support` ✅ · `Security Protocol Intact` 2/10 ·
`The Slow Game` 0/300. The ISB thesis from session 4 was RIGHT — Partagaz's Retaliate cleared it.
**EVENT — 0/9:** Strategic Undermining **40/50** (closest; completing it grants the Booming Voice
disk, which is the prerequisite for Follow My Lead 7/60) · Striking Back 5/50 · That'll Leave a Mark
20/500 · Challenging Victory 1/250 · Imperial Inquisition 0/300 · Mission Above All 0/20 ·
You Must Learn Control 0/1 · Family United 0/3. Event feat reward is **1 keycard + a data disk**,
so feats are worth far less score than nodes (+20) — **clear nodes first, feats are a side effect.**

### Open
- Sector 1 blocked at the Wandering Scavenger (owner's call — crystal-adjacent).
- Lord Vader squad is down ~50% stamina after 5 battles; rotate squads or wait out regen.
- `conquest_squad_prompt` verified 1.000 live; `conquest_battle_btn` 0.965/0.992; the two-tap
  ambiguity held exactly as designed across 5 engine battles.

## 2026-08-04 (session 7) — Sector 1 ground out 44 → 65/96, track 430 → 550. Six wins, one loss.
Farmed for score across the whole afternoon. **7 battles: 6 won, 1 lost.** Sector 1 **44 → 65/96**,
reward track **430 → 550/3500**, sector feats **2/4 → 3/4**. **Crystals 240 at every single
checkpoint** — the rail held through two Data Disk commits and a Wandering Scavenger visit.
Two data disks taken (capacity 9/12 → **12/12**, now FULL). Conquest ends in 13d 3h.

### ⭐ THE OWNER'S STANDING ORDER CHANGED — decide, don't ask
Explicit instruction this session: *"Δεν είπαμε ότι εσύ, με βάση το research σου, θα αποφασίζεις…
Θέλω να αποφασίζεις και να προχωράς."* In-run Conquest choices (**which data disk, which branch,
which squad**) are now the agent's call, made from research and stated in one line — NOT a question.
This SUPERSEDES "Conquest node choice is strategic… routing stays the owner's job" in the
`_steps_conquest` docstring and the config `for` text. **The crystal rail is untouched by this:**
never spend crystals, never buy outside the whitelist.

### ⭐ THE DISK STEP HAS NEVER BEEN ABLE TO FIRE — `conquest_disk_stockpile` is the PANEL TITLE
`conquest_disk_stockpile` (355×44) is the text **"Data Disk Stockpile"** — the header of the panel
that only opens *after* the map hex is tapped. The DISK step uses it as its **tap target**, and
nothing in the engine ever opens that panel, so the step matches nothing and silently skips every
run. Past `collected=0` was NOT "already taken" (as session 6 recorded) — it was structurally
unreachable. Measured: 0.000 against the sector map with two stockpiles plainly visible on it,
then **1.000** the instant the panel was open.
- **There is no template for the map hex.** That is the missing piece, not a threshold tweak.
- The docstring's "the hex grants the disk on the spot and auto-equips it… no confirm button" is
  **wrong on all three counts**, measured live below.

### ⭐ WHAT A DATA DISK STOCKPILE ACTUALLY IS (4 screens, not 1 tap)
1. Tap hex → **panel: pick ONE of 3 disks** (scroll; "Select a Data Disk" footer).
2. Tap a disk → **"MOVE TO DATA DISK PILE"** confirm: *"You will advance and be unable to select a
   different path."* CANCEL / **COMMIT**. No price.
3. COMMIT → drops you into **CONQUEST INVENTORY**. The disk lands **UNEQUIPPED in inventory**; it
   does NOT auto-equip.
4. Tap it → equips if capacity allows → **CONFIRM** (greys out again once applied).
Capacity is the real limit: **9/12 → 11/12** after a ◆◆, **11/12 → 12/12** after a ◆. At 12/12 no
further disk can be equipped without swapping one out.

### ⭐ THE GREEN COMMIT BUTTON IS "MOVE", NOT "BUY" — corrects session 6's read
Session 6 called the scavenger's green COMMIT "the mixed-currency-behind-one-green-button trap".
Measured: COMMIT opens **"MOVE TO SCAVENGER — Are you sure you want to visit this Scavenger? You
will advance and be unable to select a different path."** It is the **movement** confirm. Buying is
a separate act (tap an item's price chip). Walked through the node buying nothing; **crystals 240
before and after, track 470 before and after.**
- ⚠️ **But the hazard is real and now better located:** the price chips render **grey/inert while
  you are adjacent** and turn **live green the moment you stand on the node**. So the dangerous
  screen is the one *after* the move, not before it.
- This scavenger's stock was **all keycard-priced, no crystals**: The Stranger ×5 / Satele Shan ×5
  @475 (both greyed, "You Own: Max"), Incomplete Signal Data ×5 @70 and ×10 @140 (own 955).
  Stock differs per scavenger — session 6's sold a **75-CRYSTAL** booster. Never assume.

### ⭐ `defeat` IS BACKGROUND-DEPENDENT AND FAILED ITS ONE REAL TEST (0.762 < 0.85)
The lost battle produced the two-screen stack exactly as session 6 described, and then:
`defeat_upsell` **1.000** at (956,104) — the documented centre, offset closer worked — but once the
upsell was cleared, **`defeat` scored only 0.762** on the clean DEFEAT screen. Session 6 measured
0.968. The difference is the **battle background**: the "DEFEAT!" banner is **semi-transparent**, so
the crop bleeds whatever scene is behind it (0.968 over a dark map, 0.762 over a bright white
corridor). Same decay class as `home` and `galactic_battles` — a crop holding scene art.
- ⇒ **Do NOT wire `defeat` as the conquest loss detector.** It would have missed today's actual
  loss. `defeat_upsell` (1.000) is the reliable signal, and it is already a popup closer.
- ⇒ `defeat` needs re-capturing, and a tight glyph crop may not be enough — the transparency is the
  problem, not the framing. Until then the generic `battle` kind's `skip_marker=defeat` is
  **weaker than it looks** and should not be trusted for Coliseum either.
- Correction to session 6: the DEFEAT screen underneath is **"Tap anywhere to continue"** with **no
  retry offer and no crystal-priced Stim Pack visible at all**. One observation, not a guarantee.

### ⭐ `conquest_node_gold` WORKS — 0.990, and needs NO code change to use
The Challenge Path (amber ring) node matched **0.990**, next peaks **0.696 / 0.652** (the dim,
unreachable amber nodes) — the same clean either-side-of-0.85 separation as `conquest_node_open`
(0.992 / 0.963 on two live open nodes). Because a battle spec names its own template, a gold node
is farmable **today** via config: `battles: [{"node": "conquest_node_gold"}]`. No engine change.
- Not added to the default config: gold = Challenge Path = harder, and the engine takes the best
  match blindly. Point it at gold deliberately, on a fresh squad.
- Combat details for the Sector 1 gold node: 5 mixed enemies, 3 stars, **3 keycards, ⚡20, 5m** —
  the *same* price and payout as a normal node.

### ⭐ SQUAD STRENGTH RE-CONFIRMED, AND THE STAMINA CURVE MEASURED
- **Mandalorians** (Bo-Katan Mand'alor L / Mandalorian Beskar / Bo-Katan Kryze / Cobb Vanth / SLKR,
  **171,446**) — won 3 (12s, 39s, plus one), then **LOST** a Resistance node at **64%** stamina.
- **Lord Vader / Darth Vader / Admiral Piett / Grand Inquisitor / Seventh Sister, 194,424** —
  **won that same node in 31s**, then 50s and 45s. Rebuilt from 81% stamina.
- **Stamina cost measured: ~9.5%/battle.** Mandalorians 92 → 64 over 3; Vader 81 → 52 over 3.
- **"Stamina & Energy — Regeneration Boosted"** banner is active on the squad screen (a Conquest
  Ascension perk), so regen beats the 1%/30min baseline: the Vader squad went 50% → 81% overnight.
- ⇒ Stopped the grind at 52%. A Challenge node on a 52% squad is the exact mistake session 6
  recorded; the node keeps, the stamina does not.

### ⭐ Two things about the squad screen worth knowing
- The green three-figure badge ("2/2", "1/2", "0/2") is **squad synergy** — how many of that unit's
  required allies are present. NOT a usage limit. SLKR read 0/2 in a Mandalorian squad.
- **The character list has a TEXT SEARCH.** Filter dropdown → bottom field → type → the on-screen
  IME needs its own **OK** before CONFIRM. Searching "vader" returned Lord Vader / Darth Vader /
  Admiral Piett; "inquisitor" returned Grand Inquisitor / Seventh Sister. This makes rebuilding a
  5-unit squad ~8 taps instead of scrolling a 200-portrait grid whose tiles show no names.
- `SELECT SQUAD` re-confirmed as the **Inventory→Squads GAC preset manager**, not a Conquest
  loader — it cannot apply a squad to Conquest. Tabs seen: GAC5, GAC 5v5 Def/Off, GAC 3v3 Def/Off.

### ⚠️ The far-right hub pan is FLAKY — a whole-entry outage, one run in two
Run 1 of the conquest entry **halted at `GALACTIC_BATTLES` with the hub still at its default pan**.
Run 2, identical config seconds later, panned fine and reached the sector map. A manual replay of
the exact same 8 swipes `(1400,560)→(500,560)` scored `galactic_battles` **1.000**.
- So this is **not** the session-5 template decay (that template is healthy: 1.000, four times).
  It is the swipes being swallowed — a timing/race against the hub scene settling after
  `HUB_RECENTER`, whose `ensure=TPL_HOME` passes on a HUD glyph that is visible mid-transition.
- ⇒ `_pan` should verify it actually moved (e.g. re-look for the target console and re-pan once)
  rather than trusting 8 blind swipes. Untouched this session.

### Scoring model, refined
Session 6 said "one 3-star node = +20 track, +3 keycards". Measured across 6 wins: the **track is
+20 per node win regardless of stars**, while **keycards = stars earned** (a 2/3 clear gave +2
keycards and still +20 track). Sector feats pay **2 keycards** each (Law of the Dunes, Not All
Bounty Hunters — both fired off one Mandalorian win). Nodes remain far better than feats.

### Session driver (not committed to farmbot/)
`~/Downloads/202608041629_conquest_grind.py` grinds nodes from an already-open sector map, reusing
the engine's templates and 0.85 threshold. It exists because the engine re-navigates from the hub
every run (~60s) and Sector 1's remaining path alternates combat nodes with disk/scavenger hexes it
cannot read — so a full engine run buys one battle per minute of navigation. It stops on defeat.

### Open
- **Sector 1 is at the gold Challenge node**, with the **Sector 1 boss (Palpatine, 0/9 keycards)**
  behind it. Both want a fresh squad — resume at 80%+ stamina.
- Disk step still dead until a **map-hex template** exists AND a disk-choice policy is decided
  (the panel is pick-one-of-three, so there is no "just tap it" behaviour to automate).
- `defeat` needs a background-independent re-capture; until then loss detection leans on
  `defeat_upsell`.
- `_pan` needs an arrival check (see the flaky-pan entry above).
- Disk capacity is **12/12** — the next stockpile forces a swap decision, not a free add.

## 2026-08-05 — Rise of the Empire Phase 2 played end-to-end (first full RotE session)
Guild #9 "Full participation on ROTE please!" · Phase 2/6 · Astra finished the phase **#1 contributor**.

### Navigation (device-verified)
Hub right rail → **GUILD EVENT** — tap the *icon* at `(1843,435)`, NOT the label at `(1843,495)`; the label
falls through (same rail-label trap as the hub consoles). → galaxy map → tap a planet → territory view.
Territory view: the **green reticle is a selection cursor, not a marker** — it sits ~114px *below* the
marker icon it has selected, and tapping the bare deploy node returns you to the galaxy map.
**Markers need ≥5s between taps.** At 3s the tap silently fails to move the cursor, and the right panel
still shows the *previous* mission — which reads as "all six missions have identical requirements".
Verify the cursor moved; don't trust the delay. (`scripts/rote_probe.py` does this.)

### Scoring model (measured, not assumed)
- Committing a squad deploys its **squad power** immediately, win or lose.
- A **win** adds a flat **250,000** on top (fleet missions 500,000). Bracca 34,991,556 → 35,453,904 on a
  212,348-power win = exactly 212,348 + 250,000.
- A **loss** adds nothing further — the results banner reads `RESULTS 0/1 · EARNED +0 Territory Points`.
⇒ Attempting is never worse than deploying, so **use the strongest squad available for every mission**.
  (The earlier "save your GLs for deployment" reasoning is wrong: their GP is credited either way.)

### ⚠️ OPERATIONS ARE THE PLATOONS — FILL THEM BEFORE YOU DEPLOY
The orange-ringed marker on each planet is an **Operation**: "Assign Characters (Relic 6+) and Ships
(7-Star)", 6 operations per planet, **15 slots each, +11,000,000 TP per completed operation**. Each slot
demands one *specific* unit. Quota is **10 assigned units per player per operation area**.
- That is **~733,000 TP per unit** vs ~40,000 for deploying the same unit — roughly **18× better**.
  18 operations × 11M = **198M TP/phase** available, against 250K for a whole combat mission.
- **Deployed units are permanently ineligible**: tapping a slot after deploying pops
  `UNIT ALREADY DEPLOYED — This unit has already been deployed to another mission and cannot be used here.`
- **This session's mistake:** deployed all 10,283,960 unallocated GP to Felucia *before* opening an
  Operation. Felucia Op1 was sitting at **14/15**, needing only Kylo Ren (Unmasked) R6+ — owned, at R8.
  That one slot was **+11,000,000 TP**, and Op4 (13/15, two matching units) was a second. ≥22M TP lost.
- **Correct order every phase: Special missions → Combat missions → OPERATIONS → deploy the remainder.**
  Red badges on the operation tiles = slots your roster can fill, but they are **stale** — they keep
  showing after the units are deployed, so they are not a safety net.

### Phase 2 board (Geonosis DS / Felucia Mixed / Bracca LS), star gates 148M/237M/316M (Bracca 142/228/304M)
| Territory | Missions |
|---|---|
| **Geonosis** | 3× `5x Dark Side or Neutral (R6+)` · 1× `5x Geonosians (R7+)` · fleet `Dark Side Ships (7★)` |
| **Felucia** | `5x chars (R6+)` ×1 free, +**Young Lando**, +**Jabba**, +**Hondo Ohnaka** · fleet `Ships (7★)` |
| **Bracca** | 2× `5x Light Side or Neutral (R6+)` · 1× `5x Jedi (R6+)` · fleet `Light Side Ships (7★)` · **Special: Cere Junda (R7+) + any Cal Kestis (R7+)** |
- Bracca's gold marker is the **Special Mission**; 30 guild completions unlock the **Zeffo** bonus zone.
- **`5x Geonosians (R7+)` is not fieldable** — Astra's best are Sun Fac/Brood Alpha/Poggle R6 and
  Soldier/Spy R5. Button reads `REQUIRED UNITS 0/5`. Needs 2 relic levels on three Geonosians.

### Result: 15 attempted, 13 won, 2 lost
Wins: Bracca Jedi (JML 212K), all 4 Felucia grounds (Jabba 224K / GL Rey+Hondo 207K / SLKR+Y.Lando 196K /
GL Leia 203K), Bracca LS ×2 (GL Ahsoka 199K, JMK 195K), Geonosis DS ×2 (SEE 197K, Lord Vader 194K),
all 3 fleets (Leviathan 674K, Negotiator 677K, Executor 674K).
Losses: **Bracca Special** (Cere R7 + JKCK R7, only 66,739 power — the slots are locked to those two, so
there is no stronger squad; it needs relics on Cere/Cal, not better selection) and **Geonosis G4**
(166,954, Doctor Aphra R7 lead — the one squad with no GL, because 9 GLs cover only 9 of the 10 missions).
- **The in-game auto-fill is good** — it produced every winning squad above unprompted. Its one real
  danger is spending a gated unit on a mission that didn't need it, so **run the gated missions first**
  (Jabba/Hondo/Young Lando/Geonosians) and it can never steal them.
- Capital ships: the fleet screen asks you to pick when the auto-pick is already used. Best per alignment
  = **Executor** (DS, 83K, all abilities MAXED) · **Negotiator** (LS, 84K, all MAXED) · **Leviathan** (103K).
- One combat mission ran **~820s** (Jabba, 2 waves); `rote_autobattle.py --max-wait` defaults to 480 and
  will report `timeout` on a fight still in progress. Pass `--max-wait 900`; re-attach with `--no-start`.

### New scripts
`scripts/rote_probe.py NAME X Y` — tap a marker, save panel + map crops (the ≥5s-and-verify rule).
`scripts/rote_open.py NAME X Y` — marker tap + panel BATTLE at `(1470,1006)` → squad screen.

## 2026-08-05 (session 2) — the daily closed at 7/8 for the first time; shop allow-list is live
A `--daily` already in flight from 02:05 finished clean: **19/19 entries, 5 nodes simmed, 2 challenges
multi-simmed, 12 collects, 1 coliseum win, 1 halt.** The halt is benign and will recur — `guild_raid`
stops at `OUTCOME_0` because the guild has **no active raid** (`Raid is not active`, `BATTLE (5)` greyed),
so there is no outcome screen to read. Nothing to fix; it is a greyed control the matcher can't see.

### ⚠️ A piped `--daily` shows NOTHING until it exits
`... --daily 2>&1 | tee log` buffers: Python block-buffers stdout when it isn't a tty, so 22 minutes of
progress sat in the buffer and `tail -f` showed an empty file. The run was fine. To watch a live run,
either add `-u` / `PYTHONUNBUFFERED=1`, or do what worked here — diff two `devtool shot`s a few seconds
apart and compare md5s.

### The two quests the bot leaves open are now ONE
Daily quests ended 6/8 with all six claimed. The two open ones were `Finish 1 Squad Arena or Fleet Arena
battle` (PvP — no code path, permanent) and `Purchase 3 store Shipments` (the empty shop allow-list).
The second is now closed, by hand today and by config from tomorrow → **7/8**.

### ⭐ Shipments, measured
- **One purchase per slot per refresh cycle.** Buying greys the tile and stamps a ✔ over its title.
  So `count: 3` on one item buys once and skips twice — three purchases need **three different items**.
- **Tapping the card TITLE opens the buy dialog**, same as the green price button (verified on Ship
  Building Materials, then cancelled). So the item template needs no `tap_offset`.
- ⇒ crop the **full-card-width title strip**. It excludes the `You Own: N` counter and the price, both
  of which change; and because the sold-out ✔ lands *on* the title, the match drops to **0.45–0.58**
  against the 0.85 threshold — idempotence for free, as long as the crop includes the title's right end.
- ⚠️ **An icon crop is the wrong instinct here.** A title+icon strip scored **0.977–0.981 on sold-out
  cards** — grayscale `TM_CCOEFF_NORMED` normalises away the "greyed" dimming, and that crop misses
  the ✔ entirely. The README's "cannot tell enabled from greyed" is the rule; the title strip only
  escapes it because the ✔ is destructive.
- ⚠️ **`Ability Material Mk I` cannot be templated next to Mk II.** Its title strip matches the **Mk II
  card at 0.975** — one extra `I` glyph over 375x42 is not enough signal. Chose three names that share
  no prefix instead: `t4_droid` / `ability_mk2` / `ship_materials`. Verified live: 0.454 / 0.584 (both
  sold out → skip) and 1.000 (available → tap).

### Astra's Cantina store is dead stock, so the token choice is free
Embo, Kit Fisto, Stormtrooper Han, Chopper, Cassian's U-wing all read **Max**; materials sit at
7,947 / 7,470 / 2,602 / 43.99M owned. **31K tokens with nothing to buy** ⇒ the 800/day the allow-list
spends is not a cost, and the 500 spent by hand today (Mk I 100 + Mk II 200 + T4 200) bought the quest,
not the items.

### Free claims the routine does not collect
- **Episode Track** pays out on a level ladder that the `collect` entries never open — level 22 had two
  waiting. Claimed the free one (256 of a purple mat). The other is on the **paid EPISODE PASS row**
  (brown tiles, gold border); it reads `Tap to claim` but may open a real-money upgrade page, so it is
  left alone — owner's call, one tap if wanted. Worth an entry only if the ladder tile can be templated
  without matching the pass row.
- **Coliseum "Rewards Available" is not a claim.** `RANK REWARDS` is an info panel of the rank ladder;
  it pays at reset. Rank 159 → `#91-250` → 300 tokens. Nothing to press. High score 19,551 (88%),
  **4 of 5 battles unused** — free score if anyone wants to grind it, no energy cost.

## 2026-08-05 (session 3) — FULL COMPETITIVE REBUILD: exact-ILP board, TW + Fleet Arena added, 63 → 99 squads
Owner asked for "the ABSOLUTE BEST setup" across GAC 5v5/3v3, Territory War, and arena/GAC fleets, with an
explicit ask to separate **datacron-driven (temporary)** meta from **kit-driven (lasting)**. Whole board
deleted and rebuilt. Live: **99 definitions across 9 categories**, verified no dup names, contents match
payload exactly, and **no unit repeats within any mode**.

### ⭐ THE METHOD CHANGED: greedy → exact ILP (`scripts/optimize_board.py`, scipy/HiGHS)
The old `compute_teams.py` filled defense first by Hold%, so an 18%-hold wall could eat the units of a
90%-win attacker. A GAC round is decided on **net banners**, so the right objective is
`Σ P(defense holds) + Σ P(offense clears)` — same units, so they add — solved as weighted set-packing with
one squad per unit. Measured gain over greedy: 5v5 +6, 3v3 +16 points.
- **Sensitivity-tested:** the 5v5 board is IDENTICAL for offense weights 0.6→1.1 (robust). 3v3 only flips
  The Stranger def↔off below α=0.65.
- **`MIN_SEEN = 5000`, chosen by measurement not feel:** n≥2000 scores 1283 but anchors the board on
  n≈3,000 rows; n≥5000 scores 1240 with every pick well-sampled; n≥10000 scores 1225 and throws away real
  variants. Sampling error at n=3,000 is only ~1 point — the risk is **selection bias** (rare variants are
  played by stronger players), which shrinkage cannot fix. 5000 also keeps the board verifiable on swgoh.gg.
- **GL Leia 5v5 is a genuine tie** (1240 def vs 1239 off). Broken toward OFFENSE on things the linear model
  can't see: you choose the matchup on offense, 96% is near-certain vs a 31% coin-flip, and hold% decays
  against Kyber opponents. In 3v3 there is no tie — forcing her to offense costs 13, so she walls.
  Encoded as `ATTACK_ONLY_BY_FORMAT`. Every other GL placement agreed with existing doctrine.
- **GL Ahsoka moved 18% wall → 90% attacker.** That single trade is what the greedy was getting wrong.

### ⭐ DATACRONS: read from primary data, and the finding is dated
`scripts/datacron_exposure.py`. Live sets (swgoh.gg/datacrons, 2026-08-05) — each offers exactly 2 choices
per tier; only the faction/role tiers discriminate (Light/Dark Side tiers apply to everyone):
| set | name | expires | faction/role tiers |
|---|---|---|---|
| 30 | Peace & Power | **~1 day (≈Aug 6)** | L6 **Sith \| Galactic Republic** |
| 31 | For Old Times | ~4 weeks | L6 Old Republic \| Separatist |
| 32 | Necessary Means | ~1 month | L3 **Healer \| Tank**, L6 Attacker \| Support |
| 33 | Supremacy Directive | ~2 months | L6 **Resistance \| First Order** |
- **⭐ Once set 30 lapses, NO live set grants Sith or Galactic Republic.** They lose datacron support
  outright rather than trading it. Season 81 already closed (`gac/list`), so the next season is played
  **after** the lapse — every Sith/GR rate on the board was measured with a bonus that is about to vanish.
- Concrete: the 37% Queen Amidala wall is **100% Galactic Republic with no GL**, which is exactly what the
  GR L6 affix ("at the start of battle, if there are no Galactic Legend allies…") is built for. Most
  cron-exposed pick on the defensive board.
- **Luminara Unduli is a Healer** (and GR/Jedi) and **Visas Marr is a Healer** — the #1 wall in the game
  (Stranger, 57%, n=29.8K) runs two of them, and its 48% variant swaps Luminara for **Barriss Offee**,
  also a Healer. That wall leans on set 32 (Healer), ~1 month left.
- ⚠️ **A haircut was tried in the optimiser and REJECTED — record this so it isn't retried.** At 20% the
  tag proxy is so pervasive (almost every squad holds a Sith or GR unit) that it stopped ranking and
  started scrambling: JMK's 95% 3v3 team fell to 76%, below a 78% Tarkin filler. A datacron modifies a kit;
  it is not why JMK is good. Turning it down far enough to stop the damage made it change nothing.
  ⇒ exposure is **reported per squad** in the playbook (RENTED / holds ~Nd / OWNED), not priced in.
  `DURABILITY_ENABLED=False`. The board is robust either way — the only pick it moved was a wall whose
  replacements were no better.

### ⭐ FLEETS WERE BADLY OFF-META AND ARE NOW GROUNDED IN BATTLE DATA
`/gac/ship-counters/<CAPITAL>/` rows are `[attacker ships…] + [defender ships…]`; splitting 542 of them at
the defending capital (**second** occurrence on a mirror) yields a real attacker×defender matrix plus the
lineups the meta actually flies. `scripts/build_fleets.py::analyse_counters`.
- **The old config was wrong:** it had Executor flying **Imperial TIEs** — the real Executor fleet is
  **Bounty Hunters**; and Leviathan flying First Order/Imperial ships instead of **Sith**. Raddus is
  **Resistance**, not Rogue One.
- Hold (attacker win%, lower=better): Profundity 77 *(unowned)* < **Leviathan 82** < Executor 87 <
  Negotiator 89 < Chimaera 90 = Home One 90 < Endurance 92 < Executrix 92 < Raddus 94 < Malevolence 95 <
  Finalizer 98.
- **Leviathan is the only owned fleet that answers everything** — 99% vs Profundity (5.1k), 96% mirror
  (16.9k), 94% vs Executor (6.9k), 100% vs Home One (9.2k). ⇒ **it cannot sit on defense.**
- Executor 98% vs Negotiator (11.1k) and Home One (5.2k), but 80% into Leviathan and 72% into its mirror.
- **Negotiator is 20% vs Home One (n=215)** despite 96% overall — never point it there.
- ⇒ OFF = Leviathan · Executor · Negotiator (covers all 11 defendable capitals at ≥94%);
  DEF = Chimaera · Home One · Raddus. Ship-disjoint; packages are faction-disjoint anyway
  (Chimaera/Executrix share Imperial TIEs, Negotiator/Endurance share Jedi-Clone).
- **Fleet Arena = Leviathan** (best owned at both jobs; arena has no shared-ship rule).
- Only 2 ships below 7★ in the whole roster: **Raven's Claw 6★** (Home One) and **MG-100 5★** (Raddus).
- **Profundity is capital-only** — every one of its starters (Han's Falcon, Outrider, Rebel Y-wing,
  Rogue One, Ghost, Phantom II) is already owned at 7★. Unlocking it alone yields the #1 defensive fleet.

### New/changed scripts
`optimize_board.py` (ILP) · `board_config.py` (sizes, MIN_SEEN, doctrine, durability switch) ·
`build_fleets.py` (counter parsing + lineups) · `datacron_exposure.py` · `build_board.py` (one-pass driver)
· `generate_upload.py` (payload + playbook) · `upload_hotutils.py` (**paced, retrying, resume-by-name**;
`--plan/--delete-all/--create`, HU_SID from env). Old `compute_teams.py`/`generate_hotutils.py` still work.

### Data-pull lessons
- **swgoh.gg param URLs no longer need a warm top-level navigation** — do a **same-origin `fetch()` from an
  already-loaded swgoh.gg page and parse with `DOMParser`**. Cloudflare only challenges top-level
  navigations. This is faster and immune to the agent-vs-agent browser contention that broke navigation.
- Squad table columns are `['', Seen, Hold%/Win%, Banners]`; `cutoff=0&sort=seen` is what gives DEPTH
  (82 fieldable 5v5 def teams vs 24). `cutoff=0&sort=percent` returns n<10 rows at 100% — useless.
- Ship counters live at `/gac/ship-counters/season/<SEASON_ID>/` (list) and
  `/gac/ship-counters/<CAPITAL>/?season_id=…` (detail); they render as `.panel` cards, NOT tables.
- Unit faction/role tags: `/api/characters/?format=json` → `role`, `alignment`, `categories` (340 units).
- **`gac/list` (HotUtils API) gives real match history + `mapId`** e.g. `4zone_3v3_ga2_c3s1_81a`. Confirmed
  Kyber, 4 zones. Astra S81 record 0-1 (lost 966–1165), S80 1-1.
- Seasons: **S80 = latest 5v5, S81 = latest 3v3, S82 not yet published** (404).

### Board sizes used
GAC 5v5 11 def + 11 core off + bench · GAC 3v3 15 + 15 + bench · **TW 5v5 15 + 15** (deeper bench,
`off_weight 0.75` because a TW territory pays nothing unless fully cleared and the enemy guild has a finite
attempt pool) · fleets 3 + 3 + 1 arena. ⚠️ **TW per-player defensive slot count was NOT verified this
session** — the list is ranked so it can be set top-down until the map runs out.

### Gaps (unchanged shape, now quantified by how many meta squads each unit blocks)
**Third Sister blocks 8** (best: an 86% 5v5 offense and a 34% 5v5 wall) · Pirate King Hondo 7 · Vane 7 ·
Brutus/Captain Silvo/SM-33 4 each · Jedi Master Mace Windu 3 · Cobb Vanth 3 · 4-LOM 2.
**Fleet gap: Profundity** (capital only). **Star-ups: MG-100 5★→7★, Raven's Claw 6★→7★.**

### Fleet addendum — independent agent review (same session), 3 changes applied
A parallel research agent re-scraped **S81** fleet data (Kyber, 222K battles) against my S80 pull and
**independently reproduced the hold table within 1pp on all 11 capitals, same ordering** — so the fleet
hold ranking is stable across two consecutive seasons, not a one-season artifact. It also confirmed
Leviathan as the #1 fleet-offense build on swgoh.gg's S81 tier list (S tier, Elo 2992, 96.3% / 26.4K).

**⭐ CORRECTION APPLIED — Leviathan reinforcement order was backwards. Scimitar BEFORE Mark VI.**
- Scimitar grants allies **+30 Speed** (15, doubled for Sith) and **the stacks survive its death** ⇒ it
  must land first to win the race to the capital ultimate.
- Mark VI must arrive **after Sabotage the Hangars**, because Leviathan's unique gives it **+10 extra
  Devouring Swarm stacks** on its first turn after deployment. Calling it early wastes that.
- Correct manual sequence: **Sabotage Engines → Scimitar → Sabotage Hangars → Mark VI.**
- My original order came from *frequency of appearance* in the counter data, which encodes **usage, not
  call sequence**. That was a genuine methodological error — the counter panels cannot answer ordering.
- **The data actually corroborates the agent's mechanism.** Slot analysis of 51,367 Leviathan attack
  lineups: Fury/B-28/TIE Dagger are 100% at slots 0/1/2 (starters confirmed), but **Sith Fighter holds
  the FIRST reinforcement slot 95% of the time** with Mark VI last (46% slot4 / 49% slot5). That is the
  **AI's fixed reinforcement priority showing through auto-played battles** — Sith Fighter outranks
  Scimitar on the AI's hidden tier list, exactly as the agent described.
- ⚠️ **AUTO TRAP:** on auto you don't choose. If Astra autos arena, drop Sith Fighter and fill with
  **TIE Defender / Scythe / TIE Bomber** (they share Scimitar's priority tier) so Scimitar fires first.
  Order matters little in GAC (Leviathan wins ~97% either way) and decisively in Fleet Arena.

**Other applied changes:** Arena Leviathan now runs **8 slots** with Emperor's Shuttle as R4 (arena has no
shared-ship rule, so it can borrow Chimaera's ship); Executor's empty 8th slot filled with **Ebon Hawk**
(1.8% of observed Executor lineups — filler, not a recommendation).

**REJECTED refinement (record the reason):** the agent suggested DEF=Endurance / OFF=Raddus (Endurance
debuted #5 on the S81 defense tier list). **Infeasible — 7 of Endurance's 9 meta ships ARE the
Negotiator's** (Marauder, Umbaran, ARC-170 Rex, Anakin JSF, Blade of Dorin, Ahsoka JSF, Y-wing CW), and
Negotiator is on offense. Only Ebon Hawk + Clone Sergeant's ARC-170 are free of it — not a fleet. Also
noted: Endurance's #5 debut rests on 510 battles / 29 builds, i.e. a novelty spike likely to regress.

**Confirmed, act on it:** **datacrons do not affect fleets at all** — swgoh.gg's fleet tier list carries a
live datacron column and reports "no character-specific datacron is commonly run" for all 11 fleets on both
views. Exclude datacrons from fleet planning entirely. Also: **no new ship or capital ship has released in
all of 2026**; all 2026 content is character-side Era releases. Nothing imminent changes the fleet board.

**Arena ≠ GAC (why Fleet Arena is its own category):** no no-repeat rule, so run the single best fleet for
both attack and defense; nothing holds (Levi mirror ≈99% attacker), so rank is a **payout-timing** game,
not a fleet-choice game. Climbs-better-than-holds: Chimaera, Leviathan. Holds-better-than-climbs: Home One
(#4 defense but only 73.5% offense). Astra's **Darth Revan is R10**, which wins Leviathan mirrors (the race
is decided by relic depth).
⚠️ UNVERIFIED: Fleet Arena has **no published stats anywhere** (swgoh.gg is GAC-only), so all arena-specific
ordering/priority claims are mechanics + community consensus, and the published reinforcement-priority tier
lists date from 2018/2021 and predate every modern capital. The *mechanic* is current; the ship lists are not.

**New tooling:** `upload_hotutils.py --sync` — deletes definitions that are stale OR whose contents changed,
then creates the missing ones. Needed because `--create`'s resume-by-name deliberately skips existing names,
which silently no-ops when a lineup changes. Verified: it found exactly the 3 altered fleets, left 96 alone.

## 2026-08-05 (session 3, addendum) — ⭐ FOCUSED DATACRONS: the thing the faction proxy could not see
Two research agents came back after the first upload and one of them overturned a conclusion I had
already shipped. Board re-optimised and re-synced: **98 definitions live, verified.**

### ⭐ I WAS WRONG ABOUT LUMINARA — and the mechanism generalises
I attributed Luminara Unduli's defensive value to the **Healer** role tier of set 32 (~1 month left).
Wrong. She holds a **FOCUSED datacron in set 30**, which expires **2026-08-06T07:00Z — tomorrow.**
Verified directly at `/datacrons/30/?template_id=datacron_set_30_focused_luminaraunduli`:
`Is Focused: True · Allow Reroll: False · Expiration: in 1d`.
- **Set 30 "Peace & Power" has exactly FOUR focused characters** (enumerate them by regexing
  `datacron_set_\d+_focused_[a-z0-9_]+` out of the set page HTML — the index's "8 FDC Variants" counts
  each one twice, base + `_upgraded`):
  **Cassian Andor (Undercover) · Darth Revan · Dedra Meero · Luminara Unduli.**
  (Set 33's are Bishop / Raccoon / Snowtrooper Commander — none on this board.)
- **A focused datacron keys off ONE NAMED CHARACTER.** No faction/alignment/role heuristic can ever see
  it. That is precisely why my `datacron_exposure.py` coverage proxy missed the single biggest effect on
  the board while confidently flagging things that didn't matter. **Enumerate focused variants explicitly.**

### ⭐ THE COUNTERFACTUAL IS PUBLISHED — stop guessing haircuts
I had claimed the magnitude "is not something this data can measure". It is.
**`/tier-list/gac/?side=defense` and `/tier-list/3v3/?side=defense`** break each leader's rate down by
which datacron affix was running, and one row is literally
`L9 – Unactivated affix / "Doesn't apply to this squad's units"  43.5% · 17.5K` — the same squads measured
where no L9 applied. **ratio = baseline / headline** is a measured durability estimate.
- Parse with **`details.group.border-b`** (one per leader, 100/page). A regex over the whole page
  innerText BLEEDS affix rows between leaders — it produced Rey at 9.6% and ratios of 2.33. DOM-scope it.
- Cross-validated against an independent agent scrape: Stranger 43.5%, Cassian UC 12.4% — exact match.
- **Offense ratios all fall in 0.87–1.04**; defense ratios run **0.35–1.15**. An attacker already winning
  90% isn't carried by a datacron; a 25% wall can be more than half rented. ⇒ apply to **DEFENSE ONLY**.
  `scripts/durability.py`, `board_config.DEFENSE_DURABILITY = True`. Clamp [0.35,1.15], min baseline n=1000.

### Measured ratios that changed the board
| leader | 5v5 | 3v3 | verdict |
|---|---|---|---|
| **Cassian Andor (Undercover)** | 25.1→12.4 = **0.49** | 28.9→7.8 = **0.35** (clamped from 0.27) | holds a set-30 FDC; **DROPPED from 5v5 defense** |
| The Stranger | 49.5→43.5 = 0.88 | 25.2→18.7 = 0.74 | durable, still #1 in 5v5 |
| **Queen Amidala** | 25.3→**30.8** = 1.15↑ | 35.2→21.6 = 0.61 | baseline HIGHER in 5v5 → promoted to #2 |
| Lord Vader | 26.1→28.5 = 1.09↑ | 40.7→31.8 = 0.78 | durable |
| Ahsoka Tano | 16.5→17.0 = 1.03 | 29.5→23.9 = 0.81 | durable |
| Jabba | 18.8→17.7 = 0.94 | 20.4→18.9 = 0.93 | durable |
| Resistance Finn | 16.6→10.7 = 0.64 | — | dropped from 5v5 defense |
Board deltas: 5v5 def −Cassian UC/−Res Finn, +Saw Gerrera Rebels 20% / +Great Mothers; 3v3 Stranger trio
and Queen Amidala trio moved to **offense** (92% / 85%) now that their walls are discounted.
3v3 defense sum 318→250 — that is the honest post-datacron number, not a regression.

### Corrections to my own earlier note (2026-08-05 session 3)
- "no live set replaces Sith/GR" — **overstated**. They lose the **L6 faction tier only**; L3 Light/Dark
  Side survives in set 33 and set 32's role tiers are faction-agnostic. One tier, not a blackout.
- **Set 33 lands the same day set 30 dies (6 Aug) — there is no gap.** Expiries run an exact 28-day
  drumbeat (Apr 15 → May 13 → Jun 10 → Jul 8 → Aug 6 → Sep 3 → Oct 1 → Oct 29) ⇒ **set 34 ≈ 3 Sep**,
  contents UNVERIFIED (no CG post, no datamine; CG dropped quarterly Road Aheads, expect ~1 week notice).
- **Satele Shan was NERFED 2026-07-22** ("leader ability no longer grants Bastila a turn loop") AND loses
  her set-31 datacron 3 Sep. Double hit — do not invest there.
- The 5v5 tier list is **Season 80 data generated under sets 29/30/31**; set 29 already died 8 Jul, so some
  5v5 numbers are stale-inflated today. 3v3 (S81) is current.

### Territory War — rules VERIFIED (first-party), one still open
Source: official CG "Territory Wars Overview" (swgoh.gg/news/territory-wars-overview/).
- **THERE IS NO PER-PLAYER DEFENSIVE SQUAD CAP.** Quote: "all contribution limits… are **Guild limits not
  player limits**… place all their troops down". Per-territory slots scale with the *smaller* guild's
  member count; it is a guild-wide, first-come pool. ⇒ **my ranked "set top-down until the map runs out"
  is the correct behaviour — do NOT cap at N.** Exact formula UNVERIFIED (the community `min(players)÷2`
  figure is folklore).
- **A unit on defense cannot attack, and vice versa** — confirmed, and units do NOT refresh between phases.
- **A winning attack squad is locked out** ("attacking squads that *successfully* defeat an opponent are not
  available for future attacks"). **A LOSING squad: UNVERIFIED** — the word "successfully" implies losses
  don't lock, the one first-hand account describes a *retreat*, and search summarisers assert both.
  30-second test on attack day: throw a junk squad, lose deliberately, re-open squad select.
- **No per-player fleet slot** (fleets come from the same guild pool). No documented attack-attempt cap.
- **Datacrons DO apply in TW** (and GAC and Squad Arena); **NOT** in Territory Battles, Fleet Arena/any ship
  mode, or Conquest ⇒ the 6 Aug cliff hits the TW bank too, but never the fleets.
- **33 units have TW-ONLY omicrons and Astra owns all 33.** Highest-leverage buy: **Ahsoka Tano (Fulcrum)** —
  her TW omicron is the classic attempt-eater (if no other active allies: +100% Armor Pen/Crit Avoidance,
  +75% Def/HP/Off/Prot, ignores Taunt, kills can't be revived) and she currently has **0 omicrons applied**.
  Also: **Embo's** TW omicron regenerates Bounty Hunter protection every turn, which directly undoes TW chip
  damage — the Jabba+Embo wall is a better TW wall than its GAC hold implies (it is on the board at D11).
- ⚠️ **Wampa's and Darth Bane's omicrons are GRAND ARENA, not TW** — their famous cheap clears are weaker in
  TW than their GAC win rates suggest. Wampa is correctly absent from the TW bank; Bane/Sidious is kept at
  TW O8 anyway because **TW pays +1 banner per EMPTY slot**, so a 2-unit clear banks the same as a 5-unit one
  while burning three fewer units. **Darth Traya's omicron is also GA, not TW.**

## 2026-08-05 (session 3, addendum 2) — LEAGUE POPULATION: a real gap, and a correction I built then REJECTED
The 3v3 agent raised the biggest methodological objection of the session: the board is built on
**all-league** data while Astra plays **Kyber**. Verified, quantified, and then mostly NOT acted on —
the reasoning below is the durable part.

### ⭐ Verified: the league filter exists, but NOT where the board needs it
- `/tier-list/gac/?side=defense&league=kyber-d1` and `/tier-list/3v3/?...` **work** (60 leaders vs 134;
  a bogus league value falls back to base, so the param is genuinely honoured). Options are
  **kyber-d1 · aurodium · chromium · bronzium · carbonite** — only ONE Kyber bucket.
- **`/gac/squads/` IGNORES it.** `?league=kyber-d1` returns byte-identical rows to `?league=zzz`.
  ⇒ **there is no LINEUP-level Kyber-only source.** The board is lineup-level; the league data is
  leader-level. That granularity mismatch is the whole problem.
- Astra is **"Kyber 3"** per swgoh.gg (skill sub-tier, League Rank #19038). *Division* is a separate,
  GP-based axis; at 14.37M GP Astra is almost certainly Division 1, but the swgoh.gg leaderboard is
  JS-rendered so this was **not** directly confirmed. Treat `kyber-d1` as "very likely the right
  population", not proven.

### ⭐ THE TRAP: a leader-level league ratio confounds SKILL with BUILD MIX
`kyber_d1_leader_avg / all_league_leader_avg` mixes two effects and you cannot separate them:
- 5v5 **Rey**: all-league **531 builds** / 15.2K battles → 9.6%. Kyber-D1 **57 builds** / 2,724 → 20.9%.
  Ratio 2.18. Rey does not get *better* against better players — the low-league average is dragged down
  by hundreds of junk Rey builds. Applying that 2.18 to the one good lineup (measured 31%) made it the
  **#1 wall on the board off pure artifact.**
- Same shape for Boss Nass 3v3 (x1.69). Of 15 comparable 5v5 leaders and 18 in 3v3, **exactly one each
  moves in the "wrong" direction — and both are build-mix artifacts.**
- A median-shrinkage variant was also built (to stop "no Kyber data = no haircut" quietly promoting
  squads nobody at Kyber plays). It fixed that bias but not the confound, and it crushed board sums
  (5v5 288→212, 3v3 250→160) without improving the ordering.
⇒ **`league_adjust.APPLY_GLOBAL = False`.** Do not resurrect the global multiplier.

### What IS applied: one override, where two independent lines of evidence agree
`KYBER_OVERRIDES[("3v3","Rey")] = 0.31` — the **Rey / Ben Solo / Luminara** wall reads **10.3% at
Kyber-D1 (n=5,222)** vs 33.2% all-league, **and** its Luminara carries a Set 30 focused datacron dying
2026-08-06. Two unrelated reasons, same direction. **Demoted from 3v3 defense #2 → #13.**
Everything else with a Kyber-D1 shortfall is **flagged in the playbook, not multiplied**
(Lord Vader 16.8 vs 26.1 · Palpatine 15.7 vs 21.2 · Saw Gerrera 8.4 vs 20 · Jabba 12.7 vs 18.8).
**Upside ratios are never applied** — they are the direction build-mix bias pushes.

### ⭐ The 5v5 board is VALIDATED by the correct population
Rank in all-league → rank in Kyber-D1: The Stranger **#1 → #1** (40.3%, n=6,288); and nearly everything
else RISES — Partagaz +16, Ahsoka +16, Jabba +13, Palpatine +10, Queen Amidala +9, Baylan +9, Satele +8,
Cassian UC +5. Nothing meaningful falls. **No 5v5 changes were needed.** That is a genuine result, not an
absence of findings.

### Other agent findings worth keeping
- **Set expiry times are exact** (from `datetime` attributes, not the rounded "in 1mo" display):
  30 → **2026-08-06 07:00Z** · 31 → 2026-09-03 · 32 → **2026-10-01** (8 weeks, not the ~1mo I wrote) ·
  33 → 2026-10-29. Set 29 (Rebel/Rebel Fighter) **already died 2026-07-08**.
- **Set 30 holds the #1, #2, #3 and #5 datacrons in the game** (Sith Trooper 89.4% ▲11 B→S, Mace Windu
  88.8% ▲8 B→S, Sith Assassin 88.4%, Count Dooku ▲6) — all dead tomorrow, no replacement.
- **The Stranger 5v5 is NOT Healer-cron inflated** (my earlier hypothesis, now doubly refuted): swgoh.gg
  does not flag it dependent; the squad is **mixed-alignment with no shared faction**, so no L3/L6 cron
  covers it; and Luminara-vs-Barriss (57 vs 48) cannot be a Healer effect because **both are Healers**.
  The 9 points are a unit-choice effect — and plausibly Luminara's FOCUSED cron, which dies tomorrow.
- **`memory/notes.md` GL Hondo entry is STALE** — the old "#1 3v3 wall, 38% hold" reads **3.5% in
  Kyber-D1 / 9.8% Kyber-default** on S81. **GL Hondo is no longer a priority gap.** Third Sister and
  Profundity still stand.
- **4-LOM at G11 is the top gear investment**: G13 unlocks Jango/4-LOM/Asajj (Kyber-D1 **#4, 27.5%**).
  Set-31 propped, so a ~4-week half-life.
- **GL Mando & Grogu is announced and imminent** (Rotta Journey rerun gates it) — will reset the board.
- Undersizing pays: solo SEE averages **56.68 banners** vs ~50 for a 3-unit clear, because empty slots
  grant bonus banners. Solo SEE (97%) strictly beats SEE+Wat (93%) and SEE+Bane (90%) in 3v3.

### Final state
**98 definitions live, verified**: no dups, no content mismatches, no unit repeated within any mode
(GAC 5v5 116 slots / GAC 3v3 105 / TW 145 / GAC Fleet 46, all distinct).

### In-game squad presets pushed (2026-08-05) — `scripts/push_ingame_presets.py`
HotUtils squads live on the website; this writes the same board into the GAME's preset manager
(Inventory → Squads), which is what you actually tap mid-round. **91 character squads across 6 tabs.**
- Tabs now: `PROG` (untouched, not ours) · GAC 5v5 Def 11 / Off 14 · GAC 3v3 Def 15 / Off 21 ·
  **TW 5v5 Def 15 / Off 15 (new)**. Verified: 7 tabs, **no duplicate tabs**, counts match the payload
  exactly, unit lists round-trip. Before/after snapshots in `data/hotutils_backup/game_presets_*_20260805.json`.
- **Deleted the stale `GAC5` tab (56 squads)** — provably the old board (11+15+15+15=56) from the
  2026-07-18 flat push, i.e. the squads the owner asked to replace. Backed up before deletion.
- **Names are derived from the HotUtils name** (`'5v5 D01 The Stranger 57%'` → `'D01 The Strang'`) so the
  two surfaces cannot drift; the format tag and the percentage are dropped (the tab says the format, and a
  percentage is noise on a button). **16-char limit is real** — longer returns
  `INVALID_SQUAD_PRESET_NAME_LENGTH_KEY`.
- ⚠️ **FLEETS STILL CANNOT BE PUSHED** — combatType 2 is rejected ("Currently only character squad presets
  are supported"). The 3 GAC defense + 3 offense + 1 arena fleet remain **manual in-game setup**.
- ⚠️ **`id: null` always creates a NEW tab** (no dedup by name), so the script re-reads `squads/game/get`
  every run and updates existing tabs BY ID. Re-running is safe; a half-failed run is not — re-read first.
- Don't `import generate_upload` to reuse its label map: that module executes on import and rewrites
  `output/`. The script reads `output/upload_payload.json` instead.

### Merged
PR **#16** squash-merged to master (`c95da42`) — the whole board rebuild. PR #17 = the in-game push script.

## 2026-08-05 (session 4) — Conquest 24 pushed to S3; why squads LOSE, and the one-GL rule
Resumed mid-Conquest (context cleared; the 15:20 driver `~/Downloads/202608051520_conquest_session.py`
was the live thread). Track **1,325 → 1,425 / 3500**, Sector 3 **12 → 34/118**, 12d 3h left.

### ⭐ ONLY ONE GALACTIC LEGEND PER SQUAD
Adding a second GL pops **`Galactic Legend Limit` — "Your squad already contains the maximum number of
Galactic Legends."** So "stack 5 GLs and steamroll" is impossible, and any squad plan that assumes two
GLs is dead on arrival. Corollary: a GL's value must come from the **4 non-GL allies its lead buffs**.

### ⭐ WHY SQUADS LOSE — it is difficulty scaling, not just stamina
From the Sector-2 info dialog (the `i` on each sector row): **"Relic 5 with +20–60% Stat Bonuses.
Stat bonuses increase further down the Sector."** Sector 1 enemies are relic **4**. So the same squad
that clears early nodes gets walled deeper in — independent of stamina.
- **Timers are the hidden loss condition:** normal node **5m**, boss node **10m**. A "loss" at **337s**
  was a **timeout**, not a wipe. Deep nodes need *burst damage*, not bulk.
- Measured this session: JML/GAS/Stranger/Cassian/Vel at **21–32% stamina** lost; a fresh **176,280**
  Family squad at **100%** also lost (197s, a real wipe). Stamina alone was never the whole story.

### ⭐ THE SQUAD THAT ACTUALLY WORKS — JMK meta, all Galactic Republic
**Jedi Master Kenobi (L, "Harmonious Will") + Commander Ahsoka Tano + General Kenobi + R2-D2 +
Padmé Amidala = 199,141**, all 100%. Cleared Sector-3 relic-5 **Inquisitorius** nodes in **67–98s**,
including the exact node that beat the Family squad. One GL, four allies its lead buffs — that is the
shape the one-GL rule forces. Squad persists across sectors and across nodes (deploys unprompted).

### Driver gotchas (cost real battles to learn)
- ⭐ **`conquest_node_gold` is the live-front template — NOT `conquest_node_open`.** On the current
  front node: gold **0.977–0.984**, open **0.458** (matches nothing). The script's `--node` DEFAULT is
  `conquest_node_open`, i.e. wrong; the docstring example is right. Always pass `--node conquest_node_gold`.
- ⭐ **The sector map PANS.** Coordinates read from a screenshot taken *before* opening any panel are
  stale by ~185px after returning. A hardcoded `--at` tap hit empty space. **Re-locate by template every
  tap** — that is also why the loop survives the pan between battles.
- The loop **re-taps an already-3/3 node** when no gold node remains, then hangs in `await_outcome`
  until its 660s timeout. Kill it and re-read the map rather than waiting.
- **Back arrow from a Wandering Scavenger exits the WHOLE sector** to the sector list, not to the map.

### Squad picker — deterministic recipe (the roster list re-flow, solved)
1. filter dropdown **(258,408)** → 2. text box **(635,959)** → 3. clear with `input keyevent 67` ×12 →
4. `input text "Name"` (use `%s` for spaces) → 5. ⚠️ **IME "OK" at (1840,1017)** — the IME overlay
**covers CONFIRM**, so tapping CONFIRM's coords hits the keyboard. OK applies the filter AND closes the dialog.
- Faction filters work too (`GALACTIC LEGEND`, `GALACTIC REPUBLIC`, …) and are better than text for squads.
- ⭐ **Re-flow is predictable, not random.** Removing the added unit shifts the grid up one cell, so if a
  unit you are skipping stays pinned at idx0 (e.g. tired General Skywalker 23%), **every next target lands
  in the same cell**: the whole JMK squad was built by tapping **(365,580) four times**.
- First unit added becomes **SQUAD LEADER**. `CLEAR SQUAD` (750,1007) first for a deterministic build.
- Cells: rows y≈580 / 790 / 1000, cols x≈143 / 365. Empty filter ⇒ "None of the units in this filter can be used".

### Unit-identity corrections (verified on the live picker)
- **Relic −2 re-confirmed:** Kylo Ren quoted "r9" → **relic 7**; Han Solo "r10" → **relic 8**.
- **"Leia Organa"** (olive-green, relic 10, 6 omicrons, lead *I Know*) **IS the Leia Galactic Legend** —
  she appears under the GALACTIC LEGEND filter. **"Princess Leia"** (classic white dress, side buns,
  relic 7) is the separate unit the *Family United* feat needs. Do not confuse them.
- A **"Leia"** text search also returns a young-Luke portrait, and **"Han Solo"** returns both Chewbaccas
  — the search matches more than the name. **Always verify by the name shown in the squad slot after adding.**
- **SLKR renders dimmed/unavailable** in the Conquest picker.

### Sector 3 feats (all mechanic-driven)
**Path of the Padawan (Jedi Lessons ×25) — ✓ DONE** (+10 keycards; FEATS 0/4 → 1/4). The cleared session's
Jedi squad was deliberately farming it. Remaining: Stunning Tactics **16/50** · Flawless Victory **5/20**
(a win that loses any unit does NOT count — 3 wins added 0) · Maximum Output (Overcharge) **0/20**.

### Board state at 18:20
S1 **81/96** · S2 **64/96** · S3 **34/118** · track **1,425/3500** · **EVENT FEATS 2/9** · difficulty **Hard**.
⚠️ **Being on the Sector 3 map does NOT mean S1/S2 are cleared** — Conquest allows free movement between
sectors, and both are still short. Sector 1 has the lowest stat bonuses ⇒ **cheapest remaining keycards**.
- **Wandering Scavenger** (green hex) is a **shop**, not a data disk: Overcharged Critical Chance Booster
  for **15 keycards** or **75** of the purple currency, + Overcharged Health Medpac, behind a `COMMIT`
  button. Skipped — the purple currency was not positively identified as non-crystal.

### ⭐ A 3/3-STARRED NODE IS EXHAUSTED — RE-FIGHTING IT PAYS NOTHING
Tested directly on the **Sector 1 Palpatine boss** (Palpatine + Vader + Tarkin + 2 elites, all relic 4,
10m timer). Its panel already read **STARS ★★★ (3/3)** with **KEYCARDS 3/9**. Fought it anyway:
- **Cost:** 20 energy (14.3K → 14.2K) and **19% stamina** (JMK squad 70% → **51%**).
- **Gain: ZERO.** Sector still 81/96, node still 3/9, track still 1,425.
⇒ **Stars, not keycards, say whether a node is live.** `3/9` keycards on a 3/3-starred node does NOT mean
6 are still farmable there — the rest come from elsewhere (sector feats). **Read STARS before every fight.**
- ⚠️ This is an **automation gap**: `conquest_node_gold` matches the current front node *whether or not it
  is exhausted*, so the loop will happily re-fight a 3/3 node and then hang in `await_outcome` (it did this
  in S3 too). A future driver must OCR/marker-check the stars, or track cleared nodes itself.
- Boss outcome read as `timeout` from `await_outcome(700)` — neither `victory` nor `defeat*` matched, yet
  the map returned and stamina dropped. **Boss result screens are not covered by the current templates.**

### Deploy timing (why the first boss attempt never started)
The driver tapped BATTLE→BATTLE→AUTO and then sat in `await_outcome` on the **map** — the fight never
launched. The identical manual sequence with **longer pauses (3.0s node / 3.5s combat-details / 4.0s
deploy)** loaded the battle fine. The squad-screen deploy needs more settle time than `start_from_map`
allows; treat a post-deploy `on_map == True` as "deploy failed, retry", not "battle running".

## 2026-08-05 (session 5) — Sector 3 to 87/118: star-guarded driver, disks, and the bonus-battle trap
Continued session 4 the same evening. Sector 3 **34 → 87/118**, global track **1,425 → 1,685/3500**,
FEATS **1/4 → 3/4**, 18 battles fought (16 W / 1 L / 1 stall). Driver:
`~/Downloads/202608051859_conquest_grind.py` (supersedes the 1520 session script).

### ⭐ CORRECTION to session 4 — BOTH node templates are real
Session 4 concluded "`conquest_node_gold` is the live-front template — NOT `conquest_node_open`".
That was overfitted to one map state. Measured across six map states this session:
- **`conquest_node_open` = the CYAN ring node** · **`conquest_node_gold` = the AMBER ring node.**
- They are two node **stylings**, not a right/wrong pair. Amber is *not* an alignment lock — an amber
  node's Combat Details listed ordinary mixed relic-5 enemies and the Jedi squad cleared it.
- Match **both** every time and take the best (`find_all` + NMS, since `vision.find` returns only the
  single best match). Scores when correct: 0.963–0.992. A wrong-state score sits at 0.67–0.78.

### ⭐ THE STAR GUARD — how to know a node is spent BEFORE paying 20 energy
Session 4's "a 3/3 node pays nothing" is right, and here is the cheap programmatic check. Open the node
(free) and read the **STARS** row of Combat Details; **gold-pixel fraction** in box `(1340,295,1495,340)`:
- **0.000 → live** (3 dark stars) · **0.299 → spent** (3 filled gold stars). Threshold **0.05** separates them.
- ⚠️ A spent 3/3 node **still renders a green BATTLE button** — verified again on the S3 node we had just
  cleared. Nothing in the panel except the stars tells you it is dead.
- The map is no help: the node you are *standing on* is drawn as brightly as a live one, and a cleared
  node keeps its white ring (only the `x/3` label changes). Cyan chevrons = "you are here".

### ⭐ `no_node` IS NOT A FAILURE — it is a route decision
When neither ring template matches, the only ways forward are a **Data Disk Stockpile** or a **Wandering
Scavenger**. Both are irreversible: *"You will advance and be unable to select a different path."*
- **CANCEL is safe** — back out and open the other branch to compare, then commit. Did exactly this and
  the two branches offered completely different disk sets.
- The driver stops and says so rather than guessing; the route choice stays human.

### Data disks — tiers, and the capacity wall
- Disks come in **tiers by rarity colour: silver → green → blue**, and **deeper stockpiles offer stronger
  versions of the same disk**. *Guard and Penetrate*: silver = 100% Defense / 5 Def Pen; **blue = 300%
  Defense / 10 Def Pen**. Same name, triple the numbers — always read the values, not the title.
- Diamonds on the disk = its **Data Capacity cost** (1◆/2◆/3◆/4◆).
- ⚠️ **Capacity is 12/12 = FULL.** A newly collected disk therefore just banks in inventory; equipping it
  means unequipping something, and *"Conquest Pass+ makes swapping free"* implies swapping otherwise costs.
  Left the loadout alone — it is winning.
- **Equipped set includes `Booming Voice` (4◆): "when the unit in the Leader slot uses an ability, all
  other allies are called to assist."** That is the engine behind the 29–98s clears. Do not swap it out.
- Picked this session (all banked, unequipped): Guard and Penetrate (silver), Unshakable Focus (2◆),
  Guard and Penetrate (**blue**).

### ⭐ OPTIONAL BONUS BATTLE (cyan diamond node) — repeatable, but pays NOTHING material
*"You can repeatedly earn this node's rewards each time you win an optional battle here."* Measured a win
exactly: energy 14.0K→13.9K (−20) and **track 1,685 → 1,685, sector 77/118 → 77/118, purple 1,930 → 1,930.**
- ⇒ **No keycards, no track, no currency.** An unattended grinder pointed at it burns energy forever.
- ⇒ Its real use is **FEAT farming**: it is repeatable with no route commitment, so it is the ideal place
  to finish "win N battles" feats. Used it to close *Flawless Victory* (see below).
- **MULTI SIM** unlocks on that node after the first win (cost unidentified — not pressed).

### ⭐ PROGRESS MODEL (inferred from 8 clean deltas — the two counters are different things)
- **Global track (x/3500) = +20 per STANDARD battle victory.** Bonus battles award 0. So 3500 ≈ 175 wins;
  at 1,685 that is ~91 standard wins still to go.
- **Sector keycards (x/118) = node stars + sector-feat rewards.** Nothing else moves them.
- Confirms session 4's read that *Path of the Padawan* paid +10 sector keycards: the sector jumped +13 on
  a single win (3 stars + the 10-keycard feat) while the track moved only +20.

### Sector 3 feats — 3/4 done
- **Stunning Tactics** (Stun 50×) — ✓ (was 16/50 at session-4 close)
- **Path of the Padawan** — ✓ · **Flawless Victory** (win 20 without losing a unit) — ✓ **+10 keycards**
  (was 5/20 at session start, 18/20 when found; the last two came from repeatable bonus battles)
- **Maximum Output — "Gain Overcharge 20 times" 0/20** = the only one left. Nothing in normal play has
  ticked it in 18 battles ⇒ almost certainly needs the **"Overcharged …" consumables** the Wandering
  Scavengers sell (session 4 saw "Overcharged Critical Chance Booster" / "Overcharged Health Medpac").
  That is the lead to chase next session.

### Sector boss (S3)
10m timer (vs 5m normal), 5 relic-5 enemies flagged **BOSS / ELITE / ELITE**. Node reads **0/11 keycards**
but a 3-star win pays only **3** — the other 8 come from feats, same rule as any node.
⚠️ The boss was **not adjacent**: its panel had *no BATTLE button* until we committed past the Wandering
Scavenger sitting between us and it. A missing BATTLE button means "not reachable yet", not "bug".

### ~~⭐ STAMINA IS THE REAL LIMIT — not difficulty~~ ❌ **WRONG — see session 6**
> **Superseded 2026-08-05 (owner): stamina does NOT affect performance.** Everything below is a real
> observation with the wrong cause attached. The squad was not tiring — it was walking into deeper
> nodes with higher stat bonuses. Read it as a *difficulty* curve, not a stamina curve.

The Jedi squad went **100% → 11% in 8 battles** and then lost (245s, a genuine wipe inside the 300s timer).
Clear times degraded monotonically first: 29s → 85 → 98 → 111 → 125 → 129 → 136 → 142 → 149 → loss.
~~Rising clear time is the early warning; swap squads at ~40%.~~ Rising clear time is real, but it tracks
**how deep in the sector you are**, not the stamina bar. Energy is a non-constraint (13.9K ≈ 700 battles);
**squad power vs node difficulty, and route, are the only constraints.**

### Squads that worked (both ~200k, one GL + four allies, per the one-GL rule)
- **Jedi — Rey (L, Wisdom of the Sacred Texts) + Jedi Knight Revan + Jedi Knight Luke Skywalker +
  Ezra Bridger (Exile) + Grand Master Yoda = 200,398.** 8 wins, fastest 29s.
- **Rebels — Leia Organa (L) + Commander Luke Skywalker + Admiral Raddus + Cassian Andor (Undercover) +
  Ahsoka Tano (Fulcrum) = 201,215.** Killed the S3 boss and closed Flawless Victory.
- Squad-picker re-flow behaved exactly as session 4 documented: **three taps on the same cell (143,580)
  added three different units**. And the session-4 warning paid off — the Mon Calamari read as "Ackbar"
  from the portrait is actually **Admiral Raddus**. Always confirm by the name in the slot.
- Filter dialog: `SELECT FILTER` → checkbox grid; **GALACTIC LEGEND** (1295,223), **REBEL** (1295,575)
  after 3 scroll-swipes, **CONFIRM** (1496,957). Filter list order is category-then-alphabetical.
- Alignment: a "SELECT NEUTRAL SQUAD" node accepted Dark Side GLs (Jabba, SLKR) — the red ring is the
  unit's alignment, not a lock.

### ⭐ AUTO can silently never engage — and the fight then idles to the timeout
`ensure_auto` has a 45s window that starts right after the deploy tap. On a slow-loading battle neither
AUTO template matches during the load, ensure_auto gives up, and **the battle then sits on turn 1 forever**
— found one paused at 3:40 with `AUTO` off after a 466s "timeout". The battle timer does not run while it
waits for input, so this is invisible in the result.
**Fix applied:** `await_outcome` re-checks `auto_state()` every 5 polls (~15s) and re-taps AUTO if off.
That loop is the only one still running, so it is the right place for the self-heal.

### Other driver gotchas
- An open **Combat Details panel hides the feats bar**, so `on_map` (which keys off `conquest_feats_panel`)
  returns False while the panel is up. Gate on "feats panel OR combat details", not on `on_map` alone.
- The panel does **not** close by tapping map background — selecting another node replaces it.
- On the **bonus-battle** panel `conquest_battle_btn` fails to match: that layout adds a **MULTI SIM**
  button which narrows BATTLE. Tap **(1737,1000)** there instead of relying on the template.
- The map pans by 200–400px whenever a panel opens/closes. Every tap must be re-located from a fresh
  screenshot — never reuse coordinates across a panel round-trip.

### Purple currency — STILL not positively identified (unchanged from session 4)
Scavenger prices appear in **two** currencies: character shards at **525 / 475 keycards** *and* **600 purple**;
Techs at **150 purple**. Balance 1,930. It sits in the Conquest-only top bar and carries its own green "+"
(buy-more) affordance, which argues it is *not* crystals — but that is inference, not proof, so nothing was
bought. **Cheapest decisive test next session: note the hub's crystal balance and compare to 1,930.**

### Board state at close (12d 40m left)
S1 **81/96** (nodes exhausted — feat-only) · S2 **64/96** (unverified) · S3 **87/118** ·
track **1,685/3500** · FEATS S3 **3/4** · energy **13.9K/144** · purple **1,930** · difficulty **Hard**.
Leia squad ~45%, Jedi squad ~11%, JMK squad partially rested. Next step on the S3 map is the second
cyan bonus node / onward path; the sector's remaining keycards are mostly feat-locked behind *Maximum Output*.

## 2026-08-05 (session 6) — Sector 4 opened; the purple currency finally NAILED (it is crystals)
Continued the same evening, 21:20–23:00. Sector 4 **0 → 27/120**, track **1,685 → 1,870/3500**,
11 battles (9 W / 2 L). Two multi-session unknowns closed for good. Helper:
`~/Downloads/202608052125_cq_s4.py` (`deploy` = launch a hand-built squad from the SELECT SQUAD
screen, which the 1859 grind driver cannot do because it only starts from the map).

### ⭐⭐ THE PURPLE CURRENCY IS **CRYSTALS** — settled, do not spend it
Ran exactly the test session 4 proposed: read the **hub** currency bar and compare. The hub shows
`💎 1,930` — the identical balance to the Conquest top bar. Same icon, same number, same green "+".
⇒ Scavenger "75 purple", Shipments "40 purple", store "REFRESH 50" are all **crystal** prices. Off-limits.
- Session 4's counter-argument (the green "+" means it is *not* crystals) was backwards: the "+" **is**
  the buy-crystals affordance and appears next to crystals everywhere in the game.

### ⭐⭐ KEYCARDS ARE THE REWARD TRACK — SPENDING THEM COSTS PROGRESS (measured)
The other price tag is keycards, and the obvious worry was whether the shop deducts from the
`x/3500` track. Bought one **Overcharged Potency Booster (15 keycards)** to find out:
- **track 1,865 → 1,850.** Crystals unchanged at 1,930.
⇒ **The single keycard counter is both the reward track and the spendable balance.** Every purchase
is a direct, permanent subtraction from end-of-Conquest rewards. Price a purchase against the crate,
not against "spare currency" — there is no spare currency.
- Corollary: **Maximum Output is not worth buying into.** The feat pays +10 keycards; boosters cost 15
  each and one lasts a single battle. Chasing it with purchases is net-negative. Use only what is free.
- ⚠️ The bottom-bar `55 | 2` next to "Current Reward" is **not** a balance — it is the *contents preview*
  of the next crate. It never moved all session. Only the top bar is the balance.
- Scavenger stock is **one of each item per visit** — the row greys out with a ✓ after buying.

### Sector 4 feats — one squad farms two of them
**Hyper Rapture** (Breach ×50) · **For Mandalore** (win 10 with a full squad of **Light Side
Mandalorians**) · **Armor Up** (Defense Up ×80) · **Blinding Assault** (Blind ×80).
- ⭐ For Mandalore and Hyper Rapture are the **same squad**: Breach is the Mandalorian debuff, so the
  feat squad farms both at once. Measured **≈4.75 Breach per battle** (19/50 after 4 wins).
- Squad: **Bo-Katan (Mand'alor) L ("Way of the Mandalore") + The Mandalorian (Beskar Armor) + Paz Vizsla
  + The Mandalorian + Bo-Katan Kryze = 165,257**, the top 5 LS Mandalorians owned. Feat counted all
  4 wins ⇒ the tagging is right. **For Mandalore 4/10 · Hyper Rapture 19/50 at close.**
- Armor Up / Blinding Assault got **0** from this squad — they need different kits entirely.
- Other LS Mandalorians on the bench if the core five need rest: **Grogu** (yes, Mandalorian-tagged),
  Padawan Sabine, Canderous Ordo, Sabine Wren, The Armorer, IG-11. Maul/Jango/Gar Saxon are Dark Side —
  they are in the MANDALORIAN filter but would **break** the feat.

### ⭐ 165k IS NOT ENOUGH DEEPER IN THE SECTOR — and it is not a stamina problem
The Mandalorians cleared the first three S4 nodes (86–137s) then **wiped at 172s** on the node past the
first disk pile. Checked the deploy screen: **all five at 61%** — well above the 40% swap line. So the
wall was **difficulty**, not fatigue (stat bonuses rise deeper in the sector, as the sector info dialog says).
- Fix that worked: a **bigger squad**, not a rested one. **Sith Eternal Emperor L + Darth Revan +
  Darth Bane + Darth Malak + Rey (Dark Side Vision) = 216,219** took the same node first try and then
  ran 4 more (87–126s). **~200k is the working floor for Sector 4; 165k is not.**
- **Darth Bane** (relic 10, 100%) was the surprise — a top-power Sith that never came up in earlier planning.

### ⭐⭐ CORRECTION — **STAMINA DOES NOT AFFECT PERFORMANCE.** (owner, 2026-08-05)
This supersedes session 5's "⭐ STAMINA IS THE REAL LIMIT", session 4's stamina-based loss
explanations, and every "rotate/rest the squad" recommendation above. **A unit at 20% fights exactly
as well as the same unit at 100%.** Stamina is a *usage counter*, not a stat debuff.
- Every earlier stamina claim was **inferred, never measured** — and it was confounded: clear times rose
  as squads advanced, but squads advance into **deeper nodes with higher stat bonuses**. Difficulty was
  doing all the work the whole time. Session 4 had already half-seen this (a **fresh 176,280 Family squad
  at 100% lost**); tonight repeated it (the **Jabba squad at ~80–90% lost the node right after the boss**).
- ⇒ **There is no reason to stop a session, rest, or rotate for stamina.** Rotate only when a squad
  cannot beat a node. Run your **strongest** squad every time.
- ⇒ The only real budget is **energy** (13.7K ≈ 685 battles) and **squad power vs node difficulty**.
- Burn rate, for reference only (it costs nothing): ~8–9.6%/battle. Regen is passive and currently
  "Regeneration Boosted". Ignore it when planning.

### ⭐⭐ STARS = DEATHS. 0 deaths → 3★ · 1 death → 2★ · 2+ deaths → 1★ (owner, 2026-08-05)
The star count on a node win is set **purely by how many of your units died**, nothing else.
- Confirmed both ways tonight: the S4 boss win where **4 hunters died** paid exactly **1★** (sector
  26 → 27/120), and the map's stray **2/3** node is a win that cost exactly one unit.
- **The track pays a flat +20 for any win regardless of stars** — so deaths cost *sector keycards only*.
  Sector completion (x/120) is therefore a **survival** problem, not a win-count problem.
- This is also the mechanic behind session 5's *Flawless Victory* ("a win that loses any unit does NOT
  count"): flawless == 3★ == zero deaths. Same rule, different wrapper.
- ⚠️ **A 1★ or 2★ node is STILL LIVE** and can be re-fought for the missing stars. It is often the
  *easiest* live node on the map, because it sits behind you where stat bonuses are lower.
- 🐞 **Driver bug this creates:** `stars_filled()` flags a node spent on *any* gold in the star row
  (threshold 0.05, measured 0.299 for 3★). A 2★ node reads ~0.2 ⇒ the loop **skips live nodes**.
  It must count the gold stars, not detect them — only **3/3** is exhausted.

### ⭐ Squad picker — the re-flow rule has an exception that eats taps
Session 4's "tap the same cell N times" works **only if nothing unavailable is pinned above it**.
Added units *are* removed from the list and everything shifts up, **but a dimmed/unusable unit stays**
at its index and silently swallows every tap. Five taps on `(143,580)` under the SITH filter added
**one** unit for exactly this reason. **Verify the slot after every tap** — that is still the only safe rule.
- Two-filter build for a GL + off-faction crew: filter **GALACTIC LEGEND** → add the GL (becomes leader) →
  reopen the filter, uncheck it, check the crew faction → add 4. The filter resets to ALL on CLEAR SQUAD.
- Filter row geometry (1920×1080): checkbox columns **x = 143 / 717 / 1295**, rows start **y = 223**,
  step **≈114**; CONFIRM **(1496,957)**. SITH is 5 swipes down at **(1295,626)**; MANDALORIAN 2 swipes at
  **(717,707)**; BOUNTY HUNTER is on the **first** page at **(143,792)**.
- Tapping a **filled** squad slot removes that unit and makes the slot active (used to drop a 36% unit).

### Sector 4 boss — Light Side Mandalorians, and it is star-cheap if you lose units
**Bo-Katan Kryze (BOSS) + Grogu (ELITE) + The Mandalorian Beskar (ELITE) + 2 Mandalorians**, all relic 5,
**10m** timer, node reads 0/9 keycards. Gated behind the Wandering Scavenger — **no BATTLE button until
you COMMIT past it** (re-confirms session 5).
- Beaten by **Jabba the Hutt L + Bossk + Embo + Boba Fett + Krrsantan = 193,010** (all 100%), but only
  just: all four hunters died and **Jabba soloed Bo-Katan**. ⇒ **1 star, not 3** — sector 26 → **27/120**
  (+1) while the track still paid the full **+20**.
- ⭐ **Stars scale with units surviving.** A 1/3 boss stays live and can be re-fought for the other two.
- ⚠️ **`await_outcome`'s 400s default is shorter than a 10m boss.** It returned `timeout` while the fight
  was still visibly running at 2:59 remaining. That is what session 4 misread as "boss result screens are
  not covered by the templates" — the templates are fine, **the poll window is too short**. Use ≥700s
  for any 10m node.

### Navigation — how to get back into Conquest from the hub (cost 8 taps to rediscover)
Conquest is **not** under Events → Solo Events. From the hub, swipe the cantina **right to the far end**
to the table labelled **"Galactic Battles"** (shows `Hard - SECTOR n`), tap it → **SELECT A GALACTIC
BATTLE** → **CONQUEST / ENTER** → sector list → scroll → ENTER. A free daily-calendar popup may
intercept the home tap; claiming it is free and harmless.

### Consumables — all 1-battle, and we already own 3 Overcharge items
Inventory → CONSUMABLES: 8 stacks, e.g. *Critical D.O.T. Tech* "**Max Duration: 1 battle**".
⚠️ Tapping any of them opens a **Use Consumable → CONFIRM** dialog — it is one tap from being spent.
- Owned Overcharge items (free, no purchase needed): **2× Overcharged Protection Medpac + 1× Overcharged
  Potency Booster** (+150% Potency, +20 Speed). These are the only free shot at Sector 3's *Maximum Output*
  ("gain Overcharge 20 times") — test one in the S3 **repeatable bonus battle** and read the feat delta
  before deciding it is reachable at all. Given the buy-in maths above, if it needs more than 3, drop it.

### Data disk taken (only one path offered, so no branch to compare)
Stockpile offered Certain Defeat (silver), Shocking Exhaust (silver), **Unshakable Focus (2◆)** — took
Unshakable Focus (we already owned 1; it turns our Breach spam into stacking Potency **and** unevadable
−3% enemy turn meter). Capacity is still **12/12**, so it banked unequipped; the winning loadout
(**Booming Voice 4◆ / Unstable Decelerator / Certain Defeat blue**) was left alone.
- ⭐ **Rarity is the border colour, and the same disk exists at several tiers.** The equipped *Certain
  Defeat* is the **blue** version (Healing Immunity + Protection Disruption, 2 turns, unresistable); the
  stockpile was offering the **silver** one (Protection Disruption, 1 turn). Read the text, not the name.

### Board state at close (11d 21h left)
S1 **81/96** · S2 **64/96** (still unverified) · S3 **87/118** · S4 **27/120** ·
track **1,870/3500** · EVENT FEATS **2/9** · S4 feats **0/4** (For Mandalore 4/10, Hyper Rapture 19/50) ·
energy **13.7K/144** · crystals **1,930** (never spend) · difficulty **Hard**.
Stamina at close (recorded for completeness only — it does not affect performance): Mandalorians 61%,
Sith 26–51%, Jabba/Bounty Hunters ~80%.
Next, in order — **no waiting required, stamina is irrelevant**: (1) Mandalorians → 6 more S4 wins to
close **For Mandalore +10**, taking the **2★ node behind us** first since it is live and the easiest
thing on the map; (2) re-fight the **S4 boss** for its missing 2★ with a squad that can win *without
losing anyone*; (3) free Overcharge test in S3's bonus battle.
⇒ Standing strategy from here: **survival, not throughput.** Send the strongest squad, every time,
and treat a unit death as the real cost — it is worth re-running a node cleanly for the extra 2★.

## 2026-08-06 (session 7) — FEATS, researched properly: EVENT 9/9 closed, S1 4/4, S2 to 3/4
Owner asked for research first, then execution. The research changed almost every open question, so
read this section before touching Conquest feats again.

### ⭐ THE SOURCE: kahzgul's guide is written for THIS conquest
`kahzgul.substack.com/p/conquest-feats-and-team-building-4f9` — "Conquest Feats and Team Building:
**Jedi Training Leia**" is Conquest 24 exactly. Its global list matches the live EVENT feats
one-for-one (Challenge Path 250 · Purge 300 · Offense Up 500 · Rebel Fighter 50 · Undermine 50 ·
Booming Voice 60 · Vel 20 · DCS · Family United). Every sector feat matches too. It gives 2–4
candidate squads per feat. **Astra's roster can field every single one of them** — checked unit by unit.
- ⚠️ It is not infallible: it claims `Tarkin / Scorch / Scout / DTMG / DCT` "doubles with no attackers",
  but **Death Trooper, Dark Trooper, Night Trooper and Death Trooper (Peridea) are ALL role=Attacker**.
  Verify roles before trusting a "no Attackers" recommendation.

### ⭐ ROLE/ALIGNMENT DATA IS ALREADY IN THE REPO — do not re-scrape
`data/meta/raw_unit_categories_20260805.json` → `["map"][BASE_ID] = {n, role, align, cats}` for 340
units. swgoh.gg **403s a plain curl** (Cloudflare), and the notes' "same-origin fetch from a loaded
page" trick needs the MCP browser. The cached file answers role questions instantly. Use it.

### ⭐⭐ STAMINA: the 2026-08-05 correction was half right, and the wrong half costs battles
"Stamina does not affect performance" is TRUE for stats. But **at 0% the unit cannot be fielded at
all** — the picker throws a modal: *"Unit stamina exhausted — Stamina for this unit is depleted.
Stamina recovers over time or by using a Stim Pack."* Jabba hit 0 mid-batch and the driver then sat
in `await_outcome` until it reported a bogus `timeout` (the fight never launched).
- Burn measured again this session: **~9–10%/battle**, i.e. ~10 battles per unit from 100%.
- ⇒ **Rotate deliberately.** Before a batch of N battles, every member needs ≳ 10·N percent.
  Read the stamina bars off the squad screenshot and swap anything short — it is far cheaper than
  discovering it at battle 3. Astra has 397 units; there is always a fresh alternative.

### ⭐⭐ FEAT COUNTERS TICK ON A LOSS
Measured on a lost S5 bonus battle: Tactical Supremacy 0→2, Potency Up 17→18. Only **"win N battles"**
feats need a win. So a "gain/attempt X times" feat is farmable even in a sector that outguns you —
it is just slower (a loss burns the full 5m timer, a win takes 40–200s).

### ⭐⭐ SECTOR FEATS ONLY COUNT INSIDE THEIR SECTOR — event feats count anywhere
⇒ **Farm event feats in Sector 1.** Its enemies are relic 4, the lowest stat bonuses in the run, and
it has **three repeatable cyan bonus nodes** in a row (map x≈707/890/1071, y≈575). A 190k squad clears
them in 37–120s. That is the cheapest battle in the whole Conquest.

### ⭐ MAXIMUM OUTPUT IS FREE — the "buy Overcharge consumables" theory was wrong
Session 6 concluded the S3 feat needed purchased boosters and was therefore net-negative. Wrong.
**KX Security Droid and STAP are the only units in the game that GAIN Overcharge**, and KX's is
self-contained — no Empire/ISB requirement:
- his **basic** grants a stack (max 5), **being critically hit** grants one (Controlled Operation),
  and **every out-of-turn assist** grants one (assists use the basic).
- ⇒ the equipped **Booming Voice 4◆ disk** (leader ability → all allies assist) is an Overcharge engine.
- ⇒ put KX in whatever squad is strong enough for the sector; do NOT field the weak 144k ISB five for it.

### ⭐ THE THREE "ONLY UNIT IN THE GAME" FACTS
- **Buff Disruption** (S5 *Deactivate*): **Stormtrooper Luke only**, via his BASIC "TK-421", and only
  **on his own turn** — assists do not count. If he dies early or never basics, the feat gets zero
  (measured: a whole lost battle with him on the field produced 0/30).
- **Tactical Supremacy** (S5 *The Upper Hand*): **Admiral Trench, Grand Moff Tarkin, Major Partagaz** only.
  Tarkin's *Intimidation Tactics* grants it to **Empire allies**, so the count scales with Empire bodies.
- **Overcharge** (S3 *Maximum Output*): KX Security Droid, STAP.

### ⭐ "NO ATTACKERS" HAS NO DAMAGE — carry it with a non-Attacker GALACTIC LEGEND
S2's *Disarmed* squads kept timing out at the 5m mark (162k: two straight timeouts, 296s and 331s) for
the obvious reason — the feat deletes the damage role. The fix is that **4 of the 9 GLs are not
Attackers**: **Jabba the Hutt = Support**, **JML / Leia Organa / Ahsoka Tano = Tank**. Dropping one in
turned 0-for-2 into **6-for-6** (153–225s).
- Working S2 squad: **Ahsoka Tano (L) · Grand Moff Tarkin · Dark Trooper Moff Gideon · Scout Trooper ·
  RC-1262 "Scorch"** ≈ 184k — Tarkin's 3rd is AoE Crit Chance Down and the squad also Exposes, so it
  closed *Get a Chance* (100) and *Detrimental Reveal* (20) while banking *Disarmed* wins.
- Rotation squad once Tarkin's job was done: Ahsoka · Baylan Skoll · Satele Shan · General Kenobi ·
  Admiral Raddus ≈ 206k, still zero Attackers.

### Squad-builder driver — `~/Downloads/202608061854_cq_feats.py`
`build([names])` drives the picker tap-by-tap (nothing else in the stack can build a squad, and
Conquest's SELECT SQUAD is the GAC preset manager, which cannot apply to Conquest). Two bugs found live:
- **Clear the search box with 40 backspaces, not 18** — "Dark Trooper Moff Gideon" is 24 chars, so a
  short clear leaves a prefix and the next search silently matches nothing. The failure looks like
  "that unit is unusable" (empty grid + *"None of the units in this filter can be used"*), not like a typo.
- **Quote the typed text** — adb joins argv into a device-side shell command, so "Ezra Bridger (Exile)"
  dies with `syntax error: unexpected '('`.
- `build()` never claims success; it saves the finished squad screen for a read-back. Keep it that way —
  the grid re-flows and dimmed units swallow taps.

### Results this session
- **EVENT FEATS 7/9 → 9/9 ✓** (+30 keycards). *Imperial Inquisition* (Purge 300) closed in ONE battle
  with **Grand Inquisitor (L) · Seventh Sister · Fifth Brother · Ninth Sister · Second Sister** (161k)
  on the S1 bonus node. *That'll Leave a Mark* (Offense Up 500) closed in four with **JML (L) · Shaak Ti ·
  GMY · Hermit Yoda · Kelleran Beq** (190k) — Shaak Ti's basic grants Offense Up to the whole team.
  ⚠️ Yield scales with battle LENGTH, not wins: a 37s win paid +8, an 85–117s win paid ~15.
- **SECTOR 1 4/4 ✓** (was already closed earlier in the day).
- **SECTOR 2**: *Get a Chance* ✓ · *Detrimental Reveal* ✓ · *Remnant War Machine* ✓ · *Disarmed* 6/10.

## 2026-08-08 (morning) — RED CRATE SECURED at 621→631/630. Conquest 24 done.
Opened at 621/630 with 9 keycards needed and 9d 11h left. Closed it with **S4 "Armor Up"** (+10).
`Max Crate Reward Achieved` — Hard-07 crate ships to the inbox at event end. Nothing else is required
for this Conquest; remaining keycards are surplus.

### ⭐⭐ THE DECIDING FACT: feats count BUFF GAINS, not wins
*Armor Up* = **"Gain Defense Up 80 times"** (the name is a red herring — it is plain **Defense Up**).
**Dark Trooper Moff Gideon is the engine**: his special grants Defense Up to **all allies**, so one cast
= up to 5 counts. 51 → 80 in 8 battles.
- **A LOST battle still pays** if the granter casts before dying — the feat closed on a *loss*. Do not
  abandon a farm because the squad is losing; abandon it only if the granter dies early.
- Per-battle yield tracked: 91s win **+7**, then ~+3–4/battle as stamina fell. Longer battle = more casts.
- Last night's "Separatist squad → zero Defense Up" was a squad-composition miss, not a broken feat.

### ⭐ SECTOR-FEAT REWARDS ARE THE CHEAPEST KEYCARDS LEFT — bosses are the most expensive
Rewards measured: **S3 10 · S4 10 · S5 15** per sector feat. Compare with boss nodes, which are
feat-gated behind a FORCED weak squad and were all dead ends:
- **S1 boss:** stars already 3/3, so its last 3 keycards are the ISB feat only. The full ISB five
  (**144,156**, all 100% stamina, Partagaz/Dedra/Krennic/Probe/KX) **LOST in 75s to relic-4 enemies.**
  Boss nodes carry huge stat multipliers — relic tier alone does not predict difficulty. Abandoned.
- **S4 boss** 6/11 (Bad Batch feat) and **S2 mini-boss** 4/7 likewise composition-locked.
⇒ When hunting keycards, read the FEATS panel per sector FIRST; only fall back to node stars.

### ⭐ "Deactivate" (S5, 15 kc) IS NOT AUTO-FARMABLE — confirmed, stop trying
A full **109s** battle with Stormtrooper Luke alive on the field moved it **1/30 → 1/30 (zero)**.
On AUTO the AI never chooses his basic, and only his basic on his own turn counts. Closing this needs
manual per-turn tapping; it is not worth it. The 15 kc is effectively locked.

### Sub-3-star node inventory (survives this Conquest, for reference)
S1 92/96 · S2 92/96 · S3 116/118 · S4 → 114/120 · S5 125/142. Everything left sits on: the S5 gold
**Challenge node 1/3** (won it, still 1/3 — the 2nd/3rd stars need conditions a 205k squad missed),
the three boss nodes, and S5 *Deactivate*.

### ⚠️ THREE DRIVER BUGS FOUND LIVE — fix before the next run
1. **The FIRST search on the squad screen is swallowed.** Twice: Partagaz silently absent, squad power
   byte-identical (115,583) across two builds. He was at **100% stamina and perfectly usable** — the
   tap never landed. **Fix: burn one throwaway `search()` before `build()`.** Worked every time after.
2. **`open_node()`'s blind fallback tap `(1737,1000)` is dangerous.** On the sector MAP those coords are
   the **INVENTORY** button, so a mistimed node tap silently opens Data Disks instead of the fight
   (hit twice). Verify the node panel is up before pressing BATTLE; never blind-tap.
3. **`m.sector(idx)` drifts** — asked for 4, landed on 3, twice (it counts down-swipes from the top).
   **Fix: scroll to a rail.** Hard UP for 1–2 (y=432/785), hard DOWN for 3–5 (y=278/630/983).
   `~/Downloads/202608080938_goto.py` implements this and was reliable.

### Bonus nodes are the right farm surface
Cyan node = **"Optional Bonus Battle"** — *"You can repeatedly earn this node's rewards each time you
win"*. Its panel is NOT `conquest_combat_details` (template does not match) and its **BATTLE sits at
(1740,1000)** next to a **MULTI SIM**. Avoid MULTI SIM for feat farming: it awards rewards without
playing the battle, so it generates no buff events. S4's bonus node (relic-5 enemies, 5m, 20 energy,
map x≈705,y≈575 at the sector's right end) carried the whole Armor Up grind.

### Stamina is the real budget, and it is visible on the squad screen
Read the % under each portrait before every deploy — it explains losses better than squad power does.
- **Lord Vader 51% → 12%** over 5 battles; the 12% deploy lost. Empire five won 4/5 while ≥40%.
- Swapping the burnt leader for a fresh off-faction GL **made it worse**: Jabba (100%) leading the
  Empire four (60%) **lost** — losing Vader's *My New Empire* cost more than the stamina gained.
  ⇒ **Replace a burnt leader with a fresh leader of the SAME faction**, not with the biggest GP.
  Fix that worked: **Emperor Palpatine (L) · DTMG · Piett · Mara Jade · Thrawn** (159,193, four at 100%).
- Ambiguous picker names to avoid: "Darth Vader" also matches "(Duel's End)"; "Leia Organa"/"Ahsoka
  Tano"/"Rey" all collide. Search a unique token — "Palpatine", "Piett", "Thrawn", "Jabba".

### Scripts added (all `~/Downloads/`)
`202608080917_peek.py` (open a node read-only, no BATTLE) · `202608080932_look.py` (search one unit,
screenshot the grid — diagnoses swallowed adds) · `202608080938_goto.py` (rail-scroll sector entry) ·
`202608081030_safelap.py` (verified node→squad, no blind fallback) · `202608081100_run.py` (fight-N-laps
on a bonus node, keeps going through losses).

## 2026-08-08 (afternoon) — ⭐ BOTH ARENAS OPTIMISED LIVE: Fleet #6→#1, Squad #10→#6
Owner asked to optimise the roster for Arena → GAC → RotE, no crystals, and authorised arena
auto-battle (a deliberate reversal of the standing PvP-battle rail). **Crystals 5,795 UNCHANGED
throughout.** Two workflows ran (6-topic research + 3-module build); the game itself refuted one
recommendation both of them made.

### ⭐⭐ NEW HARD GAME RULE: ONE **LARGE UNIT** PER SQUAD
Adding Jabba next to Rotta pops **`Large Unit Limit` — "Your squad already contains the maximum
number of large units."** So the obvious "best Hutt Cartel five" (Rotta + Jabba + three bodies) is
**illegal**, and both the research agent and a naive power-ranked pick proposed exactly that squad.
- This is a SECOND squad-legality rule alongside the one-Galactic-Legend limit. Encoded as
  `arena_board.LARGE_UNITS` / `MAX_LARGE_UNITS`.
- **No data source has a size flag** — not HotUtils `gamedata/units` (affiliation/role/profession/
  species/omicron only), not swgoh.gg. The set is hand-kept and holds ONLY what the client has
  actually rejected. Add a unit when the game refuses it, never because it "looks big".

### ⭐ `RACCOON` IS **ROTTA THE HUTT** — and he is this shard's arena meta
Not a Guardians crossover. Hutt Cartel Attacker/Leader, released 30 Jun 2026. His zeta lead
**"A Legacy Reforged"** gives Hutt Cartel allies +50 Speed, 200% Defense, 75% Offense, 50%
Accuracy/Crit Avoidance, 40% Tenacity — a **base ability**, so it loses nothing in Squad Arena.
Ranks **1, 2, 3, 5, 9 and Astra all lead Rotta**. His *Grand-Arena-gated* clauses (Defense Pen
stacking, the all-Hutt-Cartel +50% Health start) do go dark in arena.

### ⭐ OMICRONS DO **NOT** FIRE IN SQUAD ARENA — datacrons DO
CG's 2026-04-27 Community Update says it outright ("Omicrons will not be present (similar to current
Squad Arena)"). Confirmed independently from `gamedata/units`: every omicron carries mode
7/8/9/11/14/15 and **no mode maps to Squad Arena**.
⇒ **GAC Hold% is not a valid arena estimator for omicron-dependent squads.** The #1 GAC wall
(Stranger/Luminara/Maul/Starkiller/Visas, 57%) carries 9–10 applied omicrons and is a BAD arena
defense. `arena_board.py` REPORTS this rather than applying a haircut (magnitude unmeasured) — so its
printed #1 defense is still the Stranger wall. **Read the docstring caveat before trusting that line.**
Datacrons DO apply (L3/6/9), and Astra owns a **set-33 FOCUSED Rotta datacron** — a live, arena-legal
buff on exactly the squad the shard says to run.

### Squad Arena — rebuilt the bodies, kept the leader (#10 → #6)
The old five were the *cheapest* Hutt Cartel bodies. Same leader, best legal bodies:
| | old (141,055) | new (176,402) |
|---|---|---|
|L| Rotta R10 z4 | Rotta R10 z4 |
| | Mob Enforcer R5 | **Embo R8 z2** |
| | Greedo R6 | **Boba Fett R8** |
| | Gamorrean Guard R5 | **Krrsantan R8** |
| | Cad Bane R5 | **Boushh R8** |
**+35,347 power (+25%), zero resources spent.** Beat #6 Helena (176,354) first try.
- ⚠️ **Squad Arena defense = the squad you LAST ATTACKED WITH.** There is no defense-setting screen.
  So the last battle before payout must be fought with the squad you want parked.
- **Squad Arena pays NO crystals** (removed 2021) and CG has announced it is being **retired** for
  Era Arena. Rank 10→1 ≈ +200 tokens +10K credits/day. **Do not make roster investments for it.**

### ⭐ FLEET ARENA #6 → #1 — a clean natural experiment, and the old advice was WRONG
Same opponent (#1 VERSO, 587,691), both on AUTO, minutes apart:
| reinforcements | power | result |
|---|---|---|
| Mark VI · Sith Fighter · TIE Advanced · Hound's Tooth | 621,738 | **DEFEAT** |
| **Scimitar · TIE Defender · Scythe · Imperial TIE Bomber** | 596,465 | **VICTORY** |
Won with **25,273 LESS power**. Fleet Arena defense is also "last squad attacked with" and is always
AI-run, so this lineup is now parked at rank 1.
- **The 2026-08-05 note's fix was incomplete and is superseded.** Removing Sith Fighter alone does
  nothing — **Mark VI Interceptor also outranks Scimitar** on the AI's reinforcement priority
  (measured 3.6% → 3.4% hold, indistinguishable). BOTH must go. Full fix = Scimitar + bottom-tier
  fillers only: **29.8% hold vs 3.2–3.6%** on the repo's own 51,367-battle counter data.
- **DELETE the old "Sith Fighter holds slot 1 95% of the time" claim** — artifact of a bad
  attacker/defender split; recomputed it is 67%/29%. And swgoh.gg counter-panel slot order is a
  **canonical display sort, not call order**, so no slot analysis can measure ordering at all.
- The "hold Mark VI until after Sabotage the Hangars" *reason* was also wrong (Leviathan's +10
  Devouring Swarm is unconditional). Real reason: the ENEMY's Sabotage the Hangars destroys the next
  reinforcement on deployment. Conclusion survives, mechanism didn't.
- Cost, stated: the three fillers are not Sith, so they forfeit Leviathan's Reinforcement Bonus.
- `build_fleets.FLEET_LINEUPS["Leviathan Arena"]` updated.
- **Base-ID mislabels corrected:** `SITHBOMBER` = **B-28 Extinction-class Bomber**,
  `SITHSUPREMACYCLASS` = **Mark VI Interceptor**, `SITHINFILTRATOR` = **Scimitar**. The starters were
  already the correct meta trio; earlier prose calling them "Sith Bomber"/"Sith Supremacy Class" was
  reading base IDs as names.

### ⭐ HotUtils `gamedata/units` — the browser-free unit catalogue (replaces a Cloudflare dependency)
POST `gamedata/units {sessionId}` → **410 units** with `affiliation` / `role` / `profession` /
`species` / `zeta` / `omicron` / `galacticLegend` / `hasLeaderAbility`. This is the swgoh.gg
`/api/characters/?format=json` data **without the browser**.
- **Omicron `mode` map, derived empirically** by cross-referencing applied omicrons against the
  per-unit counters in `account/data/all`: **7 = Territory Battle · 8 = Territory War · 9 = Grand
  Arena · 11 = Conquest**; 14 and 15 also book to `gacOmiCount` (GAC-family sub-modes, exact meaning
  unverified); mode 4 seen on 3 units, unmapped. **No mode = Squad Arena.**
- `account/data/all` → `data.units.units[]` also carries `power.total`, `relicLevel` (**already the
  DISPLAYED level — not the comlink `rt`, no −2 offset**), `gear.level`, `zetaCount`, `omiCount`,
  and per-mode `twOmiCount`/`gacOmiCount`/`tbOmiCount`/`cqOmiCount`. Best single source for
  investment planning.
- `data.datacrons` lists OWNED datacrons with `setId`/`templateId`/`focused`. Astra: 3× set31,
  2× set32, **7× set33 including `datacron_set_33_focused_raccoon`**. Set 30 gone (expired 8/6).
- `summary` has `squadRank`, `shipRank`, `leagueId`, `divisionId`, `skillRating`, `guildRank`.

### Gotchas learned this session
- ⚠️ **`account/refresh` KICKS THE GAME CLIENT** → the device shows `CONNECTION LOST / Your session
  has expired`. Harmless, tap RELOAD — but do the HotUtils pull BEFORE device work, not during.
- ⚠️ **swgoh.gg now Cloudflare-challenges same-origin `fetch()` too.** The 2026-08-05 recipe
  ("fetch from an already-loaded page, only top-level navigations are challenged") is **dead**:
  param URLs return 403 `Just a moment...` via fetch AND via navigation, landing on a Turnstile
  "Verify you are human" checkbox that needs a real human tap. Plan around it — HotUtils
  `gamedata/units` covers faction/role/omicron, and `gac/list` covers season state.
- **No GAC season is active** (`gac/list` → `tournaments: []`) and **S82 is unpublished**, so the
  98-definition board from 2026-08-05 is still built on the current data. No rebuild was needed.
- Arena post-battle **cooldown is ~5 min with a 💎50 skip** — never tap it; verify the button reads
  `BATTLE (n)` before pressing. Same verify-before-tap discipline as the farmbot's energy_out.
- Tapping a filled squad/fleet slot REMOVES that unit (slots do not compact); the left panel is the
  picker. The filter dialog has a **TEXT SEARCH** box — far faster than scrolling 397 units. The
  soft keyboard covers CONFIRM: `input keyevent 4` to dismiss it first.
- ⚠️ Search matches loosely: "Krrsantan" silently added **Doctor Aphra**. Verify the squad's power
  total against the expected sum after every add — arithmetic catches the wrong unit instantly.
- Tapping through an ARENA REPORT can fall through onto an opponent row and open **SEND ALLY
  REQUEST?** — answer NO.

### New scripts (PR pending)
`scripts/arena_board.py` (Squad Arena defense + climb; shard-grounded, 3 scoring bases) ·
`scripts/rote_ops.py` (RotE Operations assignment ILP + readiness gaps) ·
`scripts/invest_plan.py` (one priority ladder → relic/gear/ability queues + Grandivory mod order).
Suite **275 green**. `data/arena/shard_20260808.json` = the first real ladder capture.

### RotE readiness measured (2026-08-08) — relics are NOT the bottleneck, the QUOTA is
From `account/data/all` (`relicLevel` is already the DISPLAYED level here):
character relic spread **0:12 · 4:4 · 5:46 · 6:35 · 7:150 · 8:55 · 9:9 · 10:17**.
- **266 characters are already Relic 6+**, i.e. eligible for Operations slots. 46 sit at R5, one tier short.
- **67 of 69 ships are 7★**; only **Raven's Claw 6★** and **MG-100 SF-17 5★** are blocked from ship Operations.
⇒ With 266 eligible bodies against a **quota of 10 assigned units per player per operation area**, blanket
relic-farming "for RotE" is wasted. The binding constraint is the quota and the fact that each slot names a
SPECIFIC unit. Only relic a unit when a live Operation slot names it and Astra misses the gate — which needs
the board open. `rote_ops.readiness_gaps()` answers exactly that once `data/rote/operations_<phase>.json`
is captured. Guild Event (RotE) was still ~1h from opening at the end of this session, so no capture exists yet.

## 2026-08-08 (evening) — ⭐⭐ THE FOCUSED DATACRON *IS* THE ARENA SQUAD (owner caught this)
Ran the mod optimiser. Owner stopped the apply with one question — "have you taken the Datacron into
account?" — and the answer was no. That question overturned the afternoon's arena rebuild.

### The datacron names its five units, one per affix tier
`datacron_set_33_focused_raccoon` (owned, equipped, expires **2026-10-29**) has FIVE ability affixes and
each `targetRule` names a specific character:
| tier | targetRule | ability granted |
|---|---|---|
| 1 | `target_datacron_gamorreanguard` | `datacron_character_gamorreanguard_002` |
| 2 | `target_datacron_humanthug` (Mob Enforcer) | `datacron_character_mobenforcer_001` |
| 3 | `target_datacron_greedo` | `datacron_character_generic_015` |
| 4 | `target_datacron_cadbane` | `datacron_character_generic_003` |
| 5 | `target_datacron_raccoon` (Rotta) | `datacron_character_raccoon_001` |
**That is exactly Rotta + Mob Enforcer + Greedo + Gamorrean Guard + Cad Bane.** The squad this account
was already running was never "the cheapest bodies" — it is the datacron's designated five, and every
member draws a bespoke ability. The other affixes (statType 49/17/55/16, `targetRule: ""`) are generic
and apply regardless.
- ⚠️ **I swapped four of them out for Embo/Boba Fett/Krrsantan/Boushh on a raw-power argument**
  (141,055 → 176,402, +25%) and it did win rank 10→6. It also **discarded 4 of the 5 datacron abilities.**
  REVERTED. Power is the wrong metric when a focused datacron is in play.
- **Ladder corroboration:** rank 2 runs this same five at **154,890** and rank 5 at **135,821** — both
  BELOW the 176,402 power build, both ranked ABOVE it.
- ⇒ **Read `account/data/all` → `datacrons[].affix[].targetRule` BEFORE proposing any squad.** A focused
  datacron keys off named characters; no faction/role/power heuristic can see it. This is the second time
  focused datacrons have blindsided this repo (see 2026-08-05 addendum on Luminara).
- Relic investment in Mob Enforcer / Greedo / Gamorrean Guard / Cad Bane is **rented** — it expires with
  the cron on 2026-10-29.
- Also learned: **a LOST arena battle still sets your defence squad** (rank held at #6, power read back
  as 141,055 after a defeat).

### ⭐ Ships take no mods — rank the CREW (invest_plan bug, fixed)
Fleet Arena is the only arena that still pays crystals, yet `invest_plan.py` was ranking SHIPS, and every
downstream queue filters to `ct==1` and silently dropped them. **Darth Revan — who *is* the Leviathan —
sorted 89th in the mod order.** Fixed: `data/ship_crew.json` (generated from `gamedata/units`, where
characters carry `shipBaseId`/`shipSlot`) + `invest_plan.load_ship_crew()`; fleet rungs now yield the ship
AND its crew. Darth Revan 89th → **11th**. Arena-fleet crew = Darth Revan, Darth Malgus, Sith Marauder,
Sith Trooper, Darth Maul, Iden Versio, Grand Inquisitor, Fifth Brother.

### Grandivory: measured, and the ordering is worth ~0.5% of set value
Three runs on identical mods/fetch, only the selection ORDER differing:
| order | set-value change | mods | credits |
|---|---|---|---|
| arena-first, wrong five, no crew | **−0.42%** | 1,447 | 7.30M |
| GL-first | **+0.12%** | 1,394 | 6.90M |
| corrected: datacron five → climb → fleet crew → GAC | **−0.06%** | 1,473 | 7.44M |
- **There is almost nothing left to gain globally** — the +5.04% run on 2026-07-31 already captured it, and
  the best any ordering now finds is +0.12%. Treat the optimiser as a REDISTRIBUTION tool, not a gains tool.
- Putting four R5/R6 bodies above nine GLs costs ~0.5% of global set value. At −0.06% the corrected order
  is inside the noise, so priority alignment is effectively free; at −0.42% it was not.

### Driving Grandivory head-lessly (hard-won)
- GI is embedded in an iframe on `hotutils.com/mods/optimizer`; open it standalone via the iframe `src`
  (carries `SessionID` + `allyCode` + `NoPull`).
- State lives in **IndexedDB `ModsOptimizer` → `profiles[0]`**: `selectedCharacters` is an ORDERED
  `[{id, target}]` array. Reordering it and RELOADING is a safe way to set priority — it permutes existing
  entries and preserves each character's optimisation target. `localStorage` holds only UI state.
- ⚠️ **Synthetic MouseEvents do not work on GI** (React 16 + react-dnd): dispatching click/dblclick/drag on
  a character card does nothing, and the MCP `drag` tool fails too. But **`element.click()` on a real
  `<input>` DOES work** (that is how `lock-unselected` got toggled). Buttons respond to `.click()`; character
  cards only respond to genuine HTML5 drag-and-drop, so **adding a character to the selection could not be
  automated** — Rotta had to be left out (he is locked instead, so nothing is lost).
- ⚠️ **`lockUnselectedCharacters` defaulted to FALSE.** With it off, an optimise can STRIP mods from an
  unselected character and give them away — Rotta was unselected, so the arena leader's mods were at risk.
  Turned ON. Check `profiles[0].globalSettings` before every run.
- ⚠️ **`account/refresh` kicks the live game client** (`CONNECTION LOST → RELOAD`), and it killed the app
  outright once. Do all HotUtils refreshes BEFORE device work, never during.

### Mod move APPLIED 2026-08-08 17:36-17:44 — clean, and the bill is visible
`Move mods in-game` → **"Mods successfully moved"**, no `Row not found`, no partial apply (137 free mod
slots, well over the 10-slot pre-flight). Credits **145,321,342 → 137,890,592 (−7,430,750**, matching the
quoted 7,435,500). 1,473 mods moved.
- **modScore 2.83 → 2.83 and plusSpeed 16,662 → 16,657** — confirms again that this was pure
  REDISTRIBUTION, not an inventory gain. Never report a placement run via modScore.
- ⚠️ **The `Move mods in-game` button only opens a CONFIRM MODAL** (`.modal.hotutils-modal`,
  buttons `Cancel` / `Move my mods`). Clicking the first button does nothing on its own — an earlier
  poll sat for minutes waiting on a move that had never started. Then `Moving Your Mods...` shows for
  ~5 min on 1,473 mods.
- ⚠️ Poll in <100s chunks: a long `evaluate_script` wait dies on `Runtime.callFunctionOn timed out`.

**Measured outcome — speed, before → after:**
| group | Δ speed |
|---|---|
| arena datacron five | **+388** (Mob Enforcer 180→280, Greedo 180→293, Cad Bane 166→255, Gamorrean 169→255) |
| arena climb (Leia Rebels) | +235 |
| fleet-arena crew | +312 (Darth Maul +84, Iden Versio +89, Darth Revan +14) |
| GAC 5v5 #1 wall | +86 |
| **Galactic Legends** | **−349** (JML 568→472, JMK 557→491, Rey 505→452, GL Ahsoka 506→454, SEE 460→412) |
⇒ The priority order was honoured literally and **the GLs paid for it.** Defensive GLs took real hits
(GL Rey −53, GL Ahsoka −52) and those are AI-played in GAC, where speed matters most. If GAC matters more
than a mode that pays no crystals, re-run with GLs promoted above the arena five — that ordering measured
**+0.12%** and costs another ~1,400 moves / ~7M credits. Decide once and stop churning: each re-run is
~7M credits for a global change inside the noise.

## 2026-08-08 (night) — RotE PHASE 6 played: the Operations GL trap, and the cross-area unit lock
Phase 6/6, 22h left, guild #4, 23/56 stars, Guild GP 524,387,216. Board:
**Haven-class Medical Station (DS)** 1.07M/235M · **Kessel (Mixed)** 3.89M/235M · **Lothal (LS)** 20.2M/247M.
Star gates 235M/400M/500M (Haven, Kessel) and 247M/420M/525M (Lothal).
Markers per territory: Haven 4 combat + 1 special + ops · Kessel 3 combat + 1 fleet + 1 special + ops ·
Lothal 3 combat + 1 fleet + ops. **Neither special is fieldable** (Haven = Inquisitorius R8+ + *Third
Sister*, unowned; Kessel = Qi'ra + L3-37, both **R7** against an R8 gate → `REQUIRED UNITS 3/5`).

### Phase 6 numbers are NOT phase 2 numbers — re-read them every phase
| | phase 2 | **phase 6** |
|---|---|---|
| operation gate | Relic 6+ / 7★ | **Relic 8+ / 7★** |
| per completed operation | 11,000,000 TP | **18,480,000 TP** |
| combat-mission win | 250,000 | **up to 493,594** (+ squad power, as always) |
Quota is still **10 assigned units per player per operation AREA**, 6 operations × 15 slots per territory.

### Navigation: the Operations marker is NOT the gold marker
The **gold hexagon is the Special Mission.** Operations live behind the *territory-ability* marker — the
square tile showing that territory's ability (`Hope (Full Strength)` / `Smuggling (Disabled)` /
`Guerilla Strike (Disabled)`) → **ENTER** at (1470,1000). Ops list: OPERATION 1/2/3 at x=155,
OPERATION 4/5/6 at x=1763, y = 402 / 641 / 880. Slot grid cols 630,795,960,1125,1290 · rows 400,600,800.
`CLOSE` (745,988) · `ASSIGN` (1170,988). The op tiles stay tappable behind the open slot dialog.

### ⚠️⚠️ THE GL TRAP — most "UNDEPLOYED" slots in phase 6 are Galactic Legends
A slot renders gold `UNDEPLOYED` when Astra owns a unit meeting the gate, and red when he does not.
At an **R8 gate** the ordinary version of an iconic character usually FAILS, so the only qualifying unit
Astra owns is the GL — and the portraits are nearly identical. Verified by elimination against
`account/data/all` `relicLevel`:
| slot portrait | ordinary unit | actual fillable unit |
|---|---|---|
| hooded pale Palpatine | `EMPERORPALPATINE` **R7**, `DARTHSIDIOUS` R7 | **`SITHPALPATINE` (SEE, GL)** |
| black helmet, red seams | `KYLOREN` **R7** | **`SUPREMELEADERKYLOREN` (GL)** |
| Rey in white | `REY` R7, `REYJEDITRAINING` R7 | **`GLREY` (GL)** |
| old bearded hooded Luke | — | **`GRANDMASTERLUKE` (JML, GL)** |
⇒ **Never tap a slot on portrait recognition.** Cross-check the portrait against every same-character
baseId's `relicLevel` first; if the only R8+ match is a GL, skip it. A GL is worth ~493K guaranteed in a
combat mission; a slot in an operation that will not reach 15/15 is worth ~0.

### ⚠️ The quota is per-area, but a UNIT is unique across ALL areas
`Assigned Units: n/10` is per territory, yet each unit can be assigned only once in the whole phase.
Assigning Han Solo + Maul to **Kessel Op2** silently dropped **Haven Op1** from `3+` fillable to `1`
(8/15 +4 → +1). **Enumerate every area's fillable slots BEFORE assigning anything**, then spend the
scarce shared units on the operation closest to 15/15. The game does block same-unit double-picks with a
`DUPLICATE UNIT SELECTION — Unit already selected in another squad` modal (OK at (958,688)).

### Reading the panel
- Number on an **empty** slot = the REQUIREMENT (`8` = Relic 8+, `85` = a level-85 / 7★ ship).
  On a **filled** slot it is the assigning player's actual relic. Do not read it as ownership.
- Red badge on an operation tile = count of **distinct** units Astra can still fill, display caps at `3+`.
  Two slots naming the same unit count once (Op2 showed `2` for 4 gold slots).

### The allocation rule that fell out of the maths
Slot value = `18,480,000 / 15 × P(op reaches 15/15)` ≈ **1,232,000 × P**. Deploying that same unit is
~35–45K, a combat mission is ~493K + power over 5 units (~139K/unit). So:
**fill an operation only while P is plausible — closest-to-15 first — and stop; below ~11% a unit is worth
more in a combat mission, below ~3% more as a plain deploy.** Ops sitting at 0–2/15 in a guild that had
filled 68 of 270 phase-6 slots are worth less than deploying.

### Result: 14 units placed, no GL and no capital ship spent
| territory | before → after |
|---|---|
| Kessel | Op1 **11→13/15**, Op2 **8→10/15** (4 units: JK Luke, a TIE, Han Solo, Maul) |
| Haven | Op1 **8→9/15** (Embo), Op3 **4→7/15** (2 Inquisitor-types + **Executor**), Op6 **2→4/15** (2 ships), Op4 1→2/15 (Wampa) |
| Lothal | Op1 **7→10/15** (Kylo Ren Unmasked, Jedi Knight Revan, Razor Crest) |
Executor was safe to spend because Haven has **no fleet mission** and the two that exist take
**Leviathan** (Kessel, mixed) and **Negotiator** (Lothal, LS).

### Pool arithmetic that made "fill operations first" safe
`combatType==1 & relicLevel>=8` → **81 characters (46 LS / 35 DS, 0 Neutral)**; **67 ships at 7★**.
Phase-6 demand = 10 ground missions × 5 = 50 characters + 2 fleets × 8 = 16 ships. That leaves ~31 spare
characters and ~51 spare ships, so the full 30-unit quota could never have stranded a mission. Run this
count before agonising over any reservation list.

### ⚠️ New modal: `Unit Required in another Territory`
Committing a combat-mission squad that contains a unit **named by an operation slot in a DIFFERENT
territory** pops `Unit Required in another Territory` — *"All used units will be locked to this territory
until the next phase. Are you sure you want to use them here?"* — with the offending portraits and
`CANCEL` (715,779) / `BATTLE` (1197,779). It fired on **Jabba** for a Kessel combat mission.
- `rote_autobattle.py` cannot see this modal: it taps squad-screen BATTLE, never finds the battle HUD and
  returns `RESULT=no-battle-screen`. **Screenshot after a `no-battle-screen`** before assuming a miss-tap,
  answer the modal, then re-attach with `--no-start`.
- Answer it with the same arithmetic as everything else: a GL leading a combat mission is worth ~493K
  guaranteed; the operation that wants it is only worth `1,232,000 × P`. Jabba → BATTLE was right because
  every operation still open to Astra sat at ≤5/15.

### ⚠️ Phase-6 combat missions are 2 WAVES with PARTIAL credit — and the driver misreports the outcome
`Completed a Combat Mission (1/2 waves), earning 219,375` vs `(2/2 waves), earning 493,594`. So a phase-6
loss is **not** the phase-2 `EARNED +0`: clearing wave 1 and dying in wave 2 still banks ~44% of the prize.
- **`rote_autobattle.py`'s `outcome=` is not trustworthy here.** It called the 1/2-wave partial a `win`
  and the 2/2-wave full clear `ended`. **Read the territory activity feed** (right-hand panel of the
  territory view) for the truth — it prints waves cleared and TP earned per entry.
- Squad power did not decide it: Jabba/Darth Revan/GAS/Stranger/Darth Bane at **225,514 → 1/2 waves**,
  while GL Leia/Rotta/Satele Shan/Cmdr Ahsoka/Baylan at **215,035 → 2/2**. The in-game auto-fill sorts by
  power and ignores faction synergy, which is worth ~274,000 TP per mission when it guesses wrong.

## 2026-08-09 (02:00) — RotE phase 6, second pass: a 0/2 wipe pays NOTHING
Same phase 6 as the entry above, 17h 33m left, guild **#1**, 23/56 stars. Owner had already run the
deploy step before this session, which is the fact that explains every dead end below.

### ⚠️ A 0/2-wave loss earns +0 TP **and deploys no power** — correct the loss-is-free claim
`rote_run_mission.sh`'s header says *"A LOSS IS STILL WORTH RUNNING: the squad's galactic power is
credited as territory deployment either way (device-verified 2026-08-03)"*. That held in **phase 2**.
It is **false for a phase-6 wave-1 wipe**: two missions run back-to-back both showed
`RESULTS 0/2 — EARNED +0 Territory Points`, the Haven total stayed at exactly **150,463,903** across
both, and **no `Astra: Deployed …` line appeared in the activity feed**. Partial credit starts at
1/2 waves (219,375); below that there is nothing, not even the squad's power.
⇒ Only the ladder `2/2 = 493,594 · 1/2 = 219,375 · 0/2 = 0` is real. Do not run a mission you expect
to lose in wave 1 "for the deploy points" — there are none.

### Haven phase-6 combat is out of reach for this roster (Hope at Full Strength)
Haven's enemy ability `Hope` sits at **Full Strength** because the guild has completed **0/6** Haven
operations, and the missions are tuned accordingly. Both of Astra's best carries wiped in wave 1 in
under a minute:
| squad | power | result |
|---|---|---|
| SEE (L) + Maul Hate-Fueled + Dark Rey + Count Dooku + Kylo Ren Unmasked — **all Sith**, full lead value | 200,994 | **0/2**, +0 |
| SLKR (L) + General Hux + Sith Trooper + Bossk + Zam Wesell — 3× First Order | 188,027 | **0/2**, +0 |
Synergy was not the problem this time; the gap is size. Mods had just been redistributed to arena /
datacron / fleet crew (2026-08-08), so the GLs were fighting on leftovers. **Check where the mods are
before assuming a GL can carry a TB mission.**

### Once the owner deploys, everything else in that territory closes
Deploy is the terminal action for a territory, and it is silent about it:
- the territory's `DEPLOY` button greys out and the deploy marker gets a red 🚫 (also visible on the
  planet in the galaxy overview — Kessel and Lothal had it, Haven did not);
- combat missions there stop being playable and the button reads **`REQUIRED UNITS 0/5`** instead of
  `BATTLE (n)` — that string means *0 units available*, NOT *0 selected*;
- operation tiles lose their red badges, so there is nothing left to fill.
Read the galaxy-overview 🚫 first: it tells you which territories are already finished before you
spend ten minutes probing panels one at a time.

### Reading the mission panel: faded + ✓ = ALREADY USED
`MISSION UNITS` on a combat-mission panel lists units valid for that mission. **Vivid tile, no tick =
available. Faded tile with a white ✓ = spent.** Lothal's list was 100% ticked (deploy had eaten the LS
pool); Haven's was clean. `View All Valid Units` opens the full list. The squad screen also prints a
per-unit `n/m` uses counter next to the green party icon.

### Operations state at 02:00 (nothing left worth filling)
| territory | quota | Astra-fillable slots |
|---|---|---|
| Haven | 7/10 | Op1 9/15 → SEE · Op2 4/15 → SEE · Op4 4/15 → SLKR · Op5 3/15 → SEE+SLKR |
| Kessel | 4/10 | **none** (Op1 sat at **13/15** and he could not reach it) |
| Lothal | 3/10 | **none** |
Every remaining fillable slot in the whole map was a **Galactic Legend**, and the only one on an
operation with a plausible P was Haven Op1 — which had been **static at 9/15 for a full day**. By the
`1,232,000 × P` rule that is well under the ~11% break-even, so SEE and SLKR went to combat instead.
Kessel Op1 at 13/15 is the lesson: **the quota is not the constraint, the named units are.** Six unused
Kessel slots were worthless because no slot named a unit Astra still had free.

## 2026-08-10 (night) — fleet-node reward icons READ ON DEVICE; the 1-E entry is confirmed waste

Closes the open question the farmbot config has been carrying: *"1-E drops Resistance X-wing, which Astra
already has at 7 stars … Not yet device-confirmed, so the validated node stays until someone reads the
reward icons on 1-A."* All three panels below were read off the live client.

| Fleet HARD node | Possible rewards (per panel) | Energy | Verdict |
|---|---|---|---|
| **1-E Lothal** (bot's current entry) | Resistance X-wing **×1** (already **7★** → dead shards), Mk V ×2, Mk II ×2 | 16 | **Waste.** Shard slot yields nothing. |
| **1-A Yavin 4** | **Captain Ithano ×2** (CHARACTER, roster **4★** G10), X-wing ×1, Mk IV ×2, Mk II ×2 | 16 | Strictly dominates 1-E — same X-wing + mats **plus** 2 live shards. |
| **2-E Jakku** | Kyle Katarn ×2, **Raven's Claw ×1**, Mk III ×2, Mk VI ×2 | 20 | **Best while Raven's Claw is under 7★.** |

- **Captain Ithano is a CHARACTER, not a ship** (`ITHANO`, ct=1, r=4, g=10). The old note filing him under
  "Fleet Hard" shard targets is right about the node and wrong about the unit type.
- **Raven's Claw sits at 76/100 blueprints — 24 from 7★.** That is the nearest marginal **RotE operation
  slot** (ops gate ships at 7★, ~733,000 TP per filled slot), which makes 2-E the highest-value fleet node
  on the board right now. MG-100 StarFortress SF-17 (5★) is the only other sub-7★ ship — 185 shards away.
- **Measured drop rate: Raven's Claw ≈ 1 blueprint per 5 sims.** A 5× MULTI SIM of 2-E (100 fleet energy,
  5 sim tickets) returned **6× Kyle Katarn, 1× Raven's Claw**, Mk VI ×2, Mk II ×4, 6,600 credits, 300 ally
  points. So the ship blueprint is RNG, *not* one-per-battle → ~24 days of daily 5-sims to reach 7★.
- **Hard nodes are 5 attempts/day, then a 💎25 refresh** (declined). This caps how much of a big fleet pool
  one node can absorb: 5 × 20 = 100 energy. Do not plan a 144-energy dump through a single hard node.

### ~~Still TODO~~ — DONE 2026-08-10 13:20, and it needed three captures, not one
Swapping the bot's `campaign: fleet` entry from **1-E → 2-E** needed `farmbot/templates/node_fleet_2-E.png`
first (nav is template-matched; no template = that entry fails). Two things the original TODO missed:

1. **The `_sel` crop is not optional here, it is the PRIMARY case.** `tasks.py` already tries
   `node_<campaign>_<node>_sel` as an automatic `alt` — no config needed — and **2-E is chapter 2's
   default selection**, so the map opens with it already glowing. The unselected crop alone would have
   missed on nearly every run. Measured separation on live screens:

   | screen | `node_fleet_2-E` | `node_fleet_2-E_sel` |
   |---|---|---|
   | 2-E selected (default view) | 0.458 | **1.000** |
   | 2-E unselected (2-D selected) | **1.000** | 0.406 |

   To capture the unselected variant, select a *neighbouring* node — the map re-centres on whatever is
   selected, but template matching is position-independent, so only the node's own appearance matters.
2. ⚠️ **`chapter_tab_2` did not exist.** `--doctor` reports it as *soft-missing (handled)*, which is
   misleading here: the SELECT_CHAPTER step is `optional=True`, so a missing tab template means the bot
   **silently never switches chapter** and then hunts for 2-E inside whatever chapter the map remembers.
   Captured at **60×50 around the glyph only** (same crop size as `chapter_tab_8`). Counter-intuitive
   result from a size sweep: *widening* the crop makes discrimination WORSE, because the tab frame is
   identical across tabs and only the numeral differs — 60×50 scores tab 3 at 0.823, 130×62 at 0.846.
   Tightest wins: std 36.4, tab 2 at 0.987–1.000 against 0.823 for the nearest other tab.
   The glyph crop matches in BOTH selected and unselected states (TM_CCOEFF_NORMED subtracts the mean,
   so the brightness change does not register). That is fine — re-tapping the current chapter is a no-op,
   and it makes the step deterministic instead of state-dependent.

### 2-D checked the same day, and it is NOT the better node
2-D Jakku drops the **MG-100 StarFortress SF-17** ("Resilient Resistance Tank"), **58/85 — 27 blueprints
from SIX stars**, plus Mk VI ×2, Mk VI ×2, Mk V ×2 for 20 energy. **No character shard slot at all.**
This corrects the estimate above: the earlier "MG-100 … 185 shards away" was measuring the distance to
7★. Since **operations gate ships at 7★**, six stars unlocks nothing, and MG-100 is ~127 blueprints from
the tier that would pay. Raven's Claw at **77/100** is 23 away from the same prize. ⇒ 2-E stays the target.
- Useful for today only: **the two nodes have independent 5-attempt counters.** When 2-E is spent, 2-D is
  still open, which is the only place surplus fleet energy can go without a 💎25 refresh.
- Reward icons have **no tooltip on long-press** — a plain *tap* opens the item detail card, which is what
  prints `You Own: 58/85` and the promote-to-six-stars line.

## 2026-08-10 (night, 02:45) — the RELIC MATERIAL economy, decoded on device

Closes the biggest blind spot in `invest_plan.py`: it ranks *what is worth upgrading* and has never known
*what the client will let you buy*. Both questions were answered live this session.

### ⭐ The in-game SELECT FILTER is the affordability oracle — use it before planning a spend
Roster → filter dropdown → **SELECT FILTER** carries `RELIC AMPLIFIER UPGRADE`, `OMICRON ABILITY UPGRADE`,
`ZETA ABILITY UPGRADE`, `GEAR UPGRADE`, `ABILITY UPGRADE`, `UNIT LEVEL UPGRADE`. Each lists exactly the
units whose upgrade is **affordable right now**, with a badge = how many steps are available. This is
ground truth and costs 4 taps; `invest_plan.md`'s queues are a priority order, NOT a shopping list.
- Measured gap: the relic queue lists **39** targets and the ability queue **17** omicrons. The client
  said **~30 relic** steps affordable and only **2 omicron** — and after six relic steps the relic list
  collapsed to **4**. A queue entry is not a purchasable.
- ⚠️ The dialog **remembers its scroll offset** between openings. Taps at fixed y-coords land on different
  rows run-to-run (this session checked `501ST` by accident). Always screenshot the dialog before ticking.
- The text field sits at a fixed position at the dialog bottom; clear it with
  `input keyevent KEYCODE_MOVE_END` + 20×`keyevent 67`, then `input text "<name>"`, then **OK** (dismiss
  the IME) and only then **CONFIRM**. Driver: `~/Downloads/relic_nav.sh <backs> <name> <shot>`.

### Relic material ids: `SCV_001..011` are relic mats 1..11 in tier order
Confirmed by differencing `account/data/all` → `material.material` against the counts painted on the
Relic Amplifier panel across six live upgrades. `RM_001..004` are the separate "relic currency" trio/quad
shown in the right-hand sub-panel. (`SCV_*_SURPLUS` buckets do **not** count toward a requirement.)

| Relic step | Materials consumed (per step) | Credits |
|---|---|---|
| R5 → R6 | SCV_001 ×20, SCV_002 ×30, SCV_003 ×30, SCV_004 ×20, **SCV_005 ×20** | 250K |
| R6 → R7 | SCV_001 ×20, SCV_002 ×30, SCV_003 ×20, SCV_004 ×20, **SCV_005 ×20**, SCV_006 ×10 | 500K |
| R7 → R8 | SCV_003 ×20, SCV_004 ×20, SCV_005 ×20, SCV_006 ×20, **SCV_007 ×20**, SCV_008 ×20 | 1M |
| R8 → R9 | (consumed SCV_005 ×20 + SCV_007/008/009/010 ×20 each) | — |
| R9 → R10 | SCV_007 ×20, SCV_008 ×20, SCV_009 ×20, SCV_010 ×20, SCV_011 ×20 | 2M |

- **`SCV_005` is the binding constraint for the entire R5→R7 band** — 20 per step at *both* tiers. It ran
  **134 → 14** in six steps and stopped the run cold. It is NOT the mats the planner worries about.
- **The wall for R7+ is `SCV_007` (13) and `SCV_009` (12)**, both needing 20. That — not credits — is what
  blocks **Starkiller R9→R10**. Credits are a non-issue at 140M against a 2M top tier.
- ⇒ **"Displayed R7" is the correct planner ceiling** (`DEFAULT_TARGET_DISPLAYED_RELIC = 7` is right for
  the wrong reason): R7→R8 is where the scarce mats begin, so the queue is affordable exactly to R7.

### Executed this session (arena-first, owner's call; omicrons held)
Starkiller **R8 → R9** landed at the end of the previous session (HotUtils read R8 at the 02:10 pull, the
client read R9). R9→R10 blocked. Then, in `invest_plan` tier-1 order:

| unit | from → to | note |
|---|---|---|
| Mob Enforcer | R5 → **R7** | target met |
| Gamorrean Guard | R5 → **R7** | target met |
| Cad Bane | R5 → **R6** | one short — `SCV_005` hit 14/20, `Insufficient Materials` |
| Greedo | R6 → R6 | **not started** — same shortfall |

Credits 142.1M → 140.4M (−1.7M). GP **14,408,223 → 14,419,987** (+11,764).
The 4 units still listed as affordable are all **priority tier 12 ("not on any board")** — Snowtrooper
Commander, R5-D4, Colonel Ward, Zeb Orrelios (New Republic Pilot) — and were declined, not missed.

### Omicrons: 16 held, and that is worth ~one application
The material reads **16 / 10** on Gungan Boomadier's *Grand Army Specialist* 8→9, so `ability_mat_F` = the
omicron material and a single application costs **10**. Only two units are eligible at all — Boomadier
(priority tier 5) and Snowtrooper Commander (tier 12) — and **neither is in the 17-entry TW omicron
queue**. Owner decision 2026-08-10: **hold**, since spending 10 leaves 6 and forecloses a queued target.
Do not read `ability_mat_F = 16` as "16 omicrons to spend" — it is 1.6 applications.

### ⚠️ Amplify taps must be spaced ≥ 7s
The success animation swallows input for ~5–6s. A second `tap 1655 993` at +5.0s was silently dropped
(Gamorrean read R6 when two steps were intended). Tap → `sleep 7`+ → screenshot → verify the ring number
before the next tap. A blocked step raises an **`Insufficient Materials`** modal (OK at ~958,690), which
is harmless but eats the next tap if unhandled.

### Relic material NAMES confirmed, and where `SCV_005` actually comes from (03:25)
Shipments prints "You Own" next to every item, which pins the ids exactly:

| id | Name | Held at 03:25 |
|---|---|---|
| `SCV_005` | **Electrium Conductor** | **14** |
| `SCV_006` | **Zinbiddle Card** | 80 |
| `RM_001` | **Fragmented Signal Data** | 1,343 |

- **Electrium Conductor is sold ONLY in the crystal `Featured Shipment`: 10 for 💎1,150.** Astra holds
  💎1,855, so it is *technically* one purchase away from unblocking exactly one more R6→R7 step — but
  **crystals are off-limits**, so this is not a route. (It is also awful value.)
- **Checked and NOT stocked:** `Guild Events` (GET1/2/3) and `Grand Arena` token stores — both carry only
  gear salvage plus Zinbiddle Card / Micro Attenuators / Signal Data. So there is **no token-currency
  route** to Electrium Conductor. The non-crystal supply is event rewards only: Conquest, Territory
  Battles / Guild Event, Galactic Challenges.
- Useful side-findings in `Guild Events` (all GET3, 4,590 held of 20K cap):
  **Micro Attenuators ×5 = 125** (the mod-calibration currency — cheap, and 152 are already held),
  **Zinbiddle Card ×2 = 850**, Fragmented Signal Data ×20 = 1,600 (GET2), Incomplete Signal Data ×20 = 2,000.
- ⇒ **The relic band is gated on event cadence, not on anything the planner can schedule.** Conquest
  Ascension was 17h 32m out and the Guild Event 18h 31m out when this was read.

### Navigation gotcha: the hub back-arrow is not where you think
From the Relic Amplifier, two backs land on the **roster/Inventory**; a third drops to the **hub**, where
`tap 65 65` is the **SETTINGS gear**, not a back button. Close it at ~(1546, 240). The game also drifted
to the **Squad Arena** screen unprompted between sessions — always screenshot before tapping, or a stray
tap starts a battle.

## 2026-08-10 (early morning, 03:53–04:45) — the Mace Windu Legendary, and why auto-battle cannot play it

First attempt at **"Beset on all Sides"** (Jedi Master Mace Windu, Legendary) **Tier I**. **Lost.**
The event sits in the **Journey Guide with no deadline**, so this costs nothing but time — but most of
the hour went into diagnosing things that were never bugs, and that is what this section is for.

### ⭐ Auto-battle does NOT drive Legendary events
The top-left toggle turns green and the sim still waits for a manual ability tap **every single turn**.
Budget for turn-by-turn driving. This is the exception to the standing "auto is fine" rule — auto is
fine for Squad/Fleet Arena and for raids, and useless here.

### ⭐ A battle that never advances is waiting for INPUT, not hung
Idle animations keep playing and the pause menu still opens, so "UI responds but nothing happens" is
**not** evidence of a crash. One force-restart was spent proving this — and the restart then hit an
asset-load failure, costing a re-entry through the Journey Guide. `adb logcat` showed nothing either.
Do not force-stop the client over a stalled sim.

### ⭐ The CANCEL trap — abilities are two-step, and blind-cycling looks exactly like a freeze
Tap ability → tap target. Some abilities fire immediately; others enter a targeting mode showing
`Select an ally.` / `Select an enemy.` **The selected ability's own slot becomes CANCEL.** So cycling
the ability positions blind just selects-then-cancels forever, which is visually identical to a hang.
Always resolve the target before tapping another slot.
- Valid targets in targeting mode carry green `»` `«` chevrons beside their health bars.
- **Ability bar is right-aligned at y=985:** three abilities → x = 1245 / 1545 / 1845; two abilities →
  x = 1645 / 1845. Rightmost is usually the strongest special.
- **Long-press to read a tooltip:** `adb shell input swipe X Y X Y 1000`. Fastest way to learn an
  unfamiliar loaned or event unit's kit in context. Tap empty ground (~300, 900) to dismiss tooltips
  and the unit-info panel.
- Retreat is free: gear (65, 65) → RETREAT (955, 715) → YES (713, 771).

### Two "rendering bugs" that turned out to be mechanics
- **Dithered / stippled semi-transparent figures are Stealthed units**, not broken models. They render
  as flat grey silhouettes and read as a texture-loading failure at first glance.
- The **dark silhouettes are the civilian markers** for the tier objective, not unloaded assets.

### The objective IS the fight — Scorch Entrenched is the counter
Tier I is not a damage race: the win condition is **preventing the Bad Batch rescue**. That makes
**Scorch's Entrenched (taunt + Bulwark)** the mechanic that matters, with CX-2's Disarm behind it.

### ⭐ Why it was lost: potency, measured
Scorch **36.0 %** and CX-2 **37.5 %**, against a community target of ~90–100 % for this tier. The
debuffs the plan depends on — Scorch's DoTs and Off-Balance, CX-2's Disarm — simply do not land.

**The root cause is modding, not relics.** Both are already 7★ G13 R7, well past the event's R5 floor:

| unit | baseId | current mods | cross primary | potency |
|---|---|---|---|---|
| RC-1262 "Scorch" | `SCORCH` | **4× Defense set** + crit-chance + tenacity | Defense % | **36.0 %** |
| CX-2 | `OPERATIVE` | **6× Health set** | Health % | **37.5 %** |

Scorch does not carry **one** potency secondary. Neither unit has ever been modded for the stat.

**Inventory is not the constraint** (read off the 02:10 dump, 2,330 mods):
**184 potency-set mods** (178 at level 15), **26 unassigned** · **74 potency-primary crosses**
(only slot 7 can carry one), **7 unassigned**.

### The other two gating units are already fine
All four event units are owned and above the R5 floor, so nothing here needs farming:
Depa Billaba (`DEPABILLABA`) 7★ G13 R6 at **70.1 %** potency, Temple Guard
(`VANGUARDTEMPLEGUARD`) 7★ G13 R6 at **42.9 %**.

### ⚠️ Do not reach for a full Grandivory re-run to fix two characters
Measured 2026-08-08: ~1,473 mod moves, **−7.4M credits**, global set-value change inside the noise
(±0.12 %). Use a restricted selection with **`lockUnselectedCharacters: true`** instead.
The cost to weigh: `SCORCH` and `OPERATIVE` are both in **5v5 defense squad #3** and **TW defense #3**
(Lord Vader / Appo / Disguised Clone Trooper / CX-2 / Scorch), so a potency build degrades a live wall
until the mods go back.

The payoff is not a collection trophy: **`JEDIMASTERMACEWINDU` appears three times in the `gaps` lists
of `data/board_result.json`** (5v5 offense, 3v3 defense, 3v3 offense). The board planner already wants
him.

⇒ **The retry is a modding job, not a farming job.**

### ⭐ The potency arithmetic, measured off the dump (`scripts/potency_build.py`)

    stats.potency = baseStats[17]×100 + Σ(mod potency)/100 + 15 × completed_potency_sets

- **`statValueDecimal` for a PERCENTAGE stat is the percentage ×100.** Flat stats use ×10000 —
  speed reads `140000` for +14. Counting the wrong stat id would report +1400pp and look like a win.
- **A completed potency set is 2 mods and worth exactly +15.00pp.** Measured across seven units;
  PAO wears four and reads **+30.01pp**. Only slot **7 (cross)** can carry a potency PRIMARY —
  all 74 potency-primary mods in the inventory are slot 7.
- Verified end to end: CX-2 `baseStats 0.34 + statEffects 0.03457 = 37.46`, and his mods carry
  potency secondaries `162 + 183 = 3.45pp`. Mace Windu `0.46 + 0.45604 = 91.60`, where his mods give
  30.60pp and the missing **15.00 is exactly one set bonus**.
- ⇒ Restricting a potency build to set-7 mods in all six slots is not a simplification, it is
  optimal: swapping in an off-set mod breaks a pair and forfeits 15pp, and no secondary roll in
  this inventory pays that back.

### ⚠️⚠️ Two donor-safety traps, both of which silently under-protect
The solver's whole risk is handing out a mod off a squad that is actually in use. Both traps below
produced a confident, wrong "no squads touched" before being caught:

1. **Ships take no mods — expand fleets to their CREW.** `MAUL` holds the roster's **only 6-dot
   30pp potency cross** and crews `SITHINFILTRATOR` in `Fleet - Arena`. A protected set built from
   the literal ids in `board_result.json` contains the SHIP, not Maul, so the solver offered his
   cross as free. Expand through `data/ship_crew.json`. (Same class of error as the earlier
   "rank the CREW" invest_plan bug — it has now bitten twice.)
2. **A baseId can start with a DIGIT.** `4LOM` and `50RT` are real ids, and **4LOM flies on 5v5
   defense**. An id pattern anchored `^[A-Z]` drops him. Allowing a leading digit also swallows the
   board's formatted counts (`"29K"`, `"120K"`), so intersect with the real roster — exact, where a
   pattern is only ever a guess.

### Result: both units clear the bar without touching a single live squad
| unit | now | projected | slots | sets |
|---|---|---|---|---|
| `SCORCH` | 36.0 % | **120.7 %** | 6/6 | 3 |
| `OPERATIVE` | 37.5 % | **113.8 %** | 6/6 | 3 |

Donors — **HOTHLEIA, MOTHERTALZIN, OLDBENKENOBI, PAO, TEEBO, ZAMWESELL** — appear in no board,
arena or fleet-crew squad. 296 units are protected out of 397; the donor pool is still 832 mods,
381 of them unassigned, so the constraint never bound.
⚠️ What DOES change is **5v5 defense #3 / TW defense #3** — Scorch and CX-2 are in it and we are
re-modding *them*, trading their Defense/Health sets for potency. That is unavoidable and is the
real cost of the attempt; plan to restore before the next GAC lock.

### ⭐⭐ `mods/equip` — the direct mod-move API (no Grandivory, no browser automation)
Grandivory cannot be driven end-to-end: character cards only accept genuine HTML5 drag-and-drop, so
**adding a character to the selection is not automatable** (see the earlier GI section). That blocks the
documented route whenever the units you want are not already selected. The direct API sidesteps it, and
it is *better*: an exact loadout instead of an optimiser's heuristics.

Discovered by fetching HotUtils' own JS bundle from a logged-in page and reading the call sites —
`document.querySelectorAll("script[src]")` → `fetch` → search for `mods/`. That listing is itself worth
keeping: `mods/equip`, `mods/unequip`, `mods/batch`, `mods/reveal`, `mods/lock`, `mods/unlock`,
`mods/set/get`, `mods/set/savebaseline`, plus a `mods/task/<op>` async twin for each.

```
POST mods/task/equip   {sessionId, units:[{id:<unit UUID>, modIds:[<mod UUID> …]}],
                        getAllData:true, simulation:false}     -> {taskId, responseCode:1}
POST mods/equip        same body, synchronous
```
- **`id` is the unit's UUID, NOT its baseId** (`units.units[i].id`), and `modIds` are mod UUIDs. Shape
  read from `backupCurrentBaseline`, which builds `{id: e.id, modIds: e.mods.map(m => m.id)}`.
- Specify **all six slots**; then it does not matter whether the server reads `modIds` as "the desired
  loadout" or as "mods to equip", because both give the same end state.
- Un-equipping from the donor is automatic — no separate `mods/unequip` call is needed.

**⚠️ The no-op probe is the safe way to validate the payload before writing anything.** Re-equip a unit's
CURRENT mods: the server computes an empty diff and refuses, so a correct payload *cannot* change
anything, while a wrong one fails loudly. Two things to know:
- The live server answers an empty diff with **`responseCode 2` / `errorMessage "No mod actions to
  perform!"`** — NOT the `"TASK SKIPPED"` string the shipped bundle branches on. Guarding on the
  bundle's string alone rejects a payload the server understood perfectly (cost one aborted run).
- **A bogus UNIT id is reported precisely** (`Unit '<id>' not found on player`) — which is what proves the
  server really resolved your key. A bogus MOD id is *silently ignored*, so it is not a useful probe.

**Applied 2026-08-10 13:05, task 55247, verified against a fresh `account/data/all`:**

| unit | potency | health | protection | **speed** |
|---|---|---|---|---|
| `SCORCH` | 36.00 → **120.68 %** | 71,152 → 64,002 | 115,473 → 92,441 | 270 → **189** |
| `OPERATIVE` | 37.46 → **113.77 %** | 87,056 → 61,259 | 67,382 → 80,064 | 255 → **188** |

Projection vs measured agreed to **0.02pp**, which validates the arithmetic model above end to end.
⚠️ **The unpriced cost is SPEED: −81 and −67.** The solver maximises potency and is blind to everything
else; a potency-set mod with no speed secondary is free from its point of view. For a GAC/TW wall that
is a serious loss, and even in the event it means the Bad Batch acts more often before Scorch can
Entrench. If a future build needs both, the objective has to be multi-stat, not potency-only.
Restore point: `output/potency_restore.json` → `potency_build.py --restore <path>`.

### Tier I retried at 120.7 % potency — **still DEFEAT**, and the failure mode moved
Attempt 2 (2026-08-10 ~15:10). Squad is fixed by the event: **CX-2 + Scorch + a loaned 5★ TK
Stormtrooper**, 78,384 squad power, and all three are **"Event Unit" kits** — not the units' normal
abilities, so any guide written about their live kits is only half-relevant.

Kits as they actually appear (read via long-press in battle):
| unit | ability | effect |
|---|---|---|
| TK Stormtrooper | *Rifle Blast* (basic) | damage + **target ALLY** dispels debuffs, Crit Avoidance Up, **cooldowns −1**, weakest ally recovers 20 % |
| TK Stormtrooper | *Grenade Throw* (2t) | dispel all buffs + Physical damage to all enemies |
| Scorch | *Entrenched* (4t) | **Taunt 2 turns**, recover 25 % HP/Prot, **5 stacks Bulwark** (+150 % Defense each) |
| CX-2 | *Instruments of the Empire* (3t) | damage + **Disarm 2 turns, cannot be evaded or resisted** + Vulnerable |

- ⭐ **Potency DID its job.** Off-Balance landed, debuff stacks built on the enemy team — the exact
  thing that failed at 36 %. The stat was correctly diagnosed.
- ⚠️ **But CX-2's Disarm "can't be evaded or resisted"** — so the single most important debuff in the
  kit never needed potency at all. Worth knowing before paying for potency again.
- ❌ **The team still lost, from a different cause:** the Bad Batch side stacks buffs relentlessly
  (reached **▲10, ▲11, ▲16**) and counter-attacks, and my units were killed one by one until only a
  stealthed CX-2 remained. Enemy health bars had barely moved.
- ⇒ **Potency was necessary but NOT sufficient, and a potency-ONLY objective overshoots.** The build
  paid **−81 speed on Scorch and −67 on CX-2**, plus 7K/26K health — in a fight decided by surviving an
  enemy buff-snowball, that is trading away the very thing that was needed. A third attempt should
  optimise potency **and** speed/survivability together, not potency alone.
- Tactical notes for next time: `Grenade Throw`'s dispel is largely wasted — most enemy buffs render
  with a **padlock (undispellable)**. Open with Entrenched, keep it on cooldown, and spend the
  Stormtrooper's basic on **Scorch as the ally target** (it takes Entrenched from 4 turns to 3).

**Mods restored 2026-08-10, task 55332, verified**: Scorch back to 36.00 % / 270 speed, CX-2 to
37.46 % / 255, and all six donors to their original values. The GAC/TW wall is whole again.

#### Lead for attempt 3: the **Loaned Unit Era Level** calendar
Spotted 2026-08-11 while sweeping the login calendars. There is a **"LOANED UNIT ERA LEVEL INCREASE
CALENDAR"** (expires in 69d) whose reward reads *"Loaned Unit Era Level Increase ×N — This will
increase your Loaned Units Era Level."* Days 1–14 are already claimed (1–5 per day); days 15–28 hand
out 1–2 more each.

Why this matters here: **one third of the Beset on All Sides squad is a loaned 5★ TK Stormtrooper**,
and the fight was lost to a survivability gap, not a damage or potency gap. If this calendar's era
level is what sets that loaned unit's power, it is a **free, no-mod-cost buff to the exact slot the
account cannot otherwise improve** — and it accrues daily whether or not the event is attempted.

⚠️ **Recorded as a hypothesis, not a measured fact.** What was observed is the calendar and its
description; the link to the event's loaned Stormtrooper is inference. **Verify before planning
around it:** re-enter the Tier I squad-select and read the loaned TK Stormtrooper's star/level/power,
then compare against the 5★ seen on attempt 2 (squad power was 78,384 total). If the loaned unit has
risen, the cheapest possible attempt 3 is simply *wait and re-run* — no mod moves, no donor risk,
and therefore none of the −81/−67 speed cost that made attempt 2 worse where it mattered.

## 2026-08-11 (01:00–01:25) — TW defense SET: all 15 walls on the board, front-loaded
First time the computed **TW 5v5 - Defense** bank was actually pushed onto a live Territory War map
(season #3 vs guild *Galatic Republic*, setup phase closing 2026-08-11 ~20:45 Athens).

### The placement flow (in-game, no API path exists for this)
TW map → tap a territory → panel (`<name> Fortification`, `X/39`, *Set Defense +30 Banners · Offense
Win +6-20 · Conquer +840*) → **ENTER** → `PVP MISSION` allied-squad list → **SET DEFENSIVE SQUAD** →
**SELECT SQUAD** → the *Inventory → Squads* browser opens on the last-used tab (`TW 5v5 - Defense`).
Three traps, all hit live:
- **Tap the squad's HEADER ROW, not a portrait.** A portrait tap opens that character's research page
  (the browser is the real Inventory screen, not a picker).
- **`RESTRICTED CHARACTERS` popup = the availability oracle.** "One or more of the characters in this
  squad can not be used in this Battle" means ≥1 unit is already committed on this TW map. CONTINUE
  loads only the free units — for an already-placed squad it loads **nothing** (Squad Power 0), which
  is how D01 was identified as already down.
- **SET is irreversible.** Verify all five slots + the leader-ability banner before pressing it.

### ⭐ How to know what you already placed: STATS ÷ 30
The rank badge top-left of the TW map (`#4`) opens **STATS → Total Banners**. During setup the only
banner source is setting defense at +30/squad, so **own total ÷ 30 = squads placed**. Astra read 240
on entry (8 squads from the 00:27–01:00 pass, i.e. D01–D08) and **450 on exit = 15/15**, which is the
whole computed defense bank. That check is instant and beats scanning ten territories for your name.

### What was placed where, and why front
> ⚠️ **The placement rule stated in this subsection is HALF RIGHT and was applied backwards later
> the same night — read "TW PLACEMENT DOCTRINE" at the end of this file before placing anything.**
> "The front is where squads actually get used" is true. What does not follow is that the *weakest*
> half of the bank belongs there: D09–D15 (19% down to 6% hold) went to the front line while
> stronger walls sat behind them. Front slots are the scarcest thing on the map and must hold the
> STRONGEST squads.

No per-player cap (confirmed again: guild members sit at 368/308/308 banners with no ceiling).
**Guild chat carried no TW orders** — scrolled back 20h, activity feed only — so placement followed
the guild's *revealed* pattern: the two territories ringed in orange nearest the enemy circle were
also the most-filled (9/39 each vs 3–8 elsewhere). Those are the front line and the enemy must conquer
them before the back opens, so squads there are the ones that actually get used.
- **Trenches Fortification** (9→12/39): D09 Partagaz ISB, D10 Qui-Gon Jinn, D11 Jabba. D03 GL Rey was
  already there from the earlier pass (panel's gold banner names the territory's headline squad).
- **Forward Turrets Fortification** (10→14/39): D12 General Grievous, D13 Great Mothers, D14 Res Finn,
  D15 Bad Batch.
- Guild total 1,870 → 2,140 banners across the session; **Astra #4 → #1**.

### Two deliberate non-actions
- **No datacrons attached.** `ADD DATACRON` sits in every defensive squad slot and datacrons *do* apply
  in TW, but they are single-use per war — spending them on the weakest half of the defense bank (D09
  is 19% hold, D15 is 6%) beats nothing, while the same crons on offense convert into cleared
  territories. Kept for the attack phase.
- **Stopped at exactly 15.** The board has 390 defensive slots and no player cap, so "set top-down
  until the map runs out" is tempting — but the 15 TW offense squads share no unit with these 15 by
  construction, and a unit on defense **cannot attack**. Placing #16 would come straight out of the
  attack phase. 15/15 is the plan, and it is now fully deployed.

## 2026-08-11 (03:20–05:00) — TW: 450 → 1,314 banners. The 15-squad cap was wrong, and the fleet territory was hidden
Owner asked to "add more competitive defense squads and fleets in TW to get over 1000 points". Same war
(season #3 vs *Galatic Republic*, setup closing ~20:45 Athens). Ended at **1,314 banners, guild #1** —
the runner-up is 380. Final: **37 character squads (×30) + 6 fleets (×34)**.

### ⭐ The banner economy, read off the territory panel (this is the whole game)
`Set Defense +30 Banners · Offense Win +6-20 · Conquer +840`, and **`6000 Power Minimum`** per squad —
a G13 squad is ~150,000, so the minimum never binds. Two consequences the last session got wrong:
- **Defense pays MORE per squad than offense** (30 flat and guaranteed, vs ≤20 and only if you win).
  A wall is not a sacrifice, it is the higher-paying use of a unit that would otherwise idle.
- **A FLEET pays +34, not +30.** That is why other players' totals are not divisible by 30
  (368 = 10×30 + 2×34, 308 = 8×30 + 2×34). Fleets are the best banner-per-slot on the board.

### ⭐ "Stop at 15" was wrong — and the reason is a DATA limit, not a roster limit
The previous entry stopped at 15 to protect the attack phase. But the 15 TW offense squads only use 70
units, and Astra has **171 idle G13 characters** on top of both banks. The real ceiling was the source:
`/gac/squads/` is a **top-100-by-usage** table, 82 of which Astra can field, and after the board solve
takes its cut only **4** unit-disjoint lineups remain. Lowering `MIN_SEEN` to 0 adds exactly one.
**`scripts/tw_wall.py`** fixes this with a second, coarser-but-still-grounded tier:
- TIER 1 — the 4 leftover lineup-table walls.
- TIER 2 — **leader-level**: swgoh.gg's defense tier list ranks 100 leaders and **45 of them are idle**
  here. Leader order comes from the tier list; the 4 allies come from swgoh.gg's own category tags,
  **rarity-weighted** so a shared "Phoenix" (7 units) beats a shared "Rebel" (52). Nothing is hand-picked.
That yields **22 more squads** (110 units, verified disjoint from both banks), still leaving 60 idle.
Attack-only GLs stay off the wall (`ATTACK_ONLY_GLS`) — JMK reads 2.7% hold in Kyber-D1 and is worth
far more attacking. Same doctrine applied to fleets: **Leviathan / Executor / Negotiator held back**.

### ⭐ AIRSPACE FORTIFICATION is the fleet territory — and the HUD hides it
Ten territories, all named `<x> Fortification`; nine are ground. The tenth is **Airspace**, and on the
zoomed-out map its `n/39` label sits **behind the "Setup Phase: 16h38m" HUD text**, so it reads as an
unlabelled shield. That is why the previous session concluded there were no fleets. Entering it, the
header changes to **`Set Defensive Fleet (+34 Banners per Fleet)`**.

### The placement flow, and the four gates that stop a script
No API exists: **HotUtils' whole `/tw/*` section (Current, Planning, Scouting) is Patreon
Habanero-gated** and Astra is Chile, so `TW_DEFENSE` in `apiRights` is not reachable. Drive the device.
- **Squads** — `scripts/tw_place.py`. `SET DEFENSIVE SQUAD → SELECT SQUAD → tap header row → SET`.
- **Fleets** — `scripts/tw_fleet.py`. `SET DEFENSIVE FLEET → SELECT YOUR CAPITAL SHIP → any capital →
  SELECT FLEET → tap header → SET`. ⭐ **The preset OVERRIDES the capital you picked in the modal**, so
  the modal choice is throwaway. Fleet presets can't be pushed by API (combatType 2 rejected) but the
  **`Fleets > Main` tab already holds 9 hand-built lineups** — Leviathan, Executor, Negotiator,
  Executrix, Finalizer, Endurance, Home One, Raddus, Malevolence (no Chimaera).
- **Gate 1 — `REMEMBER TO SAVE UNITS`** ("units do not refresh") appears once enough of the roster is
  committed; it did NOT show for the first four placements. Its SET just continues.
- **Gate 2 — `Max Capacity Reached`** at **39/39**. The cap is GUILD-wide and first-come, not per
  player: Forward Turrets went 20→39 during the run with guildmates filling it too. Move territory.
- **Gate 3 — "attempting to set a squad on defense that is not full"** for a short lineup (Malevolence
  is a 6-ship meta lineup). **OK only DISMISSES — you must press SET again** to actually set.
- **Gate 4 — pushing presets kicks the game client.** `squads/game/set` while the client is open
  raises **`CONNECTION LOST` — "another device has logged into this account"**. Push first, then RELOAD.

### Automation gotchas worth keeping
- **`/tmp` is sandboxed away from the Bash tool** — tesseract reported "image file not found" for files
  Python had just written there. Scratch goes to `~/Downloads/…` (or `output/`).
- **tesseract reads nothing off this UI raw**: crop → 2× → `point(p>thresh)` to hard black-on-white.
  Thresholds differ per element (140 for list rows, 170 for the white screen titles).
- ⭐ **Match list rows by NAME, never by the `Wnn` prefix.** The squad icon left of the name OCRs as a
  digit, so `W21` comes back as `W221`; a number-based seek reads that as "overshot" and oscillates
  until it gives up. `wall_order()` matches the normalised lead name instead.
- Screenshot taken mid-scroll OCRs to nothing — retry the read before deciding to scroll again.
- The first tap on a freshly drawn screen intermittently does not register. Drive by **reacting to what
  is on screen** (`open_fleet_builder`), not by assuming a fixed tap sequence.
- **Verify with STATS ÷ banner value**, not by counting taps: `own total = 30·squads + 34·fleets`.

### State left for the attack phase
- Placed: **Forward Turrets 39/39** (D12-D15 + W01-W18), **Trenches** (D09-D11, D03, W19-W22),
  **Airspace 19/39** (6 fleets: Malevolence, Raddus, Home One, Endurance, Finalizer, Executrix).
- Held back deliberately: the **15 TW offense squads**, **60 idle G13 characters**, the **3 offense
  fleets** (Leviathan/Executor/Negotiator), and **all datacrons** (still unattached — single-use per
  war, worth more converting a territory than propping a 4%-hold wall).

## 2026-08-11 (05:00) — ⭐ TW PLACEMENT DOCTRINE (researched after getting it backwards)
Owner: *"you placed the teams in the wrong areas… we should follow the meta in TW team placement."*
Correct. Both passes this night front-loaded the WEAKEST squads. This section is the rule; it
overrides every earlier "why front" paragraph in this file.

### The three mechanics the rule follows from (first-party + community, sourced below)
1. **The front gates the map.** "Territories behind the front territory will not be available to
   attack until a front territory is defeated." A front territory that holds means the enemy never
   reaches anything behind it.
2. **Back-row conquest pays the ATTACKER double** (base +450, doubled for back row; this map's panel
   shows +840). So the deep territories are the expensive ones to lose — but they are only reachable
   *through* the front.
3. **Attrition runs one way.** Units do not refresh. Whoever attacks the front spends their best
   squads there; whatever reaches the back is leftovers. A merely annoying wall holds against
   leftovers, and would be wasted absorbing a fresh top squad at the front.

### ⭐ THE RULE
**Strongest squads in the FRONT territories, progressively weaker toward the BACK. Filler NEVER
takes a front-line slot.** The 39-slot cap is GUILD-wide and first-come, so a front slot spent on a
2%-hold wall is a slot no guildmate can spend on a real one — the cost is guild-wide, not personal.
Secondary rules that survived the research:
- **Mix factions across territories.** Opponents scout the front before choosing a route; a
  one-faction zone tells them exactly what to bring.
- **Prefer AI-friendly kits on defense** (heals, taunt, TM control, revive, AoE that strips banners)
  over kits that need manual play, and **keep specific counters for offense** — they are worth more
  breaking their wall than sitting on ours.
- Fleets: the same front/back logic, in the single **Airspace** territory.

### How this map reads (blue = ours on the LEFT, enemy circle on the RIGHT)
Distance from the enemy circle is the front/back axis — rightmost is FRONT:
- **FRONT** (rightmost, both ringed orange): **Trenches** · **Forward Turrets**
- **MID**: Airspace (the fleet territory) · and the middle column
- **BACK** (leftmost): **Special Ops Center** · **Infirmary** · the rest of the left column

### What actually happened, and what it cost
W01–W18 (4.0% down to 1.6% hold) went into **Forward Turrets and filled it to 39/39**, and W19–W22
(3.2%–1.0%) into **Trenches**. That is the exact inverse of the rule, and it burned the map's most
valuable real estate on its cheapest squads — Forward Turrets is now closed to every guildmate.
**SET IS IRREVERSIBLE** ("You will not be able to edit the squad after it is set"), so it stands for
this war. The correction applied: the tier-3 filler **W23–W28 went to Special Ops Center (back)**,
11→18/39. Final **1,494 banners** = 43 squads ×30 + 6 fleets ×34, guild #1.

### For the next war, in order
1. Compute the bank (`tw_wall.py`) — it is already ranked by hold%, so the list order IS the
   placement order.
2. Place **W01 downward into the FRONT** territories until they are full, then continue into the
   mid column, and only put the unranked tier-3 filler in the BACK.
3. The graded 15 from `build_board.py` outrank everything in the wall — **D01 (42%) belongs at the
   front, not D15 (6%)**. Sort the two banks together before placing.
4. Datacrons still stay off defense (single-use, worth more converting a territory).

Sources: [swgoh.wiki Territory War](https://swgoh.wiki/wiki/Territory_War) ·
[Gaming-Fans TW defensive teams](https://gaming-fans.com/star-wars-goh/swgoh-guides/swgoh-101-territory-wars-guide/swgoh-101-territory-wars-guide-defensive-teams/)

---

## 2026-08-11 — Era events are Era-Level/relic gated, and the Riposte quest was never stalled

### "Gain Riposte 15 times" — the counter counts BUFF-GAINS, not battles
Three sessions read the counter as stuck. It was not: it read **13/15 → 14/15 → 15/15**, one gain per
battle that had a real Riposte granter on the field. The trap is that several owned units *look* like
Riposte sources and are not:
- **Count these:** Count Dooku (G13 R7/R8), Taron Malicos, Shin Hati — they grant the actual **Riposte** buff.
- **Do NOT count:** Ezra Exile / Mission Vao (LS counter-attack appliers, not Riposte) and **Cal Kestis**
  (his Riposte-flavoured buff does not register for the quest).

Recipe that closes it: **DS Battles 8-H (Starkiller Base), 10 energy, any squad containing Dooku, auto+4X.**
+1 per battle regardless of how fast the fight ends — the "overkill prevents the cast, shorten the squad"
theory was wrong and cost several wasted runs. Claim gives 5,000 Episode XP.

Two gotchas on that node's squad screen:
- The saved squad had **Jabba the Hutt (a "large unit")**. `BATTLE` routes to **Borrow a Hero** first, and
  a squad may not hold **both an ally and a large unit** — it raises *Large Unit and Ally Combination Error*
  at start. Drop the borrowed ally (or Jabba), not both.
- `GO` on the quest card is useless here: it jumps to **Light Side** 1-A, which cannot host a Dark Side
  Riposte squad.

### Era Challenge (Mara Jade) — you fight it with LOANED units, not your roster
`SELECT EVENT SQUAD` hands you Mace Windu / Barriss Offee / Kit Fisto **all at Era Level 40** plus the
mission unit **Mara Jade at EL 43**, one slot locked by "slot restrictions". **Astra's 14.4M GP is
irrelevant to this event** — that is why R7–R10 characters never show up and why the tier losses are not a
tactics problem. Feats are pure EL checks:
- Tier I: EL 23 ✅ / 29 ✅ / 35 ✅ / **45 ⬜** · Tier II: **EL 50 ⬜** (enemies EL 50).
- Third Tier II attempt this session: **DEFEAT**, all three enemies untouched.

**The only lever is the `LOANED UNIT ERA LEVEL INCREASE CALENDAR`** (Inbox → Daily Login Rewards). Day 14
(+1) claimed; **Day 15 is +2 — exactly the 43→45 needed for Tier I's last feat** — but it unlocks at daily
reset, and the event expires *before* that. Timing is the whole story: check calendar-day vs event-expiry
before spending attempts on an EL-gated feat.

### Call Answered Era Battle — a relic-depth wall
Tiers **I–III are 3/3 complete**. Tiers IV–VII are open and 0/3 but the *Allowed* list is only
**Colonel Ward / Snowtrooper Commander / Grogu & Anzellans**, held at **R4/R4/R5**. Tier VIII states the
real bar outright: *Rotta the Hutt at R10 and the other three at R9*. Victory counts are **NOT SHARED**
between tiers. Nothing here is winnable without relic investment in three units that exist only for this
event line.

### Mara Jade Character Quests are shard-gated, not objective-gated
Every objective is already finished (`Defense Down 10/10`, `250K/250K damage`, …) and every `CLAIM` is
greyed with **"Requires 165 Shards" / "170 Shards"** against **140/330 held**. `GET SHARDS` is the
1,299-crystal path. Free drip: **August login calendar Days 14/17/21/26 = 12/14/16/18 shards.** So the
first claim unlocks around Day 17, not by playing.

### Kessel Run rewards need the website
Inbox "Unclaimed Kessel Run Rewards (From Capital Games)" is **not claimable in-game** — "Visit the Website
to claim them", 29d 13h left. Needs a browser login, so it stays a manual/user step.

## 2026-08-11 (19:20–20:00 UTC) — full mod pass: one ladder for three scripts, and calibration re-diagnosed
Owner's ask: *"τρέξε όλα τα mods, κάνε όλα τα upgrades, και δες το optimal allocation πρώτα Arena, μετά
Grand Arena, μετά Territory Battles και Territory Wars."* Session id captured via **Playwright MCP**, not
chrome-devtools (see gotcha below).

### ⭐ THE LADDER IS NOW ONE OBJECT, AND ALL THREE MOD SCRIPTS READ IT
`invest_plan.py` already owned the priority ladder and wrote it to `output/invest_plan.json`
(`mod_priority` = ordered baseIds). But `execute_upgrades.py`, `calibrate.py` and `slice_plan.py` each
rebuilt their OWN defense/offense/other buckets out of `gac_result.json`. Two real faults, not cosmetics:
- **TW units were invisible to all three** — they are not in `gac_result.json` at all.
- **The Arena datacron five were ineligible for calibration.** Mob Enforcer / Greedo / Gamorrean Guard /
  Cad Bane sit at ladder ranks 1–4 and pay a crystal reward EVERY day, and `calibrate.py` could not see
  one of them. All three now key off `mod_priority`. Rank once, filter many times.

### ⭐ TB moved ABOVE TW in the ladder (rung 8), per the owner's stated order — and it is INERT
`ROTE_TIER` 11 -> 8, TW -> 9/10, GAC fleets -> 11. **This changed nothing today**: the rung needs
`output/rote_plan.json`, which needs `data/rote/operations_<phase>.json` scraped off the device while a
TB is running. Neither exists, so tier 8 is empty (`priority tiers:` prints no T8) and the live ordering
is still Arena -> GAC -> TW. That is also why the swap was safe to make during a live TW.
**To switch it on: capture the operation panels on device.** Until then, do not claim TB is being ranked.

### ⭐⭐ A 6-DOT SLICE STEP IS A MULTI-MATERIAL BUNDLE, NOT ONE TIER'S SALVAGE
Measured on a live before/after diff of ONE successful step (Cad Bane 6C->6B):
**T06_01 ×10 + T06_02 ×20 + T06_03 ×10 + T05_05 ×10 + T05_06 ×10.**
The old per-tier model in `execute_upgrades.py` ("step from tier t costs T06_0t") is WRONG — every step
also eats the lower tiers. This is why the plan said "2 mods to 6A, affordable" and the server refused
both: **T06_02 went 21 -> 1 on that single step**, and 20 is the per-step requirement.
⇒ **T06_02 = 1 is the hard gate on ALL 6-dot slicing.** Nothing more is possible until Mod Battles farming.
⚠️ `"Not enough player currency!"` does NOT name the material. The executor's `OUT [T06_04]` label was a
guess from the step's tier and was wrong — the real shortage was T06_02. Diff, don't believe the label.

### ⭐ 5-dot slicing: ~22 salvage per step, and it was the whole session's headroom
512/499/514/535 of T05_01..04 bought **89 steps** and drained all four to 7/14/14/10 — so ~22–23 salvage
per 5-dot step, roughly uniform across tiers (the old 10 estimate was 2× low). Credits −3,753,000 for 90
steps. **15 mods reached 5A** (638 -> 653). They now strand: promotion needs 76 T05_06 and only 39 remain.

### ⭐ ALL-OR-NOTHING beats greedy on the 6-dot phase
The first rewrite let each mod climb as far as materials allowed, priority-first. That handed rank-1 Mob
Enforcer a single 6E->6D step it could never finish and spent the scarcest material (T05_06) on a partial
that still cannot be calibrated — 6A is the only tier calibration accepts. Committing only to runs that
REACH 6A doubled the plan's output on identical materials: **95 -> 97 projected instead of 95 -> 96.**
The 5-dot phase keeps the greedy walk on purpose — its four budgets are independent and abundant.

### ⭐⭐ CALIBRATION WAS AIMED AT THE WRONG MODS FOR 18 ATTEMPTS
Cumulative record is now **0 hits in 18 attempts** (0/10 before, 0/8 today). That is not bad luck, it is
the metric. A reroll **re-samples** the secondary, so it regresses to the mean: a 6-dot speed roll lands
in 3..6, i.e. **~4.5 expected per roll**. The old ranking used `headroom = rolls*6 - spd`, distance from
the MAXIMUM — which preferentially selects **high-roll mods, and a high-roll mod is usually an already
lucky one**. Every mod rerolled today sat at or above its expectation, so every attempt was negative-EV
by construction, and all seven came back lower: 23->20, 24->19, 25->21, 19->14, 23->18, 18->12, 24->18.
- New metric in `calibrate.py`: **`deficit = rolls * 4.5 - spd`**, and only reroll a positive deficit.
- **Only 9 of the account's 76 eligible 6A mods have one.** Calibration is a much smaller lever than the
  attenuator stock suggests — 164 attenuators went to 9 for zero gain.
- Best remaining targets when attenuators are refarmed: Leia Organa spd19/5 rolls (deficit 3.5),
  Fifth Brother spd11/3 (2.5), Threepio & Chewie spd21/5 (1.5), Visas Marr spd21/5 (1.5), 50R-T spd17/4 (1.0).

### Session numbers (before -> after, `mod_score.py` either side)
| | before | after |
|---|---|---|
| modScore | 2.84 | **2.85** |
| plusSpeed | 16,672 | **16,682** |
| speed15 / speed10 | 321 / 555 | 322 / 556 |
| 6A / 6-dot | 95 / 145 | 95 / 145 |
| 5A (equipped) | 638 | **653** |
| credits | 144,911,832 | 141,158,832 |
| attenuators | 164 | **9** |
Sliced 89 5-dot steps + 1 6-dot step (Cad Bane 6C->6B). 0 promotes (T05_06 39 < 76). 0 calibration hits.

### NO placement re-run — and this is the grounded answer to "optimal allocation"
Every mod touched today was **already equipped on the right character**; slicing improves a mod IN PLACE,
so nothing today implies a move. The live placement is still the 2026-08-08 apply, whose order was
`datacron five -> climb -> fleet crew -> GAC` — i.e. **already the Arena-first ladder the owner just
restated**. A Grandivory re-run costs ~1,473 moves / **~7.4M credits** and the best any ordering measured
was **+0.12%**, inside the noise. ⇒ Placement is aligned; do not churn it. Revisit only when T06_02 and
attenuators are refarmed enough to change the inventory, or when the TB rung goes live.

### Gotcha: chrome-devtools MCP was NOT available this session — Playwright MCP works
`browser_recipes.md` §4 says chrome-devtools for HotUtils. Only Playwright MCP was loaded. It works, with
one difference: **its profile has no Discord session**, so `prompt=none` silent SSO bounces to the Discord
login page and the OWNER must log in by hand once in the visible window. After that,
`browser_network_requests` filtered to `api\.hotutils\.com` + `browser_network_request(part:"request-body")`
yields the `sessionId` exactly like the DevTools panel did. `apiuserid` is unchanged and still stable.

### The farm-then-spend loop is now one command (`scripts/mods_session.sh`)
Owner's follow-up: *"keep what we need for when we farm and when we have mats available, use them."*
- **`HU_SID=<live> ./scripts/mods_session.sh [--dry]`** — refresh ladder → pull → score → slice/promote →
  calibrate → re-pull → **measured before/after delta table** → refreshed queue → next shopping list.
  **Idempotent and self-limiting:** on an empty stock every executor stops on rc2 and nothing changes, so
  it is safe to run after any farming trip without checking first. Validated live on an exhausted account
  (0 steps, 0 spend, clean rc2 stop on calibrate, all deltas +0).
- **`scripts/execute_upgrades.py --needs N`** — the shopping list. Sizes the ask for the next N mods in
  ladder order IGNORING stock, then subtracts stock so the shortfall is explicit, with the farm source
  next to each shortage. **For the next 20 (all ARENA rung): 979× T05_06 and 819× T06_02 short**, plus
  373× T06_03 and 95× T05_05; PROMO (494), T06_01 (963) and credits are already ample.
  ⇒ The farming target is unambiguous: **T06_02 and T05_06, Mod Battles Sector 9 / Guild Store /
  Episode Shipments**, and Micro Attenuators from **Smuggler's Run 2 (Jabba)**.
- Measured constant now encoded: **~41,700 credits per tier-step** (3,753,000 over 90 steps).
- ⚠️ The T06_04 line is missing from the bundle because the one measured step was 6C->6B. Notes from
  2026-07-27 say 6B->6A also draws ~15× T06_04, so the shopping list under-states that one item.

## 2026-08-12 (03:05–03:20) — GAC defense: the browser's last-used tab nearly set GL Leia as a WALL
Picked up mid-flow: the device sat on `SELECT NEUTRAL SQUAD` with **GL Leia + Threepio & Chewie +
Captain Drogan + R2-D2 + Admiral Raddus** staged and a live SET button. That is **O01, the 96%-win
offense squad** — one tap from being frozen onto defense for the whole round.

### ⭐ Root cause: SELECT SQUAD opens on the LAST-USED TAB, and it was `GAC 5v5 - Offense`
`O01 GL Leia` is the first row of that tab, so a single blind tap on the top row stages the offense
squad. Always confirm the sidebar tab (`GAC 5v5 - Defense`, y≈519) *before* tapping any header row.

### The board was 13/14, not 14/14 — and the missing squad was NOT the one the plan named
One `Character Territory` read **3/4** ("You have unused defensive slots", red dot on the zone).
The in-flight plan said to place **D02 Q Amidala**; D02 raised RESTRICTED CHARACTERS, i.e. it was
already committed. Walking the whole tab found **D01–D06 and D11 restricted, D07 free** — so
**D07 Saw Gerrera** (20.0% hold, Power 142,890) was the squad the board was actually missing. Placed
it; zone went to **ALLIED SQUADS 4/4** and the board back to 14/14. D08–D10 were left untested
because all three sit at ≤19% hold and could not have beaten D07 anyway.

### ⭐ Three traps, all hit live
- **`RESTRICTED CHARACTERS` is the availability oracle in GAC too** (same as TW). Tapping a preset
  header either loads it or raises the popup; nothing else on screen tells you.
- **The maroon name-plate under a portrait is NOT a deployment marker.** It looked like one (D01 all
  five maroon, D10 all five maroon) and a pixel scan built on it returned "D04 all free" — D04 then
  raised RESTRICTED. D02 showed 2/5 maroon yet is fully committed. Ignore the plate; use the popup.
- **The popup DIMS the whole screen, so the top-left title OCRs to noise.** A detector that asks
  "did we leave INVENTORY?" first reads the dim as success and reports a restricted squad as LOADED
  (it did, for D03). **Check for the popup FIRST**, then confirm arrival by OCRing `Squad Power:`.
- Verification fingerprint: staging-screen **`Squad Power` == sum of the roster's `gp`** for the five
  units (D07 142,890 vs 142,868 computed). Deployed squads read a few thousand higher — datacrons.

### State left
- **GAC**: 14/14 (4/4 + 3/3 ships + 3/3 + 4/4). **Round 1 starts in 20h24m**, so defense is still
  editable — GL Leia is back in the free pool and available for offense.
- **Open question for the rebuild:** the four squads in that zone read 188,714 / 154,725 / 158,887 /
  142,890, and only D07's matches a preset exactly. Datacron power explains part of it, but it was
  not proven that the deployed board *is* the graded bank. The preset oracle is gone once every zone
  is full, so re-check at the START of the next round, before any slot is filled.
- **TW (Jakku)**: not empty as an earlier note in this session said — Astra is **#1 with 1,776
  banners** (runner-up 916), front territory 39/39, second 14/39. Setup closes in 17h22m.

## 2026-08-12 (17:30–19:15) — TW attack phase, and what a published win% does NOT tell you
Picked the war up in its attack phase (3h28m left, guild 15,347 v 14,148). Six attacks: **3 wins for
+51 banners, 2 losses, 1 abort**. New tool: **`scripts/tw_attack.sh`** (`list` / `target Y` / `go Y` /
`fire`) — it stops at the two decisions the screen has to answer and scripts everything between.

### ⭐ TW units are NOT single-use — each carries its own use cap, printed on the portrait
The squad-select tiles read `0/3`, `1/2`, `1/1` under the green icon: **uses spent / uses allowed**,
and the allowance **differs per unit**. This is the whole reason preset after preset failed — Astra
had already spent most of the roster earning those 1,776 banners. Do not model TW like GAC.

### ⭐ The RESTRICTED CHARACTERS popup is the ONLY availability oracle — the plate colour lies
Re-confirms the GAC note from 03:20, now for TW. The maroon name-plate looked like a perfect
"spent" marker across O01/O02/O03/O04 — and then **O07 Gungans, with clean grey plates, still raised
RESTRICTED**. Conversely nothing on the tile predicts it. `tw_attack.sh go` therefore gates on a
green-pixel probe of the BATTLE button and auto-taps CANCEL when the popup appears, so a dead preset
costs ~8s instead of attacking with whatever was staged before.

### ⭐ swgoh.gg's offense win% is measured against ALL defences, not against a GL wall
This zone was 28 GL walls (JMK r7-8, GL Rey r7-8, 165–190K). Results, and they are not subtle:
- **coherent GL squad + its real support wins**: O03 SLKR → GL Rey wall **+19**; O02 GL Ahsoka →
  JMK wall **+19**.
- **a GL with filler bodies loses**: hand-built SEE + JK Cal + Mando + Kylo Unmasked + JK Luke
  (193,800) went **0-for-5** against a GL Rey r8 wall. A GL's leader ability does nothing for units
  outside its faction, so "high squad power" is a mirage.
- **a high-% non-GL squad loses**: O06 Malgus, rated **86%**, also went 0-for-5 to a GL Rey wall.
- **against a non-GL target the filler squad is fine**: hand-built JMK + Bane + Wampa + Maul +
  Bo-Katan (210,419) beat `jaba est` (125,587 Hutt/Nikto) for +13.
⇒ Read the target before picking the squad. Against a GL wall only a coherent GL squad is worth the
uses; save the loose parts for the sub-130K stragglers, which is where the soft targets hide (scroll
the enemy list — the top rows were all 165K+, the 125K one was ~20 rows down).

### Banner arithmetic worth remembering
`Victory +5` · `First Attempt +10` · `Second Attempt +5` · `Surviving Units +1 each`. So an untouched
squad is worth ~10 more than a chewed one — always prefer a `Battles: 0` row.

## 2026-08-12 (19:00) — Assault battles: a loss does NOT burn the attempt
"Secrets and Shadows" (Nightsisters/Phoenix). Tier I 3/3 collected; **Tier II 2/3 and Tier III 0/3
both lost on AUTO** with the game's own auto-fill (Great Mothers lead + Captain Rex + Merrin + Night
Trooper + Morgan Elsbeth, 156,790) — T3 is **8 waves** and the squad folded around 4-5.
**After both losses each tier still displayed `BATTLE (1)`**, so retries are free and the only cost is
wall-clock. Two things to fix before retrying: Captain Rex is Phoenix and gains nothing from Great
Mothers' Nightsister lead (swap in a 5th Nightsister), and auto is the known failure mode for event
battles — drive it manually.

### Polling gotcha for multi-wave battles
The "is the AUTO toggle still green?" probe **false-negatives during wave transitions** (the HUD
blanks between waves), which ended a poll at wave 3/8 and reported the fight finished. Require
**3 consecutive misses** before believing the battle is over. Also note the Bash tool caps `timeout`
at 600000 ms, so an 8-wave fight needs its poll loop split across calls.

### Blocked, and why (all verified on device this evening)
- **Coliseum JOTAZ T4** — rank 249, high score 31,726 (61%), 60% milestone claimed. Attempts spent;
  the only refresh is **250 crystals**, which the standing rule forbids. Next boss in ~2h50m.
- **Yoda (Dark Side Vision)** — Marquee "A Dark Reflection". Tiers I-III done today (refresh 2h56m);
  **Tier IV is star-gated, not battle-gated**: needs 5★ and he is 4★ at 15/65 shards. Tier V needs 6★.
  Only other shard source is the crystal offer.
- **Order 66 / Battle for Naboo** — "Raid is not active", guild at **83.9K of the 180K** launch
  tickets. That also blocks Episode Quest "Attempt 2 Raid battles" (worth **5,000** track points).
- **Regular energy** — do NOT dump it. `Guild Activities 600/600` means today's ticket cap is already
  spent, so energy spent now buys **zero** tickets, and `invest_plan.md`'s gear queue is empty. Hold
  the 1,433 until the ~23:25 reset, then put 600 into tickets — that is the one thing that actually
  moves the guild toward launching the raid.

## 2026-08-14 (01:45–02:40) — ⭐ COLISEUM SOLVED: Krayt Dragon T4 100%, and maxing a tier UNLOCKS the next
Session ask: "research current meta, play optimal". Started on **Krayt Dragon T4, rank 175,
73% (44,332), 3 attempts**. Ended **T5 rank 120**, having maxed T4 and opened T5. The whole gain came
from research, not from a stronger roster — the squad was loaned units the account already had.

### ⭐ Maxing a tier unlocks the NEXT tier AND refills attempts
This is the single most valuable fact in this note. Hitting **100% on T4** immediately flipped the
screen to **TIER 5 REWARDS with BATTLE (5)** — a brand-new reward ladder and a fresh set of attempts.
So the tier hexagon (`4`, `5`) is a *progress indicator, not a selector*: tapping it does nothing.
⇒ **Never stop at "milestones claimed". Max the tier and the game hands you a new one.**
Rank moved 175 → 142 (T4 max) → 120 (T5 43%) in one sitting.

### The grounded meta (holotables.xyz/boss/<boss>, filter Tier + "only squads I can run")
`holotables.xyz` is the Coliseum equivalent of swgoh.gg for GAC: community-submitted squads per boss
per tier, with reported %, MANUAL/AUTO flag, and written strategy notes. **WebFetch gets 403 — drive
it with the Playwright MCP browser.** Its two-letter codes: JK=Jedi Knight Luke / Jedi Knight Cal
Kestis, MJ=Mara Jade Skywalker, CL=CLS, C=Chewbacca, Q=Qi'ra, MW=Mace Windu, DT=Dark Trooper,
T&=Threepio & Chewie, Y(=Yoda (Dark Side Vision) — the notes call Yoda "soda".
**T4 100% lineup used (Danduan, and it worked first try):**
`JKL (leader, Return of the Jedi) · JKCK · Mara Jade · Qi'ra · CLS` — all loaned at **EL 46**, Mara
own 4★ EL 48. Community hit 100% at EL 32-40, so EL 46 is comfortable margin.
**MANUAL is not optional:** community AUTO tops out ~57% at T4 where MANUAL hits 100%.

### ⭐ Krayt Dragon kit — read the in-game Event Info (`i` → Bosses → KRAYT DRAGON), it is the real spec
- **Apex Predator**: takes **30% less damage while it has buffs**; deals **+30% damage while it has
  ≤3 debuffs**. ⇒ two independent reasons to strip its buffs and hold **4+ debuffs on it at all times**.
- **Violent Eruption** (granted by Dune Burrow): AoE, **−5% damage per debuff on the Krayt, max −50%**.
  This is what kills the squad. At T5 it wiped 3 of 5 because the debuff count was too low when it fired.
- **Dune Burrow**: dispels its own debuffs, −40% Speed, **+50% Defense (a dispellable BUFF)**, cannot
  counter, immune to TM removal.
- **Roar Of The Crowd**: damage it deals rises and damage it takes falls **as points are earned**
  (hard diminishing returns — late hits score far less than early ones). Enrage after **10 consecutive
  player turns — but 20 while it is burrowed.**
  ⇒ **⭐ The exploit: turns taken while it is underground are half-price.** Spend the turn-chain there.

### The turn-by-turn line that produced 100% (repeat it)
Openers, before it burrows: **Mara basic** → **CLS basic** (Speed Down) → **Qi'ra assist-call**
(slot 3, target Mara) → basics → **Cal basic** (it is a BASIC, no "Reusable in" line: Speed Down on
ALL enemies + Advantage to all allies + Stun) → **JKL special 1** (slot 2, calls Cal — only if Cal is
**not Dazed**) → **Mara special 2** (slot 3, turn meter).
**The moment it burrows** (tell: a **6th ability icon appears** = Violent Eruption granted, and its
head leaves the field): **CLS Call to Action** (slot 3 — dispels debuffs on Luke, **+100% TM = an
immediate extra turn**, +25% HP, +50% Accuracy/Crit) → **CLS Use the Force** (slot 2 — **dispels the
50% Defense buff** and lands **Tenacity Down**, which makes every later debuff stick) → **Qi'ra
Scattering Blast** (slot 2 — dispel + Stagger) → **JKL special 2** (slot 3, Vulnerability) → basics.
Biggest single jumps measured: JKL-calls-Cal **+9,400**, Qi'ra-calls-Mara **+5,300**.

### Gotchas paid for in real turns
- **Daze blocks assists.** At T5 the opening venom spray Dazed 4 of 5, so every assist-caller was dead
  weight until it wore off. Check for the spiral icon before spending an assist ability.
- **Chain-locked ability icons = Ability Block**, not cooldown (cooldown shows a number). Only the
  basic is usable; do not waste calls probing.
- **The ability bar is right-aligned and re-flows with the count.** Measured this session at y≈985:
  4 abilities → x = 1339/1503/1666/1830 · 3 → 1503/1666/1830 · 2 → 1666/1830.
  (An older note said 1245/1545/1845 for three — that spacing was wrong here.)
- **Adding a unit to a squad re-flows the whole selection sidebar**, so a position read before the add
  is stale. Re-crop after every pick.
- **The green person-icon fraction is a live synergy oracle** and it updates as you build: Mara read
  **0/1** next to the old Sith squad and flipped to **2/2** once JKL was in. Cal read 2/2. Use it.
- `scripts/turn.sh` (new) stacks score-HUD + squad bars + ability bar into ONE image, so a manual turn
  costs one Read instead of three. `./scripts/turn.sh X Y [wait]` taps then looks.

### State left
- **Krayt Dragon T5, rank 120, high score 39,306 (43%), 4 attempts unspent**, boss rotates ~18h from
  02:40. T5 max ≈ 91,400. Milestones banked this session: T4 80/90/100%, T5 10/20/30/40%.
- To beat 43% on T5 the fix is explicit: **hold 4+ debuffs on the Krayt when Violent Eruption fires.**

## 2026-08-16 — GAC REBUILT ON BANNERS AND ZONES. The old objective was the bug.
Owner: "we are doing the setup wrong in Grand Arena." He was right, and the cause was not squad
selection. Root-caused from Astra's own match data (HotUtils `gac/get`, 6 matches) plus an 11-stream
research sweep. **Everything below is either first-party or measured off the live account.**

### ⭐ THE MAP IS TWO GATED LANES (verified live, then reproduced in 6 past matches)
`4zone_5v5_ga2_c3s1_82a` zones, read from `gac/get`:
| zone | zoneId | phase | location | fleet | slots 5v5 / 3v3 |
|---|---|---|---|---|---|
| front_top | `4zone_phase01_conflict01_duel01` | 1 | 1 | no | 4 / 5 |
| front_bottom | `4zone_phase01_conflict02_duel01` | 1 | 3 | no | 4 / 5 |
| back_fleet | `4zone_phase02_conflict01_duel01` | 2 | 1 | **YES** | 3 / 3 |
| back_bottom | `4zone_phase02_conflict02_duel01` | 2 | 3 | no | 3 / 5 |

**A phase-2 zone scores 0 until the phase-1 zone at the SAME `location` is fully conquered.** Not
folklore — in every one of six matches the back zone read `state:1, score:0` exactly when its front
still had a squad standing, and `state:3+` the moment it did not. Fleets are a BACK zone (behind
front_top), which is why Astra kept scoring zero in the fleet territory.

### ⭐ THE SCORING MODEL (first-party; `scripts/gac_score.py`)
Per battle: Victory 15 · First Attempt 30 (2nd 10, 3rd+ 0) · Surviving/Full-HP/Full-Prot/Defeated-Enemy
1 each · **Unused Slot 4** · First Attack 10 once. Max = `45 + 5*slots - units_deployed`.
Territory conquest = **120 + 30/squad (5v5), +28 (3v3), +33/fleet** = **47% of the entire score**.
Ceilings **5v5 1915 / 3v3 2131**. ✅ The 3v3 number is confirmed by HotUtils printing "Your max: 2131".
- **The defender earns ZERO banners.** The community `setSquadDefenceBanners=90` constant is stale GA1
  and is arithmetically impossible against Astra's own 966-banner round.
- One hold in a FRONT zone denies 657-696; in the back, 210-219. **2.7x.**

### ⭐ WHERE THE ROUNDS ACTUALLY WENT (Astra's own numbers)
Mean conversion **37% of available banners**. Per round, ~493 banners locked behind a front zone left
at n-1 of n, and ~731 sitting in zones that were OPEN and never attacked.
- S81 vs Drew, lost 966-1165: **one** surviving enemy squad in front_top cost 755 (57 battle + 260
  territory + 438 fleet territory it kept locked). Opening that lane alone wins the match by ~250.
- The fleet territory scored **0-31 banners in 6 of the last 10 rounds**.
- S82 R2: Astra threw **seven** squads at one wall (`successfulDefends: 7`). Attempt 3+ pays 30 fewer
  banners and the units are spent win or lose. ⇒ hard rule: two attempts, then walk.

### ⭐ WHAT CHANGED IN THE PIPELINE
- `gac_score.py` NEW — banner constants, zone topology, lane values, ceilings.
- `gac_place.py` NEW — exact partition search over zone assignments, minimising expected banners
  conceded, with the lane conditional priced properly. **Honest sizing: placement is worth ~3-5 banners
  over a rank-order fill and ~130 over the worst case. It is cheap to get right and it is NOT the win.**
- `gac_attack.py` NEW — the attack ROUTE against the live opponent board: rank lanes by
  `P(conquer front) x prize behind it`, Hungarian-match our squads onto their squads on log P(win),
  finish one lane before starting the other.
- Objective swapped from `SUM Hold% + SUM Win%` (two incommensurable quantities) to **banners**, using
  swgoh.gg's `banners` column, which the repo had been scraping and discarding since day one.
- `RELIC_BASELINE=8 / RELIC_PER_LEVEL=0.045` NEW — published rates are population averages; Astra's
  copy is often 1-3 relics below. This alone demoted the Traya team (pub 87%, relic x0.66) from #4
  offense to #14, and Bad Batch (x0.56) off the board.
- Bench 6 -> 12, and `BENCH_MIN_SEEN=800`: 5v5 offense 14 -> 20 squads for 14 required wins.

### ⭐ DOCTRINE CORRECTIONS, EACH WITH ITS EVIDENCE
- **SLKR walls in 5v5.** SLKR/Dark Rey/Sith Trooper/Hux/KRU is the **#2 wall at Kyber, 47.0% hold
  (n=7,200)** and Astra had never placed it. Nothing is stranded — the wall and the attack squad are
  the same five. `CORE_ALLOW` lets it past MIN_SEEN.
- **Mace Windu is reserved for JMK** (`RESERVE_OFF_UNITS`). JMK is the only 79% answer Astra owns to an
  enemy Stranger; the solver kept spending Mace on the Queen Amidala wall for two more banners.
- **Queen Amidala/GMY/Mace haircut x0.65.** Its 37% was rented from the Mace L9 datacron, which died
  with Set 30 on 2026-08-06 and has no replacement. Kyber-D1 reads 23.8%. The board now runs the
  Shaak Ti build instead.
- ⭐ **THE ROTTA WALL WAS MISSING ENTIRELY.** Rotta the Hutt / Gamorrean Guard / Greedo / Cad Bane /
  Mob Enforcer is the **#1 defensive DATACRON in the game (41.3% Kyber-D1)** and Astra owns the focused
  cron **at max, L15/15**, plus all five units. swgoh.gg files it on the datacron tier list, not the
  squad list, so `data/meta/*` has never contained it and the board could not see it.
  ⇒ `board_config.DATACRON_SQUADS`. FDCs have **no relic gate**, so no relic penalty applies to them.
- **Datacron coverage was 4 of 11.** The live opponent ran 8 of 8. Astra owns 8 L9 crons and had five
  sitting unused, including a set-33 L9 First Order / Kylo Ren (Unmasked) that maps exactly onto the
  SLKR wall. `datacron_assign.py` now takes the board from 284% to **367% of expected hold, +83 points**.
  ⚠ Set 31 (three L9 crons, two of them Old Republic for the Satele wall) **dies 2026-09-03**.

### Corrections to earlier notes
- **Astra is Kyber DIVISION 3**, set by SKILL RATING not GP (`divisionId: 15`; 25/20/15/10/5 = D1..D5).
  The old GP-based Division-1 claim is wrong. Scrape `league=kyber`, not `league=kyber-d1`.
- **The fleet hold ranking in `build_fleets.py` is built on the wrong statistic.** `/gac/ship-counters`
  gives per-counter-squad WIN rates (a selected sample of published counters), not Hold%. The real
  tier-list Hold% at Kyber: Leviathan 22.1 · Profundity 24.8 · Executor 15.0 · Endurance 14.4 (NEW, #1
  at Kyber-D1 and rising three seasons) · Home One 14.0 · Chimaera 15.9. Leviathan is the best owned
  DEFENSIVE fleet and is currently on offense. **Deliberately not changed:** Leviathan is also the only
  99% answer to Profundity, which the live opponent flies, and the failure mode being fixed is failing
  to CONQUER. The whole re-allocation is worth ~5-25 banners; Profundity is worth 456. Revisit after it.
- **Merrin's omicron is gated to "no Galactic Legends"** in GA since May 2026 — she is a dead body
  against any GL attacker. Nightsister Spirit is the catalogued fifth. (Moot: the Great Mothers wall is
  now off the board.)
- **Undersizing is +1 banner per empty slot, not more.** The measured "solo SEE 56.68 vs ~50" gap is
  mostly a higher win rate and a cleaner clear. Its real value is unit economy.

### Live state at session end
S82 (5v5) round 2 was live, Astra **1092 - 1738** vs Two Fists In The Wind (15.2M), max 1788. Top lane
fully conquered including all 3 fleets; bottom lane left at 3/4 with GL Ahsoka standing, which kept a
417-banner back zone locked. 108 definitions pushed to HotUtils (was 98) and 6 tabs pushed in-game,
defensive names now carrying the ZONE (`5v5 FT1 …`, `FB2 …`, `BB3 …`) so the board is placed where
`gac_place.py` intends. Backup of the previous board: `data/hotutils_backup/squads_before_20260816.json`.

### Open / next
- Instrument one full round (enemy squad, my squad, attempt, result, banners) and fit `ATTEMPTS` and
  the relic haircut from real data. Signal that the haircut is too mild: the #1 wall in the game took
  **0 successful defends** on Astra's live board.
- Scrape `/gac/counters/<LEADER>/` into `data/meta/counters_5v5.json` so `gac_attack.py` uses real
  head-to-head rates instead of its two-marginal model.
- Confirm the Profundity unlock in-game (every published gate reads MET off the live roster).
- Re-key the mod ladder to GAC OFFENSE characters — 145 six-dot mods equips ~24 units, the board needs ~110.

## 2026-08-17 — THE OFFENSE/DEFENSE SPLIT, SETTLED BY SIMULATION. The owner was right.
He pushed back on the 2026-08-16 board: *"too much on defense; keep the best teams for offense and do
the best we can in defense with GLs that are not good in offense and the rest of the meta teams."*
That is a claim about opportunity cost, not about Hold%, so it was measured rather than argued.

### The tool
`scripts/gac_doctrine.py` simulates a WHOLE ROUND, both sides, under N doctrines:
- defense → `gac_place.solve` (exact, gated) → banners conceded;
- offense → walk the enemy board lane by lane, Hungarian-match our squads onto theirs on log P(win),
  units single-use across the whole board, territory credited at P(all beaten in that zone), and each
  back zone's whole value multiplied by P(its front was conquered);
- run against TWO opponent boards: the captured live one and a synthetic top-of-meta Kyber board, so a
  doctrine is never chosen on one opponent.

### The result (5v5 net banners; absolute values are meaningless, the ORDERING is the answer)
| doctrine | net |
|---|---|
| A SLKR released to defense (what shipped 2026-08-16) | −523 |
| B the classic 5 attack-GLs are attack-only | −503 |
| C only Lord Vader + Jabba may wall | −483 |
| D no GL walls at all | −472 |
| **E every GL WITH an offense role attacks** | **−425** |
| F E but SLKR walls too | −471 |

**E wins by 65-87 banners at every ATTEMPTS from 1.5 to 4.0 in 5v5, and at every realistic value in
3v3** (it only loses at 3v3/ATTEMPTS=1.5, the "walls hold a lot" regime that Astra's own 14/14 wipe
contradicts). The trend is monotone toward offense, which is the signature of a real effect.

### Why defense loses the argument
A defensive squad earns ZERO and denies only against an opponent who would otherwise have taken those
banners. Against the live 15.2M opponent Astra's board denied exactly nothing — cleared 14/14. An
offense squad earns its banners AND can be the one that conquers a territory: +210-240, plus it
unlocks the entire gated lane behind it. The two sides are not symmetric and Hold% cannot see it.

### ⭐ THE ONE EXCEPTION IS A DATA FACT, NOT A JUDGEMENT CALL
**GL REY HAS NO OFFENSE ROW IN EITHER FORMAT** — not a weak one, none, in any meta file. Doctrine D
(no GL walls) therefore strands five G13 units, which is exactly why it loses to E by 47.
⇒ `ATTACK_ONLY_GLS_WITH_OFFENSE` = JMK, JML, SEE, SLKR, GL Leia, GL Ahsoka, Lord Vader, Jabba.
⇒ GL Rey is the only GL on the board, in both formats.

### Corrections to yesterday's entry
- **SLKR ATTACKS after all.** Yesterday's "SLKR walls, he is the #2 Kyber wall at 47%" was right about
  the hold number and wrong about the conclusion: doctrine F (E + SLKR walling) trails E by 46. SLKR /
  Dark Rey is a **96% TWO-unit clear in 3v3** (n=1,931) and 90% in 5v5, and freeing him deepens the
  bank that conquers lanes. `CORE_ALLOW` retired with it.
- The per-GL marginal table (offense banners vs wall denial + gate share) agrees for every GL except
  SLKR, where it says +11.9 for walling. The full-board simulation overrules it because the marginal
  table cannot see the global re-optimisation or the territory unlock.

### Board after the change
5v5 **11 def / 21 off** (was 20), defense sum 250% → 318% with crons.
3v3 **15 def / 26 off**, defense sum 180% → 206% with crons.
110 definitions live on HotUtils, 6 tabs pushed in-game. Defense holds fell, offense depth rose — that
is the trade, and it is the one the arithmetic endorses.

### Guarded by tests
`tests/test_gac_score.py` asserts (a) GL Rey is the ONLY GL allowed to wall, (b) she still has no
offense row — the single fact the exception rests on, and the thing most likely to change under a new
meta, (c) every defensive slot is filled and offense depth exceeds the required win count.

## 2026-08-17 (session 2) — GAC defense PLACED in-game, and the banner model confirmed first-party
Emulator driven via ADB. S82 Round 3 setup phase, opponent Law Craw (14.09M). R1 and R2 both LOST, so
this was the last round of the event.

### ⭐ THE GAME CONFIRMS gac_score.py, VERBATIM
The Character Territory panel prints, per zone: **"Offense Win: +16-69 Banners"** and
**"Conquer: +240 Banners"**. 240 = `territory_banners('5v5', 4)` = 120 + 30x4, computed independently
from the wiki table. 69 = `MAX_BATTLE['5v5']`. Also printed: *"You must earn at least 10 banner(s) from
any battle to qualify for rewards at the end of the round."* The model is no longer inferred.

### ⭐ CORRECTION: ASTRA IS KYBER 4, NOT KYBER 3 AND NOT "DIVISION 3"
In-game Championships screen: **Kyber 4, Skill Range 2970-3130, Your Skill Rating 3,128** — one point
under the band ceiling. So HotUtils `divisionId: 15` maps to KYBER 4. Both earlier readings (a GP-based
"Division 1", then "Division 3") were wrong. Division is skill-rating driven; league placements update
in 16d 22h.

### The map, confirmed visually
Two 4-slot CHARACTER zones nearest the centre line (the fronts), and behind them a 3-fleet zone and a
3-squad zone. Exactly the `gac_score.ZONES` topology. The fleet zone is unambiguously a BACK zone.

### ⭐ THE API READ WAS INCOMPLETE — CHECK CRONS IN-GAME
`gac/get` with `refresh:false` reported no datacron on most squads. In-game, The Stranger, GL Rey and
Rotta all already carried theirs (Lvl 9 / Lvl 9 / **Lvl 15 max focused**). Do not trust a non-refreshed
pull for cron state; the squad list in Edit Defenses shows it plainly.

### What was placed (14/14)
- **TOP-FRONT** Stranger (s32 cron) · GL Rey (s33 cron) · Rotta the Hutt (**s33 focused, L15 MAX**) ·
  Satele Shan (s31 Old Republic/Satele — all three tiers apply to all five)
- **BOTTOM-FRONT** Palpatine · Great Mothers · Queen Amidala/Shaak Ti (s31 Light Side: +15% max health
  and protection per other Light Side ally = +60% across the squad) · Grievous Droids (s31 Separatist:
  bonus turn on kill)
- **FLEET** and **BOTTOM-BACK** left as they were (3/3 each)
- **Lord Vader and Jabba pulled OFF defense** — the whole point of doctrine E; they are 39.8 and 47.4
  banner attackers.

### Judgement calls made at the device, both deliberate
1. **Rotta stayed in TOP-FRONT** instead of moving to bottom-front as gac_place wanted. Both are fronts,
   the swap was worth ~1 banner, and moving it risked detaching a maxed focused datacron. Not worth it.
2. **The fleet zone was left alone.** In-game it is Executrix + Home One + Endurance. By the CORRECTED
   Kyber Hold% (the tier list, not the counter win% `build_fleets.py` still uses) that reads
   7.0 + 14.0 + 14.4 = 35.4, versus the plan's Chimaera + Home One + Raddus = 15.9 + 14.0 + ~1.2 = 31.1.
   ⇒ **The live fleet defense is BETTER than what the repo would have set.** `build_fleets.py` needs
   re-basing on `/tier-list/fleet/?side=defense` before it is trusted again.

### UI notes for next time (saves a lot of taps)
- Edit Defense → zone → ENTER → **REMOVE SQUAD** (red X per squad) → DONE → **ADD SQUAD**.
- ADD SQUAD → **SELECT SQUAD** opens the in-game PRESET tabs — the ones `push_ingame_presets.py` writes.
  Naming them `FT1 …` / `FB2 …` / `BB3 …` means placement is just picking by name. That naming change
  paid for itself immediately.
- **ADD DATACRON** lives in the squad builder, bottom-right, and the picker states per cron whether each
  tier applies to the current squad ("No applicable bonus mechanics" vs lit portraits). Trust that over
  any offline scorer.

## 2026-08-17 (session 3) — ⭐ ECONOMY: where value per action actually comes from
Desk research (no device — battery). Everything here is sourced; the two things I *measured*
against this account's own data are called out, and one of them killed a change I had proposed.

### ⚠ The game changed under our notes: 2026-04-27 update
- **Mod Battles cut from 9 tiers to 2; Mod Challenges DELETED.** Chapter 2 == the old tier 9
  (slicing mats + Micro Attenuators), at a lower unlock level. 1–4 dot mod rewards removed.
  Our prose said "Mod Battles Map 9" in two places (now fixed); the *code* was already right —
  `farmbot/config.json` targets `chapter_tab_mod_2`.
- **Era Currency inflow +204% to +419%**, 40 extra free Era Levels, and **Era Level 135 converts
  to Relic 8**. Tier-4 Lightspeed Tokens cut 5,000 → 3,500 EC. This is a relic engine we do not
  currently track anywhere in the repo.
- Training-droid and Mk I–III ability-mat drop rates up; star promotion no longer costs credits.

### ⭐ Raid CADENCE is the R7→R9 supply line (the fix CLAUDE.md already asks for)
CLAUDE.md: *"27 units at R9+ vs their 60, 156 parked at R7. Stop adding R7s; convert R7→R9."*
The material for that comes from exactly one place worth using:
- **Mk III raid tokens are the only reliable faucet for R8/R9 mats** (Electrium Conductor,
  Zinbiddle Card, Aeromagnifier) and the best value for R6/R7. Mk III comes ONLY from raids.
- Raids are gated by tickets: **600/member/day, 1 ticket per 1 energy spent on anything except
  Conquest energy.** Free daily energy (240 normal + 120 cantina + 240 mod + 240 ship + 135/45
  quest bonuses) covers 600 with **zero crystals**.
- **Rule: never hoard energy for a higher Guild Activity tier at the expense of 600 tickets.**
  Raid rewards dominate guild tokens. `memory/session_state.md` recorded the guild stuck at
  **83.9K/180K, unable to launch Order 66** — that is the relic pipeline starving at the source.
- Crate scaling flattens: 15M guild score → 1,000 Mk III, 60M → 2,000. **Cadence beats crate-chasing.**

### Currency routing (spend each unit where it returns most)
| Currency | Best use |
|---|---|
| Guild tokens | Blue roombas (Mk 7 BlasTech) 10/150 → **33.3 Chromium Transistors**, best relic-salvage deal |
| Mk III raid | R6/R7 for value; **only** source for R8/R9 |
| Conquest | **Sector-1 jawa tradeable salvage** → Impulse Detectors + Gyrda Keypads (R8–R10). NEVER buy IDs/GKs directly |
| Episode (EC) | Omicrons → signal data/relic mats → **attenuators 16/4,000** + slicing mats 25/3,500. ⚠ hard cap 100k, overflow is burned |
| GAC | Kyrotech only; slicing mats acceptable second |
| Shard shop | G12 gear 360 shards/4 pieces; skip anything at 720 |
| Fleet arena | Ships/pilots, then **zetas exclusively** |
| Legend tokens | Omicrons only |
| Credits | All bronziums always, + the 4 random Featured Shipment gear pieces each refresh (→ bronzium wiring) |

### Mods — what the sources add, and what MEASUREMENT rejected
- **5-roll cap is real**: no secondary can roll more than 5 times. Verified against our own
  `data/mods_full_20260811.json` — across 2,330 mods `spdRolls` **never exceeds 5** (max speed per
  rolls: 1→6, 2→12, 3→17, 4→23, 5→26). A capped mod can never gain speed from another slice.
- ❌ **But do NOT teach `slice_plan.py` about it.** Measured: exactly **1 of 1,854** queued mods is
  speed-capped, and **0 of the top 40**. The change would have been pure complexity. Measure first.
- 5A→6E is deterministic (+2 speed on an arrow primary, +1 on a speed secondary) and is NOT
  subject to the roll cap — only within-tier slices roll a random secondary.
- Slice cheap tiers first (grey→green→blue→purple→gold); cull thresholds grey any-speed,
  green 1–2 hits, blue 2–3 (thr 8), purple 3–4 (thr 10), gold thr 10.
- Only level to 12 to reveal all 4 secondaries; 15 is needed only immediately before slicing.
- **Never let mod energy cap** — it stops generating at the cap. **Lock every 6-dot mod.**

### ⭐ `scripts/calibrate.py` — cost tier now beats ladder rank (CHANGED, tested)
Attenuators are the binding constraint and an attempt is priced PER MOD by prior rerolls
(1st ≥15, 2nd ≥25, 3rd ≥35) while the hit rate does **not** improve with rr. Ranking by
importance first quietly spent the stock on the few expensive mods. On the 2026-08-11 pull the two
top-ranked candidates are both rr=2, so with 86 attenuators the old order buys **3** attempts
(35+35+15=85) and the new order buys **4** (15+15+15+35=80). Rank still breaks ties inside a price
tier; `--by-rank` restores the old behaviour. Covered by `tests/test_calibrate.py` (8 tests).

### Per-mode rules worth keeping
- **Conquest: you may skip up to 34 keycards and still red-crate.** Read ALL feats before spending
  any energy — burning attempts before reading feats is the classic waste. Hold Boss attempts until
  the disk loadout is complete (Boss Feats are locked to that single battle).
- **Energy: spread wide, never refresh deep.** A node reset is 25c for ~1.67 expected shards; the
  same 50c buys 120 energy. Costs nothing to apply: run 5 attempts across two hard nodes rather
  than 5 + reset on one. Cantina: one character at a time, to completion.
- **RotE: deployment massively outweighs combat missions**, both alignments deploy on any planet,
  and **deployment has no relic minimum** (missions need R5→R6→R7 by phase). Relevant to the empty
  TB rung in `invest_plan.py`: there is a real argument for R9-ing platoon units over meta teams.
- **Episode Quests: 28 per episode, one revealed per day, and a missed day is EP gone for good.**

### ⭐ `datacron_exposure.SETS` was rotting by design — expiry is now a DATE
Datacrons changed in Jan 2026: **monthly releases, 3-month lifespan** (was bi-monthly/4-month),
**reroll costs for levels 4–6 HALVED**, fewer factions per set, and the datacron-currency cap
raised to **100M — so banking currency across a weak set is now viable**. Reroll ladder is
1–2 rerolls @200K, 3–4 @400K, 5+ @800K, with the 4–6 band halved. Focused Datacrons are the
no-gamble alternative: linear, exactly what's displayed, go to **level 15**, can't be rerolled
or dusted, one of each per player.
The repo bug this exposed: `SETS` carried a hardcoded `days` countdown read off swgoh.gg on
2026-08-05, so it was wrong the next morning — by 2026-08-17 it still listed **set 30 as live
with "1 day" left, eleven days after it lapsed**, handing every Sith and Galactic Republic squad
a phantom expiry haircut. Now `expires` is an ISO date (kept a string: `build_board.py` dumps
this table into `board_result.json`) and `days_left()`/`live_sets()` derive the countdown, with
`today` injectable. Live today: 31→17d, 32→45d, 33→73d. ⚠ Still needs a human when a set lapses —
`live_sets()` drops the dead one but cannot invent its replacement; next set due ~2026-08-26.
Covered by `tests/test_datacron_exposure.py` (7 tests).

### Omicrons — use measured impact, not popularity
**swgoh4.life/omicrons** ranks omicrons by *measured* GAC offense/defense impact from swgoh.gg's
Kyber 1&2 insight data, not opinion. The gap between the top two entries is the whole lesson:
**Wampa "Cornered Beast"** is 76.7% popularity AND **+40.3% offense impact**, while **Captain Rex
"The Lost Commander"** is 53.9% popularity and roughly **zero** measured impact. Popularity ≠ value.
**SaberUtils** publishes an "Omicron Order" for the multi-omicron units (Starkiller has 3, all GAC;
Boba Fett SoJ has 3, all TW). swgoh.gg's ability report filters by mode AND bracket. Not yet
scraped into the repo — both pages are JS-rendered, so it needs the MCP browser like the meta files.

### ⭐ The `rt` +2 trap bit `advisor.py`, and it was hiding the whole R7 pile
The roster's `rt` is comlink's `relic.currentTier` **verbatim, two higher than the number the game
prints on the tile**. `arena_board`, `invest_plan`, `rote_ops`, `generate_hotutils` and
`build_board.py:53` all convert it — `advisor.relic_priority()` did not. It compared and reported raw
`rt`, so its documented "default target 9" actually meant **"below R7"**, and `daily_brief` printed an
R7 unit as "relic 9". Consequences, both real:
- The advisor was blind to exactly the **R7→R9 conversion this account most needs**: it treated the
  152-unit R7 pile as already at target. Fixed, the same call surfaces **115** board units below R9
  instead of **11** — top of the list is Captain Rex R7 (96% team), Mace Windu R7, Darth Malgus R7.
- It is almost certainly the origin of CLAUDE.md's "already-owned **R9** Inquisitor bench". There is
  no R9 Inquisitor: Grand Inquisitor / Fifth Brother / Inquisitor Barriss / Marrok / Seventh Sister
  are all **R7**, Ninth Sister R6, Eighth Brother R5. CLAUDE.md corrected.
Calibration, if this is ever doubted again: Starkiller rt=11 and the repo logged him R8→**R9**;
Cad Bane rt=8, logged R5→**R6**; Gamorrean Guard rt=9, logged R5→**R7**. And CLAUDE.md's independent
"27 units at R9+" reproduces EXACTLY at offset 2 (27) versus 233 at offset 0. Relic histogram
(displayed): R4×4, R5×43, R6×36, **R7×152**, R8×54, R9×10, R10×17.
`advisor.relic_priority` now takes and returns DISPLAYED levels and emits key `relic`, not `rt`.

### ⭐ Both top-line gaps are unlocked and waiting (roster-verified 2026-08-17)
- **Profundity — every published gate MET.** 7 ships all at 7★ (Bistan's + Cassian's U-wing, Biggs' +
  Wedge's X-wing, Rebel Y-wing, Ghost, Outrider) and 7 character relics clear, **three exactly at
  threshold**: Admiral Raddus R9, Cassian Andor R8, Dash Rendar R7; then Mon Mothma/Bistan/Jyn Erso R7
  and Hera Syndulla R6. Tiers need 4★/5★/6★/7★ ships and pay 10/10/20/40 blueprints; a bonus tier pays
  10 more, free once per run. **Stardust Transmission runs ~monthly; last ran 2026-07-31.**
  ⚠ Two sources disagree on the character list — swgohevents gives the relic-gated seven above, an
  older list names the Rogue One squad (Jyn/Cassian/K-2SO/Baze/Chirrut/Bistan/Scarif Pathfinder).
  Astra owns all of those at G13 too, so the gate is met either way; no need to resolve it.
- **Third Sister is NOT an event.** Reva shards come only from the **RotE Phase 3 Neutral special
  mission**, 1 shard per victory across the guild, capped at 50. Gate: **Relic-7 Grand Inquisitor** —
  Astra's is exactly R7, so it is farmable now. It is a special mission, so auto-battle fails it.

### Double drops — the one lever that multiplies energy
No published calendar; CG announces ad hoc, but the pattern is **May 4th, the November anniversary,
the winter holidays, and whenever a character is needed for a special event**. Caps: normal 2000,
cantina/mod/ship 1000 — and free bonus energy plus store-bought energy IGNORE the cap.
The synthesis that matters here, because mods are the structural gap and tickets are the relic engine:
**240 normal + 120 cantina + 240 ship = exactly 600 = the full daily raid-ticket cap.** So Astra can
hit 600 tickets every day while banking **100% of mod energy** for a double-drop window — 1000 banked
mod energy at 2× is the single biggest slicing-material spike available, and it costs no crystals and
no raid cadence. Mod energy caps at 1000, so start banking ~4 days out, not sooner.

### Open
- **GAC Kyber-4 → Kyber-3 payout delta is unquantified.** Sources only establish that Aurodium-1 →
  Kyber-5 is roughly a wash and that "A1 up to K3" is where it starts to matter. The in-game GAC
  rewards preview shows current vs next division exactly — one screenshot settles it.
- **7,731 crystals banked and growing** under the never-spend rule. Every source ranks 3× normal +
  3× fleet refreshes daily as the top sink (~50c each, ~1,500c per accelerated unit). Not proposing
  we break the rule — but the bank needs a stated purpose or it is the largest idle asset here.

Sources: Kahzgul (energy efficiency, Finance 101), EA Community Update 2026-04-27, swgoh.wiki
(Guild Activities, Mk III Raid Tokens, Episode Track, Mods Farming), swgoh4.life (conquest feats,
relic 10), swgoh-cantina (RotE).

---

## 2026-08-18 (evening) — TW max-defense, the whole RotE map, and GAC to the top of the ladder

Owner's asks, verbatim in three parts: far more Territory War squads (**mostly defense**), research
RotE so phases stop being improvised, and clear every pending daily/store item. Mid-session he added
**arena squad + fleet climb** and one standing rule: *"when optimizing TOP PRIORITY is ALWAYS GAC"*.
No crystals, no real money.

### ⭐ `tw_wall.py` had been DEAD since the doctrine rewrite — that is why the bank never grew
It referenced `board_config.ATTACK_ONLY_GLS`, renamed to `ATTACK_ONLY_BY_FORMAT` when doctrine E
landed on 2026-08-17. Every run since ended in `AttributeError` before printing a line. The 2026-08-11
war's 43 squads were the last time the wall was actually computed. **If a script in this repo stops
being mentioned in session notes, run it before assuming it works.**

### ⭐ The comlink roster silently dropped per-unit `gp`, `o` and `z`
`swgoh_data.map_roster()` replaced the HotUtils pull on 2026-08-18. HotUtils returned `gp`/`o`/`z`
per unit; **comlink does not return GP at all** (it is a derived stat, not in `rosterUnit`). So
`tw_wall` died on `KeyError('gp')` and nothing else noticed. `swgoh_data.unit_power()` is now the one
place that knows this — real `gp` when present, else the gear/relic/star proxy that `rote_ops` already
had. **Never read `unit["gp"]` again; the key is gone.** Zetas and omicrons are simply unavailable from
this source — if something needs them, the roster needs a second producer.

### Territory War: 55 defensive squads + 6 defensive fleets = 1,854 guaranteed banners
Was 15+6. Composition, and each tier has a different source of truth:
- **23 graded** — the ILP ceiling of the well-sampled lineup table. 24 is *infeasible* (HiGHS status 8),
  measured, not guessed. Everything past 23 must come from a coarser source.
- **1 leftover lineup + 21 leader-tier-list + 5 unranked-leader** (`tw_wall.py` tiers 1-3).
- **5 no-synergy filler** (new tier 4). Five idle G13 bodies clear the 6,000-power minimum ~25x over and
  bank the same flat +30 as a 28% wall. **BACK territories only** — the 39-slot cap is guild-wide and
  first-come, so a filler in a front slot is a slot no guildmate can use.
- Only **3 of 317** G13 characters are left idle.
- **Six defensive fleets, not five.** All seven built lineups are mutually disjoint and fully owned, so
  the sixth costs nothing and pays +34. Leviathan is the one kept for offense.
- `output/tw_placement_sheet.txt` merges the graded bank and the wall into ONE front-to-back order —
  doctrine step 3, which the 2026-08-11 war got backwards at the cost of its best real estate.

**Offense cut to 8 squads on the owner's explicit max-defense call.** The cost was stated before he
chose and he took it: 8 squads cannot clear a full enemy map, so +840 territory conquests are largely
forfeited. Those 8 are therefore all coherent GL-led lineups — a thin attack bank must not be diluted.

### The investment ladder: GAC 1-4, Arena 5-7
Reversed on the owner's standing rule. The old Arena-first argument (only mode paying a ranked reward
EVERY day, and the payout compounds) is **kept in the file rather than deleted** — it is a good argument
that lost, and deleting it invites re-deriving it. Note what the change did NOT cost: T5/T6 came back
EMPTY, because Astra's deployed arena wall *is* GAC 5v5 defense P02, so best-tier-wins already had those
units at tier 1. GAC-first costs the arena climb nothing on this roster.

### ⭐ RotE: the whole map is now data, and the blocker is relics, not roster
`scripts/rote_missions.py` transcribes swgoh.wiki's Zone Information table into
`data/rote/missions_1..6.json` — 71 combat, 12 special, 17 fleet across 18 territories. RotE encounters
are **static**, so this is written once and reused every rotation. Two traps are encoded, not left to be
rediscovered: a Dark Side territory also accepts **Neutral** (Hondo is the only Neutral unit owned, and
he is a required unit on Felucia), and a **Mixed territory carries no `align` key at all**, because
`_mission_pool` drops any unit missing from the 340-unit catalog whenever align is set and the roster is 398.

**Fillability, and this is the headline:** phases 1-3 are 43/44; phase 4 is 10/15; **phases 5 and 6 are
3/12 each.** The cause is relic depth — 157 characters sit at exactly R7 while phases 5-6 gate at R9,
where only 27 qualify. And almost every locked mission is **one or two levels away**:

> `python3 scripts/rote_missions.py --gaps`

Six units are a **single relic level** from opening a mission: Geonosian Soldier (R5→6), Geonosian Spy
(R5→6), L3-37 (R7→8), Qi'ra (R7→8), Bo-Katan Mand'alor (R8→9), Cassian Andor (R8→9). Bo-Katan alone
opens a **74M-TP** row. This is the same R7→R9 conversion the repo already identified, now with named
targets and an order to do them in.

`rote_ops.py` no longer refuses to run without an operations scrape — operations need the device,
missions do not. It degrades to a mission-only plan and says loudly that nothing is reserved for platoons.

### ⭐ Mission squads were being filled by RAW POWER, which is not a team
The first phase-2 plan returned "Coruscant Underworld Police, Ahsoka Tano, Rotta the Hutt, Ugnaught,
Admiral Raddus". A leader ability only benefits its own faction, so that is one working leader and four
bystanders — the exact shape notes.md 2026-08-12 measured going **0-for-5 at 193,800 power** in TW.
Free slots now rank by rarity-weighted shared faction with the squad's anchor, power as tie-break, so it
degrades to strongest-first when nothing matches. Phase 2 now returns the real GL Ahsoka and GL Leia
lineups where it previously returned assortments.

Also: **`GLREY` and `REY` are different units both displayed "Rey"**. The plan printed "Rey, Rey, Rey
(Jedi Training)", which reads as a bug and invites picking the wrong one on the device. Colliding names
inside a squad now carry their baseId.

### Four more scripts were still pinned to hardcoded rosters
`rote_ops` (5 Aug), `compute_teams` (5 Aug), `generate_hotutils` (31 Jul), `mod_analysis` and
`mod_targets` (18 Jul). All now go through `swgoh_data.latest_roster_file()`. `rote_ops` was planning
phase squads against a two-week-old account.

### Live state read off the device this session
- **RotE (Rise of the Empire) is RUNNING: phase 2/6, 22h left, guild #5, 6/56 stars, guild GP 518M.**
  Phase 2 = Geonosis (Dark) / Felucia (Mixed) / Bracca (Light), R6+. Not a TW — the 55-squad wall waits
  for the next war.
- **All four energy pools at or over cap** (144/144, 194/144, 123/144, 244/144) — regen has been
  wasting since the 06:25 session. Crystals 9,226.
- **Squad Arena #26, Fleet Arena #12**, payout ~2h. Worse than the modelled #10.
- ⚠ **Paid bundle popups interrupt the farmbot** and it does not close them (`ERA MODULE BUNDLE II`,
  `YODA (DARK SIDE VISION) BUNDLE II`). They need a manual X or a popup-closer template.

### ⭐ ARENA ON AUTO WENT 0-FOR-3 — the GAC proxy does not survive contact
Squad Arena, rank #29, three attacks, three DEFEATS, with three different top squads:

| squad | power | opponent | result |
|---|---|---|---|
| FT1 The Stranger / Luminara / Maul HF / Starkiller / Visas | 186,353 | #22 SLKR + datacron, 175,015 | DEFEAT, 4 enemies alive |
| O03 JMK / Snips / Cmdr Ahsoka / Mace / Padmé (the "90% attacker") | 197,820 | #23 GL Leia team, 179,391 | DEFEAT, 5 enemies alive |
| FT1 The Stranger (again) | 186,353 | #28 GL Leia team, 174,498 | DEFEAT |

Every one was fought on **AUTO at 4X**, and every one was against a LOWER-power opponent.
`arena_board.py` says so itself in its own `proxy` field and it should have been believed:
*"swgoh.gg GAC 5v5 Hold%/Win%. GAC attackers are limited by the no-repeat rule and arena attackers
are not, so real arena hold runs BELOW these numbers."* The 96%/90% figures are GAC numbers; they do
not transfer, and **AUTO is the known failure mode for anything but a trivial fight** (the same note
already exists in this file for event battles).

⇒ **Do not climb arena on AUTO against a GL wall.** Either drive it manually or do not spend the
attempt. Two mistakes to not repeat: I picked the first squad on RAW POWER (186K vs 175K) — the exact
"high squad power is a mirage" error this file already documents — and then treated the model's 90%
as an arena number when the model says in writing that it is not.

Mechanics confirmed on the way:
- A LOSS costs no rank, only the attempt, plus a **6-minute cooldown on all three matches** (or 50
  crystals to skip — refused, standing rule).
- Attempts **refreshed to 5 at the 22:59 daily reset** mid-session.
- **Arena payout is 18h out, not 1h** — the 1h timer on the hub is the GAC attack phase, and they
  were misread as the same clock. Climb near payout, not at the start of the window.
- Squad Arena defense really is the last squad you ATTACKED with, win or lose: the header power
  tracked 186,353 -> 197,820 -> 186,353 as the squads were swapped. The 57% Stranger wall was
  deliberately restored with the third (losing) attack, which is what that attempt was spent on.

### The farmbot: paid bundle popups were eating whole entries
Run 1 halted 11 of 18 entries; the 21:50-21:54 halt screenshots are all the same full-screen
**"YODA (DARK SIDE VISION) BUNDLE II"** offer, and it took out every energy node. `popup_close` does
not match its X. Fixed with a `bundle_offer` template cropped on the words **"OFFER EXPIRES:"** —
not the timer beside them (it counts down) and not the X (generic white chrome). Measured 1.000 on
all four bundle captures and 0.40-0.50 on eleven non-bundle screens, against a 0.88 threshold; added
to `DEFAULT_POPUP_CLOSERS` with a (980, 1) offset from the match centre to the X.
Run 2 with a live watchdog: 7 halts instead of 11, ~331 energy drained, Coliseum NEW HIGH SCORE.

### ⭐ FLEET arena on AUTO went 3-for-3: #12 → #8 → #4 → #1
The same night Squad Arena lost three, Fleet Arena won three, on AUTO, with the `Leviathan Arena`
lineup out of `build_fleets.FLEET_LINEUPS` (Scimitar / TIE Defender / Scythe / TIE Bomber
reinforcements — the set the 2026-08-08 note proved beats the higher-power Sith Fighter / Mark VI
build). Targets were chosen by LOWEST opponent power, and at #4 the rank-1 holder was the weakest
of the three offered (440,729 against Astra's 606,329), so #1 was reachable in one hop.

⇒ The split is the lesson: **fleet AUTO wins, squad AUTO does not.** It also matches the standing
memory that Fleet Arena is the one worth the effort — rank 1 pays ~400 crystals/day against ~200 at
rank 6, while Squad Arena pays no crystals at all. Three squad attempts were spent before that note
was re-read; it should have been read first.

Fleet mechanics confirmed: a ~4 min cooldown applies **even after a win**, the 💎50 skip was refused
every time, and the defensive fleet is the one last attacked with — so ending on the Leviathan Arena
lineup parks the 29.8%-hold set automatically.

### Session end state (2026-08-19 ~01:50)
- **Fleet Arena #1**, Squad Arena #29 (unchanged, 3 attempts lost).
- **Guild Activities 600/600** — raid tickets maxed, which is the whole point of the energy dump.
- Energy drained from 144/194/123/244 to 24/16/9/97; ~470 spent, cantina put through **8-G** (8 sims,
  Flawed Signal Data) rather than the bot's default 1-A.
- Daily quests: yesterday's 8/8 crate collected before the 22:59 reset; today's at 3/8.
- **RotE phase 2/6 is live with ~19h left** and the mission plan is computed but NOT YET PLAYED.
  Operations for phase 2 are still unscraped, so nothing is reserved for platoons — scrape before
  committing squads (a deployed unit can never fill a platoon slot again).

## 2026-08-19 (01:00-04:00) — RotE phase 2 played, and COMPOSITION measured against POWER

Owner's challenge mid-session — *"have you researched the exact compositions for ROTE or are you
playing random again?!"* — was correct and is the most useful thing to come out of the night. The
requirements were researched and verified; **the compositions were not, and the game's auto-fill was
being trusted instead of the repo's own plan.**

### ⭐ OPERATIONS ARE THE PRIZE, AND THEY WERE COMPLETELY UNTOUCHED
Felucia and Bracca both read **Assigned Units 0/10** — Astra had contributed nothing to platoons this
phase. Four operations sat one or two slots from completion at **+11,000,000 TP each**.

| territory | before | assigned | after |
|---|---|---|---|
| Felucia Op4 | 14/15 | 1 | **15/15 ✓ +11M** |
| Felucia Op5 | 14/15 | 1 | **15/15 ✓ +11M** |
| Felucia Op2 | 13/15 | 1 | 14/15 |
| Felucia Op3 | 9/15  | 5 | 14/15 |
| Bracca Op1  | 11/15 | 4 | **15/15 ✓ +11M** |
| Bracca Op4  | 10/15 | 2 | 12/15 |

**+33,000,000 TP from 14 units.** Guild rank moved #7 → #4 on the first two alone. Compare: those same
14 units DEPLOYED would have paid about 40K each, ~560K total. The 18x in rote_ops' docstring is real.

Three UI facts worth keeping: a slot tagged **UNDEPLOYED** is one Astra can fill; an unlabelled dark
slot means **"UNIT ALREADY DEPLOYED"** and is dead for the phase; and the game warns **"Unit Required
in another Territory"** before locking a unit — that warning is a genuine optimiser, and cancelling on
it kept a ship free rather than burying it in a 9/15 operation.
⚠ Slot taps need a **~5-6s settle**; at 2s they silently do not register.
⚠ **Geonosis is LOCKED** — all six operations 0/15 with greyed buttons, planet at 0 TP. The Dark path
never opened (Mustafar shows ⊘ on the map), so it is a guild-level block, not something Astra can fix.

### ⭐ SPECIALS ARE MANUAL. This cost the Zeffo unlock.
The Bracca Zeffo special was played on AUTO and lost, spending the phase's last attempt (50 Mk III
tokens + 1/30 guild progress). The repo's own notes already said event specials fail on auto. The
research then said it explicitly: W1 is two Purge Troopers **then an Imperial Probe Droid that appears
mid-wave and taunts** — you hold the AoE dispel for it — W2 is Second Sister + PT + IPD, the enemy
focuses **Cere** and she must not drop below max protection. Gaming-Fans' guild: **2-for-14** without
that plan, **~90.9%** with it plus JKCK omicrons on both the leader ability and Impetuous Assault.
Now encoded in `rote_missions.TACTICS`, and `auto` is a field on every mission.

### ⭐ COMPOSITION BEATS POWER, and the margin is not subtle
Measured across ten missions tonight, same account, same night:

| squad | power | result |
|---|---|---|
| auto-fill, incoherent (Leia/Rotta/GAS/Satele/JKR) | 219,456 | 2/2 in 130s |
| auto-fill, incoherent (SEE/Lando/Revan/Stranger/Bane) | 208,547 | **1/2 — 125K only** |
| auto-fill, incoherent (Rey/CLS/Raddus/BoKatan/Cassian) | 203,103 | **1/2 — 125K only** |
| **Bossk-led BOUNTY HUNTERS** (Bossk/Embo/Hondo/Zam/Krrsantan) | **166,589** | **2/2 in 40 SECONDS** |

The Bounty Hunter squad had **27,000 LESS power** than the auto-fill it replaced and won three times
faster, because every unit answered to "On The Hunt" and the Payout mechanic fired. Same lesson as the
TW 0-for-5 note: **high squad power is a mirage.**

Fleets prove it twice more — and CORRECT this file:
- Bracca fleet: coherent **Negotiator** 611,548 beat the auto-fill's incoherent 670,075 mix. **WIN, 500K.**
- Felucia fleet: **Leviathan** 521,336 over a 707,157 grab-bag. **WIN, 500K.**
⇒ The old *"fleet missions no auto"* note (from a Negotiator+Outrider loss at 672K) was **wrong about
the cause**. It was not auto; it was an incoherent lineup. Fleets auto fine when the preset is coherent.
Also: a 7-ship preset in an 8-slot mission raises *"squad is not full"* — OK only dismisses, press
BATTLE again.

### ⭐ AUTO-FILL SPENDS GATED UNITS — twice, on the same unit
It put **Jabba** into two Felucia missions that did not require him, while Jabba's OWN mission sat
unplayed. It also grabbed **Bossk**, the lead of the researched Hondo comp. Both were manually pulled
back out. This is exactly what `mission_squads()` pre-reserves against, and it is the strongest
argument for using the computed plan rather than the in-game auto-fill.
⇒ **Play the mission that REQUIRES a gated unit first.** Once Jabba was spent on his own mission the
problem disappeared for the rest of the phase.

### Other corrections
- The **Felucia Hondo** row is filed "Special" by the wiki but the in-game panel reads **Combat
  Mission** and pays Territory Points. Data corrected; it is auto-battleable and was won.
- RotE combat missions pay **per wave**: the results screen reads `RESULTS n/m` and a 1-of-2 clear
  earns 125,000 instead of 250,000. `rote_autobattle` does not recognise that screen and reports
  "ended" — two of the night's "wins" were actually partials.
- `rote_autobattle`'s 300s cap is shorter than a long fight; a "timeout" is not a loss. Jabba SOLOED
  wave 2 after the driver gave up, and took the full 250K.
- The AUTO toggle's **ring** changes colour, not the arrow — probing the centre pixel reads white in
  both states. Sample the ring.

### Phase 2 result
10 missions played: **7 full wins, 2 partials, 1 loss** (the Zeffo special). Roughly **2.5M mission TP
+ ~1.9M deployed**, on top of the **33M from operations**. Felucia 26.4M → 89.2M, Bracca 5.9M → 29.2M,
guild 6/56 → 7/56 stars and #7 → #4 at best. Phase 2 still has ~16h to run.

## 2026-08-20 (01:30-04:30) — RotE phase 3: the 11M relic level, and two mechanics we had backwards

Guild went **#8 → #1** in the bracket and **12 → 13 stars**. Astra contributed ~26M TP.

### ⭐ THE UNLOCK RULE — looked up, after guessing it wrong twice
**ONE star on the predecessor, and it lands at the NEXT PHASE.** Verbatim, from the RotE guides:

> *"Once a territory has reached one star, the territory in the next zone that has arrows pointing
> to it from the previous one will unlock **for the next phase**."*

Phases are 24h tiers, so mid-phase progress never opens anything mid-phase.

⛔ **This file twice asserted something else and both were wrong.** First "a planet needs 3 STARS on
its predecessor" — invented from two data points. Then, when Bracca hit 3★ and Kashyyyk stayed
locked, "the successor is locked while the predecessor is under 3★ … boundary theory, unconfirmed".
Also wrong. The owner corrected it: *"planets unlock by tiers on a 24hr basis. A planet needs at
least one star on its predecessor to unlock. You could have looked that up! You do not use research
enough!"* — and he is right, it is in the first paragraph of every RotE guide. **Look up a game
mechanic before inferring one from the board.**

The real rule explains every observation cleanly:
- Phase 2 ENDED with Felucia at 89.2M and Bracca at 29.2M — both under the 148M/142M 1★ line, so
  **both finished phase 2 with ZERO stars**. That is why Tatooine and Kashyyyk did not open for
  phase 3. Nothing to do with 2 vs 3 stars.
- It is also why Felucia and Bracca were still fully playable during phase 3: **a territory that did
  NOT earn a star stays open and its Combat, Platoon and Deployment missions can be run again.**
- Conversely **a starred planet LOCKS at the end of its phase** — you cannot come back for the 2nd
  and 3rd stars later. Felucia (2★) and Bracca (3★) therefore close at the phase-3 rollover.

⇒ **Felucia 2★ and Bracca 3★ mean Tatooine and Kashyyyk OPEN at the phase-4 rollover.** The earlier
claim in this file that "the Reva shard farm is downstream of Felucia's THIRD star (316M)" is
retracted — it was a consequence of the invented rule. **The Reva farm is live in phase 4.**

Bonus zones are a separate gate and the panel states it outright: Zeffo wants "Earn Stars in
Bracca: 3/**1**" (met) plus "Complete Special Mission **30** Times: 3/30" (not met).

Sources: starwars-fans.com RotE special-missions hub; swgoh.wiki Rise_of_the_Empire; the guild
board itself.

### ⭐ A COMBAT MISSION ALSO DEPLOYS THE SQUAD'S POWER
The activity feed prints BOTH lines for one action:
```
Astra: Completed a Combat Mission (2/2 waves), earning 250,000 Territory Points
Astra: Deployed 195,123 points          <- exactly the GL Leia squad's power
```
So a mission is **250K + squad power**, and plain deployment is **squad power**. There is NO
trade-off between "run missions" and "deploy" — missions strictly dominate for the units they use.
Run every mission first, then deploy the remainder. The earlier worry about "spending" units on
missions was based on a mechanic that does not exist.

### ⭐ ONE RELIC LEVEL WAS WORTH 11,000,000 TP
Bracca Operation 3 sat at **14/15** all event. The empty slot wanted **Enfys Nest at Relic 6** and
Astra had her at **R5**. One relic level → slot filled → **+11,000,000 TP** and "Rebel Strafing Run"
levelled 2 → 3. All six Bracca operations then read 15/15; Felucia's six were already complete.
⇒ **Check operation slots for a ONE-LEVEL gap before doing anything else in a phase.** Nothing else
in the mode pays 11M for a 250K-credit upgrade.

### The material hunt, and the tool that ends it
Enfys R5→R6 needed **20 Electrium Conductor**; stock was 6. `data/economy.json` said "Guild Activity
Store" and that store does not stock it. **The game answers this itself**: tap the red material on the
Relic Amplifier screen → **FIND** → a card per route, with store, quantity, price and your balance.
Authoritative, and it took one tap. Use it before editing economy.json from memory ever again.

Routes it listed (and what actually happened):
| store | pays in | qty/price | result |
|---|---|---|---|
| Guild Store | Mk II raid token | 6 / 450 | bought → 12 |
| Guild Store | Mk II raid token | 4 / 300 | bought → 16 |
| Guild Events Store | GET3 | 2 / 720 | bought → 18 |
| Episode Shipment | episode currency | 4 / 6,000 | bought → **22** ✅ |
| Shipments / Weekly | crystals | 10/1,150 · 20/2,300 | forbidden, never used |

⚠ **Every token route is daily_limit 1.** You cannot bulk-buy a relic material from one store; you
chain across four stores in one day. `action_value.py` does not model this yet — it will happily plan
a purchase that the store will refuse. The limits are now recorded in economy.json.
⚠ **`event_only.signal_data` was WRONG.** The Guild Events Store sells Fragmented (20/1,600) and
Incomplete (20/2,000). Only **Flawed and Corrupted** are cantina-only. Corrected in both economy.json
and the action_value.py docstring.

### ⛔ `rote_autobattle`'s outcome is NOT a verdict — it was wrong on 5 of 8 missions
| label | truth |
|---|---|
| bracca_ls1 "ended" | 2/2, 250,000 |
| felucia_b "ended" | 2/2, 250,000 |
| felucia_hondo "ended" | 2/2, 250,000 |
| felucia_jabba "timeout" | 2/2, 250,000 — Jabba soloed wave 2 for 5 more minutes |
| **felucia_lando "win"** | **1/2, 125,000 — a PARTIAL reported as a win** |

A partial shows the same banner as a full clear and silently pays half. **Fixed**: `read_feed()` now
OCRs the planet activity feed after every battle and reports `waves=n/m tp=N verdict=full|partial`,
exit 3 on a partial. Six tests in `tests/test_rote_autobattle.py` pin the parsing against the real
OCR text, including the wrapped-entry case (the name and "(2/2 waves)" land on different OCR lines,
so per-line matching finds nothing) and the mangled-name fallback.
⚠ **tesseract cannot read `/tmp` from this sandbox** — it silently treats the PNG bytes as a filename
and prints nothing. Write OCR scratch into `output/`, which is what tw_place.py already does.

### Composition, again — and the cost of ignoring it
The one mission run on the game's auto-fill (Jabba + Darth Revan + Darth Bane + Wampa + Ahsoka,
219,948, five factions) took **~13 minutes** and only won because Jabba soloed the last wave alone.
Every coherent squad from the TW/GAC preset banks won in 50-330s. The owner's prompt mid-session —
*"we already have ready made tw-tb squads why not use them?"* — is the right default: **open
SELECT SQUAD and take a preset, do not hand-pick and do not accept the auto-fill.**
⚠ In-game preset tabs cap at ~15 squads (TW 5v5 - Defense ends at D15). The 55-squad wall lives in
HotUtils only, so `output/tw_placement_sheet.txt` is the lookup for anything past D15.

### Other findings
- **Bracca's Zeffo bonus zone**: "Progress 53%", gated on **Complete Special Mission 30 times (2/30)**,
  requiring **Cere Junda R7+ and any Cal Kestis R7+**. Astra's attempts were already spent.
- **Felucia operations were already 6/6** from phase 2 — operations persist across phases, so the
  quota display ("Assigned Units: 0/10") resets while the slots stay filled.
- Paid-bundle popups fire on EVERY store/shipments entry, not just at launch. `bundle_offer.png`
  handles the launch case; the shop case still needs manual dismissal.
- Login calendars: 5 claimed incl. Signal Booster day 3 (**Fragmented**, not Flawed — 10/day).

## 2026-08-20 (14:00-15:00) — MOD PASS: arena team to rung 1, relocate, upgrade

Owner: *"upgrade all mods. best possible setup. Rellocate too. first prio the one arena team.
Second priority is always grand arena defense, and then grand arena offense."*

### The ladder changed, and it is NOT a full reversal of the GAC-first rule
`ARENA_DEFENSE_TIER` 5 → **1**, and `BOARD_ROLES` stops interleaving by format:
2 = GAC 5v5 def, 3 = GAC 3v3 def, 4 = GAC 5v5 off, 5 = GAC 3v3 off. Arena climb (6) and
fleet (7) stay below the whole GAC block. So exactly ONE squad — the five actually parked on
the wall — outranks GAC. Deployed wall today = **Rotta the Hutt · Mob Enforcer · Greedo ·
Gamorrean Guard · Cad Bane**.
⚠ `invest_plan.py` could not run at all before this: `_base_ids` iterated whatever sat under
`units`/`slots`, and rote_plan.json carries `slots: 5` and `deploy.units: 337` as plain ints,
so the ladder died on TypeError. Guarded + tested. The crash predated the change.

### ⛔ TWO NOTES IN THIS FILE WERE WRONG ABOUT GRANDIVORY
1. *"Rotta had to be left out (he is locked instead, so nothing is lost)."* — **He was not
   locked. `lockedCount: 0`; nothing in the profile was locked.** His mods were protected only
   by the global `lockUnselectedCharacters`, which is a different thing: it stops mods being
   TAKEN from him, and it equally stops him ever RECEIVING one. The arena leader — now rung 1 —
   had been excluded from every optimisation run.
2. *"adding a character to the selection could not be automated"* — true of the **UI** (React
   16 + react-dnd, cards need genuine HTML5 drag-and-drop), **false of the state store.**
   Appending `{id, target}` to `profiles[0].selectedCharacters` in IndexedDB and reloading
   works. Copy `target` verbatim from a comparable already-selected unit rather than inventing
   one — Rotta took Gamorrean Guard's "PvP" target, the other Hutt Cartel tank.

### ⭐ +2.58%, against a file that said there was nothing left to get
| run | set value | mods | credits |
|---|---|---|---|
| 2026-08-08 corrected order | −0.06% | 1,473 | 7.44M |
| **2026-08-20 arena-first, Rotta added, fresh data** | **+2.58%** | **1,404** | **7,016,750** |

262,089.74 → 268,849.86. This file said *"There is almost nothing left to gain globally … the
best any ordering now finds is +0.12%. Treat the optimiser as a REDISTRIBUTION tool, not a
gains tool."* That was **conditional on the inputs not changing**, and three changed at once:
36 mods were sliced since (6-dot 145 → 156), the ladder was re-ordered, and a 310th character
became eligible to receive mods for the first time. ⇒ The rule to keep is narrower: *a re-run
on UNCHANGED inputs is redistribution.* When the mod pool or the selection changes, re-measure.
⚠ Still confirm the order before running: `Fetch with HotUtils` first (data was 2 days stale),
and `Optimize my mods!` is the **`!` button**, not the same-named nav tab — clicking the tab
just switches view and looks like a hung optimise.
Move took **~9 minutes** for 1,404 mods, ended "Mods successfully moved", no `Row not found`.

### Upgrade pass — everything affordable was spent, T05_06 is the wall
`mods_session.sh`: →6A 3 mods/5 steps, →6E 4/4, →5A 4/4. **Rotta the Hutt took the first
slice**, which is the new rung 1 working. 6-dot **156 → 160**, 6A **99 → 102**, plusSpeed
16,858 → 16,861, credits −2,042,000. modScore stayed 2.83 — as always, it measures inventory
quality and never placement.
- Calibration: 5 eligible, 1 attempt (Mob Enforcer 21→17, reverted, kept 21), then
  `rc=2 GOHServiceCall Error [40]` = **out of Micro Attenuators** (22 → 7).
- Materials after: T06_02 17, T05_06 91, T05_03 6, T05_04 27, attenuators 7. One promote also
  failed mid-list on `Not enough player currency` for T05_04.
- **Shopping list**: T05_06 short **1,033** (MASTER GATE), T06_02 short 863, T05_05 short 423,
  T06_03 short 402. Farm Mod Battles Sector 9 / Guild Store / Episode Shipments, then re-run.

### Where the arena five ended up
All five carry **6 mods, all 6-dot**: Rotta Σspd 99 · Mob Enforcer 131 · Greedo 116 ·
Gamorrean Guard 104 · Cad Bane 92 (542 total, 4.0% of the 13,548 inventory speed on 30 mods).

### Allocation against REAL stock — and the cost model was wrong in both directions
Owner: *"make the best allocation as per our prio order and the mats available. Do not assume
an 'optimal' allocation we cannot reach."*

⭐ **THE 5-DOT SLICE COST IS NOT A PER-TIER CONSTANT. IT VARIES PER MOD.** Two isolated
single-step diffs on the same afternoon:
| mod | tier | salvage | credits |
|---|---|---|---|
| Cassian Andor | t1 | T05_01 38→23 = **15** | 27,000 |
| Boba Fett | t1 | T05_01 23→13 = **10** | 18,000 |
Same tier, same 5 dots, same single step — and salvage and credits both moved by the same
**1.5×**, so a per-mod multiplier drives it. No static table can be exactly right.

The old constant was a flat **22**, derived as an AVERAGE ("512/499/514/535 of T05_01..04
bought 89 steps"). Averaging hid the spread and cost real upgrades in BOTH directions:
- **Over-charging hid affordable work.** 38 T05_01 buys two-to-three steps; the planner
  proposed one. 13 in hand looked like nothing and actually bought a step.
- **Under-charging proposed fiction.** It planned `Royal Guard t4` with 27 T05_04 in hand and
  the server refused it — **twice, on two consecutive runs** — and planned a promote with 91
  T05_06 that was also refused. That is precisely the unreachable plan the owner objected to.

⇒ **Table now holds observed MINIMA and the SERVER arbitrates.** That is the cheap direction
to be wrong in: `run()` checks responseCode and retires exactly that budget, so a refusal
costs one API call and **no materials**, while a silent over-charge costs an upgrade.
`PROMO_T0506` 76 → **92** and `STEP5_SALVAGE[4]` 22 → **35** are REFUSAL BOUNDS, not measured
costs — the true numbers need a diff after a *successful* one. A promote may also consume a
material this model does not track; T05_05 sat at 17 and is the obvious suspect.

⚠ **`mode_of()` still encoded the old ladder** — `ARENA if tier <= 3` mislabelled GAC 5v5 and
3v3 defence as ARENA, so the printed plan claimed the arena wall was getting work that was
really going to a GAC squad. Display-only, but that line is exactly how a human checks the
re-order took effect. Fixed and pinned by a test.

### Where the day ended — genuinely exhausted, and the real shopping list is SMALL
6A **99 → 102**, 6-dot **156 → 160**. Swept until the allocator proposed zero steps in every
category. Every material now sits just under its cheapest next step:
| action | material | need | have | short |
|---|---|---|---|---|
| 5-dot t1 slice | T05_01 | 10 | 3 | **7** |
| 5-dot t2 slice | T05_02 | 15 | 10 | **5** |
| 5-dot t3 slice | T05_03 | 22 | 6 | 16 |
| 5-dot t4 slice | T05_04 | 35 | 27 | 8 |
| 5A→6E promote | T05_06 | ≥92 | 91 | **1** |
| 6-dot slice step | T06_02 | 20 | 17 | **3** |
| calibration | attenuators | 15 | 7 | 8 |

⇒ Report THIS, not `slice_plan`'s "T05_06 short 1,033". That number is the cost of the next
*twenty* mods and is not a plan anyone can act on; the table above is a farming trip.

---

## 2026-08-26 — TERRITORY WAR REBUILT FROM RESEARCH. `tw_wall.py` is dead.

Owner, verbatim: *"Τα σκουάτς που έχεις φτιάξει, τόσο για offense όσο και για defense, όσο και για το
wall, είναι όλα λάθος. Έχεις αφήσει GL χωρίς σκουάτς… Πρέπει να κάνεις research online… Don't be lazy."*
He was right on every count, and the two root causes were structural, not cosmetic.

### The two bugs that produced the bad board
1. **`tw_wall.py` built squads by SHARED FACTION TAG.** Take an idle leader, give it the four roster
   units with the rarest tag in common. That is not a team — no leader ability reaches them and no
   mechanic survives contact. It shipped `Ugnaught / General Syndulla / Kuiil / Darth Sidious / Poe
   Dameron` and `Tarfful / Zaalbar / Yoda & Chewie / Veteran Smuggler Chewbacca / Vandor Chewbacca`.
2. **It imported a GAC rule into TW.** `ATTACK_ONLY_BY_FORMAT` is doctrine E, measured by
   `gac_doctrine.py` on GAC rounds where a wall pays only if it denies banners. **TW pays a flat +30
   for PLACING**, win or lose, no per-player cap. Under that rule a benched GL earns zero and denies
   zero. Eight of nine GLs were locked off the wall and **four — JMK, JML, Jabba, GL Ahsoka — had no
   TW squad at all**, i.e. the account's four highest-GP units were idle. Verified against the live
   in-game tabs, not inferred: 308 units placed across 63 squads, and those four were not among them.

### What replaced it
`data/tw_board.json` (curated, every squad carries a `why` and a band) + `scripts/tw_board.py`
(validator/emitter only) + `--categories` scoping on `upload_hotutils.py`. **61 defensive squads + 6
fleets = 2,034 guaranteed banners**, 315 of 319 G13 characters placed, 4 idle (all R5-R6), offense
10 units. Live on both surfaces: 64 HotUtils definitions under `TW - Def FRONT/MID/BACK` and
`TW - Offense`, and four in-game tabs replacing `TW 5v5 - Defense/Offense/Wall`.

### ⭐⭐ THE FINDING WORTH KEEPING: a published GAC rate is a BOUND, and the bias is TWO-SIDED
Omicrons are hard-gated per mode and **no omicron in the game is dual-gated "TB or TW"** (checked
against the verbatim `While in …:` prefix on all 193). Therefore:

| Squad carries | Its swgoh.gg rate, read as a TW number |
|---|---|
| Grand-Arena omicrons | **UPPER bound** — they go inert in TW |
| **TW omicrons** | **LOWER bound** — they were inert through every battle swgoh.gg measured |
| none, or Territory-Battles omicrons | transfers clean |

Half the team applied only the downward half, which would have systematically mis-ranked the board
*against the units Astra has already paid for*. Concretely under-rated: Kelleran Beq, Admiral Trench,
Dark Trooper Moff Gideon, Shin Hati, Master Qui-Gon, Boss Nass, Tarfful, Hera Syndulla, Poggle,
Mara Jade. Astra has **30 TW omicrons applied across 22 units against ~94 Grand Arena omicrons that
contribute nothing to a TW board.**
⚠ **And a high `o` count still is not the answer**: `o` is a count, not a mode. Pull HotUtils
`account/data/all` for per-unit `twOmiCount / gacOmiCount / tbOmiCount / cqOmiCount`.
⚠ **Two TW omicrons gate on the ENEMY having no Galactic Legend** — **Poggle** (Geonosian Brood) and
**Mara Jade** (the protection strip AND her 100% TM, both inside the conditional). On defence "the
enemy" is the attacker, who leads with a GL, so both blank against exactly the attacks they exist to
stop. Those two squads are **BACK-band only**.
⚠ **Counting omicrons OVERSTATES the haircut**, because a unit's headline mechanic is often base kit.
Ben Solo's *"While Ben Solo is active, Rey can't be defeated"* and the per-encounter Instant Defeat
Immunity are **base**; the omicron only upgrades duration. Read the ability text before sizing a discount.

### ⭐ The offence rule: `Net = 20p − 6U`
A TW clear pays at most 20 banners **regardless of unit count** (Victory 5 + First Attempt 10 +
1/survivor, and the +1-per-empty-slot bonus exactly offsets the survivor bonus — **a solo clear scores
identically to a flawless 5-unit clear, 20 = 20**). A 5-unit wall banks 30, so each unit carries 6
banners of placement value. **Break-even at U = 3.33.** Clears costing ≤3 units are banner-positive
outright; 5-unit attackers need a conquest justification.
⇒ **SEE attacks SOLO** (84%, n=2,466, **+10.8**), not with Wat Tambor (86%, n=17,478, +5.2). The duo
is the better clear and the worse decision, and it frees Wat for the Trench wall.
⇒ The owner named SEE as his archetype before any of this was computed. **His instinct and the
arithmetic selected the same unit.** His stated *reason* was wrong, though — SEE's ultimate charge is
**passive** and attacker-driven, so "the AI can't run SEE" is false. He is held back on opportunity
cost. (He also measures **24.3% on defence**, n=81: a good wall correctly passed over for a better use.)

### ⚠ The tier list only records 5-UNIT squads
Every one of ~160 rows scraped is exactly 5 units. **A unit that fights below 5 is invisible in it.**
SEE's 5-unit offence row is n=20 against ~19,900 duo/solo battles — reading it as "SEE is a weak
attacker" is an artefact of the table's shape. Wampa and Darth Bane appear nowhere at all, same cause.

### ⚠ Prefer the KYBER build over the all-league "best build"
Best-build is a **post-hoc maximum over many variants and is upward-biased at small n**: GL Rey reads
57.2% on n=101 all-league and **29.1% on n=1,901 in Kyber**; SLKR's "best build" (52.1%, n=224) is
actually *worse* than his most-played (53.9%, n=2,784). Two of three squad conflicts dissolved once the
Kyber build was used instead. Empirical all-league→Kyber ratio across leaders: **~0.62-0.75**.

### Placement, from the map
**FRONT 14 · MID 20 · BACK 27.** Every squad banks +30 regardless of band, so the split has **zero
effect on Astra's own total** — it is purely a denial decision, and denial is a guild-wide public good.
**Front denial is worth 2.3× back denial** (holding a front territory denies that territory *and the
whole lane behind it*, ~2,970 vs ~1,290), a territory falls only when **every** squad in it is beaten,
and the 39-slot cap is guild-wide and first-come and *does* fill. **Place the top 14 early and the
bottom band deliberately late** — late placement self-corrects, and a 1%-hold wall in an otherwise
empty front slot still beats empty. The `39` and the `+840` are device readings; **`1,290` is a
derivation and has never been read off a panel — UNVERIFIED.**

### ⛔ WATCH — Ahsoka (Fulcrum) "Perseverance": DO NOT BUY
EA bug [11046963](https://forums.ea.com/discussions/swgoh-technical-issues-en/cal-kestisahsoka-fulcrum-omicron-not-working/11046963),
reported at 100% reproduction, with repro steps naming the exact configuration: the debuff→buff
conversion and the turn-meter grant **do not fire, solo AND alongside Cal Kestis**. Taunt-ignore does.
So the omicron delivers materially less than advertised.
**UNVERIFIED: whether the −60% Tenacity clause still fires. No source establishes it either way — do
NOT record this as a net negative.** Astra's Fulcrum is `o0`, so nothing is currently lost.
**Verification test:** one TW battle, solo Fulcrum, dispel a debuff, look for the opposite buff +20% TM
+Protection Up. **If CG patches it she becomes a 1-unit TW clear worth ~+14 net** — the best single item
on the offence board — and it simultaneously activates **Cal Kestis's `o1`, which is a pure enabler for
her and is doing nothing today.** Cal keeps his GL Rey slot on base kit regardless.
Pinned as a self-resolving check: `data/claims.json` → `fulcrum-omicron-unbought`, and
`verify_facts.py` grew an `omicrons` branch **in the same commit** so the claim actually verifies
something. Adding the key alone would have been a false green.

### Omicron buy order (unapplied, TW-gated, ranked)
1. **Great Mothers ×2** — five once-per-battle in-place full resurrections; robust under every open
   question here. 2. Padawan Sabine · 3. General Syndulla (both → GL Ahsoka, the most upgradeable wall
   on the roster) · 4. Droideka (whole-squad revive at 100% Health) · 5. Disguised Clone Trooper (names
   Lord Vader explicitly, keys off Order 66) · 6. Embo (→ Jabba) · 7. Cinta Kaz · 8. KX Security Droid
   (alone turns five otherwise-idle ISB units into a real wall) · 9. Death Trooper (Peridea) ·
   10. Gungan Phalanx. **Juhani is conditional** — her Redeemed rider needs a Dark Side *and* a Light
   Side Unaligned Force User ally, and **none of Astra's eleven Old Republic units is a UFU**, so in the
   Satele squad she is a 2-turn taunt and nothing else. **No Galactic Legend has an omicron in any
   mode** — the `o0` on all nine is structural, never spend material there.

### Process lessons, which cost more than the squad data
- ⭐ **Agreement is only evidence when the agreeing parties did not get it from each other.** Every bad
  claim this session was caught by someone *arriving independently*; the one that survived three rounds
  (an inference about Fulcrum's Tenacity clause, nearly written into this file as fact) travelled
  strictly downstream, each hop adding confidence and no evidence.
- ⛔ **A subagent has no browser MCP.** One agent spent an entire session reporting swgoh.gg as
  Cloudflare-blocked and "the biggest remaining hole" while `browser_recipes.md` §3 and §7 already
  solved it — its own 403 was an environment limit, not a project constraint. **Scraping is a
  main-session job.** A delegated scrape 403s and reads exactly like a stale recipe.
- **A GAC-derived source would never have found the two best walls.** Lord Vader and Jabba are the only
  squads on this roster that genuinely *improve* in TW rather than surviving the translation — Vader
  because his cheap counters are themselves GAC-omicron-gated and stop working, Jabba because of Embo.

## 2026-08-29 — TW LIVE PLACEMENT: 2,140 banners, guild #1. The map itself carries the orders.

Jakku, season vs an unnamed guild, setup phase. Astra went 0 -> **2,140 banners = 60 squads x30 +
10 fleets x34**, guild #1 with the runner-up on 984. Guild total 4,198 -> 7,790 during the session.

### ⭐⭐ THE THING THIS REPO DID NOT KNOW: EACH TERRITORY CARRIES AN OFFICER NOTE
The territory info panel has a **gold bar under the activity feed** holding a short officer note,
and it is the guild's placement order. On this map:

| territory | note | position |
|---|---|---|
| Trenches | **Lord V-Rey** | FRONT (orange ring) |
| Forward Turrets | **Queen A. / Jaba** | FRONT (orange ring) |
| Infirmary | **Inquis** | 2nd rank |
| Supply Depot | **Bugs** (Geonosians) | mid |
| Ion Cannon | **GG / nightsisters** | back-ish |
| Hangar · Airspace · Main Base · Command Post · Special Ops Center | none | |

⛔ **The owner stopped the run over exactly this.** The first pass put SEVEN squads into Trenches
(the whole FRONT band) when the note said Lord Vader and Rey only. **SET IS IRREVERSIBLE**, so six
off-note squads are stuck there for this war. His rule, verbatim: *"Check out what others have
placed and follow suit. The only areas where you can place whatever you want are the back ones."*
⇒ **Read the note on every territory BEFORE placing. Only note-named teams go in a noted zone.**
`scripts/tw_scan_notes.py` crops the title bar + note bar of all ten and stacks them into one image,
because OCR of the note is unreliable (`tw_goto --scan` returned "Jaba" and "eee SO EEE").
Corroborate with the allied list: `scripts/tw_peek.py` upscales the portrait strip enough to read
(at native scale a portrait is ~55px after the Read pipeline downsamples, which is guesswork).

### ⭐ THIS MAP HAS **TWO** FLEET TERRITORIES: Airspace AND Main Base
Discovered by failure: a character-squad fill in Main Base opened **SELECT YOUR CAPITAL SHIP**.
The note-scan crop had said so already, "setting a defensive fleet" in both activity feeds, and it
was read past. Check the feed wording before planning a territory's contents.

### Numbers read off the panels this war
- **Per-territory cap 36, not 39** — it scales with the SMALLER guild's member count, so it is a
  per-war number. Never hardcode it.
- **Conquer: +810 in the front territories, +1,260 in Special Ops Center.** First device confirmation
  of the back-row doubling this repo had only derived.
- Guild-wide first-come is real and it BINDS: the three un-noted ground zones (Hangar, Command Post,
  Special Ops Center) all hit **36/36** and closed, which is what stranded the last 2 squads.

### ⭐ A SHORT LINEUP BANKS THE FULL +34, SO SPLIT THE LEFTOVER SHIPS
Eight preset fleets went into Airspace. Main Base then offered **two** unused capitals (Chimaera,
Home One) and exactly 7 free ships. One full 8-slot Chimaera fleet is +34; **Chimaera+3 and
Home One+4 is +68**, and it is two battles the enemy must win instead of one. The "not full" warning
only DISMISSES — press SET a second time. Ships ran out exactly there ("No other Ships available").

### Driving lessons that cost passes
- ⛔ **`tp.screen_title()` cannot see a CENTRED modal title.** It reads the top-left box, so
  'SELECT YOUR CAPITAL SHIP' comes back as `'BS'`, and branching on that read made the fallback tap
  land on an ability card of the capital picker and wedge the flow. OCR `(600,35,1360,100)` instead.
- ⛔ **The squad list bottoms out.** With VIS=3 visible rows, the last two rows of a tab can never be
  scrolled to the top slot, so `steps=idx; tap ROW_Y` re-tapped row N-3 and returned RESTRICTED.
  Past `idx > N-VIS`, over-scroll and index UP from the last header (`Y_LAST = 805`).
- ⛔ **The left-hand TAB list scrolls too and keeps its position.** After scrolling down to reach
  `TW 4 Offense`, the fixed coordinate for `TW 1 Def FRONT` points at `TW 3`. Rewind it every pass.
- **`TW 4 Offense` has 3 rows, so it does not scroll at all** — row i is simply at `ROW_Y + 318*i`.
- **`squad_power()` only read the first digit group** when tesseract rendered the thousands separator
  as a space (116 for 116,650). Fixed to take every digit after the label.
- ⚠ **Squad Power is NOT a reliable identity check.** Roster `gp` drifts ~2,000 in BOTH directions
  because the mod optimiser moves mods, and adjacent rows can sit 1,208 apart, so a tight test
  rejects correct loads (F14 read 159,927 against a stale 160,527 and matched F11 instead). It is
  worth having as a GROSS check only (`--loose`, 12,000). Where a slip only swaps two squads bound
  for the same territory, let the game arbitrate: RESTRICTED means already committed, re-sweep after.
- ⚠ **A maroon-chip colour audit of "which rows are already placed" did NOT work** and was deleted:
  it reported F01/F02 free when both were verifiably on the board. The chip row does not sit at a
  fixed offset from the tap slot. **Count banners instead** — `total = 30*squads + 34*fleets` is
  exact and free.
- `tw_goto.py` grew a dense grid fallback: the map keeps the zoom and pan the last panel left it at,
  there is no ADB pinch gesture, and the fixed candidate list goes stale mid-session. Also note the
  title OCRs "Ion Cannon" as **"lon Cannon"**, so `goto("Ion Cannon")` never matches; search "Cannon".

## 2026-09-03/04 — Conquest 24 (3rd instance) HARD: 93 → ~181 keycards, and FIVE driver bugs
Continued the Vol-24 run. **Sector 1 FEATS 4/4 ✓**, event feats 1/9 → 3/9, Sector 2 opened and
walked to ~43/96. Most of the session went on driver bugs, all now fixed and all worth knowing.

### ⭐⭐ THE GATE TO THE NEXT SECTOR IS *ADVANCING PAST* THE BOSS, NOT BEATING IT
Sector 1's boss sat at **3/3 stars** and Sector 2 still read **LOCKED**. Taking the Data Disk
Stockpile that sits one step BEYOND the boss unlocked Sector 2 immediately. So the rule is
positional: your token has to leave the boss node. A previous session ended believing S2 "should
be unlocked" and it was not.

### ⭐⭐ A SQUAD IS ONLY COMMITTED BY PRESSING BATTLE. BACKING OUT DISCARDS IT.
This is the bug that cost the most. `cq_auto` opened with "if I am not on the map, tap back", which
from the squad screen threw away the squad just built. Every subsequent fight then ran the previous
weak squad, and the run read as *"Sector 2 is too hard"*: a no-Attacker 185k squad timed out at
296-334s on three nodes in a row and the 219k SEE squad "lost" as well. Watching one battle showed
Ahsoka/Tarkin/Gideon/Scout/Scorch on the field when SEE had been built.
⇒ **After building a squad, the very next action must be BATTLE.** `cq_auto` now fights when it
finds itself on the squad screen instead of navigating away.

### ⭐ AUTO IS STICKY BUT MUST BE VERIFIED — a manual battle never acts and reads as a timeout
The clock runs while the squad waits for input, so a battle left on manual burns the full 5 minutes
and lands on DEFEAT. Correct HUD probe points, **1100-space, y=36**: gear **37** · retreat square
**100** · **AUTO 158** · speed 226. The old constants (retreat 118 / auto 163) sat between icons.
⚠ **AUTO is BLUE when off and YELLOW-GREEN when on**, and yellow-green FAILS a plain "is it green"
test (`g > r + 30`) because r=176 vs g=199. Test **red vs blue** (`c[0] > c[2]`) instead.
`play()` now re-taps AUTO up to three times and confirms the state changed.

### ⭐ THE DEFEAT CARD NEEDS TWO PROBES, NOT ONE
`greenish(550,499)` alone matched a half-drawn REWARDS card and reported a loss on a won battle.
The defeat card is the only screen with **green VIEW COLLECTION at (550,499) directly above teal
HELP at (550,561)**. Both, plus a re-sample 5s later, before believing it.

### ⭐ MULTI SIM DOES NOT PROGRESS FEATS — tested, stop wondering
A repeatable bonus node grows a **MULTI SIM** button after its first clear. 8 sims (8 sim tickets +
160 conquest energy) paid 585K credits and 3 mod salvage and moved **Mission Above All 4/20 and
Striking Back 0/50 by exactly zero**. Sim tickets are their own currency (37.7K owned), NOT
crystals, so the test was cheap, and the conclusion is final: sims are for credits only.

### ⭐ STAMINA IS A HARD GATE AT 0%, WHATEVER IT DOES TO STATS
`STAMINA EXHAUSTED` greys the BATTLE button out. ~10% per battle, so a squad is good for ~10 fights,
and the SEE five hit 0% together mid-run. The 2026-08-05 correction ("stamina does not affect
performance") is about STATS; availability is a separate, absolute limit. Plan a rotation: nine
GL-led squads is ~90 battles, and a full sector run needs more than that.

### ⭐ Deployable Cooling Systems is a **TECH consumable**, not a data disk
`You Must Learn Control` (15 keycards) reads like a disk feat and is not. Pass+ grants **3** of them;
they live under CONSUMABLES > TECHS in the Conquest inventory. Activate one, win any battle, done.
That was the cheapest 15 keycards of the session.

### ⭐ The node panel has a FEATS tab — the ▶ beside "ENEMIES" cycles to it
That is the only way to read a boss node's feat pair. Measured this run:
- **S1 boss (6/9):** *Unguarded* (no Tanks) ✓ · **Imperial Oversight — win with a FULL ISB squad, 3 kc**,
  still open. The five ISB (Partagaz/Dedra/Krennic/Probe/KX) are **145k and lose even a relic-4
  Sector-1 bonus node**, so this needs consumables or it stays unpaid.
- **S2 mini-boss (4/7):** *The Empire is Gone* (no Empire units) ✓ with the SEE five · **Master of
  Evil — win with Darth Vader (Duel's End), 2 kc**, still open. Mutually exclusive: budget 2 battles.
  ⚠ `Sith Empire` is NOT `Empire`: Revan/Malak pass the no-Empire feat.

### Squad-picker mechanics, learned the hard way (`scripts/cq_add.sh`)
- **A picked unit lands in the FIRST EMPTY slot, whichever slot you tapped.** So slot order is just
  call order, and **slot 1 (the leader) must be the first call**. `cq_pick.sh`'s per-slot coordinates
  are therefore misleading; `cq_add.sh` replaces it.
- **Tapping an occupied slot removes that unit** and returns it to the result list, where it sorts
  FIRST again — so re-picking without changing the search text just puts the same unit back.
- Search matches ability text, so index matters: **"Partagaz" → Emperor Palpatine first**,
  **"Krennic" → Death Trooper first**, **"Luthen" → Mon Mothma first**, "Darth Vader" → base Vader.
- The green `x/y` pip on a squad card is the **omicron count**, not stamina. Stamina is the % bar.

### Squads that worked
| Squad | Power | Result |
|---|---|---|
| **Lord Vader (L) · Darth Vader · Major Partagaz · KX Security Droid · Grand Moff Tarkin** | 183k | ⭐ **6/6, 79-117s.** Closed ALL FOUR Sector-1 feats in six battles (DoT + Retaliate + KX wins). |
| **SEE (L) · Darth Revan · Darth Bane · Darth Malak · Rey (Dark Side Vision)** | 219k | ⭐ The Sector-2 workhorse: 56-120s wins, took the mini-boss. |
| Leia Organa (GL, L) · Vel Sartha · Kleya · Luthen Rael · Cassian (Undercover) | 179k | All Rebel Fighter: carries Vel-20 + Undermine-50 + Striking Back-50 in one squad. Untested at speed. |
| Ahsoka Tano (GL, L) · Tarkin · Dark Trooper Moff Gideon · Scout Trooper · Scorch | 185k | The no-Attacker four-feat S2 squad. **Too slow for Sector 2** — timed out repeatedly. Park it on bonus nodes. |

### Data disks taken this run
Equipped 12/12: **Booming Voice(4) · Certain Defeat(2) · Master's Technique(2) · Zealous Ambition(2)
· Defensive Formation I(1) · Legendary Consumable Boost(1)**. Dropped **Perseverance(3)** — its
flat **−30% allied damage** is a poor trade when the failure mode is the 5-minute timer. Bench:
Perseverance, Guard and Penetrate, Unshakable Focus, F-34T Training Droids.

### `scripts/cq_auto.py` — the sector runner, and what it still cannot do
Finds the next thing to do by Hough-voting bright node RINGS on the map (a reachable node is a thin
bright circle, an unreachable one is dim, a cleared one is amber and fails a `min channel > 140`
test, which is exactly the filter we want), then probes each candidate for a green BATTLE and
`stars_banked < 3`. It plays a stockpile by committing the first option.
⚠ **It still loses the frontier.** Sorting candidates by raw x sent it to unreachable nodes at the
sector's far end; sorting by distance from screen centre is better but the map does not recentre
after a probe tap or a stockpile, only after a win. **Backing out of a node panel leaves the SECTOR**,
and the sector chooser also carries a CONQUEST STORE button, so the "am I on the map" probe reads
true there and the runner walks into the wrong sector — it now aborts instead. Until the player
marker (the four cyan chevrons) is detected properly, drive long stretches with
`cq_grind.py --node X Y --runs 1` off a screenshot; that path is reliable.

### Standing rails confirmed this run (owner, 2026-09-03)
⛔ **Spend NO Conquest Credits and NO crystals.** The Wandering Scavenger sells **Leia (Jedi
Training) shards, 5 for 525 credits** and Cobb Vanth 5 for 475; the owner wants the credits banked
for characters. **COMMIT with nothing selected** to walk past a scavenger.

## 2026-09-04 — the Vol-24 feat map is now DATA, and BlueStacks corrupted itself
### ⭐⭐ `swgoh4.life/conquest/feats` IS the planner. Use it, do not improvise.
It lists every feat of the live volume per sector with its keycard value, a suggested squad for
each, and (the useful part) **which OTHER feats that same battle progresses**. Written up against
Astra's roster in **`data/conquest/feat_plan_vol24.md`**, with squad powers computed from the
roster. HotUtils' own Conquest pages are only Data Disks and Status, `/conquest` is gated above
this Patreon tier, and its Discord SSO is not available from an automated browser, so it is NOT
the tool for this job whatever the menu suggests.
- ⚠ **Two "event feats" pay a DATA DISK, not keycards:** Undermine x50 pays Booming Voice and
  Vel x20 wins pays Deployable Cooling Systems. **Conquest Pass+ grants both up front**, so on a
  Pass+ account they are worth ZERO, and the 16 battles this repo had budgeted for Vel were waste.
  Read the REWARDS panel of a feat before committing to it.
- Budget for Vol 24: 572 sector + 90 global = **662 against a 630 red crate**, i.e. **~32 may be
  missed**. That is the whole strategy: every battle must be a NODE (3 kc) that also feeds a feat.
  Bonus nodes pay zero keycards and are only for feats a squad is too slow to farm on real nodes.
- ⭐ Sector 2's four feats collapse into ONE squad: Emperor Palpatine · Dark Trooper Moff Gideon ·
  Grand Moff Tarkin · Darth Malak · Bastila Shan (Fallen), all non-Attackers, DTMG included.
  ⚠ Measured **240s per win** on an S2 node against 56-120s for the SEE five. No-Attacker squads
  have no damage by construction, so run them where a slow win is safe, not on the path.
- ⭐ Sector 5's "Cheese" squad (Darth Vader · Mara Jade · Tarkin · Stormtrooper Luke · Fifth Brother)
  carries Buff Disruption + Tactical Supremacy + Potency Up, **45 keycards in one squad**, and has
  to be played MANUALLY because the AI never picks Stormtrooper Luke's basic.

### ⛔ NEVER `kill -9` BLUESTACKS. It corrupted the VM and the only offered fix wipes it.
The Mac hit **load average ~700** (Chrome, OneDrive, Defender, Spotlight, several claude sessions);
BlueStacks froze at 0% CPU and was hard-killed. Every relaunch since shows *"BlueStacks Air couldn't
start due to corrupted data ... reset your data, which will remove all apps, accounts, and
settings"*, and a clean quit-and-relaunch does not clear it. `adb devices` still lists the stale VM
and `exec-out screencap` still returns frames, but **`adb shell` answers `error: closed`**, so the
device looks half-alive while being useless. Quit BlueStacks through its own dialog and wait for the
process to disappear; if it is wedged, wait for the host load to fall rather than killing it.

### ⭐ "BlueStacks data is corrupted" was the HOST, not the VM
An overnight run left the Mac at **load average ~700** (Chrome, OneDrive, Defender, Spotlight
indexing, several claude sessions). BlueStacks froze at 0% CPU, was hard-killed, and then refused to
start for hours with *"BlueStacks Air couldn't start due to corrupted data. To fix this, you need to
reset your data, which will remove all apps, accounts, and settings."* Cancel was pressed and
**Reset data never was**. Once the load fell to **6**, the same binary started cleanly on the first
try with no error at all. ⇒ **Check `uptime` before believing any emulator-corruption message**, and
never `kill -9` BlueStacks: quit it through its own dialog and wait for the process to exit.
Second half of the same lesson: after that restart `adb shell` came back `error: closed`, i.e. the
**ADB toggle in Settings > Advanced had reset to OFF**, while `exec-out screencap` kept working. A
device that screenshots but cannot `shell` is that toggle, every time.

### ⚠ Never click the host screen blind while the owner is at the keyboard
`h.sh tap` drives the real mouse. Two clicks meant for the BlueStacks window landed in Acrobat and
in a live Teams conversation because other windows kept taking focus. Guard every host click:
```bash
osascript -e 'tell application "BlueStacks" to activate'; sleep 3
front=$(osascript -e 'tell application "System Events" to name of first application process whose frontmost is true')
[ "$front" = "BlueStacks" ] && ./scripts/h.sh tap X Y || echo ABORT
```

## 2026-09-07 — Conquest 24 (4th instance): 462 → 505+ keycards, and how the feats ACTUALLY score
Picked the run up at **462/630** with 7d 17h left, Hard, event feats 7/9, sectors at
S1 93/96 · S2 90/96 · S3 103/118 · S4 59/120 · S5 26/142.

### ⭐⭐ FEAT FARMING BEATS WALKING FORWARD, AND IT IS NOT CLOSE
A forward node pays **3 keycards** and, this deep in S4/S5, resists 190-217k squads. A sector
feat pays **10 (S4) or 15 (S5)** and can be farmed on the sector's SOFTEST node, which is
already 3/3 and therefore always winnable. Measured this session:
- **S4 in 5 battles: `For Mandalore` ✓ + `Armor Up` ✓ = +20 keycards.**
- **S5 first node, one win with the Empire five: +5 Tactical Supremacy and +6 Potency Up**,
  i.e. ~8 battles for **30 keycards**, against 3 per hard forward node.
⇒ Walk a sector only far enough to open it; then turn around and farm its feats.

### ⭐ A CLEARED NODE STILL PAYS FEATS — and a LOSS pays almost nothing
Both halves matter and both are first-party measurements, not forum lore:
- Replaying a **3/3** node progressed `For Mandalore`, `Armor Up`, `Blinding Assault`,
  `The Upper Hand` and `Accurate Battle`. The community claim that feats only register on
  uncleared nodes is **false here**.
- The "Cheese" squad **LOST** the S5 first node and moved Tactical Supremacy, Buff Disruption
  and Potency Up by **exactly zero**. The same feats then moved +5/+6 on a WIN. So
  "gain/attempt feats progress win or lose" is far too strong: the unit that grants the buff
  has to **survive long enough to cast it**, and in a loss it does not.
⇒ Never farm a buff-gain feat with a squad that cannot win. Bring the hammer, not the theme.

### ⭐ The three feat squads that were measured, with real per-battle rates
| Squad | Power | Per battle |
|---|---|---|
| **Bo-Katan (Mand'alor) · Bo-Katan Kryze · Beskar Mando · Paz Vizsla · IG-12 & Grogu** | 164k | S4: **+1 For Mandalore · +10 Armor Up · +4 Blinding Assault**. Wins the S4 first node every time. |
| ⭐ **Lord Vader (L) · Darth Vader · Grand Moff Tarkin · Mara Jade · Fifth Brother** | 190k | S5: **+5 Tactical Supremacy · +6 Potency Up**. Wins the S5 first node. |
| Darth Vader · Mara Jade · Tarkin · Stormtrooper Luke · Fifth Brother ("Cheese") | 165k | **0 · 0 · 0** — it loses, and a dead Tarkin casts nothing. |
⚠ `data/conquest/feat_plan_vol24.md` says Defense Up and Blind come "40x/battle". **They do not.**
Measured 10 and 4. Treat every rate in that file as unverified until it is watched on device.

### ⭐ Who grants what (looked up, not guessed — swgoh.gg / swgoh.wiki, 2026-09-07)
- **Tactical Supremacy has exactly three sources in the game: Grand Moff Tarkin, Admiral Trench,
  Major Partagaz.** Tarkin's *Intimidation Tactics* grants it to **Empire** allies **and grants
  Tarkin himself Potency Up** — one unit feeds `The Upper Hand` and `Accurate Battle` at once,
  which is why the Empire five above is the right squad and the Cheese five is not.
- **Buff Disruption comes from Stormtrooper Luke and nobody else**, on **his own turn's basic
  only** (an assist does not count), and it only registers when the debuff **lands** — a killing
  blow scores nothing. That makes `Deactivate` a manual, stall-setup feat. **Deprioritised.**

### Where the run stands and what is left
S4 **79/120** (only `Blinding Assault` 46/80 + the boss's 10) · S5 **49/142**.
- **S4 boss (Great Mothers, R5 Nightsisters) beat a 194k JMK/GMY/Chewbacca/GK/Ahsoka squad.**
  Its panel: **1/11**, 1 of 3 stars, and two feats — *Wisdom and Wookiee* (win with Yoda &
  Chewie surviving, **4**) and *Get Wrecked* (full Bad Batch, **4**). So 10 keycards sit there
  behind a fight that needs consumables or a manual run.
- **S5's forward wall is a full Mandalorian defence** (Maul · Beskar Mando · Bo-Katan · Paz ·
  Sabine, all R5) that beat both the 217k Lord Vader/Stranger/Maul-HF/Starkiller/Malak squad
  and the 190k Jabba bounty hunters. Consumables (6 boosters, 11 medpacs, 11 techs, with
  **Legendary Consumable Boost equipped**) are the untried lever.
- Scavenger passed with **nothing bought** (Leia JT 5/525, Cobb Vanth 5/475). Stockpile took
  **Zealous Ambition 54.4%**.

### ⚠ Two driver bugs that cost most of the session's stalls
- **`cq_next.py` mistakes a bright cyan NODE RING for the player token.** `marker()` masks
  saturated cyan, and an unplayed node's ring is exactly that, so it reported the token metres
  away, ranked unreachable nodes first, and walked the runner into the Conquest INVENTORY twice.
  Drive long stretches by reading the map and calling `cq_play.py X Y` with real coordinates.
- **`cq_play.py` cannot pass a Wandering Scavenger.** The scavenger panel's own green COMMIT
  sits at the `PANEL_BATTLE` coordinate, so `greenish(PANEL_BATTLE)` is true and the code takes
  the battle branch instead of `pass_blocker()`. It then presses COMMIT (harmless, and actually
  the correct button) and `SQUAD_BATTLE` (which lands on the confirm modal), and autofight
  reports "never saw the battle HUD". Pass a scavenger by hand until the probe is title-based.
- ⚠ `cq_run.sh` exits **silently** when `cq_next.py` finds nothing: `set -e` fires on the
  failing command substitution before the `if [ -z "$xy" ]` guard can print anything.

### Stamina is the session clock, confirmed again
~10% per battle. The SEE five went 62% → 0% in five fights and `Unit stamina exhausted` greys
BATTLE out, which surfaces as a `win-noreward` from `cq_play.py` because no battle ever ran.
Rotation used, in order: Mandos → Jabba BH → Maul BH → SEE five → SEE+The Stranger →
Lord Vader power five → Empire five.
⭐ **`Fallen` in the unit search returns THE STRANGER** (R10, 41.9k GP) — the strongest drop-in
replacement on the account and a better fifth for the SEE squad than Rey (Dark Side Vision).

## 2026-09-07 (session 2) — 505 → 533+ keycards, and the two facts that were blocking the run
### ⭐⭐ STAMINA SCALES STATS LINEARLY, AND THE GAME SAYS SO ON ITS OWN SCREEN
Tap the **`+` on a unit's card on the SELECT SQUAD screen** and Conquest prints a CURRENT vs MAX
stat table for that unit. Grand Moff Tarkin at **14% stamina**, read off the device 2026-09-07:

| | CURRENT | MAX |
|---|---|---|
| Health | 21,384 | 53,729 |
| Protection | 17,027 | 42,783 |
| Speed | **83** | **210** |
| Physical Damage | 2,513 | 6,316 |
| Special Damage | 3,877 | 9,742 |
| Mastery | 23.88 | 60 |

That is **~40% of max at 14% stamina**, i.e. roughly linear, and swgoh.wiki puts it at "about 9.3%
every 10% stamina". ⛔ **The 2026-08-05 note in this file saying stamina does not affect stats is
WRONG, and so is the widespread belief that it only gates availability.** The behavioural evidence
matched before the screen was found: the same 190k Empire five WON the Sector-5 first node at
82/100/81/100/100% and then LOST it five times out of six at 10/28/9/28/28%.
⇒ A tired squad is a weaker squad, it loses, and **a loss scores no feats at all**. Rotate out at
~40%, and check the `+` panel rather than arguing about the mechanic.

### ⭐⭐ THERE ARE STIM PACKS IN THE INVENTORY ALREADY. USE THEM.
Same `+` panel: **Large ×3 (50% stamina) · Medium ×5 (25%) · Small ×3 (10%)**, already owned, no
purchase. That is **305% of stamina, about 30 extra battles**, and it was sitting unused while the
run stalled on tired squads. `ADD MORE` is the buy button (Conquest Credits / crystals) and is the
only part of this that touches the standing "bank the credits" rail.
⇒ **Spend stims on the unit that GATES a feat**, not on the carry. Two Larges went into Tarkin,
who alone gates `The Upper Hand` + `Accurate Battle` = 30 keycards.

### ⭐ RESEARCH THE COUNTER, DO NOT STACK GP (owner, 2026-09-07: "you cannot expect to win by playing lazy")
The Sector-5 Mandalorian wall beat a **217k** squad and a **190k** squad, then fell on the first
attempt to a **185k** one taken off the counter tables:
**The Stranger (L) · Maul (Hate-Fueled) · Starkiller · Barriss Offee · Visas Marr.**
The reason is mechanical, not statistical: Bo-Katan (Mand'alor) **ignores Taunt and converts
debuffs into Defense**, so the taunt-plus-DoT squad was feeding her.
⭐ **`/gac/counters/<BASEID>/` on swgoh.gg is fetchable for free.** WebFetch gets 403 on every
swgoh.gg URL, but the page loads in the **chrome-devtools MCP browser**, and `evaluate_script`
returns the whole table as TEXT, so it costs no screenshot budget. A row is **5 attackers then
5 defenders**. Full pulls are in `data/conquest/feat_plan_vol24.md`.
⚠ **GAC counter data does NOT transfer to a Conquest boss.** The 100%-win-rate JML counter
(Satele Shan · Bastila Shan · JKR · Jolee · Juhani, n=35, all owned, all at 100% stamina) still
LOST the Sector-5 boss. A Conquest boss carries boss modifiers and is fought on AUTO, while the
counter data is manual GAC play. Use the counters to pick the ARCHETYPE, then expect to need
consumables or manual driving on top.

### Measured feat rates this session (all on the sector's FIRST node)
| Squad | Feat | Rate |
|---|---|---|
| Jabba (L) · Boba · Jango · Bossk · Krrsantan, 190k | `Two Guns, One Legacy` | 1 per WIN, ~4 wins in 6 before it faded. **CLOSED, +15** |
| JKL (L) · Threepio & Chewie · Jedi Master Luke · Sun Fac · Zaalbar, 176k | `Blinding Assault` | **+5.75 blinds per win** (46 → 69 in four). **CLOSED, +10** |
| Emperor Palpatine (L) · Tarkin · Admiral Piett · Grand Inquisitor · Seventh Sister, 168k | `The Upper Hand` + `Accurate Battle` | in progress |
⭐ **Jedi Knight Luke is the Blind engine** (Blind on his BASIC, and he spreads it). Threepio &
Chewie, Mission Vao, Sun Fac and Jabba also apply it. ⛔ **Jar Jar Binks does NOT blind enemies,
he blinds HIMSELF** whenever he would gain Foresight; a search snippet suggesting otherwise was
misread here before the kit was checked.

### Sector state at 10:45
S1 93/96 · S2 90/96 · **S3 103/118 with all four feats DONE and the boss at 11/11**, so its
residue is on branches the token cannot reach · S4 89/120 · S5 67/142. **533 of the 630 crate.**

## 2026-09-07 (session 3) — SECTOR 4 AND SECTOR 5 ARE BOTH 4/4 ON FEATS. 462 → 581.
### ⭐⭐ WHEN A FEAT STALLS, CHECK WHETHER THE EFFECT HAS OTHER SOURCES
`Accurate Battle` (Potency Up x50) was being farmed off Grand Moff Tarkin because he is one of only
three Tactical Supremacy sources, and the assumption carried over. **Potency Up has about sixty
sources** (swgoh.gg `/effects/potency-up/`, readable as text in the chrome-devtools MCP browser).
`Deactivate` (Buff Disruption x30) is genuinely Stormtrooper-Luke-only, but **he was still at 100%
stamina all day because his single outing had been a LOSS, and losses cost no stamina.**
⭐ Both live in one fully-owned, fully-fresh squad, the classic cheese five:
**Commander Luke Skywalker (L) · Veteran Smuggler Han Solo · Tarfful · C-3PO · Stormtrooper Luke,
160k** (C-3PO grants Potency Up, Stormtrooper Luke applies Buff Disruption).
Measured on the **second** S5 node: **+4 Potency Up and +2.4 Buff Disruption per battle**, and
**defeats still counted the Buff Disruption attempts**. Both feats closed. **+30 keycards.**

### ⭐⭐ A FEAT SQUAD CAN BE TOO FAST, AND THAT IS WHY THE FIRST NODE IS THE WRONG FARM
Seven wins on the sector's SOFTEST node moved `The Upper Hand` and `Accurate Battle` by **zero**:
a fresh R10 carry kills the node before Tarkin ever takes a turn. The identical squad on the
**second** node, which lasts longer, scored **+5 Tactical Supremacy in three wins** and closed it.
⇒ **Farm on the softest node the squad can still win, not the softest node in the sector.**

### ⭐⭐ CONSUMABLES ARE THE LEVER FOR A CONQUEST BOSS. NOTHING ELSE MOVED IT.
The Sector-4 Great Mothers boss beat a 194k JMK squad, then a 196k SLKR squad that is the
**99%-win-rate GAC counter (n=217)**. With **one Booster, one Medpac and one Tech activated** the
same SLKR squad **won it**, taking the node from **1/11 to 3/11**.
- Activate from **INVENTORY > CONSUMABLES**, not from the squad screen's `+` (that is Stim Packs).
- **Only ONE of each category can be active at a time**: a second pick raises "Confirm Consumable
  Replacement".
- **Max Duration is counted in battles and a LOSS does not consume one**, so arming before a boss
  attempt is free and survives failed attempts.
- ⛔ Even so, the **Sector-5 boss (Jedi Master Luke, R5 with 6 omicrons) resisted everything**:
  the 100% GAC counter at full stamina, a 190k Stranger squad, and a boosted attempt. It is the
  hardest thing on the board and probably needs manual driving.

### Where the run stands
**581 of the 630 red crate, 49 short**, 7d 6h left. **S4 feats 4/4 · S5 feats 4/4 · S3 feats 4/4.**
S1 93/96 · S2 90/96 · S3 103/118 (residue on unreachable branches) · S4 91/120 · S5 113/142.
The remaining 49 has to come from **boss and mini-boss feats plus unwalked nodes**, all of which
now depend on consumable-backed or manually driven boss fights, and on a roster that is spent.
Stims left: Medium x2, Small x2 (Large all used). ⚠ The Conquest Store sells more for Conquest
Credits (2,255 banked) and the standing rail is to bank those, so none were spent.

## 2026-09-07 (evening) — RED CRATE SECURED at 630/630, six days early
"Max Crate Reward Achieved. Reward will be sent via inbox at the end of the conquest event."
**593 → 630 in one session**, 37 keycards, ~25 battles, zero Conquest Credits spent.
Final: S1 93/96 · S2 **96/96** · S3 103/118 · S4 112/120 · S5 135/142.

### ⭐⭐ THE SCORING MODEL, DERIVED AND THEN RECONCILED TO THE KEYCARD
`sector total = Σ node keycards + Σ sector-feat rewards`. Sector 4 balanced exactly before a
single battle: 20 normal nodes (12 at 3/3, 2 at 2/3, 6 at 1/3) + mini-boss 2/9 + boss 3/11 +
4 feats × 10 = 36+4+6+2+3+40 = **91/120**. Sector 2 balanced too. **Do this arithmetic first:**
if it balances, nothing is hiding and every remaining keycard has a named home. The 14:50
handoff's "49 to go, all boss fights, roster spent" was three wrong readings of the same board.

- **1 keycard per STAR**, 3 per normal node. Stars = how much of the squad survives.
- ⭐⭐ **A VISITED NODE CAN BE REPLAYED AT ANY TIME AND THE STAR DELTA IS PAID.** Measured: a
  1/3 node re-fought went to 2/3 and the sector counter moved with it. **Twenty of the 37 came
  from re-winning nodes left at 1/3 or 2/3.** This is the cheapest keycard in the mode and it is
  invisible if you only ever look at the frontier.
- ⭐ **Boss and mini-boss nodes carry TWO FEATS OF THEIR OWN.** That is why their denominators
  are 7/9/11/13 rather than 3. They are **not** in the sector FEATS list: open the node panel and
  press `►` past ENEMIES to reach FEATS, where a greyed row is already earned. Values scale by
  sector — S1/S2 boss 3+3, S3/S4 boss 4+4, S5 boss 5+5; mini-boss 2+2 in S1-S3, 3+3 in S4-S5.
- ⛔ **CORRECTION to the 2026-08-04 entry above** ("A 3/3-STARRED NODE IS EXHAUSTED — RE-FIGHTING
  IT PAYS NOTHING", and "`3/9` on a 3/3 node does NOT mean 6 are farmable"). True for NORMAL
  nodes. **False for boss nodes**, whose surplus is feat-locked, not star-locked, and is very much
  farmable: the S5 boss sat at 8/13 with 3/3 stars and paid 5 more for one feat.
- ⭐ **Rank targets by keycards per BATTLE, not by keycards available.** A boss feat pays 3-5 for
  one win; a star gap pays 1-2 and demands a flawless win. Feat-first, star gaps as the top-up.
- ⭐ **The whole Hard feat table is public** at `https://swgoh.gg/conquest/CONQUEST_VOL24/`. It
  403s for WebFetch and loads clean in the **chrome-devtools MCP browser**, where
  `document.body.innerText` returns all 49 feats as text. Read it there, never off the device.
- **Event feats are worthless for keycards**: both open ones paid **1** each.

### ⭐ A LOSS IS FREE, AND THAT CHANGES THE ORDER OF OPERATIONS
Verified twice: stamina was identical across a defeat, and the armed Booster/Medpac still read
`1/1` on the map bar afterwards. **A defeat costs no stamina and does not consume a consumable
duration** — only the 20 energy. So: **probe unarmed, then arm the retry.**
⭐ The **Sector 5 boss (Jedi Master Luke R5, 6 omicrons), written off at 14:50 as the hardest
thing on the board after several unarmed losses, fell on the FIRST ARMED ATTEMPT** and paid the
5 keycards that finished the crate. Those losses were a consumables problem, not a roster
problem, and reading them as evidence about the roster nearly cost the run.
Two multipliers: the equipped **Legendary Consumable Boost** disk **doubles Booster stat gains**
and adds +25% Speed (so Overcharged Defense = +300% Defense), and **Conquest Pass+ makes data-disk
swapping free** — still an unused lever.
⚠ A 10m-timer boss outruns `autofight`'s 420s default: it returned `timeout / unknown` while the
fight was still running and about to be won. Poll `state()` for `rewards` before concluding.

### The 37, in the order they fell
| Where | What | KC |
|---|---|---|
| S4 mini-boss | `Kenobiii!` (Maul (Hate-Fueled) in squad) — Stranger(L)·Maul HF·Starkiller·Barriss·Visas 185k | 3 |
| S4 mini-boss | `Disarmed` (no Attackers) + 3rd star — JML(L)·General Kenobi·GMY·Jolee·Barriss 190k | 4 |
| S4 | eight nodes replayed to 3/3 | 14 |
| S2 mini-boss | `Master of Evil` (Darth Vader (Duel's End) in squad) — GL Rey(L)·Vader DE·GK·GMY·Jolee 193k | 2 |
| S2 | two 1/3 nodes to 3/3 → **sector complete** | 4 |
| S5 | five 2/3 nodes to 3/3 — **004 GL Leia** preset 195k | 5 |
| S5 boss | `Hope of the Galaxy` (Rey (Jedi Training) surviving) — GL Rey(L)·Rey JT·GK·Jolee·GMY 196k, ARMED | 5 |

### Two feats this roster cannot field, dropped on evidence
- **S4 boss `Wisdom and Wookiee` / `Get Wrecked` (8).** Lost twice, once armed.
  ⭐ `Wisdom and Wookiee` wants **`YODACHEWBACCA`, which is ONE unit** (Support, G13 **R5**), not
  Yoda plus a Chewbacca. `Get Wrecked` wants all five Bad Batch, all G13 **R6**.
- **S1 boss `Imperial Oversight`, full ISB squad (3).** Lost twice, once armed with the
  Overcharged Defense Penetration Booster. All five ISB — Major Partagaz (L), Dedra Meero,
  Imperial Probe Droid, KX Security Droid, Director Krennic — are G13 R7 at **100% stamina** and
  still total only **143k**. The squad is too small; rest was never the issue.
  ⚠ **Dedra Meero has no leader ability**; Partagaz and Krennic are the only ISB leaders.

### New drivers — `scripts/cq_{open,build,fight,sweep}.py`
- `cq_open.py --pan N --node X Y [--panel-only] [--anchor right]` — opens one node, verifying a
  green BATTLE is really there before pressing it.
- `cq_build.py --clear "term" ...` — builds a squad through **SELECT FILTER's TEXT SEARCH**
  instead of scrolling 398 portraits two at a time. ⚠ Parentheses break `adb input text`, so use
  `"maul"`, not `"maul (hate"`. Grid order is power-DESCENDING, so `"chewie"` gives Threepio &
  Chewie first and Yoda & Chewie second: that is what `--pick` is for.
- `cq_fight.py` — presses BATTLE from the squad screen, auto-fights, clears the cards. Separate
  from `cq_farm.py` so a hand-built squad is not thrown away by re-entering the node.
- `cq_sweep.py pan:x,y ...` — re-fights a list of nodes once each. The star-cleanup tool.
- ⛔ **`cq_grind.state()` RETURNS "map" AS ITS FALLBACK.** The squad screen with a greyed-out
  BATTLE (squad not full) matches none of its earlier tests and therefore reads as **"map"**.
  A sweep started from there put map coordinates onto the roster grid and **silently removed the
  squad leader**, then reported three nodes "unreachable". `cq_sweep.to_map()` now tests
  `tealish(P_STORE)` — CONQUEST STORE is a positive tell for a clean sector map. Any future
  driver that taps map coordinates must gate on that, not on `state() == "map"`.

### UI facts worth keeping
- **SELECT SQUAD applies a preset only if you tap the squad's NAME.** Tapping its group icon opens
  the preset EDITOR, and CONFIRM there merely saves the preset back — the battle squad is unchanged.
- The **`+` on a squad card** is the Stim Pack / stat panel, not a swap button.
- A win costs about **10% stamina**; the Stranger five went 95% → 8% over nine wins.

### Left on the table before Sep 14 (none of it needed)
S3 **15** — never inspected this session, and the old "residue on unreachable branches" claim
deserves one look now that replays are known to pay. S4 boss **8** · S5 mini-boss **6** and one
star **1** · S1 boss **3**.

## 2026-09-12 (10:30) — mod session: placement AUDITED as correct, and two broken inputs fixed

### The material names, finally pinned to the internal ids
Matched by diffing "You Own" in the in-game stores against `pull_mods.py`'s material dict:
**T05_06 (the MASTER GATE) = `Mk 1 Capacitor`** · T05_05 = `Mk 1 Amplifier` ·
**PROMO_T5_T6 = `Mk 2 Pulse Modulator`**. All three are sold in **Episode Shipments** (25 per
2,500 EC) and the Guild Activity store, which is what makes the 100K-capped Episode currency
worth spending on slicing rather than on gear.

### Session result (HU_SID captured via chrome-devtools, Discord silent SSO worked this time)
34 tier-steps executed in ladder order: 3 mods to 6A, 5 promotes to 6E, 18 slices to 5A.
**6A 107 -> 110 · 6-dot 170 -> 175 · plusSpeed 16,823 -> 16,834 · speed20 51 -> 52.**
Cost 3.06M credits. Stopped at true material exhaustion (T06_02 225 -> 85, T05_06 667 -> 287).

### ⚠ Calibration is still a bad trade, now with a fourth data point
6 attempts on genuinely under-rolled mods (deficit >= 1), **1 kept** (General Kenobi 17 -> 19),
4 reverted, 1 stopped on `rc=2 GOHServiceCall Error [40]` when attenuators ran out.
**175 attenuators for +2 speed.** Cumulative record across sessions is now roughly 1 hit in 24.
⇒ Treat `calibrate.py` as a last call on a farming trip, never as a reason to farm attenuators.

### ⭐⭐ PLACEMENT IS CORRECT, and this is a direct audit rather than an optimiser measurement
Earlier the case rested on "a Grandivory re-run measured +0.12% for ~1,473 moves / ~7.4M credits".
Stronger evidence now: bucket every 6-dot mod by its unit's rung in `invest_plan.mod_priority`.
**T1 arena wall 30 · T2 arena attack 11 · GAC (11-100) 127 · rest 7 · off-ladder 0 · unequipped 0.**
So 168 of 175 six-dot mods sit in the top 100 and the arena wall is a perfect 30/30. Exactly ONE
6-dot mod with 15+ speed sits below rank 100 (17 spd on RC-1262 "Scorch", rank 137).
⇒ There is nothing for the optimiser to move. **Do not churn placement. Farm materials instead.**

Mean mod-speed by rung: T1 arena wall **97.0** · T2 arena attack 59.6 · GAC 58.1 · rest 42.1,
against a roster median of 38 and a roster maximum of 141.
⇒ The one real shape problem is **T2, the GL Leia arena ATTACK squad**: only 1 of 5 units is fully
6-dot and Captain Drogan, Captain Rex and R2-D2 are at **0/6**. Rotta also carries **no speed
arrow** and the lowest T1 speed (73).

### ⛔ TWO INPUTS WERE SILENTLY WRONG, and both flattered/inflated the report
1. **`data/current_mods.json` had NO WRITER anywhere in the repo.** It was hand-built on
   2026-09-04 and `mod_analysis.py` is its only reader, so the gap report was grading an
   8-day-old roster and every slicing session made it staler. It claimed **49 unleveled units**;
   the true figure on fresh data is **0**. Added `scripts/build_current_mods.py`; run it after
   every `pull_mods.py`.
2. **`mod_analysis.py` gated "low speed" at a flat `<180`.** Nothing on this roster reaches 180
   (max 141), so it flagged **137 of 137 units** and the report was noise. It now calibrates off
   the roster's own 75th percentile (61 today), overridable with `MOD_SLOW_MIN`.
   Post-fix: `OK=1 wrongSet=126 noSpeedArrow=71 lowSpeed=85 unleveled=0 not6dot=134 (of 142)`.
   ⚠ `mod_analysis.py` also reads `data/gac_result.json` for its unit list, so run
   `compute_teams.py` first or it grades last season's board.

## 2026-09-14 — full daily run: 8/8 quests, 600/600 tickets, and three store facts corrected

### Where the account actually stands (read off the device, not inferred)
- **GAC: KYBER 3, skill rating 3,203** (3,165 on 08-24, so +38). Season 83 is **3v3**.
  Weekly event: **R1 LOSS · R2 WIN 1,737-65 vs Exar Kun · R3 SETUP PHASE, 23h left.**
  ⭐ The R3 **defence board was already full — 5/5 · 5/5 · 5/5 · 3/3 fleet** — carried over from the
  09-11/09-12 placement. Nothing to re-place. Offence left untouched per the standing rail.
- **TW ended in DEFEAT, 11,735 vs 18,433.** That is the third loss in four wars and the margin
  (6,698) is nearly triple the 2,287/2,605 losses the wall argument was sized against. The
  ~1,888 banners this repo placed did not move it. **The deficit is offence, not the wall** —
  which is what the 08-24 correction already said. Revisit the 8-squad offence cap with the owner.
- **Conquest: MAX CRATE ALREADY ACHIEVED (Hard-07)**, feats 7/9, sectors 93/96 · 96/96 · 103/118,
  12,449 conquest energy banked. Extra keycards buy nothing once the crate is maxed ⇒ nothing to do.
- Raid (Order 66): all 5 attempts submitted, 1,397,500, guild 84.3M, rank 18.
- TB/RotE **not running** — guild chat says "ROTE coming soon".
- Arenas: fleet **#1 held** (auto win vs the lowest-power board target, per the measured rule);
  squad #2, untouched (auto loses there, also measured).

### ⛔ THREE STORE FACTS THE 09-12 NOTE GOT WRONG
1. **Episode Shipments does NOT sell mod slicing materials.** The 09-12 instruction to "buy ~69K EC
   via Episode Shipments" cannot be executed: the store's whole inventory is Supremacy Directives,
   omicron/Mk III ability mats, Signal Data, Kyrotech Mk7/Mk9, Injector salvage, then character
   shards. Verified by walking every row. **74.1K/100K Episode currency is still unspent.**
2. **The Guild Activity store is the slicing-mat route, and it is ONE purchase per 4h39m refresh:**
   `Mk 2 Pulse Modulator ×6 for 900`. Bought (442 -> 448). No Mk 1 Capacitor/Amplifier in today's
   rotation, so T05_06 (the MASTER GATE) has no route today at all.
3. **`execute_upgrades.py` prints "farm at Mod Battles Sector 9" and that node does not exist** —
   the 2026-04-27 update cut Mod Battles to chapters 1-2. Treat that string as stale.

### The purchases that WERE worth making (3/3 shipments quest, all forced materials)
Guild Events store, daily-limit 1 each: **Fragmented Signal Data +20** (1,652->1,672),
**Incomplete Signal Data +20** (786->806), **Zinbiddle Card +2** (45->47). `action_value.py` marks
the first two FORCED (no substitute route), so this is the highest-value recurring daily buy on the
account. Do it every day; it is cheap in guild-event tokens and nothing else spends them.

### Mods session (SID captured via chrome-devtools, Discord silent SSO worked again)
10 tier-steps: 1 mod to 6A, 2 promotes to 6E, 5 slices to 5A. **6-dot 175 -> 177 · 6A 110 -> 111 ·
plusSpeed 16,834 -> 16,835 · speed15 327 -> 328.** Cost 1.11M credits.
Stopped at true exhaustion again: **T06_02 85 -> 35, T05_06 287 -> 142.**
⚠ **Calibration, fifth data point, same answer:** 1 attempt, 0 kept, then
`rc=2 GOHServiceCall Error [40]` when attenuators ran out (67 -> 42). Cumulative ~1 hit in 25.
Shopping list to clear the next 20 mods: T06_02 short 1,165 · T05_06 short 918 · T06_03 short 583.

### Gear: the two named sub-G13 units are now as far as free materials take them
CLAUDE.md names **4-LOM + Zuckuss** as the only sub-G13 units gating anything (the Kyber-D1 #1
offence squad). Every craftable slot on both was crafted and equipped:
**4-LOM 18,577 -> 19,369** (4 slots) · **Zuckuss 17,976 -> 18,570** (3 slots).
⛔ **Both are now hard-blocked, not resource-blocked.** The remaining slots want
**Mk 9 TaggeCo Holo Lens** (FIND offers crystals only: 1,000-2,000 💎) and **Mk 8 Neuro-Saav
Electrobinoculars** (FIND returns *"No locations found"*). Do not farm for these and do not buy them.

### UI facts worth keeping
- **The AUTO button in a battle is at device (282,65), not (222,54).** The second icon in that row is
  hide-UI, and tapping it looks exactly like AUTO refusing to engage — 4 wasted screenshots and a
  battle driven by hand before the zoom showed the real centre. SPEED is (395,65).
- The hub's bottom-left thumbnail is a **jump-to-last-node shortcut**, not a nav menu.
- Challenges have a **MULTI SIM** button that sims the highest tier of every challenge at once
  (14 battles, 1 tap) — it covers both the "2 Challenges" and "1 Fleet Challenge" dailies.
- The free **Bronzium is 10/day on an ~8-minute cooldown**, and those 10 pulls complete the
  Episode-quest row "Open 10 Data Cards in the Store" (5,000 episode points).

## 2026-09-14/15 — RotE PHASE 1 played end to end, and the FLEETS were the expensive mistake
Phase 1/6, 21h left at the start, guild 0/56 stars, Guild GP 517,612,030. Board:
**Mustafar (DS)** 23.8M/116.4M · **Corellia (Mixed)** 61.4M/111.7M · **Coruscant (LS)** 68.0M/116.4M.
Star gates 116M/186M/248M (Mustafar, Coruscant) and 112M/179M/238M (Corellia).
Astra finished the session at **guild rank #1**, from #13 when the operations started.

### The phase-1 board, which this repo had never seen
**15 missions: 11 combat + 1 special + 3 fleet**, plus one Operations area per planet. That matches
`data/rote/missions_1.json` for the ground rows and exposes the gap the mission files had: they carry
ZERO fleet rows. Each fleet row is gated on one 7-star ship: **Scythe** (Mustafar), **Lando's
Millennium Falcon** (Corellia), **Outrider** (Coruscant), 400,000 TP each. Now in
`rote_missions.ROTE_FLEETS`.

### ⭐⭐ OPERATIONS PAID 50,000,000 TP FOR 9 UNITS, AND THE ENUMERATE-FIRST RULE EARNED ITS KEEP
Gate is **Relic 5+ characters / 7-star ships**, **+10,000,000 TP** per completed operation, quota 10
assigned units per area. Astra had contributed 0/10 everywhere. Five operations were one to three
slots short AND fillable:

| area | op | before | units | after |
|---|---|---|---|---|
| Coruscant | 4 | 14/15 | 1 | **15/15 ✓ +10M** |
| Coruscant | 5 | 13/15 | 2 | **15/15 ✓ +10M** |
| Corellia | 5 | 13/15 | 2 | **15/15 ✓ +10M** |
| Corellia | 6 | 12/15 | 3 | **15/15 ✓ +10M** |
| Mustafar | 3 | 14/15 | 1 | **15/15 ✓ +10M** |

Then the partials: Mustafar 6 12→14/15, Mustafar 5 11→13/15, Mustafar 4 11→12/15, Coruscant 6 8→12/15.
**18 units placed, +50,000,000 TP banked.** The same 18 units deployed would have paid about 720,000.
- ⚠ **The shared-unit cost is real and visible.** Mustafar Op6 showed badge `3+` and needed exactly 3.
  After Corellia Op6 took the third unit the badge fell to `2`, so Mustafar Op6 could only reach 14/15.
  One of the two was always going to be stranded; enumerating first is what made the choice deliberate
  rather than accidental. Do it before assigning anything.
- ⚠ **Tapping an UNDEPLOYED slot auto-picks the matching unit and shows it immediately.** Zoom the
  portrait and read the relic badge BEFORE pressing ASSIGN; that is the only chance to cancel.
- The `DUPLICATE UNIT SELECTION` modal fires when two slots in the same operation want one unit, and
  `OK` sits at (948,690). The remaining picks stay staged, so just OK and press ASSIGN.

### ⭐⭐ THE RESULT THAT DECIDES HOW TO PLAY A PHASE-1 GROUND ROW: BRING A GALACTIC LEGEND
Eleven combat rows plus the special, all on AUTO unless noted:

| row | squad | power | result |
|---|---|---|---|
| Mustafar vader | **Lord Vader SOLO** (GL) | 56,646 | **2/2** 200K |
| Mustafar ds_1 | **SEE** (GL) + Sith Empire | 181,447 | **2/2** 200K |
| Mustafar ds_2 | **SLKR** (GL) + First Order | 179,058 | **2/2** 200K |
| Mustafar ds_3 | Inquisitorius, no GL | 160,326 | 1/2 100K |
| Corellia jabba | **Jabba** (GL) + Hutt Cartel | 182,195 | **2/2** 200K |
| Corellia aphra | Aphra droids, no GL | 154,173 | 1/2 100K |
| Corellia mixed | Bounty Hunters, no GL | 166,855 | **0/2 ZERO** |
| Corellia special | Qi'ra core + **GL Ahsoka** | 163,097 | **CLEARED** |
| Coruscant jedi | **JML** (GL) + Jedi | 195,108 | **2/2** 200K |
| Coruscant jedi_named | **JMK** (GL) + Mace/Fisto | 178,024 | **2/2** 200K |
| Coruscant ls_1 | **GL Rey** + Resistance | 186,827 | **2/2** 200K |
| Coruscant ls_2 | **GL Leia** + Rebel core | 186,226 | 1/2 100K |

**Every row carrying a modern GL squad went 2/2. All three rows without one dropped a wave.** Power did
not discriminate: the 0/2 squad out-powered three of the 2/2 squads. Astra owns 9 GLs against 12 ground
rows, so **three rows are always GL-less and should be treated as the ones to play manually**, not as
free auto-clears. `TACTICS` marks phase-1 combat `auto: True`; that was inherited from phase 2 and is
only true for the GL rows.
⚠ **GL Leia's Rebel core is the exception that refines the rule.** It has a GL and still went 1/2, so
the real predicate is "a GL plus a squad from the current meta", not "a GL". Commander Luke / Han /
Chewie / R2 is an old team.
⭐ **The one squad I varied from the published five is the only ZERO of the night.** The measured
Bossk Bounty Hunter clear is Bossk/Embo/Hondo/Zam/Krrsantan; I fielded Bossk/Embo/Zam/Jango/Boba
because the search was quicker. 0/2, and the whole 200,000 with it. Field the printed five.

### ⛔⛔ THE FLEETS COST 800,000 TP, AND IT WAS THE MANUAL REBUILDS THAT LOST THEM
| fleet | lineup | power | result |
|---|---|---|---|
| Corellia (Lando's MF) | **the game's own auto-fill**: Executor + Lando's MF + Hound's Tooth + Razor Crest, reinforced Punishing One / Xanadu Blood / Slave I / IG-2000 | 629,354 | **1/1 400K** |
| Mustafar (Scythe) | rebuilt: Leviathan capital + Scythe + Imperial TIEs | 706,160 | **0/1 ZERO** |
| Coruscant (Outrider) | rebuilt: Negotiator + Outrider + the six highest-power Galactic Republic ships | 631,697 | **0/1 ZERO** |

The auto-fill's Corellia lineup is, ship for ship, `build_fleets.FLEET_LINEUPS["Executor"]` with the
gate ship swapped in. It won at the LOWEST power of the three. Both losses were lineups I assembled.
- The Mustafar loss has an obvious explanation and the Coruscant one refutes it. Mustafar paired a
  **Sith** capital with **Imperial** ships, which forfeits Leviathan's Reinforcement Bonus and is the
  incoherence this file has measured before. But Coruscant was 7 of 8 Galactic Republic under an
  all-MAXED Republic capital and lost anyway. **So "coherence" is not the whole story and I should not
  pretend it is.** What both losses share is that a human picked the ships by power while the win came
  from the game's own suggestion.
- ⚠ **The starting three are not the highest-power three.** On Coruscant the picks were consumed in
  power order, so Umbaran Starfighter and Outrider opened instead of the meta pair (Anakin's Eta-2 and
  Blade of Dorin). In a fleet battle the opening three set the whole tempo.
- ⇒ **Next phase: take the auto-fill's fleet, check only that the gate ship is present and that no
  ship it picked is needed by a later fleet row, and press BATTLE.** Rebuild only against a published
  lineup for that exact node, never against a power sort.
- The capital picker appears once the obvious capital is already spent, and it prints **ability levels**:
  Negotiator all MAXED, Home One Level 6, Endurance Level 3, Raddus Level 1, Executrix Level 7,
  Finalizer Level 4, Malevolence Level 1. Worth reading before choosing.

### Corrections to this file and to CLAUDE.md
- ⛔ **"A 0/2 wipe pays NOTHING" (2026-08-09) is WRONG.** Both wipes still printed
  `Astra: Deployed <squad power> points`. The Bounty Hunter 0/2 banked 166,855 and the Mustafar fleet
  0/1 banked 706,160. A loss forfeits the mission prize, never the deployment.
- ⛔ **The Corellia special pays 15 Mk III Guild Event Tokens per clear, not 800.** The panel prints
  `15` next to the token icon plus `Total Earned / Successful Attempts`. `TACTICS` said 800.
- ⭐ **The Lord Vader row is a HARD solo.** The other four slots read
  `This slot is unavailable due to slot restrictions`, so there is no decision to make.
- ⭐ **Mustafar battles hand you ORBITAL BOMBARDMENT as a battle button**, bottom right of the ability
  row at **(1592,819)**, and it is free opening damage that goes on cooldown (13%) once fired. Fire it
  on turn 1 of every Mustafar battle before switching AUTO on. Coruscant's equivalent was still
  charging at 10% and never became available.
- ⚠ **AUTO is at (276,63), not (222,63).** A tap at 222 lands between the buttons, and the battle then
  sits on turn 1 with every enemy at full health for as long as you leave it. Four minutes were lost to
  that before the first fight even started.
- ⚠ **A required mission unit cannot be moved out of the leader slot.** On the Mace Windu / Kit Fisto
  row Mace occupies slot 1 and therefore LEADS; the community's "JMK lead" is not fieldable. Removing
  him raises `REQUIRED MISSION UNIT · Required mission units cannot be removed`.
- ⚠ **Hermit Yoda is not eligible for the Coruscant 5x Jedi row** (`None of the units in this filter
  can be used in this mission`), although Grand Master Yoda is. Do not plan him into it.

### The squad picker, which is where the session actually lost time
- The filter dropdown opens a checkbox grid **plus a free TEXT SEARCH box** at the bottom. Type, press
  the IME `OK` at (1840,1014), and the filter becomes `TEXT SEARCH`.
- ⚠ **The search matches ABILITY TEXT, not just names.** `"Grand Inquisitor"` returns **The Stranger**
  first, `"Sith Marauder"` returns The Stranger, `"General Skywalker"` returns Ahsoka Tano, and
  `"BT-1"` helpfully returns 0-0-0 as well. **Identify every pick by its POWER against the roster
  before tapping**, never by list position alone.
- Parentheses break `adb shell input text`; search `Bastila`, not `Bastila Shan (Fallen)`.
- Character screen tiles: two columns at x 129 / 340, rows at y 550, 800. **The FLEET screen list sits
  lower: x 129 / 340, rows 667, 917.** Reusing the character offsets on the fleet screen taps the
  faction dropdown instead and silently opens the filter dialog.
- `CLEAR SQUAD` (750,1005) leaves mission units in place, which is what you want every time.
- ⚠ **The in-game auto-fill grabbed JABBA for the Aphra row**, exactly as the 2026-08-19 entry warns.
  Clear the squad before building anything.

### Deployment, and the guild's territory notes
Notes read **Corellia `3*`**, **Coruscant `3*`**, **Mustafar `Do not 1* preload only`**. Mustafar was
the laggard all night (49.3M against a 116.4M gate) and the other two were within reach, so the
10,107,895 of unallocated GP went to **Coruscant**, which needed 12,274,762 and finished the session at
**114,239,383, i.e. 2,166,867 short of its first star**. Corellia needed 16.3M and Mustafar 68M.
⚠ The Mustafar note is genuinely ambiguous and I did not resolve it. Ask the officers what it means
before next phase rather than guessing again.

## 2026-09-15 (02:10-04:00) — the dailies, run mostly by the FARMBOT, and three config facts
Second half of the same night as the RotE phase-1 session above. Daily reset had happened at ~02:10.
Finished **8/8 daily quests + the all-quests crate**, **raid tickets 600/600**, **fleet arena #9 -> #1**.

### ⭐ THE FARMBOT IS THE RIGHT TOOL AND IT WAS NOT SET UP
`farmbot/config.json` is **gitignored** (`.gitignore:28`) and had vanished along with the repo's
`.venv`, so the bot looked absent. It is not: `cp farmbot/config.example.json farmbot/config.json`
restores the full documented 19-entry routine and `--doctor` reported PREFLIGHT OK with every
blocking template present. One 33-minute unattended run did 4 energy nodes, 2 challenge multi-sims,
Galactic War restart+sim, 6 collects, the Coliseum battle, the free Bronzium and a shop buy, and it
cost ZERO of the session image budget because its vision never goes through Read. **Run it first,
every time, and hand-play only what its report lists as "still yours".**
- ⚠ `.venv` points at `~/Downloads/swvenv`, which no longer exists. A throwaway
  `uv venv /tmp/swvenv` + `uv pip install pytest pillow numpy scipy defusedxml opencv-python-headless`
  runs both the bot and the 518-test suite. Put the real venv outside ~/Downloads.
- ⚠ The routine still has a `login_august` entry. In September its `cal_tab_august` cannot match, so
  it halts at NAV_2 twice per run. Harmless, but rename it to the live month.
- ⚠ The bot must start ON THE HUB. Leaving the device inside any dialog halts it at OPEN_CAMPAIGNS
  before it does anything.

### ⭐⭐ CANTINA 1-A WAS COSTING THE ACCOUNT ITS BIGGEST RELIC LINE, AND THE FIX WAS ALREADY CAPTURED
The first run halted at SELECT_NODE and left **339 of 339 cantina energy unspent**, because
`node_cantina_1-A_sel` was never captured and the map keeps the last node SELECTED.
That forced a look at which cantina node is even correct, and `data/economy.json` already answered it:
`nodes.flawed_signal_data = Cantina 8-G`, and **Flawed Signal Data is the largest single line in every
relic recipe from R6 to R9 (35 / 45 / 55 / 45) with NO store route at all**. The example config's own
comment called 1-A "SUBOPTIMAL and knowingly so", kept only because better nodes had no template.
**`node_cantina_8-G` and `node_cantina_8-G_sel` were both already captured and sitting in the UNUSED
list.** Swapped in `config.example.json`; a one-entry run then spent 336 of 339 energy cleanly.
⇒ Before accepting any "we kept the worse option because no template exists", check the unused list.

### ⭐ GUILD EVENTS STORE: THE TWO SIGNAL-DATA CURRENCIES ARE NOW VERIFIED
`economy.json` carried "which of GET1/GET2/GET3 pays for it was NOT verified". Watching the balances:
- **Fragmented Signal Data, 20 for 1,600 -> Mk II tokens** (32.9K to 31.3K).
- **Incomplete Signal Data, 20 for 2,000 -> Mk III tokens** (2,255 to 255).
⚠ The second one matters more than it looks. CLAUDE.md says **aeromagnifiers are the one material
that FORCES Mk III**, and a single Incomplete Signal Data purchase drains a whole day of Mk III float.
Both are now recorded in `routes`. Choose between them deliberately next time; today's purchase was
made to close the shipments quest and the currency was only checked afterwards.

### ⚠ THE RAID-TICKET METER IS NOT THE "USE 600 ENERGY" QUEST, AND IT RESETS ON ITS OWN CLOCK
The daily quest read **600/600** while `Quests > Guild Activities > Personal Raid Tickets` read
**336/600** at the same moment. The ticket meter had reset part-way through the night, so the
farmbot's 237 energy was spent before the reset and never counted. **Read the ticket meter directly;
never infer it from the energy quest.** Topping it up took 216 energy through Light Side 1-F normal
(6 energy a sim, 36 sims) and 100 through Fleet 2-E normal, which closed it at 600/600.
- Hard nodes cap at 5 attempts a day and were already spent by the bot, so the top-up has to go
  through NORMAL-difficulty nodes. `node_light_1-D` does not match on the normal tab.

### Fleet arena: two battles, #9 to #1
The arena fleet was already the repo's `Leviathan Arena` build (Fury / B-28 / TIE Dagger starters,
601,709). Beat #5 at 479,440, then **#1 at 462,805**. Both on AUTO at 4x.
⚠ There is a **~5 minute cooldown between arena battles**, skippable only for 50 crystals. Plan other
work into that gap rather than waiting. Squad arena was already #1 and was left alone; it had slipped
to #3 by the end of the session, which is normal shard churn.

### Coliseum: the boss is the KRAYT DRAGON and auto tops out around 90%
Tier 7, high score **316,160 = 90%**, rewards banked up to the 90% rung, **100% still open** with 3
attempts left. A second auto attempt scored 285,289 (81%), so the spread on this squad is 81-90% and
100% is not reachable by pressing AUTO. High score is BEST-OF, so extra attempts can never lose ground.
- The squad is entirely **LOANED** and already contains **Yoda (Dark Side Vision) + Mara Jade
  Skywalker**, which are the core of holotables' top three Krayt comps; the leader is Darth Maul where
  the #1 comp uses Moff Gideon.
- Mechanics worth playing around next time: every character turn feeds 1% Enrage and **turn-meter
  removal actively hurts you**; damage taken by the dragon is **+75% while it has no bonus
  Protection**; and score snowballs, +3% stacking Offense per 5,000 points past 50,000, growing by a
  further 3% each time. Sources: holotables.xyz/boss/krayt-dragon, ahnaldt101.com/swgoh/coliseum.

### Smaller facts
- **Marquee "Blade and Bastion"** (Stormtrooper Concept): tiers I-IV SIM with sim tickets, 20 -> 30
  shards. **Tier V is gated on the unit at 6 stars**, so the ladder stops there until he is farmed.
- **Kyrotech Ascension is NOT an event.** It is a paid store pack ladder, tier 1 at EUR 2.49, and
  Egnards' valuation piece warns that some tiers are negative value. Nothing to claim, nothing to do.
- Conquest and the guild raid are both INACTIVE. The bot halted at SECTOR_LIST and OUTCOME_0
  respectively, which is the safety check working, not a failure.
- **Character Quests and the Collection dot are the only red dots left on purpose.** Both are the
  character-improvement rail, which the standing rule says to leave alone.

## 2026-09-15 (07:45) — COLISEUM: the Krayt Dragon squad, measured
Tier 7, one attempt left, boss rotating in 13h. Researched the comp, swapped ONE unit, and the score
went **338,278 (96%) -> 344,942 (98%)**, a new high score. 100% (~352,400) was not reached and no
attempts remained, so the 100% reward rung and Tier 8 are still locked. Rank 333 -> 336.

### ⭐ THE COMP, AND THE ONE UNIT THAT WAS WRONG
The Coliseum hands you a pool of **LOANED** units and you pick five; nothing here comes off the roster,
so this is pure selection and it transfers to every account.
**Field: Jedi Knight Luke Skywalker (leader, "Return of the Jedi") / Darth Talon / Mara Jade Skywalker
/ Yoda (Dark Side Vision) / Stormtrooper (Concept).**
That is Holotables' #4 Krayt squad verbatim (T11 82%, "its all about the counters" and not getting
dazed). The game's own pre-fill had **Starkiller (Luke Concept)** in Talon's slot, and swapping only
that one unit was worth +2 percentage points on AUTO with nothing else changed.
- Two independent reasons Starkiller was the weak slot: a T7 guide author says outright he is looking
  for "a character able to boost defenses, which may work better than Cal, **Starkiller**, or even
  Moff"; and mechanically the win condition is stripping DEFIANCE with debuff spam, which is Darth
  Talon's kit and not Starkiller's burst.
- Holotables' other top comps, for when the loaned pool rotates: **#1 T12** Moff Gideon (L) / Yoda
  (DSV) / Mara Jade Skywalker / Darth Talon / Dark Trooper. **#2 T11 95%** JKLS (L) / Mara Jade
  Skywalker / Jedi Knight Cal Kestis / Mace Windu / Chewbacca. **#3 T11 83%** same as #2 with Barriss
  Offee for Chewbacca, "call Mace to assist".
- **Mara Jade Skywalker and Yoda (Dark Side Vision) appear in all four top comps.** Treat them as
  auto-includes and spend the thinking on the other three.
- Astra's live loaned pool on this rotation also held Chewbacca, Moff Gideon and a Dark Trooper, so
  #1 and #2 were both buildable. Searching the pool by name works: the filter's TEXT SEARCH box is on
  this screen too.

### The mechanics that decide the score, none of which AUTO plays around
- **Enrage clock**: +1% per character turn, +4% and 4 Defiance on each of the dragon's turns. At 100%
  it Enrages and the battle ends 5 turns later. ⚠ **Removing its turn meter FEEDS Enrage**, 1% per 10%
  removed, so TM-control units are actively bad here.
- **The burst window**: damage it takes is **+75% while it has no bonus Protection**. While it holds
  bonus Protection it cannot lose Defiance, Health or Turn Meter at all. Save everything for the gap.
- **Swallow**: strips the unit's buffs and gives the dragon 20 Defiance; the unit only returns when
  Defiance is fully stripped, which is why debuff spam is the core loop. Corrosive Venom Spray
  instantly kills whoever is Swallowed.
- **Score snowballs**: past 50,000, every 5,000 points grants a stacking +3% Offense, and the bonus
  grows by another 3% each time. Early damage is worth more than late damage.
⇒ AUTO with this squad lands **81-98%** across four observed runs. The last 2 points almost certainly
need a manual run that holds fire for the no-Protection windows. Budget the attempts for that next
rotation rather than spending them all on AUTO.

### Housekeeping
- **Attempts are 5/day and the button becomes a 250-crystal refresh once spent**, which is never worth
  buying. High score is BEST-OF, so an attempt can never lose ground; the only cost of a bad run is
  the attempt itself.
- The reward ladder rungs are at 70 / 77 / 80 / 90 / 100 percent. **98% earns nothing that 90% did
  not**, so the whole game at this tier is reaching exactly 100.
Sources: holotables.xyz/boss/krayt-dragon (919 submitted squads, filterable by ally code),
ahnaldt101.com/swgoh/coliseum.

## 2026-09-15 evening — RotE PHASE 2 played live, and six rules this repo had wrong

Phase 2/6 (Geonosis / Felucia / Bracca, relic floor R6) was live from ~20:00 with 22h51m on the
clock. Guild #2 of 56 stars at start. Everything below is device-verified, not inferred.

### Board at the end of the session (23:35)
| Territory | Stars | TP | Thresholds | Note on the panel |
|---|---|---|---|---|
| Corellia (P1) | 3★ | 238,333,333 / 238,333,333 | 112 / 179 / 238M | "3* go for broke." MAXED |
| Coruscant (P1) | 3★ | 248,333,333 / 248,333,333 | 116 / 186 / 248M | "3*" MAXED |
| Mustafar (P1) | 1★ | **180,659,382 / 186,250,000** | 116 / 186 / 248M | "3*" |
| Geonosis (P2) | 0★ | 0 / 148,125,000 | 148 / 237 / 316M | **LOCKED** |
| Felucia (P2) | 0★ | 29,213,866 / 148,125,000 | 148 / 237 / 316M | "ops n combat" |
| Bracca (P2) | 0★ | 18,014,120 / 142,265,625 | 142 / 228 / 304M | "ops n combat" |

### ⭐⭐ 1. OPERATIONS ARE THE WHOLE GAME, AND THEY PAY 11,000,000 IN PHASE 2
Six operations per territory, 15 unit-slots each, **+11,000,000 TP each** on completion (phase-1
Mustafar and Corellia groups pay 10,000,000 and were already 6/6 full). **A player may assign only
10 units per territory's operation GROUP** ("Assigned Units: n/10"), gate R6+ characters and 7-star
ships. Partial fills pay NOTHING; only 15/15 pays.
⇒ **One operation is worth 44 ground combat missions.** Fill them before anything else.
Measured tonight: 10 units into Felucia (Op1 6→14/15, Op2 8→13/15, Op5 2→5/15) and 10 into Bracca
(Op1 10→14/15, Op2 8→11/15, Op3 5→8/15). Three of those four near-complete operations were then
finished by guildmates: Bracca went 1.4M to 13.96M and Felucia 0.87M to 28.9M within the hour.
**That is 33,000,000 TP that 16 of my units helped unlock**, against 1,475,000 from every combat
mission I won all night.

### ⚠ 2. THREE TRAPS IN THE OPERATION UI, ALL OF WHICH COST SOMETHING TONIGHT
- **It is a RACE.** Staging 8 slots then pressing ASSIGN lost 6 of them to guildmate "Leiferman",
  who committed the same units in the seconds between. Assign in small batches and re-read the grid.
- ⛔ **"Unit Required in another Territory" is a real warning and it FORECLOSES MISSIONS.** Accepting
  it for one ship locked **Scythe** into a Felucia platoon, which killed the **Mustafar fleet mission
  worth 400,000 TP** ("REQUIRED UNITS 2/3", unplayable). The same thing happened to **Jabba the Hutt**,
  which killed Felucia's Jabba-gated row (250,000). **Open every gated row and write down its named
  unit BEFORE filling any platoon.**
- Red-tinted slots are units you do not own or cannot field. They are why 14/15 happens and why you
  should count them before choosing which operation to concentrate on.

### ⭐ 3. A STARRED TERRITORY DOES NOT LOCK. CLAUDE.md IS WRONG ABOUT THIS.
CLAUDE.md says "a territory that did star locks at the end of its phase, so you can never come back
for its 2nd and 3rd stars." False. Mustafar had 1★ and every one of its combat missions was reset to
`BATTLE (1)` in phase 2, with the guild pushing it 118M to 180M. Corellia and Coruscant are open too,
merely pointless. **Previous phases' planets stay playable for the whole event.**

### ⛔ 4. THE UNLOCK RULE IS REAL, AND MISSING IT COSTS A WHOLE TERRITORY
Geonosis reads `0 / 148,125,000` with DEPLOY greyed to **LOCKED**. Cause: a planet opens only when its
predecessor held a star at a PHASE BOUNDARY, and Mustafar's 1st star landed *during* phase 2 (118.3M
against a 116M threshold an hour in). The Dark Side lane is therefore a full phase behind and
**Geonosis opens in phase 3**. ⇒ Getting a predecessor over its 1st star BEFORE the rollover is worth
an entire territory, which is a guild-level scheduling argument, not a personal one.

### ⭐ 5. A LOST COMBAT MISSION STILL DEPLOYS THE SQUAD'S FULL GP
Verified twice: lost a row 0/2 and the feed still logged "Astra: Deployed 160,925 points". Only the
mission bonus is forfeit. **Forfeiting mid-battle also pays the TP earned so far**, and the game says
so on the confirm dialog. ⇒ Combat rows are upside-only, so do not agonise over squads; spend the
care on gated rows and fleets instead.
⚠ **But a full 5-unit squad is MANDATORY.** Undersizing is rejected outright with "You don't meet the
minimum number of units required for this mission". That is the opposite of TW and it silently
blocked three battles tonight before I read the dialog.

### 6. WHAT EACH ROW ACTUALLY PAYS (read off the panels, they differ)
Mustafar ground **200,000** · Bracca ground **250,000** · Felucia ground **250,000** ·
Mustafar fleet **400,000** · Bracca fleet **500,000** · Felucia fleet **500,000**.
⇒ **Fleet rows are worth 2x a ground row and should be played FIRST**, with a researched lineup.

### Results, squad by squad
| Territory | Row | Squad | Result |
|---|---|---|---|
| Mustafar | Lord Vader solo | LORDVADER R10, Orbital Bombardment turn 1 then AUTO | WIN 2/2 **+200,000** |
| Mustafar | DS (Separatist droids) | Darth Revan (L) / Malgus / HK-47 / Sith Empire Trooper / Bastila Fallen, 160,925 | **LOSS 0/2** |
| Mustafar | DS | SLKR (L) / Kylo Ren Unmasked / Sith Trooper / Phasma / FO Officer, 170,460 | WIN 2/2 **+200,000** |
| Mustafar | DS | Sith Eternal Emperor (L) / Rey DSV / Darth Malak / Emperor Palpatine / Darth Traya, 199,551 | WIN 2/2 **+200,000** |
| Mustafar | fleet 400k | none | BLOCKED, Scythe in a platoon |
| Bracca | LS row | JML (L) / General Kenobi / Ezra Bridger (Exile) / Jedi Knight Luke / Ahsoka Snips, 198,622 | WIN **+250,000** |
| Bracca | LS row | Satele Shan (L) / Kelleran Beq / Jocasta Nu / Jolee Bindo / Hermit Yoda, 169,971 | LOSS |
| Bracca | LS row | GL Rey (L) / Captain Drogan / Commander Luke / Rotta / Mace Windu, 214,800 | WIN **+250,000** |
| Bracca | fleet 500k | Negotiator + GR starfighters, auto-fill, 631,697 | **LOSS** |
| Felucia | younglando | auto-fill, 206,282 | 1 of 2 waves **+125,000** |
| Felucia | mixed | auto-fill, 208,425 | WIN **+250,000** |
| Felucia | jabba | none | BLOCKED, Jabba in a platoon |
| Felucia | Hondo row | auto-fill, 203,718 | stalemate in wave 2, FORFEITED |
| Felucia | fleet 500k | **Leviathan** MAXED, 726,158 | **LOSS** |

⚠ **The Revan loss was my own substitution error.** This file already records the measured winner for
that row as SEE-led Sith Empire; I swapped in a Darth Revan lead, which has no mass dispel for the
Droideka plus MagnaGuard taunt wall the note explicitly warns about. **Use the recorded comp.**
⚠ **Both fleets lost, and a guildmate won the same Felucia row for 500,000 with the same mission.**
The capital was almost certainly right (Leviathan, all abilities MAXED, on a no-alignment-filter
planet); what I let the game choose was the **reinforcement order**. That is the thing to research.

### Deployment
Ended with **Unallocated: 10,773,814** and put all of it on Mustafar, taking it 169,885,568 to
**180,659,382**, i.e. 5,590,618 from its 2nd star. Chosen over Felucia and Bracca because only
Mustafar was within reach of a threshold, and because the officer notes read "3*" on Mustafar and
"ops n combat" on the other two. ⇒ **Deploy LAST and deploy to the territory nearest a threshold**,
not to the one furthest behind.

### The Zeffo bonus zone, in full
Bracca's panel carries `Bonus: Zeffo`, and the zone's own panel prints the unlock conditions:
**"Earn Stars in Bracca: 0/1"** AND **"Complete Special Mission 30 Times: 0/30"**. So Zeffo needs a
Bracca star and thirty guild clears of the Bracca special. Bracca finished the session at 18.0M
against a 142.3M first star, so **Zeffo could not unlock this phase whatever I did**, which is why the
deploy-all was taken over reserving Cere Junda and Cal Kestis for one clear. Both are R7 and both
clear the special's R7 gate, so they are available whenever the Bracca star becomes reachable.
✅ Re-confirmed, and the repo already had it right: the Felucia HONDO row carries the *id* `special`
but its `kind` is `combat`, and `rote_missions.py` line 107 records exactly why (device-verified
2026-08-19). The panel reads "Combat Mission, 5x characters (Relic 6+), Hondo Ohnaka", up to 250,000
TP, `BATTLE (1)`. **Only Bracca `unlock_zeffo` is a true one-shot special in this phase.** I briefly
"fixed" the JSON by renaming that id, which would have broken the `(2, "Felucia", "special")` TACTICS
key; the JSON is GENERATED, so edit `rote_missions.py` and re-run `--write`, never the JSON.

### Tooling added
`scripts/ocr.sh` and `scripts/tapword.sh`. The image budget, not the token budget, is what kills a
long device session (30MB of base64 and the API call dies). Tesseract reads the RESULTS banner, the
territory counter and the activity feed for zero budget, and `tapword.sh` locates a label by its
bounding box so a scrolling filter list can be hit reliably instead of by dead reckoning.
⚠ **tesseract cannot read from /tmp under the Bash sandbox** ("failed to open locally"). Both scripts
write to ~/Downloads for that reason. Do not move them back.
⚠ A useful trick that costs nothing: **verify a win by arithmetic.** The territory delta equals the
mission TP plus the squad's GP, so 448,622 after a 198,622 squad proves a 250,000 clear.

## 2026-09-16 early hours — arena rank 1, and why AUTO is the wrong tool twice over

### Results
- **SQUAD ARENA #3 -> #1**, one battle. **FLEET ARENA #13 -> #2**, three wins and two losses.
- **Dailies 8/8** plus the COMPLETE ALL QUESTS crate. Episode Track 800 -> 1,400 / 5,000.
- ~780 energy spent: 384 normal (Naboo 1-F x64), 140 ship (x14), 112 cantina (**Mandalore 8-G** x7,
  the Flawed Signal Data node, which was already the selected node), 144 mod (x8).

### ⭐ THE SQUAD ARENA ANSWER IS THE DATACRON, NOT THE POWER
Climbed with **Rotta the Hutt (L, "A Legacy Reforged") / Gamorrean Guard / Greedo / Krrsantan /
Mob Enforcer at 165,133**, behind the **level-15 set-33 Hutt datacron**. The saved squad had
Krrsantan AND Boushh, so only three units sat inside the cron's scope (`raccoon`, `cadbane`,
`greedo`, `gamorreanguard`, `humanthug`); swapping Boushh out for **Greedo** puts four inside it and
is worth more than the ~6k raw power it costs. Rank #1 on the shard was only 148,402.
⚠ **CAD BANE COULD NOT BE FIELDED** in the arena picker ("None of the units in this filter can be
used in this mission"), which is the only reason Krrsantan keeps the fifth slot. Find out why.
⭐ **Defence is the squad you LAST ATTACKED WITH**, so this squad is now the parked defence too.
That is the real reason to get the composition right before the final attack of a session.

### ⛔ BOTH FLEET LOSSES WERE THE SAME MIRROR, ON AUTO, WHILE HOLDING THE POWER EDGE
Rank #1 "VERSO" runs a **Leviathan mirror at 587,691** against my **606,832**, and beat me twice on
auto. Kahzgul rates the mirror at a **99% win rate on offence**, so this is execution, not matchup.
The published offence line is **Sabotage the Engines -> reinforce Scimitar -> Sabotage the Hangars
-> reinforce Mark VI Interceptor**, and auto never fires it. Every ship is owned:
`SITHINFILTRATOR` = Scimitar, `SITHSUPREMACYCLASS` = Mark VI Interceptor, and my starting three
(`SITHBOMBER` B-28, `TIEDAGGER`, `FURYCLASSINTERCEPTOR`) are already the meta trio.
⇒ **Play the mirror manually.** Source: kahzgul.substack.com/p/leviathan-counters.

### Arena mechanics worth knowing before the next climb
- **There is a ~5-6 minute cooldown between arena battles.** A BATTLE tap during it does nothing,
  silently, and consumes no attempt. Budget ~30 minutes of wall clock for a 5-battle climb.
- **"Your opponent's rank is no longer valid" costs no attempt.** Refresh the board and re-pick.
- Beating an opponent **swaps ranks**, and the board offers about 5 ranks above you, so the ladder
  collapses quickly: #13 -> #8 -> #4 -> #2 in three wins.
- **Payouts are what matter, not the rank right now.** Squad ~16:55, fleet ~17:50. Both get knocked
  down overnight, so the real climb belongs in the hour before payout with all 5 battles in hand.
- ⚠ **OCR reads 5 as 9 in this font.** Rank #1's power scanned as 987,691 when it was 587,691, which
  nearly made me skip an attackable target. Re-crop any suspiciously large number before deciding.

### Dailies: the fast path
- **MULTI SIM clears the Challenges dailies in one tap** (10 battles) and **Galactic War in one**
  (12 battles). GW needs **RESTART** first if its board is already cleared, which greys Multi Sim.
- ⛔ **The Featured Shipment store charges CRYSTALS** (400/320/320). The "Purchase 3 store Shipments"
  daily belongs in **Shipments > Guild Activity**, which charges guild tokens. Bought Mk 2 Pulse
  Modulator x6 (900, mod SLICING salvage, the documented binding constraint), Mk 9 BioTech Implant
  Salvage x10 (380), Mk 6 Arakyd Droid Caller Salvage x20 (760).
- The purchase dialog's **BUY** button sits at a different height per item, because the description
  length moves it. Read the dialog title's y and offset from that rather than hardcoding.
- Bonus Energy claims run on their own clock, roughly 11:00 and 17:00.

### Coliseum rotated to ZEFFO TOMB GUARDIANS: researched, then deliberately left alone
High score **196,314 (43%)**, rank 98, **4 of 5 attempts unspent on purpose**.
**Armor Plating**: 3 stacks at start, +2 at the start of each of its turns, cap 3, **-25% damage
received per stack**, and **one stack falls off per attack that damages it**. So the loop is strip
3 -> 0 with separate cheap hits, then burst in the window. Punishments: damaging it at 0 stacks makes
its next Special **+100% stronger, stacking**; **ten consecutive 1-damage hits give it +1000%
damage**; ten consecutive enemy turns give it +30% Offense, +200 Speed, a bonus turn and a full
dispel. Immune to Ability Block, Buff Disruption, Daze, Distracted, Fear, Health Down, Shock,
Stagger, Stun. ⇒ **AUTO chips, which is precisely what this boss punishes**, so burning the other
four attempts on auto would be the definition of a wasted attempt.
Community #1 (holotables.xyz/boss/zeffo-tomb-guardians, 963 submissions) is **JKL (L, loaned) /
Mara Jade Skywalker / JK Cal Kestis (loaned) / Barriss Offee (loaned) / Yoda (Dark Side Vision)**
at T11 75%. Saved in the slot now: **Darth Maul (L, loaned) / Yoda (DSV) / JK Cal Kestis / Mara Jade
Skywalker / Barriss Offee**. ⚠ **The loaned Jedi Knight Luke shows in the picker but will not place**,
which is the only reason Maul leads.

### Coliseum squad-screen traps
- **The filter's CONFIRM stays greyed until something is selected**; after clearing the text box you
  must tick **ALL** before it goes live.
- **Text search matches anywhere in the name**: "Cal" returns Young Lando **Cal**rissian. Use "Kestis".
- Slot taps and CLEAR SQUAD do work, but the name-band OCR lags a frame, so re-read before concluding
  a tap failed. Two taps were wasted chasing a phantom failure.

## 2026-09-16 evening — RotE PHASE 3 played, and the fleet doctrine is now inverted
Phase 3/6 opened ~20:22 Athens. Guild GP 518.2M, **11/56 stars at start, 12/56 at the end**
(Bracca earned its first). Astra went #1 -> #3 on the contributor board as guildmates pushed.
Board at the end: Mustafar/Corellia/Coruscant 3★ MAXED · Bracca **176,032,389 / 227,625,000 (1★)** ·
Felucia 268,633,501 / 316,000,000 (2★) · Geonosis 38,128,365 / 148,125,000 · Tatooine
18,238,567 / 190,953,125 · **Dathomir and Kashyyyk LOCKED** (their predecessors held no star at the
phase boundary, so the DS and LS lanes are each a full phase behind).

### ⛔⛔ THE GUILD ORDER IS AN IN-GAME MECHANIC, NOT JUST A GOLD NOTE
Pressing ASSIGN on a **Bracca operation** raised **"Disobey Guild Order. One of the officers of your
guild has flagged this mission to be ignored. Are you sure you want to disobey orders?"** with
`DISOBEY ORDER` (red) and `BACK TO MAP` (green, ~(1187,691)). Obeyed, no Bracca operations filled.
- **The red no-entry overlay on a map marker IS that flag.** On Bracca it sat on the operations
  square and the deploy chevron; the 3 combat pins, the fleet pin and the Zeffo special had none and
  raised no dialog. Deployment to Bracca also raised no dialog, so **the flag is per-mission, and the
  overlay is the only advance warning. Read it before planning a territory.**
- ⚠ The dialog is centred at y≈691, nowhere near ASSIGN at (1166,988), so a blind ASSIGN tap does
  NOTHING and the operation silently stays unchanged. Two assigns were lost that way before the
  modal was noticed. **Re-read the fill count after every assign.**

### OPERATIONS: the pay scale, and one label that nearly cost 79M
**Tatooine (P3) pays 13,200,000 per completed operation; Geonosis and Bracca (P2) pay 11,000,000.**
Gate is R7+ on Tatooine, R6+ on the P2 planets, 7★ ships everywhere. Quota is 10 units per territory.
- ⛔ **"(Full Strength)" is the ABILITY level, not the fill count.** Felucia's *friendly* ability read
  "Profitable Ventures (Full Strength)" with the bar at 6/6 and was genuinely done. Tatooine's
  *enemy* ability read "Wretched Hive (Full Strength)" with the bar at **0/6** and the scale running
  **Lvl 3 -> Lvl 2 -> Lvl 1 -> Disabled**: six operations still to fill, worth 79.2M. Friendly
  abilities are strengthened, enemy abilities are weakened. **Read the bar, never the parenthetical.**
- Assigned: **Tatooine 10/10** (Op1 8->13/15, Op5 4->9/15), **Geonosis 7/10** (Op1 6->8/15,
  Op2 5->10/15). Bracca untouched (flagged). Felucia already 6/6.
- **A platoon assignment banks the unit's GP as territory points immediately** (the feed logged
  "Astra: Deployed 174,577 points" seconds after ASSIGN).
- Duplicate slots inside one operation want the SAME unit; the second tap raises
  `DUPLICATE UNIT SELECTION` (OK at (948,690)) and that modal then swallows the following taps.
- ⭐ **Keep Galactic Legends out of platoons whenever a non-GL slot is available.** JML was
  auto-staged into Tatooine Op5 and swapped for Starkiller. SEE and Darth Maul did go in, and both
  then rendered RED (unavailable) in Geonosis Op1: the cross-territory lock is real and visible.

### ⭐⭐ THE FLEET RULE FROM PHASE 1 IS WRONG, AND THIS IS THE MEASUREMENT THAT INVERTS IT
Phase 1 concluded "take the game's auto-fill and press BATTLE". On Tatooine (gate ship **Executor**)
the auto-fill produced a power-sorted incoherent mix, Executor plus Rebel B-wing, Han's Millennium
Falcon and Emperor's Shuttle at **706,848**: the same shape as both phase-1 losses and the phase-2
losses. Replacing it with the repo's own **`build_fleets.FLEET_LINEUPS["Executor"]`** (Hound's Tooth /
Punishing One / Razor Crest starting, reinforcing Xanadu Blood / Slave I / IG-2000 / Ebon Hawk) at a
LOWER **626,875** won immediately for **+682,500 TP**.
⇒ The phase-1 Corellia win only looked like "auto-fill works" because the gate ship there (Lando's
Millennium Falcon) forced the auto-fill into that same Bounty Hunter lineup. **The auto-fill is a
power sort. Field the coherent published lineup.**
- ⭐ **`SELECT FLEET` loads saved presets and is the fast path.** Leviathan, Executor, Negotiator,
  Home One and Raddus are already saved on the account. The Executor preset was one reinforcement
  short at 547,975; adding **Ebon Hawk** took it to 626,875, within 0.4% of the 629,354 that won in P1.
- ⚠ **A fleet with an empty slot refuses to start**: "You are attempting to enter battle with a squad
  that is not full", and the BATTLE tap just does nothing until you acknowledge it. Fill all 7
  non-capital slots.
- ⚠ **The capital picker prints ability levels and is worth reading.** Negotiator is the only owned
  Light Side capital with everything MAXED (Endurance L3, Home One L6, Raddus L1).
- The other two fleets both LOST: Bracca (Light Side ships, saved **Negotiator** preset 619,465) and
  Geonosis (Dark Side ships, **Leviathan** preset 521,479 topped up to 619,552 with the
  highest-power ship on the list). **Power was not the difference; the Executor fleet is coherent
  Bounty Hunter and the other two were not.** Next phase: top a preset up with a ship of the
  SAME faction, not the top of the list.

### ⭐ AN UNGATED COMBAT ROW STILL WANTS A GALACTIC LEGEND
`missions_3.json` sent the Empire core (Palpatine / Thrawn / Mara Jade / Royal Guard / Vader Duel's
End, 156,285) to the Tatooine `mixed` row because it is the GAC front_top #4 wall. It went **1/2,
+162,500 of 325,000**. Every GL-led squad this session went 2/2. The phase-1 rule outranks the GAC
tier list: **on a row with no unit gate, lead with a GL.** A GAC hold rate does not predict a TB clear.
`rote_missions.py` now says so on that row.

### Results, mission by mission
| Mission | Squad | Result |
|---|---|---|
| Tatooine **Reva special** | GI (L) / Fifth Brother / Seventh Sister / **Inquisitor Barriss** / Second Sister, 160,065 | **WON**, guild 1/50 -> 2/50 |
| Tatooine **Mandalore special** (Krayt Dragon) | Bo-Katan Mand'alor (L) / **IG-12 & Grogu** / Mando Beskar, 101,884 | **WON**, bonus zone 3% -> 7% |
| Tatooine **fleet** | Executor lineup, 626,875 | **WON +682,500** |
| Tatooine **fennec** | Bossk (L) / Fennec / Boba / Zam / Embo, 164,093 | **WON** (341,250) |
| Tatooine **jabba** | Jabba (L) / Cad Bane / Greedo / Gamorrean Guard / Mob Enforcer, 173,304 | **WON** |
| Tatooine **mixed** | Empire core, 156,285 | 1/2, **+162,500** |
| Bracca **Jedi** | JMK (L) / General Skywalker / Ezra (Exile) / Shaak Ti / Mace Windu, 204,009 | 1/2, **+125,000** |
| Bracca **LS row A** | auto-fill, GL Rey led, 217,835 | **WON** |
| Bracca **LS row B** | auto-fill, GL Leia led, 206,430 | **LOST, +0** |
| Bracca **Zeffo special** | Cere Junda + Jedi Knight Cal Kestis, 66,444 | **LOST** |
| Bracca **fleet** | Negotiator preset, 619,465 | **LOST, +0** |
| Geonosis **fleet** | Leviathan preset, 619,552 | **LOST, +0** |
| **DEPLOY** | 10,832,733 unallocated, all to **Bracca** | Bracca 153.2M -> 176.0M |

### The two omicron checks that decided two missions
- ⛔ **`MARROK` has 0 omicrons**, so the current meta Reva answer ("100% FULL AUTO with the Marrok
  omicron", swgohrote.com) is unavailable on this account. **`INQUISITORBARRISS` IS owned** (that is
  the base id; `INQUISITORBARRISSOFFEE` does not exist) at 7★ R7, and swgohrote.com lists
  **"GI (Inq Bariss)"** as the community non-omicron comp. Her dispel-all plus health-equalise on
  Unaligned Force User allies answers the DoT pile-up that is the documented way to lose that node.
  It won first try.
- ⛔ **`JEDIKNIGHTCAL` has 0 omicrons**, and this file already recorded that the Zeffo special runs
  "~2/14 versus ~90.9%" without omicrons on both his leader ability and Impetuous Assault. It lost
  exactly as predicted, Cal dying in wave 1. **Do not spend the Zeffo attempt again until he has
  both.** The loss was still upside-only: the squad's 66,444 GP banked to Bracca.

### Device and UI facts learned tonight
- ⚠ **LARGE UNIT LIMIT is 2 per squad.** The published Tatooine Jabba comp (Jabba / Cad Bane /
  Krrsantan / Rotta / Gamorrean Guard) is **not fieldable**: three of those five are large. Jabba plus
  Gamorrean Guard fills the limit and the third add is refused outright.
- ⚠ **The squad-screen TEXT SEARCH matches ability text, and it silently fields the wrong unit.**
  "Emperor Palpatine" returned **Darth Bane** and he was fielded as leader; "Krrsantan" returned
  **Doctor Aphra**; "Jedi Master Luke" returned **Jedi Master Kenobi**; "General Kenobi" returned
  **General Skywalker**. **Read the slot label after every single add.**
- ⚠ **A CLIENT RESTART mid-session resets a squad you just built** back to the auto-fill, and it does
  NOT consume the mission attempt (verified twice, on the Reva special and the Bracca Jedi row).
  Re-check the squad after any reload. A newsletter popup also lands in front of the hub afterwards.
- **Felucia's combat rows all read COMPLETE (greyed) for me this phase** while Tatooine's, Bracca's
  and Geonosis's read `BATTLE (1)`. **Felucia's DEPLOY button was also greyed** while Bracca's and
  Tatooine's worked. Cause not established; worth pinning down next phase, because it made the
  officer note "Felucia first the rest here" resolve to Bracca in practice.
- **`swgohrote.com` is a live and useful source**: per-node auto-battle teams, phase tabs, a Special
  Missions tab and community suggestions. It is a JS app, so drive it with the Playwright MCP and
  read `document.body.innerText`. Its Mandalore entry ("Bo Katan Mandalore" lead, "IG12",
  *"IG call bo to assist, don't use Birds with BAM. Ballista if someone gets eaten"*) made that
  Krayt Dragon clear work first try.
- The image budget again was the binding constraint, 12MB of 20MB by 22:35. `scripts/ocr.sh`,
  `scripts/tapword.sh` and an 800px/q45 screencap (about 60KB) keep verification nearly free.
- ⚠ `.venv` is a **dangling symlink** to a deleted `~/Downloads/swvenv`, so `pytest` only runs from
  the homebrew interpreter and 10 test modules cannot collect (numpy, PIL). 402 tests pass;
  `tests/test_rote_missions.py` is 20/20.

## 2026-09-17 (00:15-02:30) — dailies 8/8, arena #1/#2, and the farmbot config had drifted
Run straight after the RotE phase-3 session above. **Daily Quests 8/8 plus the all-quests crate**,
**Squad Arena #8 -> #1**, **Fleet Arena #10 -> #2**, **Coliseum 5/5 attempts**.

### The farmbot did the bulk of it, and it costs ZERO image budget
One `--daily` run (29 min, unattended): 5 energy nodes, 2 challenge multi-sims, 7 collects, 1
bonus-energy grant, 1 PvE battle, 1 token purchase, 4 harmless halts. Report at
`farmbot/reports/2026-09-17_0015.md`. The 2026-09-15 advice holds exactly: **run it first, every
time, and hand-play only what its report lists as "still yours".**
- ⚠ **`.venv` is still a dangling symlink to a deleted `~/Downloads/swvenv`.** Rebuild with
  `uv venv /tmp/swvenv && uv pip install --python /tmp/swvenv/bin/python pillow numpy
  opencv-python-headless defusedxml scipy pytest`. That runs the bot and the test suite.
- ⛔ **`farmbot/config.json` is gitignored and HAD DRIFTED from the tracked `config.example.json`.**
  The live file still farmed **cantina 1-A** while the example has carried **cantina 8-G** since
  2026-09-15. 8-G is the Flawed Signal Data node, the largest single line in every relic recipe from
  R6 to R9 with no store route at all. **Diff config.json against config.example.json at the start of
  every run**, because the gitignored file silently survives across sessions and loses fixes.
- The routine still carries a `login_august` entry; in September its `cal_tab_august` cannot match and
  it halts twice. Harmless with `--daily`, and there is no September template captured.

### What the bot will never do, and what each one cost
- ⭐ **SQUAD ARENA #8 -> #1** in two battles with the **Hutt datacron squad** (Rotta the Hutt (L) /
  Gamorrean Guard / Greedo / Krrsantan / Mob Enforcer, 165,133). It beat a **195,973** team and then a
  **181,741** team. Power is not the discriminator here, the level-15 Hutt cron is. Defence is the
  squad you last attacked with, so that squad is now parked correctly.
- ⭐ **FLEET ARENA #10 -> #2** in three battles (606,832). Target selection is the whole game: the
  board offers about five ranks up, and **beating an opponent swaps ranks**, so always attack the
  HIGHEST-ranked opponent you can beat rather than the weakest. #2 at 426,182 was both.
- ⛔ **The #1 fleet (VERSO, 587,691, Leviathan mirror) beat AUTO for the third time.** The repo's fix
  is to play it manually on the published line (Sabotage the Engines, reinforce Scimitar, Sabotage
  the Hangars, reinforce Mark VI Interceptor). **That is not executable over ADB: the fleet battle
  has a FIVE MINUTE timer and one screenshot-decide-tap round trip costs about 10 seconds**, so the
  clock went 4:42 to 3:30 across a single turn before I aborted to auto. Either the owner plays that
  one battle by hand, or the account accepts fleet #2. Do not burn more attempts on auto.
- ⚠ **OCR misreads 5 as 9 in the arena font, again.** #1's power scanned as 987,691 and is 587,691.
  The 2026-09-16 note predicted exactly this. Re-read any suspiciously large number from a crop.
- **Coliseum**: all 5 attempts on auto, high score stuck at **264,585 (81%)** across every one of
  them, next boss in 20h. Auto converges to the same score, so extra attempts add nothing once the
  first has run.
- **Grand Arena**: 3v3, Kyber 3, skill 3,164, Round 1 Setup with 23h left. **Defence was ALREADY
  fully set (5/5, 3/3, 5/5, 5/5)**, carried over, so nothing was donating free banners and it was
  left alone. `gac3v3_board.py --structure balanced` produces a better zone split (net +351, with
  Rey 31.2%, Leia 25.4% and Cassian 25.2% in the FRONTS rather than the back), but it runs off the
  **Season 81** tier list and re-placing all 15 squads is a fresh-session job.

### Closing the last two quests by hand
- **"Use 600 Energy" was stuck at 516/600** and every configured node was exhausted: the two hard
  campaign nodes reported `hard_depleted`, and the mod node reported out of energy despite 229 banked.
  ⭐ **The fix is the quest's own GO button**: it lands on **Light Side 1-A on NORMAL**, which is
  repeatable, costs 6 energy, and offers MULTI SIM. One 38-sim tap spent 228 energy and closed both
  the quest and the raid-ticket meter. **Remember that normal campaign nodes are the energy dump of
  last resort; the farmbot only knows hard nodes, which are attempt-capped.**
- **"Purchase 3 store Shipments"**: use **Shipments > Guild** (gold guild-token prices), never the
  Featured tab, which is crystals. ⚠ **Tapping the item ICON opens an info popup with no BUY button.**
  The purchase control is the **green price button on the tile**, and only then does a BUY confirm
  appear. Three attempts were wasted on the icon before that was clear.
- ⚠ A quest **GO** button can drop you straight into the crystal-priced Featured store. Back out.

### `.venv` rebuilt for real, 2026-09-17 02:20
`.venv` had been a **dangling symlink to a deleted `~/Downloads/swvenv`** since at least 2026-09-15,
which is why `pytest` only ran from the homebrew interpreter and 10 test modules could not collect.
Replaced with a real directory at `/Users/plessas/SourceCode/sw-utils/.venv` (Python 3.12.14) using
the recipe the repo already documents at the top of `requirements-dev.txt`:

    rm .venv && uv venv .venv && uv pip install --python .venv/bin/python -r requirements-dev.txt

**Full suite is 518 passed**, up from the 402 that were merely collectable. `.venv/bin/python -m
farmbot.run --doctor` reports PREFLIGHT OK and `scripts/daily_brief.py` runs, so `scripts/daily.sh`
and every `.venv/bin/...` line in this file work again. `.venv` is gitignored, so this is machine
state, not a commit.
- ⚠ **`requirements-dev.txt` is the complete contract.** The 2026-08-01 note that "comlink-python
  lives only in `.venv`" is WRONG: `scripts/swgoh_data.py` imports only `json`, `os`, `re` and
  `datetime` and talks to comlink over plain `urllib`. There is no comlink package to install.

## 2026-09-17/18 — RotE PHASE 4 played, and OPERATIONS are the whole game

Phase 4 opened ~21:30 local on 09-17. Guild GP 518,474,625, **16/56 stars at the start, 17/56 at
the end** — Tatooine starred, which **unlocks Kessel for phase 5**. Account went from guild rank
#4 to **#1** on the phase leaderboard.

### The live board, and which officer notes were actually actionable
| Planet | Zone | Start | Note | What was possible |
|---|---|---|---|---|
| Mustafar / Corellia / Coruscant / Bracca | P1-P2 | 3★ MAX | — | nothing worth doing |
| Geonosis | P2 | 246.0M/316M, 2★ | `3 star` | **combat only** (ops + deploy CLOSED) |
| Felucia | P2 | 268.6M/316M, 2★ | `All in!!` | **combat only** (ops + deploy CLOSED) |
| Tatooine | P3 | 117.5M/191M, 0★ | `3 star` | everything → **STARRED** |
| Dathomir | P3 | 1.2M/159M, 0★ | `preload 1st` | everything |
| Kashyyyk | P3 | 0.8M/191M, 0★ | `preload 2nd` | everything |

Phase-4 planets proper (Medical Station, Kessel, Lothal) stayed **LOCKED** all phase: their
predecessors held no star at the phase boundary. Mandalore bonus went 39% → **60%**.

### ⭐⭐ THREE MECHANICS THIS REPO HAD WRONG OR MISSING
- ⭐ **"Preload" is not "deploy here first". It means deliberately banking territory points
  BELOW a star threshold** so the zone does not unlock its downstream neighbour before the guild
  can feed it. Confirmed against swgoh.wiki / ROTE-planner write-ups. So `preload 1st/2nd` on
  Dathomir/Kashyyyk is a *hold*, not a push — which is why both sit at ~1M against a 159-191M bar.
- ⛔ **OPERATIONS AND DEPLOY CLOSE ON PLANETS OLDER THAN THE CURRENT ZONE. COMBAT DOES NOT.**
  Geonosis's operation screen refuses with a hard dialog — *"Invalid Action / Units cannot be
  assigned during this phase"* — and its DEPLOY button is greyed, while all four of its combat
  markers are live `BATTLE (1)`. Felucia the same. Tatooine/Dathomir/Kashyyyk (zone 3) were fully
  open in phase 4. ⇒ **The 2026-09-15 mystery of "Felucia's DEPLOY was greyed" is solved: it is
  the rule, not a bug.** ⇒ A `3 star` note on a zone-2 planet in phase 4 is **stale**: with deploy
  shut, 47-51M cannot be closed by combat rows worth 250-341K each.
- ⛔ **RotE SPECIAL MISSIONS ARE ONCE PER EVENT, NOT PER PHASE.** Both Tatooine specials showed a
  greyed **COMPLETE** button with `Successful Attempts 4 of 4` / `3 of 4` — they were spent in
  phase 3 and never came back. Only Dathomir's and Kashyyyk's were available, because those
  planets had only just opened. ⇒ Budget the Reva farm across the WHOLE event: Tatooine's
  `Complete Special Mission 25 Times: 4/25` advances once per player per event, not per phase.

### ⭐⭐ OPERATIONS PAY 40x A COMBAT ROW AND ARE THE ONLY THING THAT MOVED THE NEEDLE
First-party, off the operation screens: **zone-3 operations pay `+13,200,000 TP` each, zone-2
`+11,000,000`**, 6 per planet, 15 slots each, and each player may assign **10 units per
territory** (`Assigned Units: n/10`). A combat row pays at most 341,250. That is a **39x** ratio.
- ⭐ **Tatooine had two operations sitting at 14/15. Two units finished both: +26,400,000 TP**,
  which took Tatooine from 143.7M to 170.1M and put the 191M star in reach; 4.1M of ship deploy
  then crossed it. **That is the entire star, bought with two characters.**
  It also drove `Wretched Hive` 4/6 → **6/6 = Disabled**, killing the enemy ability that hinders
  Tatooine *and Kessel*.
- ⇒ **THE FIRST THING TO DO IN ANY PHASE IS OPEN EVERY OPERATION SCREEN AND LOOK FOR 13/15 AND
  14/15.** One unit into a 14/15 is worth 39 combat rows. Nothing else in the mode is close.
- ⛔ **AND IT IS WHY `Special → Operations → Combat → Deploy` IS NOT NEGOTIABLE.** I ran Dathomir's
  combat first, and when I came back to its operations **four slots refused with `UNIT ALREADY
  DEPLOYED`** — they wanted units I had just spent on combat rows. Dathomir Op6 stalled at 9/15
  instead of completing. Combat rows are mine alone and cannot be taken; operation slots are
  guild-contested AND unit-specific. Fill operations first, always.
- Slot refusals come in three flavours and all three need handling in any tap loop:
  `UNIT ALREADY DEPLOYED`, `DUPLICATE UNIT SELECTION` (two slots want the same unit and you own
  one), and `RELIC LEVEL REQUIREMENT` (owned but under the zone floor; CANCEL, not OK).

### Results, row by row
| Planet | Row | Squad | Result |
|---|---|---|---|
| Dathomir | special (Nightsister/Merrin) | Great Mothers (L) / Night Trooper / Morgan Elsbeth / Death Trooper (Peridea) / Merrin — 158,582 | **WON**, +260,828 |
| Dathomir | Dr Aphra | Doctor Aphra (L) / IG-90 / BT-1 / 0-0-0 / HK-47 — 148,835 | **2/2**, +341,250 |
| Dathomir | DS combat A | Dark Trooper Moff Gideon (L) / Scout Trooper / Captain Enoch / Death Trooper / Moff Gideon — 154,940 | ⛔ **0/2, +0** |
| Dathomir | DS combat B | SLKR (L) / Dark Rey / Kylo Ren Unmasked / General Hux / Sith Trooper — 196,042 | **2/2**, +341,250 |
| Dathomir | Empire | Lord Vader (L) / Darth Vader / Grand Moff Tarkin / Emperor Palpatine / Royal Guard — 189,119 | **2/2**, +341,250 |
| Tatooine | mixed (ungated) | **SEE (L) / Darth Revan / The Stranger / Darth Bane / Darth Malak — 219,399** | **2/2**, +341,250 |
| Tatooine | Jabba | Jabba (L) / Embo / Greedo / Gamorrean Guard / Cad Bane — 190,690 | **2/2**, +341,250 |
| Tatooine | Fennec | Bossk (L) / Fennec Shand / Zam Wesell / Boba Fett / Jango Fett — 167,380 | **2/2**, +341,250 |
| Tatooine | fleet | Executor auto-fill, 600,242 | **1/1**, **+682,500** |
| Kashyyyk | special (Saw) | Saw Gerrera (L) / Captain Drogan / Cassian Andor (Undercover) / Captain Rex / Jyn Erso — 172,002 | **WON** |
| Kashyyyk | Wookiees | Tarfful (L) / Clone Wars Chewbacca / Chewbacca / Threepio & Chewie / Zaalbar — 158,418 | **2/2**, +341,250 |
| Kashyyyk | LS A | GL Rey (L) + auto-fill (Rotta / General Skywalker / Satele Shan / Commander Ahsoka) — 220,865 | **2/2**, +341,250 |
| Kashyyyk | LS B | GL Leia + auto-fill mishmash — 216,797 | ⚠ **1/2, +162,500** |
| Kashyyyk | fleet | — | ⛔ **requires Profundity, NOT OWNED** |

### What the losses teach
- ⛔ **swgohrote's `P3 DS Combat` LEGEND IS UNPLAYABLE HERE AND IT SAYS SO IN ITS OWN NOTES.**
  "Dark Trooper Moff Gideon / Scout Trooper, **Captain Enoch (omi)**, Death Trooper, Moff Gideon".
  `CAPTAINENOCH` has **0 omicrons** on this account, and the squad went **0/2** — wave 1, against
  Dark Magick. This is the third time an omicron-gated guide comp has cost a row here
  (`JEDIKNIGHTCAL`/Zeffo, `MARROK`/Reva, now `CAPTAINENOCH`/Dathomir).
  ⇒ **Before fielding any swgohrote LEGEND, grep its note for `(omi)` and check `o` on that unit.**
  The working substitute for a generic Dathomir DS row is a **GL**: SLKR went 2/2 at the same
  relic floor.
- ⚠ **Power-sorted AUTO-FILL is a coin flip: 1 win, 1 partial.** GL Rey's auto-fill went 2/2;
  GL Leia's went 1/2. Every *coherent researched* squad went 2/2 except the omicron one.
  Auto-fill is acceptable only on an ungated row when nothing else needs the units.
- ⛔ **AUTO-FILL GRABS `JABBATHEHUTT` FOR UNGATED DARK/MIXED ROWS.** It did it twice. Jabba is the
  gate unit for the Tatooine Jabba row, so accepting it forfeits a whole 341,250 row. **Always
  CLEAR SQUAD on a gated planet before looking at what the game picked.**
- ⭐ **The Tatooine `mixed` row is SOLVED.** Phase 3's Empire core went 1/2 (+162,500); the
  **SEE Sith five went 2/2** (+341,250). Filter `SITH` and take the top five by power — it comes
  out exactly SEE / Darth Revan / The Stranger / Darth Bane / Darth Malak, 219,399.

### Device / UI notes
- **Filter-by-faction then "tap the top tile N times" is the fast way to build a researched squad.**
  Used units vanish from the filtered list, so the top-5-by-power under a faction filter often IS
  the researched squad: `IMPERIAL REMNANT` → the Gideon five exactly (154,940), `FIRST ORDER` →
  the SLKR five (196,042), `SITH` → the SEE five (219,399). Verify by squad power, which matches
  the computed `gp` sum to the unit.
- ⚠ **In-game `Pwr` is NOT the roster's `gp`** for every unit (mods count), and
  `data/roster/swgoh_roster_fresh_20260911.json` is a week stale — Cad Bane, Grand Inquisitor and
  several Empire units had all gone up a relic since. **Identify list tiles by portrait, then
  confirm by the squad-power total, never by a remembered `gp`.**
- `scripts/tapword.sh <Pwr number> --dy -55` taps a specific roster tile reliably; hardcoded grid
  positions drift as soon as one unit is added (the list re-flows).
- ⛔ **There are no `TB RotE` in-game preset tabs.** `SELECT SQUAD` shows only
  GAC 5v5/3v3 Def+Off and TW 1-4. Every RotE squad had to be hand-built, ~10 taps each.
  ⇒ **Push `output/rote_squads.json` with `scripts/push_ingame_presets.py` before the next phase**
  (do it while the game is closed — the write kicks the BlueStacks client).
- Deploy screen has a `SHIPS` / `CHARACTERS` / `DARK SIDE` / `LIGHT SIDE` filter plus SELECT ALL,
  which is the only sane way to split a deploy: ships-only was 4,097,099 (exactly enough to star
  Tatooine), Dark Side characters 2,679,836 → Dathomir, the rest 4,411,076 → Kashyyyk.
- ⚠ **`back` from the galaxy map exits the whole event**, and two of them walk out of the game to
  the BlueStacks launcher. One `back` per planet screen, verify with `ocr.sh panel` between.

## 2026-09-18/19 — RotE PHASE 5: the 14/15 hunt paid 39.6M, and the preset pusher was a no-op

Phase 5 opened ~20:08 local 09-18. Guild GP 518,601,610, **19/56 stars**, account guild rank
**#1**. Open planets: **Kessel** (zone 4, newly unlocked by Tatooine starring in phase 4),
**Dathomir** and **Kashyyyk** (zone 3, still fully open). Tatooine sat at 3★ MAXED with DEPLOY
greyed. Vandor, Malachor and Ring of Kafrene all **LOCKED** (their zone-4 predecessors hold no
star), so phase 5's own planets never opened.

### ⛔⛔ `push_ingame_presets.py` COULD NOT PUSH RotE, AND FAILED SILENTLY
The phase-4 note ended "Push `output/rote_squads.json` with `scripts/push_ingame_presets.py`
before the next phase". **That command was incapable of doing it.** `CATEGORY_TO_TAB` listed
only the six GAC/TW categories, so `build()` iterated those, found no `TB RotE - P<n>` rows,
returned `[]`, printed the live tab list and exited **having sent nothing and warned nothing**.
This is the "documented hook is not a wired hook" failure a second time: the instruction was
written, never executed, and the next session hand-built all 14 squads at ~10 taps each.
- Fixed: `ROTE_CAT_RE` discovers the RotE categories **from the payload** (a new phase needs no
  edit), and `rote_preset_name()` strips the `P<n> ` prefix plus the `MANUAL` / `[aspir]`
  planning markers, shortening the PLANET and keeping the ROW word whole when it must cut
  (`P1 Coruscant jedi_named` → `Corus jedi_named`). `tests/test_push_ingame_presets.py`, 8 tests.
- **Pushed and verified ON DEVICE**: `TB RotE - P1/P2/P3/P4/P6`, 32 squads, now appear in
  SELECT SQUAD under the TW tabs. `Dathomir aphra` loaded at exactly the recorded **148,835**.
- `rote_squads.py` was printing `upload_hotutils.py --sync --payload output/rote_squads.json`,
  the precise command CLAUDE.md says deletes ~114 GAC/TW squads. Now prints `--create` plus the
  preset push, with the reason inline.

### ⭐⭐ KASHYYYK: 3 UNITS → 3 COMPLETED OPERATIONS → +39,600,000 TP
Operations 1, 3 and 5 were each sitting at **14/15**. One unit each finished all three. The
territory ability went `Formations (Disabled)` → **`Formations (Hindered)`, 4/6**. Final board:
Op1 15/15, Op2 13/15, Op3 15/15, Op4 15/15, Op5 15/15, Op6 12/15, using 6 of the 10 allowance.
**This is the single highest-value action available in the mode and it took four taps.** Open
every operation screen on every open planet before doing anything else.

### ⚠ BUT THE 14/15 RULE IS BOUNDED BY PER-SLOT UNIT REQUIREMENTS
CLAUDE.md's "one unit into a 14/15 is worth 39 combat rows" is true and it is not free.
**Each of the 15 slots demands one SPECIFIC unit.** On Dathomir, ~11 slots were open across
four operations and only **3** were fillable. The tells, all seen the same night:
- **No `UNDEPLOYED` label under a tile = you do not own that unit.** This is the fastest read
  on the screen and it is the one that decides whether a 14/15 is actually free TP.
- `RELIC LEVEL REQUIREMENT` = owned, under the zone floor. **CANCEL, never UNIT DETAILS.**
- `DUPLICATE UNIT SELECTION` = two slots want a unit you own once, or it is already committed
  (several Kessel ship slots refused because those ships are on the GAC defence fleets).
⇒ Budget "I have 10 units for this territory" as an upper bound, never a plan.

### Operations, all three planets
| Planet | Zone | Gate | Per op | Before | After | Used |
|---|---|---|---|---|---|---|
| Kessel | 4 | **R8** + ships 7★ | **+18,480,000** | all 0/15 | Op1 **8/15**, Op2 2/15 | 10/10 |
| Dathomir | 3 | R7 | +13,200,000 | 2/6 done | Op4 12/15, Op5 **14/15** | 3/10 |
| Kashyyyk | 3 | R7 | +13,200,000 | 1/6 done | **4/6 done** | 6/10 |
Kessel's six were untouched by the whole guild, so seeding Op1 to 8/15 makes it the natural
completion target. Kashyyyk's operation reinforces **four** territories at once (Kashyyyk,
Lothal, Ring of Kafrene, Scarif); Dathomir's reinforces the **Death Star**.

### Dathomir combat: 3 wins, 1 loss, and the loss still paid
137,449,467 → **152,429,269 / 158,960,938** after combat plus a full deploy. 6.53M short of its
first star with 19h left, which the guild closes.
| Row | Squad | Result |
|---|---|---|
| Doctor Aphra (gated) | preset `Dathomir aphra` 148,835 | **2/2, +341,250** |
| DS/Neutral ungated | preset `Dathomir ds_1`, the SLKR five, 196,183 | **2/2, +341,250** |
| DS/Neutral ungated | `ds_2` minus restricted, **plus Darth Revan**, 185,282 | **2/2, +341,250** |
| DS/Neutral ungated | game AUTO-FILL: Vader/Grand Inquisitor/Tarkin/Piett/**Dark Trooper Moff Gideon**, 172,038 | ⛔ **0/2, +0** |
- ⛔ **The auto-fill Jabba trap fired again**, exactly as phase 4 recorded: the first ungated DS
  row pre-filled **Jabba the Hutt**, who gates Kessel's `jabba` row. CLEAR SQUAD every time.
- ⛔ **A Gideon-led Empire comp lost on Dathomir for the SECOND event running.** Phase 4's
  `Dark Trooper Moff Gideon / Scout Trooper / Captain Enoch / Death Trooper / Moff Gideon` went
  0/2; this phase the auto-fill's `Vader / Grand Inquisitor / Tarkin / Piett / Dark Trooper Moff
  Gideon` also went 0/2, at a HIGHER 172,038 power than two squads that won. **Stop bringing
  Dark Trooper Moff Gideon to Dathomir.** The Nightsister waves beat it twice.
- ⭐ **Confirmed first-party: a LOSS still credits the squad's GP as deployment.** The 0/2 row
  logged `Astra: Deployed 172,038 points` and the planet total rose. `rote_run_mission.sh`'s
  header claim is correct, so an unwinnable row is still worth entering rather than deploying
  those units plainly.
- ⚠ **`RESTRICTED CHARACTERS` on a preset means its units are already spent this phase.**
  Baylan/Shin/Starkiller had gone into Kessel's operations an hour earlier. CONTINUE loads the
  survivors and you top up from the left roster panel: **a dark tile there is unavailable, a
  red-ringed one is free**. Darth Revan made the patched squad *stronger* (185,282) than the
  preset it replaced (182,226).

### Deploy: send it all to the ONE planet whose star is reachable
13,093,604 unallocated. Kashyyyk needed 131M and Kessel 235M, both impossible this phase;
Dathomir needed 19.6M. All of it went to Dathomir.
- ⚠ **`Unit Required in another Territory` names the units you are about to strand** (Jabba and
  three others here). The right test is not "is this unit gated somewhere" but **"can the
  territory it is gated on actually star?"** Kessel cannot (0/235M), Dathomir could, so
  deploying Jabba was correct despite forfeiting Kessel's 341,250 `jabba` row.
- Assigning a unit to an OPERATION also credits its GP as deploy points immediately (two feed
  entries, 33,705 and 126,405, appeared the moment the ASSIGN landed).

### Kessel special is 1,000 Mk III tokens and is UNPLAYABLE HERE
Gate is **5 characters at R8+ including Qi'ra and L3-37**. Both sit at **R7**, and the free-slot
Marrok is R7 too; the game itself prints `REQUIRED UNITS 3/5`. `missions_4.json` already flags
the row `aspirational` and it is still correct. Two R7→R8 upgrades unlock it. That is relic
spend to unlock relic currency, so it is an **owner decision**, not an autonomous one.

### Map-reading notes
- **Resolve a planet by tapping it and reading the HEADER, never by position.** Three planets on
  the phase-5 map show three dark stars and look identical at a glance; the big glowing one next
  to Tatooine was Kessel, not Tatooine, and the planet directly "above" Tatooine was Vandor
  (locked), not Kessel. Two wrong guesses cost two screenshots each.
- Dark stars under a planet = thresholds not yet earned, not a star count.
- The gold diamond marker is the **special mission**; the dark-blue crate marker is
  **operations**. On Kessel they sit close together and the gold one is the more tempting tap.

## 2026-09-19 (01:00-02:10) — dailies 8/8, arena #1, and two pointers this repo had wrong

Daily Quests **8/8 + crate**, Guild Activities **600/600**. `farmbot.run --daily` did the PvE
grind (5 energy nodes, 2 challenge sims, 6 collects, 1 bonus-energy, 1 PvE win, 1 token shop
buy, 4 unknown-screen halts); everything below is what the bot structurally cannot do.

### ⭐ ARENA: THE DATACRON BEATS 32K OF POWER, CONFIRMED A THIRD TIME
**Squad Arena #4 to #1** by attacking the rank-1 board directly: the **165,222** Hutt Cartel
five (Rotta the Hutt lead / Gamorrean Guard / Greedo / Krrsantan / Mob Enforcer, carrying the
set-33 **level-15** Hutt cron) beat a **197,155** GL Leia team. That is a 32K power deficit
overturned. Mechanism is the one already recorded: **omicrons do not fire in Squad Arena and
datacrons do**, and Rotta's `A Legacy Reforged` lead is a BASE ability, so his squad keeps its
whole kit while a GL squad loses most of its own.
⇒ The game pre-fills this squad now, so the correct play is simply to accept it and attack the
top of the board. **Defence is the squad you last attacked with**, so finishing on this one
parks the right wall.
**Fleet Arena #14 to #9 to #5** on the Leviathan build (B-28 / TIE Dagger / Fury starters).
⚠ Fleet has a **6m49s cooldown between attacks and skipping it costs 50 crystals**. Never pay
it; do something else and come back.

### ⛔ THE GUILD STORE DOES NOT SELL MOD SLICING SALVAGE
CLAUDE.md lists the farm for T06_02 / T05_06 as "Mod Battles Sector 9 · **Guild Store** ·
Episode Shipments". The Guild Shipments tab was read end to end tonight and it sells **gear
salvage only** (Mk 2 Pulse Modulator, Mk 9 BioTech, Mk 6 Arakyd, Mk 4 Sienar, Mk 3 Carbanti,
Mk 10 BlasTech and so on), priced in guild tokens. **There is no mod slicing salvage in it.**
Correct the pointer to Mod Battles and Episode Shipments.
⚠ Also: the **Featured** Shipments tab is entirely crystal-priced (320-400 each). For the
"Purchase 3 store Shipments" daily, go to a TOKEN tab (Guild, Cantina) and never Featured.

### Coliseum: the attempts were left UNUSED on purpose, and that is the right call
Krayt Dragon T7, high score **344,942 (98%)**, rank 260, **4 attempts unspent**.
This repo's own 2026-09-15 measurement is the reason: AUTO landed **81-98% across four runs**,
the high score is already 98% and is **best-of**, so no AUTO run can improve it, and the reward
ladder pays nothing between 90% and 100%. The last two points need a MANUAL run that holds fire
for the no-bonus-Protection windows. **Spending attempts on AUTO here is pure waste** — bank
them for a session with the image budget to play it by hand.
- The game pre-fills **Darth Maul (lead) + Starkiller (Luke Concept)**, and BOTH are the wrong
  picks already documented above: the comp is **JKLS (L) / Darth Talon / Mara Jade Skywalker /
  Yoda (DSV) / Stormtrooper (Concept)**.
- `RANK REWARDS` is an INFO panel, not a claim button; Coliseum payouts arrive in the inbox
  daily. Rank 260 sits in the `#251-500` band for 150 tokens; **breaking into `#91-250` doubles
  it to 300**, which is the real argument for chasing a higher score.

### Energy: spend the overflow, it is being wasted where it sits
Regular energy was at **229/144** after the resupply claims, ie 85 over cap and regenerating
into nothing. One `MULTI SIM` of **22 battles on Dark Side 8-E burned 220 of it** and closed
both the 600-energy quest and the 600 guild tickets in a single action. Sim tickets are at
39.2K, so they are not a constraint. Mod energy, by contrast, was drained to 5/144 by the
farmbot, so Mod Battles was not available as the dump.

## 2026-09-19/20 — RotE PHASE 6: the operations fill EATS your Galactic Legends

Phase 6/6 opened ~20:08 local 09-19 with 20h53m on the clock. Guild GP 518,871,451, **23/56
stars** at the start and **24/56** by the end (Kashyyyk took its 2nd). Astra went **#3 to #1**
on the phase contributor board.

### The board: only TWO territories were contributable, and the rest of the map is scenery
| Territory | Zone | State on arrival | Verdict |
|---|---|---|---|
| **Kessel** | 4 | 130,703,907 / 235,143,105, **0★** | the only reachable 1st star, everything went here |
| **Kashyyyk** | 3 | 298,486,599 / 305,525,000, 1★ | starred during the session, 3rd star at 407M is out of reach |
| Medical Station | 4 | 0★, **red no-entry overlay** | guild-flagged, obeyed, never entered |
| 2 padlocked bonus zones | | locked | Zeffo/Mandalore gates never met |
| Death Star · Hoth · Scarif | 6 | never unlocked | their zone-5 predecessors never held a star |
Vandor, Malachor and Ring of Kafrene never opened either, so **phases 5 and 6 were played
entirely on phase-3 and phase-4 planets**. `data/rote/missions_5.json` and `missions_6.json`
were dead weight for this whole event.

### ⭐⭐ THE OPERATIONS FILL SPENDS YOUR BEST UNITS, AND IT BREAKS THE RESEARCHED COMBAT COMPS
`rote_fill_ops.py` placed 7 units into Kessel's operations, chosen by the GAME (each slot offers
its highest-power eligible owned unit). It took **Sith Eternal Emperor, Emperor Palpatine,
GL Rey and Ben Solo** among them. An hour later:
- the researched Kessel `mixed_1` comp (the **SEE Sith five**, 219,399, proven 2/2 on Tatooine)
  was unfieldable, and
- the researched Kashyyyk `ls_1` comp (the **GL Rey five**) was unfieldable.
Both rows had to be rebuilt from what was left, and `ls_1` then went **1/2**.
⇒ Operations are still correct to run first: a unit in an op is worth 1/15 of 18,480,000, about
**1.232M**, against roughly 99K for a fifth of a 493,594 combat row. That is 12x and it is not
close. **But the fill must not be blind.** Either field the phase's gated and researched combat
rows first when their units are R8+, or teach `rote_fill_ops.py` to skip any base id named in a
`TACTICS` squad for the open phases. The phase-4 note's reason for ops-first (combat locks units
out of operations with `UNIT ALREADY DEPLOYED`) is real; this is the equal and opposite cost, and
neither note knew about the other.

### ⛔ `rote_fill_ops.py` COULD NOT DISMISS THE RELIC DIALOG, AND THAT FAILS SILENTLY
`RELIC LEVEL REQUIREMENT` is a **two-button** dialog (CANCEL, and a green UNIT DETAILS). The
script only knew the one-button "cannot be used here" layout, and its `OK_DLG` point lands in the
dead space between the two buttons: the dialog stays up, every later cell tap is swallowed by it,
and the run reports `placed 0` with no error. Fixed with a `dismiss()` that checks the relic
layout FIRST (its green button also satisfies the one-button test, so order of checks decides)
and taps CANCEL, never UNIT DETAILS, which navigates out of the event.
`tests/test_rote_fill_ops.py`, 5 tests.

### ⭐ THE RED BADGE ON AN OPERATION BUTTON IS "SLOTS YOU CAN FILL", AND IT IS TRUSTWORTHY
Kessel's six operations read 13/15 (**no badge**), 6/15 (3+), 8/15 (2), 4/15 (3+), 9/15 (2),
8/15 (3). The fill script placed exactly 0 · 1 · 0 · 1 · 2 · 3, and stopped at **7/10 assigned**
with every badge gone. So a missing badge really does mean "nothing here for you", and the
13/15 that looked like the jackpot was unreachable. Board went 48/90 to 55/90.
⚠ **Kessel's gate is R8, not the R9 this repo attributes to phases 5 and 6.** The gate belongs to
the ZONE, not the phase: Kessel is zone 4 (`Relic 8 or Higher`), Kashyyyk zone 3 (`Relic 7`).

### Kashyyyk operations were 5/6 done and the last slot is TWO relic levels away
Operation 6 sat at **14/15**, worth 13,200,000 for one unit, and the empty slot wanted a **Hoth
Rebel at R7**. Astra holds **Hoth Rebel Scout R5** and **Hoth Rebel Soldier R5**, so it is two
relic levels, not one, and `RELIC LEVEL REQUIREMENT` is what the slot answers with.

### Combat, all on AUTO. Six rows, 2,051,563 TP
| Row | Squad | Power | Result |
|---|---|---|---|
| Kessel `jabba` | Jabba (L) / Krrsantan / Bossk / Embo / Jango Fett | 191,890 | **2/2, +493,594** |
| Kessel `mixed_1` | Darth Bane (L) / Darth Revan / The Stranger / Darth Malak / Maul (Hate-Fueled) | 204,700 | **2/2, +493,594** |
| Kessel `mixed_2` | JMK (L) / General Skywalker / Rex / Fives / Echo | 196,209 | ⛔ **1/2, +219,375** |
| Kessel `fleet` | Home One preset | 602,331 | ⛔ **LOST**, attempt burned |
| Kashyyyk `wookiee` | Tarfful (L) / Clone Wars Chewbacca / Threepio & Chewie / Zaalbar / Chewbacca | 158,418 | **2/2, +341,250** |
| Kashyyyk `ls_1` | JML (L) / Grand Master Yoda / Cal Kestis / General Kenobi / Rey (Jedi Training) | 197,935 | ⛔ **1/2, +162,500** |
| Kashyyyk `ls_2` | GL Ahsoka (L) / Huyang / Fulcrum / Ezra (Exile) / Padawan Sabine | 186,295 | **2/2, +341,250** |
- ⛔ **POWER IS NOT THE DISCRIMINATOR, AGAIN.** The two highest-power ground squads of the night
  (JMK 196,209 and JML 197,935) are the two that dropped a wave, while 158,418 of Wookiees went
  2/2. JMK plus General Skywalker is a protection and counter engine built for GAC and it runs
  the clock out on a timed PvE wave. **Bring damage to an ungated row.**
- ⭐ **`TARFFUL MUST LEAD` is confirmed, and the trap is invisible.** The game restored the phase-3
  Wookiee squad at the identical 158,418 but with **Clone Wars Chewbacca in slot 1** and his
  `Wookiee Resolve` showing as the leader ability. Tarfful's is `It's All in the Fur`. Same five
  units, same power, wrong leader. **Slot 1 is the leader; read the leader-ability name, not the
  power.**
- ⛔ **The Kessel fleet row is NOT solved by the coherent-lineup rule.** `missions_4.json` names
  Home One because Ghost sits in that lineup, and Home One at 602,331 still lost, burning the
  attempt (1/50 to 2/50) and the 987,188 TP. Only the fleet's GP landed, as deployment. Ghost is
  the gate, not the carry.
- ⛔ **`rote_autobattle.py` misreported that loss as `outcome=win`, then attached the PREVIOUS
  row's feed line to it** (it echoed `1/2 waves, 219,375` a second time). The fleet fight ended in
  50s and the feed had not refreshed. **A fleet row is 1 wave; any "n/2" on a fleet is a stale
  read.** Confirm from the planet feed plus the attempt counter, never from the driver's label.

### Three UI facts worth keeping
- ⛔ **`Large Unit Limit`: Jabba the Hutt and Rotta the Hutt cannot share a squad.** Both are large
  units and only one fits. Nothing in the mission requirements hints at it, and the dialog then
  swallows the next several taps, so a scripted fill silently places nothing after it.
- ⭐ **The in-squad TEXT SEARCH matches ABILITY TEXT, not just names.** Searching `Emperor`
  returned **Darth Bane and Admiral Piett** and did NOT return Sith Eternal Emperor. Use a
  distinctive name fragment, and treat "no result" as "unavailable" only after a second term.
  `None of the units in this filter can be used in this mission` is the real "already spent" tell.
- ⭐ **A SPECIAL MISSION IS ONCE PER EVENT, NOT ONCE PER PHASE.** Kashyyyk's Saw Gerrera special
  read `COMPLETE`, greyed, with `Successful Attempts: 1 of 2`, because phase 3 had already run it
  on 2026-09-17. Do not budget a special into a later phase's plan once it has been cleared.

### Deploy went last, and all of it to the one territory that can star
12,684,762 unallocated, every point to **Kessel**, which closed at **146,759,366 / 235,143,105**.
Kashyyyk was already past its 2nd star and its 3rd needs 108M more, so nothing was held back for
it. Kessel needs 88.4M from the guild with 19h42m left, and 5 completed operations would be 92.4M.

## 2026-09-19/20 (00:15-04:00) — dailies 8/8, and the mod PLACEMENT that had never run

Daily Quests **8/8 + crate**, Guild Activities **600/600**, 5 login calendars claimed
(including Signal Booster day 3 = 10 Fragmented Signal Data). `farmbot.run --daily` did the PvE
grind in ~30 min (5 energy nodes, 2 challenge sims, 6 collects, 1 PvE win, 1 shop buy, 4 halts).
**Fleet Arena #13 to #8**; Squad Arena left alone at #1, which also leaves the Hutt Cartel wall
parked, since defence is the squad you last attacked with.

### ⭐⭐ THE GRANDIVORY SELECTED-CHARACTER LIST WAS EMPTY, SO PLACEMENT HAD NEVER BEEN OPTIMISED
`profiles.selectedCharacters` in the optimizer's IndexedDB was `[]`. Not stale, EMPTY. That is
the direct cause of the gaps `mod_analysis.py` keeps reporting: Satele Shan and Bo-Katan on
**5** total mod speed, Kleya on 0, Maul (Hate-Fueled) on **0**, The Stranger on 29 while he is
the #2 hardest defence in the game. Nothing was ever allocating mods by priority.
- ⛔ **CLAUDE.md's "re-run rarely, ~1,473 moves / ~7.4M credits for a measured <=0.12%" DOES NOT
  APPLY TO THIS CASE.** That measurement was a re-run against an already-optimised list. Against
  an empty one the same action is worth a great deal, and conflating the two is what let the
  roster sit mis-allocated. **Check `selectedCharacters` before quoting that number.**
- **`Auto-generate List` is the way in, and its default is WRONG for this account.** The modal
  ships `ignore-arena` CHECKED, and it says so: *"unless you specify otherwise, your current
  arena team will not be placed at the top of the list."* The owner's mod ladder is
  **Arena first**. Uncheck it and the generated list opens with Rotta / Krrsantan / Greedo /
  Gamorrean Guard / Mob Enforcer, which is exactly tier 1. Settings used: use case
  **GAC / TW / ROTE**, all alignments, **minimum gear 13**, overwrite, omicron boosts all OFF
  (they change the stat model and only one mode's omicrons ever fire at a time).
- ⚠ **28 of the 321 generated entries had an ALL-ZERO target** (`"name":"unnamed"`), so the
  optimizer had nothing to aim at for them, and they included **Rotta the Hutt (the arena
  defence leader), The Stranger, Maul (Hate-Fueled), Satele Shan and Cassian (Undercover)**.
  These are the characters too new for a swgoh.spineless.net preset. Filled them with the median
  of the tool's own 231 `PvP` targets (speed 100, potency 10, physDmg 10, health 5) by writing
  `selectedCharacters` back into IndexedDB and reloading, which the app rehydrates cleanly.

### Result: 1,729 moves, 8,835,000 credits, and the deployed arena five up 33%
| Unit | before | after | delta |
|---|---|---|---|
| **Rotta the Hutt** (arena lead) | 73 | **126** | **+53** |
| **Krrsantan** | 37 | **108** | **+71** |
| Greedo | 108 | 116 | +8 |
| Gamorrean Guard | 109 | 85 | -24 |
| **Mob Enforcer** | 98 | **130** | **+32** |
| **DEPLOYED ARENA FIVE** | **425** | **565** | **+140 (+33%)** |
| **Maul (Hate-Fueled)** | **0** | **93** | **+93** |
| **The Stranger** | 29 | **105** | **+76** |
| Darth Revan | 75 | 111 | +36 |
Roster-wide `plusSpeed` **16,874 to 16,966**, 6-dot 182 to **185**, 6A 114 to **116**,
modScore 2.85 to **2.88**. Paid for by stripping the hoarders the generator ranks low:
Luminara Unduli 125 to 15, Visas Marr 141 to 46, Barriss Offee 69 to 25, Cad Bane 97 to 37.
- ⚠ **Do not judge this by the top of `output/mod_priority.txt`.** Its top 25 sums to **-105**,
  which reads like a regression, and it is an artefact: that list still carries **Cad Bane** in
  the arena five and ranks Luminara #20 and Visas Marr #23. Score the squad that is actually
  deployed instead.
- ⛔ **`output/arena_result.json` IS STALE AND IT POISONS TIER 1.** Its `deployed` array is
  `[RACCOON, HUMANTHUG, GREEDO, GAMORREANGUARD, CADBANE]` off a **shard snapshot dated
  2026-08-08**, but the live wall has run **Krrsantan** in place of Cad Bane since 2026-09-19.
  So `invest_plan.py` spends tier-1 priority on a unit that is not on the board. Grandivory read
  the LIVE squad and got it right, which is the only reason Krrsantan gained 71.

### ⛔ "HotUtils is taking a long time to respond" IS NOT A FAILURE, AND RETRYING IS THE TRAP
The move timed out client-side after ~45s. A mid-flight re-measure looked like a disaster
(plusSpeed 16,874 to **15,815**, 6-dot 185 to 178, only 5.17M of the 8.835M spent), because a
1,729-move plan half-applied is worse than either endpoint. **The move was still running.**
Pressing `Move mods in-game` again answered **`Player is already in a game action!`**, and five
minutes later the full 8,835,000 had been drawn and every number was above where it started.
⇒ On a timeout, **wait and re-measure; never re-fire.** The partial state is transient, not a
result. Budget several minutes for a full-roster move before believing any score.

### Store and material notes
- ⛔ **`execute_upgrades.FARM` was sending you to two places that do not exist.** It named the
  **Guild Store** for every 5-dot and 6-dot material (it sells GEAR salvage only, read end to end
  2026-09-19) and **"Sector 9"** (the 2026-04-27 update cut Mod Battles to two tiers; the old
  Map 9 is **chapter 2**, which is what `farmbot/config.json` actually sims). Both corrected.
- ⭐ **Episode Shipments DOES sell Signal Data**, which contradicts CLAUDE.md's "SIGNAL DATA is
  cantina-energy-only, no store sells it for a token". Live prices: **45 Fragmented for 4,500 EC**
  and **40 Incomplete for 5,400 EC**. Episode Currency was sitting at **80.4K of a 100K cap**, so
  it was actively being wasted; bought both, which also closed the 3-shipment daily.
- Mod energy is **not** a farming lever here: the farmbot max-sims mod chapter 2-F every run and
  leaves the pool at 4/144. The 600-energy quest was closed with **18x Dark Side 8-H (180 energy)**.
- Calibration is still blocked: all 5 planned rerolls died on the first with
  `rc=2 GOHServiceCall Error [40]` and attenuators never moved off 16, so it is not attenuators.
  Unresolved.

### Coliseum: new boss, and AUTO is still the wrong tool
Krayt Dragon rotated out for **ZEFFO TOMB GUARDIANS**, tier 9, high score **196,314 (43%)** with
the 40% crate claimed and the 50 / 60 / 70 / 100% tiers open. One attempt on the game's pre-filled
Darth Maul squad scored **87,363 (19%)**, less than half the standing score. Banked the other
three: the same conclusion the Krayt Dragon reached, now re-measured on a fresh boss. The tiers
need a researched comp and a manual run, not another auto roll.
Yesterday's rank #281 paid **150 Mk III tokens**; rank is now 144, inside the #91-250 band that
pays 300.

## 2026-09-20/21 — S83 META RE-PULLED, and THE FLEET DEFENCE LOCKS ITS CREW

Owner lifted all three standing rails for this session: **GAC offense, crystals and
gear/relic/ability spending are all allowed now**; only real money is out. Standing
instruction was "grounded in the current meta, optimal play only".

### ⭐⭐ THE TIER LISTS WERE A SEASON STALE, AND THE #1 WALL CHANGED
Re-pulled the live **Season 83** Kyber 3v3 lists (1.31M battles) into
`tierlist_3v3_{def,off}_kyber_s83_20260921.json` and repointed `gac3v3_board.py`.
- ⭐ **Rotta the Hutt / Gamorrean Guard / Mob Enforcer is now the best wall in the
  format: 48.0% raw hold on n=8,676**, shrunk 38.6%. This file used to carry
  "Rotta / Cad Bane / Gamorrean Guard 12.6% on n=665" — that is the OLD BUILD, and the
  swap of Cad Bane for Mob Enforcer is the whole difference. Astra also holds the
  level-15 Hutt cron that the published sample mostly does not, so 48% is a floor.
- Rey's defensive third is now **Cal Kestis**, not Luminara Unduli.
- The Stranger / Maul (Hate-Fueled) / Starkiller tops BOTH lists (34.0% hold n=28.1K,
  91.6% win n=26.5K).
- Transport, and it split by tool: **chrome-devtools MCP loaded `?side=defense` clean,
  `?side=offense` drew a Cloudflare interstitial that never cleared even after a warm
  base-page navigation and a reload.** **Playwright MCP then loaded the base
  `/tier-list/3v3/` first try, and that URL defaults to the OFFENSE view.** So the
  reliable recipe is now: chrome-devtools for defence, Playwright for offence.

### The board, and a pin search worth +120 banners
`--structure free` alone lands at net **+238**. Hill-climbing `--pin-def`:
+Rotta **+311**, +Lord Vader **+331**, +Ahsoka **+342**, +Leia **+358** (plateau; adding
Rey, The Stranger or Kelleran changes nothing). So the greedy `free` search is leaving
~120 banners on the table and **the pin set is worth searching every season**.
`--doctrine` on the fresh data still says **K=5 GLs wall at every conversion rate**, and
names the same five as before: Rey, Lord Vader, Ahsoka Tano, SLKR, Leia Organa.
⚠ `--gl-wall` is a **no-op when combined with `--pin-def`** (K=3..6 all returned +311).

### ⛔⛔ A PLACED DEFENSIVE FLEET LOCKS ITS CREW CHARACTERS, AND THE BOARD MODEL DOES NOT KNOW IT
Placing the computed board in-game, `A4 GL Leia / Captain Drogan / R2-D2` raised
**RESTRICTED CHARACTERS — "One or more of the characters in this squad can not be used
in this Battle"**, and so did `K3 Snowtrooper Commander / Snowtrooper / TIE Fighter
Pilot`. Both squads contain a **ship crew member** (R2-D2, TIE Fighter Pilot) already
committed to a walling fleet. `gac3v3_board.py` treats ships and characters as separate
pools and cannot see this, so **any board it produces may contain 1-2 unplaceable
squads**. Push CONTINUE and the squad still goes down full if the crew unit is free at
that moment; otherwise pick a substitute. Both eventually placed here, so the lock is
evaluated live and is not a hard pre-filter. ⇒ **Place the crew-heavy squads LAST**, and
if a zone will not fill, that is the reason, not a bad preset.

### GAC S83 round 2 was lost before the session started, and the fleet split is why
Score **1,584 vs 2,045**. It was already mathematically decided: 463 behind with only the
3-fleet territory left, whose ceiling is 219 + 3x79 = **456**. The cause is structural:
**Leviathan, Executor and Negotiator were all on DEFENCE**, so the only attackers left
were Raddus (71.9%) and Endurance (51.9%), and both lost to 506-546K Kyber fleets for
1 banner each. `gac3v3_board.py --fleets` says the opposite and should be obeyed:
**wall Home One / Negotiator / Raddus, attack with Leviathan / Executor / Chimaera**
(expected denial 24 against expected offense 360). Hand-priced the same way this repo
priced rule 7: walling the best three is worth ~401 all-in, attacking with them ~458.
⚠ Not fixed on the live board this session: rebuilding a defensive fleet is a full
manual 8-ship job per fleet and the character zones were the bigger win.

### Round 3 defence PLACED (5/5 · 5/5 · 5/5 · 3/3)
`output/gac3v3_board_r3_s83.json`, pushed to the in-game preset tabs first with
`push_ingame_presets.py --payload output/gac3v3_upload_r3_s83.json --names-as-is --push`
so the whole board could be set from SELECT SQUAD. Crons re-attached to the two that
depend on one: the **level-15 Hutt cron** on Rotta (+155% Defense, +140% Potency, +100%
Health, +100% Crit Damage, no downgrade arrow) and the lightside/Jedi-Vanguard L9 on
Kelleran Beq.
- ⚠ **The cron picker's DEFAULT selection is usually wrong.** Twice the pre-selected
  entry was an off-scope Dark Side/Empire cron whose own panel said *"Does not apply to
  any characters in the current squad"*. Read the bonus panel before pressing EQUIP;
  the right one shows character portraits under the Level 3 bonus.
- ⚠ In the SELECT SQUAD picker you must tap the **squad NAME/header row**. Tapping a
  portrait opens that character's sheet and costs two screens to back out of.

### Coliseum: the boss is JOTAZ, and the green pip is a real optimiser
Zeffo Tomb Guardians rotated out. Jotaz ends after **it** takes 20 turns, takes less
damage the longer it lives, revives once at full health, and hits buffless targets for
+250%, so it is a front-loaded burst race. **81% -> 95% (264,585 -> 311,590), rank 202 ->
172, the 90% crate claimed.**
- ⛔ The community top comps are **unfieldable here**: Jedi Knight Cal Kestis is not in
  this era's loan pool. And the squad-screen **search box matches ABILITY text, not
  names** — "Mace" returned "none of the units in this filter can be used", while Mace
  Windu was sitting in the pool and was found by eye.
- ⭐ **The N/M green pip on each portrait is a synergy oracle and it predicted the
  score.** One variable changed, same auto, same boss:
  JKL(L) / Mace Windu(L) / Mara Jade Skywalker / Barriss Offee(L) / **Starkiller (Luke
  Concept)** = 7/8 pips = **300,995 (92%)**; swap Starkiller for **Kit Fisto**, a Jedi so
  JKL's lead crit bonus doubles, = 8/8 = **311,590 (95%)**.
  Dropping the healer Barriss for a third attacker = **283,135 (87%)**, so she earns it.
- JKL's lead is +10% crit chance AND crit damage to Light Side, **doubled for Jedi**,
  which is why Dark-Side Yoda (DSV) reads 0/2 under it and 1/1 under Darth Maul's.
- ⭐ **The banked high score is a MAX, not a last value.** A final attempt can only
  help, so when you need to cross a threshold, maximise VARIANCE, not the mean.

### The rest of the run
Dailies **8/8 + crate**, Guild Activities **600/600**, all 5 login calendars, farmbot
19 entries (5 energy nodes, 2 challenges, 8 collects, 1 PvE win, 4 halts).
**Territory War (Jakku) JOINED** — guild was 15/50 against a 25 minimum.
**Fleet Arena #11 -> #7 -> #3** on auto with the Leviathan arena build, picking the
LOWEST-power opponent each time (at #7 the rank-3 holder was also the weakest at 360K).
Did NOT buy the 50-crystal cooldown skips: payout was ~16h out, so the rank would decay
before it paid.
Mods session: 6-dot 185 -> 186, plusSpeed 16,966 -> 16,967, 872,000 credits, 15
attenuators. **Calibration is still dead on `rc=2 GOHServiceCall Error [40]`.** The
slicing gate is **T05_06, short 866**.
Episode Shipments, bought with Episode Currency and not crystals (71K -> 60.3K of a 100K
cap): **Ability Material Omicron x2** (owned 5 -> 7) and Ability Material Mk III.
Signal Data was already bought out this cycle.

### 2026-09-21 (03:00) — the board AUDITED, and three of my own claims corrected

Owner pushed back on the GAC strategy, so I attacked it rather than defended it.
Named teammates could not spawn (the Agent tool could not resolve a tmux pane even
though `tmux list-panes` works from Bash, and `pretool-agent-guard.sh` blocks the
unnamed fallback), so this was done single-handed.

**VERIFIED CORRECT (do not re-litigate):**
- **The gate structure IS modelled properly.** `board_denial` at
  `scripts/gac3v3_board.py:195` computes `conceded = sa + sb + fall_a*sf + fall_b*sk`,
  so each BACK zone's value is multiplied by the probability its own FRONT falls.
  `TOTAL_AVAILABLE` 2082 = 3x(5x57+260) + (3x76+219), matching the first-party panels.
- **`net` = denial + offense - 2082**, i.e. an expected MARGIN. Legitimate objective.
- **The zone assignment is NOT sensitive to the fleet zone's hold q.** Run with the
  model's fleets (q=31%) and with the best defensive fleets forced (q=44%): both give
  FRONT-A 76-77%, FRONT-B 78%, BACK-B 54%. The optimiser BALANCES the fronts either
  way, which is the concave-optimal thing to do. ⇒ CLAUDE.md's "below q~20% front-A
  leads, above it front-B" is not operative here; it describes a stacked split the
  optimiser never chooses.
- **The placed board equals the planned board.** Confirmed first-party via HotUtils
  `gac/get {refresh:true}` — all 15 squads present and all 3 units each, including
  `GLLEIA/CAPTAINDROGAN/R2D2_LEGENDARY` and
  `REMNANTSNOWCOMMANDER/SNOWTROOPER/TIEFIGHTERPILOT`, the two that raised RESTRICTED
  CHARACTERS during placement. ⛔ **`gac/get` WITHOUT `refresh:true` served a
  day-old snapshot** showing the superseded Cad Bane and Luminara builds, which reads
  exactly like "your placement did not save". Always pass `refresh:true` to verify.
- The Rotta datacron override moves the ESTIMATE (net +358 at 38.6% hold, +373 at 44%,
  +385 at 48%) but never the SELECTION. So it is worth stating, not worth acting on.

**⛔ THREE DEFECTS IN THE MODEL, FOUND BY AUDIT:**
1. **`allocate_fleets` never receives `realization`.** `main()` calls it as
   `allocate_fleets(fdef, foff, args.p_front_a_falls)` (~line 647), so the fleet split
   is always decided at r=1.0 no matter what `--realization` says. Its `denial` term is
   discounted by `p_front_a_falls` (0.25) while its `earn` term is not discounted at
   all, which structurally favours attacking.
2. **`allocate_fleets`'s `earn` is not gated by P(clearing THEIR front-A)**, though
   `offense_value` does gate the equivalent term with `p1`. The account's top five
   offence squads give P(clear a 5-squad front) = 0.539, so the fleet earn is nearly
   doubled by this omission.
3. **`--realization` does not change the squad SELECTION at all.** The 15 walls chosen
   at r=1.0 and at r=0.37 are byte-identical; only the reported `offense` number moves.
   Either contention between the pools is too low to bind, or the local search is not
   exploring the defence/offence trade. Unresolved.

**⭐ CORRECTIONS TO WHAT I WROTE EARLIER TONIGHT:**
- I called the fleet split the **"root cause"** of losing round 2 and priced it at
  **+57 banners**. Both wrong. Correcting defects 1 and 2 above and re-deriving:
  attack-best beats wall-best by **+33 at r=1.0 and +6 at r=0.37**, and it wins at
  every r from 1.0 down to 0.25, so the DIRECTION was right and the MAGNITUDE was
  roughly double what it should be. It is not a root cause of a 461-banner loss.
- The real round-2 story is denial, not offence: **the opponent scored 2,045 of the
  2,082 available, a 98% conversion, so the board denied about 37 banners.** Astra
  meanwhile cleared all 15 of their squads and took 3 territories.
- ⇒ **`offense_value`'s "this account converts about 37%" is STALE.** CLAUDE.md dates
  that figure to a period with "~493/round stranded behind a front zone he left at
  3/4". Round 2 measured **squad conversion at essentially 100%** and overall 76%, and
  the entire 498-banner shortfall was the fleet territory, which was forfeited because
  the three best capitals were walling. **Use r ~= 1.0 for squads.**

**WHY THE PLACED BOARD STANDS.** The pin set was hill-climbed at r=1.0. Re-climbing at
r=0.37 finds a different optimum (add The Stranger and SLKR to the wall, net -312 to
-283). But the two boards cross over at **r ~= 0.85**: the r=0.37 board is +29 at
r=0.37, +3 at r=0.8 and **-10 at r=1.0**. Since measured squad conversion is ~1.0, the
board already placed is the right one. Re-placing would be a downgrade.

**WHY THE FLEET SPLIT WAS LEFT ALONE.** Worth +33. Against that: three full manual
8-ship rebuilds, and walling Raddus/Home One locks a different crew set than
Leviathan/Executor/Negotiator does. The crew-to-capital mapping is NOT in this repo, and
a squad losing a unit costs a whole wall (the 21.6% GL Leia squad is 59 banners plus its
share of the front-A gate). Spending +33 of expected value to risk more than that, on a
board already verified correct, is a bad trade. Revisit once crew data exists.

### 2026-09-21 (05:40) — ⭐⭐ THE OWNER WAS RIGHT: DEFENCE DOES NOT HOLD, SO THE BEST SQUADS ATTACK

Owner: *"you need to keep the best teams for offense. GLs on defense should be limited."*
He is right, and there is first-party evidence for it that this repo had never looked at.

**THE MEASUREMENT THAT SETTLES IT.** `gac/get` returns
`gac.home.player.defensePercent9` and `defensePercent14`. For Astra they are **14 and 2**
(opponent Kyp Durron: 66 and 10). And round 2 is unambiguous: **the opponent scored 2,045
of the 2,082 available, 98.2%, so the board realised 1.8% denial** while
`gac3v3_board.py` was predicting 66%. Astra's own offence cleared **15/15 squads**.
⇒ **realised offence ~= 1.0, realised defence 0.02-0.14.** The model prices BOTH at 1.0,
which is precisely why it over-walls. Scale the defensive rates by the measured d and the
whole argument for walling GLs evaporates.

**WHY Hold% IS NOT TRANSFERABLE AND Win% IS.** swgoh.gg measures Hold% over ALL attackers,
including the ones who threw the wrong squad at it. A Kyber-3 opponent routes the correct
counter, so what you realise is the lower tail, not the mean. Win% has no such problem
because you also choose the matchup. The repo already half-knew this ("1 - Win% IS NEVER A
HOLD RATE") without drawing the consequence.

**AND THE MODEL'S OFFENCE TERM IS MATCHUP-BLIND, WHICH IS THE OTHER HALF.** `/gac/counters/`
is genuinely Kyber and format scoped ("Season 83 - 3v3", 35.6K battles on Lord Vader alone)
and the spread is enormous for the SAME wall:
- **Lord Vader** wall: **Darth Bane + Count Dooku 98%**, Bo-Katan/IG-12/Mando 93%,
  SLKR 87%, **GL Leia / Captain Drogan / R2-D2 86%**.
- **SLKR** wall: **Darth Bane + partner 87-94%** (n=388, 117, 55), Stranger trio 100% (n=8).
⇒ **Darth Bane is the universal answer and he is single-use**, so breadth of attackers is
the binding constraint, not average win rate. `offense_value` sums generic rates over the
top 15 and cannot see any of this, so it treats the 15th and 16th squads as interchangeable
when they are not.

**EVERY ONE OF THE NINE GLs HAS AN S83 OFFENCE ROW** (Rey 79.3% n=1,245 up to Lord Vader
92.5% n=16K). By CLAUDE.md's own rule 7 - a GL walls only if it has NO offence role - none
of them should wall. The 3v3 "K = 4 or 5 GLs wall" finding was measured on this same model
and inherits its denial error.

**WHAT WAS PLACED (verified via `gac/get {refresh:true}`, all 15 squads full 3-unit):**
`output/gac3v3_board_r3_v3.json`, net +311, **only 2 GLs walling**.
- FRONT-A: GL Rey · Kelleran Beq · GL Leia · Great Mothers · Stormtrooper Luke
- FRONT-B: Rotta · Cassian (Undercover) · Carson Teva · Darth Traya · Iden Versio
- BACK-B : Snowtroopers · Thrawn · Tuskens · Boss Nass · Satele Shan
Freed for offence: **Lord Vader 92.5%, Ahsoka 91.6%, The Stranger 91.6%**, plus SLKR, Jabba,
JMK, JML, SEE. Rey (79.3%) and Leia (79.6%) still wall because they are the 16th/17th best
attackers and would not make a 15-attack rotation anyway.
Cost against the 02:45 board: **-47 on the model objective, all of it in the denial term the
data falsifies.** At the measured d the two are within ~10.

**⛔ TWO PLACEMENT TRAPS, BOTH COST REAL TIME TONIGHT.**
1. **Every HotUtils write kicks the client and the kick lands LATE.** Three separate
   in-flight squad removals were silently discarded by a CONNECTION LOST that fired seconds
   after a `squads/game/set`. Finish ALL pushes, reload once, then place, and touch nothing
   HotUtils-side until the board is done.
2. **RESTRICTED CHARACTERS is not always fatal and not always survivable.** The same dialog
   placed A4 (with R2-D2) and K3 (with TIE Fighter Pilot) full 3-unit earlier, but returned
   an EMPTY builder for the Stranger squad. Read the zone count after, never assume.
3. In the preset picker, tap the squad NAME ROW. A portrait opens the character sheet, and
   a header sitting in the bottom ~15% of the list does not register - nudge it up first.

## 2026-09-22 (11:24-) — GAC ROUND 3 LOST ON THE FLEET SPLIT, AND ALL 15 CRONS ARE ON

### ⛔⛔ THE OVERNIGHT NOTE WAS WRONG TWICE, AND BOTH ERRORS WERE FREE TO CHECK
It said "1,603 to 0, three of four territories conquered" and "the fleet zone was two first
attempts, so rule 6 says walk away". Live `gac/get` at 11:50 says **1,605 to 1,629**, and
`away.zones[fleet].squads[].successfulDefends` reads **1, 2, 3**.
- ⭐ **`successfulDefends` IS THE PER-TARGET ATTEMPT COUNTER.** Six fleet attempts were spent
  and all six lost. Reading it as "we made two attempts" turns a zero-bonus fourth attempt
  into an imagined free first. Read it before every attack decision.
- ⭐ **`zones[].score` on YOUR side sums to the scoreline.** 550 + 537 + 2 + 516 = 1,605.
  The `2` is the fleet zone: six losses paid one banner twice and nothing else.
- ⇒ The round was never won. It ends 2026-09-23 00:00 EEST at a **24-banner loss**, and the
  week is **1-2** (R1 win, R2 loss, R3 loss). Skill rating stays ~3,165, Kyber 3.

### ⛔ THE FLEET POOL WAS EXHAUSTED, AND THAT IS THE WHOLE STORY
The attack builder for the enemy Profundity offers **Raddus alone, 56,083 power, "No other
Ships available"**. 23 ships sit on our three defensive fleets and the other ~46 were spent
across the six attempts. There was nothing left to attack with at 11:50 and nothing to do.
- ⭐⭐ **THE FIX IS THE INVERSION `gac3v3_board.py --fleets` HAS WANTED FOR WEEKS.**
  Wall **Home One 13.7% / Negotiator 12.9% / Raddus 8.1%**, attack with **Leviathan 95.5% /
  Executor 91.4% / Chimaera 81.7%**. Model: expected denial 24, expected offence 360.
- ⭐ **WHY IT IS NOT A CLOSE CALL.** The live S83 `/gac/ship-counters/` pages for
  CAPITALPROFUNDITY, CAPITALLEVIATHAN and CAPITALEXECUTOR return 50 rows each, and **every
  single row attacks with Leviathan or Profundity**. Astra owns Leviathan and not
  Profundity, so walling Leviathan deletes the only measured counter this roster has.
  Scraped 2026-09-22 with Playwright MCP (chrome-devtools could not clear Cloudflare that
  day; Playwright needed one retry after a 403 and then passed).
- ⛔ **IT CANNOT BE DONE MID-ROUND.** In EDIT DEFENSES the fleet zone shows ALLIED FLEETS 3/3
  with **ADD FLEET greyed out**, and every ship is spent, so removing one leaves a hole you
  cannot refill. Do it in the next DEFENCE phase, off the fresh pool.
- ⚠ Our walled Leviathan is running **7 of 8 slots**, donating one banner. Still not worth a
  manual 8-ship rebuild on its own; fix it when the fleets are rebuilt anyway.

### ⭐ ALL 15 DEFENSIVE SQUADS NOW CARRY A DATACRON (was 5)
`gac_cron_assign.py` re-run against the fresh `account/data/all`; the allocation is unchanged.
FRONT-A Rey L9 · Kelleran L9 · GL Leia L6 · Great Mothers L9▶8 · ST Luke L6.
FRONT-B Rotta L15 · Iden L9▶8 · Traya L9▶8 · Cassian L9▶8 · Carson Teva L8.
BACK-B Satele L9▶8 · Snowtroopers L3 · Thrawn L3 · Tuskens L4 · Boss Nass L6.
- ⭐ **KELLERAN HAD THE WRONG TWIN.** Two set34 L9 crons scope
  `lightside/jedivanguard/<character>`: one ends in **quigonjinn**, one in **jocastanu**.
  The 06:03 pass equipped quigonjinn. Jocasta Nu is IN the squad, so the jocastanu twin
  applies all three tiers **and shows plain `Lvl 9` with no relic downgrade** while the
  other reads `Lvl 9 ▶ 8`. The downgrade arrow is a reliable tell that you picked wrong.
- ⭐ **CARSON TEVA'S set33 Lvl 8 IS THE SECOND-BEST CRON ON THE BOARD**: **+120% Defense,
  +50% Health, +50% Offense, +50% Crit Damage**, tier 2 scoped to him, and NO downgrade
  despite the squad's lowest relic being 4. Set-33 focused crons cap differently from set 34.
- ⚠ **READ THE PICKER, THE PLAN'S TAG FILE LIES BOTH WAYS.** GL Leia's squad matched tier 2
  `resistance` only because **R2-D2 is Resistance**, which is not obvious; Great Mothers
  matched `tank`+`support`; and the picker prints "Does not apply to any characters in the
  current squad" per tier, in red, every time. Trust it over `data/unit_tags.json`.
- ⚠ **SET 32 EXPIRES 2026-10-01** (swgoh.gg, checked 2026-09-22; set 35 "Duty and Defiance"
  is already live to 2026-12-24, set 33 expires ~late Oct, set 34 on 2026-11-26). Great
  Mothers, ST Luke and Cassian carry set-32 crons and will go bare partway through the next
  event. Re-run `gac_cron_assign.py` on 1 Oct.
- ⚠ **In EDIT DEFENSES the `5/5` badge IS the hit target.** Three taps that looked like a
  wrong coordinate were taps issued while the board was still animating in from `back`.
  Let the screen settle, then tap once.

### TERRITORY WAR: 8 MORE SQUADS PLACED, AND THE DRIFT IS BEATEN BY UNGUARDED RE-SWEEPS
Special Ops Center (a back territory, device (110,750)) went **24/38 to 32/38**, so **+240
guaranteed banners**. All three preset tabs now report every row either committed or placed.
- ⭐ **`tw_fill.py`'s row guard is what blocks the last rows, not the scroll.** At BACK idx 23
  and 24 the paging slips exactly one row, so the guard correctly sees B23 where it wanted
  B24 and refuses. `--loose` does not help: the neighbours are 37,833 GP apart, far outside
  its 12,000 window. **Call `tw_fill.one(idx, TABS[tab], None)` directly instead** (expect
  None disables the guard) and sweep the tail repeatedly; RESTRICTED still prevents any
  double placement, and three passes converged. That is the concrete form of the
  `tw-fill-index-drift` rule.
- ⚠ A `CONNECTION ERROR / TRY AGAIN` popup during a sweep kills it with `not on PVP ('BS')`.
  Tap TRY AGAIN, confirm the allied count, resume from the last index.
- Jakku territories and capacity at 12:40: Command Post 38/38 FULL · Hangar 34 · Supply Depot
  31 · Trenches 25 · Forward Turrets 25 · Ion Cannon 25 (gold note "Bugs/sisters") ·
  Airspace 24 (fleet) · Special Ops Center 24 · Main Base 21 (fleet).
- ⚠ `tw_goto.py --scan` OCRs the NOTE unreliably: nine of ten came back as noise and only
  Ion Cannon parsed. Use it to find territories by NAME, not to read the officer note.

### MODS AND EVENTS
- Two slice steps executed: plusSpeed 16,967 to 16,971, 420,000 credits. **Micro Attenuators
  are at 3 (currency id 41), so calibration is still dead.** Slicing is gated on T05_06
  (short 905), T06_02 (225), T05_04 (221): Mod Battles chapter 2 and Episode Shipments.
- ⭐ **PROFUNDITY'S NEXT EVENT IS 2026-09-30.** It ran 2026-08-31; the cadence is
  end-of-month, monthly (04-30, 05-31, 06-30, 07-31, 08-31, 09-30). CLAUDE.md updated.
  It is the single biggest free GAC upgrade available and it fixes the fleet problem above
  from the other side.
- ⛔ **The farmbot ran 19 minutes against the BlueStacks App Center and farmed nothing**
  because SWGOH was never launched. `--doctor` says "device: ready", the report says
  "run outcome: complete", and the only tell is `halted_entries=19`. Launch the game with
  `adb shell monkey -p com.ea.game.starwarscapital_row -c android.intent.category.LAUNCHER 1`
  and confirm `dumpsys window | grep mCurrentFocus` shows `CapitalGamesActivity` first.

### 2026-09-22 (14:00-17:00) — BOTH ARENAS TO #1, DAILIES 8/8, AND THE COLISEUM CEILING
- ⭐ **SQUAD ARENA #5 to #1 and the payout was taken at #1** (16:58 EEST). Two battles with
  the Hutt datacron squad (Rotta (L) / Gamorrean Guard / Greedo / Krrsantan / Mob Enforcer,
  165,916), beating a 181,741 GL Leia team and then the live #1. Knocked back to #5 once
  in between and re-climbed. Defence is the squad you last attacked with, so it is parked.
- ⭐ **FLEET ARENA #11 to #1** in five battles (11>7, then knocked to 10, 10>6, 6>2, 2>1).
  Target selection is the whole game: take the HIGHEST rank you can beat, because a win
  SWAPS ranks. Fleet power 607,927 against opponents at 426-532K.
- ⚠ **Two arena blockers to plan around.** `Somebody is already battling you` means an
  opponent is mid-attack on your defence and EVERY attack of yours is refused until they
  finish. And each opponent card carries its own 3-8 minute cooldown with a 50-crystal
  skip; buy the skip only near the payout, which is the standing crystal rule.
- ⚠ **The arena font's 5 reads as 9 again.** "My Rank: #9" on the battle result was #5
  every time. Third session in a row this has bitten. Cross-read the Select-an-Arena panel.
- **Daily quests 8/8 + the all-quests crate.** The 600-energy quest was closed by dumping
  the **DARK SIDE overflow (229/144)** as 22 MULTI SIMs on Takodana 8-D NORMAL.
  ⚠ The big overflowing pool on the home bar is dark side, NOT mod energy; mod was 18/144.
- ⭐⭐ **EPISODE SHIPMENTS SELLS SIGNAL DATA, AND CLAUDE.md SAYS IT DOES NOT.**
  Fragmented Signal Data 45 for 4,500 and Incomplete Signal Data 40 for 5,400, one of each
  per refresh. The claim "SIGNAL DATA is cantina-energy-only, no store sells it for a
  token" is wrong. Episode currency was 60,900 with no competing claim; 49,400 left after
  three purchases (which also closed the 3-shipments quest). Signal Data is the largest
  single line in every relic recipe from R6 to R9, so this is a real R7-to-R9 faucet the
  repo did not know about. Buy it every refresh.
- ⛔ **COLISEUM: THE COMMUNITY META SQUAD DOES NOT BEAT AUTO'S CEILING.** Boss DRYAX,
  tier 9, high score stuck at **235,040 (47%)**, rank 267. Rebuilt to the #2 community
  lineup (**JK Luke Skywalker (L, loaned) / Mara Jade Skywalker / JK Cal Kestis (loaned) /
  Dark Trooper (loaned) / Stormtrooper (Concept)**, reported 93% on T11) and the in-game
  synergy pips confirmed it: Mara and Cal go to **2/2** under the JKL lead against 0/1
  under the Darth Maul lead the game pre-loads. It still did not beat 235,040 on AUTO.
  The gap is the Dryax mechanic AUTO cannot play: while one Dryax is 12% off the other's
  health it gains stacking Offense and inflicts Daze plus Buff Immunity, so the fight is
  about keeping the two EVEN. **Two attempts banked on purpose.**
- ⭐ **The filter dialog's TEXT SEARCH makes squad building cheap.** Tap the box,
  `keyevent 123` then 20x `keyevent 67` to clear, `input text "Cal%sKestis"`,
  `keyevent 66`, CONFIRM. The one matching portrait lands at device (115,480).
- ⭐ **Image budget: `screencap | sips -Z 800 -s formatOptions 40` is ~45KB per full
  screen** against ~130KB for `d.sh`'s 1100px/q55, with every button label still legible.
  Use it for any long device session. `scripts/ocr.sh` against the native 1920px capture
  is slow enough to blow a 120s Bash timeout; downscale to 1300px before tesseract.
- Free Bronzium claimed. **68.9K ally points are idle** (250 per pull, ~275 pulls); no
  other sink exists for them, so they are worth a batch run some session.
- Inbox: a Kessel Run reward notice that can only be claimed on the EA website, not in game.

### ⛔ CORRECTION, 2026-09-22 17:40 — ROUND 3 WAS FOUGHT WITH **ZERO** DATACRONS ON DEFENCE
Owner caught this. Two errors of mine, one on top of the other.
1. **`gac/get` HAS NO `datacron` FIELD ON A UNIT.** The unit object carries
   `baseId, cellIndex, cqOmiCount, gacOmiCount, gearLevel, id, image, killed, level,
   omiCount, rarity, relicLevel, state, stats, tbOmiCount, twOmiCount, ultimate,
   unitDefId, zetaCount, zetaLead` and nothing else, on BOTH sides, all 90 units. So
   `u.get('datacron')` returning None is not evidence of anything. **Never infer cron
   state from `gac/get`.** The in-game EDIT DEFENSES squad row is the only oracle: a cron
   shows as a fourth "portrait" with its level under it.
2. **The five crons attached at 06:03 were PENDING, NOT LIVE, for round 3.** Round 3's
   attack phase started 2026-09-22 00:00 EEST, so 06:03 is inside it, and the screen says
   *"Defense changes deploy when the next Attack Phase starts."* The board the opponent
   actually attacked was the one set during round 3's DEFENCE phase on 21 Sept, which the
   06:03 note itself describes as "found with all fifteen squads carrying no datacron at
   all". ⇒ **Kyp Durron attacked a datacron-free board.**
⇒ The cron pass explains nothing about the 24-banner loss. All 15 land at the FIRST attack
phase of the next weekly event, together with the fleet inversion. Two consequences:
- **Attach crons during the DEFENCE phase, never during the attack phase**, or they sit
  idle for a whole round. This is the sharp edge of `gac-defence-datacrons-are-mandatory`.
- When auditing "is the board set", audit the DEPLOYED board, and remember EDIT DEFENSES
  shows the PENDING one. The two differ for the whole of every attack phase.

---

## 2026-09-23 (overnight) — TW offence failed 0-for-2, and the cause is the defence plan

### GAC S83 is OVER. There is no round 4, and nothing was actionable tonight.
`gac/list` is unambiguous: the event `...SEASON_83:O1789592400000` has **exactly three
matches**, and match 3 ended 2026-09-22 21:00 UTC (00:00 EEST) at **1,605 to 1,629**.
Round 1 win 1,080-68 vs Melkor, round 2 loss 1,584-2,045 vs Papam, round 3 loss vs Kyp
Durron. Event record 1-2. Match 3 was mathematically lost well before the end: +25 banners
were needed and the fleet pool was exhausted, so per the standing rule ("do not grind
banners after the round is decided") nothing was thrown at it.
⭐ **`squad.datacron` in `gac/get` IS readable and IS populated.** The 2026-09-22 note says
"`gac/get` has no datacron key on a unit at all", which is true of the UNIT record and
misleading: the key lives on the **squad**. Kyp Durron's board returned `dc:1` on two
squads (Jabba, Boss Nass) while all fifteen of ours returned `dc:0`. That is independent
first-party confirmation that round 3 was fought with a datacron-free board.

### ⭐⭐ THE FLEET INVERSION, READY TO EXECUTE AT THE NEXT SETUP PHASE
`gac3v3_board.py --fleets` against the live S83 lists:
- **WALL: Home One 13.7% · Negotiator 12.9% · Raddus 8.1%**
- **ATTACK: Leviathan 95.5% · Executor 91.4% · Chimaera 81.7%**
- P(fleet territory holds) 31%, expected denial 24, expected offence **360**.
We did the opposite in S83 and the attack pool topped out at Home One 77.3%, which is how
six fleet attempts went 0-for-6. A fleet is 8 tiles in BOTH formats, so this split carries
into a 5v5 season unchanged. ⛔ It can only be set in a DEFENCE phase.

### TW: two attacks, two zero-kill losses, and it was not bad luck
Jakku, attack phase, us 11,902 vs them 13,856 and falling. Forward Turrets 27/38 then
26/38 (a guildmate killed Reznov mid-session). Conquer is **+830**, first-party off the
territory panel; "Offense Win: +6-20", "Set Defense: +30".
- **SEE solo, 57,141 + a set-34 dark-side Lvl 3 cron = 97,141** vs a 133,986 Gungan wall.
  Lost, 5 enemies alive.
- **JML (L) / Hermit Yoda / JK Cal / JK Luke / Jocasta Nu, 192,348** + a light-side Lvl 3
  cron vs a 137,766 Gungan wall. Four Jedi dead by 3:19, JML alone, lost. 5 enemies alive.
Both forfeited rather than submitted, because zero kills means the chip damage is
negligible and SUBMIT would have gifted the wall the turn meter it built.

⭐ **Root cause: the defence plan ate every counter.** A TW unit is single-use, and the ~300
units placed on defence include Traya/Nihilus/Savage (this repo's own measured Boss Nass
answer, n=5,947), JMK, SLKR, Satele, Queen Amidala, **Darth Bane, Wat Tambor, Shaak Ti,
GM Yoda and Inquisitor Barriss**. Every one of those is a member of a measured top counter
row. The offence bank was chosen by unit ECONOMY (`Net = 20p - 6U`) and never by matchup,
so it reserved the three highest-GP leftovers instead of a squad that beats something.
⇒ **Choose the TW offence reserve during SETUP, by naming the target archetype.**

⚠ **`Net = 20p - 6U` is a SETUP-phase trade only.** Once the attack phase opens, no more
defence can be placed, the 6-banner placement value is sunk, and an unused unit is worth 0.
That argues "attack with everything" and it is WRONG, because a zero-kill loss leaves the
defender its turn meter for the next guildmate. Attack only with squads that can win.

⚠ **THE 3v3 COUNTER FILE IS THE WRONG TABLE FOR TW, AND IT IS WHAT COST SEE.**
`counters_3v3_s83_20260922.json` ranks **SEE + Darth Bane 100% (n=111)** against a Boss
Nass lead, which is why SEE went first. In 3v3 that lead fields **3** Gungans; TW fields
**5**. The 5v5 files said it properly all along: `meta_def5v5_s82.txt` has Boss Nass at
**23% hold on n=31.1K** and `meta_off5v5_s82.txt` has **SEE + Wat Tambor 86% on n=5,842**
as the real 5v5 answer, with Wat Tambor sitting on our own defence. **TW is always 5v5.**

⚠ **Power is an ANTI-signal for Gungan walls.** In Forward Turrets the four lowest-power
squads (133,986 · 137,766 · 141,665 · 146,335) were ALL Boss Nass Gungans, because Gungans
are cheap and tanky. Sorting targets by ascending power walks you straight into the hardest
matchup on the board. Identify composition before choosing a target: crop the portrait row
at native resolution (`sips -c 105 900 --cropOffset <322|592|862> 30`, then upscale 3x).

### Technique that paid off
⭐ **`power.total` from HotUtils `account/data/all` is a UNIQUE FINGERPRINT for reading the
in-game available-unit list.** The TW attack screen shows `Pwr NNNNN` and no names, and
OCR of that column maps straight onto the roster (291 of 333 characters have a unique
total; the GL cluster at 57,429 is the notable collision). Saved to
`data/pw_fingerprint_20260922.json`. That is how the offence pool was enumerated.
⚠ **Scroll in SMALL steps when enumerating it.** A 430-490px swipe silently skipped rows and
hid JK Cal, Hermit Yoda, Jocasta Nu and Ki-Adi-Mundi; a 200px swipe found all 25. The first
pass produced a confident, wrong "the JML squad is not fieldable".
⭐ A **Lvl 3 datacron is worth ~+40,000 squad power** (SEE 57,141 to 97,141). Never skip the
cron on a TW attack. Free crons are the ones not in `output/gac_cron_plan.json`.

---

## 2026-09-23 (daytime) — the Scavenger is the lever, and crystals are not

Owner lifted the spending rail: "any resource EXCEPT real money". Every crystal sink was
tested and **4,858 crystals were deliberately NOT spent**, because none of them buys
anything this account needs. What DID move was free.

### ⭐⭐ THE SCAVENGER CONVERTS JUNK GEAR INTO THE FORCED RELIC MATERIALS
`action_value.py` names three materials as FORCED (no substitute at any price):
**Aeromagnifier** (Mk III raid tokens only) and **Chromium Transistor / Aurodium Heatsink**
(Mk II only). The GET3 balance is **5 tokens**, so the Mk III route is effectively shut.
The Scavenger (hub far-right pan, next to Galactic Battles) targets all three directly.
- **Aeromagnifier: 2 → 230.** Pool was Mk IX / Mk VII / Mk XII at 9 value, 175 value each,
  roughly 19.4 pieces per unit. Spent ~4,400 pieces, kept 365 Mk IX + 96 Mk XII in reserve.
- **Aurodium Heatsink: 386 → 821.** Pool is a DIFFERENT gear tier (Mk III / V / VII / VIII
  at 5 value), 50 value each, so the two targets do not compete for input.
- **Chromium Transistor left alone on purpose**: its pool is Mk VIII-XI, which is real
  gearing stock, not junk, and it already sits at 474.
- Mechanics: multiplier cycles **x1 → x10 → x50 → x1** (x50 is the max). Leftover value is
  **credited to the next unit**, so nothing is wasted and big batches are safe.
  ⚠ The input list re-sorts by COUNT as you assign, so a long tap-loop drifts onto a
  different item. Assign in batches of ~20 taps and re-read. One batch consumed all 426
  remaining Mk VII instead of leaving the reserve I intended. Junk, so harmless, but the
  drift is real.
⇒ At 40 Aeromagnifiers per R7→R9, 230 is about **6 units' worth of the hardest line**, and
it cost nothing but gear that had no other use. **Do this every time gear piles up.**

### ⭐ COLISEUM: THE BLOCKER WAS THE SQUAD, NOT THE ATTEMPTS
The 2026-09-22 note banked attempts because "the meta squad does not beat AUTO's ceiling".
That was measured against **Dryax**. The boss rotated to **Krayt Dragon** and the correct
board is different. holotables.xyz/boss/krayt-dragon ranks by score; the top three all run
**Darth Jar Jar + Yoda (Dark Side Vision)** and Darth Jar Jar is **NOT OWNED**, so the
fieldable optimum is board #4:
**JKL (L, loaned) / Mara Jade Skywalker / JK Cal Kestis (loaned) / Mace Windu (loaned) /
Barriss Offee (loaned)** — every non-leader pip reads **2/2**.
- Tier 8 went to **100% / 380,000 on the FIRST attempt**, which **unlocked tier 9 AND
  refilled attempts 4 → 5**, exactly as `coliseum-squad-synergy-indicator` says. Rank
  417 → 300.
- ⚠ The game pre-loads a **Darth Maul** lead that reads 0/1 on three units. Always re-lead.
- ⚠ **Yoda DSV reads 0/2 under a JKL lead** despite being the highest era unit (93). He
  only earns his place next to Darth Jar Jar. Do not force him in.
- Tier 9 converged at **25% (101,981)** across three AUTO attempts, including one after the
  era upgrade below. Two attempts left deliberately unspent.
- ⭐ Squad building is cheap via the filter's **TEXT SEARCH**: tap filter, tap the box, clear
  with `keyevent 123` + 24x `keyevent 67`, `input text "Mace%sWindu"`, tap OK (1838,1015),
  CONFIRM (1495,958), then the single match lands at **(115,480)**.

### ⭐ ERA LEVELS ARE THE COLISEUM GATE, AND COLISEUM PAYS FOR THEM
The Coliseum runs paid **~23,000 era_upgrade_basic_1, ~10,500 each basic_2/3, 2,750
basic_4, 1,060 advanced_1** and more. Era Units screen (Collection → Era Units) shows
**Total Era Level 363, next reward at 425**.
**Mara Jade Skywalker 90 → 92** (+122 Special Damage, +31.19% Resistance), which puts her
above the **loanedUnitEraLevel of 91** and she is the ONLY owned unit in the Krayt board.
⚠ The star-gate material is SHARED across era units and Mara consumed it (835 → 185), so
Yoda (needs 450), Starkiller (300) and Stormtrooper Concept are now blocked. Spending it on
the Coliseum squad member was the right sink.

### EVENTS BEAT NODES FOR SLICING SALVAGE, BY A LOT
- **Smuggler's Run II** (Resource Event, one tier, R3+/Jabba/5 Hutt-Smuggler, SIM x2) and
  **Rebel Roundup** (Assault Battle, tiers I-III, all SIM-able) were both sitting unplayed.
- Together they paid **T05_06 49 → 201 (+152)** and **attenuators 6 → 98 (+92)**, plus 9
  mods and relic mats.
- Against that, **Mod Battles 2-F measured +1 T05_06 and +2 attenuators per 126 mod
  energy** (7 sims). ⇒ **That settles the farmbot config's open 2-F vs 2-D question the
  way it asked to be settled: neither node is a viable T05_06 farm. The events are.**
  Do NOT buy mod-energy refreshes for slicing salvage.
- With the new stock `execute_upgrades.py` promoted **Threepio & Chewie 5A → 6E**, and the
  binding material moved off T05_06 onto **T05_04 (59)** and **T06_02 (15)**.
- Calibration now runs (98 attenuators) but still throws `rc=2 GOHServiceCall Error [40]`
  after one attempt, so a second material gates it. One reroll missed and reverted cleanly.

### WHY NO CRYSTALS WERE SPENT (all seven sinks tested)
1. **Mod energy refresh** (50c/120) — measured above, ~1 T05_06. Worthless for a 900 gap.
2. **Cantina refresh** (100c/120) — Flawed Signal Data is cantina-only, but the need is
   **16,200**. Rounding error.
3. **Episode Shipment refresh** — **not offered**; it runs a fixed 5d20h cycle with no
   crystal button. Signal Data cannot be re-bought early.
4. **Era Shipment** — 1,278 era tokens against a 1,380 floor, and it sells Coaxial
   Servomotor, not era XP.
5. **Conquest** — **not running, next event in 5d 7h**, so Stim Packs buy nothing.
6. **Arena refreshes** — both arenas already **#1**.
7. **Hard-node refreshes** — no named unit is gated on shards; the named gaps are
   event-gated (Profundity 09-30, Third Sister via RotE) or gear-gated.
⇒ The honest answer is that this account's bottlenecks are event-, guild- and
farm-gated. Crystals stay banked at 4,858.

### TW closed out 0-for-3
Inquisitorius (GI lead, 7 TW omicrons, 161,236 + a Lvl 3 dark cron) went into **beeeeer**,
the lowest-power AND lowest-relic (all R5) Gungan wall left, and lost with **zero kills**;
forfeited. That is three zero-kill losses from the three best available squads.
⭐ Corroboration that it is not just our roster: **beeeeer showed `Battles: 5` and was still
at FULL health**, so five guildmates had already attacked and every one of them forfeited.
War ended 12,144 vs 23,928 with Forward Turrets at 16/38.

---

## EVENT UNITS TO GRAB, AND WHAT TO PREPARE (written 2026-09-23)

### ⭐⭐ 1. PROFUNDITY — 2026-09-30, READY, NOTHING TO PREPARE
Re-verified against `swgoh_roster_fresh_20260922.json` today: **all 14 gates PASS.**
- Ships, all 7★: UWINGSCARIF · UWINGROGUEONE · XWINGRED3 · XWINGRED2 · YWINGREBEL ·
  GHOST · OUTRIDER
- Characters: Admiral Raddus **R9**, Cassian Andor **R8**, Dash Rendar **R7**,
  Mon Mothma R7, Bistan R7, Jyn Erso R7, Hera (HERASYNDULLAS3) R6
⛔ **Raddus, Cassian and Dash sit EXACTLY at threshold.** Do not strip or re-assign their
relics for anything between now and the event, and do not let a relic plan touch them.
⛔ **PLAY IT MANUALLY. The Stardust Transmission cannot be simmed or auto-farmed.**
Profundity is 24.8% hold AND 98.4% win, the best capital in the game on both sides, and it
is the biggest free upgrade available to this account. It is also exactly what beat us in
GAC S83: the opponent's fleet zone ran Profundity and we had no answer.
⚠ Confirm the date on swgohevents.com/event/profundity in the days before, do NOT trust this
line. Cadence is end-of-month monthly (04-30 · 05-31 · 06-30 · 07-31 · 08-31 · 09-30) and
this repo has already been burned once by a stale Profundity date.

### ⭐ 2. THIRD SISTER (Reva) — PREP NEEDED: NINTH SISTER R6 → R7
Farmed from the RotE **Phase 3 · TATOOINE** special `special_reva` (1 shard per guild
victory, guild max 50), NOT bought. Zone 3 applies a blanket rule: **every unit must be
7★ AND Relic 7+**.
Verified today, the account clears it with **EXACTLY five and zero slack**:
**Grand Inquisitor · Seventh Sister · Fifth Brother · Marrok · Inquisitor Barriss**
(all 7★ R7). **Ninth Sister is R6 (FAIL) and Eighth Brother R5 (FAIL).**
⇒ **The one prep action worth doing: take Ninth Sister R6 → R7.** It is a single relic
level, it restores the comp the published guides actually use (GI / 7th / 9th / 5th / 8th),
and it gives a spare body so one bad relic move cannot lock us out of the farm entirely.
The 230 Aeromagnifiers and 821 Aurodium Heatsinks banked from the Scavenger today are
exactly the forced materials that feed this.
⛔ **One attempt, no retries** — Special Missions complete once. Do not auto-battle it.
⚠ Do not confuse it with the PHASE 4 Medical Station special, which *requires* an owned
Third Sister at R8 and pays 1,000 Mk III tokens. One mission FARMS her, the other SPENDS her.
Why she is worth it: turns an already-owned R7 Inquisitor bench into both a **26% wall** and
an **85% attacker**.

### 3. UNITS WE DO NOT HAVE AND WHAT THEY WOULD BUY
- **Darth Jar Jar — NOT OWNED.** Gates the #1 Coliseum board by a wide margin: the top three
  holotables Krayt Dragon boards all run him, scoring **1,054,555 / 656,663 / 629,089**
  against the **226,793** board we can actually field. If a Darth Jar Jar event or farm
  appears, it is the single biggest Coliseum upgrade on the table.
- **The Ronin — NOT OWNED** (era unit, listed in Collection → Era Units).
- **GL Hondo — NOT OWNED, and explicitly NOT a gap.** Do not spend on him.
- **Jaxxon — 15/30 shards**, marquee has ~6d left. Tier 3 needs him at 4★, so the marquee
  self-blocks until 30 shards. Keep clearing whatever tiers unlock; Tier 1 also paid a
  5,000-point Episode quest.

### 4. NEAR-TERM EVENTS TO NOT MISS
- **Smuggler's Run III — 2026-09-25** (swgohevents front page). Smuggler's Run II paid a
  large part of today's **+92 attenuators / +152 T05_06**, so III is worth clearing the day
  it lands. See [[events-beat-nodes-for-slicing-salvage]].
- **Assault Battles and Resource Events generally**: nothing red-dots them, they are
  SIM-able once starred, and they out-earn energy nodes by orders of magnitude. Check the
  EVENT ACTIVE tile every session.
- ⚠ **Journey Guide unlocks are largely PERMANENT now** (Solo Journeys / Guild Journeys /
  Galactic Legends tabs), so most GL and Hero's Journey unlocks are no longer date-gated;
  only rotating Legendary/Mythic events are. Profundity is one of the date-gated ones.

---

## 2026-09-23 (evening) — DARTH JAR JAR: "Terrible Tings" Legendary Event

**Where:** home → EVENT ACTIVE → Solo Events → **Terrible Tings** (Legendary Event, ends
~2026-10-20, same day as the Era of Myths & Legends). Four tiers pay **80 / 65 / 85 / 100
shards** (330 = 7★). Victory counts unlimited, rewards once.

### Tier gates, read off the in-game panels (NOT the web, which guessed wrong)
- **Tier I: NO requirements.** Borrowed Yoda (DSV) EL 130, solo. ✅ **WON 2026-09-23, 3★,
  35 turns, first attempt.** DJJ activated at **4★** (activation cost 100 credits).
- **Tier II (65):** Mara Jade / Yoda DSV / Starkiller / Stormtrooper (Concept) at 5★ (all
  met), **Starkiller EL 95** (✅ done 2026-09-23), **Jaxxon 5★** (the only open gate).
- **Tier III (85):** all six at 6★ **including The Ronin (NOT OWNED)** + a 7th line.
- **Tier IV (100):** all six at 7★ + six era-level lines.
⇒ Tiers III/IV are out of reach free-to-play while The Ronin is unowned. Do not spend on them.

### ⭐ Jaxxon 5★ is FREE by ~2026-09-26: the marquee pays 5 shards per daily refresh
Jaxxon was **4★ at 45/65** on 2026-09-23. The Action Jaxxon marquee's **Tier III replays daily**
("Refresh in" timer, ~20:55 EEST) and pays **5 Jaxxon shards** + Mk IX×2 + Mk VII×2 + 15.
Four refreshes = 65 = 5★. Marquee ends ~2026-09-29, so there is slack of ~3 days.
⛔ The shard-source screen puts a **€89.99 Jaxxon Bundle II** card where the unit page's
left arrow sits. A blind tap at (682,1008) opened its store page on 2026-09-23. Verify the
screen before every tap on that flow. Crystal packs (1,299 / 5,999 / 12,990) are not needed.

### Tier I recipe (Yoda DSV vs Grand Master Yoda) — solved, scripted
Each GMY stance takes damage from ONE ability: **Peace → Force Fisticuffs (x=1344)**,
**Justice → Consume, I Will (1505, cd 3)**, **Guardian → Hear Me, You Will (1663, cd 4)**;
matching ability on cooldown → **Bide (1824, cd 5)**. No AUTO button exists in this fight.
- Stance read: long-press GMY at (1183,199), full-screen OCR, grep "peace/justice/guardian
  stance". Dismiss with a tap at (300,900).
- Cooldown read: the countdown digit is white; **white-pixel fraction of the icon > 0.05 = on
  cooldown** (0.163 vs 0.000, clean separation).
- Driver: `~/Downloads/djj/yoda_loop.py` + `bt.py`. The stance cycle was near-regular
  (peace → justice → guardian); Bide covered every other Guardian. Zero forced misplays.

### Tier II recipe (Starkiller vs 3 Stormtroopers) — researched, not yet played
GAC Film Room, 2026-09-23 (won first try, 25 turns, 25 Air Supply left): Air Supply drops per
buff on each Stormtrooper at the start of its turn; 0 = loss. **Son of the Suns (1st special)
every time it is up** (Buff Immunity 2 turns + Shared Fate). **Laser-Sword Strike (basic)
the trooper that has buffs** (dispels all). **Grip of Tython (2nd special) only when nobody
has buffs.** Watch Air Supply, not health.

### Tier III / IV mechanics (web, for later): Luuke only takes damage with 2+ of
Blind/Defense Down/Stagger/Stun/Vulnerable, and you lose if Mara or JKL dies. Final tier:
Jaxxon must have Massively Overpowered, Viper Target Lock, Cal Kestis Manipulated when
defeated, or they revive; loss if any loaned unit dies.

### Era levels spent
- Starkiller 90 → **95** (Tier II gate): 2,000 of the first material + 100 rare + 47,700.
- **DJJ 0 → 91**: 1,050 + 50 + 100 + 2,750 + 454,500 era credits (1.01M → 556K).
- ⭐ The binding material is the FIRST icon on the level panel (silver stack): 3,350 → 300
  after both. DJJ 92 needs 350. Coliseum loans sit at EL 91, so 91 is the useful floor.

### Coliseum payoff the same evening: Krayt Dragon T9 25% → 40%
With DJJ at EL 91 the holotables DJJ board became fieldable: **DJJ (L) / Qi'ra / Yoda DSV /
JK Cal Kestis / Commander Luke** (loans at EL 91; only Yoda reads a full pip under DJJ).
Opening (JakeSkywalker's T9 line, adapted): DJJ S1 → Yoda S2 on DJJ (or Consume) → CLS Call
to Action + Use the Force → Qi'ra Scattering Blast → JK Cal (pistol, then Whirlwind Slam) →
DJJ S2 → then AUTO once only the Sith pair is left.
- Attempt 1: **160,618 = 40%**, new high (was 101,981 / 25%), paid the 30% and 40% rungs,
  rank 326 → 274. Attempt 2 with a 6-debuff stack before the eruption: 150,515 (37%).
- ⚠ **The loans die to the first surfacing either way at EL 91.** The Krayt's own tooltips:
  Violent Eruption **can't be evaded** and deals **9% less per debuff on it (max −50%)**;
  Corrosive Venom Spray (cd 3) **dispels all buffs first**, then AoE + Daze + Poison. So
  Foresight does not dodge either hit at this level; debuffs are the only mitigation.
- The DJJ pair then carries ~75K on AUTO. The 100% T9 boards run DJJ/Yoda at **EL 103+**;
  the gap is era levels, not play. More DJJ levels need the first-slot material (300/350).

### Era Shipment sells DROID BRAIN (corrects the "no token route" line above)
Era Shipment: **Droid Brain ×10 = 5,000 era tokens**, Aeromagnifier ×10 = 4,000, Gyrda Keypad
×10 = 4,500, Flawed Signal Data further down. Era tokens were 1,908 on 2026-09-23, so it is a
route, just not an affordable one yet. Era tokens come from Coliseum and era play.
