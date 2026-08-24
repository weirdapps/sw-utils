# SWGOH — Grand Arena team builder (Astra / Kyber 3 → Kyber 2)

Reusable pipeline that builds **grounded** GAC defense + offense squads and fleets from live
swgoh.gg meta + the player's live roster, and pushes them into **HotUtils** as organized squad groups.

"Grounded" is the whole point: every defense pick is a top-**Hold%** team on swgoh.gg and every
offense pick a top-**Win%** team — so when the player sorts swgoh.gg the same way, they see the same teams.

> **Read `memory/notes.md` FIRST.** It's the durable knowledge base — live board counts, GL allocation,
> every HotUtils API recipe (squads, in-game presets, mods slice/calibrate/level) and the gotchas learned
> the hard way. `scripts/browser_recipes.md` has the copy-paste browser JS. This CLAUDE.md is the map;
> notes.md is the territory. Session ids rotate — recapture each session (browser_recipes.md §4).

## What this repo can do (three pipelines)
1. **Build GAC teams** (grounded squads + fleets → HotUtils groups + in-game presets) — see workflow below.
2. **Optimize mods** for those teams (move → slice → calibrate → level) — see "Mod optimization" below.
3. **Plan RotE + Territory War** — the whole 6-phase RotE mission map is data, and the TW wall is
   computed to ~55 squads. See "Territory War" and "Rise of the Empire" below.

## ⭐ Standing rule: GAC IS ALWAYS TOP PRIORITY (owner, 2026-08-18)
When any script ranks what to invest in, **Grand Arena outranks everything** — Arena, TB, TW, fleets.
Encoded as tiers 1-4 in `invest_plan.py`; Arena dropped to 5-7. The superseded Arena-first argument is
kept in that file on purpose, so it is not re-derived. Note it costs the arena climb nothing here: the
deployed arena wall *is* GAC 5v5 defense, so best-tier-wins already had those units at tier 1.

## ⚠ The roster has NO per-unit `gp` any more
`swgoh_data.map_roster()` (comlink) replaced the HotUtils pull on 2026-08-18. Comlink does not return
per-unit GP — nor omicrons (`o`) or zetas (`z`). **Never read `unit["gp"]`**; call
`swgoh_data.unit_power()`, which returns real `gp` when present and a documented gear/relic/star proxy
otherwise. `tw_wall.py` died on `KeyError('gp')` before this was centralised.
Roster path: always `swgoh_data.latest_roster_file()` — never a hardcoded date.

## Player
- **Astra** · ally **145357294** · GAC **KYBER 3** · **14.57M GP** · skill rating **3,165**
  (Kyber-3 band **3130-3310**). Read off the in-game Championships screen **2026-08-24**: he was 3,128
  in the Kyber-4 band (2970-3130) on 08-17, crossed 3,130 and **was PROMOTED**. The bands are contiguous.
  Division is set by **skill rating, not GP**. ⚠ Three earlier claims were wrong: the GP-based
  "Division 1", "Division 3", and "Kyber 4" (true on 08-17, stale since).
  ⚠ **The two division fields disagree** — `playerRating.playerRankStatus.divisionId` = 15 while
  `seasonStatus[S82].division` = 10. Since the in-game screen reads Kyber 3 with divisionId still 15,
  **divisionId 15 == Kyber 3**. Read the Championships screen; do not infer the mapping from HotUtils.

## ⭐⭐ THE KYBER LADDER, AND WHAT ACTUALLY MOVES YOU UP (swgoh.wiki, 2026-08-24)

| Division | Kyber skill rating | Astra |
|---|---|---|
| **Kyber 1** | **3610+** | **445 to go** |
| Kyber 2 | 3310+ | 145 to go |
| Kyber 3 | 3130+ | ← **3,165, here** |
| Kyber 4 | 2970+ | |
| Kyber 5 | < 2970 | |

