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
