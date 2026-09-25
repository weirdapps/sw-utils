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
| **~16:30 09-25** | **Squad Arena re-climb** (payout ~17:00) | 4 battles left; Rotta Hutt squad | Hit #1 at 00:50 09-25, knocked to **#3** by 03:00. Climb in the last 30 min. |
| **~17:45 09-25** | **Fleet Arena** (payout ~18:00) | 2 battles left; Leviathan preset | **#1** at 01:50 09-25. Re-climb only if knocked. |
| **~20:55 daily** | **Action Jaxxon marquee Tiers I-III** | SIM all three, claim Tier III shards | **55/65** after the 09-24 claim. Two more (09-25, 09-26) = 5★ → DJJ Tier II. |
| **by ~20:55 09-25** | **Coliseum Jotaz T8** (boss rotates then) | 3 attempts banked | AUTO converged 92-93% (high 95%) on both the 8/8-pip Jedi board and holotables' 98% board. Only a MANUAL run reaches 100%. |
| **~21:00 09-25** | **TW Jakku setup phase** (joined 09-25 03:05, 22/50, min 25) | `tw_scan_notes.py`, obey the gold notes, place from `tw_placement_sheet.txt` | SET is irreversible. Do not attack Gungan walls. |
| **00:00 09-26** | **GAC round 1 ends / round 2** | `pull_gac.py` twice (first pull after a flip is stale), scrape new leaders, plan | R1: **us 1,709** vs DarkBane (0 at 03:00). Defence edits made during R1 deploy at R2. |
| 09-26 ~10:00 | **Ground War** (Assault Battles) | Play/star, then SIM | Assault Battles are a Droid Brain / relic source. |
| 09-27 ~10:00 | **Galactic Bounties II** ("very rare") | Check tiers and rewards | |
| 09-28 ~10:00 | **Endor (Omega Battles)**, Conquest ~09-28 | Plan squads before entering | |
| ~09-29 | **Coven of Shadows**; Episode + Era Shipment refresh | Buy Fragmented + Incomplete (Episode) and **Flawed ×25 (Era, 1,250 tokens)** | Flawed is the binding relic mat (1 after GG R8). |
| ~09-29 | Jaxxon marquee ends | Clear Tier IV once Jaxxon is 5★ | |
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
- ⛔ **Crystals only for a measured, significant gain** (owner, 2026-09-24: "any other currency,
  only if the value is significant"). One 100c cantina refill bought +6 Flawed and unlocked
  Gamorrean Guard R8 on 2026-09-25; that is the bar. Never the Jawa deal or early arena skips. Banked: 7,798.
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
