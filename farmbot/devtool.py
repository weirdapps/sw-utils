"""devtool.py — non-interactive device driver for capture + diagnosis.

`capture.py` prompts for a name and a crop box, which makes it unusable from a script or an
agent session. This is the same job with everything on argv, plus the read-only diagnostics
that answer "why did the run halt here?": what does the screen look like, does template X match
it, and which templates does my config need that I haven't captured yet.

    python -m farmbot.devtool shot [out.png]              screencap to a file
    python -m farmbot.devtool tap X Y                     tap
    python -m farmbot.devtool swipe X1 Y1 X2 Y2 [MS]      swipe
    python -m farmbot.devtool crop L T R B NAME           screencap -> crop -> templates/NAME.png
    python -m farmbot.devtool find NAME...                match templates against the live screen
    python -m farmbot.devtool coverage                    config's required templates vs what exists

Read-only by default: only `tap`, `swipe` and `crop` touch the device state.
"""
import argparse
import glob
import os
import sys

from farmbot import vision
from farmbot.adb import ADB
from farmbot.capture import crop_and_save

ROOT = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.join(ROOT, "templates")
DEFAULT_SHOT = os.path.join(ROOT, "halts", "_devtool.png")


def required_templates(routine):
    """(blocking, soft) template names the routine will look for, each as {name: [entry labels]}.

    Asks the engine rather than re-deriving the step lists: an earlier version of this function
    mirrored tasks._steps_for by hand and immediately drifted from it. Building the real Steps means
    coverage can never disagree with what the run will actually do. Still device-free — Step
    construction touches no I/O.

    BLOCKING = a template whose absence halts the step that wants it. SOFT = one whose absence is
    handled: optional steps, skip markers (their loss downgrades a graceful skip to a halt, which
    `--daily` then isolates), ensure-checks, and the popup closers.
    """
    from farmbot.tasks import DEFAULT_POPUP_CLOSERS, EnergyDumpTask, tap_target

    blocking, soft = {}, {}

    def want(bucket, name, label):
        if name:
            bucket.setdefault(name, []).append(label)

    for closer in DEFAULT_POPUP_CLOSERS:
        # A closer may carry a tap offset — coverage only cares about the template name.
        want(soft, tap_target(closer)[0], "popup dismissal")

    engine = EnergyDumpTask([], lambda name, timeout: None, lambda x, y: None)
    for i, entry in enumerate(routine):
        kind = entry.get("kind", "energy_node")
        label = entry.get("name") or (f"{entry.get('campaign')} {entry.get('node')}"
                                      if kind == "energy_node" else f"{kind}[{i}]")
        try:
            steps = engine._steps_for(entry)
        except (KeyError, ValueError, TypeError) as exc:
            # Report the broken entry instead of crashing the whole coverage run — a preflight
            # that prints a traceback and nothing else is worse than no preflight.
            want(blocking, f"<malformed entry: {exc}>", label)
            continue
        for step in steps:
            if step.pan is not None:
                continue                      # a swipe burst, not a perception step
            want(soft if step.optional else blocking, step.template, label)
            # `forbid` is a SAFETY veto: if its template is missing it silently never matches and
            # the guard is simply off, so it is blocking, not soft.
            want(blocking, step.forbid, label)
            for name in (step.skip_marker, step.ensure, step.forbid_tap,
                         *step.ensure_extra, *step.alt, *step.skip_marker_alt):
                want(soft, name, label)
    # A name that is blocking anywhere is blocking, even if some other entry treats it as optional.
    soft = {n: u for n, u in soft.items() if n not in blocking}
    return blocking, soft


def coverage(routine, template_dir=TEMPLATE_DIR):
    """(missing, degraded, unused) — absent-and-blocking, absent-but-handled, and captured-but-unasked."""
    blocking, soft = required_templates(routine)
    have = {os.path.splitext(f)[0] for f in os.listdir(template_dir) if f.endswith(".png")}
    missing = {n: u for n, u in sorted(blocking.items()) if n not in have}
    degraded = {n: u for n, u in sorted(soft.items()) if n not in have}
    unused = sorted(have - set(blocking) - set(soft))
    return missing, degraded, unused


