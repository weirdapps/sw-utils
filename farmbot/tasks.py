"""tasks.py — EnergyDumpTask state machine. Device-free: all perception via injected `look`.

Models the REAL SWGOH energy-dump flow (validated live 2026-08-02), one node at a time,
each an independent journey that starts and ends at the hub:

    HOME (verify) -> tap Campaigns -> Campaigns menu (verify) -> tap <campaign> PLAY
      -> [optional: tap Hard tab] -> [optional: tap chapter tab] -> tap node icon -> tap MULTI SIM
      -> SIM dialog (pre-set to max energy) -> tap SIM confirm -> rewards -> tap home button

Multi Sim auto-fills the quantity to the max the current energy allows, so there is no
"set max" step.

Two kinds of expected interruption skip a node instead of halting the whole run (both recover
to the hub and continue to the next node), driven by a generic per-step `skip_marker`:
  * Energy-out — CONFIRM_SIM: the confirm is unavailable and a "Purchase Energy" crystal prompt
    shows. skip_marker = its CANCEL button, which we TAP (never PURCHASE).
  * Depleted Hard node — OPEN_MULTISIM: a Hard node's 5 daily attempts are used up, so the panel
    shows a refresh timer + 💎200 instead of MULTI SIM. skip_marker = that state, which we do NOT
    tap (skip_tap=False) so the 💎200 refresh is never pressed.

The hub is popup-prone (login/era calendars, GoH newsletter). When an expected screen is missing,
known popups are dismissed (tap their close-X) and the screen re-checked once before halting.
"""
from dataclasses import dataclass
from typing import Optional, Tuple

# Reusable screen/element templates (captured once, shared across all energy types).
TPL_HOME = "home"                        # we are on the hub screen (verify only)
TPL_CAMPAIGNS_ENTRY = "campaigns_entry"  # the "Campaigns" button on the hub
TPL_CAMPAIGNS_MENU = "campaigns_menu"    # the Campaigns menu is open (verify only)
TPL_MULTI_SIM = "multi_sim"              # the MULTI SIM button on a node's detail panel
TPL_SIM_CONFIRM = "sim_confirm"          # the green SIM confirm in the Multi Sim dialog
TPL_REWARDS = "rewards"                  # the post-sim rewards popup CONTINUE button (tap to dismiss)
TPL_HOME_BUTTON = "home_button"          # the house icon that returns to the hub
TPL_ENERGY_OUT = "energy_out"            # the CANCEL button of the "Purchase Energy" prompt shown
                                         # when energy is too low to sim — tap it (never PURCHASE)
TPL_HARD_TAB = "hard_tab"                # the (unselected) "Hard" difficulty toggle on LS/DS/Fleet maps
TPL_NORMAL_TAB = "normal_tab"            # the (unselected) "Normal" difficulty toggle on LS/DS/Fleet maps
TPL_HARD_DEPLETED = "hard_depleted"      # a Hard node with its 5 daily attempts used up: the panel
                                         # shows a refresh timer + 💎200 instead of MULTI SIM. This is
                                         # a MARKER only — NEVER tapped, so crystals are never spent.

TPL_CHALLENGES_ENTRY = "challenges_entry"  # the "Challenges" button on the hub
TPL_CHALLENGES_MENU = "challenges_menu"    # the Challenges menu is open (verify only)
TPL_CHALLENGE_LOCKED = "challenge_locked"  # a challenge not yet 3-starred: no MULTI SIM. MARKER only
                                           # (never tapped) so a real battle is never started.

TPL_BATTLE_START = "battle_start"   # the green START/DEPLOY on a PvE battle's team-select screen
TPL_BATTLE_AUTO = "battle_auto"     # the AUTO toggle inside a battle (self-play)
TPL_VICTORY = "victory"             # a battle VICTORY/results screen (tap to advance to rewards)
TPL_DEFEAT = "defeat"               # a battle DEFEAT screen (tap to dismiss). Recorded, never retried.
DEFAULT_BATTLE_TIMEOUT_S = 180.0    # how long to wait for a real-time battle to resolve

# Popups that can cover the hub (login/era calendars, GoH newsletter). Their close controls are
# distinctive and safe to tap; a template that isn't captured yet simply never matches (no-op).
DEFAULT_POPUP_CLOSERS = ("popup_close", "newsletter_close")

# Campaigns whose chapter/tier tabs have a distinct visual from the shared LS/DS/Cantina/Fleet
# chapter tabs, so their tab templates are campaign-scoped (chapter_tab_<campaign>_<n>).
SCOPED_CHAPTER_CAMPAIGNS = frozenset({"mod"})

