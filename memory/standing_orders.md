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
| **~16:30 09-26** | **Squad Arena** (payout ~17:00) | 4 battles left; Rotta Hutt squad | **#1** at 01:10 09-26. Re-climb only if knocked. |
| **~17:45 09-26** | **Fleet Arena** (payout ~18:00) | 5 battles left; Leviathan preset | **#1** since 09-25. Re-climb only if knocked. |
| **~20:00 09-26** | **TW Jakku attack phase** (24h) | Attack with SEE / JML trio / Leviathan / Inquisitorius by matchup | 19 squads + 7 fleets placed to the notes (808). Never a Gungan wall. |
| **~20:59 09-26** | **Jaxxon marquee Tier III → 5★** | Claim (+5 = 65/65), promote Jaxxon, clear Tier IV, then **DJJ Tier II** | The game lists this marquee and Terrible Tings as Mk VI Besh sources (the era-level gate); check which tier pays it. |
| **~20:55 09-26** | **Coliseum boss rotates** (Dryax done at 97%) | holotables.xyz/boss/<new>, owned-only board | Rank 86 pays 600 era tokens/day. |
| **00:00 09-27** | **GAC R2 attack vs ИваН** | `pull_gac.py` twice, scrape new leaders, exact rows only | SR 3,164 (Kyber 3). His answers are all ≥81%; the round is won on offence. |
| **before 02:30 09-27** | **Raid tickets** | Spend all four energy pools (Dark Side nodes) | Guild day resets ~02:32, NOT 22:59. 0/600 for the 09-26 guild day. |
| 09-26 ~10:00 | **Ground War** (Assault Battles) | Play/star, then SIM | Assault Battles are a Droid Brain / relic source. Starts after the 03:10 session; play it in the evening one. |
| 09-27 ~10:00 | **Galactic Bounties II** ("very rare") | Check tiers and rewards | |
| ~20:00 09-28 | **Rise of the Empire TB** | Specials → ops → combat → deploy | P3 Tatooine `special_reva` = Third Sister shards (232/330). |
| 09-28 ~10:00 | **Endor (Omega Battles)**, Conquest ~09-28 | Plan squads before entering | |
| ~09-29 10:00 | **Coven of Shadows**; Episode + Era Shipment refresh | Buy Fragmented + Incomplete (Episode), **Flawed ×25 (Era, 1,250)** and **Impulse ×10 (Era, 3,000)** | Binding R8 mats: Flawed 11/45, Impulse 1/20. |
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
  Gamorrean Guard R8 on 2026-09-25; that is the bar. Never the Jawa deal or early arena skips. Banked: 7,938 (1,250 lost to a scripted mis-tap on 09-26).
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