# A template with almost no internal contrast correlates with any similarly-shaped gradient, so
# TM_CCOEFF_NORMED's global max lands somewhere arbitrary and still clears the threshold. Measured:
# a 66x34 crop of blurred bar-counter texture (std 20) false-matched at 0.917 on three unrelated
# screens. Real glyph crops sit near std 58.
MIN_TEMPLATE_STD = 25.0


def low_contrast_templates(template_dir=TEMPLATE_DIR, floor=MIN_TEMPLATE_STD):
    """[(name, std)] for templates too flat to be trusted, worst first."""
    import numpy as np
    from PIL import Image

    out = []
    for path in sorted(glob.glob(os.path.join(template_dir, "*.png"))):
        try:
            std = float(np.array(Image.open(path).convert("L")).std())
        except Exception:      # noqa: BLE001 — an unreadable template is a separate problem
            continue
        if std < floor:
            out.append((os.path.splitext(os.path.basename(path))[0], std))
    return sorted(out, key=lambda t: t[1])


def _adb(cfg):
    adb = ADB(cfg["device_serial"])
    if not adb.device_ready():
        raise SystemExit(f"device not ready: {cfg['device_serial']} — check `adb devices`")
    return adb


def main(argv=None):
    from farmbot.run import DEFAULT_CONFIG, load_config, routine_of

    p = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    p.add_argument("--config", default=DEFAULT_CONFIG)
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("shot"); s.add_argument("out", nargs="?", default=DEFAULT_SHOT)
    s = sub.add_parser("tap"); s.add_argument("x", type=int); s.add_argument("y", type=int)
    s = sub.add_parser("swipe")
    for a in ("x1", "y1", "x2", "y2"):
        s.add_argument(a, type=int)
    s.add_argument("ms", type=int, nargs="?", default=400)
    s = sub.add_parser("crop")
    for a in ("left", "top", "right", "bottom"):
        s.add_argument(a, type=int)
    s.add_argument("name")
    s = sub.add_parser("find")
    s.add_argument("names", nargs="+")
    s.add_argument("--threshold", type=float, default=0.0, help="report all scores above this")
    sub.add_parser("coverage")
    args = p.parse_args(argv)

    cfg = load_config(args.config)

    if args.cmd == "coverage":
        missing, degraded, unused = coverage(routine_of(cfg))
        for name, users in missing.items():
            print(f"MISSING  {name:<32} needed by: {', '.join(sorted(set(users)))}")
        for name, users in degraded.items():
            print(f"soft     {name:<32} absent but handled: {', '.join(sorted(set(users)))}")
        for name in unused:
            print(f"unused   {name}")
        print(f"\n{len(missing)} missing, {len(degraded)} soft, {len(unused)} unused")
        return 1 if missing else 0

    adb = _adb(cfg)

    if args.cmd == "shot":
        os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
        img = adb.screencap()
        img.save(args.out)
        print(f"{args.out} {img.size[0]}x{img.size[1]}")
    elif args.cmd == "tap":
        adb.tap(args.x, args.y)
        print(f"tap {args.x},{args.y}")
    elif args.cmd == "swipe":
        adb.swipe(args.x1, args.y1, args.x2, args.y2, args.ms)
        print(f"swipe {args.x1},{args.y1} -> {args.x2},{args.y2} ({args.ms}ms)")
    elif args.cmd == "crop":
        path = crop_and_save(adb.screencap(), (args.left, args.top, args.right, args.bottom),
                             args.name, TEMPLATE_DIR)
        print(f"saved {path}")
    elif args.cmd == "find":
        screen = vision.to_gray(adb.screencap())
        templates = vision.load_templates(TEMPLATE_DIR)
        for name in args.names:
            tpl = templates.get(name)
            if tpl is None:
                print(f"{name:<32} NO SUCH TEMPLATE")
                continue
            m = vision.find(screen, tpl, threshold=args.threshold)
            print(f"{name:<32} {'conf=%.3f at (%d,%d)' % (m.confidence, m.cx, m.cy) if m else 'no match'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
