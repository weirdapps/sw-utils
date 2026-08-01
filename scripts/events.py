#!/usr/bin/env python3
"""events.py — A4 upcoming events (swgohevents.com iCalendar feed).

Reads the public https://swgohevents.com/ical feed (text/calendar, no auth, not
Cloudflare-blocked) into structured upcoming events. Unit-unlocking event types
(Legendary / Journey / Galactic Legend / Marquee) are flagged as notable — those
are the "don't miss" windows for closing roster gaps like GL Hondo.

Usage:  python3 scripts/events.py
"""
import urllib.request

ICAL_URL = "https://swgohevents.com/ical"
NOTABLE = ("LEGENDARY", "JOURNEY", "GALACTIC LEGEND", "MARQUEE")


def _unfold(text):
    """RFC 5545 line unfolding: a newline followed by a space/tab continues the line."""
    return text.replace("\r\n", "\n").replace("\n ", "").replace("\n\t", "")


def parse_ics(text):
    """Parse an iCalendar string into a list of event dicts (name/date/category/desc/url)."""
    out = []
    cur = None
    for line in _unfold(text).split("\n"):
        if line == "BEGIN:VEVENT":
            cur = {}
        elif line == "END:VEVENT":
            if cur is not None:
                out.append(cur)
                cur = None
        elif cur is not None and ":" in line:
            raw_key, _, val = line.partition(":")
            key = raw_key.split(";")[0]  # drop params, e.g. DTSTART;VALUE=DATE
            field = {"SUMMARY": "name", "DTSTART": "date", "DTEND": "end",
                     "CATEGORIES": "category", "URL": "url", "DESCRIPTION": "desc"}.get(key)
            if field:
                cur[field] = val
    return out


def is_notable(event):
    cat = (event.get("category") or "").upper()
    return any(n in cat for n in NOTABLE)


def fetch_ical(url=ICAL_URL, timeout=20):
    req = urllib.request.Request(url, headers={"User-Agent": "sw-utils/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "replace")


def filter_upcoming(evs, today):
    """Drop events before `today` (YYYYMMDD) and sort ascending by date.
    ISO-basic dates sort correctly as plain strings."""
    return sorted((e for e in evs if e.get("date", "") >= today),
                  key=lambda e: e.get("date", ""))


def _today_athens():
    from datetime import datetime
    try:
        from zoneinfo import ZoneInfo
        return datetime.now(ZoneInfo("Europe/Athens")).strftime("%Y%m%d")
    except Exception:
        return datetime.now().strftime("%Y%m%d")


def upcoming_events(url=ICAL_URL, today=None):
    evs = parse_ics(fetch_ical(url))
    return filter_upcoming(evs, today or _today_athens())


def fmt_date(d):
    return f"{d[:4]}-{d[4:6]}-{d[6:8]}" if d and len(d) == 8 else (d or "?")


if __name__ == "__main__":
    evs = upcoming_events()
    print(f"Upcoming events — {len(evs)} in the swgohevents calendar\n")
    for e in evs:
        star = "  ⭐ notable" if is_notable(e) else ""
        print(f"  {fmt_date(e.get('date'))}  {e.get('name', '?')}  [{e.get('category', '?')}]{star}")
