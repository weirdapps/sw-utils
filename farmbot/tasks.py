"""tasks.py — EnergyDumpTask state machine. Device-free: all perception via injected `look`."""
from dataclasses import dataclass
from typing import Optional

TPL_HOME = "home"
TPL_SIM = "sim_button"
TPL_SIM_MAX = "sim_max"
TPL_CONFIRM = "sim_confirm"
TPL_REWARDS = "rewards"
TPL_BACK = "back"
TPL_ENERGY_OUT = "energy_out"


@dataclass
class Summary:
    nodes_attempted: int = 0
    sims_done: int = 0
    energy_out_nodes: int = 0
    halted: bool = False
    halt_state: Optional[str] = None
    stopped_reason: str = "complete"


class EnergyDumpTask:
    def __init__(self, nodes, look, tapper, should_stop=lambda: False,
                 halt=lambda state: None, max_actions=400, timeout=10.0,
                 energy_out_timeout=2.0, delay=lambda: None):
        self.nodes = nodes
        self.look = look
        self.tapper = tapper
        self.should_stop = should_stop
        self.halt = halt
        self.max_actions = max_actions
        self.timeout = timeout
        self.energy_out_timeout = energy_out_timeout
        self.delay = delay
        self._actions = 0

    def _steps_for(self, node):
        # (state, template_name, should_tap). HOME verifies only (no tap).
        return [
            ("HOME", TPL_HOME, False),
            ("CAMPAIGN", f"campaign_{node['campaign']}", True),
            ("NODE", f"node_{node['node']}", True),
            ("SIM_BUTTON", TPL_SIM, True),
            ("SIM_MAX", TPL_SIM_MAX, True),
            ("CONFIRM", TPL_CONFIRM, True),
            ("REWARDS", TPL_REWARDS, True),
            ("BACK", TPL_BACK, True),
            ("HOME", TPL_HOME, False),
        ]

    def run(self):
        self._actions = 0        # reset so run() is re-entrant (a re-run doesn't inherit the prior tap count)
        s = Summary()
        for node in self.nodes:
            if self.should_stop():
                s.stopped_reason = "killed"
                return s
            s.nodes_attempted += 1
            for state, tpl, should_tap in self._steps_for(node):
                if self._actions >= self.max_actions:
                    s.stopped_reason = "cap"
                    return s
                if self.should_stop():
                    s.stopped_reason = "killed"
                    return s
                m = self.look(tpl, self.timeout)
                if m is None:
                    if state == "CONFIRM" and \
                            self.look(TPL_ENERGY_OUT, self.energy_out_timeout) is not None:
                        s.energy_out_nodes += 1
                        break                      # this node's energy type is out → next node
                    self.halt(state)
                    s.halted = True
                    s.halt_state = state
                    s.stopped_reason = "halt"
                    return s
                if should_tap:
                    self.tapper(m.cx, m.cy)
                    self._actions += 1
                    self.delay()
                    if state == "CONFIRM":
                        s.sims_done += 1
        return s
