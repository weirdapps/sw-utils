"""Tests for A4 events (scripts/events.py).

parse_ics() reads the swgohevents.com iCalendar feed into structured upcoming
events. It must handle RFC 5545 line folding (continuation lines start with a
space) so wrapped DESCRIPTIONs come back intact.
"""
import events

SAMPLE = (
    "BEGIN:VCALENDAR\r\n"
    "VERSION:2.0\r\n"
    "BEGIN:VEVENT\r\n"
    "UID:abc\r\n"
    "SUMMARY:Endor Escalation - Heroic Battle\r\n"
    "DESCRIPTION:https://x\\n\\nRequires: Ewo\r\n"
    " ks\r\n"
    "DTSTART;VALUE=DATE:20260806\r\n"
    "DTEND;VALUE=DATE:20260807\r\n"
    "CATEGORIES:HEROIC BATTLE\r\n"
    "END:VEVENT\r\n"
    "BEGIN:VEVENT\r\n"
    "UID:def\r\n"
    "SUMMARY:Forest Moon - Assault Battles\r\n"
    "DTSTART;VALUE=DATE:20260808\r\n"
    "CATEGORIES:ASSAULT BATTLES\r\n"
    "END:VEVENT\r\n"
    "END:VCALENDAR\r\n"
)


def test_parses_all_vevents():
    assert len(events.parse_ics(SAMPLE)) == 2


def test_parses_core_fields():
    e = events.parse_ics(SAMPLE)[0]
    assert e["name"] == "Endor Escalation - Heroic Battle"
    assert e["date"] == "20260806"
    assert e["category"] == "HEROIC BATTLE"


def test_unfolds_wrapped_description():
    e = events.parse_ics(SAMPLE)[0]
    assert "Requires: Ewoks" in e["desc"]  # folded "Ewo\n ks" -> "Ewoks"


def test_strips_value_params_from_dtstart():
    # "DTSTART;VALUE=DATE:..." -> key is DTSTART, value is the date
    e = events.parse_ics(SAMPLE)[1]
    assert e["date"] == "20260808"


def test_filter_upcoming_drops_past_and_sorts():
    evs = [{"name": "old", "date": "20250101"},
           {"name": "later", "date": "20260810"},
           {"name": "soon", "date": "20260806"}]
    out = events.filter_upcoming(evs, "20260801")
    assert [e["name"] for e in out] == ["soon", "later"]
