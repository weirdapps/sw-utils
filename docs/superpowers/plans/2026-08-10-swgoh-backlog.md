<!-- MOVED HERE 2026-08-12 from ~/Downloads so it is not lost with the scratch dir.

     EXECUTION STATUS UNKNOWN. This plan was written on 2026-08-10 by an earlier
     session and I did not run it, so I cannot say which of its tasks landed.
     Check `git log --since=2026-08-10` and the checkboxes below before assuming
     anything is outstanding. Recorded for the content, not as a work queue.
-->

# SWGOH Backlog Implementation Plan (2026-08-10)

> **For agentic workers:** Steps use checkbox (`- [ ]`) syntax for tracking. Execute task-by-task,
> stop at each **GATE** for owner review.

**Goal:** Close the three open threads left by the 2026-08-10 night session — the farmbot's wasted
fleet node, the undocumented Mace Windu event attempt, and the failed Jedi Master Mace Windu unlock —
plus the day's dailies.

**Architecture:** Three independent workstreams, ordered by *risk and device dependency*, not by size.
Documentation first (zero risk, no emulator). Then the farmbot config change (small, reversible, has a
test suite and a `--doctor` preflight). Then dailies (routine). Then the potency rebuild + event retry
(highest risk: it moves mods off a live GAC/TW defense squad, and the event costs real time to drive
by hand).

**Tech Stack:** Python 3.14 + pytest · OpenCV template matching (`farmbot/vision.py`) · ADB over
`127.0.0.1:5555` (BlueStacks) · `~/Downloads/sw.sh` for manual taps · HotUtils web API + Grandivory
optimizer (Chrome DevTools MCP).

---

## Global Constraints

- **Never spend crystals.** Astra holds 💎1,855. Not for energy refreshes, not for Electrium Conductor,
  not for the 💎25 hard-node refresh. This rail is absolute.
- **Never commit a HotUtils session id.** They are ephemeral; recapture each session per
  `scripts/browser_recipes.md` §4.
- **`account/refresh` kicks the live game client** (`CONNECTION LOST → RELOAD`). Do every HotUtils
  refresh *before* device work, never during.
- **Amplify / upgrade taps must be spaced ≥ 7s** — the success animation swallows input for 5–6s.
- **Screenshot before every blind tap.** The client drifts between screens unprompted; a stray tap on
  the Squad Arena screen starts a battle.
- Auto-battle is allowed for arena and raids. It is **not** allowed for Legendary events — it does not
  drive them (verified 2026-08-10).

---

## File Structure

| File | Responsibility | Task |
|---|---|---|
| `memory/notes.md` | Durable knowledge base. Append-only, dated sections. | 1, 5 |
| `farmbot/templates/node_fleet_2-E.png` | **NEW.** Unselected 2-E node icon for template nav. | 2 |
| `farmbot/config.json:128-136` | The `campaign: fleet` routine entry. | 2 |
| `scripts/potency_build.py` | **NEW.** Offline solver: best achievable potency per unit from the live mod dump. | 4 |
| `tests/test_potency_build.py` | **NEW.** Unit tests for the solver. | 4 |
| `output/hu_account_fresh.json` | Live mod + unit dump (2,330 mods, 397 units). Read-only input. | 4 |

---

## Facts already established (do not re-derive)

**Event — "Beset on all Sides" (Jedi Master Mace Windu, Legendary):**
gating units are 7★ **R5+** CX-2, Scorch, Depa Billaba, Temple Guard. All four are owned and above the
floor. There is **no published hard potency threshold**; community consensus is ~90–100 % effective
potency on Scorch for the Bad Batch tier. The event lives in the **Journey Guide — no deadline.**

| unit | baseId | stars | gear | relic | **potency now** |
|---|---|---|---|---|---|
| RC-1262 "Scorch" | `SCORCH` | 7★ | G13 | R7 | **36.0 %** |
| CX-2 | `OPERATIVE` | 7★ | G13 | R7 | **37.5 %** |
| Depa Billaba | `DEPABILLABA` | 7★ | G13 | R6 | 70.1 % |
| Temple Guard | `VANGUARDTEMPLEGUARD` | 7★ | G13 | R6 | 42.9 % |
| Mace Windu | `MACEWINDU` | 7★ | G13 | R7 | 91.6 % |

