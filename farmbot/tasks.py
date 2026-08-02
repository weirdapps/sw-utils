"""tasks.py — EnergyDumpTask state machine. Device-free: all perception via injected `look`.

Models the REAL SWGOH energy-dump flow (validated live 2026-08-02), one node at a time,
each an independent journey that starts and ends at the hub:

    HOME (verify) -> tap Campaigns -> Campaigns menu (verify) -> tap <campaign> PLAY
      -> [optional: tap chapter tab] -> tap node icon -> tap MULTI SIM
      -> SIM dialog (pre-set to max energy) -> tap SIM confirm -> rewards -> tap home button

Multi Sim auto-fills the quantity to the max the current energy allows, so there is no
"set max" step. Energy-out shows as the confirm being unavailable while an energy_out marker
is present -> that node is skipped (never refreshed with crystals) and we recover to the hub.
"""
from dataclasses import dataclass
from typing import Optional

# Reusable screen/element templates (captured once, shared across all energy types).
TPL_HOME = "home"                       # we are on the hub screen (verify only)
TPL_CAMPAIGNS_ENTRY = "campaigns_entry"  # the "Campaigns" button on the hub
TPL_CAMPAIGNS_MENU = "campaigns_menu"    # the Campaigns menu is open (verify only)
TPL_MULTI_SIM = "multi_sim"              # the MULTI SIM button on a node's detail panel
TPL_SIM_CONFIRM = "sim_confirm"          # the green SIM confirm in the Multi Sim dialog
TPL_REWARDS = "rewards"                  # the post-sim rewards popup (tap to dismiss)
TPL_DIALOG_CLOSE = "dialog_close"        # the red X that closes the Multi Sim dialog
TPL_HOME_BUTTON = "home_button"          # the house icon that returns to the hub
TPL_ENERGY_OUT = "energy_out"            # marker that the node's energy is exhausted


@dataclass
class Step:
    label: str
    template: str
    tap: bool = True             # False = verify the screen only, no tap
    energy_out_here: bool = False  # absence + energy_out marker => skip node (not halt)
    mark_sim: bool = False       # a successful tap here counts as one sim dump


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
        """Build the ordered Step list for one node from its compact config entry.

        node = {"campaign": <name>, "node": <id>, ["chapter": <n>], "sim": "max"}
        Per-node templates are named campaign_<name>, chapter_tab_<n>, node_<id>.
        """
        steps = [
            Step("HOME", TPL_HOME, tap=False),
            Step("OPEN_CAMPAIGNS", TPL_CAMPAIGNS_ENTRY),
            Step("CAMPAIGNS_MENU", TPL_CAMPAIGNS_MENU, tap=False),
            Step("SELECT_CAMPAIGN", f"campaign_{node['campaign']}"),
        ]
        if node.get("chapter") is not None:
            steps.append(Step("SELECT_CHAPTER", f"chapter_tab_{node['chapter']}"))
        steps += [
            Step("SELECT_NODE", f"node_{node['node']}"),
            Step("OPEN_MULTISIM", TPL_MULTI_SIM),
            Step("CONFIRM_SIM", TPL_SIM_CONFIRM, energy_out_here=True, mark_sim=True),
            Step("REWARDS", TPL_REWARDS),
            Step("RETURN_HOME", TPL_HOME_BUTTON),
        ]
        return steps

    def _tap(self, match):
        self.tapper(match.cx, match.cy)
        self._actions += 1
        self.delay()

    def _recover_to_home(self):
        """Best-effort return to the hub after an energy-out (the Multi Sim dialog is open).
        Close the dialog if present, then tap the home button if present. If neither is
        found the next node's HOME verify will halt safely."""
        for tpl in (TPL_DIALOG_CLOSE, TPL_HOME_BUTTON):
            m = self.look(tpl, self.energy_out_timeout)
            if m is not None:
                self._tap(m)

    def run(self):
        self._actions = 0        # reset so run() is re-entrant (a re-run doesn't inherit the prior tap count)
        s = Summary()
        for node in self.nodes:
            if self.should_stop():
                s.stopped_reason = "killed"
                return s
            s.nodes_attempted += 1
            for step in self._steps_for(node):
                if self._actions >= self.max_actions:
                    s.stopped_reason = "cap"
                    return s
                if self.should_stop():
                    s.stopped_reason = "killed"
                    return s
                m = self.look(step.template, self.timeout)
                if m is None:
                    if step.energy_out_here and \
                            self.look(TPL_ENERGY_OUT, self.energy_out_timeout) is not None:
                        s.energy_out_nodes += 1
                        self._recover_to_home()
                        break                      # this node's energy is out -> next node
                    self.halt(step.label)
                    s.halted = True
                    s.halt_state = step.label
                    s.stopped_reason = "halt"
                    return s
                if step.tap:
                    self._tap(m)
                    if step.mark_sim:
                        s.sims_done += 1
        return s
