"""Tests for the r/SWGalaxyOfHeroes board-chatter signal (scripts/reddit_swgoh.py)."""
import io
import json
import os
import urllib.error
from unittest.mock import MagicMock, call, patch

import pytest

import reddit_swgoh

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")


def _feed():
    with open(os.path.join(FIXTURES, "reddit_swgoh.rss"), encoding="utf-8") as fh:
        return fh.read()


def _make_response(body: str):
    """Return a context-manager mock that yields a response-like object."""
    resp = MagicMock()
    resp.read.return_value = body.encode("utf-8")
    ctx = MagicMock()
    ctx.__enter__ = MagicMock(return_value=resp)
    ctx.__exit__ = MagicMock(return_value=False)
    return ctx


def _http_error(code: int):
    return urllib.error.HTTPError(url="", code=code, msg="", hdrs=None, fp=None)


def test_parse_feed_returns_all_entries():
    entries = reddit_swgoh.parse_feed(_feed())
    # Fixture captured 2026-08-11 had 25 entries; floor guards against fixture regeneration.
    assert len(entries) >= 20
    assert all(e["title"] and e["link"] for e in entries)


def test_parse_feed_unescapes_html_entities():
    xml = (
        '<feed xmlns="http://www.w3.org/2005/Atom"><entry>'
        "<title>The &amp;quot;Guardians&amp;quot; problem</title>"
        '<link href="https://example.com/x"/>'
        "<updated>2026-08-11T10:00:00+00:00</updated>"
        "<author><name>/u/someone</name></author>"
        "</entry></feed>"
    )
    entries = reddit_swgoh.parse_feed(xml)
    assert entries[0]["title"] == 'The "Guardians" problem'


def test_parse_feed_on_empty_document_returns_empty_list():
    assert reddit_swgoh.parse_feed('<feed xmlns="http://www.w3.org/2005/Atom"/>') == []


# ---------------------------------------------------------------------------
# fetch_feed tests
# ---------------------------------------------------------------------------


def test_fetch_feed_sends_correct_user_agent():
    """The outgoing Request must carry the exact User-Agent string."""
    with patch("urllib.request.urlopen", return_value=_make_response("ok")) as mock_open:
        reddit_swgoh.fetch_feed("https://example.com/feed")
    req = mock_open.call_args[0][0]
    assert req.get_header("User-agent") == reddit_swgoh.USER_AGENT


def test_fetch_feed_retries_once_on_429():
    """A 429 response triggers exactly one retry; the retry's body is returned."""
    ok_ctx = _make_response("content-after-retry")
    with (
        patch(
            "urllib.request.urlopen",
            side_effect=[_http_error(429), ok_ctx],
        ) as mock_open,
        patch("time.sleep") as mock_sleep,
    ):
        result = reddit_swgoh.fetch_feed("https://example.com/feed")

    assert result == "content-after-retry"
    assert mock_open.call_count == 2
    mock_sleep.assert_called_once_with(reddit_swgoh.RETRY_SLEEP)


def test_fetch_feed_reraises_non_429_http_error_immediately():
    """A non-429 HTTPError is re-raised without retry and without sleep."""
    with (
        patch("urllib.request.urlopen", side_effect=_http_error(403)),
        patch("time.sleep") as mock_sleep,
    ):
        try:
            reddit_swgoh.fetch_feed("https://example.com/feed")
            assert False, "expected HTTPError"
        except urllib.error.HTTPError as exc:
            assert exc.code == 403
    mock_sleep.assert_not_called()


def test_fetch_feed_propagates_second_consecutive_429():
    """Two consecutive 429s: the second propagates (no infinite loop)."""
    with (
        patch("urllib.request.urlopen", side_effect=[_http_error(429), _http_error(429)]),
        patch("time.sleep"),
    ):
        try:
            reddit_swgoh.fetch_feed("https://example.com/feed")
            assert False, "expected HTTPError"
        except urllib.error.HTTPError as exc:
            assert exc.code == 429


# ---------------------------------------------------------------------------
# board_units / match_entries tests
# ---------------------------------------------------------------------------

NAME_MAP = {
    "GLREY": {"ct": 1, "n": "Rey"},
    "BENSOLO": {"ct": 1, "n": "Ben Solo"},
    "LORDVADER": {"ct": 1, "n": "Lord Vader"},
    "HONDO": {"ct": 1, "n": "Hondo Ohnaka"},
}


def test_board_units_collects_both_formats_and_perspectives():
    gac = {
        "5v5": {"defense": [{"units": ["GLREY", "BENSOLO"]}], "offense": [{"units": ["LORDVADER"]}]},
        "3v3": {"defense": [{"units": ["GLREY"]}], "offense": []},
    }
    assert reddit_swgoh.board_units(gac) == {"GLREY", "BENSOLO", "LORDVADER"}


def test_board_units_of_empty_result_is_empty():
    assert reddit_swgoh.board_units({}) == set()


