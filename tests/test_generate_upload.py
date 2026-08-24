"""Tests for generate_upload's fleet naming.

HotUtils keys a squad definition by NAME, not by (name, category). Two fleets
that share a name are ONE definition, and the second upsert overwrites the first
rather than adding. Measured live 2026-08-24: a 117-definition payload synced to
113 because the GAC and TW fleet banks generated identical names, and the loss
presented as a partial upload rather than a collision.

generate_upload.py runs its work at import time (it is a script, not a module),
so the naming helper is exercised by loading it in isolation rather than by
importing the module.
"""
import os
import re

import pytest

SRC = os.path.join(os.path.dirname(__file__), "..", "scripts", "generate_upload.py")


@pytest.fixture(scope="module")
def fleet_name():
    """Pull `fleet_name` out of the script without executing the script body."""
    text = open(SRC).read()
    m = re.search(r"^def fleet_name\(.*?(?=^\S|\Z)", text, re.S | re.M)
    assert m, "fleet_name() not found in generate_upload.py"
    ns = {}
    exec(compile(m.group(0), SRC, "exec"), ns)
    return ns["fleet_name"]


def test_gac_and_tw_fleets_never_collide(fleet_name):
    # The exact collision that cost 4 definitions: same slot, same capital ship,
    # different mode. These MUST be two names.
    gac = fleet_name("GAC Fleet - Defense", 1, "Chimaera")
    tw = fleet_name("TW Fleet - Defense", 1, "Chimaera")
    assert gac != tw
    assert gac == "GAC Fleet D1 Chimaera"
    assert tw == "TW Fleet D1 Chimaera"


def test_defense_and_offense_never_collide(fleet_name):
    assert (fleet_name("GAC Fleet - Offense", 1, "Leviathan")
            != fleet_name("TW Fleet - Offense", 1, "Leviathan"))
    assert (fleet_name("GAC Fleet - Defense", 1, "Raddus")
            != fleet_name("GAC Fleet - Offense", 1, "Raddus"))


def test_arena_keeps_its_own_shape(fleet_name):
    assert fleet_name("Fleet - Arena", 1, "Leviathan") == "Arena Fleet Leviathan"


def test_the_whole_live_fleet_set_is_unique(fleet_name):
    # The real board: 3 GAC def, 3 GAC off, 6 TW def, 1 TW off, 1 arena = 14 names.
    plan = [("GAC Fleet - Defense", ["Chimaera", "Home One", "Raddus"]),
            ("GAC Fleet - Offense", ["Leviathan", "Executor", "Negotiator"]),
            ("TW Fleet - Defense", ["Chimaera", "Home One", "Raddus",
                                    "Executor", "Negotiator", "Malevolence"]),
            ("TW Fleet - Offense", ["Leviathan"]),
            ("Fleet - Arena", ["Leviathan"])]
    names = [fleet_name(cat, i, cap)
             for cat, caps in plan for i, cap in enumerate(caps, 1)]
    assert len(names) == 14
    assert len(set(names)) == 14, f"collisions: {[n for n in names if names.count(n) > 1]}"
