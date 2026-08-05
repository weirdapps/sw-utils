# SWGOH endgame daily routine (2026) — automation reference

Grounding for the farmbot daily orchestrator: what a high-GP endgame player (5M+ GP, multiple GLs,
Kyber GAC) does every day, mapped to how the bot handles each. Sourced 2026-08-03 (post Cantina 2.0,
May 2026; Eras & Episodes). Verify node IDs on swgoh.gg/db/missions (Cantina 2.0 renumbered nodes).

Automation tags: **COLLECT** (tap-to-claim) · **SIM** (Multi-Sim / ticket sim) · **BATTLE-PVE**
(auto-battle vs AI) · **PVP/MANUAL** (excluded — human/PvP).

## The daily, mapped to bot kinds

| Task | Tag | Bot kind | Notes |
|------|-----|----------|-------|
| Spend all Normal energy (LS/DS Hard nodes) | SIM | `energy_node` | 5 attempts/Hard node/day; multi-sim once 3★ |
| Spend all Cantina energy | SIM | `energy_node` | Cantina C1–C9 (C9 added May 2026) |
| Spend all Fleet/Ship energy | SIM | `energy_node` | Fleet Battles Hard nodes |
| Spend all Mod energy | SIM | `energy_node` | **Mod Battles T1 (5-dot) + T2 (slicing)** — Mod *Challenges* were removed in Cantina 2.0 |
| Finish 2 character Challenges | SIM | `challenge_sim` | 8 challenges rotate weekly; sim once 3★ |
| Finish 1 Fleet Challenge | SIM | `challenge_sim` | Ship Building / Ability Materials; locks out at 6★ capital ship |
| **Galactic War** | SIM (after 50 completions) / BATTLE-PVE before | `battle` (or a GW sim tap) | **Endgame = full-sim for 12 tickets.** Astra (14M GP) is almost certainly past 50 → GW is SIM, one tap, no fight |
| Coliseum daily | BATTLE-PVE | `battle` | Era boss-score; a Daily Quest requires an active fight; `attempts` for the day |
| Daily login reward / streak | COLLECT | `collect` | Inbox/home popup; lost if missed |
| Loaned-unit Era level token | COLLECT | `collect` | Daily inbox (Cantina 2.0) |
| Bonus energy: Normal ×3, Cantina ×1, Mod ×1, Ship ×1 | COLLECT | `collect` (`counter: energy_claimed`) | **6 windows/day, +45 each, 2-hour window, LOST if missed** (Normal noon/6pm/9pm; others ~noon/6pm rel. to reset) |
| Squad + Fleet Arena daily payout | COLLECT | `collect` | **Rank-based, no fight needed** — collect-only |
| Store/token spends (Cantina/GET/Guild/Shard/Squad/Fleet/Episode) | COLLECT-ish | manual | Spending non-crystal currency — left MANUAL (bot never auto-buys, to avoid wrong-currency spend) |
| Achievements / Journey Guide milestones | COLLECT | `collect` | Periodic |
| Raid attempt (600 tickets/day is the guild duty) | BATTLE-PVE/GUILD | `battle` | Order 66 raid; endgame GL teams auto-battle |

## The 7 Daily Quests → daily crate (65 crystals, Omega, 45 tickets, …)

1. Use 600 energy — SIM (covered by energy_node farms; also makes 600 raid tickets)
2. Open 1 Data Card in Store — **MANUAL** (store spend)
3. Purchase 3 Store Shipments — **MANUAL** (store spend)
4. Finish 2 Challenges — SIM (`challenge_sim` ×2)
5. Finish 1 Fleet Challenge — SIM (`challenge_sim`)
6. **Finish 1 Squad/Fleet Arena battle — PVP, MANUAL** (can't sim; the one PvP tap/day)
7. Finish a Galactic War battle — SIM after 50 completions (else auto-battle)

So the bot can satisfy 5 of 7 Daily Quests automatically; **2 are inherently manual** (the arena battle + the two store-purchase quests count as the store-spend items). The crate itself expires at daily reset.

## Time-boxed / must-not-miss (bot should run at/after the bonus windows)
Bonus energy (6×/day, 2-hr windows) · daily login streak · Daily-Quest crate (expires at reset) ·
arena payouts · 600 raid tickets · (periodic) GAC join/defense/attack, TB/TW phases, Conquest.

## Genuinely NOT automatable (human judgment) — the bot must never attempt these
GAC attack/defense · Territory War attacks/defense · Conquest sectors & feats · Proving Grounds ·
TB Special Missions (exact squad combos) · Coliseum team optimization (auto-battle ok, score not
optimized). PvP (Squad/Fleet Arena battling, GAC, TW) is **excluded by the owner's PvE-only rule**.

## Energy economy (post-Cantina 2.0)
Pools (cap 144 free): Normal (10/hr), Cantina (5/hr), Mod (10/hr), Ship (10/hr). Free bonuses add
~45 each per window. Endgame spend priority: Cantina → Normal(Hard) → Mod → Fleet. Standard crystal
spend is the first 3 Normal refreshes (50 crystals each) — **the bot does NOT refresh (never spends
crystals); refreshes stay a manual choice.**

## Implications wired into the bot
- `config.example.json` demonstrates the full routine across all four kinds.
- GW: for a 50+ completion account, prefer a **sim** entry over `battle` (one tap). Represented as a
  `battle` in the example for the general case; switch to sim for Astra once the GW-sim button is captured.
- The 2 store-purchase Daily Quests + the 1 arena battle are **left manual by design** (currency spend
  / PvP) — the bot reports them as the residual manual daily, it never performs them.