**Why Scorch is at 36 %:** he wears **4× Defense set + 1 crit-chance + 1 tenacity**, with a Defense%
primary on the cross and **not one potency secondary**. CX-2 wears **6× Health set**, Health% cross,
two tiny potency secondaries (1.62 % + 1.83 %). Neither has ever been modded for the stat.

**Inventory is not the constraint:**
- **184 potency-set mods** (178 at level 15) — **26 unassigned**
- **74 potency-primary crosses** — **7 unassigned**

**The cost side — this is the trade-off to accept before starting Task 4:**
`SCORCH` + `OPERATIVE` are both in **5v5 defense squad #3** and **TW defense #3**
(Lord Vader / Appo / Disguised Clone Trooper / CX-2 / Scorch). Re-modding them for potency degrades a
live GAC and TW wall until the mods are restored.

**The payoff:** `JEDIMASTERMACEWINDU` appears **three times in `data/board_result.json`'s `gaps` lists**
(5v5 offense, 3v3 defense, 3v3 offense). Unlocking him is not a collection trophy — the board planner
already wants him.

⚠️ **Do NOT reach for a full Grandivory re-run.** Measured 2026-08-08: ~1,473 mod moves, **−7.4M
credits**, and a global set-value change inside the noise (±0.12 %). For two characters that is the
wrong hammer. Task 4 uses a **restricted selection with `lockUnselectedCharacters: true`.**

---

## Task 1: Record the Mace Windu session in `memory/notes.md`

The 03:53–04:45 block produced real, hard-won knowledge that exists **only** in the assistant's
auto-memory. The repo's own convention (`CLAUDE.md`: "notes.md is the territory") means anything not
written there is invisible to the next session. Zero risk, no emulator — do it first.

**Files:**
- Modify: `memory/notes.md` (append after line 2349, the current end)

**Interfaces:**
- Produces: a dated `## 2026-08-10 (early morning)` section that Task 5 will extend with the retry outcome.

- [ ] **Step 1: Append the section**

Append verbatim to the end of `memory/notes.md`:

```markdown
## 2026-08-10 (early morning) — the Mace Windu Legendary, and why auto-battle cannot play it

First attempt at **"Beset on all Sides"** (Jedi Master Mace Windu, Legendary) Tier I. **Lost.**
The event sits in the **Journey Guide with no deadline**, so this costs nothing but time — but four
hours went into diagnosing things that were never bugs, and that is what this section is for.

### ⭐ Auto-battle does NOT drive Legendary events
The top-left toggle turns green and the sim still waits for a manual ability tap **every single turn**.
Budget for turn-by-turn driving. This is the exception to [[arena-autobattle-allowed]] — auto is fine
for arena and raids, and useless here.

### ⭐ A battle that never advances is waiting for input, not hung
Idle animations keep playing and the pause menu still opens, so "UI responds but nothing happens" is
**not** evidence of a crash. One force-restart was spent proving this — and the restart then hit an
asset-load failure, costing a re-entry through the Journey Guide. Do not force-stop the client over a
stalled sim.

### ⭐ The CANCEL trap — abilities are two-step, and blind-cycling looks exactly like a freeze
Tap ability → tap target. Some abilities fire immediately; others enter a targeting mode showing
`Select an ally.` / `Select an enemy.` **The selected ability's own slot becomes CANCEL.** So cycling
the ability positions blind just selects-then-cancels forever, which is visually identical to a hang.
Always resolve the target before tapping another slot.
- Valid targets in targeting mode carry green `»` `«` chevrons beside their health bars.
- **Ability bar is right-aligned at y=985:** three abilities → x = 1245 / 1545 / 1845; two abilities →
  x = 1645 / 1845. Rightmost is usually the strongest special.
- **Long-press to read a tooltip:** `adb shell input swipe X Y X Y 1000`. Fastest way to learn an
  unfamiliar loaned/event unit's kit in context. Tap empty ground (~300,900) to dismiss.
- Retreat is free: gear (65,65) → RETREAT (955,715) → YES (713,771).

### Two "rendering bugs" that were game mechanics
- **Dithered / stippled semi-transparent figures are Stealthed units**, not broken models.
- The **dark silhouettes are civilian markers** for the tier objective, not unloaded textures.

### The objective is the fight — Scorch Entrenched is the counter
Tier I is not a damage race: the win condition is **preventing the Bad Batch rescue**. That makes
**Scorch's Entrenched (taunt + Bulwark)** the mechanic that matters, with CX-2's Disarm behind it.

### ⭐ Why it was lost: potency, measured
Scorch **36.0 %** and CX-2 **37.5 %** against a community target of ~90–100 % for this tier. The
debuffs — Scorch's DoTs and Off-Balance, CX-2's Disarm — simply do not land. Root cause is modding, not
relics: **Scorch wears 4× Defense set with a Defense% cross and not one potency secondary**; CX-2 wears
6× Health set. Neither has ever been modded for the stat.
Inventory is not the constraint — **184 potency-set mods (26 unassigned) and 74 potency-primary crosses
(7 unassigned)** are already owned.

⇒ Retry is a **modding** job, not a farming job. See the next section.
```

