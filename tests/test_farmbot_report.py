from farmbot import report
from farmbot.tasks import Summary


def test_report_lists_what_ran_and_omits_zero_counters():
    s = Summary(nodes_attempted=3, sims_done=2, collected=5)
    text = report.render(s, "2026-08-03 19:00")
    assert "**2** energy nodes simmed" in text
    assert "**5** free rewards collected" in text
    assert "auto-battles won" not in text        # zero counters are dropped, not printed as 0


def test_report_always_states_the_safety_rails_even_at_zero():
    """0 refused purchases is the good news, so it is printed rather than dropped — the report is
    the only place the operator sees the rails held."""
    text = report.render(Summary(), "2026-08-03 19:00")
    assert "crystal-priced purchases refused: **0**" in text
    assert "PvP matches played: **0**" in text


def test_report_flags_a_crystal_balance_change():
    ok = report.render(Summary(), "t", crystals_before=5340, crystals_after=5340)
    assert "unchanged ✅" in ok
    bad = report.render(Summary(), "t", crystals_before=5340, crystals_after=5290)
    assert "CHANGED BY -50" in bad


def test_report_calls_out_a_tripped_spend_guard():
    text = report.render(Summary(blocked_spends=2), "t")
    assert "refused: **2**" in text
    assert "the guard fired" in text


def test_report_carries_the_residual_manual_checklist():
    manual = [{"task": "Squad Arena battle", "why": "PvP"}]
    text = report.render(Summary(), "t", manual=manual)
    assert "Still yours" in text
    assert "- [ ] **Squad Arena battle** — PvP" in text


def test_report_says_so_when_no_manual_list_is_configured():
    assert "none configured" in report.render(Summary(), "t")


def test_report_surfaces_halts_with_the_step_label():
    text = report.render(Summary(halted_entries=1, halt_state="SELECT_NODE"), "t")
    assert "Needs a look" in text
    assert "`SELECT_NODE`" in text


def test_report_says_nothing_happened_rather_than_printing_an_empty_list():
    assert "nothing — every entry was already done" in report.render(Summary(), "t")


def test_write_appends_a_trailing_newline(tmp_path):
    p = tmp_path / "r.md"
    report.write(str(p), "body")
    assert p.read_text() == "body\n"
