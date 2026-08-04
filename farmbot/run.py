"""run.py — CLI orchestrator for the energy-dump macro. Wires device I/O to the state machine."""
import argparse
import datetime as _dt
import json
import os
import random
import signal
import time

from farmbot import report, vision
from farmbot.adb import ADB
from farmbot.tasks import EnergyDumpTask

ROOT = os.path.dirname(os.path.abspath(__file__))
DEFAULT_CONFIG = os.path.join(ROOT, "config.json")
TEMPLATE_DIR = os.path.join(ROOT, "templates")
HALT_DIR = os.path.join(ROOT, "halts")
REPORT_DIR = os.path.join(ROOT, "reports")
STOP_FILE = os.path.join(ROOT, "STOP")
_REQUIRED = ("device_serial", "caps", "vision")


def parse_args(argv=None):
    p = argparse.ArgumentParser(description="SWGOH energy-dump macro (PvE only).")
    p.add_argument("--config", default=DEFAULT_CONFIG)
    p.add_argument("--dump", action="store_true", help="run the energy dump (default action)")
    p.add_argument("--daily", action="store_true",
                   help="run the full daily routine (all kinds); alias of --dump")
    p.add_argument("--capture", action="store_true", help="capture a template instead of running")
    p.add_argument("--dry-run", action="store_true", help="print the plan, tap nothing")
    p.add_argument("--doctor", action="store_true",
                   help="preflight only: device, config and template coverage. Taps nothing.")
    p.add_argument("--report", metavar="PATH",
                   help="write the daily markdown report here (default: farmbot/reports/<date>.md)")
    return p.parse_args(argv)


def doctor(cfg, template_dir=TEMPLATE_DIR, device_ready=None):
    """Preflight. Returns (ok, lines).

    Exists because the failure mode this bot actually has is boring: a template that was never
    captured. A missing template can't match, so the step it belongs to halts mid-run — after the
    entries before it already spent energy. Checking coverage up front turns that into a list.
    """
    from farmbot.devtool import low_contrast_templates, required_templates

    lines, ok = [], True
    routine = routine_of(cfg)
    lines.append(f"routine: {len(routine)} entries")

    kinds = {}
    for entry in routine:
        kinds[entry.get("kind", "energy_node")] = kinds.get(entry.get("kind", "energy_node"), 0) + 1
    lines.append("  " + ", ".join(f"{k}×{n}" for k, n in sorted(kinds.items())))

    if device_ready is None:
        lines.append(f"device: not checked ({cfg['device_serial']})")
    elif device_ready:
        lines.append(f"device: ready ({cfg['device_serial']})")
    else:
        lines.append(f"device: NOT READY ({cfg['device_serial']}) — check `adb devices`")
        ok = False

    import os
    blocking, soft = required_templates(routine)
    have = {os.path.splitext(f)[0] for f in os.listdir(template_dir) if f.endswith(".png")}
    missing = {n: u for n, u in sorted(blocking.items()) if n not in have}
    degraded = {n: u for n, u in sorted(soft.items()) if n not in have}
    unused = sorted(have - set(blocking) - set(soft))
    if missing:
        ok = False
        lines.append(f"templates: {len(missing)} MISSING — these entries would halt:")
        lines += [f"  missing {name}  (needed by {', '.join(sorted(set(users)))})"
                  for name, users in missing.items()]
    else:
        lines.append("templates: every blocking template is present")
    if degraded:
        # Not a failure: these only cover paths that already degrade safely (a skip marker that
        # can't match turns a graceful skip into a halt, which --daily isolates).
        lines.append(f"  {len(degraded)} soft-missing (handled, but capture them when you can): "
                     + ", ".join(degraded))
    if unused:
        lines.append(f"  ({len(unused)} captured but unused: {', '.join(unused)})")

    # Only templates this routine actually relies on: a flat leftover in the directory is noise.
    used = set(blocking) | set(degraded)
    flat = [(n, sd) for n, sd in low_contrast_templates(template_dir) if n in used]
    if flat:
        lines.append("templates: LOW CONTRAST — these can match almost anything:")
        lines += [f"  {name} (std {sd:.0f}, want >= 25) — recapture around a glyph, not texture"
                  for name, sd in flat]
        ok = False

    if not cfg.get("manual"):
        lines.append("manual: no residual checklist configured — the report can't tell you "
                     "what's still yours to do")
    return ok, lines


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