- [ ] **Step 2: Verify the markdown renders and no heading level is wrong**

Run: `grep -n '^## 2026-08-10' memory/notes.md`
Expected: two hits — the existing `(night)` sections and the new `(early morning)` one.

- [ ] **Step 3: Commit**

```bash
git add memory/notes.md
git commit -m "notes: the Mace Windu Legendary attempt — auto-battle, the CANCEL trap, and the potency root cause"
```

**GATE 1 — show the owner the diff before moving on.**

---

## Task 2: Swap the farmbot's fleet node from 1-E to 2-E

`1-E` is confirmed waste: its only shard slot drops Resistance X-wing, already 7★. `2-E` (Jakku) drops
**Raven's Claw** blueprints at 76/100 — 24 from 7★, which is the nearest marginal **RotE operations
slot** (~733,000 TP). Nav is template-matched, so the config change **must not** ship without the
template or the entry halts every run.

**Files:**
- Create: `farmbot/templates/node_fleet_2-E.png`
- Modify: `farmbot/config.json:128-136`

**Interfaces:**
- Consumes: nothing.
- Produces: template name `node_fleet_2-E` — resolved by `farmbot/tasks.py` as
  `node_<campaign>_<id>`, i.e. campaign `fleet` + node `2-E`.

- [ ] **Step 1: Bring the emulator up and confirm ADB**

```bash
adb devices
```
Expected: `127.0.0.1:5555   device`. If empty, start BlueStacks and
`adb connect 127.0.0.1:5555`.

- [ ] **Step 2: Navigate to the Fleet HARD chapter-2 map and screenshot**

Hub → Campaigns → Fleet → **Hard** tab → **chapter 2** tab. Screenshot with
`~/Downloads/sw.sh shot`.
⚠️ Leave **2-E unselected** — `node_dark_8-B` ships a separate `_sel` variant precisely because a
selected node renders differently. A crop taken selected will not match on a fresh run.

- [ ] **Step 3: Capture the crop**

```bash
python3 -m farmbot.run --capture
```
At the prompts: name `node_fleet_2-E`, then the box as `left,top,right,bottom` read off the
screenshot. Crop around the node **glyph and its label**, not flat background texture — `--doctor`
rejects low-variance crops (`std < 25`).

- [ ] **Step 4: Verify the template actually matches before touching the config**

```bash
python3 -m farmbot.run --doctor
```
Expected: `node_fleet_2-E` present, no missing-template failure, no low-variance warning.

- [ ] **Step 5: Edit the config entry**

In `farmbot/config.json`, replace the `campaign: fleet` entry (currently lines 128-136):

