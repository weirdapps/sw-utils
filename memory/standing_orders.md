# STANDING ORDERS: Astra account management
Owner mandate, 2026-09-23: *"Since you are now managing this account, be prepared to pursue
any pending items and act on them as soon as they become available."*

**Read this at the START of every session, before doing anything else.** Work the WATCH LIST
top-down, act on anything whose trigger has passed, then report. Do not wait to be asked.

## OPERATING MODEL (owner decision, 2026-09-23)
**The owner starts the session. My job is to make sure nothing is forgotten while I am
already running, and to PROMPT him.** No cron, no resident loop.

Three obligations that follow from that:
1. ⭐ **"Run the daily tasks" ALWAYS includes a full WATCH LIST sweep.** It is not just the
   farmbot and the 8 dailies. Work the table below top-down, act on every trigger that has
   passed, and say what you skipped and why. See DAILY TASKS below for the exact routine.
2. ⭐ **PROMPT THE OWNER, unasked, the moment a deadline is near or an opportunity opens.**
   If something is due in the next few hours, say so in that session even if he asked about
   something else entirely. He is relying on me to raise it, not on himself to remember.
3. ⭐ **END EVERY SESSION with the next three triggers and their times**, so he knows when to
   start the next one. This is the whole substitute for a wake mechanism; skipping it is how
   a deadline gets missed.

⚠ **Honest limit:** I only run while a session is open, and the game lives on local
BlueStacks, so no VPS or GitHub Action can drive it. A trigger that passes with no session
open is simply missed, which is exactly why obligation 3 is not optional.

---

## DAILY TASKS ROUTINE (what "run the daily tasks" means)
0. **Read this file. Sweep the WATCH LIST. Act on anything whose trigger has passed.**
1. Check live timers on the hub rail; never trust the times written here.
2. Farmbot once, then finish by hand what it misses (shop purchases, the arena battle).
3. Claim every red dot: inbox, Episode Track, quests, Coliseum, guild, login calendars.
4. Both arenas to #1 if a payout is near.
5. Check the EVENT ACTIVE tile for SIM-able Resource Events and Assault Battles.
6. Scavenger if low-tier gear has piled up; `mods_session.sh` if materials arrived.
7. **Report, then list the next three triggers with times.**

---

## WATCH LIST (times are Europe/Athens; re-read the live timer, never trust these)

| When | Item | First action | Rule |
|---|---|---|---|
| **~00:00 on 09-25** | **GAC round 1 ATTACK phase vs DarkBane** | re-pull `gac/get` (the first pull after a flip returns the OLD match), scrape counters for NEW leaders via Playwright, `gac3v3_attack.py`, attack | ⭐⭐ TOP PRIORITY. ⚠ Corrected 09-24: midnight on 09-23 opened the DEFENCE phase ("SET DEFENSES! 23h 56m"), not the attack phase. Opponent: 13.41M GP, 10 GLs, modScore 6.17. Fleets: attack with Leviathan / Executor. |
| ~18:00 daily | Fleet Arena payout | Check rank ~17:45, re-climb if knocked | **#5** at 09-24 00:00 (was #9). 5 battles/day. No crystal skips at >2h out. |
| **~17:00 daily** | Squad Arena payout | Check rank ~16:30, re-climb if knocked | **#3** at 09-24 00:07. ⚠ Corrected: the PRIZES tab reads ~17:00, not 07:00. Defence = the squad you LAST attacked with (Rotta). |
| 23:00 daily | Daily quests reset | farmbot once, then finish by hand | Farmbot misses the shop step and the arena battle. |
| **on boss rotation** | **Coliseum** | Look the NEW boss up on holotables, rebuild, run | ⭐ Maxing a tier refills attempts and opens the next. The blocker is always the SQUAD. **Zeffo T9 62%, rank #92, 2 attempts left until ~21:05 09-24**: AUTO has plateaued at ~60% on both boards, so play the researched MANUAL line (notes.md) to reach 70% and rank ≤90 (600/day). |
| **~20:55 daily** | **Action Jaxxon marquee, Tiers I-III daily** | SIM all three, claim **5 Jaxxon shards** from Tier III | Jaxxon **50/65** after the 09-23 claim. Three more claims (09-24, 25, 26) = 5★. Marquee ends ~09-29. |
| **when Jaxxon hits 5★ (~09-26)** | **DJJ "Terrible Tings" Tier II** | EVENT ACTIVE → Terrible Tings → Tier II | Starkiller vs 3 Stormtroopers: Son of the Suns when up, basic the buffed trooper, watch Air Supply. Recipe in `notes.md`. 65 shards → DJJ 5★ + 6,700 Mk VII Aurek + 330 Mk VII cores. |
| 2026-09-25 | Smuggler's Run III | SIM every tier | Run II paid a big share of +92 attenuators and +152 T05_06. |
| ~2026-09-28 | **Conquest opens** | Plan squads before entering | Stamina-gated, not energy-gated (12,449 banked). |
| ~2026-09-29 | Episode Shipment refresh | Buy Fragmented + Incomplete Signal Data + Omicron mats | ~53K episode currency banked. Omicrons cost 20 mats; 18 on hand. |
| **every Era Shipment refresh (~09-29)** | **Era Shipment: Flawed Signal Data ×25 for 1,250 era tokens** | Buy it first | Flawed is the binding relic material (27 on hand, 45 per R7→R8). Era tokens come from Coliseum rank. |
| ~2026-09-29 | Jaxxon marquee ends | Clear Tier IV once Jaxxon is 5★ | Jaxxon **50/65** after the 09-23 claim. |
| **2026-09-30** | **PROFUNDITY** | **PLAY IT BY HAND** | ⛔ Cannot be simmed. All 14 gates verified PASS. |
| 2026-10-01 | Set 32 datacrons expire | Re-run `gac_cron_assign.py`, re-attach | Great Mothers, ST Luke, Cassian carry set-32. |

## ALWAYS-ON (no trigger, do whenever the state allows)
1. **Scavenger** whenever low-tier gear accumulates. It is free and it is the best lever
   found so far: Aeromagnifier 2 to 230, Aurodium 386 to 821 in one pass.
2. **Check the EVENT ACTIVE tile every session.** Resource Events and Assault Battles never
   red-dot, are SIM-able once starred, and out-earn energy nodes by orders of magnitude.
3. **`mods_session.sh` after any farming**, it spends whatever arrived in ladder order.
4. ✅ **Ninth Sister is R7** (found already done on 09-24). Relic spend now follows `invest_plan.py`; every R7→R8 is gated on Flawed 45 + Impulse 20.
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

⭐ **Close every session with this block, always:**
```
NEXT TRIGGERS
  <time>  <item>  <what I will do>
  <time>  <item>  <what I will do>
  <time>  <item>  <what I will do>
```
The owner starts the sessions, so this block is the only thing standing between a deadline
and a missed deadline. Write it even when the session was about something unrelated.
