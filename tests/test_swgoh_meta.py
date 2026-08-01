"""Tests for swgoh_meta parsing (extracted from compute_teams for reuse)."""
import json

import swgoh_meta as sm


def test_seen_num_handles_k_and_m_suffixes():
    assert sm.seen_num("1.2M") == 1_200_000
    assert sm.seen_num("12.3K") == 12_300
    assert sm.seen_num("450") == 450


def test_parse_txt_reads_pipe_rows(tmp_path):
    f = tmp_path / "off.txt"
    f.write_text("ROWS=1\n82%|12.3K|48.5|BAYLAN,MARROK,SHIN\n")
    rows = sm.parse_txt(str(f))
    assert rows[0]["rate"] == 82
    assert rows[0]["units"] == ["BAYLAN", "MARROK", "SHIN"]
    assert rows[0]["seenN"] == 12_300


def test_parse_json_def_reads_hold_rows(tmp_path):
    f = tmp_path / "def.json"
    f.write_text(json.dumps({"rows": [
        {"hold": "38%", "seen": "1.1K", "banners": "55.0", "units": ["GLHONDO", "VANE"]}]}))
    rows = sm.parse_json_def(str(f))
    assert rows[0]["rate"] == 38
    assert rows[0]["units"] == ["GLHONDO", "VANE"]


def test_load_meta_routes_json_and_txt(tmp_path):
    (tmp_path / "d.json").write_text(json.dumps({"rows": [
        {"hold": "50%", "seen": "1K", "banners": "1", "units": ["A"]}]}))
    (tmp_path / "o.txt").write_text("40%|2K|1|B,C\n")
    meta = sm.load_meta({("5v5", "def"): "d.json", ("5v5", "off"): "o.txt"}, str(tmp_path))
    assert meta[("5v5", "def")][0]["rate"] == 50
    assert meta[("5v5", "off")][0]["units"] == ["B", "C"]