```json
    {
      "kind": "energy_node",
      "campaign": "fleet",
      "difficulty": "hard",
      "chapter": 2,
      "node": "2-E",
      "sim": "max",
      "for": "Fleet energy. Device-confirmed 2026-08-10 by reading the reward panels: 2-E 'Jakku' drops Kyle Katarn x2, Raven's Claw x1, Mk III x2, Mk VI x2 for 20 energy. It replaces 1-E, whose only shard slot was Resistance X-wing at 7 stars already — dead shards. Raven's Claw sits at 76/100 blueprints and 7 stars gates a RotE operations slot worth ~733,000 TP, which makes this the highest-value fleet node on the board. Measured drop rate is ~1 blueprint per 5 sims (a 5x MULTI SIM returned 6x Kyle Katarn and 1x Raven's Claw), so ~24 days of daily 5-sims to reach 7 stars. Hard nodes cap at 5 attempts/day (5 x 20 = 100 energy) before a crystal refresh, so do NOT plan a 144-energy dump through this node alone."
    },
```

- [ ] **Step 6: Run the test suite**

```bash
python3 -m pytest tests/ -q
```
Expected: all pass. `tests/test_farmbot_tasks.py` covers node-step construction; a malformed entry
fails here rather than on the device.

- [ ] **Step 7: Dry-run the routine**

```bash
python3 -m farmbot.run --dry-run
```
Expected: the fleet entry prints as chapter-2 / node 2-E with a `hard_tab` step, and taps nothing.

- [ ] **Step 8: Commit**

```bash
git add farmbot/templates/node_fleet_2-E.png farmbot/config.json
git commit -m "farmbot: fleet node 1-E -> 2-E, the only fleet node with a live shard slot"
```

**GATE 2 — do not start Task 3 until `--doctor` and `pytest` are both green.**

---

## Task 3: Run the day's dailies

Nothing has been run since ~02:00. This is the routine path and it validates Task 2 live: the fleet
entry either navigates to 2-E or halts with a screenshot in `farmbot/halts/`.

**Files:** none modified (report only).

- [ ] **Step 1: Run the daily routine**

```bash
python3 -m farmbot.run --daily --report output/daily_$(TZ='Europe/Athens' date '+%Y%m%d').md
```
`--daily` isolates a bad entry instead of aborting the rest.

- [ ] **Step 2: Check for halts**

```bash
ls -la --sort=modified farmbot/halts/ | tail -5
```
Any file newer than the run start is a halt — open it and read the screen before re-running.

- [ ] **Step 3: Confirm the fleet entry hit 2-E**

Read the generated report. Expected: the fleet node step completed, not halted. If it halted at
`SELECT_NODE`, the crop from Task 2 is wrong — recapture, do not lower `vision.match_threshold`
(0.85 is load-bearing; below ~0.7 the Conquest matcher replays cleared nodes).

- [ ] **Step 4: Play the one battle the bot will never play**

One Squad or Fleet Arena battle, by hand — the only daily quest with no code path. Auto-battle is
allowed here.

**GATE 3 — report dailies completed (n/8) and any halt.**

---

## Task 4: Build a potency loadout for Scorch and CX-2

The retry is gated on one stat. Solve it offline first so the device work is a single applied move,
not a guessing loop.

**Files:**
- Create: `scripts/potency_build.py`
- Create: `tests/test_potency_build.py`
- Read: `output/hu_account_fresh.json`

**Interfaces:**
- Consumes: the HotUtils dump schema — `d['data']['mods']['mods']` (each mod has `setId`, `slot`,
  `rarity`, `level`, `primaryStat.stat.unitStatId`, `secondaryStat[].stat.unitStatId`,
  `secondaryStat[].stat.statValueDecimal`, and `unit`, which is a **dict or null**, not a string);
  `d['data']['units']['units']` (each has `baseId`, `stats.potency`).
- Produces:
  - `potency_of(mod) -> float` — the potency percentage a single mod contributes via primary + secondaries.
  - `best_loadout(mods, donor_ok) -> dict` — `{slot: mod_id}` for slots 1..6, maximising potency.
  - `projected_potency(unit, loadout, mods) -> float` — base potency (unit total minus current mod
    contribution) plus the new loadout's contribution plus set bonuses.

