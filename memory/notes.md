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
- Even season = 5v5, odd = 3v3. As of 2026-07: S80=5v5 (current), S79=latest 3v3.

## GL allocation (defense-first, but reserve attack GLs)
- Offense always: JMK, JML, SEE, SLKR. 5v5 also GL Leia (96% #1 attacker).
- Defense: Lord Vader, GL Rey, GL Ahsoka, Jabba (+ GL Leia in 3v3).

## Fleets (grounded caps from /gac/ship-counters; reinforcements = faction meta from owned ships)
- Defense: Leviathan (81%), Negotiator (87%), Home One (90%).
- Offense: Executor, Malevolence, Raddus.
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
