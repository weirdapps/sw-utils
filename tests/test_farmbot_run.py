import json
import pytest
from farmbot import run
from farmbot.tasks import Summary


def test_parse_args_defaults():
    ns = run.parse_args([])
    assert ns.config.endswith("config.json")
    assert ns.dry_run is False


def test_load_config_ok(tmp_path):
    p = tmp_path / "c.json"
    p.write_text(json.dumps({
        "device_serial": "s",
        "caps": {"max_actions": 10, "action_delay_ms": [1, 2]},
        "vision": {"match_threshold": 0.9, "step_timeout_s": 5, "energy_out_timeout_s": 1},
        "nodes": [{"campaign": "cantina", "node": "5-D", "sim": "max"}],
    }))
    cfg = run.load_config(str(p))
    assert cfg["device_serial"] == "s"


def test_load_config_missing_key_raises(tmp_path):
    p = tmp_path / "c.json"
    p.write_text(json.dumps({"device_serial": "s"}))
    with pytest.raises(ValueError):
        run.load_config(str(p))


def test_kill_switch_reads_stop_file(tmp_path):
    flag = tmp_path / "STOP"
    should_stop = run.make_kill_switch(str(flag))
    assert should_stop() is False
    flag.write_text("")
    assert should_stop() is True


def test_make_delay_sleeps_within_range():
    slept = []
    d = run.make_delay([700, 1800], sleeper=lambda s: slept.append(s),
                       rng=lambda lo, hi: (lo + hi) / 2)
    d()
    assert slept == [1.25]          # 1250 ms → 1.25 s


def test_format_summary_mentions_counts():
    out = run.format_summary(Summary(nodes_attempted=2, sims_done=5, stopped_reason="complete"))
    assert "2" in out and "5" in out and "complete" in out


def test_make_swipe_directions():
    calls = []

    class FakeADB:
        def swipe(self, x1, y1, x2, y2, ms):
            calls.append((x1, x2))

    sw = run.make_swipe(FakeADB(), near=500, far=1400)
    sw("left")
    sw("right")
    assert calls[0] == (1400, 500)   # "left" reveals later nodes: drag content far->near
    assert calls[1] == (500, 1400)   # "right" reveals earlier nodes: near->far


def test_make_swipe_scrolls_a_vertical_list():
    """The Quests list has to be dragged vertically; the map scan's left/right does nothing to it."""
    calls = []

    class FakeADB:
        def swipe(self, x1, y1, x2, y2, ms):
            calls.append((y1, y2))

    sw = run.make_swipe(FakeADB(), top=300, bottom=900)
    sw("up")
    sw("down")
    assert calls[0] == (900, 300)    # "up" drags content up = reveals the rows below the fold
    assert calls[1] == (300, 900)


def test_load_config_accepts_routine_key(tmp_path):
    p = tmp_path / "c.json"
    p.write_text(json.dumps({
        "device_serial": "s",
        "caps": {"max_actions": 10, "action_delay_ms": [1, 2]},
        "vision": {"match_threshold": 0.9, "step_timeout_s": 5, "energy_out_timeout_s": 1},
        "routine": [{"kind": "collect", "claim": "login_claim"}],
    }))
    cfg = run.load_config(str(p))
    assert run.routine_of(cfg)[0]["kind"] == "collect"


def test_load_config_missing_routine_and_nodes_raises(tmp_path):
    p = tmp_path / "c.json"
    p.write_text(json.dumps({
        "device_serial": "s",
        "caps": {"max_actions": 10, "action_delay_ms": [1, 2]},
        "vision": {"match_threshold": 0.9, "step_timeout_s": 5, "energy_out_timeout_s": 1},
    }))
    with pytest.raises(ValueError):
        run.load_config(str(p))


def test_routine_of_prefers_routine_over_nodes():
    assert run.routine_of({"routine": [1], "nodes": [2, 3]}) == [1]
    assert run.routine_of({"nodes": [2, 3]}) == [2, 3]
    assert run.routine_of({}) == []


def test_parse_args_daily_flag():
    assert run.parse_args(["--daily"]).daily is True
    assert run.parse_args([]).daily is False


def test_format_summary_includes_collector_counts():
    out = run.format_summary(Summary(collected=3, challenges_simmed=2, energy_claimed=1,
                                     nothing_to_collect=4, stopped_reason="complete"))
    assert "collected=3" in out
    assert "challenges_simmed=2" in out
    assert "energy_claimed=1" in out
    assert "nothing_to_collect=4" in out


def test_example_config_is_valid_and_mixed_kind():
    import os
    path = os.path.join(os.path.dirname(run.__file__), "config.example.json")
    cfg = run.load_config(path)
    kinds = {e.get("kind", "energy_node") for e in run.routine_of(cfg)}
    assert {"energy_node", "collect", "challenge_sim", "battle"} <= kinds


def test_format_summary_includes_battle_counts():
    out = run.format_summary(Summary(battles_won=3, battles_lost=1, stopped_reason="complete"))
    assert "battles_won=3" in out
    assert "battles_lost=1" in out


def test_format_summary_includes_halted_entries():
    out = run.format_summary(Summary(halted_entries=2, stopped_reason="complete"))
    assert "halted_entries=2" in out


def test_example_config_includes_a_conservative_conquest_entry():
    """Conquest is stamina-bound (-10% per battle per character) and node choice is strategic,
    so the shipped default fights the smallest number of nodes that is still useful."""
    import os
    path = os.path.join(os.path.dirname(run.__file__), "config.example.json")
    cfg = run.load_config(path)
    entries = [e for e in run.routine_of(cfg) if e.get("kind") == "conquest"]
    assert len(entries) == 1
    entry = entries[0]
    assert entry["pan"] == "far_right"          # the console is off the hub's default pan
    assert entry["max_battles"] <= 2            # stamina, not energy, is the budget
    assert entry["battles"] == [{"node": "conquest_node_open", "count": 2}]
    # the cap has to bind the expanded count, not just the length of the list
    assert sum(b.get("count", 1) for b in entry["battles"]) <= entry["max_battles"]


def test_example_config_coliseum_no_longer_smuggles_a_tap_into_nav():
    """The first of the two BATTLE presses used to live in `nav`, which is why attempt 1 worked
    and attempts 2+ stranded. Both presses belong to the per-attempt loop now, so keeping the nav
    hop would press BATTLE three times on the first attempt."""
    import os
    path = os.path.join(os.path.dirname(run.__file__), "config.example.json")
    cfg = run.load_config(path)
    entry = [e for e in run.routine_of(cfg) if e.get("name") == "coliseum"][0]
    assert entry["start"] == "battle_start"
    assert entry["nav"] == ["coliseum_tile"]
