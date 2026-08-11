from farmbot.devtool import coverage, required_templates
from farmbot.run import doctor

CANTINA = {"campaign": "cantina", "node": "1-A", "sim": "max"}


def _write(tmp_path, *names):
    for n in names:
        (tmp_path / f"{n}.png").write_bytes(b"")
    return str(tmp_path)


def test_required_templates_separates_blocking_from_soft():
    blocking, soft = required_templates([CANTINA])
    # the nav chain must exist or the entry halts
    assert {"home", "campaigns_entry", "campaigns_menu", "campaign_cantina",
            "node_cantina_1-A", "multi_sim", "sim_confirm"} <= set(blocking)
    # skip markers only downgrade a graceful skip into a halt, so they are soft
    assert "energy_out" in soft
    assert "energy_out" not in blocking


def test_popup_closers_count_as_used_not_unused():
    """They are looked for on every screen-miss, so reporting them as 'unused' would be noise."""
    _, soft = required_templates([CANTINA])
    assert "popup_close" in soft


def test_coverage_reports_a_genuinely_missing_template(tmp_path):
    have = _write(tmp_path, "home", "campaigns_entry", "campaigns_menu", "campaign_cantina",
                  "multi_sim", "sim_confirm", "rewards", "home_button")
    missing, degraded, unused = coverage([CANTINA], have)
    assert "node_cantina_1-A" in missing          # never captured -> the entry would halt
    assert "energy_out" in degraded               # absent but handled
    assert unused == []


def test_coverage_flags_captured_but_unasked_templates(tmp_path):
    have = _write(tmp_path, "home", "campaigns_entry", "campaigns_menu", "campaign_cantina",
                  "node_cantina_1-A", "multi_sim", "sim_confirm", "rewards", "home_button",
                  "energy_out", "hard_depleted", "popup_close", "newsletter_close", "leftover")
    missing, _, unused = coverage([CANTINA], have)
    assert missing == {}
    assert unused == ["leftover"]


def test_required_templates_tracks_the_new_kinds():
    """Coverage is derived from the engine's own Steps, so a new kind is covered automatically."""
    routine = [
        {"kind": "sequence", "name": "gw", "nav": [{"template": "quests_entry"}],
         "taps": [{"template": "gw_multisim"}]},
        {"kind": "shop", "name": "s", "nav": ["shipments_entry"],
         "buys": [{"item": "buy_thing"}], "confirm": "shop_confirm_cantina"},
    ]
    blocking, soft = required_templates(routine)
    assert "quests_entry" in blocking and "shipments_entry" in blocking
    assert "gw_multisim" in soft and "buy_thing" in soft      # both optional by design


def test_an_uncaptured_alt_outcome_does_not_fail_preflight():
    """`tier_complete` has no crop yet. An alt outcome is a fallback skin of a screen the entry
    already handles, so its absence costs only the graceful path — preflight warns, never fails."""
    entry = {"kind": "battle", "name": "coliseum", "nav": ["coliseum_tile"],
             "start": "battle_start", "victory_alt": ["tier_complete"]}
    blocking, soft = required_templates([entry])
    assert "tier_complete" in soft
    assert "tier_complete" not in blocking


def test_alternative_skip_markers_are_soft_not_blocking():
    """The second depleted-panel crop (Fleet Hard's 💎200 chip) isn't captured yet; like the first
    it only downgrades a graceful skip into a halt, which --daily isolates."""
    entry = {"campaign": "fleet", "difficulty": "hard", "chapter": 1, "node": "1-E", "sim": "max"}
    blocking, soft = required_templates([entry])
    assert "hard_depleted_200" in soft
    assert "hard_depleted_200" not in blocking


def test_doctor_fails_on_a_missing_blocking_template(tmp_path):
    cfg = {"device_serial": "x", "caps": {}, "vision": {}, "routine": [CANTINA]}
    ok, lines = doctor(cfg, template_dir=_write(tmp_path, "home"), device_ready=True)
    assert ok is False
    assert any("MISSING" in ln for ln in lines)


def test_doctor_fails_when_the_device_is_down(tmp_path):
    cfg = {"device_serial": "x", "caps": {}, "vision": {}, "routine": []}
    ok, lines = doctor(cfg, template_dir=_write(tmp_path), device_ready=False)
    assert ok is False
    assert any("NOT READY" in ln for ln in lines)


def test_doctor_passes_when_only_soft_templates_are_absent(tmp_path):
    """A soft-missing skip marker is a warning, not a preflight failure — the run still works."""
    have = _write(tmp_path, "home", "campaigns_entry", "campaigns_menu", "campaign_cantina",
                  "node_cantina_1-A", "multi_sim", "sim_confirm", "rewards", "home_button")
    cfg = {"device_serial": "x", "caps": {}, "vision": {}, "routine": [CANTINA],
           "manual": [{"task": "t", "why": "w"}]}
    ok, lines = doctor(cfg, template_dir=have, device_ready=True)
    assert ok is True
    assert any("soft-missing" in ln for ln in lines)


def test_doctor_warns_when_no_manual_checklist_is_configured(tmp_path):
    cfg = {"device_serial": "x", "caps": {}, "vision": {}, "routine": []}
    _, lines = doctor(cfg, template_dir=_write(tmp_path), device_ready=True)
    assert any("no residual checklist" in ln for ln in lines)


def test_a_malformed_entry_is_reported_not_raised(tmp_path):
    """A preflight that prints a traceback and nothing else is worse than no preflight — the whole
    point is to list every problem in one pass."""
    blocking, _ = required_templates([{"kind": "teleport"}, CANTINA])
    assert any(n.startswith("<malformed entry") for n in blocking)
    assert "node_cantina_1-A" in blocking            # the valid entry was still analysed

    cfg = {"device_serial": "x", "caps": {}, "vision": {},
           "routine": [{"kind": "teleport"}]}
    ok, lines = doctor(cfg, template_dir=_write(tmp_path), device_ready=True)
    assert ok is False
    assert any("malformed entry" in ln for ln in lines)


def test_an_offset_popup_closer_is_still_counted_as_used():
    """A closer may carry a tap offset. Coverage has to read its template name, not the pair, or
    `coliseum_results` reports as an unused leftover and the sort blows up."""
    _, soft = required_templates([CANTINA])
    assert "coliseum_results" in soft


def test_required_templates_covers_the_conquest_kind():
    entry = {"kind": "conquest", "name": "conquest", "pan": "far_right", "disks": 1,
             "battles": [{"node": "conquest_node_1a"}]}
    blocking, soft = required_templates([entry])
    assert {"galactic_battles", "conquest_card", "conquest_header", "conquest_enter",
            "conquest_feats_panel"} <= set(blocking)
    # the free disk may already be gone and a node may already be cleared: both skip, never halt
    assert "conquest_disk_stockpile" in soft
    assert "conquest_node_1a" in soft
