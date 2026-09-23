# STANDING ORDERS: Astra account management
Owner mandate, 2026-09-23: *"Since you are now managing this account, be prepared to pursue
any pending items and act on them as soon as they become available."*

**Read this at the START of every session, before doing anything else.** Work the WATCH LIST
top-down, act on anything whose trigger has passed, then report. Do not wait to be asked.

⚠ **Honest limit:** I only run while a session is open, and the game lives on local
BlueStacks, so no VPS or GitHub Action can drive it. "As soon as available" means *first
action of the next session after the trigger*, unless a wake mechanism is set up.

---

## WATCH LIST (times are Europe/Athens; re-read the live timer, never trust these)

| When | Item | First action | Rule |
|---|---|---|---|
| **~23:58 daily** | **GAC round attack phase** | `gac/get` then `gac3v3_attack.py`, then attack | ⭐⭐ TOP PRIORITY, standing rule. Fleets: attack with **Leviathan / Executor**, they are free now. |
| ~17:55 daily | Fleet Arena payout | Check rank ~17:45, re-climb if knocked | Currently #1. 5 battles/day. No crystal skips at >2h out. |
| ~07:00 daily | Squad Arena payout | Check rank, re-climb if knocked | Currently #1. Defence = the squad you LAST attacked with. |
| 23:00 daily | Daily quests reset | farmbot once, then finish by hand | Farmbot misses the shop step and the arena battle. |
| **on boss rotation** | **Coliseum** | Look the NEW boss up on holotables, rebuild, run | ⭐ Maxing a tier refills attempts and opens the next. The blocker is always the SQUAD. |
| 2026-09-25 | Smuggler's Run III | SIM every tier | Run II paid a big share of +92 attenuators and +152 T05_06. |
| ~2026-09-28 | **Conquest opens** | Plan squads before entering | Stamina-gated, not energy-gated (12,449 banked). |
| ~2026-09-29 | Episode Shipment refresh | Buy Fragmented + Incomplete Signal Data | The only non-cantina Signal Data route. ~47K episode currency banked. |
| ~2026-09-29 | Jaxxon marquee ends | Clear any newly unlocked tier | Tier 3 needs 4 stars = 30 shards, have 15. |
| **2026-09-30** | **PROFUNDITY** | **PLAY IT BY HAND** | ⛔ Cannot be simmed. All 14 gates verified PASS. |
| 2026-10-01 | Set 32 datacrons expire | Re-run `gac_cron_assign.py`, re-attach | Great Mothers, ST Luke, Cassian carry set-32. |

## ALWAYS-ON (no trigger, do whenever the state allows)
1. **Scavenger** whenever low-tier gear accumulates. It is free and it is the best lever
   found so far: Aeromagnifier 2 to 230, Aurodium 386 to 821 in one pass.
2. **Check the EVENT ACTIVE tile every session.** Resource Events and Assault Battles never
   red-dot, are SIM-able once starred, and out-earn energy nodes by orders of magnitude.
3. **`mods_session.sh` after any farming**, it spends whatever arrived in ladder order.
4. **Ninth Sister R6 to R7** when relic mats allow. Unblocks Third Sister slack.
5. Claim every red dot: inbox, Episode Track, quests, Coliseum, guild.

## HARD PROHIBITIONS
- ⛔ **Do not touch relics on Admiral Raddus (R9), Cassian Andor (R8), Dash Rendar (R7)**
  before Profundity is played. All three sit exactly at threshold.
- ⛔ **Never spend real money.** Suggest only; the owner decides.
- ⛔ **Do not spend crystals** on energy refreshes, the Jawa Daily Deal, or arena skips.
  All eight sinks were tested and priced on 2026-09-23; none is worth it. Banked: 5,708.
- ⛔ **Do not attack a TW Gungan wall** with this account's leftover pool. 0-for-3, and five
  guildmates forfeited the same wall.
- ⛔ **Do not burn Coliseum attempts on AUTO** once a tier has converged.

## REPORTING
Every session: state what the trigger was, what was done, and what is next. Report failures
with the actual output. Never claim something landed without verifying it on screen.
