"""report.py — turn a run Summary into a human-readable daily report.

The point of the report is not the counters; it is the SECOND half. The bot deliberately refuses a
few daily tasks (PvP matches, anything that can't be simmed or auto-battled, anything priced in
crystals), and those are exactly the ones that are easy to forget and expensive to miss. So every
run ends by printing what is still the player's job, sourced from the config's `manual` list rather
than hardcoded here — the routine and the residual checklist have to stay in sync, and they only do
that if they live in the same file.

Pure string-building: no device, no clock of its own (the timestamp is passed in), so it is testable.
"""

# Counters worth showing, in report order. Anything left at 0 is dropped, so a short run reads
# short — except the two safety rails, which are printed even at 0 because "0" is the good news.
_COUNTERS = [
    ("sims_done", "energy nodes simmed"),
    ("challenges_simmed", "daily challenges multi-simmed"),
    ("collected", "free rewards collected"),
    ("energy_claimed", "bonus-energy grants claimed"),
    ("battles_won", "PvE auto-battles won"),
    ("battles_lost", "PvE auto-battles lost"),
    ("bought", "shop items bought with tokens"),
    ("energy_out_nodes", "nodes skipped — out of energy"),
    ("hard_depleted_nodes", "nodes skipped — daily attempts used"),
    ("nothing_to_collect", "collectors with nothing waiting"),
    ("halted_entries", "entries that hit an unknown screen"),
]


def render(summary, timestamp, manual=(), crystals_before=None, crystals_after=None):
    """Markdown report for one run. `manual` = the config's residual human checklist."""
    lines = [f"# farmbot daily — {timestamp}", ""]

    lines.append("## Done by the bot")
    lines.append("")
    rows = [(label, getattr(summary, name, 0)) for name, label in _COUNTERS]
    shown = [(label, n) for label, n in rows if n]
    if shown:
        lines += [f"- **{n}** {label}" for label, n in shown]
    else:
        lines.append("- nothing — every entry was already done or had nothing waiting")
    lines.append("")

    lines.append("## Safety rails")
    lines.append("")
    blocked = getattr(summary, "blocked_spends", 0)
    lines.append(f"- crystal-priced purchases refused: **{blocked}**"
                 + ("  ← the guard fired; check the shop config" if blocked else ""))
    if crystals_before is not None and crystals_after is not None:
        delta = crystals_after - crystals_before
        verdict = "unchanged ✅" if delta == 0 else f"**CHANGED BY {delta:+d} — investigate**"
        lines.append(f"- crystal balance {crystals_before} → {crystals_after}: {verdict}")
    lines.append("- PvP matches played: **0** (the bot has no code path that can play one)")
    lines.append("")

    if summary.halted or summary.halted_entries:
        lines.append("## Needs a look")
        lines.append("")
        if summary.halt_state:
            lines.append(f"- last unknown screen at step `{summary.halt_state}` "
                         "— see `farmbot/halts/` for the screenshot")
        if summary.halted:
            lines.append("- the run **aborted** here (use `--daily` to isolate and continue instead)")
        lines.append("")

    lines.append("## Still yours — the bot will never do these")
    lines.append("")
    if manual:
        lines += [f"- [ ] **{m['task']}** — {m['why']}" for m in manual]
    else:
        lines.append("- (none configured — add a `manual` list to the config)")
    lines.append("")
    lines.append(f"_run outcome: {summary.stopped_reason}; "
                 f"{summary.nodes_attempted} routine entries attempted_")
    return "\n".join(lines)


def write(path, text):
    with open(path, "w") as f:
        f.write(text if text.endswith("\n") else text + "\n")
    return path
