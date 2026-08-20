#!/usr/bin/env python3
"""PreToolUse(Read) guard against the 30MB API request cap.

The cap is on BYTES, not tokens. A BlueStacks screencap is a 1-2MB PNG; Claude Code
re-encodes it to ~600KB of base64 and then re-sends it on *every* subsequent API call.
Sixty screenshots = 29MB = dead session. Token-wise those same sixty are only ~90k,
so auto-compact never fires to save you: the counter that would trigger it can't see
the thing that's killing you.

Two defences, in order:
  1. REWRITE  - transcode the image to 1100px / q55 JPEG in a temp cache and point the
                Read at that instead. ~73KB vs ~485KB, measured; game UI stays legible
                down to the guild chat ticker. The original file is never touched.
  2. REFUSE   - if this session has already banked BUDGET_BYTES of image payload, deny
                the read rather than let the API return a 400 that eats the session.

Fails open everywhere: any error and the Read proceeds untouched.
"""
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys

MAX_WIDTH = 1100          # measured: smallest in-game text still readable
QUALITY = 55
SHRINK_ABOVE = 150_000    # bytes on disk; anything smaller isn't worth transcoding
BUDGET_BYTES = 20_000_000 # banked base64 image payload before we start refusing
CACHE_DIR = "/tmp/claude-img-cache"
LOG = os.path.join(CACHE_DIR, "shrink.log")
IMAGE_EXT = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp"}

# Reset the tally at a compaction boundary - images before it are out of context.
# Marker naming has varied across Claude Code versions, so match several.
COMPACT_MARKERS = ('"isCompactSummary":true', '"compact_boundary"', '"type":"summary"')
DATA_RE = re.compile(r'"data":"([A-Za-z0-9+/=]{2000,})"')


def emit(obj):
    print(json.dumps(obj))
    sys.exit(0)


def log(msg):
    try:
        os.makedirs(CACHE_DIR, exist_ok=True)
        with open(LOG, "a") as fh:
            fh.write(msg + "\n")
    except OSError:
        pass


def banked_image_bytes(transcript):
    """Base64 image payload already sitting in this session's context."""
    if not transcript or not os.path.isfile(transcript):
        return 0
    total = 0
    try:
        with open(transcript, errors="replace") as fh:
            for line in fh:
                if any(m in line for m in COMPACT_MARKERS):
                    total = 0          # everything before the boundary is gone
                    continue
                if '"type":"image"' not in line:
                    continue
                total += sum(len(m) for m in DATA_RE.findall(line))
    except OSError:
        return 0
    return total


def transcode(src, dst):
    """1100px-wide JPEG. magick preferred, sips is the macOS-native fallback."""
    if shutil.which("magick"):
        cmd = ["magick", src, "-resize", f"{MAX_WIDTH}x>", "-quality", str(QUALITY), dst]
    elif shutil.which("sips"):
        cmd = ["sips", "-s", "format", "jpeg", "-s", "formatOptions", str(QUALITY),
               "-Z", str(MAX_WIDTH), src, "--out", dst]
    else:
        return False
    try:
        subprocess.run(cmd, check=True, capture_output=True, timeout=25)
    except (subprocess.SubprocessError, OSError):
        return False
    return os.path.isfile(dst) and os.path.getsize(dst) > 0


def main():
    try:
        hook = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        sys.exit(0)

    path = (hook.get("tool_input") or {}).get("file_path") or ""
    if os.path.splitext(path)[1].lower() not in IMAGE_EXT or not os.path.isfile(path):
        sys.exit(0)

    banked = banked_image_bytes(hook.get("transcript_path"))
    if banked > BUDGET_BYTES:
        emit({
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": (
                    f"IMAGE BUDGET HIT: ~{banked // 1_000_000}MB of screenshots are already in "
                    f"context and the API refuses any request over 30MB. Reading another one "
                    f"will kill the session with a 400.\n"
                    f"Do this instead: write where you are to memory/session_state.md, then ask "
                    f"the user to run /clear or /compact and say 'continue' - the SessionStart "
                    f"hook replays that ledger and you pick up mid-task. Do not retry this Read."
                ),
            }
        })

    try:
        original_size = os.path.getsize(path)
    except OSError:
        sys.exit(0)
    if original_size <= SHRINK_ABOVE:
        sys.exit(0)

    try:
        stamp = f"{path}:{os.path.getmtime(path)}:{original_size}"
    except OSError:
        sys.exit(0)
    dst = os.path.join(CACHE_DIR, hashlib.sha1(stamp.encode()).hexdigest()[:16] + ".jpg")

    if not os.path.isfile(dst):
        os.makedirs(CACHE_DIR, exist_ok=True)
        if not transcode(path, dst):
            log(f"PASSTHROUGH (transcode failed) {path}")
            sys.exit(0)

    new_size = os.path.getsize(dst)
    if new_size >= original_size:      # already well compressed; don't make it worse
        sys.exit(0)

    log(f"{original_size:>9} -> {new_size:>8}  {path}")
    tool_input = dict(hook.get("tool_input") or {})
    tool_input["file_path"] = dst
    emit({
        "suppressOutput": True,
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "allow",
            "permissionDecisionReason": (
                f"Screenshot downscaled for the API byte cap "
                f"({original_size // 1024}KB -> {new_size // 1024}KB). Original untouched at {path}"
            ),
            "updatedInput": tool_input,
        },
    })


if __name__ == "__main__":
    main()
