# Mod session — 2026-07-27 (Astra) — LATEST · TWO batches (placement re-opt + farmed-material upgrades)

100% browser-free API for upgrades; Grandivory (standalone bridge URL) for placement.
Two batches: (1) early — full placement re-opt + calibration attempts; (2) after Plessas farmed
T05_06 +225 & attenuators +32 in-game — slice/promote batch in best order.

## Score delta (full day: session start -> end)
| metric | start | end | Δ |
|---|--:|--:|--:|
| **HotUtils modScore** (inventory quality) | **2.37** | **2.37** | **0.00** (coarse/sticky) |
| Grandivory set-value sum (placement, batch 1) | 242,226 | 253,262 | **+4.56%** |
| 6A (6-dot gold) | 86 | **88** | **+2** (JKR, Baylan) |
| 6-dot total | 134 | **136** | **+2** (GK, Great Mothers 6E) |
| plusSpeed (total equipped mod speed) | 15,048 | 15,097 | **+49** |
| credits | 150.16M | 144.84M | −5.32M |
| Micro Attenuators | 72 | 14 | −58 net (spent 90, farmed +32) |
| T05_06 (master binding) | 5* | 55 | farmed +225, spent ~175 |

**Key finding: HotUtils `modScore` is a COARSE, INVENTORY-quality metric.** It did NOT move (2.37) despite
813 mods re-placed AND +2 6A / +2 6-dot mods — it would take dozens of upgrades to tick to 2.38, and
placement never affects it at all. So track session progress by **6A / 6-dot / plusSpeed / Grandivory
set-value**, not modScore. Report a "mod score delta" as BOTH modScore + those drivers.
(*T05_06 was 5 at the batch-2 start after batch-1 slicing; it was farmed to 230 before batch 2.)

## What happened
- **Materials partially farmed since 2026-07-25** (CG snapshot 21:38): T05_06 3→15, T05_03 6→303,
  T05_04 27→329, T06_02 84→89, Micro Attenuators 15→72. PROMO unchanged (528).
- **Slice:** Baylan Skoll 6C→6B (1 step). Then T05_06 ran dry. Promotes: **0** (need ~76, had 15).
  - **Precise recipe (live diff): ONE 6-dot slice step = 10× T05_06 + 20× T06_02 + ~126K credits.**
    15 T05_06 buys exactly one step. T05_06 is STILL the master gate for the whole slice/promote chain.
- **Calibrate:** 4 first-attempts on the highest-headroom rr=0 6A DEF mods (Ahsoka spd19, Darth Revan 21,
  Lord Vader 22, Jabba 23), stat:5 (Speed), keep-only-if-improved. **ALL 4 MISSED** (RNG ~25%; unlucky 0/4).
  0 kept, stats intact, 60 attenuators spent (72→12, below the 15 floor). Mechanic confirmed: reroll
  redistributes roll-weights across the 4 secondaries biased toward the target — not a clean speed bump.
- **Placement:** Grandivory re-optimize on the intact Jul-19 GAC priority list → **+4.56% set value,
  813 mods reassigned, 4,045,250 credits**, "Mods successfully moved" clean (no Row-not-found; data 2 min
  fresh). The large shuffle = the Jul-19 apply never fully landed (partial "Row not found") + drift since.
  Declined the optional +37.1M "level all moved mods to 15" (filler; move-only is ~4M).

