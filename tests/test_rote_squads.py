#!/usr/bin/env python3
"""Tests for scripts/rote_squads.py — the RotE per-node teams as a pushable squad tab.

The point of the emitter is that the plan stops living only in a Python dict nobody opens
mid-phase and becomes a saved squad the picker can serve. So the things worth pinning are the
ones that would silently make it unusable: a malformed envelope that upload_hotutils rejects,
a play order that puts free rows before gated ones, and a MANUAL special that looks safe to
auto-battle.
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import rote_missions as rm            # noqa: E402
import rote_squads as rs              # noqa: E402


def test_envelope_matches_what_upload_hotutils_expects():
    for d in rs.definitions():
        assert set(d) == {"n", "sz", "ct", "cat", "u"}, d
        assert d["ct"] == 1, "RotE squads are characters, not ships"
        assert d["sz"] == len(d["u"]), f"{d['n']}: sz {d['sz']} vs {len(d['u'])} units"
        assert 1 <= d["sz"] <= 5
        for pair in d["u"]:
            assert len(pair) == 2 and all(isinstance(x, str) for x in pair), d["n"]


def test_gated_rows_are_played_before_free_ones():
    """The auto-fill spends gated units on rows that did not need them; once that happens
    the gated row is dead for the phase. So specials and unit-gated rows go first."""
    rows, _ = rs.plan(3)
    order = [rs._priority(m) for m, _t, _l in rows]
    assert order == sorted(order), "play order must be non-decreasing in priority"
    assert order[0] == 0, "phase 3 should open on a special"


def test_manual_missions_are_labelled_so_nobody_autos_them():
    for phase in range(1, 7):
        rows, _ = rs.plan(phase)
        for mission, _tac, label in rows:
            if mission.get("auto") is False:
                assert "MANUAL" in label, f"{label} is manual-only but unlabelled"


def test_aspirational_squads_are_labelled():
    for phase in range(1, 7):
        for mission, tac, label in rs.plan(phase)[0]:
            if tac.get("aspirational"):
                assert "[aspir]" in label, f"{label} is not fillable but unlabelled"


def test_one_category_per_phase_and_none_exceeds_the_ingame_tab_cap():
    """In-game preset tabs stop accepting squads around 15 — TW 5v5 - Defense ends at D15.
    A category that overflows would push fine to HotUtils and then silently truncate."""
    counts = {}
    for d in rs.definitions():
        counts[d["cat"]] = counts.get(d["cat"], 0) + 1
    assert counts, "no squads emitted at all"
    for cat, n in counts.items():
        assert cat.startswith("TB RotE - P"), cat
        assert n <= 15, f"{cat} has {n} squads, over the in-game tab cap"


def test_every_planned_squad_reaches_the_payload():
    planned = sum(1 for p in range(1, 7)
                  for m in rm.build(p)["missions"]
                  if (m.get("tactics") or {}).get("squad"))
    assert len(rs.definitions()) == planned
