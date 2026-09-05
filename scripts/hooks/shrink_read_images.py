#!/usr/bin/env python3
"""PreToolUse guard against the 30MB API request cap.

The cap is on BYTES, not tokens. A BlueStacks screencap is a 1-2MB PNG; Claude Code
re-encodes it to ~600KB of base64 and then re-sends it on *every* subsequent API call.
Sixty screenshots = 29MB = dead session. Token-wise those same sixty are only ~90k,
so auto-compact never fires to save you: the counter that would trigger it can't see
the thing that's killing you.

Three defences, in order:
  1. WARN     - past WARN_BYTES, allow the read but tell the caller to start landing
                the task, because the hard stop is close.
  2. REWRITE  - transcode the image to 1100px / q55 JPEG in a temp cache and point the
                Read at that instead. ~73KB vs ~485KB, measured; game UI stays legible
                down to the guild chat ticker. The original file is never touched.
  3. REFUSE   - past BUDGET_BYTES, deny the read rather than let the API return a 400
                that eats the session.

⚠ Only /clear recovers from the 400. /compact is itself an API call carrying the whole
context, so it fails too. That is why this file refuses instead of hoping.

⚠ The tally is computed STRUCTURALLY, by parsing each transcript line. It used to
substring-match markers like '"compact_boundary"' against the raw text, which meant
reading this very file into context reset the budget to zero and disarmed the guard,
verified 2026-09-05, the day a session died at 30,040,700 bytes with 224 images in it.
A parse failure counts nothing and never resets.

Fails open everywhere: any error and the tool call proceeds untouched.
"""
import hashlib
import json
import os
import shutil
import subprocess
import sys

MAX_WIDTH = 1100          # measured: smallest in-game text still readable
QUALITY = 55
SHRINK_ABOVE = 150_000    # bytes on disk; anything smaller isn't worth transcoding
WARN_BYTES = 12_000_000   # banked base64 image payload before we start nagging
BUDGET_BYTES = 20_000_000 # ...and before we start refusing. 10MB of headroom under 30.
CACHE_DIR = "/tmp/claude-img-cache"
LOG = os.path.join(CACHE_DIR, "shrink.log")
IMAGE_EXT = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp"}

# Tools that can put an image into context. Read is 96% of it in practice (214 of the
# 224 that killed the 2026-09-05 session); the MCP screenshot tools hand back an image
# with no file path, so they get the budget check but not the transcode.
IMAGE_TOOLS = (
    "Read",
    "mcp__plugin_chrome-devtools-mcp_chrome-devtools__take_screenshot",
    "mcp__plugin_playwright_playwright__browser_take_screenshot",
)

# A real boundary is {"type":"system","subtype":"compact_boundary"} (CLI 2.1.261).
# microcompact_boundary is deliberately NOT here: it clears tool results selectively,
# so zeroing on it UNDER-counts. Over-counting costs one refused Read; under-counting
# costs the session.
RESET_SUBTYPES = {"compact_boundary"}

ADVICE = (
    "Do this instead: write where you are to memory/session_state.md, then ask the user "
    "to run /clear and say 'continue' - the SessionStart hook replays that ledger and you "
    "pick up mid-task. /compact will NOT work, it is itself an oversize API call. "
    "Do not retry this call."
)


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


def _image_bytes_in(node):
    """Sum base64 payload of every image block anywhere under `node`."""
    if isinstance(node, dict):
        if node.get("type") == "image":
            data = (node.get("source") or {}).get("data")
            return len(data) if isinstance(data, str) else 0
        return sum(_image_bytes_in(v) for v in node.values())
    if isinstance(node, list):
        return sum(_image_bytes_in(v) for v in node)
    return 0


def banked_image_bytes(transcript):
    """Base64 image payload already sitting in this session's context."""
    if not transcript or not os.path.isfile(transcript):
        return 0
    total = 0
    try:
        with open(transcript, errors="replace") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                except (json.JSONDecodeError, ValueError):
                    continue          # unparseable: count nothing, reset nothing
                if not isinstance(entry, dict):
                    continue
                if (entry.get("type") == "system"
                        and entry.get("subtype") in RESET_SUBTYPES) \
                        or entry.get("isCompactSummary") is True:
                    total = 0         # everything before the boundary is gone
                    continue
                total += _image_bytes_in(entry.get("message") or {})
    except OSError:
        return 0
    return total


def decide(banked):
    """(kind, message) once the tally matters, else None."""
    if banked > BUDGET_BYTES:
        return "deny", (
            f"IMAGE BUDGET HIT: ~{banked // 1_000_000}MB of screenshots are already in "
            f"context and the API refuses any request over 30MB. One more will kill the "
            f"session with a 400.\n{ADVICE}"
        )
    if banked > WARN_BYTES:
        return "warn", (
            f"IMAGE BUDGET {banked // 1_000_000}MB / {BUDGET_BYTES // 1_000_000}MB. "
            f"Reads are refused past the limit and the 400 that follows is only "
            f"recoverable with /clear. Land the task, or checkpoint to "
            f"memory/session_state.md now."
        )
    return None


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

    tool = hook.get("tool_name") or ""
    path = (hook.get("tool_input") or {}).get("file_path") or ""
    is_image_read = os.path.splitext(path)[1].lower() in IMAGE_EXT and os.path.isfile(path)
    if tool not in IMAGE_TOOLS and not is_image_read:
        sys.exit(0)

    verdict = decide(banked_image_bytes(hook.get("transcript_path")))
    if verdict and verdict[0] == "deny":
        emit({"hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": verdict[1],
        }})
    warning = verdict[1] if verdict else None

    if not is_image_read:                          # MCP screenshot: budget check only
        if warning:
            emit({"hookSpecificOutput": {"hookEventName": "PreToolUse",
                                         "additionalContext": warning}})
        sys.exit(0)

    try:
        original_size = os.path.getsize(path)
        stamp = f"{path}:{os.path.getmtime(path)}:{original_size}"
    except OSError:
        sys.exit(0)
    if original_size <= SHRINK_ABOVE:
        if warning:
            emit({"hookSpecificOutput": {"hookEventName": "PreToolUse",
                                         "additionalContext": warning}})
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
    reason = (f"Screenshot downscaled for the API byte cap "
              f"({original_size // 1024}KB -> {new_size // 1024}KB). Original untouched at {path}")
    emit({
        "suppressOutput": True,
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "allow",
            "permissionDecisionReason": reason if not warning else f"{warning}\n{reason}",
            "updatedInput": tool_input,
        },
    })


if __name__ == "__main__":
    main()
