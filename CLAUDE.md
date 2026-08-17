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
- **Astra** · ally **145357294** · GAC **KYBER 4** · 14.47M GP · skill rating **3,128** (Kyber-4 band is
  2970-3130, so he sits one point off promotion). Read off the in-game Championships screen 2026-08-17;
  the HotUtils `divisionId: 15` maps to Kyber 4, NOT Division 3 as first inferred, and division is set by
  **skill rating, not GP**. ⚠ Two earlier claims were wrong: the GP-based "Division 1", and "Division 3".
  ⇒ **Scrape swgoh.gg with `league=kyber` (all divisions), not `league=kyber-d1`** — they are different
  buckets and disagree materially (Chimaera 15.9% vs 0.8% hold).
- **9 Galactic Legends:** JMK, JML, SEE, SLKR, GL Leia, Lord Vader, GL Rey, Jabba, GL Ahsoka.
- **Known gaps, ranked by banners:** **Profundity** (24.8% hold AND 98.4% win — best in the game on
  both sides) · **Third Sister** (turns an already-owned **R7** Inquisitor bench into both a 26% wall
  and an 85% attacker) · **4-LOM + Zuckuss at G11/R0** (the only sub-G13 units gating anything: they
  unlock the Kyber-D1 #1 offense squad). *GL Hondo is NOT a gap.*
- ⭐ **BOTH top gaps are unlocked and waiting — verified against the roster 2026-08-17:**
  - **Profundity — every gate MET.** All 7 ships at 7★ (Bistan's + Cassian's U-wing, Biggs' + Wedge's
    X-wing, Rebel Y-wing, Ghost, Outrider) and all 7 character relics clear, **three of them exactly at
    threshold**: Admiral Raddus R9, Cassian Andor R8, Dash Rendar R7 (then Mon Mothma/Bistan/Jyn R7,
    Hera R6). Stardust Transmission runs ~monthly, last ran 2026-07-31 ⇒ **next ~late Aug 2026. Play it.**
  - **Third Sister has no event** — Reva shards drop from the **RotE Phase 3 Neutral special mission**,
    1 per guild victory, max 50. The gate is a **Relic-7 Grand Inquisitor**, and Astra's is exactly R7.
    ⇒ It is farmable now, but only by running that mission every RotE. Do not auto-battle it.
- ⚠ **The real structural gap is MODS, not gear or relics.** Head-to-head with the live S82 opponent:
  145 six-dot mods vs 720, total mod speed 16,682 vs 25,873, 10 mods at 25+ speed vs 47 — while Astra's
  gearScore is *higher*. Relic spend is equal in total (2,213 vs 2,189 levels) but wrong in shape:
  27 units at R9+ vs their 60, and 156 parked at R7. Stop adding R7s; convert R7→R9 on the offense plan.
- ⭐ **That R7→R9 conversion has exactly one supply line: RAID CADENCE.** Mk III raid tokens are the only
  reliable faucet for R8/R9 mats, and raids are gated by **600 tickets/member/day = 1 ticket per energy
  spent on anything but Conquest**. Free daily energy covers 600 with zero crystals, so a missed dump is
  a missed relic. Never trade tickets for a higher Guild Activity tier. Full economy map + the currency
  routing table: `memory/notes.md` § 2026-08-17 session 3.

## The board is TWO GATED LANES, not a list of slots (verified 2026-08-16)
Read live off HotUtils `gac/get` and confirmed against six of Astra's own matches. `scripts/gac_score.py`
holds it; don't re-derive it.

```
LANE TOP     front_top    (4 squads, 5v5 / 5, 3v3)  ──gates──▶  FLEET territory (3 fleets)
LANE BOTTOM  front_bottom (4 squads, 5v5 / 5, 3v3)  ──gates──▶  back_bottom (3 squads / 5)
```
Both fronts are open the second the attack phase starts. **A back territory is invisible and
unattackable until every squad in its own front is dead.** Zone ids carry it: `phase01` = front,
`phase02` = back, matched by `location`.

**Banners (first-party, `gac_score.BANNER`):** Victory 15 · First Attempt 30 (2nd 10, 3rd+ 0) ·
Surviving/Full-Health/Full-Protection/Defeated-Enemy 1 each · **Unused Slot 4** · First Attack 10 once.
Max per battle = `45 + 5·slots − units_deployed` → 5v5 65–69, 3v3 57–59, fleet 73–79.
**Territory conquest = 120 + 30/squad (5v5), +28 (3v3), +33/fleet — and it is 47% of the whole score.**
Kyber ceilings: **5v5 1915 · 3v3 2131** (HotUtils printed 2131 independently — the model is validated).
⇒ One hold in a front zone denies **657–696**; the same hold in the back denies **210–219**.
⇒ **The defender earns zero banners.** Defense is pure denial. Never add a defender-side term.

## Rules (encoded in the scripts — don't hand-wave them)
1. Every unit **owned + G13+**.
2. **No unit repeats within a format** (3v3 and 5v5 are separate seasons, so a unit CAN appear in both;
   within one format, defense + offense share no unit — defense locks & each unit attacks once).
3. ⭐ **OFFENSE FIRST, to a proven full clear. Defense from the remainder.** (This replaces "defense
   first by Hold%", which was the root cause of the losing streak: Astra converts ~37% of available
   banners and a mean of 493/round sat locked behind a front zone he left at 3/4.) **Conquer a lane or
   do not enter it** — a front at 3/4 pays the same territory banners as 0/4: zero.
4. **Price everything in BANNERS, never in Hold%/Win%.** Defense = `max_battle − avg banners conceded`
   plus its share of gate denial; offense = avg banners earned. swgoh.gg publishes both as the
   `banners` column and the repo already scrapes it.
5. **Fill every slot.** An unset defensive slot hands the attacker the *maximum* (69 in 5v5) for free.
   Undersized DEFENSE is strictly worse than a full squad ("Defeated Enemies … includes unset").
   Undersizing on OFFENSE is worth only +1/slot — do it for unit economy, not for the bonus.
6. **Two attempts per target, then walk away.** Attempt 2 is −20 banners, attempt 3 is −30, and the
   units are spent win or lose. Astra threw seven squads at one wall in S82 R2.
7. ⭐ **EVERY GL THAT HAS AN OFFENSE ROLE ATTACKS. A GL WALLS ONLY IF IT HAS NONE.**
   Today that means **eight GLs attack and only GL Rey walls** — she is the one with no offense row in
   any meta file, in either format. Measured, not asserted: `scripts/gac_doctrine.py` simulates whole
   rounds against real opponent boards under six doctrines, and this one wins by 65-87 banners at every
   value of the free parameter. A wall earns nothing and denies only against an opponent who would
   otherwise have taken those banners — Astra's board was cleared 14/14, so it denied zero. An attacker
   earns its banners *and* can be the squad that conquers a territory, worth 210-240 more plus the lane
   behind it. Re-run `gac_doctrine.py` when the meta shifts; don't reason about it from Hold%.
8. **Reserve support units the attack bank cannot replace** (`RESERVE_OFF_UNITS`) — Mace Windu is the
   last available fifth for JMK's 90% attacker (General Kenobi is committed to GL Rey's wall). Without
   the reservation JMK falls off the offense board and the round is 67 net banners worse.
   ⚠ **Astra has NO good answer to The Stranger.** Best well-sampled is SLKR at 76% (n=2,769); the
   often-quoted "JMK 79%" is the *General Kenobi* variant on n=403, and the Mace variant is 43%.