def test_match_keeps_only_posts_naming_a_board_unit():
    entries = [
        {"title": "Lord Vader is still unkillable", "link": "a", "updated": "", "author": ""},
        {"title": "Best cantina farming route", "link": "b", "updated": "", "author": ""},
    ]
    out = reddit_swgoh.match_entries(entries, {"LORDVADER"}, NAME_MAP)
    assert len(out) == 1
    assert out[0]["units"] == ["LORDVADER"]


def test_match_ignores_units_not_on_the_board():
    entries = [{"title": "Why is Hondo Ohnaka a Galactic Legend?", "link": "a", "updated": "", "author": ""}]
    assert reddit_swgoh.match_entries(entries, {"LORDVADER"}, NAME_MAP) == []


def test_match_is_case_insensitive():
    entries = [{"title": "lord vader counters?", "link": "a", "updated": "", "author": ""}]
    out = reddit_swgoh.match_entries(entries, {"LORDVADER"}, NAME_MAP)
    assert len(out) == 1


def test_match_respects_word_boundaries():
    """'Rey' must not match inside 'Greyjoy' or 'Reyna'."""
    entries = [{"title": "Greyjoy tier list", "link": "a", "updated": "", "author": ""}]
    assert reddit_swgoh.match_entries(entries, {"GLREY"}, NAME_MAP) == []


def test_match_reports_every_board_unit_in_one_title():
    entries = [{"title": "Rey vs Ben Solo, who wins", "link": "a", "updated": "", "author": ""}]
    out = reddit_swgoh.match_entries(entries, {"GLREY", "BENSOLO"}, NAME_MAP)
    assert sorted(out[0]["units"]) == ["BENSOLO", "GLREY"]


# ---------------------------------------------------------------------------
# Regression tests for names ending in non-word characters (the \b defect).
# 78 of 829 display names end in ) or " or ', making trailing \b unmatchable
# even when the name appears verbatim in the title.  These tests use real
# name_type_map.json entries so they track production data, not invented names.
# ---------------------------------------------------------------------------

_REAL_NAME_MAP = json.load(
    open(os.path.join(os.path.dirname(__file__), "..", "data", "name_type_map.json"))
)


@pytest.mark.parametrize(
    "base_id",
    [
        "APPO",                       # ends in " (quote inside the name)
        "BASTILASHANDARK",            # ends in )
        "BOUSHH",                     # ends in )
        "CASSIANUNDERCOVER",          # ends in )
        "CT210408",                   # ends in "
        "MAULHATEFUELED",             # ends in )  — on 5v5 defense board in the live game
        "THEMANDALORIANBESKARARMOR",  # ends in )
        "KYLORENUNMASKED",            # ends in )
        "VADERDUELSEND",              # ends in '
    ],
)
def test_match_names_ending_in_non_word_char(base_id):
    """Names that end in ) or " or ' must fire when a title contains them verbatim.

    These all failed with the original \\b…\\b pattern because \\b asserts a
    word-to-non-word transition, but the name already ends in a non-word char,
    so there is no such transition at the position after the match.
    """
    display = _REAL_NAME_MAP[base_id]["n"]
    title = f"Thread about {display} in GAC defense"
    nm = {base_id: _REAL_NAME_MAP[base_id]}
    out = reddit_swgoh.match_entries(
        [{"title": title, "link": "x", "updated": "", "author": ""}],
        {base_id},
        nm,
    )
    assert out, (
        f"match_entries should have matched {base_id!r} ({display!r}) "
        f"in title {title!r}"
    )
    assert out[0]["units"] == [base_id]


def test_match_names_ending_in_quote_appo():
    """Spot-check: 'CC-1119 \"Appo\"' (ends in a double-quote) matches."""
    display = _REAL_NAME_MAP["APPO"]["n"]   # 'CC-1119 "Appo"'
    nm = {"APPO": _REAL_NAME_MAP["APPO"]}
    title = f"Is {display} worth farming?"
    out = reddit_swgoh.match_entries(
        [{"title": title, "link": "x", "updated": "", "author": ""}],
        {"APPO"},
        nm,
    )
    assert out, f"Expected APPO to match in: {title!r}"


def test_match_non_word_ending_name_does_not_match_when_glued_to_word_char():
    """Even after the fix, names must not match when glued to a word character.

    'Rey' from GLREY must not fire on 'Greyjoy' — the negative guard must hold.
    This re-asserts the existing test_match_respects_word_boundaries to confirm
    the lookahead fix does not regress on the case the original \\b handled.
    """
    entries = [
        {"title": "Greyjoy tier list", "link": "a", "updated": "", "author": ""},
        {"title": "Reynaldo counters?", "link": "b", "updated": "", "author": ""},
    ]
    # GLREY -> "Rey"
    result = reddit_swgoh.match_entries(entries, {"GLREY"}, NAME_MAP)
    assert result == [], "Rey must not fire on 'Greyjoy' or 'Reynaldo'"