# Campaigns with a Normal/Hard difficulty toggle at the bottom of the map. The game REMEMBERS the
# last-used difficulty, so the toggle step is optional: if the wanted difficulty's (unselected)
# button is visible we're on the other one and tap to switch; if it isn't, we're already there.
DIFFICULTY_CAMPAIGNS = frozenset({"light", "dark", "fleet"})


@dataclass
class Step:
    label: str
    template: str
    tap: bool = True                 # False = verify the screen only, no tap
    tap_offset: tuple = (0, 0)       # (dx, dy) from the match center — tap a control near a marker
    mark_sim: bool = False           # a successful tap here counts as one sim dump
    ensure: Optional[str] = None     # after the tap, this template must appear; if not, re-tap
    ensure_extra: Tuple[str, ...] = ()  # templates that ALSO satisfy `ensure` (stop re-tapping),
                                     # e.g. a depleted-Hard panel is "open" without MULTI SIM
    ensure_retries: int = 2          # extra taps allowed to make `ensure` appear (taps can toggle a panel)
    scrollable: bool = False         # if the template isn't visible, swipe-scan the map to find it
    optional: bool = False           # template absent => skip this step (no tap, no halt), e.g. a
                                     # difficulty toggle when already on the wanted difficulty
    skip_marker: Optional[str] = None   # template absent + this present => skip node (not halt)
    skip_tap: bool = False           # tap skip_marker (e.g. energy_out CANCEL) vs just recover home
    skip_counter: str = "skipped_nodes"  # which Summary counter to bump on a skip
    mark: Optional[str] = None            # on a successful tap, bump this Summary counter
    optional_counter: Optional[str] = None  # when an `optional` step is skipped (absent), bump this
    timeout: Optional[float] = None       # per-step look-timeout override (e.g. a long battle wait)


@dataclass
class Summary:
    nodes_attempted: int = 0
    sims_done: int = 0
    energy_out_nodes: int = 0
    hard_depleted_nodes: int = 0
    collected: int = 0
    challenges_simmed: int = 0
    energy_claimed: int = 0
    nothing_to_collect: int = 0
    battles_won: int = 0
    battles_lost: int = 0
    skipped_nodes: int = 0
    halted: bool = False
    halt_state: Optional[str] = None
    stopped_reason: str = "complete"


