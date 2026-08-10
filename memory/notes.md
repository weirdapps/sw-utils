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

### Still TODO (not done — would change unattended behaviour)
Swapping the bot's `campaign: fleet` entry from **1-E → 2-E** needs `farmbot/templates/node_fleet_2-E.png`
first (nav is template-matched; no template = that entry fails). Note `node_dark_8-B` ships a separate
`_sel` variant, so the crop must be taken with the node **unselected**. Config change without the capture
will just halt that entry.

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
