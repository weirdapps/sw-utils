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
