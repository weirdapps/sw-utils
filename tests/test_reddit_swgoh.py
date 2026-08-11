"""Tests for the r/SWGalaxyOfHeroes board-chatter signal (scripts/reddit_swgoh.py)."""
import os

import reddit_swgoh

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")


def _feed():
    with open(os.path.join(FIXTURES, "reddit_swgoh.rss"), encoding="utf-8") as fh:
        return fh.read()


def test_parse_feed_returns_all_entries():
    entries = reddit_swgoh.parse_feed(_feed())
    assert len(entries) == 25
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
