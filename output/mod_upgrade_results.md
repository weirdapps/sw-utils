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
- **Calibration blocked:** attempted a speed calibration sweep over 58 6-dot mods (50 never-calibrated). After the earlier gains (Rey 23->26) the game service returns `GOHServiceCall Error [40]` on every reroll (daily calibration cap; persists past a 20s pause). Resume after daily reset (~07:00 Athens).
