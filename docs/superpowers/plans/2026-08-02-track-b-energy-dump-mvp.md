# Track B — Energy-Dump MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a supervised macro that drives native in-game **sim** of already-3★ SWGOH nodes through an Android emulator, spending the day's current energy with no manual tapping and halting safely on any unknown screen.

**Architecture:** New `farmbot/` package. All device I/O is isolated behind `adb.py` (ADB subprocess wrappers) and `vision.py` (OpenCV template matching). `tasks.py` holds an `EnergyDumpTask` state machine that consumes *injected* perception/tap interfaces, so it is fully unit-testable with no device. `run.py` is the CLI orchestrator (config, caps, kill-switch, summary). `capture.py` bootstraps reference templates.

**Tech Stack:** Python 3.14 (`.venv`), OpenCV (`opencv-python-headless`), Pillow, NumPy, pytest. Android platform-tools (`adb`) + BlueStacks Air (Apple Silicon).

## Global Constraints

- **PvE only** — energy-dump (sim 3★ nodes) only. No GW/challenges/PvP in this MVP.
- **Never spend crystals** — dump current energy then stop. No auto energy-refresh.
- **Never blind-tap** — every tap is gated by a successful template match (relative-to-match offsets only).
- **Halt-on-unknown** — unexpected screen or state timeout → STOP, save `farmbot/halts/<ts>_<state>.png`, exit non-zero.
- **Dual kill-switch** — SIGINT (Ctrl-C) + a `farmbot/STOP` file flag polled each step. Plus a hard `max_actions` cap.
- **Device I/O isolated** — only `adb.py`/`vision.py` touch the device/OpenCV; everything else takes injected interfaces.
- **Tests deterministic, no live device** — mock `subprocess.run` in adb tests; synthesize images with NumPy; drive the state machine with fakes.
- **Run tests with:** `.venv/bin/pytest tests/ -q` (from repo root).
- **Match type:** `Match(cx: int, cy: int, confidence: float)` — `cx,cy` = center of the matched region (the tap point). Defined in `farmbot/vision.py`; used everywhere.

---

### Task 1: Scaffold package, deps, test path

**Files:**
- Create: `farmbot/__init__.py`
- Create: `farmbot/requirements.txt`
- Create: `farmbot/config.example.json`
- Create: `farmbot/templates/.gitkeep`
- Modify: `tests/conftest.py` (add repo root to `sys.path`)
- Modify/Create: `.gitignore` (append farmbot runtime paths)
- Test: `tests/test_farmbot_scaffold.py`

**Interfaces:**
- Consumes: nothing.
- Produces: importable `farmbot` package; `.venv` has `cv2`, `PIL`, `numpy`; `tests/conftest.py` puts repo root on `sys.path` so `from farmbot.X import Y` works.

- [ ] **Step 1: Create the package marker**

Create `farmbot/__init__.py`:
```python
"""farmbot — supervised PvE energy-dump macro (Track B MVP). PvE only; never PvP."""
```

- [ ] **Step 2: Declare dependencies**

Create `farmbot/requirements.txt`:
```text
opencv-python-headless>=4.10
pillow>=10.4
numpy>=1.26
```

- [ ] **Step 3: Install deps into the venv**

Run: `.venv/bin/pip install -r farmbot/requirements.txt`
Expected: installs `cv2`, `PIL`, `numpy`. If no `opencv-python-headless` wheel exists for Python 3.14, fall back to `pip install opencv-python-headless --pre`; if still unavailable, use `opencv-python` (full) — the code uses no GUI calls, so either works.

- [ ] **Step 4: Make the repo root importable in tests**

Modify `tests/conftest.py` — append below the existing `scripts` line:
```python
# Make the repo root importable so `from farmbot.X import Y` resolves.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
```

- [ ] **Step 5: Add an example config**

Create `farmbot/config.example.json`:
```json
{
  "device_serial": "emulator-5554",
  "caps": { "max_actions": 400, "action_delay_ms": [700, 1800] },
  "vision": { "match_threshold": 0.88, "step_timeout_s": 10.0, "energy_out_timeout_s": 2.0 },
  "nodes": [
    { "campaign": "cantina", "node": "5-D", "sim": "max" },
    { "campaign": "dark", "difficulty": "hard", "node": "6-E", "sim": "max" }
  ]
}
```

- [ ] **Step 6: Keep the templates dir; ignore runtime output**

Create `farmbot/templates/.gitkeep` (empty file). Append to `.gitignore` (create it if absent):
```gitignore
# farmbot runtime
farmbot/halts/
farmbot/config.json
farmbot/STOP
```

- [ ] **Step 7: Write the smoke test**