9. Fleets are single-use too; the 6 fleets share no ship. The fleet territory is a BACK zone.

## Pipeline order (run them in this order — each reads the previous one's output)
```
python3 scripts/build_board.py       # select, priced in banners, relic-corrected  -> data/board_result.json
python3 scripts/gac_place.py         # assign squads to zones                      -> output/gac_placement.json
python3 scripts/datacron_assign.py   # match owned crons to walls                  -> output/datacron_plan.json
python3 scripts/generate_upload.py   # payload + playbook, names carry the ZONE    -> output/
HU_SID=<live> python3 scripts/upload_hotutils.py --sync
HU_SID=<live> python3 scripts/push_ingame_presets.py --push
# per round, once matchmaking lands:
python3 scripts/gac_attack.py        # the attack ROUTE vs the live opponent board
# when the meta shifts, re-settle the offense/defense split by measurement:
python3 scripts/gac_doctrine.py      # simulates whole rounds under six doctrines
```
`build_board.py --sweep` re-calibrates `GATE_WEIGHT` by measurement rather than feel.

## Full workflow (re-run each GAC season / when meta shifts)
Browser steps can't be pure scripts (Cloudflare + authenticated sessions) — the JS snippets are in
`scripts/browser_recipes.md`. Run them via the in-session MCP browser.

