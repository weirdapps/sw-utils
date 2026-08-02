# farmbot Daily Collectors (sub-project E) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend the `farmbot/` engine from energy-only Multi-Sim to a config-driven daily routine that also auto-collects free dailies and sims Daily Challenges — PvE only, never spending crystals.

**Architecture:** Keep `EnergyDumpTask` and its entire run loop; split `_steps_for()` into per-`kind` step builders (`energy_node` extracted verbatim, plus new `collect` and `challenge_sim`). Config gains a back-compatible `routine` list where each entry has an optional `kind` (default `energy_node`). Two additive `Step` fields (`mark`, `optional_counter`) wire per-kind `Summary` counters.

**Tech Stack:** Python 3.14, stdlib + OpenCV/PIL (unchanged); pytest; device-free tests inject `look`/`tapper`/`swipe`.

**Spec:** `docs/superpowers/specs/2026-08-03-farmbot-daily-collectors-design.md`

## Global Constraints

- **Never spend premium currency.** Only *free-claim* templates are ever registered as tap targets; a crystal-cost / "buy" control is never a tap target, so it can never be pressed. (Simpler than the spec's skip_marker phrasing and strictly safer — noted deviation.)
- **Never PvP.** Arena/GAC/TW entries are `collect` on the payout button only; no battle/fight template is ever a tap target.
- **Back-compat is non-negotiable:** `_steps_energy_node` is the current `_steps_for` body *extracted verbatim*; **all 80 existing tests must stay green** after every task.
- **`farmbot/config.json` is gitignored** → all schema examples go in the committed `farmbot/config.example.json`.
- **Run tests with** `.venv/bin/python -m pytest -q` from the repo root.
- **Every commit message ends with the trailer** `Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>`.
- Counters are **disjoint**: energy sims → `sims_done`; challenge sims → `challenges_simmed` (never both).

## File Structure

- `farmbot/tasks.py` — MODIFY. Add template constants (`challenges_entry`, `challenges_menu`, `challenge_locked`); add `Step.mark` + `Step.optional_counter`; add `Summary` counters (`collected`, `challenges_simmed`, `energy_claimed`, `nothing_to_collect`); split `_steps_for` into a dispatcher + `_steps_energy_node` (verbatim) + `_steps_collect` + `_steps_challenge_sim`; wire the two new fields into the run loop.
- `farmbot/run.py` — MODIFY. `load_config` accepts `routine` **or** `nodes`; add `routine_of(cfg)`; `main`/dry-run use it; add `--daily` flag; extend `format_summary`.
- `farmbot/config.example.json` — MODIFY. Document the mixed-kind `routine` schema.
- `tests/test_farmbot_tasks.py` — MODIFY. `import pytest`; add dispatcher + collect + challenge tests.
- `tests/test_farmbot_run.py` — MODIFY. Add routine-alias, `--daily`, `format_summary`, and example-config tests.

---

### Task 1: Kind-dispatcher (extract `energy_node` verbatim)

Enabling refactor: route entries by `kind`. No energy behavior changes; the new observable behavior is that an *unknown* kind raises a clear error.

**Files:**
- Modify: `farmbot/tasks.py` (`_steps_for` at lines 110-155)
- Test: `tests/test_farmbot_tasks.py`

**Interfaces:**
- Consumes: existing `EnergyDumpTask`, `Step`, `Summary`.
- Produces: `EnergyDumpTask._steps_for(node)` dispatches on `node.get("kind","energy_node")`; `EnergyDumpTask._steps_energy_node(node)` (verbatim old body); unknown kind → `ValueError`.

- [ ] **Step 1: Add `import pytest` to the test file**

At the top of `tests/test_farmbot_tasks.py`, under `from collections import namedtuple`, add:

```python
import pytest
```

- [ ] **Step 2: Write the failing tests**

Append to `tests/test_farmbot_tasks.py`:

```python
def test_unknown_kind_raises():
    task = EnergyDumpTask([{"kind": "bogus"}], scripted_look(set()), lambda x, y: None)
    with pytest.raises(ValueError):
        task.run()


def test_explicit_energy_node_kind_still_simms():
    node = {"kind": "energy_node", "campaign": "cantina", "node": "1-A", "sim": "max"}
    task = EnergyDumpTask([node], scripted_look(FLOW), lambda x, y: None)
    assert task.run().sims_done == 1
```

- [ ] **Step 3: Run tests to verify the new one fails**

Run: `.venv/bin/python -m pytest tests/test_farmbot_tasks.py::test_unknown_kind_raises -v`
Expected: FAIL (today an unknown-kind dict hits `node['campaign']` → `KeyError`, not `ValueError`).

- [ ] **Step 4: Refactor `_steps_for` into a dispatcher + verbatim builder**

In `farmbot/tasks.py`, rename the current method `def _steps_for(self, node):` (line 110) to `def _steps_energy_node(self, node):` — **change only the method name; leave its entire body (through `return steps`) byte-for-byte unchanged.** Then add a new dispatcher directly above it:

```python
    def _steps_for(self, node):
        """Dispatch an ordered Step list by the entry's kind (default energy_node)."""
        kind = node.get("kind", "energy_node")
        builders = {
            "energy_node": self._steps_energy_node,
        }
        builder = builders.get(kind)
        if builder is None:
            raise ValueError(f"unknown routine kind: {kind!r}")
        return builder(node)
```

- [ ] **Step 5: Run the full suite (green guard + new tests pass)**

Run: `.venv/bin/python -m pytest -q`
Expected: PASS — 82 passed (80 existing + 2 new).

- [ ] **Step 6: Commit**

```bash
git add farmbot/tasks.py tests/test_farmbot_tasks.py
git commit -m "$(cat <<'EOF'
farmbot: kind-dispatcher — extract _steps_energy_node verbatim

_steps_for now routes by entry kind (default energy_node); unknown kind
raises ValueError. Energy flow unchanged (verbatim extract, 80 tests green).

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

### Task 2: `collect` kind (tap-to-collect dailies)

**Files:**
- Modify: `farmbot/tasks.py` (`Step` 57-73; `Summary` 76-85; run loop optional-branch 228-229 and tap-branch 252-262; dispatcher map from Task 1; add `_steps_collect`)
- Test: `tests/test_farmbot_tasks.py`

**Interfaces:**
- Consumes: `_steps_for` dispatcher (Task 1).
- Produces: `Step.mark: Optional[str]=None`, `Step.optional_counter: Optional[str]=None`; `Summary.collected/nothing_to_collect/energy_claimed` (ints, default 0); `EnergyDumpTask._steps_collect(node)` for `node = {"kind":"collect","nav":[str],"claim":str,["count":int],["counter":str],["scrollable":bool]}`.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_farmbot_tasks.py`:

```python
def test_collect_happy_path():
    node = {"kind": "collect", "nav": ["inbox_entry"], "claim": "login_claim"}
    present = {"home", "inbox_entry", "login_claim", "rewards", "home_button"}
    taps = []
    task = EnergyDumpTask([node], scripted_look(present), lambda x, y: taps.append((x, y)))
    s = task.run()
    assert s.halted is False
    assert s.collected == 1
    assert s.nothing_to_collect == 0
    assert len(taps) == 4        # nav + claim + reward-dismiss + home


def test_collect_nothing_to_collect_when_claim_absent():
    node = {"kind": "collect", "nav": ["inbox_entry"], "claim": "login_claim"}
    present = {"home", "inbox_entry", "home_button"}   # no claim, no reward popup
    taps = []
    task = EnergyDumpTask([node], scripted_look(present), lambda x, y: taps.append((x, y)))
    s = task.run()
    assert s.halted is False
    assert s.collected == 0
    assert s.nothing_to_collect == 1
    assert len(taps) == 2        # nav + home only (claim + reward optional-skipped)


def test_collect_count_claims_until_absent():
    node = {"kind": "collect", "nav": [], "claim": "gift_claim", "count": 3}
    present = {"home", "home_button"}
    look = scripted_look(present, sequences={"gift_claim": [True, True, False]})
    taps = []
    task = EnergyDumpTask([node], look, lambda x, y: taps.append((x, y)))
    s = task.run()
    assert s.collected == 2
    assert s.nothing_to_collect == 0     # first claim present => i==0 did not book "nothing"
    assert len(taps) == 3                # 2 claims + home


def test_collect_free_energy_books_energy_claimed():
    node = {"kind": "collect", "nav": [], "claim": "energy_free_claim", "counter": "energy_claimed"}
    present = {"home", "energy_free_claim", "home_button"}
    task = EnergyDumpTask([node], scripted_look(present), lambda x, y: None)
    s = task.run()
    assert s.energy_claimed == 1
    assert s.collected == 0


def test_collect_does_not_tap_when_only_non_free_control_present():
    # A paid/"buy" control is present but the FREE claim template is absent -> nothing collected,
    # nothing tapped except the return-home. Proves paid controls are never tap targets.
    node = {"kind": "collect", "nav": [], "claim": "store_free_claim"}
    present = {"home", "store_buy_crystals", "home_button"}
    taps = []
    task = EnergyDumpTask([node], scripted_look(present), lambda x, y: taps.append((x, y)))
    s = task.run()
    assert s.halted is False
    assert s.collected == 0
    assert s.nothing_to_collect == 1
    assert len(taps) == 1                # only RETURN_HOME
```

- [ ] **Step 2: Run to verify they fail**

Run: `.venv/bin/python -m pytest tests/test_farmbot_tasks.py -k collect -v`
Expected: FAIL (`_steps_collect` unknown kind → ValueError; `Summary` has no `collected`).

- [ ] **Step 3: Add the two `Step` fields**

In `farmbot/tasks.py`, inside the `Step` dataclass (after `skip_counter`, line 73), add:

```python
    mark: Optional[str] = None            # on a successful tap, bump this Summary counter
    optional_counter: Optional[str] = None  # when an `optional` step is skipped (absent), bump this
```

- [ ] **Step 4: Add the `Summary` counters**

In `farmbot/tasks.py`, inside the `Summary` dataclass (after `hard_depleted_nodes`, line 81), add:

```python
    collected: int = 0
    challenges_simmed: int = 0
    energy_claimed: int = 0
    nothing_to_collect: int = 0
```

- [ ] **Step 5: Wire the fields into the run loop**

In `farmbot/tasks.py`, change the optional-skip branch (currently lines 228-229):

```python
                if m is None and step.optional:
                    if step.optional_counter:
                        self._bump(s, step.optional_counter)
                    continue   # step not applicable (e.g. already on the wanted difficulty)
```

And in the tap branch, immediately after the `if step.mark_sim: s.sims_done += 1` block (line 255), add:

```python
                    if step.mark:
                        self._bump(s, step.mark)
```

- [ ] **Step 6: Add `_steps_collect` and register it in the dispatcher**

In `farmbot/tasks.py`, add `"collect": self._steps_collect,` to the `builders` dict in `_steps_for`, then add the method (place it after `_steps_energy_node`):

```python
    def _steps_collect(self, node):
        """A tap-to-collect daily: HOME -> [nav taps] -> CLAIM (skip if absent = nothing to collect)
        -> dismiss any reward popup -> RETURN_HOME. Only the FREE claim template is a tap target, so
        a crystal-cost variant is never pressed (it simply won't match). `count`>1 taps the claim
        repeatedly (stacked gifts), stopping when absent. `counter` books to a specific Summary
        field (e.g. energy_claimed); default is `collected`."""
        steps = [Step("HOME", TPL_HOME, tap=False)]
        for i, tpl in enumerate(node.get("nav", [])):
            steps.append(Step(f"NAV_{i}", tpl, scrollable=node.get("scrollable", False)))
        counter = node.get("counter", "collected")
        for i in range(node.get("count", 1)):
            steps.append(Step(f"CLAIM_{i}", node["claim"], optional=True, mark=counter,
                              optional_counter=("nothing_to_collect" if i == 0 else None)))
        steps.append(Step("COLLECT_REWARDS", TPL_REWARDS, optional=True))
        steps.append(Step("RETURN_HOME", TPL_HOME_BUTTON))
        return steps
```

- [ ] **Step 7: Run the full suite**

Run: `.venv/bin/python -m pytest -q`
Expected: PASS — 87 passed (82 + 5 new).

- [ ] **Step 8: Commit**

```bash
git add farmbot/tasks.py tests/test_farmbot_tasks.py
git commit -m "$(cat <<'EOF'
farmbot: collect kind — tap-to-collect free dailies

Adds Step.mark/optional_counter, Summary collected/nothing_to_collect/
energy_claimed, loop wiring, and _steps_collect. Only free-claim templates
are tap targets (paid controls never pressed). Idempotent: absent claim =>
nothing_to_collect, no halt.

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

### Task 3: `challenge_sim` kind (Daily Challenges via Multi-Sim)

**Files:**
- Modify: `farmbot/tasks.py` (template constants near lines 27-42; dispatcher map; add `_steps_challenge_sim`)
- Test: `tests/test_farmbot_tasks.py`

**Interfaces:**
- Consumes: `_steps_for` dispatcher; `Step.mark` (Task 2); `Summary.challenges_simmed` (Task 2).
- Produces: `EnergyDumpTask._steps_challenge_sim(node)` for `node = {"kind":"challenge_sim","challenge":<template>}`; template constants `TPL_CHALLENGES_ENTRY`, `TPL_CHALLENGES_MENU`, `TPL_CHALLENGE_LOCKED`.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_farmbot_tasks.py`:

```python
def test_challenge_sim_happy_path_disjoint_from_sims_done():
    node = {"kind": "challenge_sim", "challenge": "challenge_ability_mats"}
    present = {"home", "challenges_entry", "challenges_menu", "challenge_ability_mats",
              "multi_sim", "sim_confirm", "rewards", "home_button"}
    taps = []
    task = EnergyDumpTask([node], scripted_look(present), lambda x, y: taps.append((x, y)))
    s = task.run()
    assert s.halted is False
    assert s.challenges_simmed == 1
    assert s.sims_done == 0            # disjoint from energy sims
    assert len(taps) == 6             # open, select, multisim, confirm, rewards, home


def test_challenge_not_three_starred_skips_without_battle():
    node = {"kind": "challenge_sim", "challenge": "challenge_ability_mats"}
    present = {"home", "challenges_entry", "challenges_menu", "challenge_ability_mats",
              "challenge_locked", "home_button"}          # no multi_sim/sim_confirm
    taps, halts = [], []
    task = EnergyDumpTask([node], scripted_look(present),
                          lambda x, y: taps.append((x, y)), halt=lambda st: halts.append(st))
    s = task.run()
    assert s.halted is False
    assert halts == []
    assert s.skipped_nodes == 1
    assert s.challenges_simmed == 0
```

- [ ] **Step 2: Run to verify they fail**

Run: `.venv/bin/python -m pytest tests/test_farmbot_tasks.py -k challenge -v`
Expected: FAIL (`challenge_sim` unknown kind → ValueError).

- [ ] **Step 3: Add template constants**

In `farmbot/tasks.py`, after `TPL_HARD_DEPLETED` (line 42), add:

```python
TPL_CHALLENGES_ENTRY = "challenges_entry"  # the "Challenges" button on the hub
TPL_CHALLENGES_MENU = "challenges_menu"    # the Challenges menu is open (verify only)
TPL_CHALLENGE_LOCKED = "challenge_locked"  # a challenge not yet 3-starred: no MULTI SIM. MARKER only
                                           # (never tapped) so a real battle is never started.
```

- [ ] **Step 4: Add `_steps_challenge_sim` and register it**

In `farmbot/tasks.py`, add `"challenge_sim": self._steps_challenge_sim,` to the `builders` dict, then add the method:

```python
    def _steps_challenge_sim(self, node):
        """A Daily Challenge Multi-Sim on the Challenges screen (not the Campaigns menu). Reuses the
        sim chrome (multi_sim/sim_confirm/rewards). A challenge not yet 3-starred shows no MULTI SIM;
        if a challenge_locked marker is present we skip (never battle), else the uncaptured screen
        safe-halts. Uses mark='challenges_simmed' (not mark_sim) to stay disjoint from energy sims."""
        return [
            Step("HOME", TPL_HOME, tap=False),
            Step("OPEN_CHALLENGES", TPL_CHALLENGES_ENTRY),
            Step("CHALLENGES_MENU", TPL_CHALLENGES_MENU, tap=False),
            Step("SELECT_CHALLENGE", node["challenge"], ensure=TPL_MULTI_SIM,
                 ensure_extra=(TPL_CHALLENGE_LOCKED,), scrollable=True),
            Step("OPEN_MULTISIM", TPL_MULTI_SIM,
                 skip_marker=TPL_CHALLENGE_LOCKED, skip_tap=False, skip_counter="skipped_nodes"),
            Step("CONFIRM_SIM", TPL_SIM_CONFIRM, mark="challenges_simmed",
                 skip_marker=TPL_ENERGY_OUT, skip_tap=True, skip_counter="energy_out_nodes"),
            Step("REWARDS", TPL_REWARDS),
            Step("RETURN_HOME", TPL_HOME_BUTTON),
        ]
```

- [ ] **Step 5: Run the full suite**

Run: `.venv/bin/python -m pytest -q`
Expected: PASS — 89 passed (87 + 2 new).

- [ ] **Step 6: Commit**

```bash
git add farmbot/tasks.py tests/test_farmbot_tasks.py
git commit -m "$(cat <<'EOF'
farmbot: challenge_sim kind — Daily Challenges via Multi-Sim

Reuses the sim chrome on the Challenges screen; mark='challenges_simmed'
stays disjoint from energy sims_done. Not-3-starred challenge skips via the
challenge_locked marker (never battles); uncaptured screen safe-halts.

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

### Task 4: Config `routine`/`nodes` alias + `routine_of` helper

**Files:**
- Modify: `farmbot/run.py` (`_REQUIRED` line 19; `load_config` 31-37; add `routine_of`; `main` 110, 127; dry-run loop 109-112)
- Test: `tests/test_farmbot_run.py`

**Interfaces:**
- Consumes: existing `run.load_config`.
- Produces: `run.routine_of(cfg) -> list`; `load_config` requires `device_serial`,`caps`,`vision` and (`routine` or `nodes`).

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_farmbot_run.py`:

```python
def test_load_config_accepts_routine_key(tmp_path):
    p = tmp_path / "c.json"
    p.write_text(json.dumps({
        "device_serial": "s",
        "caps": {"max_actions": 10, "action_delay_ms": [1, 2]},
        "vision": {"match_threshold": 0.9, "step_timeout_s": 5, "energy_out_timeout_s": 1},
        "routine": [{"kind": "collect", "claim": "login_claim"}],
    }))
    cfg = run.load_config(str(p))
    assert run.routine_of(cfg)[0]["kind"] == "collect"


def test_load_config_missing_routine_and_nodes_raises(tmp_path):
    p = tmp_path / "c.json"
    p.write_text(json.dumps({
        "device_serial": "s",
        "caps": {"max_actions": 10, "action_delay_ms": [1, 2]},
        "vision": {"match_threshold": 0.9, "step_timeout_s": 5, "energy_out_timeout_s": 1},
    }))
    with pytest.raises(ValueError):
        run.load_config(str(p))


def test_routine_of_prefers_routine_over_nodes():
    assert run.routine_of({"routine": [1], "nodes": [2, 3]}) == [1]
    assert run.routine_of({"nodes": [2, 3]}) == [2, 3]
    assert run.routine_of({}) == []
```

- [ ] **Step 2: Run to verify they fail**

Run: `.venv/bin/python -m pytest tests/test_farmbot_run.py -k "routine" -v`
Expected: FAIL (`run.routine_of` does not exist; routine-only config raises on missing `nodes`).

- [ ] **Step 3: Update `_REQUIRED`, `load_config`, and add `routine_of`**

In `farmbot/run.py`, change line 19 to drop `nodes` from the strict-required tuple:

```python
_REQUIRED = ("device_serial", "caps", "vision")
```

Replace `load_config` (lines 31-37) with:

```python
def load_config(path):
    with open(path) as f:
        cfg = json.load(f)
    for key in _REQUIRED:
        if key not in cfg:
            raise ValueError(f"config missing required key: {key}")
    if "routine" not in cfg and "nodes" not in cfg:
        raise ValueError("config missing required key: routine (or nodes)")
    return cfg


def routine_of(cfg):
    """The ordered routine entries: prefer the canonical `routine`, fall back to the `nodes` alias."""
    return cfg.get("routine", cfg.get("nodes")) or []
```

- [ ] **Step 4: Point `main` and dry-run at `routine_of`**

In `farmbot/run.py`, in the dry-run block (lines 109-112) change `for n in cfg["nodes"]:` to `for n in routine_of(cfg):`. In the task construction (line 127) change `cfg["nodes"]` to `routine_of(cfg)`.

- [ ] **Step 5: Run the full suite**

Run: `.venv/bin/python -m pytest -q`
Expected: PASS — 92 passed (89 + 3 new). Existing `test_load_config_ok` (nodes) and `test_load_config_missing_key_raises` still pass.

- [ ] **Step 6: Commit**

```bash
git add farmbot/run.py tests/test_farmbot_run.py
git commit -m "$(cat <<'EOF'
farmbot: config accepts routine (or nodes alias) + routine_of helper

load_config requires device_serial/caps/vision and either routine or nodes;
main and dry-run read routine_of(cfg). Back-compat: existing nodes configs
and tests unchanged.

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

### Task 5: `--daily` flag + `format_summary` counters

**Files:**
- Modify: `farmbot/run.py` (`parse_args` 22-28; `format_summary` 78-82)
- Test: `tests/test_farmbot_run.py`

**Interfaces:**
- Consumes: `Summary` (with Task 2/3 counters).
- Produces: `run.parse_args([...]).daily` (bool); `format_summary` string includes `collected=/challenges_simmed=/energy_claimed=/nothing_to_collect=`.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_farmbot_run.py`:

```python
def test_parse_args_daily_flag():
    assert run.parse_args(["--daily"]).daily is True
    assert run.parse_args([]).daily is False


def test_format_summary_includes_collector_counts():
    out = run.format_summary(Summary(collected=3, challenges_simmed=2, energy_claimed=1,
                                     nothing_to_collect=4, stopped_reason="complete"))
    assert "collected=3" in out
    assert "challenges_simmed=2" in out
    assert "energy_claimed=1" in out
    assert "nothing_to_collect=4" in out
```

- [ ] **Step 2: Run to verify they fail**

Run: `.venv/bin/python -m pytest tests/test_farmbot_run.py -k "daily or collector" -v`
Expected: FAIL (`--daily` unknown arg; counters absent from summary string).

- [ ] **Step 3: Add the `--daily` flag**

In `farmbot/run.py` `parse_args`, after the `--dump` line (line 25), add:

```python
    p.add_argument("--daily", action="store_true",
                   help="run the full daily routine (all kinds); alias of --dump")
```

- [ ] **Step 4: Extend `format_summary`**

In `farmbot/run.py`, replace `format_summary` (lines 78-82) with:

```python
def format_summary(summary):
    return (f"nodes_attempted={summary.nodes_attempted} sims_done={summary.sims_done} "
            f"collected={summary.collected} challenges_simmed={summary.challenges_simmed} "
            f"energy_claimed={summary.energy_claimed} nothing_to_collect={summary.nothing_to_collect} "
            f"energy_out_nodes={summary.energy_out_nodes} "
            f"hard_depleted_nodes={summary.hard_depleted_nodes} skipped_nodes={summary.skipped_nodes} "
            f"halted={summary.halted} halt_state={summary.halt_state} reason={summary.stopped_reason}")
```

- [ ] **Step 5: Run the full suite**

Run: `.venv/bin/python -m pytest -q`
Expected: PASS — 94 passed (92 + 2 new). Existing `test_format_summary_mentions_counts` still passes ("2","5","complete" still present).

- [ ] **Step 6: Commit**

```bash
git add farmbot/run.py tests/test_farmbot_run.py
git commit -m "$(cat <<'EOF'
farmbot: --daily flag + per-kind counters in the run summary

format_summary now reports collected/challenges_simmed/energy_claimed/
nothing_to_collect/skipped_nodes alongside the existing energy counts.

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

### Task 6: Document the schema in `config.example.json`

**Files:**
- Modify: `farmbot/config.example.json`
- Test: `tests/test_farmbot_run.py`

**Interfaces:**
- Consumes: `run.load_config`, `run.routine_of`.
- Produces: a committed mixed-kind example config that stays valid.

- [ ] **Step 1: Write the failing test**

Append to `tests/test_farmbot_run.py`:

```python
def test_example_config_is_valid_and_mixed_kind():
    import os
    path = os.path.join(os.path.dirname(run.__file__), "config.example.json")
    cfg = run.load_config(path)
    kinds = {e.get("kind", "energy_node") for e in run.routine_of(cfg)}
    assert {"energy_node", "collect", "challenge_sim"} <= kinds
```

- [ ] **Step 2: Run to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_farmbot_run.py::test_example_config_is_valid_and_mixed_kind -v`
Expected: FAIL (the current example has only `nodes` energy entries — no `collect`/`challenge_sim`).

- [ ] **Step 3: Rewrite `config.example.json`**

Replace the entire contents of `farmbot/config.example.json` with (strict JSON — descriptions use `for` fields, not comments):

```json
{
  "device_serial": "emulator-5554",
  "caps": { "max_actions": 400, "action_delay_ms": [700, 1800] },
  "vision": { "match_threshold": 0.88, "step_timeout_s": 10.0, "energy_out_timeout_s": 2.0 },
  "routine": [
    { "kind": "energy_node", "campaign": "cantina", "chapter": 1, "node": "1-A", "sim": "max", "for": "Cantina energy dump (kind optional; energy_node is the default)" },
    { "kind": "collect", "name": "login_reward", "nav": ["inbox_entry"], "claim": "login_claim", "for": "daily login calendar reward" },
    { "kind": "collect", "name": "arena_payout_squad", "nav": ["arena_entry", "squad_arena_tab"], "claim": "arena_payout_claim", "for": "squad arena daily payout (collect-only, never battles)" },
    { "kind": "collect", "name": "free_energy", "nav": [], "claim": "energy_free_claim", "counter": "energy_claimed", "count": 2, "for": "timed free-energy grants; books to energy_claimed; skipped if not yet available" },
    { "kind": "challenge_sim", "challenge": "challenge_ability_mats", "for": "daily ability-mat challenge, Multi-Sim (needs 3 stars)" }
  ]
}
```

- [ ] **Step 4: Run the full suite**

Run: `.venv/bin/python -m pytest -q`
Expected: PASS — 95 passed (94 + 1 new).

- [ ] **Step 5: Commit**

```bash
git add farmbot/config.example.json tests/test_farmbot_run.py
git commit -m "$(cat <<'EOF'
farmbot: document mixed-kind routine schema in config.example.json

Example now shows energy_node + collect + challenge_sim entries; a test
loads it to keep the example valid as the schema evolves.

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Post-implementation (live, not codeable here)

These are supervised on-device steps for after the code lands — the engine safe-halts on any
uncaptured template, so nothing runs blindly:

1. **Capture templates** (browser/ADB capture flow, unselected where relevant): `inbox_entry`,
   `login_claim`, `store_entry`, `store_free_claim`, `gift_claim`, `achievements_claim`,
   `arena_entry`, `squad_arena_tab`, `fleet_arena_tab`, `arena_payout_claim`, `energy_free_claim`,
   `challenges_entry`, `challenges_menu`, the challenge icons, and (for graceful skip) `challenge_locked`.
2. **Wire the local `farmbot/config.json`** (gitignored) with the real collect + challenge_sim
   entries, mirroring `config.example.json`.
3. **Validate live** with `.venv/bin/python -m farmbot.run --dry-run` then `--daily`, confirming
   crystals unchanged and no PvP battle ever started.
4. **Update `memory/notes.md`** with a session record + point the daily routine at the captured set.

## Self-Review

**1. Spec coverage:**
- §3 generalize runner → Tasks 1-3. §4 config routine/nodes + kind default → Tasks 1, 4, 6.
- §5 three step builders → Tasks 1 (energy verbatim), 2 (collect), 3 (challenge_sim). §5 counter
  wiring (`mark`, `optional_counter`) → Task 2. §6 idempotency (`nothing_to_collect`) → Task 2.
- §6 run model / `--daily` → Task 5. §7 safety (free-only tap targets; never PvP) → Task 2 test
  `..._only_non_free_control_present`; challenge never-battle → Task 3 test. §8 templates →
  Post-implementation §1. §10 reporting → Task 5. §11 tests → each task's tests. ✅ all covered.

**2. Placeholder scan:** No TBD/TODO; every code + test step shows real content. ✅

**3. Type consistency:** `_steps_for`/`_steps_energy_node`/`_steps_collect`/`_steps_challenge_sim`,
`Step.mark`/`Step.optional_counter`, `Summary.collected`/`challenges_simmed`/`energy_claimed`/
`nothing_to_collect`, and `run.routine_of` are named identically across the tasks that define and
consume them. Counters are disjoint (`sims_done` vs `challenges_simmed`) per Global Constraints. ✅

**Cumulative test count:** 80 → 82 → 87 → 89 → 92 → 94 → 95.
