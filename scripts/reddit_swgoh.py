#!/usr/bin/env python3
"""reddit_swgoh.py - board-relevant chatter from r/SWGalaxyOfHeroes.

Reads the public Atom feed. No OAuth: Reddit closed unauthenticated .json in
May 2026 but left .rss open. The trade is that RSS carries no score and no
comment counts, so entries can be ranked by recency and relevance only, never
by popularity.

Usage:  python3 scripts/reddit_swgoh.py
"""
import html
import json
import os
import re
import time
import urllib.error
import urllib.request

# defusedxml, not xml.etree: stdlib ElementTree does not expand external
# entities (so XXE is not the concern) but it is vulnerable to entity-expansion
# DoS. This parses bytes off the network, so use the hardened parser.
from defusedxml import ElementTree as ET

FEED_URL = "https://www.reddit.com/r/SWGalaxyOfHeroes/hot/.rss?limit=25"
USER_AGENT = "sw-utils-brief/1.0 (personal use)"
ATOM = "{http://www.w3.org/2005/Atom}"
RETRY_SLEEP = 30

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GAC_RESULT = os.path.join(ROOT, "data", "gac_result.json")
NAME_MAP_FILE = os.path.join(ROOT, "data", "name_type_map.json")


def parse_feed(xml_text):
    """Parse an Atom feed into [{"title","link","updated","author"}]."""
    root = ET.fromstring(xml_text)
    entries = []
    for entry in root.findall(f"{ATOM}entry"):
        title_el = entry.find(f"{ATOM}title")
        link_el = entry.find(f"{ATOM}link")
        updated_el = entry.find(f"{ATOM}updated")
        author_el = entry.find(f"{ATOM}author/{ATOM}name")
        title = html.unescape((title_el.text or "").strip()) if title_el is not None else ""
        entries.append(
            {
                "title": title,
                "link": link_el.get("href", "") if link_el is not None else "",
                "updated": (updated_el.text or "")[:10] if updated_el is not None else "",
                "author": (author_el.text or "") if author_el is not None else "",
            }
        )
    return entries


def fetch_feed(url=FEED_URL):
    """Fetch the feed. Retries once on 429, which is the unauth throttle."""
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        if exc.code != 429:
            raise
        time.sleep(RETRY_SLEEP)
        with urllib.request.urlopen(req, timeout=20) as resp:
            return resp.read().decode("utf-8", errors="replace")


def board_units(gac_result):
    """Every base id currently placed on the board, both formats, both sides."""
    units = set()
    for fmt in gac_result.values():
        for perspective in ("defense", "offense"):
            for squad in fmt.get(perspective, []):
                units.update(squad.get("units", []))
    return units


def match_entries(entries, units, name_map):
    """Keep only entries naming a board unit; annotate with the ids matched.

    Matching is on the display name with word boundaries, so 'Rey' does not fire
    on 'Greyjoy'. Entries naming no board unit are dropped rather than ranked
    low: the section is about the board, not about the subreddit.
    """
    patterns = []
    for base_id in units:
        display = (name_map.get(base_id) or {}).get("n")
        if not display:
            continue
        patterns.append((base_id, re.compile(rf"\b{re.escape(display)}\b", re.IGNORECASE)))

    matched = []
    for entry in entries:
        hits = [base_id for base_id, pattern in patterns if pattern.search(entry["title"])]
        if hits:
            item = dict(entry)
            item["units"] = sorted(hits)
            matched.append(item)
    return matched


def load_board_chatter(feed_xml=None, gac_path=GAC_RESULT, name_map_path=NAME_MAP_FILE):
    """End to end: feed plus board plus names -> board-relevant entries."""
    xml_text = feed_xml if feed_xml is not None else fetch_feed()
    with open(gac_path) as fh:
        gac = json.load(fh)
    with open(name_map_path) as fh:
        name_map = json.load(fh)
    return match_entries(parse_feed(xml_text), board_units(gac), name_map)