Create `tests/test_farmbot_scaffold.py`:
```python
import json
import os
import farmbot  # noqa: F401


def test_package_imports():
    assert farmbot.__doc__


def test_example_config_is_valid_json():
    root = os.path.join(os.path.dirname(__file__), "..")
    with open(os.path.join(root, "farmbot", "config.example.json")) as f:
        cfg = json.load(f)
    assert cfg["device_serial"]
    assert cfg["caps"]["max_actions"] > 0
    assert isinstance(cfg["nodes"], list) and cfg["nodes"]
```

- [ ] **Step 8: Run it**

Run: `.venv/bin/pytest tests/test_farmbot_scaffold.py -v`
Expected: PASS (2 tests). Also confirm deps import: `.venv/bin/python -c "import cv2, PIL, numpy; print('ok')"` → `ok`.

- [ ] **Step 9: Commit**

```bash
git add farmbot/__init__.py farmbot/requirements.txt farmbot/config.example.json farmbot/templates/.gitkeep tests/conftest.py .gitignore tests/test_farmbot_scaffold.py
git commit -m "farmbot: scaffold package, deps, and test import path"
```

---

### Task 2: `adb.py` — device I/O wrappers

**Files:**
- Create: `farmbot/adb.py`
- Test: `tests/test_farmbot_adb.py`

**Interfaces:**
- Consumes: nothing (wraps the `adb` binary via an injected `runner`, default `subprocess.run`).
- Produces:
  - `ADB(serial: str, runner=subprocess.run)`
  - `ADB.device_ready() -> bool`
  - `ADB.screencap() -> PIL.Image.Image`
  - `ADB.tap(x: int, y: int) -> None`
  - `ADB.swipe(x1, y1, x2, y2, ms=300) -> None`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_farmbot_adb.py`:
```python
import io
from PIL import Image
from farmbot.adb import ADB


class FakeCompleted:
    def __init__(self, stdout=b"", returncode=0):
        self.stdout = stdout
        self.returncode = returncode


def _png_bytes(w=4, h=3, color=(10, 20, 30)):
    buf = io.BytesIO()
    Image.new("RGB", (w, h), color).save(buf, format="PNG")
    return buf.getvalue()


def test_device_ready_true_when_state_is_device():
    calls = []
    def runner(cmd, **kw):
        calls.append(cmd)
        return FakeCompleted(stdout=b"device\n")
    adb = ADB("emulator-5554", runner=runner)
    assert adb.device_ready() is True
    assert calls[0] == ["adb", "-s", "emulator-5554", "get-state"]


def test_device_ready_false_when_offline():
    adb = ADB("s", runner=lambda cmd, **kw: FakeCompleted(stdout=b"offline\n"))
    assert adb.device_ready() is False


def test_screencap_returns_image():
    adb = ADB("s", runner=lambda cmd, **kw: FakeCompleted(stdout=_png_bytes(4, 3)))
    img = adb.screencap()
    assert img.size == (4, 3)


def test_tap_issues_input_tap():
    calls = []
    adb = ADB("s", runner=lambda cmd, **kw: calls.append(cmd) or FakeCompleted())
    adb.tap(120, 240)
    assert calls[0] == ["adb", "-s", "s", "shell", "input", "tap", "120", "240"]


def test_swipe_issues_input_swipe():
    calls = []
    adb = ADB("s", runner=lambda cmd, **kw: calls.append(cmd) or FakeCompleted())
    adb.swipe(1, 2, 3, 4, ms=250)
    assert calls[0] == ["adb", "-s", "s", "shell", "input", "swipe", "1", "2", "3", "4", "250"]
```

- [ ] **Step 2: Run to verify they fail**

Run: `.venv/bin/pytest tests/test_farmbot_adb.py -v`
Expected: FAIL (`ModuleNotFoundError: farmbot.adb`).

- [ ] **Step 3: Implement `adb.py`**

Create `farmbot/adb.py`:
```python
"""adb.py — thin ADB wrappers. The ONLY module (with vision) that touches the device."""
import io
import subprocess
from PIL import Image


class ADB:
    def __init__(self, serial, runner=subprocess.run):
        self.serial = serial
        self._run = runner

    def _adb(self, *args, capture=False):
        cmd = ["adb", "-s", self.serial, *args]
        return self._run(cmd, capture_output=capture)

    def device_ready(self):
        out = self._adb("get-state", capture=True)
        return (out.stdout or b"").decode(errors="ignore").strip() == "device"

    def screencap(self):
        out = self._adb("exec-out", "screencap", "-p", capture=True)
        return Image.open(io.BytesIO(out.stdout)).convert("RGB")

    def tap(self, x, y):
        self._adb("shell", "input", "tap", str(int(x)), str(int(y)))

    def swipe(self, x1, y1, x2, y2, ms=300):
        self._adb("shell", "input", "swipe",
                  str(int(x1)), str(int(y1)), str(int(x2)), str(int(y2)), str(int(ms)))
