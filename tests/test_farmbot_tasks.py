from collections import namedtuple
from farmbot.tasks import EnergyDumpTask, Summary

M = namedtuple("M", ["cx", "cy", "confidence"])
NODES = [{"campaign": "cantina", "node": "5-D", "sim": "max"}]


def make_look(present):
    """Return a `look` that yields a Match for any template name in `present`, else None."""
    def look(name, timeout):
        return M(10, 20, 0.99) if name in present else None
    return look


ALL_TPLS = {"home", "campaign_cantina", "node_5-D", "sim_button", "sim_max",
            "sim_confirm", "rewards", "back"}


def test_happy_path_taps_and_counts_one_sim():
    taps = []
    task = EnergyDumpTask(NODES, make_look(ALL_TPLS), lambda x, y: taps.append((x, y)))
    s = task.run()
    assert s.stopped_reason == "complete"
    assert s.nodes_attempted == 1
    assert s.sims_done == 1
    # taps = CAMPAIGN, NODE, SIM, MAX, CONFIRM, REWARDS, BACK = 7 (2 HOME verifies don't tap)
    assert len(taps) == 7
    assert s.halted is False


def test_unknown_screen_halts():
    halts = []
    present = ALL_TPLS - {"sim_button"}          # SIM screen never appears, not energy-out
    task = EnergyDumpTask(NODES, make_look(present), lambda x, y: None,
                          halt=lambda state: halts.append(state))
    s = task.run()
    assert s.halted is True
    assert s.halt_state == "SIM_BUTTON"
    assert s.stopped_reason == "halt"
    assert halts == ["SIM_BUTTON"]


def test_energy_out_skips_node_without_halting():
    present = (ALL_TPLS - {"sim_confirm"}) | {"energy_out"}   # confirm absent, energy-out shown
    task = EnergyDumpTask(NODES, make_look(present), lambda x, y: None)
    s = task.run()
    assert s.halted is False
    assert s.energy_out_nodes == 1
    assert s.sims_done == 0
    assert s.stopped_reason == "complete"


def test_kill_switch_stops_before_next_node():
    task = EnergyDumpTask(NODES, make_look(ALL_TPLS), lambda x, y: None,
                          should_stop=lambda: True)
    s = task.run()
    assert s.stopped_reason == "killed"
    assert s.nodes_attempted == 0


def test_action_cap_stops_run():
    task = EnergyDumpTask(NODES, make_look(ALL_TPLS), lambda x, y: None, max_actions=3)
    s = task.run()
    assert s.stopped_reason == "cap"
    assert s.sims_done == 0


def test_run_is_reentrant_second_run_matches_first():
    # max_actions=10 lets one run (7 taps) complete cleanly, but if the action
    # counter isn't reset it carries over and trips the cap partway through run #2.
    taps = []
    task = EnergyDumpTask(NODES, make_look(ALL_TPLS),
                          lambda x, y: taps.append((x, y)), max_actions=10)
    s1 = task.run()
    n1 = len(taps)
    s2 = task.run()
    n2 = len(taps) - n1
    assert s1.stopped_reason == "complete" and s1.sims_done == 1 and n1 == 7
    assert s2 == s1                 # identical Summary — counters not inflated
    assert s2.stopped_reason == "complete" and s2.sims_done == 1
    assert n2 == 7                  # second run taps the full node, cap not tripped
