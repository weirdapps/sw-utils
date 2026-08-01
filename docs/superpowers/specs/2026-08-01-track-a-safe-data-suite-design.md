# Track A — Safe Data Suite (Design)

- **Date:** 2026-08-01 · **Repo:** sw-utils · **Risk:** none (read-only external + existing HotUtils)
- **Parent:** `2026-08-01-swgoh-automation-roadmap-design.md`

A0 provides the data backbone; A1–A4 are modules over it. All external reads are read-only
(comlink + swgoh.gg API); mod inventory continues to come from HotUtils.

---

## A0 — comlink data backbone

**Purpose:** Replace fragile in-session swgoh.gg scraping (Cloudflare + authenticated browser)
with structured API pulls.

**Approach (chosen):** self-host `swgoh-comlink` via Docker locally, on-demand; access from
Python via `comlink-python` (PyPI `swgoh-comlink`, v2.2+). Meta data via the **swgoh.gg API**
(key, header `x-gg-bot-access`), not scraping.
- *Alternatives considered:* keep browser scraping (rejected — Cloudflare-fragile, needs live
  session); run comlink on the VPS as a perpetual service (deferred — local on-demand is simpler,
  no daemon to maintain).

**Module:** `scripts/swgoh_data.py`
- `get_roster(allycode)` → roster with gear/relic/equipped-mods/GP (comlink `/player` + `StatCalc`)
- `get_meta(season, fmt)` → Hold%/Win% squads, counters, mod-efficiency (swgoh.gg API)
- `get_events()` → active/upcoming events (comlink `getEvents` + swgoh.gg `/events`)
- `get_datacrons(allycode)` → datacron inventory (comlink)
- `get_gac_bracket(allycode)` → live bracket / leaderboard (comlink `getLeaderboard`)

**Boundaries / deps:** comlink **cannot** see unequipped mods → mod inventory stays via HotUtils
`account/data/all` (existing `pull_mods.py`). So the two read sources are `swgoh_data.py` (public
data) + `pull_mods.py` (HotUtils mod inventory).

**Integration:** update `compute_teams.py` to source roster from `get_roster()` instead of the
`ROSTER_FILE` browser scrape, and meta from `get_meta()`.

**Success:** `compute_teams.py` runs end-to-end with **zero browser steps**.

---

## A1 — daily brief

**Purpose:** One artifact that says exactly what to do today.

**Approach (chosen):** `scripts/daily_brief.py` → terminal summary + `output/brief_<date>.html`
(same pattern as existing `playbook.html`). Email delivery via existing Outlook/mail infra is a
later option, not v1.

**Inputs:** `swgoh_data` (roster, events, GAC bracket) + `pull_mods` (materials, modScore) +
A3 advisor output.

**Sections:**
1. **Energy/sim plan** — which nodes to sim today (from A3).
2. **Farm targets + panic-farm** (from A4).
3. **GAC status** — current opponent + board reminder.
4. **Event countdowns.**
5. **Mod material status** — T05_06 / T06_02 / Micro Attenuators + next slice/calibrate target.

**Success:** the brief covers the full daily routine at a glance.

---

## A2 — GAC opponent scouting → board

**Purpose:** Build the board against the **likely opponent's** tendencies, not just generic meta —
the lever for Kyber 3 → 2.

**Approach:** resolve opponent ally code (HotUtils GAC planning, or comlink bracket) → fetch
opponent roster (comlink) + GAC defense history (swgoh.gg) → produce "opponent likely defenses +
your best counters" and feed into `compute_teams.py` offense planning.

**Module:** new `scripts/scout.py` + hook into `compute_teams.py`.

**Note:** opponent identity is known only once matchmaking sets it → scouting runs **per round**.

**Success:** the offense plan references the opponent's actual recurring defenses.

---

## A3 — farm/gear/datacron advisor

**Purpose:** Data-driven "what to farm / gear / roll next."

**Module:** `scripts/advisor.py`

**Inputs:** roster (`swgoh_data`) × board needs (`compute_teams` gaps) × known gaps
(Hondo / Third Sister / Profundity) × mod materials (`pull_mods`) × datacron inventory + meta
(`swgoh_data`).

**Outputs:** ranked **farming priority** (which nodes / energy types); **gear/relic** "what next";
**datacron roll targets** (which datacron for which GAC squad — planning only; rolling is manual
in-game, no write API).

**Feeds:** A1 (brief) and B1 (macro's "what to farm" list).

**Success:** produces an actionable ranked list the brief and macro consume.

---

## A4 — event / GL-journey readiness

**Purpose:** Never miss GL Hondo's return (the #1 gap); know exactly what's missing.

**Module:** `scripts/events.py`

**Inputs:** swgohevents.com **iCalendar feed** + swgoh.gg `/events` + roster.

**Outputs:** event return calendar; per-event readiness (owned vs required units at required gear);
panic-farm list when an event nears.

**Success:** "GL Hondo returns on X; missing Y at gear Z; here's the panic-farm list" is generated
automatically.