⭐⭐ **SKILL RATING MOVES ON WIN/LOSS ONLY. THE BANNER MARGIN DOES NOT AFFECT IT.**
Verbatim: *"Skill Rating will be adjusted at the end of each round based on whether it was a win
or a loss."* Banners decide **who wins the round**; they do not size the rating change. A 1-banner
win and a 900-banner win are worth exactly the same rating. It is a Bayesian/Elo-like system on the
two players' ratings, so beating a higher-rated opponent pays more; community tracking puts a
typical swing in the **mid-30s per win**. ⇒ 445 points is roughly **13 net wins**.

⇒ **This does NOT retire the banner work — it reframes it.** Banners are the MECHANISM for winning
the round, and this account converts only ~37% of available banners with ~493/round stranded behind
a front zone left at n-1. Fixing that is still the whole game. What changes:
- **Never skip a weekly event.** Verbatim: *"Every weekly event you miss will reduce your Skill
  Rating as if you had lost two matches during that week."* That is the cheapest rating in the game.
- **Do not grind banners after the round is mathematically decided** — won or lost, the rating is
  already set. Extra banners then buy only reward-crate thresholds, never rating.
- **Roster upgrades do not bump rating directly.** They raise P(win), which pays out over the next
  few rounds. Do not expect Profundity or a mod pass to move the number the same week.
- Division changes happen **after each round**; League changes only at **season end**. Kyber is the
  top league, so Kyber 1 is the ceiling.

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
    Hera R6). ⭐ **NEXT STARDUST TRANSMISSION IS 2026-08-31** (swgohevents.com/event/profundity).
    Gates re-verified against the 08-24 roster with the CORRECT base ids — the ones implied by the
    old note are guesses that do not resolve. Ships, all 7★: **UWINGSCARIF · UWINGROGUEONE ·
    XWINGRED3 · XWINGRED2 · YWINGREBEL · GHOST · OUTRIDER**; Hera is **HERASYNDULLAS3** (R6, gate R6).
    ⛔ **PLAY IT — it cannot be automated**, and it is the biggest free GAC upgrade available here.
  - **Third Sister has no event** — Reva shards drop from the RotE **Phase 3 · TATOOINE (mixed)**
    special, `special_reva` in `data/rote/missions_3.json`, 1 per guild victory, guild max 50.
    ⚠️ **THE GATE IS NOT "GRAND INQUISITOR R7". Zone 3 applies a BLANKET rule:** *"Requires all
    units to be at 7 stars and Relic Level 7 for all missions except Deployment"*
    (swgoh.wiki/Rise_of_the_Empire). **All five units you bring must be 7★ R7+.**
    ⭐ **Checked against the 08-24 roster — Astra clears it with EXACTLY five:**
    **Grand Inquisitor (lead) · Seventh Sister · Fifth Brother · Marrok · Inquisitor Barriss**
    (all 7★ R7). **Ninth Sister is R6 and Eighth Brother is R5 — both FAIL the gate.**
    ⇒ The comp published in guides (GI / 7th / 9th / 5th / 8th) is **UNPLAYABLE here**: it needs
    both failing units. Any guide tactic that leans on Ninth Sister's team-wide crit avoidance
    does not apply. **Ninth Sister R6→R7 is ONE relic level and restores the researched comp.**
    ⇒ Grand Inquisitor cannot be swapped out of the leader slot.
    ⇒ **One attempt, no retries** — *"Special Missions may only be completed once."* Do not
    auto-battle it.
    ⚠ **Do not confuse it with the PHASE 4 · Medical Station special**, which *requires* an owned
    **Third Sister at R8** and pays **1,000 Mk III tokens**. `rote_missions.py --gaps` lists
    THIRDSISTER against "P4 Medical Station/special" for exactly that reason, and reading that row
    as "the Reva farm is in phase 4" is wrong — one mission FARMS her, the other SPENDS her.
    The phase-4 row is a second reason to unlock her: Mk III is the R8/R9 relic supply line.
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
   ⭐ **RETRACTED 2026-08-24: "Astra has NO good answer to The Stranger" IS FALSE.**
   The answer is **Satele Shan (L) · Bastila Shan · Jedi Knight Revan · Jolee Bindo · Juhani**,
   **79% on n=6,655**, off `/gac/counters/STRANGER/` (Season 82, Kyber-scoped, 29.9K battles).
   That beats the SLKR 76% (n=2,769) this file used to name, on more than twice the sample.
   **Astra owns all five at G13** (Satele/Bastila/JKR/Jolee R8, Juhani R7).
   Verified twice: a research agent reported it and an independent browser pull of the same page
   reproduced every quoted row (625/89%, 1414/88%, 318/85%, 305/83%, and the 6,655/79% itself).
   ⚠ **That squad is currently sitting on 5v5 DEFENSE at 16.2% hold**, where it earns zero and
   cannot attack. Moving it to offense is a real decision, not a formality: it is the account's
   best Stranger answer, and The Stranger is the **#2 hardest defence in the game** (31% hold,
   68% attacker win, n=29.9K). Only Rotta is harder (64% attacker win) and Astra answers Rotta
   already with Lord Vader 96% (n=2,096) and SLKR 89% (n=1,303).
   ⚠ **Time-boxed:** the 79% is measured with Set 31 live, whose L6 is Old Republic, and
   **Set 31 expires 2026-09-03**. Expect the rate to soften after that.
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

