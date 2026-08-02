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
