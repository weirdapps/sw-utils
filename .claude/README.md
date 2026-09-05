# `.claude/`: the byte-cap defences

`settings.json` wires three hooks. They exist for one failure: **the API refuses any
request over 30MB, and the limit is BYTES, not tokens.** Auto-compact cannot see it
coming, because 224 screenshots are only ~90k tokens but ~30MB of base64. On
2026-09-05 a session died twice at 30,040,215 and 30,040,700 bytes with 219 images
in context.

| Hook | Script | Job |
|---|---|---|
| `PreToolUse` on `Read` + the two screenshot MCP tools | `scripts/hooks/shrink_read_images.py` | Warn at 12MB, transcode anything over 150KB to 1100px/q55 JPEG, refuse past 20MB |
| `StopFailure` | `scripts/hooks/oversize_recovery.py` | On the size-cap 400 only: desktop alert, and write `memory/session_state.md` from the transcript's non-image tail |
| `SessionStart` on `startup\|clear\|resume` | inline | Replay `memory/session_state.md` if it is under 24h old |

## Three things that are easy to get wrong

**Only `/clear` recovers from the 400.** `/compact` is itself an API call carrying the
whole context, so it fails the same way. Nothing reaches the model past the cap, which
is why `StopFailure` alerts the human rather than advising the assistant.

**The refusal matters more than the transcode.** The images that killed the session
were already ~90KB JPEGs written by the `cq_*` scripts, below the 150KB transcode
threshold. At that size 20MB is about 165 images. The transcode only earns its keep
against raw `d.sh` screencaps, which are 1-2MB PNGs.

**The tally is computed structurally, by parsing each transcript line.** It used to
substring-match `"compact_boundary"` against the raw text, which meant that reading
`shrink_read_images.py` into context reset the budget to zero and disarmed the guard.
`microcompact_boundary` is deliberately not a reset: it clears tool results
selectively, so zeroing on it under-counts, and under-counting costs the session while
over-counting costs one refused `Read`.

## Scope

Deliberately project-local. Transcoding to 1100px/q55 keeps SWGOH UI legible down to
the guild chat ticker, but it would wreck deck and brand review in the other repos.
Tests: `tests/test_shrink_read_images.py`, `tests/test_oversize_recovery.py`.
