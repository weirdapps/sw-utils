# farmbot — sub-project E: the "collect-or-sim" daily routine

- **Date:** 2026-08-03
- **Status:** Design approved; implementation not started.
- **Branch:** `farmbot-daily-collectors` (off `farmbot-multipool-validation` @ `37ab8fc`, i.e. includes PR #12's engine).
- **Player:** Astra · ally 145357294 · ~14.35M GP · Kyber.

## 1. Context

`farmbot/` today is a **Multi-Sim energy-dump macro**: a device-free template-matching state
machine (`EnergyDumpTask` in `farmbot/tasks.py`) that drives BlueStacks via ADB + OpenCV to
Multi-Sim 3★ campaign nodes across the 4 energy pools. It is complete and live-validated (PR #12,
80 tests).

The user asked to expand the bot to farm **"Coliseum, arenas, events, raids, and ALL other
dailies."** That request is not one feature — it is 4–5 independent subsystems with different
execution models. It was decomposed (see §9) and **sub-project E (passive collectors) was chosen to
build first**, because it is closest to the existing code, safe, useful every day, and forces the
daily-run scaffold the later orchestrator (A) will reuse.

### Governing decisions (from the brainstorming session)
1. **PvE only, never PvP.** Arena / GAC / TW are **collect-only**: the bot claims the daily payout
   (collectible without fighting) and **never auto-plays a PvP match**. This preserves the player's
   standing PvE-only boundary and keeps ban risk near zero. Consequence: the daily-activities
   crate's single required *squad-arena battle* stays **manual** — E flags it, never bots it.
2. **Never spend crystals** (or any premium currency). Hard rail, unchanged from the sim-macro.
3. **The unifying principle of E:** automate every daily that resolves via **tap-to-collect** or
   **Multi-Sim** — and *nothing* that needs a real-time battle, a PvP match, or a crystal spend.

## 2. Scope

### In scope (the "collect-or-sim" set)
- **Collect (tap-to-collect):** daily login-calendar reward; free daily store item/bundle;
  inbox/gift claims; achievements / Journey-Guide claims; **Squad + Fleet Arena payout**;
  **free-energy claims** (the timed grants on the energy bar).
- **Sim (Multi-Sim):** the **Daily Challenges** (training droids, ability mats, credits, gear,
  shard/GET) — battles that are Multi-Sim-able once 3-starred; same sim mechanism as the engine,
  different screen (the Challenges menu).
- **"All other free or sim":** handled structurally, not by hardcoding — E is **config-driven**, so
  any future free-collect or sim-able daily is a new routine entry + template, no new code.

### Out of scope (this sub-project)
- Real-time battles: Coliseum, Assault Battles, Events, Galactic War, Raids → sub-projects B / C.
- PvP matches (Arena/GAC/TW battling) → excluded by decision; payout collect only.
- Crystal spend; **scheduling** (an external launchd/cron runs E at grant times later);
  **template auto-capture** (a live, on-device step).

## 3. Architecture — generalize the runner (chosen approach ①)

The existing run loop is already mode-agnostic: popup-dismiss, scroll-scan, skip-vs-halt,
kill-switch, per-step `optional`/`ensure`/`skip_marker`, and `Summary` do not depend on energy. The
*only* energy-specific code is `_steps_for()`, which hardcodes the **Campaigns-menu** navigation.
Collect tasks and the Challenges screen live on **different screens**, so they need their own step
sequences regardless — which is why a pure-config approach is not viable and a second parallel
engine would only duplicate the loop.

**Decision:** keep the class and the entire run loop; split `_steps_for()` into **per-`kind` step
builders** dispatched from a single entry point. One engine, one loop, maximal reuse; the
"all free-or-sim" catch-all needs no new code paths.

```
EnergyDumpTask.run()            # unchanged loop: iterate routine entries, run each entry's steps
  └─ _steps_for(entry)          # NEW: dispatch on entry.get("kind", "energy_node")
       ├─ _steps_energy_node()  # today's _steps_for body, EXTRACTED VERBATIM
       ├─ _steps_collect()      # HOME → [nav] → CLAIM → [dismiss] → RETURN_HOME
       └─ _steps_challenge_sim()# HOME → OPEN_CHALLENGES → … → MULTI_SIM → CONFIRM_SIM → REWARDS → HOME
```

The class may keep its name for now (renaming ripples through tests); a follow-up may rename it to
`RoutineTask`. Not required for E.

## 4. Config schema (back-compatible)

Canonical list key becomes `routine`; **`nodes` is still accepted as an alias** so the 5 validated
entries and the 80 tests are untouched (`cfg.get("routine", cfg.get("nodes"))`). Each entry gains an
**optional `kind`, default `"energy_node"`**. `load_config`'s validation changes from requiring the
literal `nodes` key to requiring **either `routine` or `nodes`** (the other required keys —
`device_serial`, `caps`, `vision` — are unchanged).

```jsonc
{
  "device_serial": "emulator-5554",
  "caps":  { "max_actions": 400, "action_delay_ms": [700, 1800] },
  "vision":{ "match_threshold": 0.85, "step_timeout_s": 8.0, "energy_out_timeout_s": 2.0 },
  "routine": [
    // kind omitted => energy_node (unchanged behavior)
    { "campaign": "mod", "chapter": 2, "node": "2-F", "sim": "max", "for": "T05_06 salvage" },

    { "kind": "collect", "name": "login_reward",
      "nav": ["inbox_entry"], "claim": "login_claim", "for": "daily login calendar" },
    { "kind": "collect", "name": "store_free",
      "nav": ["store_entry"], "claim": "store_free_claim", "for": "free daily bundle" },
    { "kind": "collect", "name": "arena_payout_squad",
      "nav": ["arena_entry", "squad_arena_tab"], "claim": "arena_payout_claim",
      "for": "squad arena daily rank reward (collect-only, no battle)" },
    { "kind": "collect", "name": "energy_free",
      "nav": [], "claim": "energy_free_claim", "count": 2,
      "for": "timed free-energy grants; skip if not yet available" },

    { "kind": "challenge_sim", "challenge": "challenge_ability_mats",
      "for": "daily ability-mat challenge (Multi-Sim, 3★)" }
  ]
}
```

Field reference:
- `energy_node` — unchanged: `campaign`, `[difficulty]`, `[chapter]`, `node`, `sim`.
- `collect` — `name` (label for the summary), `nav` (ordered list of templates to tap to reach the
  claim screen), `claim` (the claim/collect button template), `count` (optional; tap the claim
  button up to N times for multi-item screens, stopping when absent), `scrollable` (optional).
- `challenge_sim` — `challenge` (the challenge's icon template); reuses `multi_sim` / `sim_confirm`
  / `rewards`.

## 5. Step builders

All three reuse the existing `Step` dataclass and its features (`tap`, `tap_offset`, `ensure`,
`ensure_extra`, `scrollable`, `optional`, `skip_marker`, `skip_tap`, `skip_counter`).

**Two additive `Step` fields wire the new counters** (both default such that existing steps are
unchanged, preserving extract-verbatim):
- `mark: Optional[str] = None` — on a successful tap, bump the named `Summary` counter. (The existing
  `mark_sim` bool is left untouched so `_steps_energy_node` stays verbatim; `collect`/`challenge_sim`
  use `mark` instead.)
- `optional_counter: Optional[str] = None` — when an `optional` step is skipped because its template
  is absent, bump the named counter. Existing optional steps (e.g. `SELECT_DIFFICULTY`) pass `None`,
  so the loop branch `if m is None and step.optional: continue` gains only
  `if step.optional_counter: bump(...)` before `continue` — behavior-preserving.

**`_steps_energy_node(entry)`** — the current `_steps_for` body, extracted **verbatim**. This is the
guarantee that all 80 existing tests pass unchanged.

**`_steps_collect(entry)`**
```
HOME (verify)
[ for t in entry["nav"]: Step(nav, t, scrollable=entry.get("scrollable", False)) ]
CLAIM  (entry["claim"], optional=True,                         # absent => nothing to collect => skip
        mark=entry.get("counter", "collected"),               # success bumps collected/energy_claimed
        optional_counter="nothing_to_collect")                # absent bumps nothing_to_collect
[ REWARDS dismiss if a reward popup appears ]                  # reuse TPL_REWARDS, optional
RETURN_HOME (home_button)
```
- Idempotent: an absent claim button (`optional=True`) means nothing to collect → the step is
  skipped, `nothing_to_collect` is bumped, no halt. `entry["counter"]` lets free-energy entries book
  to `energy_claimed` instead of `collected`.
- `count` > 1: repeat the CLAIM step, stopping at the first absent claim.
- Crystal-cost safety: if a claim path can surface a 💎-cost variant, that template is registered as
  a `skip_marker` (skip the entry), **never** a tap target.

**`_steps_challenge_sim(entry)`**
```
HOME → OPEN_CHALLENGES → CHALLENGES_MENU (verify) → SELECT_CHALLENGE(entry["challenge"], ensure=MULTI_SIM)
→ OPEN_MULTISIM → CONFIRM_SIM (mark="challenges_simmed", skip_marker=energy_out) → REWARDS → RETURN_HOME
```
- Uses `mark="challenges_simmed"` (not `mark_sim`), so challenge sims stay **disjoint** from energy
  `sims_done` — the two counters never double-count.
- A challenge not yet 3-starred won't offer Multi-Sim → treated like a depleted node (skip + flag),
  reusing `skip_marker`/`ensure_extra` semantics. Never falls back to a real battle.

## 6. Idempotency & run model

- **Idempotent by construction:** every already-satisfied daily is a graceful skip (`optional` claim
  absent, or `skip_marker`), never a halt. E is safe to run any number of times per day.
- **Single-pass, "collect what's claimable now."** Free-energy grants unlock at staggered game-clock
  times; E claims whatever is currently available and books the rest to `nothing_to_collect` — it
  does not wait or retry within a run. Note: an absent claim button cannot cheaply distinguish
  "already claimed" from "not yet available", so both fall under `nothing_to_collect`. Splitting them
  would need a dedicated countdown-timer template per grant (like `hard_depleted`) — deferred as
  optional/future, not required for E.
- **CLI:** add `--daily` to run the full `routine` (all kinds). Keep `--dump` as an alias so existing
  muscle memory / docs keep working. `--dry-run` and `--capture` unchanged.
- **Scheduling is external** and out of scope: a launchd/cron job may invoke `--daily` at the
  energy-grant times; E just needs to be safe to re-run (it is).

## 7. Safety rails (reaffirmed)

- **Never** tap PURCHASE / 💎-cost / crystal-refresh. Claim buttons only. Any crystal-cost template
  is a `skip_marker`, never a tap target (extends the proven `energy_out` / `hard_depleted` pattern).
- **Never PvP.** Arena entries are `collect` on the **payout** button; no battle/fight template is
  ever registered as a tap target.
- Kill-switch (Ctrl-C / `farmbot/STOP`), halt-screenshots (`farmbot/halts/`), hub-start/end per
  entry, and popup auto-dismiss are all inherited unchanged.
- Uncaptured template ⇒ **safe-halt** (existing behavior) — E degrades gracefully as templates fill
  in, and never blunders forward on an unrecognized screen.

## 8. Templates required (live, on-device capture)

Captured with the existing recipe (navigate → screenshot → PIL-crop → verify self-match; capture
**unselected** where a selection glow would otherwise cause a miss). Uncaptured = safe-halt, so
capture can be incremental.

- **collect:** `inbox_entry`, `login_claim`, `store_entry`, `store_free_claim`, `gift_claim`,
  `achievements_claim` / `journey_guide_claim`, `arena_entry`, `squad_arena_tab`, `fleet_arena_tab`,
  `arena_payout_claim`, `energy_free_claim`.
- **challenges:** `challenges_entry`, `challenges_menu`, and the daily challenge icons
  (`challenge_training_droids`, `challenge_ability_mats`, `challenge_credits`, `challenge_gear`,
  `challenge_shard`, `challenge_get`).
- Possibly a generic reward-popup dismiss if a claim screen's popup differs from the campaign
  `rewards` CONTINUE.

Exact node/tab/button identities are confirmed **on device at capture time** (reward icon is the
source of truth). The design lists what is needed; capture is a supervised live step.

## 9. Where E sits in the whole daily bot (for later)

| # | Sub-project | Model | Status |
|---|-------------|-------|--------|
| **E** | **Passive collectors (this spec)** | tap-collect / Multi-Sim | designing |
| B | Auto-battle engine (Coliseum, Assault Battles, Events) | start → poll-until-resolved → branch | future |
| C | Raids | deploy / auto | future (guild-gated) |
| A | Daily orchestrator (sequences sim-macro + E + B + C, one report) | orchestration | future (needs E, B) |
| D | Arena/GAC/TW | **collect-only** → folded into E | — |

## 10. Reporting

`Summary` gains per-kind counters: `collected`, `challenges_simmed`, `energy_claimed`,
`nothing_to_collect` (existing counters retained: `sims_done`, `energy_out_nodes`,
`hard_depleted_nodes`, `skipped_nodes`, `halted`, `halt_state`, `stopped_reason`).
`format_summary` prints a per-kind daily report, including a `nothing_to_collect` line (items already
claimed or not yet available). This report is the seed of A's future unified daily summary.

## 11. Testing (TDD, device-free)

Same harness as today — inject fake `look` / `tapper` / `swipe` sequences; no device needed.

- **Guard:** `_steps_energy_node` is extract-verbatim ⇒ **all 80 existing tests must still pass**.
- **New tests:**
  - collect happy-path (nav → claim → dismiss → home; `collected` bumped);
  - collect nothing-to-collect (claim absent ⇒ `nothing_to_collect`, no halt);
  - collect free-energy entry books to `energy_claimed` (via `entry["counter"]`), not `collected`;
  - collect `count` > 1 (claims until absent);
  - challenge_sim happy-path (`challenges_simmed` bumped **and `sims_done` unchanged** — disjoint);
  - challenge not-3★ skip (no Multi-Sim ⇒ skip, no battle);
  - **crystal-cost template is never tapped** (skip_marker path);
  - mixed-kind routine ordering (energy_node + collect + challenge_sim in one run);
  - `routine`/`nodes` alias + default-kind back-compat (+ `load_config` accepts either key);
  - `Summary` / `format_summary` per-kind output.

## 12. Open questions

None blocking. Deferred to capture time: exact template identities; whether any claim screen needs a
distinct reward-dismiss template.