1. **Refresh roster** → `data/roster/` (browser_recipes.md §1). Update `ROSTER_FILE` in compute_teams.py to the new filename.
2. **Read live board counts** from HotUtils GAC Planning (browser_recipes.md §2). Update `BOARD` if changed.
3. **Scrape swgoh.gg meta** → `data/meta/`. 4 views: 5v5 def (JSON), 5v5 off, latest-3v3 def, latest-3v3 off (txt). Seasons: even = 5v5, odd = 3v3.
   - **Transport: the in-session MCP browser, per browser_recipes.md §3.** This is the primary path, not a fallback. `scripts/fetch_meta.py` cannot do it: Cloudflare challenges every parameterised `/gac/squads/` URL for a Playwright-launched browser, and that was verified on 2026-08-12 across bundled Chromium and real Chrome, headed and headless, fresh and persistent profiles. The base page always loads; the moment any query parameter is added it is challenged. The MCP browser clears the same challenge in about 15 seconds.
   - **Conversion: `scripts/fetch_meta.py` is still what you use.** `rows_to_json()` turns the §3 extractor's `rate%|seen|banners|CSVunits` lines into the JSON envelope, and `EXTRACT_JS` holds the extractor itself so there is one copy of it. Both are tested against the shipped `meta_5v5_defense_s80.json`.
   - **Season ids need the full prefix**: `CHAMPIONSHIPS_GRAND_ARENA_GA2_EVENT_SEASON_<n>`. The bare `SEASON_80` returns a 404 that arrives behind the Cloudflare interstitial, so it reads as a block when it is not one.
   - `fetch_meta.py`'s `main()` remains in the tree for the day the challenge stops firing. It fails loudly with the page title when it cannot get a table, which distinguishes a wrong season from a live challenge.
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
   **calibration → Micro Attenuators = `summary.currency` id 41** (farm: Smuggler's Run 2 with Jabba, best;
   also **GET3 5-for-125** and **Episode currency 16-for-4,000**, and Mod Battles **chapter 2** — which is
   the old "Map 9" after the 2026-04-27 update cut Mod Battles to 2 tiers and deleted Mod Challenges).
   When a material runs out the API returns `responseCode 2 / GOHServiceCall Error [40]` — and it does NOT
   name the material, so diff a fresh pull rather than trusting a label. Latest state: `output/mod_upgrade_results.md`.
5. **Calibration targets the UNLUCKY mod** — `deficit = rolls×4.5 − spd`, never `rolls×6 − spd`. A reroll
   re-samples, so rerolling an above-average mod loses on average (measured 0 hits in 18 attempts).

## Conventions
- Data-driven only — NO hardcoded teams in compute (teams come from the meta files ∩ roster).
- Fleet reinforcements are standard faction-meta (swgoh.gg only publishes capital + starting-3).
- Base IDs: roster `b` field == swgoh.gg `data-unit-def-tooltip-app` == HotUtils `characterId` (all identical).
- Do NOT commit secrets. HotUtils session ids are ephemeral — never hardcode them in committed files.
- ⭐ **Screenshots are the session's real budget, and the limit is BYTES not tokens.** The API refuses
  any request over 30MB; a raw `d.sh` screencap is ~2.7MB PNG and images were measured at ~99% of the
  payload in 66 dead sessions (78 crashes, every day 2026-08-02→08-17). Auto-compact can never rescue
  it — 60 images is ~90k tokens but ~29MB, so the byte cap lands while the window is barely a third
  full, and `/compact` is itself an oversize call. `scripts/hooks/shrink_read_images.py` (PreToolUse
  on Read, wired in `.claude/settings.json`) transcodes anything over 150KB to 1100px/q55 JPEG —
  measured 1.9MB→71KB with in-game text still readable — and hard-denies once ~20MB is banked.
  Originals on disk are untouched, so the vision/OCR scripts still get native resolution.
  If it ever does die: `/clear`, then say "continue" — SessionStart replays `memory/session_state.md`.