**Constants (SWGOH `unitStatId` enum — do not guess these again):**
`5` = Speed · `17` = **Potency %** · `18` = Tenacity % · `48` = Offense % · `49` = Defense % ·
`53` = Crit Chance % · `55` = Health % · `56` = Protection %.
**`setId` 7 = Potency set**, 2 mods per set, and only slot **7 (cross)** can carry a potency **primary**.

- [ ] **Step 1: Write the failing test**

Create `tests/test_potency_build.py`:

```python
import pytest
from scripts.potency_build import potency_of, POTENCY_STAT_ID, POTENCY_SET_ID


def _mod(primary, secondaries, set_id=1, slot=2):
    return {
        "setId": str(set_id),
        "slot": slot,
        "primaryStat": {"stat": {"unitStatId": primary, "statValueDecimal": 2400}},
        "secondaryStat": [
            {"stat": {"unitStatId": s, "statValueDecimal": v}} for s, v in secondaries
        ],
    }


def test_potency_primary_counts_in_percent():
    # statValueDecimal is scaled by 100: 2400 -> 24.00%
    assert potency_of(_mod(POTENCY_STAT_ID, [], slot=7)) == pytest.approx(24.0)


def test_non_potency_primary_contributes_nothing():
    assert potency_of(_mod(48, [])) == pytest.approx(0.0)


def test_potency_secondaries_accumulate():
    mod = _mod(48, [(POTENCY_STAT_ID, 162), (POTENCY_STAT_ID, 183), (5, 140000)])
    assert potency_of(mod) == pytest.approx(3.45)
```

- [ ] **Step 2: Run it and watch it fail**

```bash
python3 -m pytest tests/test_potency_build.py -v
```
Expected: `ModuleNotFoundError: No module named 'scripts.potency_build'`.

- [ ] **Step 3: Implement `potency_of`**

Create `scripts/potency_build.py` with the constants and:

```python
POTENCY_STAT_ID = 17
POTENCY_SET_ID = 7
_SCALE = 100.0  # statValueDecimal is the percentage x100


def potency_of(mod):
    """Potency percentage points this one mod contributes (primary + secondaries)."""
    total = 0.0
    prim = mod["primaryStat"]["stat"]
    if prim["unitStatId"] == POTENCY_STAT_ID:
        total += prim["statValueDecimal"] / _SCALE
    for sec in mod.get("secondaryStat", []):
        if sec["stat"]["unitStatId"] == POTENCY_STAT_ID:
            total += sec["stat"]["statValueDecimal"] / _SCALE
    return total
```

- [ ] **Step 4: Run the tests green**

```bash
python3 -m pytest tests/test_potency_build.py -v
```
Expected: 3 passed.

- [ ] **Step 5: Add the loadout solver and its tests**

Extend both files with `best_loadout` (greedy per slot over candidate mods, preferring `setId == 7`
so full sets form, then by `potency_of` descending) and `projected_potency` (adds 15 % per completed
potency set at max level, 10 % otherwise). Test: a pool of six potency-set mods yields three
completed sets and a projection above the input base.

- [ ] **Step 6: Run it against live data and print the verdict**

```bash
python3 scripts/potency_build.py --unit SCORCH --unit OPERATIVE \
    --dump output/hu_account_fresh.json --donors unassigned
```
Expected output: for each unit, current potency, projected potency, and the mod list, split into
*unassigned* mods (free to take) and *donor* mods (must be stripped from a named unit).

**DECISION POINT — bring this to the owner:**
- If **unassigned-only** clears ~90 %, take it. No live squad is touched, and the whole trade-off above
  evaporates.
- If it needs donors, the plan pulls from units that appear in **no** `board_result.json` squad. Only
  if that still falls short does 5v5 defense #3 get disturbed — and that is the owner's call, not mine.

- [ ] **Step 7: Apply the loadout**

Drive the Grandivory optimizer at `hotutils.com/mods/optimizer` per `memory/notes.md`
"Driving Grandivory head-lessly":
1. Refresh HotUtils **before** any device work (`account/refresh` kicks the live client).
2. Open the iframe `src` standalone.
3. In IndexedDB `ModsOptimizer → profiles[0]`, confirm
   **`globalSettings.lockUnselectedCharacters === true`** — it has defaulted to `false` before and an
   optimise then strips mods off unselected characters.
