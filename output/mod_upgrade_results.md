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