```

- [ ] **Step 4: Run to verify they pass**

Run: `.venv/bin/pytest tests/test_farmbot_adb.py -v`
Expected: PASS (5 tests).

- [ ] **Step 5: Commit**

```bash
git add farmbot/adb.py tests/test_farmbot_adb.py
git commit -m "farmbot: add ADB device I/O wrappers (mocked-subprocess tested)"
```

---

### Task 3: `vision.py` — matching primitives

**Files:**
- Create: `farmbot/vision.py`
- Test: `tests/test_farmbot_vision.py`

**Interfaces:**
- Consumes: nothing.
- Produces:
  - `Match = namedtuple("Match", ["cx", "cy", "confidence"])`
  - `to_gray(img) -> numpy.ndarray` (accepts PIL image or ndarray → 2-D uint8)
  - `find(screen, template, threshold=0.88) -> Optional[Match]`
  - `load_templates(dir_path) -> dict[str, numpy.ndarray]` (keyed by file stem, gray)

- [ ] **Step 1: Write the failing tests**

Create `tests/test_farmbot_vision.py`:
```python
import numpy as np
from PIL import Image
from farmbot import vision


def _marker():
    m = np.zeros((20, 20), dtype=np.uint8)
    np.fill_diagonal(m, 255)          # textured, asymmetric
    m[0, :] = 255
    return m


def _gradient(h=120, w=160):
    row = np.linspace(0, 255, w, dtype=np.uint8)
    return np.tile(row, (h, 1))


def test_to_gray_from_pil():
    g = vision.to_gray(Image.new("RGB", (5, 4), (255, 255, 255)))
    assert g.shape == (4, 5) and g.dtype == np.uint8


def test_find_locates_template_center():
    screen = _gradient()
    marker = _marker()
    screen[50:70, 90:110] = marker
    m = vision.find(screen, marker, threshold=0.9)
    assert m is not None
    assert abs(m.cx - 100) <= 1 and abs(m.cy - 60) <= 1   # center of [90:110, 50:70]
    assert m.confidence >= 0.9


def test_find_returns_none_when_absent():
    screen = _gradient()          # marker never pasted
    assert vision.find(screen, _marker(), threshold=0.9) is None


def test_load_templates_reads_pngs(tmp_path):
    Image.fromarray(_marker()).save(tmp_path / "sim_button.png")
    tpls = vision.load_templates(str(tmp_path))
    assert "sim_button" in tpls
    assert tpls["sim_button"].ndim == 2
```

- [ ] **Step 2: Run to verify they fail**

Run: `.venv/bin/pytest tests/test_farmbot_vision.py -v`
Expected: FAIL (`ModuleNotFoundError: farmbot.vision`).

- [ ] **Step 3: Implement `vision.py`**

Create `farmbot/vision.py`:
```python
"""vision.py — OpenCV template matching. Device/image concerns live here (with adb)."""
import glob
import os
from collections import namedtuple

import cv2
import numpy as np
from PIL import Image

Match = namedtuple("Match", ["cx", "cy", "confidence"])


def to_gray(img):
    if isinstance(img, Image.Image):
        img = np.array(img)
    if img.ndim == 3:
        return cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    return img


