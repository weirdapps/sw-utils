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
    shows a refresh timer + a crystal price instead of MULTI SIM. skip_marker = that state, which
    we do NOT tap (skip_tap=False) so the refresh is never pressed. The price differs per campaign
    (💎25 on Light-Side Hard, 💎200 on Fleet Hard), so the marker takes several skins.

The hub is popup-prone (login/era calendars, GoH newsletter). When an expected screen is missing,
known popups are dismissed (tap their close-X) and the screen re-checked once before halting.
"""
from dataclasses import dataclass
from typing import Optional, Tuple

# Reusable screen/element templates (captured once, shared across all energy types).
TPL_HOME = "home"                        # we are on the hub screen (verify only). Crops ONLY the
                                         # "85 Astra / MAX LE" glyphs of the level plate. Do not
                                         # widen it: one pixel right lies the GP readout, which
                                         # ticks up as the account grows, and above-right lies the
                                         # 3D hub scene, whose art changes between episodes. The
                                         # previous crop held both and decayed to 0.815 — under
                                         # the 0.85 threshold — so every entry's first step failed
                                         # and _ensure_hub could not repair it (tapping the home
                                         # button does not restore a panned camera).
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
TPL_HARD_DEPLETED_ALT = ("hard_depleted_200",)   # the same depleted panel, other skin: the crop
                                         # above came from Light-Side Hard, whose refresh chip reads
                                         # 💎25, while Fleet Hard's reads 💎200 — so one crop cannot
                                         # cover both and the Fleet node halted instead of skipping.
                                         # Also markers only. An uncaptured skin simply never
                                         # matches, which is the pre-existing behaviour.

TPL_EVENTS_ENTRY = "events_entry"          # the "EVENT ACTIVE" overlay on the hub's right rail.
                                           # Deliberately NOT the 3D "Events" console: the overlay is
                                           # a fixed HUD element, so it is immune to the hub pan and
                                           # opens the same Events menu (Solo / Challenges / Guild
                                           # Raids / Guild Events). It is only absent if no event is
                                           # running at all, which is rare; then the step just skips.
EVENTS_ENTRY_TAP_OFFSET = (0, -71)         # "EVENT ACTIVE" label -> the portrait button above it
TPL_EVENTS_MENU = "events_menu"            # "Select From the Following Events" (verify only)
TPL_GUILD_RAIDS_TAB = "guild_raids_tab"    # the "Guild Raids" tab inside the Events menu
TPL_CHALLENGES_TAB = "challenges_tab"      # the "Challenges" tab in the Events menu
TPL_CHALLENGES_MENU = "challenges_menu"    # the "Select a Challenge" screen (verify only)
TPL_CHALLENGES_MULTISIM = "challenges_multisim"        # MULTI SIM button (sims ALL daily challenges)
TPL_CHALLENGES_SIM_CONFIRM = "challenges_sim_confirm"  # green SIM confirm in the challenge-sim dialog

TPL_BATTLE_START = "battle_start"   # the green START/DEPLOY on a PvE battle's team-select screen
TPL_BATTLE_AUTO = "battle_auto"     # the AUTO toggle inside a battle (self-play)
TPL_VICTORY = "victory"             # a battle VICTORY/results screen (tap to advance to rewards)
TPL_CELEBRATION = "celebration_continue"   # full-screen "X reached 7 stars!" celebrations have a
                                    # bottom-right CONTINUE and NO home button, so an entry that
                                    # lands on one cannot return to the hub and every entry after
                                    # it fails its HOME check. Seen live when a bronzium starred up
                                    # Mace Windu. Dismissing it is always safe: it only advances.
TPL_COLISEUM_HIGHSCORE = "coliseum_highscore"   # Coliseum replaces the normal victory screen with a
                                    # "NEW HIGH SCORE / tap anywhere" banner when the run beats the
                                    # banked score. It IS a win, so it is a victory alternative — and
                                    # it is also a popup closer, because if it is left up it covers
                                    # the hub and every following entry fails its HOME check.
TPL_TIER_COMPLETE = "tier_complete"  # Coliseum's other non-standard result: clearing a tier shows
                                    # "TIER COMPLETE / NEW TIER UNLOCKED <n>" in place of VICTORY.
                                    # Same two jobs as the high-score banner — a win to book (wire
                                    # it into an entry's `victory_alt`) and a screen that strands
                                    # the run if left up, hence a popup closer too. Crop it on the
                                    # banner's own dismiss control so tapping it can only advance.
TPL_COLISEUM_RESULTS = "coliseum_results"   # Coliseum's fourth result screen: "BATTLE RESULTS" with
                                    # a CONTINUE. Unlike the banners above, the title we can
                                    # recognise and the control that dismisses it are far apart.
COLISEUM_RESULTS_TAP_OFFSET = (0, 464)   # title centre -> CONTINUE (measured 2026-08-04 on device)
TPL_DEFEAT_UPSELL = "defeat_upsell"      # "Did you know you have upgrades available?" — the panel a
                                         # LOST Conquest battle stacks on top of the DEFEAT screen.
DEFEAT_UPSELL_TAP_OFFSET = (-891, -39)   # match centre (956,104) -> the back arrow (65,65). Measured
                                         # live 2026-08-04. There is no close X and no CONTINUE; the
                                         # back arrow is the only exit, which is why this needs an
                                         # offset rather than a centre tap.
TPL_DEFEAT = "defeat"               # a battle DEFEAT screen (tap to dismiss). Recorded, never retried.
DEFAULT_BATTLE_TIMEOUT_S = 180.0    # how long to wait for a real-time battle to resolve


def tap_target(spec):
    """Normalise a tap target to (template, (dx, dy)).

    The thing that is RECOGNISABLE and the thing that is TAPPABLE are often not the same pixel:
    a hub rail's label is distinctive while its icon is the hit target, and a full-screen result
    banner is named by a title hundreds of pixels above the CONTINUE that dismisses it. `nav` hops
    and `sequence` taps already carry their own `offset`; this is the same idea for the places
    that only ever took a bare template name.
    """
    if isinstance(spec, str):
        return spec, (0, 0)
    name, offset = spec
    return name, tuple(offset)

# --- hub panning -------------------------------------------------------------------------------
# The hub is a wide horizontal 3D panorama, not a flat menu. Its persistent OVERLAYS (player badge,
# left rail, energy bar, home button) sit at fixed screen positions, but the game-mode CONSOLES
# (Campaigns, Events, Raids, ...) live in the 3D scene and move/rescale with the camera pan — so a
# console template matched at one pan taps the wrong place at another. Two facts make this tractable:
#   * The pan only changes when WE swipe (a scroll-scan for an off-screen console leaves it dirty).
#   * Leaving the hub for any submenu and returning restores the DEFAULT pan (measured: a center-band
#     pixel diff of 6.5 vs 41.4 for a panned hub) — the home button alone does NOT, it's a no-op
#     when the hub is already showing.
# So `recenter` = bounce through a harmless submenu, and `pan` = swipe until the panorama clamps
# against an end stop, which is the only other pan that is reproducible without counting pixels.
TPL_HUB_ANCHOR = "hub_anchor"            # a pan-invariant left-rail icon (Collection) — read-only,
                                         # opening it costs nothing and never spends
TPL_HUB_ANCHOR_OPEN = "hub_anchor_open"  # a marker that the anchor submenu actually opened
HUB_ANCHOR_TAP_OFFSET = (0, -64)         # label center -> icon center (measured on device)
PAN_FAR_RIGHT = "far_right"   # camera to the right end of the panorama (Events / Scavenger / GW)
PAN_FAR_LEFT = "far_left"     # camera to the left end (Raids / Guilds / Guild Events)
# Enough swipes to hit the end stop from anywhere; over-swiping past a clamped edge is a no-op.
DEFAULT_PAN_SWIPES = 8
# `swipe(direction)` is expressed as which way the CONTENT is dragged, so revealing the right end
# of the panorama means dragging content left.
_PAN_SWIPE_DIRECTION = {PAN_FAR_RIGHT: "left", PAN_FAR_LEFT: "right"}

# --- conquest ------------------------------------------------------------------------------------
# Reached from the FAR-RIGHT hub pan, via a chooser that offers Galactic War and Conquest side by
# side. Everything below was read off the device on 2026-08-04, including the two traps:
#   * the two ENTER buttons on the chooser are pixel-identical, so the only safe anchor is the
#     CONQUEST title and an offset tap;
#   * one BATTLE template matches both the Combat Details button and the squad-select button, so
#     starting a fight is two taps, not one.
TPL_GALACTIC_BATTLES = "galactic_battles"          # the hub console (far-right pan). Captured AT
                                                   # the far-right end stop, and it only works
                                                   # there: hub console labels are objects in the
                                                   # 3D scene, so panning shears them in
                                                   # perspective and a flat template stops
                                                   # matching (a mid-pan capture scored 0.318 at
                                                   # the end stop, and 0.469 even at best scale
                                                   # in its own best position). What makes the
                                                   # end-stop capture safe is that _pan
                                                   # over-swipes into the stop: two independent
                                                   # pans there agreed to 0.9991. The crop stops
                                                   # short of the red "3+" notification badge,
                                                   # which is a changing count.
TPL_CONQUEST_CARD = "conquest_card"                # the CONQUEST title on "SELECT A GALACTIC BATTLE"
CONQUEST_ENTER_TAP_OFFSET = (0, 704)               # CONQUEST title centre -> its ENTER button.
                                                   # Measured: crop (1155,200)-(1445,262) => centre
                                                   # (1300,231); ENTER at (1298,934) => dy 703.
TPL_CONQUEST_HEADER = "conquest_header"            # the sector-list header: proof we are in
                                                   # Conquest and not in Galactic War
TPL_CONQUEST_ENTER = "conquest_enter"              # ENTER on the unlocked sector's row
TPL_CONQUEST_FEATS_PANEL = "conquest_feats_panel"  # the sector map is up (verify only)
TPL_CONQUEST_DISK_STOCKPILE = "conquest_disk_stockpile"  # the green "Data Disk Stockpile" hex: a
                                                   # FREE one-tap disk — no battle, no energy, and
                                                   # the disk auto-equips while capacity allows.
TPL_CONQUEST_DISK_OBTAINED = "conquest_disk_obtained"    # "You obtained this Data Disk", already
                                                   # showing on the first frame after the hex tap.
                                                   # NOT a dialog and NOT a button: it is part of
                                                   # the node's PERSISTENT side panel, which stays
                                                   # pixel-identical through an outside tap and is
                                                   # replaced only by tapping another node. So it
                                                   # is read, never pressed, and never waited on.
TPL_CONQUEST_NODE_OPEN = "conquest_node_open"      # the bright ring of an un-cleared combat node.
                                                   # Cleared nodes render dim: measured on a live
                                                   # sector map, open 1.000/0.973 vs cleared
                                                   # 0.663/0.348. The 0.85 threshold sits between
                                                   # them, which is what makes repeated matches
                                                   # walk from node to node instead of re-hitting
                                                   # one. Beware: the cyan arrows are a SELECTION
                                                   # cursor, not an availability marker — a
                                                   # cleared 3/3 node keeps them once tapped.
TPL_CONQUEST_COMBAT_DETAILS = "conquest_combat_details"  # a battle node's Combat Details panel
TPL_CONQUEST_BATTLE_BTN = "conquest_battle_btn"    # BATTLE — matches BOTH the Combat Details
                                                   # "BATTLE ⚡20" and the squad-select "BATTLE"
TPL_CONQUEST_SQUAD_PROMPT = "conquest_squad_prompt"      # the squad-select screen. Crops the
                                                   # SUBTITLE ("Tap a slot to add or swap a
                                                   # character."), never the title — the title
                                                   # reads SELECT LIGHT/DARK/NEUTRAL SQUAD and so
                                                   # only matches a third of nodes. Verified live
                                                   # at 1.000 on a NEUTRAL node's screen.
# Stamina, not energy, is the budget: -10% per battle per character against +1% per 30 min, while
# 15,649 banked energy is ~780 nodes at ⚡20. Two battles is roughly one squad's session.
DEFAULT_CONQUEST_MAX_BATTLES = 2

# --- shops -------------------------------------------------------------------------------------
# Shipments mixes token-priced and CRYSTAL-priced tabs behind visually identical green buttons, and
# every tab carries a permanent "REFRESH ... 💎50" bar, so "tap the green button" is exactly the
# wrong instinct here. What makes this safe is a detail of the purchase dialog: its BUY button
# renders the CURRENCY ICON inline, next to the price. So a confirm template cropped around
# "BUY + <token icon>" (and deliberately not the digits, which vary with price) can only ever match
# a purchase in THAT currency. The guard is therefore structural rather than a runtime check:
# no crystal-currency confirm template exists in the repo, so no crystal purchase can be confirmed.
TPL_SHOP_CONFIRM = "shop_confirm_cantina"  # default: Cantina tokens. Override per entry with
                                           # `confirm` to shop another currency.
TPL_SHOP_CANCEL = "shop_cancel"            # the dialog's close-X — backs out without buying

# Popups that can cover the hub (login/era calendars, GoH newsletter). Their close controls are
# distinctive and safe to tap; a template that isn't captured yet simply never matches (no-op).
# `bronzium_skip` is the bottom-right SKIP/FINISH of the data-card reveal. It earns a place here
# because that flow leaves a SECOND screen behind ("BUY AGAIN 250 / FINISH") which has no home
# button, and verified against a live capture it matches FINISH at 1.000 while nothing in the
# template set matches BUY AGAIN — so dismissing it can only ever finish, never re-buy.
# An entry may be a bare name (tap the match) or (name, (dx, dy)) when the dismiss control sits
# away from the marker — the only such case today is `coliseum_results`, whose CONTINUE is far
# below the "BATTLE RESULTS" title. A blind offset is only safe off a HIGHLY specific marker, so
# keep offset closers cropped on distinctive text, never on chrome.
# The full-screen PAID BUNDLE offer ("ERA MODULE BUNDLE II", "YODA (DARK SIDE VISION) BUNDLE II",
# ...). It fires on its own timer, covers the hub completely, and `popup_close` does not match its
# X — which cost the 2026-08-18 evening run FOUR entries in five minutes, including all the energy
# nodes: the halt screenshots at 21:50:00 / 21:50:46 / 21:51:32 / 21:54:21 are all the same bundle.
#
# The marker is the words "OFFER EXPIRES:" — NOT the timer beside them, which counts down, and NOT
# the X, which is generic white chrome. Measured over the eleven halt captures plus four normal
# screens: 1.000 on every bundle, 0.40-0.50 on everything else, against a 0.88 threshold.
TPL_BUNDLE_OFFER = "bundle_offer"
BUNDLE_OFFER_TAP_OFFSET = (980, 1)       # match centre (877,142) -> the close X (1857,143)

DEFAULT_POPUP_CLOSERS = ("popup_close", "newsletter_close", TPL_COLISEUM_HIGHSCORE,
                         TPL_TIER_COMPLETE, TPL_CELEBRATION, "bronzium_skip",
                         (TPL_COLISEUM_RESULTS, COLISEUM_RESULTS_TAP_OFFSET),
                         (TPL_BUNDLE_OFFER, BUNDLE_OFFER_TAP_OFFSET),
                         (TPL_DEFEAT_UPSELL, DEFEAT_UPSELL_TAP_OFFSET))

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
    alt: Tuple[str, ...] = ()        # fallbacks for `template` itself: one screen, several skins
                                     # (a Coliseum win shows a high-score banner, not VICTORY)
    ensure_retries: int = 2          # extra taps allowed to make `ensure` appear (taps can toggle a panel)
    scrollable: bool = False         # if the template isn't visible, swipe-scan the map to find it
    scroll_scan: Tuple[str, ...] = ()   # per-step scan directions, for a target on the other axis:
                                     # the engine default is horizontal (built for the campaign
                                     # map), while a reordered quest LIST scrolls vertically
    optional: bool = False           # template absent => skip this step (no tap, no halt), e.g. a
                                     # difficulty toggle when already on the wanted difficulty
    skip_marker: Optional[str] = None   # template absent + this present => skip node (not halt)
    skip_marker_alt: Tuple[str, ...] = ()  # more skins of the SAME skip state, tried in turn — a
                                     # depleted Hard panel is priced 💎25 on LS and 💎200 on Fleet
    skip_tap: bool = False           # tap skip_marker (e.g. energy_out CANCEL) vs just recover home
    skip_counter: str = "skipped_nodes"  # which Summary counter to bump on a skip
    mark: Optional[str] = None            # on a successful tap, bump this Summary counter
    optional_counter: Optional[str] = None  # when an `optional` step is skipped (absent), bump this
    skip_entry: bool = False         # an absent `optional` step means the REST of this entry is
                                     # moot, not just this step (no battle started => no outcome)
    timeout: Optional[float] = None       # per-step look-timeout override (e.g. a long battle wait)
    pan: Optional[str] = None        # not a template step: swipe the hub panorama to an end stop
                                     # (PAN_FAR_RIGHT / PAN_FAR_LEFT) and move on. `template` unused.
    pan_swipes: int = DEFAULT_PAN_SWIPES
    forbid: Optional[str] = None     # a veto marker: even when `template` matched, seeing this means
                                     # the tap is unsafe (crystal-priced purchase) — do NOT tap
    forbid_tap: Optional[str] = None    # tap this instead when vetoed (e.g. a CANCEL button)
    forbid_counter: str = "blocked_spends"


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
    bought: int = 0
    battles_unavailable: int = 0
    battles_unresolved: int = 0
    blocked_spends: int = 0
    recentered: int = 0
    chapter_already_set: int = 0
    skipped_nodes: int = 0
    halted_entries: int = 0
    halted: bool = False
    halt_state: Optional[str] = None
    stopped_reason: str = "complete"


class EnergyDumpTask:
    def __init__(self, nodes, look, tapper, should_stop=lambda: False,
                 halt=lambda state: None, max_actions=400, timeout=10.0,
                 energy_out_timeout=2.0, delay=lambda: None,
                 swipe=lambda direction: None,
                 scroll_scan=("right", "right", "left", "left", "left", "left"),
                 popup_closers=DEFAULT_POPUP_CLOSERS, popup_retries=3,
                 continue_on_halt=False):
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
        self.continue_on_halt = continue_on_halt
        self._actions = 0

    def _steps_for(self, node):
        """Dispatch an ordered Step list by the entry's kind (default energy_node)."""
        kind = node.get("kind", "energy_node")
        builders = {
            "energy_node": self._steps_energy_node,
            "collect": self._steps_collect,
            "challenge_sim": self._steps_challenge_sim,
            "battle": self._steps_battle,
            "sequence": self._steps_sequence,
            "shop": self._steps_shop,
            "conquest": self._steps_conquest,
        }
        builder = builders.get(kind)
        if builder is None:
            raise ValueError(f"unknown routine kind: {kind!r}")
        return builder(node)

    @staticmethod
    def _hub_prelude(node):
        """The steps that put the hub camera somewhere known before an entry navigates.

        Default is nothing: the hub is already at its default pan unless a previous entry
        swiped it. `recenter: true` bounces through the anchor submenu to force the default pan;
        `pan: far_left|far_right` then drives the camera to that end stop. An entry that reads a
        console off the default pan needs BOTH (recenter first, so the swipe burst starts from a
        known place and can't be short by an earlier scroll).
        """
        pan = node.get("pan")
        steps = [Step("HOME", TPL_HOME, tap=False)]
        if node.get("recenter") or pan:
            steps += [
                # The template is the rail's LABEL (distinctive, badge-free), but the label itself
                # isn't a hit target — a tap there falls through to the 3D scene behind the rail
                # and opens whatever console happens to be there. Offset up onto the icon.
                Step("HUB_ANCHOR", TPL_HUB_ANCHOR, tap_offset=HUB_ANCHOR_TAP_OFFSET,
                     ensure=TPL_HUB_ANCHOR_OPEN),
                # `ensure` doubles as the arrival check: the hub is back and at its default pan.
                Step("HUB_RECENTER", TPL_HOME_BUTTON, ensure=TPL_HOME, mark="recentered"),
            ]
        if pan:
            if pan not in _PAN_SWIPE_DIRECTION:
                raise ValueError(f"unknown pan target: {pan!r}")
            steps.append(Step(f"PAN_{pan.upper()}", TPL_HOME, tap=False, pan=pan,
                              pan_swipes=node.get("pan_swipes", DEFAULT_PAN_SWIPES)))
        return steps

    @staticmethod
    def _nav_steps(node):
        """The `nav` list of any entry, as Steps. An entry may give a nav hop as a bare template
        name, or as {"template": t, "offset": [dx, dy]} when the thing that is RECOGNISABLE and the
        thing that is TAPPABLE are not the same pixel — the hub's rail labels and HUD overlays are
        distinctive but inert, while their icons are hit targets and look like everything else.

        A hop may also set `"scroll"`, because a nav target does not always stay put: the Quests
        list REORDERS as quests complete, sorting claimable rows to the top and pushing e.g. the
        Galactic War row below the fold, where its template matches nothing and the entry halts.
        `true` uses the engine's scan; a list of directions overrides it, which is what a vertical
        list needs (the default scan is horizontal, built for the campaign map). Opt-in per hop: a
        scan of the HUB would leave the panorama panned for every entry after this one."""
        steps = []
        for i, nav in enumerate(node.get("nav", [])):
            if isinstance(nav, str):
                nav = {"template": nav}
            scroll = nav.get("scroll")
            steps.append(Step(f"NAV_{i}", nav["template"],
                              tap_offset=tuple(nav.get("offset", (0, 0))),
                              scrollable=bool(scroll) or node.get("scrollable", False),
                              scroll_scan=tuple(scroll) if isinstance(scroll, list) else ()))
        return steps

    def _steps_energy_node(self, node):
        """Build the ordered Step list for one node from its compact config entry.

        node = {"campaign": <name>, "node": <id>, ["difficulty": "hard"], ["chapter": <n>], "sim": "max"}
        Per-node templates: campaign_<name>, hard_tab (if difficulty), chapter_tab_<n>,
        node_<campaign>_<id> (campaign-scoped so e.g. Cantina 1-A and Fleet 1-A don't collide).
        """
        steps = [
            *self._hub_prelude(node),
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
            # OPTIONAL, for exactly the reason SELECT_DIFFICULTY is: the game remembers the last
            # chapter per campaign, and a tab template is captured UNSELECTED. Once the bot has
            # visited this chapter, the tab renders selected and the unselected template stops
            # matching — which is what made DS chapter 8 halt on every run after the first.
            # Absent tab => already on it. If we are genuinely on the wrong chapter, SELECT_NODE
            # fails next and halts there, which is the clearer signal anyway.
            # scrollable: high chapter tabs (e.g. Cantina 9) can sit off the visible tab row.
            steps.append(Step("SELECT_CHAPTER", tab, scrollable=True, optional=True,
                              optional_counter="chapter_already_set"))
        # On a Hard node the panel can open into a depleted state (no MULTI SIM) — treat that as
        # "panel ready" so SELECT_NODE stops re-tapping, then OPEN_MULTISIM skips it cleanly.
        node_ensure_extra = (TPL_HARD_DEPLETED, *TPL_HARD_DEPLETED_ALT) if is_hard else ()
        steps += [
            # Node icons are captured UNSELECTED, but the map keeps the last-played node selected,
            # so on the second visit the icon is glowing and the unselected crop misses — this is
            # what halted DS 8-B every run after the first, with the panel already open and MULTI
            # SIM sitting right there. `_sel` is an optional companion crop of the same node in its
            # selected state; matching THAT node specifically is what makes it safe to proceed
            # (a bare "is a panel open?" check could sim whatever node someone left selected).
            Step("SELECT_NODE", f"node_{node['campaign']}_{node['node']}",
                 alt=(f"node_{node['campaign']}_{node['node']}_sel",),
                 ensure=TPL_MULTI_SIM, ensure_extra=node_ensure_extra, scrollable=True),
            Step("OPEN_MULTISIM", TPL_MULTI_SIM,
                 skip_marker=TPL_HARD_DEPLETED, skip_marker_alt=TPL_HARD_DEPLETED_ALT,
                 skip_tap=False, skip_counter="hard_depleted_nodes"),
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
        steps = self._hub_prelude(node) + self._nav_steps(node)
        counter = node.get("counter", "collected")
        for i in range(node.get("count", 1)):
            # skip_entry from the SECOND iteration on. An absent optional step is not free: it pays
            # a full look, a popup sweep and a re-look, and `count` 8 on an empty Quests panel plus
            # 6 on an empty inbox burned ~10 minutes of a live run proving there was nothing there.
            # Once a claim is gone the ones stacked behind it are gone too, so the rest of the entry
            # is moot. What stops a *transient* miss ending the entry is that `look` polls for the
            # whole step timeout and the engine re-looks after dismissing popups — two full windows,
            # against a reward overlay that fades in well under one.
            # Iteration 0 stays a plain skip: an entry with nothing to collect books
            # nothing_to_collect and leaves through its own RETURN_HOME.
            steps.append(Step(f"CLAIM_{i}", node["claim"], optional=True, mark=counter,
                              skip_entry=i > 0,
                              optional_counter=("nothing_to_collect" if i == 0 else None)))
            # Dismiss AFTER EVERY claim, not once at the end: each claim throws up a rewards
            # overlay that covers the next CLAIM button, so a single trailing dismissal drained
            # exactly one item per run no matter how many were stacked up.
            steps.append(Step(f"CLAIMED_{i}", TPL_REWARDS, optional=True))
        steps.append(Step("RETURN_HOME", TPL_HOME_BUTTON))
        return steps

    def _steps_challenge_sim(self, node):
        """Sim ALL daily challenges in one action (captured live). Flow: HOME -> Events console
        (off the initial hub, so scrollable) -> Challenges tab -> MULTI SIM -> SIM confirm ->
        rewards -> home. When nothing is simmable the MULTI SIM button is greyed (its green template
        won't match), so the optional MULTI_SIM/CONFIRM steps skip cleanly with no halt. `mark`=
        'challenges_simmed' keeps it disjoint from energy sims_done. Bulk, so no per-challenge field."""
        return [
            *self._hub_prelude(node),
            Step("OPEN_EVENTS", TPL_EVENTS_ENTRY, tap_offset=EVENTS_ENTRY_TAP_OFFSET,
                 ensure=TPL_EVENTS_MENU),
            Step("CHALLENGES_TAB", TPL_CHALLENGES_TAB, ensure=TPL_CHALLENGES_MENU),
            Step("CHALLENGES_MENU", TPL_CHALLENGES_MENU, tap=False),
            Step("MULTI_SIM", TPL_CHALLENGES_MULTISIM, optional=True,
                 ensure=TPL_CHALLENGES_SIM_CONFIRM),
            Step("CONFIRM_SIM", TPL_CHALLENGES_SIM_CONFIRM, optional=True, mark="challenges_simmed"),
            Step("REWARDS", TPL_REWARDS, optional=True),
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
        steps = self._hub_prelude(node) + self._nav_steps(node)
        for a in range(node.get("attempts", 1)):
            # START is OPTIONAL because it greys out once the day's attempts are spent — the raid
            # after submission, the Coliseum past its last try. Requiring it made a second run of
            # the day halt and strand the app inside the battle screen, which broke the
            # idempotence the whole routine depends on. Absent START => no battle => the AUTO and
            # OUTCOME steps below find nothing and skip too.
            steps.append(Step(f"START_{a}", start, optional=True, skip_entry=True,
                              optional_counter="battles_unavailable"))
            # The SECOND tap of the same button. Coliseum's `BATTLE (n)` and the squad-select
            # `BATTLE` that follows it are one template, so an attempt is two presses, not one.
            # Only attempt 1 ever worked, because the config smuggled its first press into `nav`;
            # attempts 2+ pressed once and sat on squad select until OUTCOME timed out. Attempts
            # are 5/day against a payout that resets daily, so each of those was lost for good.
            # Optional, which is what makes it safe when there is no second button: a flow that
            # goes straight into the fight (or a raid that deploys in one press) finds nothing
            # here and skips. It can only ever fire where the start template actually matched,
            # so it cannot wander onto the 💎250 refresh that replaces a spent BATTLE button.
            steps.append(Step(f"DEPLOY_{a}", start, optional=True))
            steps.append(Step(f"AUTO_{a}", auto, optional=True))
            # Stays REQUIRED: once a battle has actually started, an outcome we cannot read is a
            # genuine unknown and should halt with a screenshot. It is only unreachable-by-design
            # when START was absent, and skip_entry above has already left the entry by then.
            steps.append(Step(f"OUTCOME_{a}", victory, timeout=btimeout, mark="battles_won",
                              alt=tuple(node.get("victory_alt", ())),
                              skip_marker=defeat, skip_tap=True, skip_counter="battles_lost"))
            steps.append(Step(f"POST_{a}", TPL_REWARDS, optional=True))
        steps.append(Step("RETURN_HOME", TPL_HOME_BUTTON))
        return steps

    def _steps_sequence(self, node):
        """A navigate-then-press-these-in-order entry, for flows that are just a fixed button
        sequence rather than a battle or a node sim. Galactic War is the motivating case:
        RESTART -> MULTI SIM -> SIM confirm -> rewards is four taps and no fighting, because a
        50+-completion account can sim the whole war for sim tickets.

        Every tap defaults to OPTIONAL, which is the important part: buttons in these flows grey
        out once the thing is done for the day (GW's RESTART during an active war, its MULTI SIM
        once simmed). Optional means "already done today" reads as a skip, not a halt, so the entry
        is safely idempotent — running the routine twice in a day does nothing the second time.

        node = {"nav": [tpl...], "taps": [{"template": t, ["offset": [dx,dy]], ["mark": counter],
                 ["required": true]}]}
        """
        steps = self._hub_prelude(node) + self._nav_steps(node)
        for i, t in enumerate(node.get("taps", [])):
            steps.append(Step(f"STEP_{i}_{t['template']}"[:40], t["template"],
                              tap_offset=tuple(t.get("offset", (0, 0))),
                              optional=not t.get("required", False),
                              mark=t.get("mark"),
                              timeout=t.get("timeout")))
        steps.append(Step("RETURN_HOME", TPL_HOME_BUTTON))
        return steps

    def _steps_shop(self, node):
        """Buy token-priced shop items: HOME -> [recenter] -> nav to a shop tab -> per buy
        (item -> confirm) -> RETURN_HOME.

        Shipments prices some tabs in TOKENS and others in CRYSTALS using visually identical green
        buttons, and every tab carries a permanent "REFRESH ... 💎50" bar. Two independent guards
        keep the never-spend-crystals rail intact — either alone would be enough:

        1. Only an ITEM-SPECIFIC template is ever a tap target. `buys[].item` names a template
           cropped around one product card, so there is no template at all for the REFRESH bar and
           no generic "green button" to hit by accident. Shop stock rotates, so an item that isn't
           offered today simply doesn't match => optional skip, not a halt.
        2. `confirm` is a CURRENCY-SPECIFIC template ("BUY" + that currency's coin, digits
           excluded so it survives a price change). A crystal-priced dialog renders a different
           coin, so the confirm never matches and the buy is skipped. No crystal-currency confirm
           template exists, which is what makes this a rail rather than a check.

        An entry may additionally set `forbid` (a veto template): if that is on screen the confirm
        is abandoned via CANCEL and booked to `blocked_spends`. Off by default — guard 2 already
        covers the crystal case, and a screen-wide glyph search would false-positive on the
        permanent REFRESH bar.

        `buys` = [{"item": <template>, ["count": n]}].
        """
        steps = self._hub_prelude(node) + self._nav_steps(node)
        confirm = node.get("confirm", TPL_SHOP_CONFIRM)
        cancel = node.get("cancel", TPL_SHOP_CANCEL)
        for b, buy in enumerate(node.get("buys", [])):
            for n in range(buy.get("count", 1)):
                # optional: stock rotates, and a sold-out/unaffordable item stops matching mid-loop.
                steps.append(Step(f"ITEM_{b}_{n}", buy["item"], optional=True,
                                  scrollable=node.get("scrollable", False)))
                steps.append(Step(f"BUY_{b}_{n}", confirm, optional=True, mark="bought",
                                  forbid=node.get("forbid"), forbid_tap=cancel))
                steps.append(Step(f"BOUGHT_{b}_{n}", TPL_REWARDS, optional=True))
        steps.append(Step("RETURN_HOME", TPL_HOME_BUTTON))
        return steps

    def _steps_conquest(self, node):
        """Conquest: hub -> Galactic Battles console -> CONQUEST -> sector map -> free disks,
        then up to `max_battles` node fights.

        Three things make this its own kind rather than a `battle` with a long `nav`:

        1. **The chooser is ambiguous.** "SELECT A GALACTIC BATTLE" shows WAR and CONQUEST with
           pixel-identical ENTER buttons, so no ENTER template can tell them apart. The CONQUEST
           title is unique, and its ENTER sits +704px below it. A blind offset can miss, so
           SECTOR_LIST verifies the sector-list header before anything else is pressed — that is
           the check that we are in Conquest and not in Galactic War.
        2. **Starting a fight takes two taps.** `conquest_battle_btn` matches the Combat Details
           "BATTLE ⚡20" AND the squad-select "BATTLE". A single start step taps the first and
           strands the run on squad select (already recorded live for Coliseum). So START taps
           once with `ensure_retries=0` — it verifies the squad screen appeared but never re-taps
           to force it, because if we were ALREADY on squad select that first tap started the
           fight and a re-tap would land inside a live battle. DEPLOY then presses the same
           button again, and is optional precisely so the already-started case skips it.
        3. **Nothing after a battle is guessed.** Conquest's defeat/retry flow sells crystal-priced
           Stim Packs and has never been captured, so OUTCOME is REQUIRED, has no skip marker and
           taps nothing it cannot name: an unreadable post-battle screen halts with a screenshot
           for a human. That is the crystal rail here — the engine cannot press a Stim Pack
           because it has no template that could match one.

        What it deliberately does NOT decide is which node to attack. `conquest_node_open` matches
        every un-cleared node equally, so the engine fights whichever one the matcher happens to
        rank highest — that is arbitrary, not strategic, and Conquest node choice is strategic
        (paths branch, and the golden Challenge Path gates one of the event feats). `max_battles`
        exists so the arbitrary picks stay cheap; routing stays the owner's job.

        node = {"kind": "conquest", "pan": "far_right", ["disks": n], ["max_battles": n],
                "battles": [{"node": <template>, ["count": n]}]}
        """
        disk = node.get("disk", TPL_CONQUEST_DISK_STOCKPILE)
        obtained = node.get("obtained", TPL_CONQUEST_DISK_OBTAINED)
        battle_btn = node.get("battle_btn", TPL_CONQUEST_BATTLE_BTN)
        auto = node.get("auto", TPL_BATTLE_AUTO)
        victory = node.get("victory", TPL_VICTORY)
        btimeout = node.get("battle_timeout_s", DEFAULT_BATTLE_TIMEOUT_S)
        counter = node.get("counter", "collected")
        steps = [
            *self._hub_prelude(node),
            Step("GALACTIC_BATTLES", TPL_GALACTIC_BATTLES),
            Step("CHOOSE_CONQUEST", TPL_CONQUEST_CARD, tap_offset=CONQUEST_ENTER_TAP_OFFSET),
            Step("SECTOR_LIST", TPL_CONQUEST_HEADER, tap=False),
            # Only the unlocked sector renders an ENTER; the locked rows show a padlock instead,
            # so there is nothing to disambiguate and no offset to guess.
            Step("ENTER_SECTOR", TPL_CONQUEST_ENTER),
            Step("SECTOR_MAP", TPL_CONQUEST_FEATS_PANEL, tap=False),
        ]
        for i in range(node.get("disks", 0)):
            # ⚠️ KNOWN DEAD STEP — it cannot fire, and has never fired. `conquest_disk_stockpile`
            # is the TITLE TEXT of the stockpile panel ("Data Disk Stockpile"), and that panel only
            # opens once the map HEX is tapped. Nothing here taps the hex, so the step matches
            # nothing and skips. Measured 2026-08-04: 0.000 against a sector map with two
            # stockpiles plainly on it, then 1.000 the instant the panel was open by hand. Past
            # runs booking `collected=0` were not "already taken" — they were unreachable.
            #
            # Fixing it needs BOTH a template for the map hex (none exists) and a decision this
            # code cannot make: the panel is a PICK ONE OF THREE list ending in a "MOVE TO DATA
            # DISK PILE" confirm that locks the branch, and the disk then lands UNEQUIPPED in the
            # inventory needing an equip + CONFIRM against a 12-point capacity budget. There is no
            # "just tap it" behaviour to automate — see memory/notes.md, session 7.
            #
            # Left in place, and deliberately harmless: `optional` means it skips instead of
            # halting, and no `skip_entry` means it cannot cancel the node fights queued behind it.
            steps.append(Step(f"DISK_{i}", disk, optional=True, mark=counter,
                              ensure=obtained, ensure_retries=0))
        # `conquest_node_open` matches EVERY un-cleared node while the engine takes the single
        # best match, so a spec carries a `count` instead of being repeated. What makes the count
        # advance rather than re-hit one node is that clearing a node DIMS it: measured on a live
        # sector map, open nodes scored 1.000/0.973 and cleared ones 0.663/0.348, either side of
        # the 0.85 match threshold. Which open node gets picked is arbitrary (render noise decides
        # 1.000 vs 0.973) — see the config entry, that choice is the owner's, not the engine's.
        # Cap AFTER expanding, or a `count` sails straight past the stamina budget.
        battles = [b for b in node.get("battles", ()) for _ in range(b.get("count", 1))]
        battles = battles[:node.get("max_battles", DEFAULT_CONQUEST_MAX_BATTLES)]
        for a, battle in enumerate(battles):
            steps += [
                Step(f"NODE_{a}", battle["node"], optional=True, skip_entry=True,
                     ensure=TPL_CONQUEST_COMBAT_DETAILS, optional_counter="battles_unavailable"),
                Step(f"START_{a}", battle_btn, optional=True, skip_entry=True,
                     ensure=TPL_CONQUEST_SQUAD_PROMPT, ensure_retries=0,
                     optional_counter="battles_unavailable"),
                Step(f"DEPLOY_{a}", battle_btn, optional=True),
                # Captured in its OFF state, so once AUTO is on it stops matching and this skips —
                # which is the behaviour we want. There is deliberately no ON-state alternative:
                # matching one would make this tap AUTO back OFF.
                Step(f"AUTO_{a}", auto, optional=True),
                Step(f"OUTCOME_{a}", victory, timeout=btimeout, mark="battles_won",
                     alt=tuple(node.get("victory_alt", ()))),
                Step(f"POST_{a}", TPL_REWARDS, optional=True),
            ]
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
        """Best-effort return to the hub after a skip/halt: clear any popups, then tap the home
        button if present. If it isn't, the next entry's HOME verify handles it (skip or halt)."""
        self._dismiss_popups()
        m = self.look(TPL_HOME_BUTTON, self.energy_out_timeout)
        if m is not None:
            self._tap(m)

    def _ensure_hub(self):
        """Start-of-run repair. A run that halted mid-flow leaves the game deep in a menu, and then
        the NEXT run halts on its very first HOME check — before it has collected anything (this
        cost two runs in one evening). Try what the engine already does after a skip: clear known
        popups, and only if the hub still isn't showing, tap the home button. Once per run, not per
        entry: an entry that cannot reach the hub mid-routine is a real failure and should still
        halt with a screenshot."""
        if self.should_stop() or self.look(TPL_HOME, self.energy_out_timeout) is not None:
            return
        if self._dismiss_popups() and self.look(TPL_HOME, self.energy_out_timeout) is not None:
            return                      # the hub was there all along, just covered
        m = self.look(TPL_HOME_BUTTON, self.energy_out_timeout)
        if m is not None:
            self._tap(m)

    def _pan(self, target, swipes):
        """Swipe the hub panorama until it clamps against `target`'s end stop. Deliberately
        over-swipes: past the edge each extra swipe is a no-op, which is exactly what makes the
        resulting pan reproducible. Not counted against max_actions (navigation, not an action)."""
        direction = _PAN_SWIPE_DIRECTION[target]
        for _ in range(swipes):
            if self.should_stop():
                return
            self.swipe(direction)
            self.delay()

    def _scroll_find(self, template, scan=()):
        """Swipe to bring an off-screen target into view, re-looking after each swipe. `scan`
        overrides the engine's default directions for a target on the other axis (a quest list
        scrolls vertically, the campaign map horizontally).
        Swipes don't count toward the action cap (they're navigation, not sim actions)."""
        for direction in (scan or self.scroll_scan):
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
                name, offset = tap_target(closer)
                m = self.look(name, self.energy_out_timeout)
                if m is not None:
                    self._tap(m, offset)
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
        self._ensure_hub()
        for node in self.nodes:
            if self.should_stop():
                s.stopped_reason = "killed"
                return s
            s.nodes_attempted += 1
            skipped = False
            try:
                steps = self._steps_for(node)
            except (KeyError, ValueError, TypeError) as exc:
                # A malformed entry (missing "claim", a typo'd pan target) used to raise straight
                # out of run(), losing the Summary, the report and every entry after it — the one
                # failure --daily is supposed to contain. Treat it as this entry's halt.
                self._bump(s, "halted_entries")
                s.halt_state = f"CONFIG:{node.get('name') or node.get('kind', 'entry')}:{exc}"
                if not self.continue_on_halt:
                    s.halted = True
                    s.stopped_reason = "halt"
                    return s
                continue
            for step in steps:
                if self._actions >= self.max_actions:
                    s.stopped_reason = "cap"
                    return s
                if self.should_stop():
                    s.stopped_reason = "killed"
                    return s
                if step.pan is not None:
                    # Not a perception step: drive the hub camera into an end stop so the consoles
                    # that live off the default pan sit at reproducible screen positions.
                    self._pan(step.pan, step.pan_swipes)
                    continue
                m = self.look(step.template, step.timeout if step.timeout is not None else self.timeout)
                for alt in step.alt:
                    if m is not None:
                        break
                    m = self.look(alt, self.energy_out_timeout)
                if m is None and step.scrollable:
                    # target may be off-screen; swipe-scan on the step's axis
                    m = self._scroll_find(step.template, step.scroll_scan)
                if m is None and step.optional:
                    # A popup can hide a control that IS there. Without this, a calendar covering
                    # the Quests screen made eight claimable crates read as "nothing to collect".
                    if self._dismiss_popups():
                        m = self.look(step.template, self.timeout)
                    if m is None:
                        if step.optional_counter:
                            self._bump(s, step.optional_counter)
                        if step.skip_entry:
                            self._recover_to_home()
                            skipped = True
                            break
                        continue   # genuinely not applicable (e.g. already on that difficulty)
                if m is None:
                    # Expected interruption (energy-out / depleted Hard): marker present => skip node.
                    if step.skip_marker is not None:
                        marker = self.look(step.skip_marker, self.energy_out_timeout)
                        for skin in step.skip_marker_alt:
                            if marker is not None:
                                break
                            marker = self.look(skin, self.energy_out_timeout)
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
                            m = self._scroll_find(step.template, step.scroll_scan)
                    if m is None:
                        self.halt(step.label)
                        if self.continue_on_halt:
                            # Orchestrator mode: isolate this entry's failure, recover to the hub,
                            # and carry on with the rest of the daily routine.
                            self._bump(s, "halted_entries")
                            s.halt_state = step.label
                            self._recover_to_home()
                            skipped = True
                            break
                        s.halted = True
                        s.halt_state = step.label
                        s.stopped_reason = "halt"
                        return s
                if step.forbid is not None and self.look(step.forbid, self.energy_out_timeout):
                    # Veto. The control matched, but the surrounding state makes tapping it unsafe
                    # — a purchase dialog showing a crystal price. Back out via CANCEL rather than
                    # confirm, and abandon the entry; the rest of the routine is unaffected.
                    self._bump(s, step.forbid_counter)
                    if step.forbid_tap:
                        cancel = self.look(step.forbid_tap, self.energy_out_timeout)
                        if cancel is not None:
                            self._tap(cancel)
                    self._recover_to_home()
                    skipped = True
                    break
                if step.tap:
                    self._tap(m, step.tap_offset)
                    if step.ensure:
                        # some taps toggle a panel (e.g. tapping an already-selected node
                        # closes its detail panel); re-tap until the expected panel appears.
                        tries = step.ensure_retries
                        while tries > 0 and not self._panel_ready(step):
                            self._tap(m, step.tap_offset)
                            tries -= 1
                    # Booked only once the tap has demonstrably landed. Marking before the ensure
                    # loop let a recenter that never moved the camera still report recentered=1.
                    if step.ensure and not self._panel_ready(step):
                        continue
                    if step.mark_sim:
                        s.sims_done += 1
                    if step.mark:
                        self._bump(s, step.mark)
            if skipped:
                continue
        return s