4. Set `selectedCharacters` to `SCORCH` and `OPERATIVE` only, each with a potency-weighted target.
5. "Optimize my mods!" (the **`!`** button, not the nav tab) → **"Move mods in-game"** →
   the confirm modal's **"Move my mods"** (the first button only opens the modal).
6. If it errors `Row not found`, HotUtils data is stale → "Fetch my data" → re-optimise → retry.
   Partial applies persist.

- [ ] **Step 8: Verify on live data, not on the projection**

Re-pull the account dump and assert the real numbers:

```bash
python3 -c "
import json
d=json.load(open('output/hu_account_fresh.json'))['data']
for u in d['units']['units']:
    if u['baseId'] in ('SCORCH','OPERATIVE'):
        print(u['baseId'], u['stats']['potency'])
"
```
Expected: both materially above 36/37.5 %, ideally ≥ 90 %. **Do not proceed to Task 5 on a projection.**

- [ ] **Step 9: Commit**

```bash
git add scripts/potency_build.py tests/test_potency_build.py
git commit -m "potency_build: solve the best potency loadout from the live mod dump"
```

**GATE 4 — report measured before/after potency and exactly which units gave up mods.**

---

## Task 5: Retry "Beset on all Sides" Tier I

**Files:**
- Modify: `memory/notes.md` (extend the Task 1 section with the outcome)

- [ ] **Step 1: Confirm the loadout is live in the client**

Open Scorch in-game and read the potency on his stat panel. HotUtils and the client have disagreed
before (Starkiller read R8 in one and R9 in the other).

- [ ] **Step 2: Enter via the Journey Guide**

Not via Events — the restart on 2026-08-10 required a Journey Guide re-entry.

- [ ] **Step 3: Drive the battle by hand**

Auto-battle will not play it. Per turn: screenshot → identify the ability → tap → **resolve the
target** (green `»«` chevrons) before tapping anything else. Ability bar y=985; three abilities at
x = 1245 / 1545 / 1845.
Opening line: **Scorch Entrenched** (taunt + Bulwark) to absorb the first AoE and deny the rescue,
CX-2 Disarm behind it.

- [ ] **Step 4: Book the outcome**

Win → continue to Tier II. Loss → retreat (gear 65,65 → RETREAT 955,715 → YES 713,771), record the
*measured* reason, and stop. It is free to retry; it is not free to guess.

- [ ] **Step 5: Append the outcome to `memory/notes.md` and commit**

```bash
git add memory/notes.md
git commit -m "notes: Beset on all Sides Tier I retry outcome"
```

**GATE 5 — outcome reported before any mod restoration.**

---

## Task 6: Restore the board and ship

- [ ] **Step 1: Restore the mods** *(only if Task 4 took mods from a board squad)*

Re-run Grandivory with the normal priority order and `lockUnselectedCharacters: true`. Verify
5v5 defense #3 (Lord Vader / Appo / Disguised Clone Trooper / CX-2 / Scorch) is back to its prior
speeds before the next GAC lock.

- [ ] **Step 2: Full test suite**

```bash
python3 -m pytest tests/ -q
```

- [ ] **Step 3: Open the PR**

```bash
git log --oneline master..HEAD
gh pr create --title "Fleet node 2-E, the Mace Windu potency root cause, and a potency solver" --body "..."
```

---

## Open risks

1. **The potency target is community consensus, not a published number.** ~90–100 % is a guide's
   report, not a game constant. If the retry still fails at 95 %, the cause is elsewhere (turn order,
   the rescue timer, RNG on who is stealthed) — do not just keep adding potency.
2. **The 2-E crop may need two attempts.** The unselected-vs-selected distinction has bitten this repo
   before (`node_dark_8-B_sel`).
3. **Electrium Conductor is untouched by this plan.** The relic band stays blocked until Conquest
   Ascension (~21:00 today) or the Guild Event (~22:00) pays out. Nothing here changes that, and no
   crystal purchase will.