class EnergyDumpTask:
    def __init__(self, nodes, look, tapper, should_stop=lambda: False,
                 halt=lambda state: None, max_actions=400, timeout=10.0,
                 energy_out_timeout=2.0, delay=lambda: None,
                 swipe=lambda direction: None,
                 scroll_scan=("right", "right", "left", "left", "left", "left"),
                 popup_closers=DEFAULT_POPUP_CLOSERS, popup_retries=3):
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
        self.scroll_scan = scroll_scan   # directions to try when a scrollable target isn't in view
        self.popup_closers = popup_closers
        self.popup_retries = popup_retries
        self._actions = 0

    def _steps_for(self, node):
        """Dispatch an ordered Step list by the entry's kind (default energy_node)."""
        kind = node.get("kind", "energy_node")
        builders = {
            "energy_node": self._steps_energy_node,
            "collect": self._steps_collect,
            "challenge_sim": self._steps_challenge_sim,
            "battle": self._steps_battle,
        }
        builder = builders.get(kind)
        if builder is None:
            raise ValueError(f"unknown routine kind: {kind!r}")
        return builder(node)

    def _steps_energy_node(self, node):
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
            Step("SELECT_CAMPAIGN", f"campaign_{node['campaign']}", tap_offset=(0, 673),
                 scrollable=True),   # Fleet/Mod cards start off-screen in the Campaigns menu
        ]
        is_hard = node.get("difficulty") == "hard"
        if node["campaign"] in DIFFICULTY_CAMPAIGNS:
            # Ensure the wanted difficulty is selected. optional=True: the unselected button is only
            # visible when we're on the OTHER difficulty; if it's absent we're already correct.
            want_tab = TPL_HARD_TAB if is_hard else TPL_NORMAL_TAB
            steps.append(Step("SELECT_DIFFICULTY", want_tab, optional=True))
        if node.get("chapter") is not None:
            # LS/DS/Cantina/Fleet share one chapter-tab visual (generic chapter_tab_<n>). Mod Battles
            # uses "tier" tabs with a distinct look, so those are campaign-scoped to avoid colliding
            # with a same-numbered standard chapter (e.g. Mod tier 2 vs Fleet chapter 2).
            ch = node["chapter"]
            tab = (f"chapter_tab_{node['campaign']}_{ch}"
                   if node["campaign"] in SCOPED_CHAPTER_CAMPAIGNS else f"chapter_tab_{ch}")
            # scrollable: high chapter tabs (e.g. Cantina 9) can sit off the visible tab row.
            steps.append(Step("SELECT_CHAPTER", tab, scrollable=True))
        # On a Hard node the panel can open into a depleted state (no MULTI SIM) — treat that as
        # "panel ready" so SELECT_NODE stops re-tapping, then OPEN_MULTISIM skips it cleanly.
        node_ensure_extra = (TPL_HARD_DEPLETED,) if is_hard else ()
        steps += [
            Step("SELECT_NODE", f"node_{node['campaign']}_{node['node']}",
                 ensure=TPL_MULTI_SIM, ensure_extra=node_ensure_extra, scrollable=True),
            Step("OPEN_MULTISIM", TPL_MULTI_SIM,
                 skip_marker=TPL_HARD_DEPLETED, skip_tap=False, skip_counter="hard_depleted_nodes"),
            Step("CONFIRM_SIM", TPL_SIM_CONFIRM, mark_sim=True,
                 skip_marker=TPL_ENERGY_OUT, skip_tap=True, skip_counter="energy_out_nodes"),
            Step("REWARDS", TPL_REWARDS),
            Step("RETURN_HOME", TPL_HOME_BUTTON),
        ]
        return steps

    def _steps_collect(self, node):
        """A tap-to-collect daily: HOME -> [nav taps] -> CLAIM (skip if absent = nothing to collect)
        -> dismiss any reward popup -> RETURN_HOME. Only the FREE claim template is a tap target, so
        a crystal-cost variant is never pressed (it simply won't match). `count`>1 taps the claim
        repeatedly (stacked gifts), stopping when absent. `counter` books to a specific Summary
        field (e.g. energy_claimed); default is `collected`."""
        steps = [Step("HOME", TPL_HOME, tap=False)]
        for i, tpl in enumerate(node.get("nav", [])):
            steps.append(Step(f"NAV_{i}", tpl, scrollable=node.get("scrollable", False)))
        counter = node.get("counter", "collected")
        for i in range(node.get("count", 1)):
            steps.append(Step(f"CLAIM_{i}", node["claim"], optional=True, mark=counter,
                              optional_counter=("nothing_to_collect" if i == 0 else None)))
        steps.append(Step("COLLECT_REWARDS", TPL_REWARDS, optional=True))
        steps.append(Step("RETURN_HOME", TPL_HOME_BUTTON))
        return steps

    def _steps_challenge_sim(self, node):
        """A Daily Challenge Multi-Sim on the Challenges screen (not the Campaigns menu). Reuses the
        sim chrome (multi_sim/sim_confirm/rewards). A challenge not yet 3-starred shows no MULTI SIM;
        if a challenge_locked marker is present we skip (never battle), else the uncaptured screen
        safe-halts. Uses mark='challenges_simmed' (not mark_sim) to stay disjoint from energy sims."""
        return [
            Step("HOME", TPL_HOME, tap=False),
            Step("OPEN_CHALLENGES", TPL_CHALLENGES_ENTRY),
            Step("CHALLENGES_MENU", TPL_CHALLENGES_MENU, tap=False),
            Step("SELECT_CHALLENGE", node["challenge"], ensure=TPL_MULTI_SIM,
                 ensure_extra=(TPL_CHALLENGE_LOCKED,), scrollable=True),
            Step("OPEN_MULTISIM", TPL_MULTI_SIM,
                 skip_marker=TPL_CHALLENGE_LOCKED, skip_tap=False, skip_counter="skipped_nodes"),
            Step("CONFIRM_SIM", TPL_SIM_CONFIRM, mark="challenges_simmed",
                 skip_marker=TPL_ENERGY_OUT, skip_tap=True, skip_counter="energy_out_nodes"),
            Step("REWARDS", TPL_REWARDS),
            Step("RETURN_HOME", TPL_HOME_BUTTON),
        ]

    def _steps_battle(self, node):
        """A PvE auto-battle: HOME -> [nav] -> per attempt (START -> AUTO(optional) -> await VICTORY
        with a long timeout; DEFEAT = recorded skip, never retried) -> dismiss rewards -> RETURN_HOME.
        PvE only: no PvP tile is ever a nav/start target. start/auto/victory/defeat default to shared
        templates, overridable per entry; `attempts` repeats the fight (e.g. Coliseum's 5)."""
        start = node.get("start", TPL_BATTLE_START)
        auto = node.get("auto", TPL_BATTLE_AUTO)
        victory = node.get("victory", TPL_VICTORY)
        defeat = node.get("defeat", TPL_DEFEAT)
        btimeout = node.get("battle_timeout_s", DEFAULT_BATTLE_TIMEOUT_S)
        steps = [Step("HOME", TPL_HOME, tap=False)]
        for i, tpl in enumerate(node.get("nav", [])):
            steps.append(Step(f"NAV_{i}", tpl, scrollable=node.get("scrollable", False)))
        for a in range(node.get("attempts", 1)):
            steps.append(Step(f"START_{a}", start))
            steps.append(Step(f"AUTO_{a}", auto, optional=True))
            steps.append(Step(f"OUTCOME_{a}", victory, timeout=btimeout, mark="battles_won",
                              skip_marker=defeat, skip_tap=True, skip_counter="battles_lost"))
            steps.append(Step(f"POST_{a}", TPL_REWARDS, optional=True))
        steps.append(Step("RETURN_HOME", TPL_HOME_BUTTON))
        return steps

    def _tap(self, match, offset=(0, 0)):
        self.tapper(match.cx + offset[0], match.cy + offset[1])
        self._actions += 1
        self.delay()

    @staticmethod
    def _bump(summary, counter):
        setattr(summary, counter, getattr(summary, counter) + 1)

    def _recover_to_home(self):
        """Best-effort return to the hub after a skip. Tap the home button if present;
        if not, the next node's HOME verify will halt safely."""
        m = self.look(TPL_HOME_BUTTON, self.energy_out_timeout)
        if m is not None:
            self._tap(m)

    def _scroll_find(self, template):
        """Swipe the map to bring an off-screen target into view, re-looking after each swipe.
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

    def _dismiss_popups(self):
        """Tap the close-X of any known popup that's on screen. Loops so a stack of auto-popups
        clears. Returns True if it dismissed at least one (caller then re-checks the screen)."""
        dismissed = False
        for _ in range(self.popup_retries):
            hit = False
            for closer in self.popup_closers:
                m = self.look(closer, self.energy_out_timeout)
                if m is not None:
                    self._tap(m)
                    hit = True
                    dismissed = True
            if not hit:
                break
        return dismissed

    def _panel_ready(self, step):
        """Has the tapped control produced its expected panel? True if `ensure` or any
        `ensure_extra` marker is visible."""
        if self.look(step.ensure, self.energy_out_timeout) is not None:
            return True
        return any(self.look(e, self.energy_out_timeout) is not None for e in step.ensure_extra)

    def run(self):
        self._actions = 0        # reset so run() is re-entrant (a re-run doesn't inherit the prior count)
        s = Summary()
        for node in self.nodes:
            if self.should_stop():
                s.stopped_reason = "killed"
                return s
            s.nodes_attempted += 1
            skipped = False
            for step in self._steps_for(node):
                if self._actions >= self.max_actions:
                    s.stopped_reason = "cap"
                    return s
                if self.should_stop():
                    s.stopped_reason = "killed"
                    return s
                m = self.look(step.template, step.timeout if step.timeout is not None else self.timeout)
                if m is None and step.scrollable:
                    m = self._scroll_find(step.template)   # target may be off-screen; swipe-scan
                if m is None and step.optional:
                    if step.optional_counter:
                        self._bump(s, step.optional_counter)
                    continue   # step not applicable (e.g. already on the wanted difficulty)
                if m is None:
                    # Expected interruption (energy-out / depleted Hard): marker present => skip node.
                    if step.skip_marker is not None:
                        marker = self.look(step.skip_marker, self.energy_out_timeout)
                        if marker is not None:
                            self._bump(s, step.skip_counter)
                            if step.skip_tap:
                                self._tap(marker)   # e.g. energy_out CANCEL — never 💎PURCHASE/refresh
                            self._recover_to_home()
                            skipped = True
                            break
                    # Maybe a popup is covering the expected screen — dismiss it and re-check once.
                    if self._dismiss_popups():
                        m = self.look(step.template, self.timeout)
                        if m is None and step.scrollable:
                            m = self._scroll_find(step.template)
                    if m is None:
                        self.halt(step.label)
                        s.halted = True
                        s.halt_state = step.label
                        s.stopped_reason = "halt"
                        return s
                if step.tap:
                    self._tap(m, step.tap_offset)
                    if step.mark_sim:
                        s.sims_done += 1
                    if step.mark:
                        self._bump(s, step.mark)
                    if step.ensure:
                        # some taps toggle a panel (e.g. tapping an already-selected node
                        # closes its detail panel); re-tap until the expected panel appears.
                        tries = step.ensure_retries
                        while tries > 0 and not self._panel_ready(step):
                            self._tap(m, step.tap_offset)
                            tries -= 1
            if skipped:
                continue
        return s
