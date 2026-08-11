"""Tests for swgoh.gg GAC meta conversion (scripts/fetch_meta.py)."""
import json
import os

import fetch_meta
import swgoh_meta

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")
DATA_META = os.path.join(os.path.dirname(__file__), "..", "data", "meta")


def _rows_text():
    with open(os.path.join(FIXTURES, "gac_rows_5v5_def.txt")) as fh:
        return fh.read()


def test_rows_to_json_builds_the_expected_envelope():
    out = fetch_meta.rows_to_json(_rows_text(), "SEASON_80", "5v5", "defense", "2026-08-11")
    assert out["season"] == "SEASON_80"
    assert out["format"] == "5v5"
    assert out["perspective"] == "defense"
    assert out["pulled"] == "2026-08-11"
    assert len(out["rows"]) == 3


def test_rows_to_json_row_shape_matches_the_shipped_file():
    out = fetch_meta.rows_to_json(_rows_text(), "SEASON_80", "5v5", "defense", "2026-08-11")
    row = out["rows"][0]
    assert set(row) == {"hold", "seen", "banners", "units"}
    assert row["hold"] == "32%"
    assert row["seen"] == "34.9K"
    assert row["banners"] == "36.35"
    assert row["units"] == ["GLREY", "BENSOLO", "LUMINARAUNDULI"]


def test_rows_to_json_preserves_commas_inside_seen_counts():
    out = fetch_meta.rows_to_json(_rows_text(), "S", "5v5", "defense", "d")
    assert out["rows"][2]["seen"] == "7,837"
    assert out["rows"][2]["units"] == ["JANGOFETT", "4LOM", "ASAJJDARKDISCIPLE"]


def test_rows_to_json_skips_blank_lines():
    out = fetch_meta.rows_to_json("\n\n32%|1K|2|A,B\n\n", "S", "5v5", "defense", "d")
    assert len(out["rows"]) == 1


def test_output_round_trips_through_the_existing_parser(tmp_path):
    """The whole point of matching the format: swgoh_meta must read it unchanged."""
    out = fetch_meta.rows_to_json(_rows_text(), "SEASON_80", "5v5", "defense", "2026-08-11")
    path = tmp_path / "meta.json"
    path.write_text(json.dumps(out))
    parsed = swgoh_meta.parse_json_def(str(path))
    # parse_json_def returns a list of dicts with keys: rate, seen, seenN, ban, units
    assert len(parsed) == 3
    assert parsed[0]["rate"] == 32
    assert parsed[0]["seen"] == "34.9K"
    assert parsed[0]["units"] == ["GLREY", "BENSOLO", "LUMINARAUNDULI"]


def test_first_row_matches_shipped_5v5_defense_json():
    """Ground-truth: converting the real first extractor line yields byte-for-byte the shipped row."""
    first_line = "57%|29.8K|25.21|STRANGER,LUMINARAUNDULI,MAULHATEFUELED,STARKILLER,VISASMARR"
    out = fetch_meta.rows_to_json(first_line, "SEASON_80", "5v5", "defense", "2026-08-05")

    shipped_path = os.path.join(DATA_META, "meta_5v5_defense_s80.json")
    with open(shipped_path) as f:
        shipped = json.load(f)

    assert out["rows"][0] == shipped["rows"][0]