def find(screen, template, threshold=0.88):
    s = to_gray(screen)
    t = to_gray(template)
    res = cv2.matchTemplate(s, t, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(res)
    if max_val < threshold:
        return None
    h, w = t.shape[:2]
    return Match(cx=int(max_loc[0] + w // 2), cy=int(max_loc[1] + h // 2), confidence=float(max_val))


def load_templates(dir_path):
    out = {}
    for path in glob.glob(os.path.join(dir_path, "*.png")):
        stem = os.path.splitext(os.path.basename(path))[0]
        out[stem] = to_gray(Image.open(path).convert("RGB"))
    return out
```

- [ ] **Step 4: Run to verify they pass**

Run: `.venv/bin/pytest tests/test_farmbot_vision.py -v`
Expected: PASS (4 tests).

- [ ] **Step 5: Commit**

```bash
git add farmbot/vision.py tests/test_farmbot_vision.py
git commit -m "farmbot: add vision matching primitives (find/to_gray/load_templates)"
```

---

### Task 4: `vision.py` — `wait_for` polling

**Files:**
- Modify: `farmbot/vision.py` (add `wait_for`)
- Test: `tests/test_farmbot_vision_wait.py`

**Interfaces:**
- Consumes: `find`, `Match` (Task 3).
- Produces: `wait_for(screen_provider, template, timeout=10.0, interval=0.5, threshold=0.88, finder=find, clock=time.monotonic, sleeper=time.sleep) -> Optional[Match]`
  - `screen_provider` is a zero-arg callable returning a fresh screen each call.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_farmbot_vision_wait.py`:
```python
from farmbot import vision
from farmbot.vision import Match


def test_wait_for_returns_match_when_it_appears():
    responses = [None, None, Match(1, 2, 0.99)]
    calls = {"n": 0}
    def finder(screen, template, threshold):
        r = responses[calls["n"]]
        calls["n"] += 1
        return r
    clock_vals = iter([0.0, 0.0, 0.1, 0.2, 0.3])
    m = vision.wait_for(lambda: object(), object(), timeout=5.0, interval=0.01,
                        finder=finder, clock=lambda: next(clock_vals), sleeper=lambda s: None)
    assert m == Match(1, 2, 0.99)
    assert calls["n"] == 3


def test_wait_for_times_out_to_none():
    clock_vals = iter([0.0, 1.0, 2.0, 11.0])
    m = vision.wait_for(lambda: object(), object(), timeout=10.0, interval=0.01,
                        finder=lambda *a: None, clock=lambda: next(clock_vals), sleeper=lambda s: None)
    assert m is None
```

- [ ] **Step 2: Run to verify they fail**

Run: `.venv/bin/pytest tests/test_farmbot_vision_wait.py -v`
Expected: FAIL (`AttributeError: module 'farmbot.vision' has no attribute 'wait_for'`).

- [ ] **Step 3: Implement `wait_for`**

Add to `farmbot/vision.py` (top: `import time`; append the function):
```python
def wait_for(screen_provider, template, timeout=10.0, interval=0.5, threshold=0.88,
             finder=find, clock=time.monotonic, sleeper=time.sleep):
    start = clock()
    while True:
        m = finder(screen_provider(), template, threshold)
        if m is not None:
            return m
        if clock() - start >= timeout:
            return None
        sleeper(interval)
```

- [ ] **Step 4: Run to verify they pass**

Run: `.venv/bin/pytest tests/test_farmbot_vision_wait.py -v`
Expected: PASS (2 tests).

- [ ] **Step 5: Commit**

```bash
git add farmbot/vision.py tests/test_farmbot_vision_wait.py
git commit -m "farmbot: add vision.wait_for polling (injected clock/sleeper)"
```

---

### Task 5: `tasks.py` — `EnergyDumpTask` state machine

**Files:**
- Create: `farmbot/tasks.py`
- Test: `tests/test_farmbot_tasks.py`

**Interfaces:**
- Consumes: `Match` shape (`.cx`, `.cy`) from Task 3 — but only via the injected `look` callable, so no import of vision is required.
- Produces:
  - `Summary` dataclass: `nodes_attempted:int, sims_done:int, energy_out_nodes:int, halted:bool, halt_state:Optional[str], stopped_reason:str` (`"complete"|"cap"|"killed"|"halt"`)
  - Template-name constants: `TPL_HOME, TPL_SIM, TPL_SIM_MAX, TPL_CONFIRM, TPL_REWARDS, TPL_BACK, TPL_ENERGY_OUT`
  - `EnergyDumpTask(nodes, look, tapper, should_stop=lambda: False, halt=lambda state: None, max_actions=400, timeout=10.0, energy_out_timeout=2.0, delay=lambda: None)` with `.run() -> Summary`
  - `look(template_name: str, timeout: float) -> Optional[Match]`; `tapper(cx: int, cy: int) -> None`; `halt(state_name: str) -> None`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_farmbot_tasks.py`:
```python
from collections import namedtuple
from farmbot.tasks import EnergyDumpTask, Summary

M = namedtuple("M", ["cx", "cy", "confidence"])
NODES = [{"campaign": "cantina", "node": "5-D", "sim": "max"}]


def make_look(present):
    """Return a `look` that yields a Match for any template name in `present`, else None."""
    def look(name, timeout):
        return M(10, 20, 0.99) if name in present else None
    return look


ALL_TPLS = {"home", "campaign_cantina", "node_5-D", "sim_button", "sim_max",
            "sim_confirm", "rewards", "back"}


def test_happy_path_taps_and_counts_one_sim():
    taps = []
    task = EnergyDumpTask(NODES, make_look(ALL_TPLS), lambda x, y: taps.append((x, y)))
    s = task.run()
    assert s.stopped_reason == "complete"
    assert s.nodes_attempted == 1
    assert s.sims_done == 1
    # taps = CAMPAIGN, NODE, SIM, MAX, CONFIRM, REWARDS, BACK = 7 (2 HOME verifies don't tap)
    assert len(taps) == 7
    assert s.halted is False


def test_unknown_screen_halts():
    halts = []
    present = ALL_TPLS - {"sim_button"}          # SIM screen never appears, not energy-out
    task = EnergyDumpTask(NODES, make_look(present), lambda x, y: None,
                          halt=lambda state: halts.append(state))
    s = task.run()
    assert s.halted is True
    assert s.halt_state == "SIM_BUTTON"
    assert s.stopped_reason == "halt"
    assert halts == ["SIM_BUTTON"]


def test_energy_out_skips_node_without_halting():
    present = (ALL_TPLS - {"sim_confirm"}) | {"energy_out"}   # confirm absent, energy-out shown
    task = EnergyDumpTask(NODES, make_look(present), lambda x, y: None)
    s = task.run()
    assert s.halted is False
    assert s.energy_out_nodes == 1
    assert s.sims_done == 0
    assert s.stopped_reason == "complete"


def test_kill_switch_stops_before_next_node():
    task = EnergyDumpTask(NODES, make_look(ALL_TPLS), lambda x, y: None,
                          should_stop=lambda: True)
    s = task.run()
    assert s.stopped_reason == "killed"
    assert s.nodes_attempted == 0


def test_action_cap_stops_run():
    task = EnergyDumpTask(NODES, make_look(ALL_TPLS), lambda x, y: None, max_actions=3)
    s = task.run()
    assert s.stopped_reason == "cap"
    assert s.sims_done == 0
```

- [ ] **Step 2: Run to verify they fail**

Run: `.venv/bin/pytest tests/test_farmbot_tasks.py -v`
Expected: FAIL (`ModuleNotFoundError: farmbot.tasks`).

- [ ] **Step 3: Implement `tasks.py`**

Create `farmbot/tasks.py`:
```python
"""tasks.py — EnergyDumpTask state machine. Device-free: all perception via injected `look`."""
from dataclasses import dataclass
from typing import Optional

TPL_HOME = "home"
TPL_SIM = "sim_button"
TPL_SIM_MAX = "sim_max"
TPL_CONFIRM = "sim_confirm"
TPL_REWARDS = "rewards"
TPL_BACK = "back"
TPL_ENERGY_OUT = "energy_out"


@dataclass
class Summary:
    nodes_attempted: int = 0
    sims_done: int = 0
    energy_out_nodes: int = 0
    halted: bool = False
    halt_state: Optional[str] = None
    stopped_reason: str = "complete"


class EnergyDumpTask:
    def __init__(self, nodes, look, tapper, should_stop=lambda: False,
                 halt=lambda state: None, max_actions=400, timeout=10.0,
                 energy_out_timeout=2.0, delay=lambda: None):
        self.nodes = nodes
        self.look = look
        self.tapper = tapper
        self.should_stop = should_stop
        self.halt = halt
        self.max_actions = max_actions
        self.timeout = timeout
        self.energy_out_timeout = energy_out_timeout
        self.delay = delay
        self._actions = 0

    def _steps_for(self, node):
        # (state, template_name, should_tap). HOME verifies only (no tap).
        return [
            ("HOME", TPL_HOME, False),
            ("CAMPAIGN", f"campaign_{node['campaign']}", True),
            ("NODE", f"node_{node['node']}", True),
            ("SIM_BUTTON", TPL_SIM, True),
            ("SIM_MAX", TPL_SIM_MAX, True),
            ("CONFIRM", TPL_CONFIRM, True),
            ("REWARDS", TPL_REWARDS, True),
            ("BACK", TPL_BACK, True),
            ("HOME", TPL_HOME, False),
        ]

    def run(self):
        s = Summary()
        for node in self.nodes:
            if self.should_stop():
                s.stopped_reason = "killed"
                return s
            s.nodes_attempted += 1
            for state, tpl, should_tap in self._steps_for(node):
                if self._actions >= self.max_actions:
                    s.stopped_reason = "cap"
                    return s
                if self.should_stop():
                    s.stopped_reason = "killed"
                    return s
                m = self.look(tpl, self.timeout)
                if m is None:
                    if state == "CONFIRM" and \
                            self.look(TPL_ENERGY_OUT, self.energy_out_timeout) is not None:
                        s.energy_out_nodes += 1
                        break                      # this node's energy type is out → next node
                    self.halt(state)
                    s.halted = True
                    s.halt_state = state
                    s.stopped_reason = "halt"
                    return s
                if should_tap:
                    self.tapper(m.cx, m.cy)
                    self._actions += 1
                    self.delay()
                    if state == "CONFIRM":
                        s.sims_done += 1
        return s
```

- [ ] **Step 4: Run to verify they pass**

Run: `.venv/bin/pytest tests/test_farmbot_tasks.py -v`
Expected: PASS (5 tests).

- [ ] **Step 5: Commit**

```bash
git add farmbot/tasks.py tests/test_farmbot_tasks.py
git commit -m "farmbot: add EnergyDumpTask state machine (halt/energy-out/cap/kill)"
```

---

### Task 6: `run.py` — CLI orchestrator

**Files:**
- Create: `farmbot/run.py`
- Test: `tests/test_farmbot_run.py`

**Interfaces:**
- Consumes: `ADB` (Task 2); `vision.load_templates`, `vision.wait_for`, `vision.to_gray` (Tasks 3-4); `EnergyDumpTask`, `Summary` (Task 5).
- Produces (the independently testable pure helpers):
  - `parse_args(argv) -> argparse.Namespace` (`--config`, `--dump`, `--capture`, `--dry-run`)
  - `load_config(path) -> dict` (raises `ValueError` on a missing required key)
  - `make_kill_switch(stop_file) -> Callable[[], bool]`
  - `make_delay(action_delay_ms, sleeper=time.sleep, rng=random.uniform) -> Callable[[], None]`
  - `format_summary(summary) -> str`
  - `main(argv=None) -> int`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_farmbot_run.py`:
```python
import json
import pytest
from farmbot import run
from farmbot.tasks import Summary


def test_parse_args_defaults():
    ns = run.parse_args([])
    assert ns.config.endswith("config.json")
    assert ns.dry_run is False


def test_load_config_ok(tmp_path):
    p = tmp_path / "c.json"
    p.write_text(json.dumps({
        "device_serial": "s",
        "caps": {"max_actions": 10, "action_delay_ms": [1, 2]},
        "vision": {"match_threshold": 0.9, "step_timeout_s": 5, "energy_out_timeout_s": 1},
        "nodes": [{"campaign": "cantina", "node": "5-D", "sim": "max"}],
    }))
    cfg = run.load_config(str(p))
    assert cfg["device_serial"] == "s"


def test_load_config_missing_key_raises(tmp_path):
    p = tmp_path / "c.json"
    p.write_text(json.dumps({"device_serial": "s"}))
    with pytest.raises(ValueError):
        run.load_config(str(p))


def test_kill_switch_reads_stop_file(tmp_path):
    flag = tmp_path / "STOP"
    should_stop = run.make_kill_switch(str(flag))
    assert should_stop() is False
    flag.write_text("")
    assert should_stop() is True


def test_make_delay_sleeps_within_range():
    slept = []
    d = run.make_delay([700, 1800], sleeper=lambda s: slept.append(s),
                       rng=lambda lo, hi: (lo + hi) / 2)
    d()
    assert slept == [1.25]          # 1250 ms → 1.25 s


def test_format_summary_mentions_counts():
    out = run.format_summary(Summary(nodes_attempted=2, sims_done=5, stopped_reason="complete"))
    assert "2" in out and "5" in out and "complete" in out
```

- [ ] **Step 2: Run to verify they fail**

Run: `.venv/bin/pytest tests/test_farmbot_run.py -v`
Expected: FAIL (`ModuleNotFoundError: farmbot.run`).

- [ ] **Step 3: Implement `run.py`**

Create `farmbot/run.py`:
```python
"""run.py — CLI orchestrator for the energy-dump macro. Wires device I/O to the state machine."""
import argparse
import datetime as _dt
import json
import os
import random
import signal
import time

from farmbot import vision
from farmbot.adb import ADB
from farmbot.tasks import EnergyDumpTask

ROOT = os.path.dirname(os.path.abspath(__file__))
DEFAULT_CONFIG = os.path.join(ROOT, "config.json")
TEMPLATE_DIR = os.path.join(ROOT, "templates")
HALT_DIR = os.path.join(ROOT, "halts")
STOP_FILE = os.path.join(ROOT, "STOP")
_REQUIRED = ("device_serial", "caps", "vision", "nodes")


def parse_args(argv=None):
    p = argparse.ArgumentParser(description="SWGOH energy-dump macro (PvE only).")
    p.add_argument("--config", default=DEFAULT_CONFIG)
    p.add_argument("--dump", action="store_true", help="run the energy dump (default action)")
    p.add_argument("--capture", action="store_true", help="capture a template instead of running")
    p.add_argument("--dry-run", action="store_true", help="print the plan, tap nothing")
    return p.parse_args(argv)


def load_config(path):
    with open(path) as f:
        cfg = json.load(f)
    for key in _REQUIRED:
        if key not in cfg:
            raise ValueError(f"config missing required key: {key}")
    return cfg


def make_kill_switch(stop_file):
    flag = {"stopped": False}

    def _sigint(_signum, _frame):
        flag["stopped"] = True

    try:
        signal.signal(signal.SIGINT, _sigint)
    except ValueError:
        pass  # not on the main thread (e.g. under a test runner) — file flag still works

    def should_stop():
        return flag["stopped"] or os.path.exists(stop_file)

    return should_stop


def make_delay(action_delay_ms, sleeper=time.sleep, rng=random.uniform):
    lo, hi = action_delay_ms

    def delay():
        sleeper(rng(lo, hi) / 1000.0)

    return delay


def format_summary(summary):
    return (f"nodes_attempted={summary.nodes_attempted} sims_done={summary.sims_done} "
            f"energy_out_nodes={summary.energy_out_nodes} halted={summary.halted} "
            f"halt_state={summary.halt_state} reason={summary.stopped_reason}")


def main(argv=None):
    args = parse_args(argv)
    cfg = load_config(args.config)
    if args.capture:
        from farmbot import capture
        return capture.main(cfg, args)

    adb = ADB(cfg["device_serial"])
    if not adb.device_ready():
        print(f"device not ready: {cfg['device_serial']} — check `adb devices`")
        return 2

    templates = vision.load_templates(TEMPLATE_DIR)
    vcfg = cfg["vision"]
    thr = vcfg["match_threshold"]

    def look(name, timeout):
        tpl = templates.get(name)
        if tpl is None:
            return None
        return vision.wait_for(lambda: vision.to_gray(adb.screencap()), tpl,
                               timeout=timeout, threshold=thr)

    if args.dry_run:
        print("DRY RUN — nodes:")
        for n in cfg["nodes"]:
            print(f"  {n}")
        return 0

    os.makedirs(HALT_DIR, exist_ok=True)

    def halt(state):
        ts = _dt.datetime.now().strftime("%Y%m%d-%H%M%S")
        path = os.path.join(HALT_DIR, f"{ts}_{state}.png")
        try:
            adb.screencap().save(path)
        except Exception as exc:  # noqa: BLE001 — best-effort screenshot on halt
            print(f"halt screenshot failed: {exc}")
        print(f"HALT at {state} — saved {path}")

    task = EnergyDumpTask(
        cfg["nodes"], look, adb.tap,
        should_stop=make_kill_switch(STOP_FILE),
        halt=halt,
        max_actions=cfg["caps"]["max_actions"],
        timeout=vcfg.get("step_timeout_s", 10.0),
        energy_out_timeout=vcfg.get("energy_out_timeout_s", 2.0),
        delay=make_delay(cfg["caps"]["action_delay_ms"]),
    )
    summary = task.run()
    print(format_summary(summary))
    return 1 if summary.halted else 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run to verify they pass**

Run: `.venv/bin/pytest tests/test_farmbot_run.py -v`
Expected: PASS (6 tests).

- [ ] **Step 5: Commit**

```bash
git add farmbot/run.py tests/test_farmbot_run.py
git commit -m "farmbot: add run.py CLI orchestrator (config, kill-switch, wiring)"
```

---

### Task 7: `capture.py` — template bootstrapping

**Files:**
- Create: `farmbot/capture.py`
- Test: `tests/test_farmbot_capture.py`

**Interfaces:**
- Consumes: `ADB` (Task 2) — only inside the interactive `main`.
- Produces:
  - `crop_and_save(image, box, name, out_dir) -> str` — `box=(left, top, right, bottom)`; saves `<out_dir>/<name>.png`; returns the path. Pure and testable.
  - `main(cfg, args) -> int` — interactive: screencap → prompt for `name` + box → `crop_and_save`. Manual; thin.

- [ ] **Step 1: Write the failing test**

Create `tests/test_farmbot_capture.py`:
```python
import os
from PIL import Image
from farmbot import capture


def test_crop_and_save_writes_png_of_box_size(tmp_path):
    img = Image.new("RGB", (100, 80), (0, 0, 0))
    path = capture.crop_and_save(img, (10, 20, 40, 60), "sim_button", str(tmp_path))
    assert os.path.basename(path) == "sim_button.png"
    saved = Image.open(path)
    assert saved.size == (30, 40)      # (40-10) x (60-20)
```

- [ ] **Step 2: Run to verify it fails**

Run: `.venv/bin/pytest tests/test_farmbot_capture.py -v`
Expected: FAIL (`ModuleNotFoundError: farmbot.capture`).

- [ ] **Step 3: Implement `capture.py`**

Create `farmbot/capture.py`:
```python
"""capture.py — bootstrap reference templates from the live emulator (supervised, one-time)."""
import os

from farmbot.adb import ADB


def crop_and_save(image, box, name, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, f"{name}.png")
    image.crop(box).save(path)
    return path


def main(cfg, args):
    root = os.path.dirname(os.path.abspath(__file__))
    out_dir = os.path.join(root, "templates")
    adb = ADB(cfg["device_serial"])
    if not adb.device_ready():
        print(f"device not ready: {cfg['device_serial']}")
        return 2
    img = adb.screencap()
    print(f"screen size: {img.size}. Enter template name and box to crop.")
    name = input("template name (e.g. sim_button): ").strip()
    coords = input("box as left,top,right,bottom: ").strip()
    left, top, right, bottom = (int(v) for v in coords.split(","))
    path = crop_and_save(img, (left, top, right, bottom), name, out_dir)
    print(f"saved {path}")
    return 0
```

- [ ] **Step 4: Run to verify it passes**

Run: `.venv/bin/pytest tests/test_farmbot_capture.py -v`
Expected: PASS (1 test).

- [ ] **Step 5: Commit**

```bash
git add farmbot/capture.py tests/test_farmbot_capture.py
git commit -m "farmbot: add template capture helper (crop_and_save + interactive)"
```

---

### Task 8: README + manual bootstrapping & integration checklist

**Files:**
- Create: `farmbot/README.md`

**Interfaces:**
- Consumes: everything above.
- Produces: the human runbook (setup prerequisite, capture, dry-run, live run, kill-switch). No code.

- [ ] **Step 1: Run the full suite (regression gate)**

Run: `.venv/bin/pytest tests/ -q`
Expected: all prior tests (30) + the new farmbot tests PASS.

- [ ] **Step 2: Write the runbook**

Create `farmbot/README.md`:
```markdown
# farmbot — SWGOH energy-dump macro (Track B MVP)

⚠️ **PvE only. ToS/ban risk accepted by the owner. Runs on Astra's Mac only.**
Never spends crystals; never touches PvP (Arena/GAC/TW).

## One-time setup (manual)
1. Install **BlueStacks Air** (Apple Silicon). Install SWGOH; **log in as Astra**.
2. Enable ADB: BlueStacks → Settings → Advanced → Android Debug Bridge. Note the serial.
3. Install platform-tools so `adb` is on PATH; confirm `adb devices` lists the emulator.
4. `.venv/bin/pip install -r farmbot/requirements.txt`
5. `cp farmbot/config.example.json farmbot/config.json`; set `device_serial` and your 3★ `nodes`.

## Capture templates (supervised, one-time per game build)
For each screen the flow needs — `home`, `campaign_<name>`, `node_<id>`, `sim_button`,
`sim_max`, `sim_confirm`, `rewards`, `back`, `energy_out` — navigate the emulator to that
screen, then:
```
.venv/bin/python -m farmbot.run --capture
```
Enter the template name and the crop box. Templates land in `farmbot/templates/`.

## Run
- Dry run (prints the node plan, taps nothing): `.venv/bin/python -m farmbot.run --dry-run`
- Live dump: `.venv/bin/python -m farmbot.run --dump`
- **Kill-switch:** Ctrl-C, or `touch farmbot/STOP` (delete it before the next run).
- On any unknown screen the run halts and saves `farmbot/halts/<ts>_<state>.png`.

## Safety model
Every tap is gated by a template match (never blind-taps). Hard `max_actions` cap.
Energy-out on a node is detected and skipped (never refreshes with crystals).
```

- [ ] **Step 3: Commit**

```bash
git add farmbot/README.md
git commit -m "farmbot: add runbook (setup, capture, run, safety)"
```

---

## Self-review (completed by plan author)

- **Spec coverage:** energy-dump-only ✓ (Task 5 flow); vision-guided state machine ✓ (Tasks 3-5); halt-on-unknown + screenshot ✓ (Task 5 `halt`, Task 6 wiring); dual kill-switch ✓ (Task 6 `make_kill_switch` + Task 5 `should_stop`); action cap ✓ (Task 5); no crystal spend ✓ (energy-out skips, never refreshes); BlueStacks Air + ADB ✓ (Task 2, README); config shape ✓ (Task 1); device-free tests ✓ (all tasks); capture bootstrapping ✓ (Task 7). Prerequisite/setup ✓ (README).
- **Placeholder scan:** none — every code/test step is concrete.
- **Type consistency:** `Match(cx, cy, confidence)` used identically in vision/tasks/run; `look(name, timeout)`, `tapper(cx, cy)`, `halt(state)`, `Summary` fields consistent across Tasks 5-6; template-name constants match the `look` names asserted in Task 5 tests and captured in the README.

## Manual integration (not unit-testable — supervised, on the emulator)

After Task 8, perform once on the live BlueStacks emulator: capture the templates, run
`--dry-run`, then a real `--dump` with a **short** node list and watch it; confirm it sims,
returns home, and that Ctrl-C / `STOP` abort cleanly. Re-capture templates after any game update.