## Batch 2 (02:53 — after Plessas farmed the right material)
- **Purchase verified: RIGHT material.** T05_06 5→230 (+225), attenuators 12→44 (+32), T06_02 69→94.
  Exactly the bottleneck — no wasted spend (contrast: earlier he'd been buying finished 6A mods from the store).
- **Upgrades in best order** (slice existing 6-dot DEF to 6A first → promote best 5A DEF → calibrate last):
  JKR 6D→6A (3 steps) + Baylan 6B→6A (1 step) = **+2 6A**; General Kenobi + Great Mothers 5A→6E = **+2 6-dot**.
  All defense, clean (4/4). Spent ~175 T05_06 + 70 T06_02 + 60 PROMO.
- **Calibration: 0/2 again** (Ahsoka spd24→19, JKR spd24→19, reverted). **Cumulative 0/6 this day.**
  Confirms: calibrating already-decent-speed (24) mods rarely beats them; slice-for-speed is the better lever.
  Attenuators 44→14. **Recommendation: stop calibrating decent-speed mods; save attenuators for low-speed/
  high-roll 6A mods only, or skip — slicing already bumps speed for free.**
- **Placement re-opt: deferred** (only 4 mods changed since the batch-1 813-move placement; upgraded in place,
  so chars already benefit; a full re-opt + ~4M credits is low-ROI for 4 mods). Run after the next big batch.
- **execute_upgrades.py cost constants corrected** to grounded values: 6-dot slice step = 20 T06_02 + 10 T05_06;
  promote = 76 T05_06 + 27 PROMO. build_plan now shares the T05_06 budget between slices and promotes.

## New reusable scripts
- `scripts/mod_score.py` — reads auth/player/login summary (modScore/gearScore/totalScore/mod6Dot/
  speed25-10/plusSpeed + attenuators/credits). Run before+after to diff. `--refresh` forces CG sync.
- `scripts/calibrate.py` — calibration sweep: ranks 6A GAC mods by speed headroom (rolls×6−spd),
  defense-first, rr asc (cheapest); reroll→keep-if-improved→else revert; self-stops on material-out.
  `--max N --min-headroom H --dry`.

## To resume (still farming-gated)
Farm **T05_06** (master binding — 5 left) for slices/promotes, and **Micro Attenuators** (Mod Battles
Map 9 — 12 left) for calibration. T06_02 (69), T05_03/04 (300+), PROMO (528) are stranded behind T05_06.
Placement is now current; re-run only after the next real slice/calibrate batch.

---

# Mod upgrade session — 2026-07-20 (Astra, ally 145357294)

Goal: from most→least important, upgrade / slice / calibrate mods for GAC until materials run out.
Priority = GAC defense-squad chars → offense → rest, by speed secondary (see `scripts/slice_plan.py`).

## Done
| action | count | mods |
|---|--:|---|
| Sliced to **6A** (6-dot gold) | 9 | Jabba, Rey, Lord Vader, Darth Revan ×3, JKR ×2, Ahsoka |
| Sliced to **6B** (partial) | 1 | Morgan Elsbeth |
| **Promoted** 5A→6E | 5 | Starkiller, Bastila, Ezra (Exile), JKR ×2 |
| **Calibrated** toward speed | Rey 23→26 | (Jabba 26 already near-max; others maxed/low charges) |
| Sliced to **5A** | 15 | Darth Revan, R2-D2, Morgan ×2, Ben Solo, Baylan, Scorch, CX-2, Appo, Ezra, Shin Hati, Boushh, Dengar, Great Mothers, Bastila |
| Leveled to 15 | 1 | (prereq for slicing) |

6-dot gold count: **72 → 81**. 6-dot total: 122 → 127. Credits spent ≈ 7M (137.9M left).

## Materials — exhausted where it counts
| material | left | gates |
|---|--:|---|
| T06_02 | 3 | 6-dot slice-up (binds at ×20/step) — **out** |
| T05_06 | 15 | 5A→6E promote (binds at ×50) — **out** |
| T05_03 | 6 | 5C→5B — **out** |
| T05_04 | 27 | 5B→5A — **out** |
| T05_01 / T05_02 / T05_05 | 400 / 272 / 423 | stranded (low 5-dot steps; can't reach 5A without T05_03/04) |
| PROMO_T5_T6 | 518 | stranded (needs T05_06 to promote) |
| T06_01 / T06_03 / T06_04 | 823 / 30 / 151 | stranded (need T06_02 to slice 6-dot) |

Stopping point is genuine: every **complete** upgrade path is blocked by a depleted intermediate tier.
Leftover materials only allow pushing low mods 5E→5C (≈0 GAC value), so execution stopped here.

## To resume after farming
Farm **T06_02** (6-dot slice-up) and **T05_06** (promotions) first — they're the binding constraints.
Then re-run `scripts/slice_plan.py` on a fresh `data/mods_full_*.json` and execute the queue again.
API recipes + payloads in `memory/notes.md`.


## Follow-up actions 2026-07-20 (later)
- **Leveled 92 sub-15 mods on GAC-squad chars to level 15** (batch `mods/level` requestType 3). Cost 16.16M credits (121.7M left). All confirmed level 15.
- **Calibration blocked = OUT OF MATERIAL (not a daily cap):** the calibration material is **Micro Attenuators** (`summary.currency` id 41), which my slicing-only tracker didn't watch. Had 1000 → **5 left** (need ≥15 for one more). `GOHServiceCall Error [40]` = insufficient attenuators. Only Rey (23→26) landed before it ran dry. **Refill: Mod Battles Map 9 (in-game only)**, then resume the sweep over the 50 never-calibrated 6A mods (target flat→speed).

---

# Mod upgrade session — 2026-07-25 (Astra) — 100% via curl API, no browser

Executed with the new browser-free pipeline: `scripts/pull_mods.py` (pull+refresh) →
`scripts/slice_plan.py` (rank) → `scripts/execute_upgrades.py` (slice/promote via `mods/tier`).

## Done
| action | count | mods |
|---|--:|---|
| Sliced to **6A** | 5 | Starkiller, Morgan Elsbeth, Bastila Shan (DEF); Darth Malak, JKL (off) |
| **Promoted** 5A→6E | 7 | Baylan, Appo, Darth Revan, R2-D2, Bastila Shan, Lord Vader, General Kenobi (all DEF) |
| Sliced partial 6E→6C | 1 | Baylan Skoll (banked 2 of 4 steps; T05_06 ran out at step 3) |

**6A: 81 → 86.  6-dot total: 127 → 134.  Credits ≈ 3.25M spent (139.4M left).**
Calibration **deliberately skipped** (15 attenuators = only 1 attempt; saved for a real sweep — user decision).

## Corrected material recipe (from live before/after diffs — supersedes the ~50 estimate)
- **5A→6E promote ≈ 76× T05_06 + 54× T05_05 + 27× PROMO_T5_T6 + credits.**
- **6-dot slice steps ALSO consume T05_06** (+ the per-tier T06_0x salvage). So **T05_06 is the master binding material** for the entire chain (promotes AND slices), not T06_02.
- Per full 6E→6A slice: the 6D→6C step is the T06_02-heavy one (~80); other steps use T06_01/03/04 + T05_05/06.

## Materials at stop (T05_06 exhausted)
| mat | start | end |
|---|--:|--:|
| T05_06 (master binding) | 538 | **3** |
| T06_02 | 254 | 84 (stranded) |
| PROMO_T5_T6 | 718 | 528 (stranded) |
| T05_05 | 805 | 425 |
| Micro Attenuators (cur 41) | 15 | 15 (saved) |
| credits | 142.7M | 139.4M |

## To resume after farming
Farm **T05_06** (master binding) + **Micro Attenuators** (Mod Battles Map 9). Then:
`HU_SID=<live> python3 scripts/pull_mods.py && python3 scripts/slice_plan.py && HU_SID=<live> python3 scripts/execute_upgrades.py --dry`
Baylan Skoll is mid-slice at 6C — finishing it to 6A is the top queued item. Then calibrate the defense 6A pool.

---

# Audit session — 2026-07-25 (Astra) — full mods + squads + fleets management pass

Browser-free HotUtils API (curl/urllib) for mods + Playwright same-origin fetch for swgoh.gg.
Session captured via Discord silent SSO (chrome-devtools). **Net game-state change: none** — the
account was already optimal; every remaining lever is farming-gated or deferred by user choice.

## Mods — confirmed materially exhausted (no action possible)
Fresh `account/refresh` (gameDataAgeUtc 2026-07-25T00:09 — no in-game play since the 03:00 run):

| material | qty | gate |
|---|--:|---|
| **T05_06** (master binding) | **3** | promotes + every 6-dot slice step — OUT |
| T06_02 | 84 | 6-dot slice (stranded behind T05_06) |
| PROMO_T5_T6 | 528 | stranded |
| Micro Attenuators (cur 41) | 15 | 1 calibration attempt only |
| credits | 139.2M | — |

- Live `mods/tier` on **Baylan Skoll 6C→6A** returned `rc=2 "Not enough player currency!"` — 3× T05_06 can't cover one step. Promotes: **0** possible.
- 6A = **86**, 6-dot = 134 (unchanged since 03:00). **0 sub-15 mods on GAC chars** (all 220 sub-15 are 5-dot filler → leveling would waste credits).
- **Calibration: SAVED** (user) — 15 attenuators = 1 attempt (~25%); saving for a farmed sweep of the ~50 uncalibrated 6A defense mods.

## Squads / fleets — verified current, NO rebuild
- swgoh.gg season unchanged: **S80** (5v5) / **S79** (3v3), not rolled.
- Roster refreshed → 2026-07-25: +103K GP; +Cobb Vanth (filler); 19 relic/star bumps to units **already on the board** (Cassian UC r6→8, Kleya r6→7, Luthen r5→7, Ben Solo/Boushh r7→8, Leviathan 6★→7★).
- Recompute (fresh roster + fresh S80/S79 meta): **5v5 & 3v3 DEFENSE identical** to the live HotUtils board. Offense = same real teams (clean full-size); live board's extras are harmless partial-team reference lines. No new GL / squad-defining unit; **gaps unchanged** (GL Hondo, Third Sister, Profundity).
- Mod-placement re-optimization: **DEFERRED** (user) — only ~12 mods changed tier since the Jul 19 optimize; best ROI after the next farmed slice batch.

## Repo refreshed
roster 20260725; fresh meta (4 files, S80/S79); gac_result recompute (archived to history/2026-07-25); deliverables regenerated (playbook.html + payload, offense now clean 12/13); compute_teams.py + generate_hotutils.py ROSTER_FILE bumped to 20260725.
