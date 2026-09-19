"""The refusal dialogs `rote_fill_ops` has to tell apart before it taps anything.

Both dialogs put a green button on screen, so the single-button test matches the
two-button RELIC LEVEL REQUIREMENT layout as well. Dismissing that one through
OK_DLG taps the dead space between CANCEL and UNIT DETAILS, leaving it up and
swallowing every later cell tap, which is how a fill run silently places nothing.
"""
import importlib.util
import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]


def _load():
    spec = importlib.util.spec_from_file_location(
        "rote_fill_ops", ROOT / "scripts" / "rote_fill_ops.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["rote_fill_ops"] = mod
    spec.loader.exec_module(mod)
    return mod


rfo = pytest.importorskip("PIL") and _load()

GREEN = (40, 190, 90)
DARK = (20, 34, 64)
CYAN = (60, 200, 220)


class FakeImage:
    """Answers `box()` from a dict of 1100-space points, nearest match wins."""

    def __init__(self, points):
        self.points = points

    def at(self, x, y):
        best = min(self.points, key=lambda p: (p[0] - x) ** 2 + (p[1] - y) ** 2)
        return self.points[best]


@pytest.fixture
def taps(monkeypatch):
    seen = []
    monkeypatch.setattr(rfo, "tap", lambda x, y, wait=1.5: seen.append((x, y)))
    monkeypatch.setattr(rfo, "box", lambda im, x, y, w=40, h=14: im.at(x, y))
    return seen


def test_relic_dialog_is_cancelled_not_detailed(taps):
    """UNIT DETAILS navigates out of the event, so CANCEL is the only safe tap."""
    im = FakeImage({rfo.RELIC_DETAILS: GREEN, rfo.OK_DLG: DARK})
    assert rfo.dismiss(im) is True
    assert taps == [rfo.RELIC_CANCEL]
    assert rfo.RELIC_DETAILS not in taps


def test_relic_dialog_wins_over_the_one_button_test(taps):
    """Its green button also satisfies ok_dialog(), so order of checks decides."""
    im = FakeImage({rfo.RELIC_DETAILS: GREEN, rfo.OK_DLG: GREEN})
    assert rfo.ok_dialog(im.at(*rfo.OK_DLG)) is True
    rfo.dismiss(im)
    assert taps == [rfo.RELIC_CANCEL]


def test_cannot_be_used_here_still_dismissed_through_ok(taps):
    im = FakeImage({rfo.RELIC_DETAILS: DARK, rfo.OK_DLG: GREEN})
    assert rfo.dismiss(im) is True
    assert taps == [rfo.OK_DLG]


def test_no_dialog_leaves_the_screen_alone(taps):
    im = FakeImage({rfo.RELIC_DETAILS: DARK, rfo.OK_DLG: DARK})
    assert rfo.dismiss(im) is False
    assert taps == []


def test_assign_lit_reads_the_bright_cyan_button():
    assert rfo.assign_lit(CYAN) is True
    assert rfo.assign_lit(DARK) is False
