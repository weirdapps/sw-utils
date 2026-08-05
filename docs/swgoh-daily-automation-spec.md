<!-- Generated 2026-08-03 by a 50-agent workflow: 6 research sweeps + 3 codebase audits,
     then 40 adversarial refutation passes, then synthesis.
     CONFIDENCE WARNING: the refutation pass was deliberately skeptical ("default to
     refuted if uncertain") and killed 35 of 40 claims it examined. Treat every node id,
     star level and drop rate below as a HYPOTHESIS to confirm on device — the node's
     reward ICON is the only ground truth the game exposes. Where this file disagrees with
     farmbot/TARGETS.md, neither wins by default. -->

# SWGOH daily automation spec (farmbot)

Canonical merge of the 2026 research sweep, the adversarial verification pass, and the codebase audits.
Player: **Astra** · 14.35M GP · Kyber 3 · 9 GLs · raiding guild. Written 2026-08-03.

**Hard rails (non-negotiable):** never spends crystals · never plays a PvP match (payout collection is fine) · may spend in-game tokens · Multi-Sim > PvE auto-battle > MANUAL.

**Scheduling:** the routine is **not** once-daily. Free-regen caps at 144/pool and regen *halts* there, and the three free-bonus windows are 2h and expire. Run **3× per day anchored in UTC** at `reset−12h+10m`, `reset−6h+10m`, `reset−3h+10m`. A single daily pass wastes ~288 energy/day and cannot reach the 600-energy quest (4 × 144 = 576 < 600).

---

## The complete 2026 endgame daily

Ordered by the sequence one bot run should execute. Kinds: `energy_node` · `collect` · `challenge_sim` · `battle` · `shop` · `MANUAL`. **(new)** marks a kind/nav target that does not exist yet.

| # | Task | Cadence | Classification | Bot kind | Guard required | Notes |
|---|------|---------|----------------|----------|----------------|-------|
| 0 | **Preflight** | every run | — | harness | `--doctor`: device ready, SWGOH foregrounded, template coverage green, STOP file absent, **crystal balance snapshot** | Abort non-zero on any gap. Never touch the device on a failed preflight. |
| 1 | **Recenter hub** | every entry | — | `_hub_prelude` | `hub_anchor` + `hub_anchor_open` must both match; if either template is absent, **warn-and-skip, do not halt** | Consoles are 3D and render at pan-dependent position/scale/tap-target. Overlays (badge, home, energy) are pan-invariant. Templates captured, wiring unvalidated. |
| 2 | **Free bonus energy** (6 grants / 3 windows) | 3×/day, 2h window, **lost if missed** | COLLECT | `collect` | Template must anchor on the word **FREE**; the crystal-priced refresh row sits directly below it and is blacklisted | reset−12h: Normal+Cantina+Mod. reset−6h: Normal+Fleet. reset−3h: Normal. 270 energy/day. **Claim before dumping** — bonus ignores the 144 cap. `energy_free_claim` NOT captured. |
| 3 | **Inbox** (mail, gifts, Episode payouts, Loaned-Unit Era token) | daily | COLLECT | `collect` | Only free CLAIM / CLAIM-ALL crops are tap targets | `inbox_entry`/`inbox_menu`/`inbox_claim` captured; entry not in live config. |
| 4 | **Daily login calendar** + secondary calendars | daily, forfeits at month end | COLLECT | `collect` | Claim must be matched **before** `_dismiss_popups` closes the calendar | `daily_login_tab`/`login_calendar_menu`/`cal_tab_*` captured; `login_claim` NOT captured. |
| 5 | **Fleet Arena payout** | daily @ reset−5h | COLLECT | `collect` | Nothing that starts a match may ever be a tap target on this screen | Confirmed still live. Largest guaranteed daily crystal income. Templates missing. |
| 6 | **Squad Arena payout** | daily @ reset−6h | COLLECT | `collect` | Same, **plus** a missing tab must degrade to a clean skip, not a halt | Retirement announced 27 Apr 2026, ship date unconfirmed. Do not capture until presence is verified. |
| 7 | **All character Challenges** (bulk MULTI SIM) | daily | SIM | `challenge_sim` | Sim-ticket floor ≥40; reject-template for Era Challenge tiles; **verify against the Daily Quest counter, not the badge**; crystal delta = abort | Captured + live-validated (14 battles in one tap). Do **not** assert a fixed completion count — the roster rotates by weekday. Mod Challenges no longer exist; absence must be a clean no-op. |
| 8 | **Fleet Challenge ×1** | daily, day-gated | SIM | `challenge_sim` **(new nav)** | Highest tier only (T4 Ship Ability Mats = the only Zeta tier); auto-battle fallback **hard-disabled** → degrade to MANUAL | Separate screen from character Challenges — the existing MULTI SIM does **not** satisfy "Finish 1 Fleet Challenge". 1 challenge live Tue–Sun, 3 on Mon. 2 shared attempts/day. |
| 9 | **Galactic War full-campaign sim** | daily | SIM | `gw_sim` **(new)**, collect-shaped | Require a **positively matched ENABLED** `gw_multisim`; `gw_restart` is a **hard-blacklisted tap target**; sim tickets ≥12; abort if the confirm shows a crystal cost; verify the quest row flips | 12 sim tickets, no energy, one tap. Must run **before** any human touches GW (sim is whole-campaign, all-or-nothing). No enabled MULTI SIM ⇒ record `gw_already_done`, no-op. `gw_*` templates captured, entry unwired. |
| 10 | **Mod energy dump** — T2 `2-D` → `2-E` → `2-C` → `2-F` | 2×/day | SIM | `energy_node` | `expect_reward` per node; `hard_depleted` = marker only, never tapped; crystal snapshot | **Highest-leverage pool for this account.** T06_02=31 is the binding gate → 2-D first. Current config farms 2-F, which feeds the most-surplus material. **Tier 1 excluded** (does not feed the slice chain; drives the 500-mod hard cap). Multiple nodes required — a single depleted node strands the whole pool. |
| 11 | **Cantina energy dump** — `3-B` → `6-A` → `9-D`/`9-F` | 1–2×/day | SIM | `energy_node` | Explicit allow-list of one node per pass; **per-entry sim count** (see gap M-14) | Scarcest pool (5/hr). 3-B Vane + 6-A Silvo are the two hard GL-Hondo blockers (both 2★). Stage 9 Omicron is on **9-B/9-D/9-F**, not 9-A/9-E/9-G. Stage 9 needs a **manual 3★ clear first**. Drop `1-A` — Geonosian Soldier is 7★. |
| 12 | **Fleet Hard dump** — `1-A` → `3-D` → `2-A` → `2-E` → `2-D` | 2×/day | SIM | `energy_node` | Rotate to next node on `hard_depleted`; **never tap by coordinate** on the sim panel; the `hard_depleted` crop is 💎25 and will MISS at Fleet's 💎200 → must degrade to safe halt | 5 attempts/node/day. ~285 energy/day covers ~3 full nodes. Drop `1-E` — Resistance X-wing is 7★. 1-A Ithano and 3-D Quiggold are Accelerated (2 shards/drop). |
| 13 | **LS/DS Hard dump** — `1-D` → `8-B` → `9-F` (overflow) | 2×/day | SIM | `energy_node` | Same, **plus** `requires_3star: true` on any tier 6–9 node so an unstarred new battle is never treated as SIM | 1-D Kix is now Accelerated (7-22-2026), 12 energy, 2 shards — best Normal-energy node. 8-B blocked on the ch8 nav bug. 9-F is gear-salvage overflow only. |
| 14 | **Coliseum — quest tick** | daily, opt-in | AUTO_BATTLE (quest tick only) | `battle` | Screen-identity precondition before START; `attempts` hard-pinned to 1; explicitly **not** a score attempt | Score is a persistent high-water mark, so a throwaway auto run cannot lower a banked score. Leaderboard/score optimisation is MANUAL. |
| 15 | **Free Bronzium ×1** ("Open 1 Data Card") | daily | COLLECT (free claim) | `collect`, Store-scoped **(new nav)** | Bronzium template must be tight; crystal/real-money neighbours as reject templates; **exactly one pull**, never 10 | Ally Points are outside the rails' token list — this is a free claim, not a token spend. Store → Data Cards is the highest-crystal-density screen in the game. `bronzium_free`/`bronzium_claim`/`bronzium_skip` captured. |
| 16 | **Token shop buys** (Cantina tab only, phase 1) | daily | SHOP_TOKENS (gated) | `shop` | Item template cropped **including its token price chip** + currency-specific confirm + crystal-balance assert + no REFRESH template exists | See §2. Everything else stays MANUAL. |
| 17 | **Daily Activity Prize Box** + per-quest claims | daily, **expires at reset** | COLLECT | `collect` | Free-claim crops only | 8/8 is unreachable (quest 6 is PvP), but per-quest rewards still claim. `daily_activity_claim`/`quests_menu` captured. |
| 18 | **Post-run verify + report** | every run | — | harness | **Crystal balance identical to the pre-run snapshot** → else abort loudly; assert 600-energy quest counter; log sim-ticket + raid-ticket deltas | Emit the residual MANUAL list (§3) and exit non-zero on any halt/cap/kill. |
| — | Guild Activities (day's objective) | daily | SCHEDULER HINT | read-only | — | Not a task. An advisory tie-breaker on pool ordering. The Sat/Sun Squad-Arena halves are permanently MANUAL-SKIP. Never hoard energy for a tier at the cost of the 600 tickets. |
| — | 600 Raid Tickets | daily (guild clock) | DERIVED | post-condition | — | Not a task. 1 ticket per energy point from Normal/Cantina/Mod/Ship. Currently a **failing** post-condition (~491/600 on the live config) until the node set widens and the run splits into 2–3 passes. **Guild reset ≠ personal reset** — a run straddling guild reset splits the contribution across two guild-days. |

---

## Token & shop policy

### Current posture: REPORT-ONLY + one free claim

The bot performs **zero token purchases today**. It may:
1. Claim the **one free Bronzium** pull (Daily Quest 2) — a free claim, not a spend.
2. **Read and report** every currency balance in the daily summary (`Cantina 4,120 — consider spending`), with a distance-to-cap line for Episode Currency (~30k hard cap, actively destroys income at cap).

The human executes all purchases. This preserves 100% of the "before the caps bite" value at zero spend risk.

### Phase 1 (only after B-1 and B-5 in §4 land, and after a supervised trial)

**Exactly one permitted tab: Cantina Battles Shipments.** It is the only tab with a captured currency-specific confirm (`shop_confirm_cantina`), which is guard #2 in `_steps_shop`.

Purchases permitted, each as an explicit item template cropped to **include the token price chip**:
- Character shards for units **below 7★** (roster-verified, re-confirmed each GAC season).
- Cassian's U-wing blueprints (5/400) once no sub-7★ character remains.
- Nothing else. No "buy the cheapest thing" heuristic. No positional taps. No count > 1 per run per item.

Preconditions before any tab is added: crystal-balance snapshot asserted pre/post; `forbid` made fail-**closed**; the item + confirm + cancel templates all present at preflight; ≥3 supervised runs with `blocked_spends` and `bought` logged.

### Permanently blacklisted — never a nav target, never a tap target

| Blacklisted | Why |
|---|---|
| **Every REFRESH / "Refresh Shipments" / circular-arrow control, in every tab** | Crystal ladder 50→50→100×4→200×3→400×3→900×3→1,800×3→3,600×2 = 17,600 crystals. #1 crystal-leak vector. The Shard Store's 25c and Mod Store's 15c refreshes are the most dangerous because they look harmless. |
| **Featured Shipment** | Crystal-primary; stock re-randomises every restock so credit/crystal slot assignment is not stable. |
| **Weekly Shipment** | Crystal-only except two token rows; adjacent rows cost 500–5,750 crystals. Blacklist the whole tab. |
| **Store → Data Cards** (except the free Bronzium) | Chromium + limited-time real-money packs in the same grid. |
| **Store → Resources / Crystals / Gifts** | Crystal- and real-money-only. Do not navigate in. |
| **Conquest Store** | Dual-priced rows: the *same* item shows 475 Conquest Credits **and** 600 crystals side by side. Icon matching is insufficient. |
| **Mod Store** | Needs speed-secondary OCR the engine does not have; 15-crystal refresh; and mod inventory is hard-capped at 500 with no bot sell path. |
| **Squad Arena / Fleet Arena / Grand Arena stores** | PvP-screen adjacency; the primary CTA on the parent screen is a battle button. |
| **Any "Purchase Energy 💎200" / "buy sim tickets" upsell** | Reuse the proven `energy_out` CANCEL template. CANCEL, never PURCHASE. |
| **Hard-node attempt refresh (💎25→50→100→200)** | `hard_depleted` is a marker with `skip_tap=False`. Never pressed. |
| **Proving Grounds tier refresh (2,200 crystals ×2)** | ~44% of the current balance in one tap. |
| **Conquest Stim Packs / Marquee Data Card / Conquest Pass+** | Crystal controls inside a battle-retry or event flow the bot would naturally be tapping. |

### Machine-readable allow-list shape

```json
{
  "shop_policy": {
    "mode": "report_only",
    "crystal_assert": { "snapshot_before": true, "assert_unchanged_after": true, "on_delta": "abort_run" },
    "global_blacklist": [
      "refresh_bar", "crystal_price", "featured_tab", "weekly_tab", "resources_tab",
      "crystals_tab", "gifts_tab", "conquest_tab", "mod_store_tab",
      "squad_arena_store_tab", "fleet_arena_store_tab", "grand_arena_store_tab"
    ],
    "free_claims": [
      { "name": "bronzium_daily", "nav": ["store_entry", "bronzium_free"],
        "claim": "bronzium_claim", "dismiss": "bronzium_skip", "count": 1,
        "reject": ["crystal_price", "chromium_card", "realmoney_pack"] }
    ],
    "report_balances": [
      { "currency": "episode",  "cap": 30000, "warn_above": 24000 },
      { "currency": "cantina",  "cap": null,  "warn_above": null },
      { "currency": "gw",       "cap": null,  "warn_above": null },
      { "currency": "guild",    "cap": null,  "warn_above": null },
      { "currency": "get1" },  { "currency": "get2" }, { "currency": "get3" },
      { "currency": "fleet_arena" }, { "currency": "shard" },
      { "currency": "micro_attenuator", "id": 41 }
    ],
    "buys": [
      {
        "enabled": false,
        "name": "cantina_shipments",
        "tab": "shop_tab_cantina",
        "nav": ["shipments_entry", "shop_tab_cantina"],
        "confirm": "shop_confirm_cantina",
        "cancel": "shop_cancel",
        "forbid": "crystal_price",
        "forbid_mode": "fail_closed",
        "max_purchases_per_run": 3,
        "items": [
          { "item": "buy_cantina_uwing_400", "count": 1,
            "requires_roster_below_7star": "CASSIANUWING", "price_chip": "cantina_token" }
        ]
      }
    ]
  }
}
```

`forbid_mode: "fail_closed"` is load-bearing: an **uncaptured** `forbid` template must veto, not permit (see gap **B-5**).

---

## Left MANUAL by design

| Task | Reason | Note |
|---|---|---|
| Daily Quest 6 — 1 Squad/Fleet Arena battle | **PvP** | The single unavoidable manual tap. Blocks the 8/8 crate permanently. Report it every run. |
| Grand Arena Championship (join, defense, attacks) | **PvP** | The repo's *other* pipeline (`compute_teams.py` → HotUtils) exists to plan this offline. Alert on the 24h Join Phase — not joining lowers Skill Rating. |
| Territory War (all phases) | **PvP** | Flag the sign-up window; missing it forfeits rewards entirely. |
| Era Arena (when it ships) | **PvP** | Replaces Squad Arena. Same rail. |
| Guild raid **deployment** | **Human judgment + irreversible** | Units lock out for the whole raid on deploy; score is guild-visible and shared. Only COLLECT (finished-raid claim) and REPORT are automatable. |
| Coliseum score/rank push | **Human judgment** | Era Levels + per-boss Overcharge allocation vs a rotating boss; mods/relics do not apply. Only the 1-attempt quest tick is automated. |
| Conquest (all of it) | **Human judgment + no sim + crystals** | Data-disk picks under a capacity budget, feat routing, stamina; keycard-**score**-dependent crates; Stim Packs are crystal-priced in the retry flow. |
| Territory Battle — special missions, platoons, deployment | **Human judgment (guild-coordinated)** | Wrong platoon donation blocks a guildmate and cannot be undone. TB combat missions are a *possible* narrow AUTO_BATTLE lane behind a human-curated (phase, territory, mission, squad) allowlist. |
| Era Challenges | **Human judgment** | Feat-conditional (specific unit at specific Era Level); 7-day window means no time pressure. Astra's GP/GLs give zero advantage. |
| Assault Battles / Era Battles | **Human judgment** | Faction-locked ≠ squad pre-filled; 63 lineup states; the `battle` kind has no unit-selection capability. Only a re-run of a battle+tier the human already cleared is defensible. |
| Legendary / GL / Journey / Marquee events | **Human judgment** | One-time unlock rewards; a wrong squad burns a limited attempt. |
| Ultimate Journey Event | **Human judgment** | Monthly, R7+ GL check needed. |
| Proving Grounds | **Human judgment + crystals** | Simmability unconfirmed; the only repeat is a **2,200-crystal** refresh. |
| Mod management (slice / promote / calibrate / level) | **Separate pipeline** | HotUtils API + Grandivory, not the game client. `mods/tier` with `simulation:true` is **not** a dry run. |
| Guild Exchange — request gear | **Human judgment** | Depends on the current gearing plan. Donating is COLLECT-shaped and could be automated later. |
| **All** token/currency purchases except the Cantina carve-out | **Irreversible spend + roster judgment** | Which shard to buy is the highest-judgment recurring decision in the game and shifts as farms complete. |
| Webstore daily reward + Kessel Run | **Outside the ADB surface** | It is a website. Needs a separate authenticated Playwright script. |
| Every crystal refresh (Normal/Fleet/Mod/Cantina/Conquest/Hard-node) | **Crystals** | Advice only. Recommended for the human: Normal ×3, Fleet ×3, then **Mod ×3** (overrides generic advice — Mod is this account's live bottleneck), then Cantina ×3. Hard-node attempt refresh: skip. |

---

## Engineering gaps, prioritized

Merged and deduplicated across all three audits. Items already fixed since the audits ran are noted at the end.

### Blockers

| ID | Gap | One-line fix |
|---|---|---|
| **B-1** | `defeat.png` missing **and** `victory.png` ↔ `rewards.png` cross-match at 0.983 (both are the same green CONTINUE bar) — a loss matches `victory`, so `battles_lost` is structurally always 0 and capturing `defeat` alone will not fix it. | Re-capture `victory` from the VICTORY banner/star row (not CONTINUE), capture `defeat` from the DEFEAT banner, and replace the victory-then-skip_marker sequence with a `wait_any([victory, defeat])` helper. |
| **B-2** | `--daily` can never report failure: `continue_on_halt` breaks before `s.halted = True`, so `main()` returns 0 even when every entry halted; `cap` and `killed` also exit 0; `halt_state` is overwritten per entry. | `return 0 if (stopped_reason == "complete" and not halted and not halted_entries) else 1`; change `halt_state` to `halt_states: list[str]` and print the joined list with each failing entry's name+kind. |
| **B-3** | An **optional** step is skipped *before* popups are dismissed, so a popup over a claim books `nothing_to_collect` and silently loses the day's reward; a popup over `AUTO_{a}` burns a battle attempt on an unplayed 180 s timeout. | Move the `_dismiss_popups()` + re-look block above the optional check in `run()`, gated on `_dismiss_popups` actually having closed something. |
| **B-4** | `collect` kind has **never executed a tap on device**. `energy_free_claim`, `login_claim`, `arena_entry`, `squad_arena_tab`, `arena_payout_claim` are all absent, and an absent template on an optional step is indistinguishable from "already claimed" — a permanent silent false negative on ~270 energy/day plus both arena payouts. | Capture cheapest-first (`energy_free_claim` → `login_claim` → arena chain); make `look()` distinguish *template file absent* from *not on screen* so a missing file on an optional step is a hard error, not a `nothing_to_collect`. |
| **B-5** | The `forbid` veto fails **open**: `if step.forbid is not None and self.look(step.forbid, ...)` + `look()` returning `None` for an uncaptured template ⇒ an absent `crystal_price.png` reads as "no crystal glyph on screen ⇒ safe to CONFIRM". Preflight does not require `forbid`/`cancel` either. | Pass the known-template set into the task and treat an uncapturable `forbid` as **vetoed**; add `forbid`/`cancel` to `devtool.required_templates` for `kind=="shop"`; raise the forbid look timeout from `energy_out_timeout` to `step_timeout`. **No shop entry ships until this lands.** |
| **B-6** | No crystal-balance assertion exists anywhere — the "never spends crystals" rail is verified only by a human reading the notes after the fact. | Snapshot the crystal counter at run start and end (OCR or a template-diff on the HUD chip); any decrease aborts the run and exits non-zero. |

### Major

| ID | Gap | One-line fix |
|---|---|---|
| **M-1** | Chapter-8/9 nav is geometrically impossible: tab strip is at y≈182 but every swipe is issued at a hardcoded y=560 (the node map); `scroll_scan` starts with two *right* swipes (wrong direction for a high chapter); `SELECT_CHAPTER` has no `ensure`, so a mis-tap is misattributed to `SELECT_NODE`. | Add `Step.swipe_y` (make `make_swipe` take y per call), order the scan direction by chapter number, and give `SELECT_CHAPTER` an `ensure` so a wrong-chapter landing re-taps. |
| **M-2** | `match_threshold: 0.85` is provably ambiguous — `home_button` scores 0.850–0.858 on real hub frames while `hard_tab` false-positives at 0.886 on a map that is *already* Hard. No global threshold works. | Re-capture `home_button` (include the frame, not just the glyph) and `hard_tab`/`normal_tab` so selected/unselected separate by >0.10; restore 0.88; add optional per-template threshold overrides. |
| **M-3** | Live config farms the **wrong nodes**: mod `2-F` (surplus T05, not the binding T06_02 at 2-D), cantina `1-A` (Geonosian Soldier already 7★, burning the scarcest pool), fleet `1-E` (Resistance X-wing already 7★). Six of eight researched sub-7★ shard nodes are still uncaptured. | Rewrite the routine to §1 rows 10–13; capture Fleet Hard first (5 of 6 missing targets, all in ch1–3). |
| **M-4** | No `expect_reward` assertion per node — a Cantina-2.0 reward shuffle silently burns 5 irreplaceable attempts/day on the wrong shard, with zero error signal, because sim auto-collects. | Add a required `expect_reward` template (a crop of the reward-strip icon, **not** node art) asserted at `SELECT_NODE`; mismatch ⇒ skip + loud `wrong_reward` counter. Auto-retire an entry when its target hits 7★ from the roster JSON. |
| **M-5** | Only one Mod node is wired; when it depletes, the entire Mod pool (the #1 material bottleneck) goes unspent — observed live at 213/144. | Wire 2-D → 2-E → 2-C → 2-F so the existing depleted-skip cascades; add `requires_3star` + `repeat_until_energy_out`. |
| **M-6** | Multi-Sim auto-fills to max energy, so the **first** node consumes the whole pool and every later same-pool entry energy-outs. Cantina has two must-farm nodes (Vane, Silvo). | Add a per-entry `sim: <n>` count (not just `"max"`), or alternate the head of the cantina list by weekday, or rely on the 3-run schedule with one node per pass. |
| **M-7** | No PvP screen-identity precondition on `battle` START — the never-play-PvP rail is a comment, not a check, and `battle_start.png` is a low-texture green-button crop. | Make `screen` mandatory for `kind=="battle"` (a `tap=False` identity step before START) and add a global `PVP_MARKERS` veto checked in `_tap`. |
| **M-8** | ADB failures are silent: `tap`/`swipe` never check `returncode`, `TimeoutExpired` escapes uncaught, `ADBError` from `screencap` kills `main()` with a traceback and **no summary**, and there is no app-foreground check. | Raise `ADBError` on non-zero returncode/timeout in `tap`/`swipe`; wrap `task.run()` in try/except and print a partial summary; add a `dumpsys window` foreground check next to `device_ready()`. |
| **M-9** | Kill switch is up to 180 s late (`vision.wait_for` never polls `should_stop`), is misreported as a **halt**, and still issues up to 6 popup-dismiss taps after the operator asked to stop. | Thread `should_stop` into `wait_for` as an abort predicate; have `_scroll_find`/`_pan` raise a private `Stopped` so `stopped_reason="killed"`; early-return from `_dismiss_popups`/`_recover_to_home`; restore `default_int_handler` on the second SIGINT. |
| **M-10** | `STOP` file is never cleared and there is no `--stop`/`--resume`; one stopped run turns every subsequent unattended run into a silent exit-0 no-op. | Warn loudly with the file mtime and exit non-zero unless `--force`; add `--stop`/`--resume`; surface STOP state in `--dry-run`/`--doctor`. |
| **M-11** | `_pan` and `_scroll_find` are open-loop: 8 blind swipes with no post-condition, and a failed scroll leaves the view displaced ~1800px with no restore, stranding every later entry. | Give `_pan` an `expect=` template that breaks early and reports failure; have `_scroll_find` restore its starting offset on failure; make `recenter` mandatory for every entry. |
| **M-12** | `max_actions: 400` in the live config aborts the **entire run** on cap (not isolated like a halt), and the summary says only `reason=cap`. | Raise to ≥600, make the cap per-entry (bump `halted_entries`, recover, continue), and print `ACTION CAP HIT — routine truncated after entry N`. |
| **M-13** | `energy_out_timeout` (2.0 s) is used for `_panel_ready`, `_recover_to_home`, `_dismiss_popups`, post-swipe looks and `ensure` checks — too short for animated transitions; on timeout the engine re-taps the **original** coordinates, which toggles a node panel shut (a plausible cause of the intermittent SELECT_NODE failures). | Add `Step.ensure_timeout` defaulting to `step_timeout`; keep the 2 s probe only for instantaneous skip_marker checks; re-look before each `ensure` re-tap instead of reusing a stale Match. |
| **M-14** | Hub recenter is captured but unwired and unvalidated; `OPEN_EVENTS` has a tap-offset and `ensure` but the tap has never been proven to open Events at a pinned pan. | Wire `recenter: true` on entry 1 and `recenter + pan` on the Events-rooted entries; validate the `events_entry` hit-box offset on device *after* the pan is pinned. |
| **M-15** | GW is a one-tap sim for this account and all five `gw_*` templates are captured, but no entry exists in either config — it is being done by hand daily. | Add a `gw_sim` entry (collect-shaped, **not** `battle`) with the enabled-MULTI-SIM gate and the RESTART blacklist from §1 row 9. |
| **M-16** | Raid entry exists in `config.example.json` but not `config.json`, and the notes describe template names (`raid_deploy`, `raid_results`, guild nav) that do not match the shipped entry. | Reclassify the raid to MANUAL deploy + COLLECT claim per §3, and correct the notes to the shipped nav (`events_entry → raids_tab → raid_active`). |
| **M-17** | "The bot reports the residual manual dailies" is documented in three places and implemented nowhere. | Add a no-op `manual` kind (empty Step list, cannot tap) carrying `name`/`for`, and have `format_summary` emit a trailing `STILL MANUAL: …` block. |
| **M-18** | No test loads the real `templates/` directory — all 104 tests inject a scripted `look`, so missing files and template collisions cannot fail CI, and `devtool.py` is untracked with zero tests. | Commit `devtool.py` with tests; add `tests/test_farmbot_templates.py`: (a) `coverage()` clean for both configs, (b) N×N cross-match below threshold with an explicit allowlist, (c) each template self-matches at 1.0 and stays below threshold on the archived `halts/` frames. |
| **M-19** | PRs #12, #13, #14 are all still open and stacked; `master` carries none of the last three sessions' work, and the only working routine (`config.json`) is gitignored and unversioned on one machine. | Merge #12 → #13 → #14 in that order via `gh pr merge`, re-run the suite on master, and commit a redacted `config.astra.json` so the working routine is reviewable. |
| **M-20** | Docs are stale in ways that will mislead the next session: `farmbot/README.md` documents the legacy `nodes` schema, a nonexistent `dialog_close`, and omits `--daily` and three of four kinds; repo `CLAUDE.md` never mentions farmbot; `TARGETS.md` has wrong nodes (Sith Infiltrator 3-D, Stage-9 Omicron letters, LS 7-B Bronzium Wiring, LS 1-C Carbonite); `notes.md`/`CLAUDE.md` still say "Mod Battles Map 9" (deleted — it is Tier 2). | Rewrite `README.md` around the dispatched engine + capture rules; add a farmbot bullet to `CLAUDE.md`; apply the §5 corrections to `TARGETS.md` and `notes.md`. |
| **M-21** | No scheduler exists, so the 2-hour bonus-energy windows will keep being missed, and `nothing_to_collect` cannot distinguish "already claimed" from "not yet available". | Ship a launchd plist firing `--daily` at reset−12h/−6h/−3h (+10 min) **in UTC**, logging each summary to a dated file; optionally capture the grant countdown template to split the two cases. |

### Minor

| ID | Gap | One-line fix |
|---|---|---|
| **m-1** | `Summary.skipped_nodes` is unreachable dead state (every skip step overrides `skip_counter`) yet printed on every run, reading as "nothing was skipped". | Make it a genuine roll-up (bump both) or drop it from `Summary` and `format_summary`. |
| **m-2** | `normal_tab.png` is orphaned — required by neither config, since every difficulty entry sets `hard`. | Keep only if a Normal-difficulty node is planned; have preflight report orphans so this stays visible. |
| **m-3** | `config.example.json` silently lost 6 entries in commit `1489a52` (`inbox_gifts`, `store_free`, `arena_payout_fleet`, `guild_rewards`, `galactic_war`, Coliseum attempts 5→1) while the notes still call it "the full 18-entry routine"; it also omits the validated DS 8-B node. | Restore the entries (an absent template is a safe skip/halt) and correct the notes' entry count. |
| **m-4** | `config.json` still uses the legacy `nodes` alias rather than the canonical `routine`. | Regenerate from the example with `routine`. |
| **m-5** | `challenges_sim_confirm` ↔ `sim_confirm` cross-match at 0.970 — the proof that `sim_confirm` does not false-match the crystal PURCHASE button covers the energy flow only and has not been extended to the challenges confirm. | Raise the CONFIRM_SIM threshold, require the ensure-anchor (`challenges_sim_confirm` reachable only from a matched `challenges_multisim`), and add an explicit negative match against crystal/BUY/REFILL artifacts. |

### Already fixed since the audits ran (do not re-litigate)

`--doctor` preflight with `devtool.coverage()` now exists in `run.py`. `hub_anchor`/`hub_anchor_open` are captured and `_hub_prelude` is wired. `_steps_shop` guard #2 was redesigned from `forbid=crystal_price` to a **currency-specific confirm** (`shop_confirm_cantina`), with `shop_cancel` and `shop_tab_cantina` captured — the fail-open `forbid` bug (B-5) survives but is now a second-line guard, not the only one. `format_summary` already prints `bought` / `blocked_spends` / `recentered`. Live coverage today: `config.json` is missing only `defeat`; `config.example.json` is missing `defeat`, `energy_free_claim`, `login_claim`, `arena_entry`, `squad_arena_tab`, `arena_payout_claim`.

---

## Uncertain / must confirm on-device

Every item here blocks the code that depends on it. Default to **not automating** until confirmed.

| # | Question | Why it matters | How to settle it |
|---|---|---|---|
| 1 | **Does Squad Arena still exist?** Retirement announced 27 Apr 2026 ("we will be retiring Squad Arena and refreshing your quests"); community expected mid-June; the 8 Jul 2026 patch notes do not mention it. | Kills the Squad payout collector, the Squad shipments tab, and rewrites Daily Quest 6. | Open the Arenas console and look. Do not capture Squad templates first. |
| 2 | **Is the Daily Quest list 7 or 8, and what is the exact wording?** The 10-Year update added a Coliseum quest (350→300 EP each, 1,500→1,600 crate); the Apr 2026 update promised "refreshed" quests. All wiki sources are April-2025 vintage. | The whole quest-mapping table and the "residual MANUAL" report depend on it. | Screenshot the Quests panel and transcribe all rows verbatim. |
| 3 | **Is GW's SIM control present** (level 85 + 50 lifetime campaign completions), and does it require an untouched run? | Decides one-tap SIM vs a 12-node auto-battle module. The untouched-run requirement is strong inference, not documented. | Screenshot the GW screen pre- and post-completion. Recapture `gw_multisim` in **both** enabled and disabled states — today's crop was taken while GW was already done and is very likely the disabled variant. |
| 4 | **Are Mod Battles Tier 2 nodes attempt-capped?** Multiple 2026 sources say Mod nodes are unlimited, but the live run booked `hard_depleted` on Mod 2-F with Mod energy stuck at 213/144. | If it is a false positive, the `hard_depleted` skip is starving the top-priority pool. | Screenshot the Mod 2-F panel and read what replaced MULTI SIM. If it is not a genuine attempt-reset bar, restrict the `hard_depleted` skip_marker to `{light, dark, fleet}`. |
| 5 | **Is Mod Battles Tier 1 3★ / simmable post-rework?** No Tier-1 templates exist. | Moot if Tier 1 stays excluded (recommended), but blocks any future Tier-1 entry. | Visual check. |
| 6 | **Do the Fleet Challenge day rotation and the 6★-capital-ship lockout still hold?** Source is swgoh.wiki, which `TARGETS.md` itself flags as stale, and Cantina 2.0 demonstrably churned this area. | Determines whether Daily Quest 5 is completable every day and which tier to sim. | Check the Fleet Challenge screen on three different weekdays. |
| 7 | **Cantina Stage 9 node letters and Omicron placement.** Research says Omicron repeats on 9-B/9-D/9-F (not 9-A/9-E/9-G), from swgoh.gg read 2026-08-03; `TARGETS.md` says the opposite. | Wrong letters at 20 energy/battle waste the scarcest pool. Also: are 9-A/9-D/9-G already 3★? Sim needs a manual zero-death clear first. | Open Stage 9 and read each node's repeat-reward strip; note which show MULTI SIM vs only BATTLE. |
| 8 | **Is Mod Battles 2-C a T05_06 source?** Inferred from the 2-E ∩ 2-F drop overlap; never farmed. | 2-C is 14 energy vs 2-F's 18 — a 22% saving on promote pushes. | One sim + a HotUtils material diff. |
| 9 | **Is `hard_depleted` valid on Fleet?** The crop is the 💎25 first-refresh chip from LS Hard 1-D; Fleet shows 💎200 at a later ramp step, and Hard refresh prices escalate 25→50→100→200 per node per day. | The template will MISS, so the graceful skip degrades to a safe halt — acceptable, but it must never fall through to a positional tap. | Capture a second `hard_depleted` variant per price tier, or crop the countdown-timer bar (price-invariant) instead of the chip. |
| 10 | **The 5-attempt Hard-node cap** is corroborated only by this repo's live 2026-08-02 run, not an external 2026 source. | Drives every Hard-node rotation and the 600-ticket arithmetic. | Count attempts on one node. |
| 11 | **Personal reset vs guild reset offset.** Guild reset is 30 min after the *founder's* arena payout in the founder's timezone; bonus/store/attempt clocks key off Astra's own reset; the game anchors to UTC and does **not** observe DST. | A run straddling guild reset splits the 600-ticket contribution across two guild-days and fails invisibly. | Read Settings → Time Settings once, record the reset in UTC, and re-check after each DST flip. |
| 12 | **Shard-Shop conversion math**: guidance says ship blueprints convert best (4 × 19 = 76 > 5 × 15 = 75), but the GW price table lists characters at 10/400 vs blueprints at 4/400, which reverses the conclusion. | Halves or doubles the return on the largest recurring token spend. | Buy one of each at the same 400-token price and diff the Shard Store balance. |
| 13 | **Post-Cantina-2.0 store contents and prices for every token store.** All price tables cited (GET1/2/3, Raid Mk I/II/III, Fleet Arena Zeta @2,000, Cantina U-wing @400, Shard Shop 360/4) come from wiki pages last edited Apr 2025, i.e. pre-Cantina-2.0 and pre-Era-Arena. | The entire §2 phase-1 buy list. | Re-read each tab on device before enabling any buy. |
| 14 | **Does a Mk I Raid Store still exist in 2026?** Likely consolidated into the GET stores when the legacy raids sunset; the claim's own item list (Han + GK + Traya in one store) is the post-consolidation signature. | Prevents building a store module for content that no longer exists. | Look at the Shipments tab strip. |
| 15 | **Episode Currency cap behaviour at ceiling.** Sources contradict themselves: "the Track refuses to let you claim further currency bundles" vs "the overflow is silently destroyed". If unclaimed bundles simply bank, there is no urgency. | Decides whether the cap needs an auto-buy or just a report line. | Reach ~28k and observe, or read the Track UI at high balance. |
| 16 | **Coliseum daily attempt count** (5 assumed, device-observed once) and whether an attempt-exhausted state renders a crystal control. | `attempts` is pinned to 1, so low risk — but the `_steps_battle` docstring literally invites a 5-attempt config. | Exhaust attempts once and screenshot. |
| 17 | **Are Assault Battle Challenge Tiers attempt-limited with a crystal refresh**, and is there an `ab_attempts_depleted` visual? | Only relevant if the narrow AUTO_BATTLE carve-out is ever built. | Visual check during a live AB window. |
| 18 | **Proving Grounds simmability.** Reported to become simmable once 3★'d, with a history of bugs where previously-3★'d tiers showed no sim button. The only repeat is a 2,200-crystal refresh. | Would be the best monthly bot target if true. | Check during the 24h post-Conquest window. |
| 19 | **Micro Attenuator + slicing-material state is a moving target.** The "attenuators exhausted at 15" figure is 2026-07-25; the 07-31 dump reads attenuators 86, T06_02 31, T05_06 182, and the recorded calibration ROI is **0/10**. | Drives node priority (2-D vs 2-E vs 2-C) and any GET3 advice. | Re-read `data/mods_full_*.json` at the start of each session; never hardcode the bottleneck. |
| 20 | **Vane's shard source.** swgoh.gg (read 2026-08-03) lists Cantina Normal 3-B at 10 energy; `TARGETS.md:109` says he was removed from nodes in Oct 2025 and is packs/Shipments only. One of the two is wrong, and Vane is a hard GL-Hondo blocker at 2★. | Determines whether the #1 account gap has a free farm at all. | Open Cantina Stage 3 and look at 3-B's reward strip. |
