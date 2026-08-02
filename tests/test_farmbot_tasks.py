from collections import namedtuple

from farmbot.tasks import EnergyDumpTask

M = namedtuple("M", ["cx", "cy", "confidence"])

# The templates present on the real happy-path flow for one cantina node "1-A" (no chapter).
FLOW = {"home", "campaigns_entry", "campaigns_menu", "campaign_cantina",
        "node_1-A", "multi_sim", "sim_confirm", "rewards", "home_button"}
NODE = {"campaign": "cantina", "node": "1-A", "sim": "max"}


def scripted_look(present, sequences=None):
    """Return a `look(name, timeout)` that yields a Match for names in `present`.

    `sequences` (name -> list[bool]) overrides `present` for that template on a
    per-call basis (True = present that call), so a test can make e.g. sim_confirm
    absent for node 1 and present for node 2.
    """
    seqs = {k: iter(v) for k, v in (sequences or {}).items()}

    def look(name, timeout):
        if name in seqs:
            try:
                return M(10, 20, 0.99) if next(seqs[name]) else None
            except StopIteration:
                pass
        return M(10, 20, 0.99) if name in present else None

    return look


def test_happy_path_seven_taps_one_sim():
    taps = []
    task = EnergyDumpTask([NODE], scripted_look(FLOW), lambda x, y: taps.append((x, y)))
    s = task.run()
    assert s.stopped_reason == "complete"
    assert s.nodes_attempted == 1
    assert s.sims_done == 1
    assert s.energy_out_nodes == 0
    assert s.halted is False
    # taps = OPEN_CAMPAIGNS, SELECT_CAMPAIGN, SELECT_NODE, OPEN_MULTISIM,
    #        CONFIRM_SIM, REWARDS, RETURN_HOME = 7 (HOME + CAMPAIGNS_MENU verify only)
    assert len(taps) == 7


def test_chapter_adds_one_tap():
    node = {"campaign": "cantina", "chapter": 1, "node": "1-A", "sim": "max"}
    taps = []
    task = EnergyDumpTask([node], scripted_look(FLOW | {"chapter_tab_1"}),
                          lambda x, y: taps.append((x, y)))
    s = task.run()
    assert s.sims_done == 1
    assert len(taps) == 8       # + SELECT_CHAPTER


def test_unknown_screen_halts():
    halts = []
    present = FLOW - {"multi_sim"}       # panel reached but MULTI SIM never appears (not energy-out)
    task = EnergyDumpTask([NODE], scripted_look(present), lambda x, y: None,
                          halt=lambda st: halts.append(st))
    s = task.run()
    assert s.halted is True
    assert s.halt_state == "OPEN_MULTISIM"
    assert s.stopped_reason == "halt"
    assert halts == ["OPEN_MULTISIM"]


def test_energy_out_skips_and_recovers_without_halting():
    # confirm absent + energy_out (Purchase prompt) shown -> tap CANCEL + home_button; no halt.
    present = (FLOW - {"sim_confirm"}) | {"energy_out"}
    taps = []
    task = EnergyDumpTask([NODE], scripted_look(present), lambda x, y: taps.append((x, y)))
    s = task.run()
    assert s.halted is False
    assert s.energy_out_nodes == 1
    assert s.sims_done == 0
    assert s.stopped_reason == "complete"
    # 4 nav taps before confirm + 2 recovery taps (energy_out=CANCEL, home_button)
    assert len(taps) == 6


def test_kill_switch_before_first_node():
    task = EnergyDumpTask([NODE], scripted_look(FLOW), lambda x, y: None,
                          should_stop=lambda: True)
    s = task.run()
    assert s.stopped_reason == "killed"
    assert s.nodes_attempted == 0


def test_action_cap_stops_run():
    task = EnergyDumpTask([NODE], scripted_look(FLOW), lambda x, y: None, max_actions=3)
    s = task.run()
    assert s.stopped_reason == "cap"
    assert s.sims_done == 0


def test_run_is_reentrant():
    task = EnergyDumpTask([NODE], scripted_look(FLOW), lambda x, y: None)
    s1 = task.run()
    s2 = task.run()
    assert (s1.nodes_attempted, s1.sims_done) == (1, 1)
    assert (s2.nodes_attempted, s2.sims_done) == (1, 1)
    assert s2 == s1                 # identical Summary — counters not inflated across runs


def test_multi_node_continues_after_energy_out():
    n1 = {"campaign": "cantina", "node": "1-A", "sim": "max"}
    n2 = {"campaign": "light", "node": "1-A", "sim": "max"}
    present = {"home", "campaigns_entry", "campaigns_menu", "campaign_cantina",
               "campaign_light", "node_1-A", "multi_sim", "rewards", "home_button",
               "energy_out"}
    # sim_confirm: absent for node 1 (-> energy-out), present for node 2 (-> sim)
    look = scripted_look(present, sequences={"sim_confirm": [False, True]})
    task = EnergyDumpTask([n1, n2], look, lambda x, y: None)
    s = task.run()
    assert s.nodes_attempted == 2
    assert s.energy_out_nodes == 1
    assert s.sims_done == 1
    assert s.halted is False
    assert s.stopped_reason == "complete"


def test_campaign_tap_uses_play_offset():
    # SELECT_CAMPAIGN matches the title but taps the PLAY button below it (offset 0,+673),
    # because tapping the title only flips the card. Match center is (10,20) here.
    taps = []
    task = EnergyDumpTask([NODE], scripted_look(FLOW), lambda x, y: taps.append((x, y)))
    task.run()
    assert (10, 20 + 673) in taps
    assert taps.count((10, 693)) == 1


def test_node_tap_retries_until_panel_opens():
    # Tapping an already-selected node can toggle its panel shut. SELECT_NODE ensures
    # MULTI SIM appears; here multi_sim is absent on the first check then present after a re-tap.
    taps = []
    present = FLOW | {"multi_sim"}                       # fallback True after the sequence
    look = scripted_look(present, sequences={"multi_sim": [False, True]})
    task = EnergyDumpTask([NODE], look, lambda x, y: taps.append((x, y)))
    s = task.run()
    assert s.halted is False
    assert s.sims_done == 1
    assert len(taps) == 8        # 7 happy-path taps + 1 node re-tap
