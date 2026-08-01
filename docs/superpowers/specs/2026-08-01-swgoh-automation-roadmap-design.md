# SWGOH Automation — Roadmap & Decomposition (Design Overview)

- **Date:** 2026-08-01
- **Repo:** sw-utils
- **Owner:** Astra (ally 145357294, GAC Kyber, ~14.3M GP)
- **Companion specs:** `2026-08-01-track-a-safe-data-suite-design.md`, `2026-08-01-track-b-pve-farming-macro-design.md`

## Goal

Astra is burnt out on the daily SWGOH grind; the realistic alternative is abandoning the
account. Objective: make the account **run itself on the decision layer** and **remove the
manual grind on the execution layer**, so the only thing done by hand is the part worth doing
(GAC attacks). Astra has given **explicit, informed acceptance of ToS/ban risk for Track B**,
because the downside (account loss) is bounded by the fact the account would otherwise be
abandoned.

## Core principle (the dividing line)

- **Data / Decision layer** — *what* to build / place / farm / gear / roll / counter. Fully
  automatable, **zero ban risk** (read-only APIs + existing tolerated HotUtils writes). → **Track A**.
- **Execution / Battle layer** — *playing* battles. NOT safely automatable via third-party input
  simulation (ban risk). Only the game's native sim/auto-battle are sanctioned. → **Track B**
  automates **only PvE farming execution**, on Astra's own machine, at accepted risk.

## Hard boundary (non-negotiable)

- ✅ **PvE farming automation — in scope** (grinding own nodes; no human opponent).
- ❌ **PvP-combat automation — out of scope** (Squad/Fleet Arena, GAC, TW — playing against real
  people). Astra plays GAC by hand anyway; excluding this costs nothing.
- ❌ No real-money purchase automation. No account-credential handling beyond what HotUtils already does.

## Decomposition

**Track A — Safe data suite** (Python; read-only comlink + swgoh.gg API + existing HotUtils reads/writes):

| ID | Sub-project | One-liner |
|----|-------------|-----------|
| A0 | comlink data backbone | Replace fragile browser scraping with structured API pulls |
| A1 | daily brief | One artifact: exactly what to do today |
| A2 | GAC opponent scouting → board | Build the board vs the real opponent's tendencies |
| A3 | farm/gear/datacron advisor | Data-driven "what to farm/gear/roll next" |
| A4 | event / GL-journey readiness | Never miss GL Hondo's return; know what's missing |

**Track B — Grind-killer** (ToS/ban risk; runs on Astra's Mac):

| ID | Sub-project | One-liner |
|----|-------------|-----------|
| B1 | PvE farming execution macro | Auto-sim/auto-play own PvE nodes via Android emulator + ADB + vision |

## Dependency graph & build order

1. **A0** — foundation; everything reads through it.
2. **A1** — fast visible value; needs A0.
3. **A3** — needs A0; feeds A1 and B1.
4. **A2** — needs A0; extends existing GAC pipeline.
5. **A4** — needs A0; feeds A1.
6. **B1** — emulator/ADB setup can start in parallel; consumes A3's "what to farm" list;
   standalone fallback = manual node list.

## Shared conventions

- **Data-driven only** — no hardcoded rosters/teams (consistent with existing CLAUDE.md rules).
- **Secrets via env** — HotUtils session id, swgoh.gg API key; never committed.
- **Artifacts** — project outputs → repo `output/`; ad-hoc → `~/Downloads`; specs → `docs/superpowers/specs/`.
- **Risk isolation** — comlink is read-only + no login (zero incremental risk); HotUtils writes
  unchanged; B1 is fully isolated on the user's machine, PvE only.

## Approaches

Per-sub-project approach trade-offs and the chosen option are documented inline in the two
companion specs (each "Approach" subsection lists the alternative considered and why it was
rejected). This overview locks scope, boundary, and build order only.

## Success criteria (overall)

- Daily routine reduces to: **read the brief → (optionally) launch B1 → tap GAC by hand.**
- No dependence on in-session browser scraping (Cloudflare eliminated).
- Each sub-project independently shippable and testable.
