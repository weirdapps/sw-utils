# SWGOH — Grand Arena team builder (Astra / Kyber 3 → Kyber 2)

Reusable pipeline that builds **grounded** GAC defense + offense squads and fleets from live
swgoh.gg meta + the player's live roster, and pushes them into **HotUtils** as organized squad groups.

"Grounded" is the whole point: every defense pick is a top-**Hold%** team on swgoh.gg and every
offense pick a top-**Win%** team — so when the player sorts swgoh.gg the same way, they see the same teams.

> **Read `memory/notes.md` FIRST.** It's the durable knowledge base — live board counts, GL allocation,
> every HotUtils API recipe (squads, in-game presets, mods slice/calibrate/level) and the gotchas learned
> the hard way. `scripts/browser_recipes.md` has the copy-paste browser JS. This CLAUDE.md is the map;
> notes.md is the territory. Session ids rotate — recapture each session (browser_recipes.md §4).

## What this repo can do (two pipelines)
1. **Build GAC teams** (grounded squads + fleets → HotUtils groups + in-game presets) — see workflow below.
2. **Optimize mods** for those teams (move → slice → calibrate → level) — see "Mod optimization" below.

## Player
- **Astra** · ally **145357294** · GAC league **Kyber 3** (climbing to Kyber 2) · ~14M GP.
- **9 Galactic Legends:** JMK, JML, SEE, SLKR, GL Leia, Lord Vader, GL Rey, Jabba, GL Ahsoka.
- **Known gaps:** Profundity (fleet — #1 defensive fleet), Third Sister (non-GL wall). *GL Hondo is NOT a gap — the "#1 3v3 wall" figure was all-league; it reads 3.5% in Kyber-D1 on S81.*

## Live board (Kyber, read from HotUtils GAC Planning — reconfirm each season)
- **5v5:** 11 defense squads + 3 fleets. **3v3:** 15 defense squads + 3 fleets. Offense mirror-clears.
- Config lives in `scripts/compute_teams.py` (`BOARD`). Update if league/board changes.

## Rules (encoded in the scripts — don't hand-wave them)
1. Every unit **owned + G13+**. 2. **No unit repeats within a format** (3v3 and 5v5 are separate seasons, so a unit CAN appear in both; but within one format, defense + offense share no unit — defense locks & each unit attacks once). 3. **Defense first** by Hold%. 4. **Reserve the 4 pure-attack GLs** (JMK, JML, SEE, SLKR) for offense before defense claims units, or defense strands their support (e.g. JML's Cal/GMY). 5. GL Leia → offense in 5v5 (she's the #1 attacker). 6. Fleets are single-use too; the 6 fleets share no ship.

## Full workflow (re-run each GAC season / when meta shifts)
Browser steps can't be pure scripts (Cloudflare + authenticated sessions) — the JS snippets are in
`scripts/browser_recipes.md`. Run them via the in-session MCP browser.

1. **Refresh roster** → `data/roster/` (browser_recipes.md §1). Update `ROSTER_FILE` in compute_teams.py to the new filename.
2. **Read live board counts** from HotUtils GAC Planning (browser_recipes.md §2). Update `BOARD` if changed.
3. **Scrape swgoh.gg meta** → `data/meta/` (browser_recipes.md §3). 4 views: 5v5 def (JSON), 5v5 off, latest-3v3 def, latest-3v3 off (txt). Note the current season ids (even=5v5, odd=3v3).
4. **Compute:** `python3 scripts/compute_teams.py` → `data/gac_result.json`.
5. **Generate:** `python3 scripts/generate_hotutils.py` → `output/` (6 category JSONs + upload_payload.json + playbook.html). Review the FLEETS config in that script (owned ships, no-repeat).
6. **Upload to HotUtils** (browser_recipes.md §4): capture session, delete old GAC squads, base64 the upload_payload.json, create all via `squads/upsert`. Verify categories.
7. **Playbook:** open `output/playbook.html` for the human-readable plan (hold/win %, reasoning, gaps, fleets).

## HotUtils categories (the "4 groups" the player wants)
Squads: `GAC 5v5 - Defense` · `GAC 5v5 - Offense` · `GAC 3v3 - Defense` · `GAC 3v3 - Offense`.
Fleets: `GAC Fleet - Defense` · `GAC Fleet - Offense` (full ~8-ship lineups).
HotUtils accepts arbitrary category strings and shows them as filter groups.

## Mod optimization (move → slice → calibrate → level)
Full API payloads, material recipes, and every gotcha are in `memory/notes.md`.

> **After every farming trip, run one command:** `HU_SID=<live> ./scripts/mods_session.sh`.
> It refreshes the ladder, pulls live mods, spends whatever salvage/attenuators have arrived
> (in priority order), re-scores, and prints the next shopping list. Idempotent and self-limiting —
> on an empty stock it costs two API reads and changes nothing. Add `--dry` to plan only.

**One ladder, three scripts.** `invest_plan.py` owns the priority order (Arena → Grand Arena →
Territory Battles → Territory War → fleets) and writes it to `output/invest_plan.json` as
`mod_priority`. `execute_upgrades.py`, `calibrate.py` and `slice_plan.py` ALL key off that list —
never rebuild importance from `gac_result.json`, which cannot see TW units or the arena datacron five.
⚠️ The TB rung is currently EMPTY: it needs `data/rote/operations_<phase>.json` scraped on device.

Pipeline detail:
1. **Placement** — drive the **Grandivory optimizer** inside HotUtils (`/mods/optimizer`) with the GAC priority
   order; "Optimize my mods!" (the `!` button, not the nav tab) → "Move mods in-game". If it errors
   `Row not found`, the HotUtils data is stale → "Fetch my data" → re-optimize → retry (partial-applies persist).
   **Re-run rarely:** ~1,473 moves / ~7.4M credits for a measured ≤0.12% — slicing improves a mod IN PLACE,
   so an upgrade session implies no placement change at all.
2. **Rank** what to upgrade: `python3 scripts/slice_plan.py` → `output/slice_queue.json` (ladder order,
   then speed secondary). `scripts/execute_upgrades.py --needs N` = the farming shopping list.
   `scripts/mod_targets.py` + `mod_analysis.py` = grounded best-mod targets vs current (from swgoh.gg mod-meta).
3. **Execute via HotUtils API** (mods full data at `account/data/all` → `d.data.mods.mods`):
   - **Slice/promote:** `mods/tier {modIds,getAllData:true}` — one tier/call. ⚠️ **`simulation:true` is NOT a dry run — it really slices.**
   - **Level to 15:** `mods/level {modIds,requestType:3}` (credits only). **Slicing requires level 15 first.**
   - **Calibrate → speed:** `mods/reroll {modId,stat:5}` → `mods/acceptreroll {keepMod}`.
4. **Binding materials** (the real limits, from live diffs): a **6-dot step is a BUNDLE** —
   `T06_01×10 + T06_02×20 + T06_03×10 + T05_05×10 + T05_06×10` — so **T06_02 gates all 6-dot slicing**;
   promote 5A→6E → **T05_06 ×76**; 5-dot→5A → **~22 of the tier being left**;
   **calibration → Micro Attenuators = `summary.currency` id 41** (farm: Smuggler's Run 2 with Jabba, best).
   When a material runs out the API returns `responseCode 2 / GOHServiceCall Error [40]` — and it does NOT
   name the material, so diff a fresh pull rather than trusting a label. Latest state: `output/mod_upgrade_results.md`.
5. **Calibration targets the UNLUCKY mod** — `deficit = rolls×4.5 − spd`, never `rolls×6 − spd`. A reroll
   re-samples, so rerolling an above-average mod loses on average (measured 0 hits in 18 attempts).

## Conventions
- Data-driven only — NO hardcoded teams in compute (teams come from the meta files ∩ roster).
- Fleet reinforcements are standard faction-meta (swgoh.gg only publishes capital + starting-3).
- Base IDs: roster `b` field == swgoh.gg `data-unit-def-tooltip-app` == HotUtils `characterId` (all identical).
- Do NOT commit secrets. HotUtils session ids are ephemeral — never hardcode them in committed files.