def make_swipe(adb, y=560, near=500, far=1400, ms=400, x=960, top=300, bottom=900):
    """Horizontal node-map swipes plus vertical list scrolls. A direction names which way the
    CONTENT is dragged: 'left' reveals later nodes, 'right' earlier ones, 'up' reveals the rows
    below the fold (the Quests list reorders as quests complete and can push a target row off)."""
    def swipe(direction):
        if direction == "left":
            adb.swipe(far, y, near, y, ms)
        elif direction == "up":
            adb.swipe(x, bottom, x, top, ms)
        elif direction == "down":
            adb.swipe(x, top, x, bottom, ms)
        else:
            adb.swipe(near, y, far, y, ms)

    return swipe


def format_summary(summary):
    return (f"nodes_attempted={summary.nodes_attempted} sims_done={summary.sims_done} "
            f"collected={summary.collected} challenges_simmed={summary.challenges_simmed} "
            f"energy_claimed={summary.energy_claimed} nothing_to_collect={summary.nothing_to_collect} "
            f"battles_won={summary.battles_won} battles_lost={summary.battles_lost} "
            f"bought={summary.bought} blocked_spends={summary.blocked_spends} "
            f"recentered={summary.recentered} "
            f"energy_out_nodes={summary.energy_out_nodes} "
            f"hard_depleted_nodes={summary.hard_depleted_nodes} skipped_nodes={summary.skipped_nodes} "
            f"halted_entries={summary.halted_entries} "
            f"halted={summary.halted} halt_state={summary.halt_state} reason={summary.stopped_reason}")


def main(argv=None):
    args = parse_args(argv)
    cfg = load_config(args.config)
    if args.capture:
        from farmbot import capture
        return capture.main(cfg, args)

    adb = ADB(cfg["device_serial"])
    ready = adb.device_ready()

    if args.doctor:
        ok, lines = doctor(cfg, device_ready=ready)
        print("\n".join(lines))
        print("\nPREFLIGHT " + ("OK" if ok else "FAILED"))
        return 0 if ok else 1

    if not ready:
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
        for n in routine_of(cfg):
            print(f"  {n}")
        return 0

    os.makedirs(HALT_DIR, exist_ok=True)

    def halt(state):
        ts = _dt.datetime.now().strftime("%Y%m%d-%H%M%S")
        path = os.path.join(HALT_DIR, f"{ts}_{state}.png")
        try:
            adb.screencap().save(path)
        except Exception as exc:  # noqa: BLE001 — best-effort screenshot on halt
            print(f"HALT at {state} — screenshot failed: {exc}")
        else:
            print(f"HALT at {state} — saved {path}")

    task = EnergyDumpTask(
        routine_of(cfg), look, adb.tap,
        should_stop=make_kill_switch(STOP_FILE),
        halt=halt,
        max_actions=cfg["caps"]["max_actions"],
        timeout=vcfg.get("step_timeout_s", 10.0),
        energy_out_timeout=vcfg.get("energy_out_timeout_s", 2.0),
        delay=make_delay(cfg["caps"]["action_delay_ms"]),
        swipe=make_swipe(adb),
        continue_on_halt=args.daily,   # --daily = resilient orchestrator: isolate a bad entry, go on
    )
    summary = task.run()
    print(format_summary(summary))

    stamp = _dt.datetime.now()
    path = args.report or os.path.join(
        REPORT_DIR, f"{stamp.strftime('%Y-%m-%d_%H%M')}.md")
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    report.write(path, report.render(summary, stamp.strftime("%Y-%m-%d %H:%M"),
                                     manual=cfg.get("manual", ())))
    print(f"report: {path}")
    return 1 if summary.halted else 0


if __name__ == "__main__":
    raise SystemExit(main())
