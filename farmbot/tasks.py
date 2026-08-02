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
TPL_REWARDS = "rewards"                  # the post-sim rewards popup CONTINUE button (tap to dismiss)
TPL_HOME_BUTTON = "home_button"          # the house icon that returns to the hub
TPL_ENERGY_OUT = "energy_out"            # the CANCEL button of the "Purchase Energy" prompt shown
                                         # when energy is too low to sim — tapping it cancels (never PURCHASE)
TPL_HARD_TAB = "hard_tab"                # the "Hard" difficulty toggle on LS/DS/Fleet campaign maps


@dataclass
class Step:
    label: str
    template: str
    tap: bool = True             # False = verify the screen only, no tap
    tap_offset: tuple = (0, 0)   # (dx, dy) from the match center — tap a control near a distinctive marker
    energy_out_here: bool = False  # absence + energy_out marker => skip node (not halt)
    mark_sim: bool = False       # a successful tap here counts as one sim dump
    ensure: Optional[str] = None   # after the tap, this template must appear; if not, re-tap
    ensure_retries: int = 2      # extra taps allowed to make `ensure` appear (taps can toggle a panel)
    scrollable: bool = False     # if the template isn't visible, swipe-scan the map to find it


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
                 energy_out_timeout=2.0, delay=lambda: None,
                 swipe=lambda direction: None,
                 scroll_scan=("right", "right", "left", "left", "left", "left")):
        self.nodes = nodes
        self.look = look
        self.tapper = tapper
        self.should_stop = should_stop
        self.halt = halt
        self.max_actions = max_actions
        self.timeout = timeout
        self.energy_out_timeout = energy_out_timeout
        self.delay = delay
        self.swipe = swipe
        self.scroll_scan = scroll_scan   # directions to try when a scrollable node isn't in view
        self._actions = 0

    def _steps_for(self, node):
        """Build the ordered Step list for one node from its compact config entry.

        node = {"campaign": <name>, "node": <id>, ["difficulty": "hard"], ["chapter": <n>], "sim": "max"}
        Per-node templates: campaign_<name>, hard_tab (if difficulty), chapter_tab_<n>,
        node_<campaign>_<id> (campaign-scoped so e.g. Cantina 1-A and Fleet 1-A don't collide).
        """
        steps = [
            Step("HOME", TPL_HOME, tap=False),
            Step("OPEN_CAMPAIGNS", TPL_CAMPAIGNS_ENTRY),
            Step("CAMPAIGNS_MENU", TPL_CAMPAIGNS_MENU, tap=False),
            # Match the distinctive campaign title, then tap the PLAY button below it
            # (tapping the title/artwork only flips the card; PLAY buttons are identical
            # across cards so they can't be matched directly). Title center y~254, PLAY y~927.
            Step("SELECT_CAMPAIGN", f"campaign_{node['campaign']}", tap_offset=(0, 673)),
        ]
        if node.get("difficulty") == "hard":
            steps.append(Step("SELECT_DIFFICULTY", TPL_HARD_TAB))  # LS/DS/Fleet Hard toggle
        if node.get("chapter") is not None:
            steps.append(Step("SELECT_CHAPTER", f"chapter_tab_{node['chapter']}"))
        steps += [
            Step("SELECT_NODE", f"node_{node['campaign']}_{node['node']}",
                 ensure=TPL_MULTI_SIM, scrollable=True),
            Step("OPEN_MULTISIM", TPL_MULTI_SIM),
            Step("CONFIRM_SIM", TPL_SIM_CONFIRM, energy_out_here=True, mark_sim=True),
            Step("REWARDS", TPL_REWARDS),
            Step("RETURN_HOME", TPL_HOME_BUTTON),
        ]
        return steps

    def _tap(self, match, offset=(0, 0)):
        self.tapper(match.cx + offset[0], match.cy + offset[1])
        self._actions += 1
        self.delay()

    def _recover_to_home(self):
        """Best-effort return to the hub after an energy-out. Tap the home button if present;
        if not, the next node's HOME verify will halt safely."""
        m = self.look(TPL_HOME_BUTTON, self.energy_out_timeout)
        if m is not None:
            self._tap(m)

    def _scroll_find(self, template):
        """Swipe the node map to bring an off-screen node into view, re-looking after each swipe.
        Swipes don't count toward the action cap (they're navigation, not sim actions)."""
        for direction in self.scroll_scan:
            if self.should_stop() or self._actions >= self.max_actions:
                return None
            self.swipe(direction)
            self.delay()
            m = self.look(template, self.energy_out_timeout)
            if m is not None:
                return m
        return None

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
                if m is None and step.scrollable:
                    m = self._scroll_find(step.template)   # node may be off-screen; swipe-scan
                if m is None:
                    if step.energy_out_here:
                        eo = self.look(TPL_ENERGY_OUT, self.energy_out_timeout)
                        if eo is not None:
                            s.energy_out_nodes += 1
                            self._tap(eo)          # tap CANCEL to dismiss the purchase prompt (never PURCHASE)
                            self._recover_to_home()
                            break                  # this node's energy is out -> next node
                    self.halt(step.label)
                    s.halted = True
                    s.halt_state = step.label
                    s.stopped_reason = "halt"
                    return s
                if step.tap:
                    self._tap(m, step.tap_offset)
                    if step.mark_sim:
                        s.sims_done += 1
                    if step.ensure:
                        # some taps toggle a panel (e.g. tapping an already-selected node
                        # closes its detail panel); re-tap until the expected panel appears.
                        tries = step.ensure_retries
                        while tries > 0 and self.look(step.ensure, self.energy_out_timeout) is None:
                            self._tap(m, step.tap_offset)
                            tries -= 1
        return s
