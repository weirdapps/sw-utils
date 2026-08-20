"""Tests for the RotE activity-feed verdict reader (scripts/rote_autobattle.py).

Why this file exists: on 2026-08-20 the driver's own win/ended/timeout label was wrong on 5 of
8 missions, in both directions — three full clears reported "ended", one reported "timeout",
and a 1-of-2-wave PARTIAL reported "win". A partial pays 125,000 instead of 250,000 and nothing
else on screen says so, so the feed text is the only verdict. These are the real OCR strings
that session produced, line wrapping and mangled names included.
"""
import rote_autobattle as rb

# Real tesseract output. Note "Astra" on the 2/2 entry came back as "ASLIG" — OCR mangles the
# name often enough that the unanchored fallback has to exist.
REAL_OCR = """Sv ASLIG. GCUipICloUu a VUiVal iViooiui bua
(2/2 waves), earning 250,000 Territory
Points
\\yf Astra: Deployed 621,041 points 7m
La Astra: Completed a Combat Mission 4m
(1/1 waves), earning 500,000 Territory
Points
\\yf Astra: Deployed 11,924,835 points <Im"""


def test_anchors_on_the_player_and_takes_the_newest_entry():
    row, mine = rb.parse_feed(REAL_OCR, "Astra")
    assert row == (1, 1, 500000)
    assert mine is True


def test_falls_back_to_any_row_when_the_name_never_matches():
    row, mine = rb.parse_feed(REAL_OCR, "Nobody")
    assert row == (1, 1, 500000)
    assert mine is False, "an unanchored row may be a guildmate's and must be flagged"


def test_detects_a_partial_clear():
    """The failure the driver called a 'win'. 1/2 waves is half credit."""
    txt = "La Astra: Completed a Combat Mission 4m\n(1/2 waves), earning 125,000 Territory\nPoints"
    row, mine = rb.parse_feed(txt, "Astra")
    assert row == (1, 2, 125000)
    assert mine is True
    assert row[0] < row[1], "caller must treat done < total as PARTIAL"


def test_entry_wrapping_across_lines_is_handled():
    """Name and waves land on separate OCR lines; matching per line finds nothing."""
    txt = "Astra: Completed a Combat Mission\n(2/2 waves), earning 250,000 Territory Points"
    assert rb.parse_feed(txt, "Astra") == ((2, 2, 250000), True)


def test_unreadable_feed_returns_none_rather_than_guessing():
    assert rb.parse_feed("", "Astra") == (None, False)
    assert rb.parse_feed("Astra: Deployed 621,041 points", "Astra") == (None, False)


def test_ignores_a_guildmates_newer_row_when_the_player_has_one():
    txt = ("Astra: Completed a Combat Mission (2/2 waves), earning 250,000 Territory Points\n"
           "KTMSarge: Completed a Combat Mission (1/2 waves), earning 125,000 Territory Points")
    row, mine = rb.parse_feed(txt, "Astra")
    assert row == (2, 2, 250000)
    assert mine is True
