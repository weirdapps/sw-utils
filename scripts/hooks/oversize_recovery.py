#!/usr/bin/env python3
"""StopFailure handler for the 30MB request cap.

`StopFailure` is the only hook event that observes the API 400, and it does see it:
the payload carries the verbatim text in `last_assistant_message`. Verified against
/tmp/gcloud-stopfailure.log, which caught both of the 2026-09-05 deaths.

What it CANNOT do is fix the session. At 30MB every API call fails, `/compact` is
itself an API call carrying the whole context, and hook output is delivered to the
model, which is unreachable. Only `/clear` works, and no hook can invoke it.

So this does the two things that are actually possible:
  1. tell the human, out of band, that the session is dead and what to type;
  2. write memory/session_state.md from the transcript's non-image tail, so that
     `/clear` followed by "continue" resumes something real instead of nothing.

Prevention lives in shrink_read_images.py. This is the net under it.
"""
import json
import os
import subprocess
import sys
import time

MAX_LEDGER_CHARS = 7000
TAIL_ENTRIES = 60
LOG = "/tmp/claude-oversize-recovery.log"

# The 400 reads:
#   API Error: 400 [{"error":{"code":400,"message":"The message size (30040700 bytes)
#   exceeds 30.000MB limit.","status":"FAILED_PRECONDITION"}}]
FINGERPRINTS = ("message size", "exceeds", "limit")

BANNER = "<!-- written automatically by scripts/hooks/oversize_recovery.py -->"


def log(msg):
    try:
        with open(LOG, "a") as fh:
            fh.write(f"{time.strftime('%F %T')} {msg}\n")
    except OSError:
        pass


def is_size_cap_400(text):
    low = (text or "").lower()
    return "400" in low and all(f in low for f in FINGERPRINTS)


def _texts(entry):
    """(user_prompts, assistant_text, tool_calls, todos) from one transcript entry."""
    users, says, tools, todos = [], [], [], None
    msg = entry.get("message") or {}
    content = msg.get("content")
    if isinstance(content, str):
        if entry.get("type") == "user":
            users.append(content)
        return users, says, tools, todos
    for block in content or []:
        if not isinstance(block, dict):
            continue
        kind = block.get("type")
        if kind == "text" and block.get("text", "").strip():
            (users if entry.get("type") == "user" else says).append(block["text"].strip())
        elif kind == "tool_use":
            name = block.get("name", "?")
            inp = block.get("input") or {}
            if name == "TodoWrite":
                todos = inp.get("todos")
                continue
            hint = (inp.get("file_path") or inp.get("command")
                    or inp.get("pattern") or inp.get("description") or "")
            tools.append(f"{name}({str(hint)[:110]})")
    return users, says, tools, todos


def build_ledger(transcript):
    """The recoverable tail: prompts, reasoning, tool trail, open todos. No images."""
    if not transcript or not os.path.isfile(transcript):
        return None
    entries = []
    try:
        with open(transcript, errors="replace") as fh:
            for line in fh:
                if '"type":"image"' in line and len(line) > 50_000:
                    line = ""          # skip the megabyte lines outright
                if not line.strip():
                    continue
                try:
                    entries.append(json.loads(line))
                except (json.JSONDecodeError, ValueError):
                    continue
    except OSError:
        return None

    users, says, tools, todos = [], [], [], None
    for entry in entries[-TAIL_ENTRIES:]:
        u, s, t, td = _texts(entry)
        users += u
        says += s
        tools += t
        if td is not None:
            todos = td

    def block(title, items, limit):
        items = [i for i in items if i][-limit:]
        if not items:
            return ""
        return f"\n## {title}\n" + "\n".join(f"- {i[:600]}" for i in items) + "\n"

    out = [
        f"# Session state (auto-checkpoint)\n{BANNER}\n",
        f"Written {time.strftime('%F %T %Z')} after the session hit the 30MB API request cap.\n",
        "**Everything durable belongs in `memory/notes.md`. This file is only what was "
        "still in flight.** Delete it once the work has landed.\n",
    ]
    if todos:
        rows = []
        for td in todos:
            if isinstance(td, dict):
                rows.append(f"[{td.get('status', '?')}] {td.get('content', '')}")
        out.append(block("Open todos at the moment of death", rows, 20))
    out.append(block("Last instructions from the user", users, 6))
    # The tail of a dying session is mostly its own 400s. Echoing them back is noise.
    out.append(block("What I was saying", [s for s in says if not is_size_cap_400(s)], 6))
    out.append(block("Last tool calls", tools, 25))
    out.append(
        "\n## How to resume\n"
        "Say `continue`. Re-read `memory/notes.md` and this file, then pick up from the "
        "last tool call above. Screenshots are gone from context on purpose: do not "
        "re-read them in bulk, and expect the budget guard to refuse past 20MB.\n"
    )
    return "".join(out)[:MAX_LEDGER_CHARS]


def notify(banked_note):
    """Out-of-band alert. The model cannot be reached, so this is for the human."""
    msg = (f"Session hit the 30MB API cap{banked_note}. Type /clear then 'continue'. "
           f"/compact will NOT work.")
    try:
        subprocess.run(
            ["osascript", "-e",
             f'display notification {json.dumps(msg)} with title "Claude Code: session dead" '
             f'sound name "Basso"'],
            capture_output=True, timeout=10, check=False)
    except (subprocess.SubprocessError, OSError):
        pass
    print(msg, file=sys.stderr)


def main():
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        sys.exit(0)

    last = payload.get("last_assistant_message") or ""
    if not is_size_cap_400(last):
        sys.exit(0)

    cwd = payload.get("cwd") or os.getcwd()
    target = os.path.join(cwd, "memory", "session_state.md")
    note = ""

    try:
        ledger = build_ledger(payload.get("transcript_path"))
        if ledger:
            previous = ""
            if os.path.isfile(target):
                with open(target, errors="replace") as fh:
                    kept = fh.read().strip()
                # Keep a hand-written ledger; only ever discard our own last one.
                if kept and BANNER not in kept:
                    previous = f"\n---\n\n## Recorded by hand before the crash\n\n{kept}\n"
            os.makedirs(os.path.dirname(target), exist_ok=True)
            with open(target, "w") as fh:
                fh.write(ledger + previous)
            note = f", checkpoint written to {os.path.relpath(target, cwd)}"
            log(f"wrote {target} ({len(ledger)} chars)")
    except OSError as exc:
        log(f"ledger failed: {exc}")

    notify(note)
    sys.exit(0)


if __name__ == "__main__":
    main()