## Territory War — 55 defensive squads, not 15
TW is its own mode: it shares no units with GAC, defense banks a **flat +30 per squad** the moment it is
set (a fleet +34), and the map holds 390 slots against a **guild-wide, first-come** pool.
```
python3 scripts/build_board.py     # 23 graded TW walls (the ILP ceiling — 24 is infeasible) + 8 offense
python3 scripts/tw_wall.py         # extends to 55 via leader-tier-list, unranked-leader, then filler
                                   # -> output/tw_wall.json + output/tw_placement_sheet.txt
```
- **55 squads × 30 + 6 fleets × 34 = 1,854 guaranteed banners** (was 1,494). 3 of 317 G13 chars idle.
- **Place from `tw_placement_sheet.txt`, in order, front-most territory first.** It merges the graded
  bank and the wall into ONE ranking — sorting them separately is what put a 4% wall in front of a 42%
  one in the 2026-08-11 war. Rows flagged `BACK` are no-synergy filler and must never take a front slot.
- Offense is deliberately only 8 coherent GL-led squads (owner's max-defense call; conquest forfeited).
- ⚠️ **DO NOT OVERSELL THE WALL. Corrected 2026-08-24 after I overstated it.** Going 15 → 55 squads
  adds **1,200 banners** (40 × 30) from ONE player. The guild's last three wars were
  L 15,287-17,574 · L 16,020-18,625 · W 16,192-15,053, so the losing margins were **2,287 and
  2,605** — **more than 1,200. A full wall does NOT flip either loss on its own.**
- ⭐ **And the wall is not where the deficit is.** Their own score is flat at 15.3-16.2k across all
  three wars, so the variable is the opponent, not them. Placement banners are near-symmetric when
  both guilds fill; the differentiator is **CONQUEST**, at **+450 per territory and +900 for a back
  row**, plus +10 per defensive slot in it. Two back-row conquers ≈ the whole losing margin.
  ⇒ Fill every slot anyway — an empty one costs 30 directly **and gifts the enemy +10 on their
  conquer bonus — but the war is lost on offense, and this repo forfeited offense by choice.**
  Revisit the 8-squad offense cap with the owner before blaming the wall.

## Rise of the Empire (RotE) — the map is written down, stop improvising
RotE encounters are **static**, so the whole 6-phase map lives in `data/rote/`.
```
python3 scripts/rote_missions.py --write   # regenerate data/rote/missions_1..6.json from the wiki table
python3 scripts/rote_missions.py --gaps    # which required units miss their gate, CHEAPEST FIRST
python3 scripts/rote_ops.py --phase N      # the squad to bring to every mission in phase N
python3 scripts/rote_squads.py --phase N   # the RESEARCHED per-node teams + play order
HU_SID=<live> python3 scripts/upload_hotutils.py --create --payload output/rote_squads.json
```
⛔ **`--create`, never `--sync`, for a PARTIAL payload.** `--sync` deletes every definition not in
the payload, so `--sync --payload rote_squads.json` wipes all ~114 GAC/TW squads and leaves 17.
`--sync` is only for `output/upload_payload.json`, which is the whole board.
- ⭐ **`rote_missions.TACTICS` is the researched per-node team list; `rote_squads.py` pushes it as
  a `TB RotE - P<n>` squad tab so the phase is played from SELECT SQUAD, never from auto-fill.**
  Play order is **specials → unit-gated → faction-gated → free**: auto-fill will spend a gated unit
  on a row that did not need it, and that kills the gated row for the phase.
  Three tests keep the list honest — a squad must be **fillable** (owned, and every FREE slot at or
  above the phase relic floor; a shortfall on a REQUIRED unit is a roster gap, not a bug, and is
  `--gaps`' job), **no unit may be double-booked inside a phase**, and a comp the roster cannot
  field yet must be flagged `aspirational` with a note saying so. Those tests immediately caught
  two guide lineups that were unplayable here (Vandor Chewbacca R5 and Dengar R6 against an R7
  floor) and one squad this repo double-booked.
- Source is swgoh.wiki's Zone Information table; re-fetch it before editing a row and bump `SOURCE_VERIFIED`.
- ⭐ **HOW PLANETS UNLOCK — ONE star on the predecessor, effective the NEXT phase.** Phases are 24h
  tiers, so mid-phase progress never opens anything mid-phase. Two corollaries that drive planning:
  a territory that earned **no** star stays open and its missions can be run again in later phases;
  a territory that **did** star **locks at the end of its phase**, so you can never come back for
  its 2nd and 3rd stars. Bonus zones (Zeffo, Mandalore) are a separate gate — N clears of a special.
  ⛔ This repo invented a "3 stars" rule from two board readings on 2026-08-20 and was wrong twice
  before the owner pointed out it is stated plainly in every RotE guide. **Look the mechanic up.**
- ⭐⭐ **OPERATIONS ARE ~90% OF A STAR, AND THAT IS THE WHOLE GUILD ARGUMENT FOR R7→R9.**
  From the wiki Zone Information tables: a **Phase 6 operation pays 86,486,400**, so six of them
  = **518,918,400** against Scarif's 1★ threshold of **555,710,999** — **93% of the star from
  operations alone** (≈89% on Death Star and Hoth). Phase 5 ops are 33,264,000 each, ≈58% of a 1★.
  ⇒ **One R9 unit filling one Phase-6 op slot returns ~86.5M TP. Deploying that same unit pays
  its GP, ~1.5M. That is roughly 57x.** Nothing else in the mode is close.
  ⚠️ **Phase 5/6 op slots gate at 7★ R9**, and Astra has 161 at exactly R7 against 27 at R9+, so
  the roster is shaped precisely wrong for where the points are. This is the same R7→R9 conversion
  GAC wants, paying twice.
  ⚠️ The old "13.2M per operation in phase 5" figure was wrong: **13.2M is PHASE 3.**
  **Guild sizing:** at 519M deployable the ceiling is ~28-33 stars and they finished at **20**, so
  8-13 stars are on the table — and it is **unfilled operations and uncleared combat, not GP**.
  ⭐ **Cheapest star on the map: Jedi Knight Cal Kestis collapses Zeffo's required deployment from
  102,375,000 to 3,229,167, a 32x cut.** Astra owns him (he is on the GL Rey wall).
- ⚠️ **"A deployed unit becomes ineligible" is too strong.** The real rules: a unit may be deployed
  to ONE territory and used in one platoon/special/combat **in that territory** per phase; once
  deployed there it can only be used for that territory; and entering a mission without deploying
  auto-deploys it there. ⇒ Mass-deploying to one planet kills those units for **other planets'**
  ops and combat, not for the one they are on. Correct order: **Special → Operations → Combat →
  Deploy last.** Completing a platoon also raises that Platoon Mission's level (steps at 2/4/6),
  so running combat before ops are full makes the combat strictly harder.
- **Operations still need an on-device scrape** (`data/rote/operations_<phase>.json`). Without one
  `rote_ops` plans MISSIONS ONLY and reserves nothing for platoons — it says so loudly. Operations
  before deploy, always: a deployed unit is permanently ineligible for a platoon slot.
- ⭐ **Phases 5-6 are only 3/12 fillable, and the cause is relic depth**: 157 characters sit at exactly
  R7 while those phases gate at R9, where just 27 qualify. `--gaps` names the six units that are a
  SINGLE relic level from opening a mission (Bo-Katan Mand'alor alone opens a 74M-TP row).
- Squads are filled by **faction coherence**, not raw power — a leader ability only helps its own
  faction, and this account measured a filler squad going 0-for-5 at 193K power.
- Fleet missions are recorded but NOT solved: ship "power" here is a stars-only proxy, so every 7* ship
  ties. Each fleet row names the required ship and the in-game preset that already contains it.

## Full workflow (re-run each GAC season / when meta shifts)
Browser steps can't be pure scripts (Cloudflare + authenticated sessions) — the JS snippets are in
`scripts/browser_recipes.md`. Run them via the in-session MCP browser.

1. **Refresh roster** → `data/roster/` (browser_recipes.md §1). Update `ROSTER_FILE` in compute_teams.py to the new filename.
2. **Read live board counts** from HotUtils GAC Planning (browser_recipes.md §2). Update `BOARD` if changed.
3. **Scrape swgoh.gg meta** → `data/meta/`. 4 views: 5v5 def (JSON), 5v5 off, latest-3v3 def, latest-3v3 off (txt). Seasons: even = 5v5, odd = 3v3.
   - ⛔ **`/gac/squads/` IS ALL-LEAGUE AND THE `league=` PARAM IS IGNORED.** Tested 2026-08-24:
     `?league=kyber` returns byte-identical rows to no param at all. This file used to say
     "scrape with `league=kyber`, not `league=kyber-d1`" — **neither does anything on this page.**
     So every rate in `data/meta/*` is a league-MIXED number, and Kyber defences hold harder than
     it shows. `league_adjust.py` corrects for this per leader, but **only on DEFENCE** (tables
     exist for `('5v5','def')` and `('3v3','def')` only) — **offence is uncorrected**, and offence
     is where the banners are.
   - The pages that ARE genuinely Kyber-scoped: **`/gac/counters/<LEADER>/`** and the **tier
     lists**. Prefer them whenever a decision turns on a rate.
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

**One ladder, three scripts.** `invest_plan.py` owns the priority order (**Grand Arena → Arena →
Territory Battles → Territory War → fleets** — GAC first per the standing rule above; this was
Arena-first until 2026-08-18) and writes it to `output/invest_plan.json` as `mod_priority`. `execute_upgrades.py`, `calibrate.py` and `slice_plan.py` ALL key off that list —
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
   promote 5A→6E → **T05_06 ≥92** (refusal bound: the server rejected one with 91 in hand on
   2026-08-20; the old "76" was wrong); 5-dot slice → **the cost VARIES PER MOD, it is not a
   per-tier constant** — two isolated t1 steps the same afternoon cost 15 then 10 salvage
   (27,000 then 18,000 credits, both scaling 1.5× together). `STEP5_SALVAGE` therefore holds
   observed MINIMA and lets the server arbitrate: a refusal costs one API call and NO
   materials, while over-charging silently drops upgrades you could afford — a flat "~22"
   average was hiding affordable t1/t2 steps *and* proposing t4 steps the server refused;
   **calibration → Micro Attenuators = `summary.currency` id 41** (farm: Smuggler's Run 2 with Jabba, best;
   also **GET3 5-for-125** and **Episode currency 16-for-4,000**, and Mod Battles **chapter 2** — which is
   the old "Map 9" after the 2026-04-27 update cut Mod Battles to 2 tiers and deleted Mod Challenges).
   When a material runs out the API returns `responseCode 2 / GOHServiceCall Error [40]` — and it does NOT
   name the material, so diff a fresh pull rather than trusting a label. Latest state: `output/mod_upgrade_results.md`.
5. **Calibration targets the UNLUCKY mod** — `deficit = rolls×4.5 − spd`, never `rolls×6 − spd`. A reroll
   re-samples, so rerolling an above-average mod loses on average (measured 0 hits in 18 attempts).

## Pricing actions, and checking the repo's own facts (added 2026-08-17)
Two gaps closed. Before this, GAC was the only mode priced in a real unit (banners), nothing
priced energy at all, and no written fact was ever re-checked against the roster.

```
python3 scripts/action_value.py            # what is actually scarce, and what buys it
python3 scripts/verify_facts.py            # does the repo's prose still match the roster?
python3 scripts/verify_facts.py --unit IMAGUNDI   # ground truth for one unit, in one second
```
- **`data/economy.json` holds the researched constants, each with a source URL.** Recipes and
  store prices come from swgoh.wiki, not from memory or from reading the game UI. Re-verify against
  the cited page before editing, and update `_verified_utc`.
- **A relic upgrade is a FIXED BASKET, so throughput is the MINIMUM over (stock ÷ need), never the
  average.** A surplus of nine materials buys nothing when the tenth is empty. That one fact gives
  shadow prices for free: farming a material you already hold in surplus is waste, however good the
  node looks.
- ⭐ **Two hard gates that raid tickets cannot buy, at any price:**
  **SIGNAL DATA** is cantina-energy-only (no store sells it for a token) and is the largest line in
  the basket — **100 Flawed per R7→R9**. **DROID BRAIN** has no repeatable token route at all.
  ⇒ Cantina energy is NOT interchangeable with the other pools despite paying the same 1 ticket,
  and Assault Battles / Endor Escalation / Knightfall / Coven of Shadows are **mandatory**, not
  optional, for anything past R8.
- **Aeromagnifier is the only thing forcing Mk III raid tokens** (35,300 Mk III would buy a whole
  R7→R9 basket, but gyrda/impulse/zinbiddle all have cheaper non-Mk-III routes). So spend Mk III on
  aeromagnifiers and cover the rest from scrap points and Conquest credits. Chromium Transistor and
  Aurodium Heatsink are the equivalent forced draw on Mk II.
- **Never compare two currencies by their raw numbers.** 90 scrap points is not cheaper than 250
  Mk III tokens — they are different units. `plan_routes` deliberately refuses to take that minimum
  (the first draft did, and called scrap "cheapest"); it reports per-currency spend and marks a
  material FORCED only when it has exactly one allowed route.
- **`verify_facts.py` exists because a wrong written fact cost a raid attempt.** `data/claims.json`
  holds every checkable assertion the prose leans on; a failure means **a file in this repo is
  telling you something untrue — fix the file, not the checker.** Run `--unit <BASEID>` before
  acting on any gear/relic claim: the character card shows RELIC in Arabic and GEAR in Roman, and
  conflating them is exactly the 2026-08-17 error.
- `pull_mods.py` now also writes **`all_mats`** (the full material dict it used to discard), which is
  what lets `action_value.py` price the shortfall against real stock instead of gross demand.
  Until a pull runs with a live `HU_SID`, the report is demand-only and says so.

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
