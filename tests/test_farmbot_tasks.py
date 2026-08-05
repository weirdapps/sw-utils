from collections import namedtuple

import pytest

from farmbot.tasks import EnergyDumpTask

M = namedtuple("M", ["cx", "cy", "confidence"])

# The templates present on the real happy-path flow for one cantina node "1-A" (no chapter).
FLOW = {"home", "campaigns_entry", "campaigns_menu", "campaign_cantina",
        "node_cantina_1-A", "multi_sim", "sim_confirm", "rewards", "home_button"}
NODE = {"campaign": "cantina", "node": "1-A", "sim": "max"}

# A Hard node (LS Hard 1-D): adds hard_tab + chapter_tab_1 to the flow.
HARD_NODE = {"campaign": "light", "difficulty": "hard", "chapter": 1, "node": "1-D", "sim": "max"}
HARD_FLOW = {"home", "campaigns_entry", "campaigns_menu", "campaign_light", "hard_tab",
             "chapter_tab_1", "node_light_1-D", "multi_sim", "sim_confirm", "rewards", "home_button"}


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
               "campaign_light", "node_cantina_1-A", "node_light_1-A", "multi_sim", "rewards",
               "home_button", "energy_out"}
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


def test_hard_difficulty_adds_toggle_tap():
    node = {"campaign": "light", "difficulty": "hard", "chapter": 1, "node": "1-D", "sim": "max"}
    present = {"home", "campaigns_entry", "campaigns_menu", "campaign_light", "hard_tab",
              "chapter_tab_1", "node_light_1-D", "multi_sim", "sim_confirm", "rewards", "home_button"}
    taps = []
    task = EnergyDumpTask([node], scripted_look(present), lambda x, y: taps.append((x, y)))
    s = task.run()
    assert s.sims_done == 1
    assert s.halted is False
    assert len(taps) == 9        # +SELECT_DIFFICULTY vs the 8-tap chaptered non-hard flow


def test_difficulty_toggle_skipped_when_already_on_wanted_difficulty():
    # Game remembers difficulty. If already on Hard, the unselected HARD button isn't shown, so the
    # optional SELECT_DIFFICULTY step is skipped rather than halting.
    node = {"campaign": "light", "difficulty": "hard", "chapter": 1, "node": "1-D", "sim": "max"}
    present = HARD_FLOW - {"hard_tab"}          # already on Hard
    taps = []
    task = EnergyDumpTask([node], scripted_look(present), lambda x, y: taps.append((x, y)))
    s = task.run()
    assert s.sims_done == 1
    assert s.halted is False
    assert len(taps) == 8                       # no difficulty toggle tap (vs 9 when it's present)


def test_normal_node_taps_normal_toggle_when_on_difficulty_campaign():
    # A Normal LS/DS/Fleet node ensures Normal is selected via the (optional) normal_tab.
    node = {"campaign": "light", "difficulty": "normal", "chapter": 1, "node": "1-A", "sim": "max"}
    present = {"home", "campaigns_entry", "campaigns_menu", "campaign_light", "normal_tab",
               "chapter_tab_1", "node_light_1-A", "multi_sim", "sim_confirm", "rewards", "home_button"}
    taps = []
    task = EnergyDumpTask([node], scripted_look(present), lambda x, y: taps.append((x, y)))
    s = task.run()
    assert s.sims_done == 1
    assert s.halted is False
    assert len(taps) == 9                       # includes the normal_tab tap


def test_cantina_has_no_difficulty_step():
    # Cantina/Mod have no Normal/Hard toggle: a missing normal_tab/hard_tab must not matter.
    task = EnergyDumpTask([NODE], scripted_look(FLOW), lambda x, y: None)  # FLOW has no *_tab
    s = task.run()
    assert s.sims_done == 1
    assert s.halted is False


def test_scrollable_node_found_after_swipe():
    present = FLOW - {"node_cantina_1-A"}                    # node not in initial view
    look = scripted_look(present, sequences={"node_cantina_1-A": [False, True]})  # appears after a swipe
    swipes = []
    task = EnergyDumpTask([NODE], look, lambda x, y: None, swipe=lambda d: swipes.append(d))
    s = task.run()
    assert s.halted is False
    assert s.sims_done == 1
    assert len(swipes) >= 1


def test_scroll_gives_up_and_halts():
    present = FLOW - {"node_cantina_1-A"}                    # node never appears
    halts, swipes = [], []
    task = EnergyDumpTask([NODE], scripted_look(present), lambda x, y: None,
                          halt=lambda st: halts.append(st), swipe=lambda d: swipes.append(d))
    s = task.run()
    assert s.halted is True
    assert s.halt_state == "SELECT_NODE"
    assert len(swipes) == 6                          # exhausted the default scroll_scan


def test_hard_depleted_skips_and_recovers_without_halting():
    # A Hard node whose 5 daily attempts are used up: the panel shows a refresh timer + 💎200
    # instead of MULTI SIM. hard_depleted present, multi_sim/sim_confirm absent -> skip, not halt,
    # and NEVER tap the panel (skip_tap=False) so the 💎200 refresh is never pressed.
    present = (HARD_FLOW - {"multi_sim", "sim_confirm"}) | {"hard_depleted"}
    taps, halts = [], []
    task = EnergyDumpTask([HARD_NODE], scripted_look(present),
                          lambda x, y: taps.append((x, y)), halt=lambda st: halts.append(st))
    s = task.run()
    assert s.halted is False
    assert halts == []
    assert s.hard_depleted_nodes == 1
    assert s.sims_done == 0
    assert s.stopped_reason == "complete"
    # OPEN_CAMPAIGNS, SELECT_CAMPAIGN, SELECT_DIFFICULTY, SELECT_CHAPTER, SELECT_NODE, home_button = 6
    # (no OPEN_MULTISIM/CONFIRM tap; SELECT_NODE ensure is satisfied by hard_depleted so it doesn't re-tap)
    assert len(taps) == 6


def test_hard_depleted_multi_node_continues_to_next():
    # Two depleted Hard nodes: skip the first, recover, skip the second — never halt. State is
    # stable per frame (no MULTI SIM ever appears, hard_depleted always shows), as on a real device.
    n2 = {"campaign": "light", "difficulty": "hard", "chapter": 1, "node": "1-E", "sim": "max"}
    present = (HARD_FLOW - {"multi_sim", "sim_confirm"}) | {"hard_depleted", "node_light_1-E"}
    task = EnergyDumpTask([HARD_NODE, n2], scripted_look(present), lambda x, y: None)
    s = task.run()
    assert s.nodes_attempted == 2
    assert s.hard_depleted_nodes == 2
    assert s.sims_done == 0
    assert s.halted is False
    assert s.stopped_reason == "complete"


def test_popup_dismissed_then_proceeds():
    # A hub popup covers HOME on the first look; popup_close present -> tap it -> HOME appears -> proceed.
    look = scripted_look(FLOW, sequences={"home": [False, True], "popup_close": [True, False]})
    taps = []
    task = EnergyDumpTask([NODE], look, lambda x, y: taps.append((x, y)))
    s = task.run()
    assert s.halted is False
    assert s.sims_done == 1
    assert len(taps) == 8            # 1 popup dismiss + 7 happy-path taps


def test_popup_dismiss_gives_up_and_halts():
    # HOME never appears and no known popup closer is present -> halt at HOME.
    present = FLOW - {"home"}
    halts = []
    task = EnergyDumpTask([NODE], scripted_look(present), lambda x, y: None,
                          halt=lambda st: halts.append(st))
    s = task.run()
    assert s.halted is True
    assert s.halt_state == "HOME"
    assert halts == ["HOME"]


def test_mod_chapter_uses_scoped_tab_template():
    # Mod Battles tier tabs are campaign-scoped: chapter 2 -> chapter_tab_mod_2, NOT chapter_tab_2.
    node = {"campaign": "mod", "chapter": 2, "node": "2-F", "sim": "max"}
    present = {"home", "campaigns_entry", "campaigns_menu", "campaign_mod", "chapter_tab_mod_2",
               "node_mod_2-F", "multi_sim", "sim_confirm", "rewards", "home_button"}
    # chapter_tab_2 (generic) present too — must be ignored in favor of the scoped one.
    task = EnergyDumpTask([node], scripted_look(present | {"chapter_tab_2"}), lambda x, y: None)
    s = task.run()
    assert s.sims_done == 1
    assert s.halted is False


def test_mod_chapter_never_taps_the_generic_tab():
    """Mod's tier tabs look nothing like the shared LS/DS/Cantina/Fleet chapter tabs, so Mod tier 2
    must ask for chapter_tab_mod_2 and never settle for a same-numbered generic tab."""
    node = {"campaign": "mod", "chapter": 2, "node": "2-F", "sim": "max"}
    task = EnergyDumpTask([node], scripted_look(set()), lambda x, y: None)
    chapter = [st for st in task._steps_for(node) if st.label == "SELECT_CHAPTER"]
    assert [st.template for st in chapter] == ["chapter_tab_mod_2"]

    # and with only the generic tab on screen it is skipped, not tapped
    present = {"home", "campaigns_entry", "campaigns_menu", "campaign_mod", "chapter_tab_2",
               "node_mod_2-F", "multi_sim", "sim_confirm", "rewards", "home_button"}
    s = EnergyDumpTask([node], scripted_look(present), lambda x, y: None).run()
    assert s.chapter_already_set == 1


def test_standard_chapter_uses_generic_tab_template():
    # LS/DS/Cantina/Fleet share the generic chapter_tab_<n>.
    node = {"campaign": "cantina", "chapter": 3, "node": "3-B", "sim": "max"}
    present = {"home", "campaigns_entry", "campaigns_menu", "campaign_cantina", "chapter_tab_3",
               "node_cantina_3-B", "multi_sim", "sim_confirm", "rewards", "home_button"}
    task = EnergyDumpTask([node], scripted_look(present), lambda x, y: None)
    s = task.run()
    assert s.sims_done == 1
    assert s.halted is False


def test_chapter_tab_found_after_swipe():
    # A high chapter tab isn't in the initial view; SELECT_CHAPTER swipe-scans to reveal it.
    node = {"campaign": "cantina", "chapter": 9, "node": "9-A", "sim": "max"}
    present = {"home", "campaigns_entry", "campaigns_menu", "campaign_cantina",
               "node_cantina_9-A", "multi_sim", "sim_confirm", "rewards", "home_button"}
    look = scripted_look(present, sequences={"chapter_tab_9": [False, True]})  # appears after a swipe
    swipes = []
    task = EnergyDumpTask([node], look, lambda x, y: None, swipe=lambda d: swipes.append(d))
    s = task.run()
    assert s.halted is False
    assert s.sims_done == 1
    assert len(swipes) >= 1


def test_unknown_kind_raises_when_building_steps():
    task = EnergyDumpTask([], scripted_look(set()), lambda x, y: None)
    with pytest.raises(ValueError, match="unknown routine kind"):
        task._steps_for({"kind": "bogus"})


def test_a_malformed_entry_aborts_only_itself_under_daily():
    """A typo in one entry used to raise straight out of run(), losing the Summary, the report and
    every entry after it — the exact failure --daily exists to contain."""
    good = {"campaign": "cantina", "node": "1-A", "sim": "max"}
    routine = [{"kind": "collect", "name": "typo", "nav": []}, good]   # no "claim" key
    s = EnergyDumpTask(routine, scripted_look(FLOW), lambda x, y: None,
                       continue_on_halt=True).run()
    assert s.halted is False
    assert s.halted_entries == 1
    assert s.halt_state.startswith("CONFIG:typo")
    assert s.sims_done == 1          # the good entry after it still ran
    assert s.stopped_reason == "complete"


def test_a_malformed_entry_still_stops_a_debug_run():
    routine = [{"kind": "collect", "name": "typo", "nav": []}]
    s = EnergyDumpTask(routine, scripted_look(FLOW), lambda x, y: None).run()
    assert s.halted is True
    assert s.stopped_reason == "halt"


def test_explicit_energy_node_kind_still_simms():
    node = {"kind": "energy_node", "campaign": "cantina", "node": "1-A", "sim": "max"}
    task = EnergyDumpTask([node], scripted_look(FLOW), lambda x, y: None)
    assert task.run().sims_done == 1


def test_collect_happy_path():
    node = {"kind": "collect", "nav": ["inbox_entry"], "claim": "login_claim"}
    present = {"home", "inbox_entry", "login_claim", "rewards", "home_button"}
    taps = []
    task = EnergyDumpTask([node], scripted_look(present), lambda x, y: taps.append((x, y)))
    s = task.run()
    assert s.halted is False
    assert s.collected == 1
    assert s.nothing_to_collect == 0
    assert len(taps) == 4        # nav + claim + reward-dismiss + home


def test_collect_nothing_to_collect_when_claim_absent():
    node = {"kind": "collect", "nav": ["inbox_entry"], "claim": "login_claim"}
    present = {"home", "inbox_entry", "home_button"}   # no claim, no reward popup
    taps = []
    task = EnergyDumpTask([node], scripted_look(present), lambda x, y: taps.append((x, y)))
    s = task.run()
    assert s.halted is False
    assert s.collected == 0
    assert s.nothing_to_collect == 1
    assert len(taps) == 2        # nav + home only (claim + reward optional-skipped)


def test_collect_count_claims_until_absent():
    node = {"kind": "collect", "nav": [], "claim": "gift_claim", "count": 3}
    present = {"home", "home_button"}
    look = scripted_look(present, sequences={"gift_claim": [True, True, False]})
    taps = []
    task = EnergyDumpTask([node], look, lambda x, y: taps.append((x, y)))
    s = task.run()
    assert s.collected == 2
    assert s.nothing_to_collect == 0     # first claim present => i==0 did not book "nothing"
    assert len(taps) == 3                # 2 claims + home


def test_collect_ends_the_entry_once_a_later_claim_is_absent():
    """`count` used to probe every iteration even on an empty panel, and each absent optional step
    pays a full look + popup sweep + retry. With count 8 on the Quests panel and 6 on the inbox, a
    live run spent ~10 minutes finding nothing."""
    node = {"kind": "collect", "nav": [], "claim": "gift_claim", "count": 8}
    looks = []
    inner = scripted_look({"home", "home_button", "rewards"},
                          sequences={"gift_claim": [True, True, False]})

    def look(name, timeout):
        looks.append(name)
        return inner(name, timeout)

    taps = []
    s = EnergyDumpTask([node], look, lambda x, y: taps.append((x, y))).run()
    assert s.collected == 2
    assert s.halted is False
    assert looks.count("gift_claim") == 3   # 2 claims + the probe that ended it, not 8
    assert len(taps) == 5                   # 2 claims + 2 reward dismissals + return home


def test_stopping_a_collect_early_still_leaves_the_hub_ready():
    """Ending the entry mid-list must still put the app back on the hub, or every entry after it
    fails its HOME check."""
    early = {"kind": "collect", "name": "inbox", "nav": [], "claim": "gift_claim", "count": 6}
    after = {"kind": "collect", "name": "login", "nav": [], "claim": "login_claim"}
    look = scripted_look({"home", "home_button", "login_claim", "rewards"},
                         sequences={"gift_claim": [True, False]})
    s = EnergyDumpTask([early, after], look, lambda x, y: None).run()
    assert s.halted is False
    assert s.collected == 2          # 1 from the early-stopped entry + 1 from the next
    assert s.nodes_attempted == 2


def test_a_momentarily_covered_claim_does_not_end_the_entry():
    """The claim can still be behind the previous reward overlay when the next iteration looks for
    it. Before treating an optional step as absent the engine dismisses known popups and re-looks —
    that second look (on top of `look` itself being a polling wait) is what keeps a transient miss
    from ending the whole entry."""
    node = {"kind": "collect", "nav": [], "claim": "gift_claim", "count": 3}
    look = scripted_look({"home", "home_button", "rewards"},
                         sequences={"gift_claim": [True, False, True],
                                    "popup_close": [True, False]})
    s = EnergyDumpTask([node], look, lambda x, y: None).run()
    assert s.collected == 2          # the covered claim was found on the re-look, not skipped
    assert s.halted is False


def test_collect_free_energy_books_energy_claimed():
    node = {"kind": "collect", "nav": [], "claim": "energy_free_claim", "counter": "energy_claimed"}
    present = {"home", "energy_free_claim", "home_button"}
    task = EnergyDumpTask([node], scripted_look(present), lambda x, y: None)
    s = task.run()
    assert s.energy_claimed == 1
    assert s.collected == 0


def test_collect_does_not_tap_when_only_non_free_control_present():
    # A paid/"buy" control is present but the FREE claim template is absent -> nothing collected,
    # nothing tapped except the return-home. Proves paid controls are never tap targets.
    node = {"kind": "collect", "nav": [], "claim": "store_free_claim"}
    present = {"home", "store_buy_crystals", "home_button"}
    taps = []
    task = EnergyDumpTask([node], scripted_look(present), lambda x, y: taps.append((x, y)))
    s = task.run()
    assert s.halted is False
    assert s.collected == 0
    assert s.nothing_to_collect == 1
    assert len(taps) == 1                # only RETURN_HOME


def test_challenge_sim_bulk_multisim():
    # Real flow (captured live): Events -> Challenges tab -> MULTI SIM -> SIM confirm sims ALL
    # available daily challenges at once.
    node = {"kind": "challenge_sim"}
    present = {"home", "events_entry", "events_menu", "challenges_tab", "challenges_menu",
               "challenges_multisim", "challenges_sim_confirm", "rewards", "home_button"}
    taps = []
    task = EnergyDumpTask([node], scripted_look(present), lambda x, y: taps.append((x, y)))
    s = task.run()
    assert s.halted is False
    assert s.challenges_simmed == 1
    assert s.sims_done == 0            # disjoint from energy sims
    # taps: events, challenges_tab, multisim, sim_confirm, rewards, home = 6
    assert len(taps) == 6
    # The Events entry is the fixed "EVENT ACTIVE" HUD overlay, whose label is not itself a hit
    # target — the tap is offset up onto the portrait button.
    assert taps[0] == (10, 20 - 71)


def test_challenge_sim_nothing_to_sim_no_halt():
    # Nothing simmable => the green MULTI SIM is greyed (template absent) => optional steps skip,
    # no halt, no sim booked.
    node = {"kind": "challenge_sim"}
    present = {"home", "events_entry", "events_menu", "challenges_tab", "challenges_menu",
               "home_button"}
    halts = []
    task = EnergyDumpTask([node], scripted_look(present), lambda x, y: None,
                          halt=lambda st: halts.append(st))
    s = task.run()
    assert s.halted is False
    assert halts == []
    assert s.challenges_simmed == 0


def test_battle_happy_path_victory():
    node = {"kind": "battle", "nav": ["coliseum_tile"], "start": "battle_start"}
    present = {"home", "coliseum_tile", "battle_start", "battle_auto", "victory", "rewards", "home_button"}
    taps = []
    task = EnergyDumpTask([node], scripted_look(present), lambda x, y: taps.append((x, y)))
    s = task.run()
    assert s.halted is False
    assert s.battles_won == 1
    assert s.battles_lost == 0
    # tile, start, the second press of the same BATTLE button, auto, victory, rewards, home
    assert len(taps) == 7


def test_battle_defeat_recorded_no_halt():
    node = {"kind": "battle", "nav": ["coliseum_tile"], "start": "battle_start"}
    present = {"home", "coliseum_tile", "battle_start", "battle_auto", "defeat", "home_button"}  # no victory
    taps, halts = [], []
    task = EnergyDumpTask([node], scripted_look(present),
                          lambda x, y: taps.append((x, y)), halt=lambda st: halts.append(st))
    s = task.run()
    assert s.halted is False
    assert halts == []
    assert s.battles_lost == 1
    assert s.battles_won == 0


def test_battle_multiple_attempts():
    node = {"kind": "battle", "nav": [], "start": "battle_start", "attempts": 2}
    present = {"home", "battle_start", "battle_auto", "victory", "rewards", "home_button"}
    task = EnergyDumpTask([node], scripted_look(present), lambda x, y: None)
    s = task.run()
    assert s.battles_won == 2
    assert s.halted is False


def test_battle_auto_optional_when_absent():
    node = {"kind": "battle", "nav": [], "start": "battle_start"}
    present = {"home", "battle_start", "victory", "rewards", "home_button"}   # no battle_auto
    task = EnergyDumpTask([node], scripted_look(present), lambda x, y: None)
    s = task.run()
    assert s.battles_won == 1
    assert s.halted is False


def test_battle_unknown_outcome_halts():
    node = {"kind": "battle", "nav": [], "start": "battle_start", "battle_timeout_s": 0.01}
    present = {"home", "battle_start", "battle_auto", "home_button"}   # neither victory nor defeat
    halts = []
    task = EnergyDumpTask([node], scripted_look(present), lambda x, y: None,
                          halt=lambda st: halts.append(st))
    s = task.run()
    assert s.halted is True
    assert s.halt_state == "OUTCOME_0"


def test_daily_continue_on_halt_isolates_entries():
    # Orchestrator mode: entry 1 halts (panel reached but no MULTI SIM, not energy-out), entry 2 is a
    # clean collect. The halt is isolated: run completes, entry 2 still executes.
    n1 = {"campaign": "cantina", "node": "1-A", "sim": "max"}
    n2 = {"kind": "collect", "nav": [], "claim": "login_claim"}
    present = {"home", "campaigns_entry", "campaigns_menu", "campaign_cantina", "node_cantina_1-A",
               "login_claim", "rewards", "home_button"}   # no multi_sim/sim_confirm/energy_out
    task = EnergyDumpTask([n1, n2], scripted_look(present), lambda x, y: None, continue_on_halt=True)
    s = task.run()
    assert s.halted is False              # run completed, not aborted
    assert s.halted_entries == 1          # entry 1 halted but was isolated
    assert s.collected == 1               # entry 2 still ran
    assert s.stopped_reason == "complete"


def test_default_halt_aborts_whole_run():
    # Without continue_on_halt (default), a halt aborts the whole run (back-compat).
    n1 = {"campaign": "cantina", "node": "1-A", "sim": "max"}
    n2 = {"kind": "collect", "nav": [], "claim": "login_claim"}
    present = {"home", "campaigns_entry", "campaigns_menu", "campaign_cantina", "node_cantina_1-A",
               "login_claim", "rewards", "home_button"}
    task = EnergyDumpTask([n1, n2], scripted_look(present), lambda x, y: None)
    s = task.run()
    assert s.halted is True
    assert s.halt_state == "OPEN_MULTISIM"
    assert s.collected == 0               # aborted before entry 2


# --- hub panning (recenter + end-stop pan) -------------------------------------------------

HUB = {"home", "home_button", "hub_anchor", "hub_anchor_open"}


def test_recenter_bounces_through_the_anchor_submenu():
    """`recenter` must open a harmless submenu and come back — that is what restores the
    default pan (the home button alone is a no-op while the hub is already showing)."""
    node = {"kind": "collect", "name": "x", "recenter": True, "claim": "c"}
    taps = []
    task = EnergyDumpTask([node], scripted_look(HUB | {"c", "rewards"}),
                          lambda x, y: taps.append((x, y)))
    s = task.run()
    labels = [st.label for st in task._steps_for(node)]
    assert labels[:3] == ["HOME", "HUB_ANCHOR", "HUB_RECENTER"]
    assert s.recentered == 1
    assert s.halted is False


def test_no_recenter_by_default():
    """An entry that doesn't ask for it pays no recenter cost — the hub is already default-panned
    unless something swiped it."""
    task = EnergyDumpTask([NODE], scripted_look(FLOW), lambda x, y: None)
    assert [st.label for st in task._steps_for(NODE)][:2] == ["HOME", "OPEN_CAMPAIGNS"]


def test_pan_swipes_toward_the_end_stop_without_tapping():
    node = {"kind": "collect", "name": "ev", "pan": "far_right", "pan_swipes": 3, "claim": "c"}
    swipes, taps = [], []
    task = EnergyDumpTask([node], scripted_look(HUB | {"c", "rewards"}),
                          lambda x, y: taps.append((x, y)), swipe=swipes.append)
    task.run()
    # far_right = reveal the right end of the panorama = drag content left
    assert swipes == ["left", "left", "left"]


def test_pan_far_left_drags_content_right():
    node = {"kind": "collect", "name": "raids", "pan": "far_left", "pan_swipes": 2, "claim": "c"}
    swipes = []
    task = EnergyDumpTask([node], scripted_look(HUB | {"c", "rewards"}),
                          lambda x, y: None, swipe=swipes.append)
    task.run()
    assert swipes == ["right", "right"]


def test_pan_implies_recenter():
    """Panning to an end stop is only reproducible if we start from a known pan."""
    node = {"kind": "collect", "name": "ev", "pan": "far_right", "claim": "c"}
    task = EnergyDumpTask([node], scripted_look(HUB), lambda x, y: None)
    labels = [st.label for st in task._steps_for(node)]
    assert "HUB_ANCHOR" in labels
    assert labels.index("HUB_ANCHOR") < labels.index("PAN_FAR_RIGHT")


def test_unknown_pan_target_is_rejected():
    task = EnergyDumpTask([], scripted_look(set()), lambda x, y: None)
    with pytest.raises(ValueError, match="unknown pan target"):
        task._steps_for({"kind": "collect", "pan": "sideways", "claim": "c"})


# --- shop kind (token spends, crystals vetoed) ---------------------------------------------

SHOP = {"kind": "shop", "name": "cantina_shop", "nav": ["shipments_entry", "shop_tab_cantina"],
        "buys": [{"item": "buy_ability_mat_mk3"}]}
SHOP_FLOW = {"home", "home_button", "shipments_entry", "shop_tab_cantina",
             "buy_ability_mat_mk3", "shop_confirm_cantina", "rewards"}


def test_shop_buys_a_token_priced_item():
    taps = []
    task = EnergyDumpTask([SHOP], scripted_look(SHOP_FLOW), lambda x, y: taps.append((x, y)))
    s = task.run()
    assert s.bought == 1
    assert s.blocked_spends == 0
    assert s.halted is False


def test_shop_cannot_confirm_a_crystal_priced_dialog():
    """The structural guard: the confirm template carries the TOKEN coin, so a crystal-priced
    dialog (a different coin, hence no match) can never be confirmed. It skips, it never buys."""
    look = scripted_look(SHOP_FLOW - {"shop_confirm_cantina"})
    s = EnergyDumpTask([SHOP], look, lambda x, y: None).run()
    assert s.bought == 0
    assert s.halted is False


def test_shop_forbid_veto_cancels_instead_of_confirming():
    """The optional second guard: an entry may name a veto template; seeing it must back out via
    CANCEL rather than confirm."""
    node = dict(SHOP, forbid="crystal_price")
    look = scripted_look(SHOP_FLOW | {"crystal_price", "shop_cancel"})
    s = EnergyDumpTask([node], look, lambda x, y: None).run()
    assert s.bought == 0
    assert s.blocked_spends == 1
    assert s.halted is False


def test_shop_skips_an_item_that_is_not_in_stock():
    """Shop stock rotates; a missing item is a normal no-op, not a halt."""
    look = scripted_look(SHOP_FLOW - {"buy_ability_mat_mk3", "shop_confirm_cantina"})
    task = EnergyDumpTask([SHOP], look, lambda x, y: None)
    s = task.run()
    assert s.bought == 0
    assert s.blocked_spends == 0
    assert s.halted is False


def test_shop_count_repeats_the_buy():
    node = dict(SHOP, buys=[{"item": "buy_ability_mat_mk3", "count": 3}])
    task = EnergyDumpTask([node], scripted_look(SHOP_FLOW), lambda x, y: None)
    assert task.run().bought == 3


def test_shop_has_no_template_for_the_refresh_bar():
    """Every shop tab carries a permanent 'REFRESH 💎50' bar. Nothing in the generated steps may
    reference it — the only tap targets are the item, its confirm, and the standard chrome."""
    task = EnergyDumpTask([SHOP], scripted_look(SHOP_FLOW), lambda x, y: None)
    templates = {st.template for st in task._steps_for(SHOP)}
    assert not any("refresh" in t for t in templates)
    assert templates <= SHOP_FLOW


# --- sequence kind (Galactic War and friends: a fixed button order, no battle) ---------------

GW = {"kind": "sequence", "name": "galactic_war",
      "nav": [{"template": "quests_entry"}, {"template": "quest_gw_row", "offset": [646, 14]}],
      "taps": [{"template": "gw_restart"}, {"template": "gw_multisim"},
               {"template": "gw_sim_confirm", "mark": "challenges_simmed"},
               {"template": "rewards"}, {"template": "gw_redeem"}]}
GW_FLOW = {"home", "home_button", "quests_entry", "quest_gw_row", "gw_restart", "gw_multisim",
           "gw_sim_confirm", "rewards", "gw_redeem"}


def test_sequence_presses_every_button_in_order():
    taps = []
    s = EnergyDumpTask([GW], scripted_look(GW_FLOW), lambda x, y: taps.append((x, y))).run()
    assert s.halted is False
    assert s.challenges_simmed == 1
    assert len(taps) == 8       # 2 nav + 5 sequence + home


def test_sequence_nav_offset_is_applied():
    """The GW quest row is matched on its text but the GO button sits to its right."""
    taps = []
    EnergyDumpTask([GW], scripted_look(GW_FLOW), lambda x, y: taps.append((x, y))).run()
    assert (10 + 646, 20 + 14) in taps


def test_sequence_is_idempotent_when_already_done_today():
    """GW's RESTART and MULTI SIM grey out once the war is simmed. Optional taps mean a second run
    that day is a no-op rather than a halt."""
    halts = []
    look = scripted_look(GW_FLOW - {"gw_restart", "gw_multisim", "gw_sim_confirm"})
    s = EnergyDumpTask([GW], look, lambda x, y: None, halt=halts.append).run()
    assert s.halted is False
    assert halts == []
    assert s.challenges_simmed == 0


def test_sequence_required_tap_still_halts():
    node = dict(GW, taps=[{"template": "gw_restart", "required": True}])
    halts = []
    s = EnergyDumpTask([node], scripted_look(GW_FLOW - {"gw_restart"}), lambda x, y: None,
                       halt=halts.append).run()
    assert s.halted is True
    assert halts and halts[0].startswith("STEP_0")


def test_battle_accepts_an_alternative_victory_screen():
    """Coliseum shows a 'NEW HIGH SCORE' banner instead of the normal VICTORY screen when the run
    beats the banked score. That is still a win, so it must book battles_won, not halt."""
    node = {"kind": "battle", "nav": ["coliseum_tile"], "start": "battle_start",
            "victory_alt": ["coliseum_highscore"]}
    present = {"home", "coliseum_tile", "battle_start", "battle_auto",
               "coliseum_highscore", "rewards", "home_button"}      # note: no "victory"
    halts = []
    s = EnergyDumpTask([node], scripted_look(present), lambda x, y: None,
                       halt=halts.append).run()
    assert s.battles_won == 1
    assert s.battles_lost == 0
    assert s.halted is False
    assert halts == []


def test_high_score_banner_is_a_popup_closer():
    """Left up, it covers the hub and every later entry fails its HOME check — which is exactly the
    cascade seen live on 2026-08-03 (one battle halt turned into three)."""
    from farmbot.tasks import DEFAULT_POPUP_CLOSERS
    assert "coliseum_highscore" in DEFAULT_POPUP_CLOSERS


def test_chapter_tab_is_optional_because_the_game_remembers_the_chapter():
    """A tab template is captured unselected, so once the bot has visited that chapter the tab
    renders selected and stops matching. Requiring it made DS ch8 halt on every run after the
    first."""
    node = {"campaign": "dark", "difficulty": "hard", "chapter": 8, "node": "8-B", "sim": "max"}
    present = {"home", "campaigns_entry", "campaigns_menu", "campaign_dark", "hard_tab",
               "node_dark_8-B", "multi_sim", "sim_confirm", "rewards", "home_button"}
    halts = []
    s = EnergyDumpTask([node], scripted_look(present), lambda x, y: None,
                       halt=halts.append).run()          # note: no chapter_tab_8 in `present`
    assert s.halted is False
    assert halts == []
    assert s.sims_done == 1
    assert s.chapter_already_set == 1


def test_a_celebration_modal_does_not_strand_the_run():
    """Star-up celebrations are full-screen with no home button. Seen live: a bronzium starred up a
    character, RETURN_HOME found nothing, and the next three entries all failed their HOME check."""
    from farmbot.tasks import DEFAULT_POPUP_CLOSERS
    assert "celebration_continue" in DEFAULT_POPUP_CLOSERS

    node = {"kind": "collect", "name": "c", "nav": [], "claim": "claim"}
    # home_button only becomes reachable once the celebration is dismissed
    seen = {"dismissed": False}

    def look(name, timeout):
        if name == "celebration_continue" and not seen["dismissed"]:
            return M(10, 20, 0.99)
        if name == "home_button" and not seen["dismissed"]:
            return None
        return M(10, 20, 0.99) if name in {"home", "home_button", "claim"} else None

    def tap(x, y):
        seen["dismissed"] = True

    s = EnergyDumpTask([node], look, tap).run()
    assert s.halted is False


def test_node_selected_state_is_an_accepted_alternative():
    """The map keeps the last-played node selected, so a second visit shows the glowing icon that
    the unselected crop cannot match. Live: DS 8-B halted with its panel already open."""
    node = {"campaign": "dark", "difficulty": "hard", "chapter": 8, "node": "8-B", "sim": "max"}
    present = {"home", "campaigns_entry", "campaigns_menu", "campaign_dark", "hard_tab",
               "node_dark_8-B_sel",          # selected variant only
               "multi_sim", "sim_confirm", "rewards", "home_button"}
    halts = []
    s = EnergyDumpTask([node], scripted_look(present), lambda x, y: None,
                       halt=halts.append).run()
    assert halts == []
    assert s.sims_done == 1


# --- nav that has to scroll to reach its target ----------------------------------------------


def test_a_nav_hop_can_scroll_to_find_a_row_below_the_fold():
    """The Quests list REORDERS as quests complete: claimable rows sort to the top and push the
    Galactic War row off-screen, so its template matched nothing and the entry halted at NAV_1.
    A nav hop can name its own scan directions — a list scrolls vertically, while the engine's
    default scan is horizontal because it was built for the campaign map."""
    node = {"kind": "sequence", "name": "gw",
            "nav": ["quests_entry",
                    {"template": "quest_gw_row", "offset": [646, 14], "scroll": ["up", "up"]}],
            "taps": [{"template": "gw_multisim"}]}
    look = scripted_look({"home", "home_button", "quests_entry", "gw_multisim"},
                         sequences={"quest_gw_row": [False, True]})
    swipes, halts, taps = [], [], []
    s = EnergyDumpTask([node], look, lambda x, y: taps.append((x, y)),
                       swipe=swipes.append, halt=halts.append).run()
    assert halts == []
    assert s.halted is False
    assert swipes == ["up"]                  # found after one vertical drag
    assert (10 + 646, 20 + 14) in taps       # and the GO-button offset still applies


def test_a_nav_hop_without_scroll_does_not_swipe():
    """Scrolling stays opt-in per hop: a scan leaves the hub panorama dirty for every entry after
    it, so a missing hub console must halt rather than swipe."""
    node = {"kind": "sequence", "name": "gw", "nav": ["quests_entry"], "taps": []}
    swipes, halts = [], []
    s = EnergyDumpTask([node], scripted_look({"home", "home_button"}), lambda x, y: None,
                       swipe=swipes.append, halt=halts.append).run()
    assert swipes == []
    assert halts == ["NAV_0"]
    assert s.halted is True


# --- Coliseum's other non-standard result screen ---------------------------------------------


def test_a_tier_clear_banner_is_read_as_a_win_not_a_halt():
    """Clearing a Coliseum tier shows 'TIER COMPLETE / NEW TIER UNLOCKED n' in place of the normal
    victory screen, so the OUTCOME step timed out and halted."""
    node = {"kind": "battle", "nav": ["coliseum_tile"], "start": "battle_start",
            "victory_alt": ["coliseum_highscore", "tier_complete"]}
    present = {"home", "coliseum_tile", "battle_start", "battle_auto",
               "tier_complete", "rewards", "home_button"}   # neither victory nor highscore
    halts = []
    s = EnergyDumpTask([node], scripted_look(present), lambda x, y: None, halt=halts.append).run()
    assert s.battles_won == 1
    assert s.halted is False
    assert halts == []


def test_tier_complete_is_a_popup_closer():
    """Same failure class as the high-score banner: left up it covers the hub and every later
    entry fails its HOME check."""
    from farmbot.tasks import DEFAULT_POPUP_CLOSERS
    assert "tier_complete" in DEFAULT_POPUP_CLOSERS


# --- starting a run that isn't at the hub ----------------------------------------------------


def test_a_run_that_starts_inside_a_menu_recovers_to_the_hub():
    """A run that halted leaves the game deep in a menu, and the next run then halted on its very
    first HOME check before collecting anything (twice in one evening)."""
    look = scripted_look(FLOW, sequences={"home": [False, True]})
    taps, halts = [], []
    s = EnergyDumpTask([NODE], look, lambda x, y: taps.append((x, y)), halt=halts.append).run()
    assert halts == []
    assert s.halted is False
    assert s.sims_done == 1
    assert len(taps) == 8       # the recovery home-button tap + the 7 happy-path taps


def test_hub_recovery_runs_once_per_run_not_once_per_entry():
    """It is a start-of-run repair. An entry that cannot find HOME mid-routine is a genuine
    failure and must still halt with a screenshot."""
    looks = []
    inner = scripted_look(FLOW)

    def look(name, timeout):
        looks.append(name)
        return inner(name, timeout)

    EnergyDumpTask([NODE, NODE], look, lambda x, y: None).run()
    assert looks.count("home") == 3      # 1 start-of-run probe + 1 HOME verify per entry


def test_a_hub_that_is_only_covered_by_a_popup_is_not_tapped_home():
    """Dismissing the popup is enough; tapping the home button on top of that is pointless (it is
    a no-op while the hub is showing) and costs an action."""
    look = scripted_look(FLOW, sequences={"home": [False, True], "popup_close": [True, False]})
    taps = []
    s = EnergyDumpTask([NODE], look, lambda x, y: taps.append((x, y))).run()
    assert s.halted is False
    assert len(taps) == 8       # 1 popup dismiss + 7 happy-path taps, no extra home-button tap


# --- a skip state with more than one skin ----------------------------------------------------


FLEET_HARD = {"campaign": "fleet", "difficulty": "hard", "chapter": 1, "node": "1-E", "sim": "max"}


def test_a_second_depleted_skin_also_skips_instead_of_halting():
    """`hard_depleted` was cropped from Light-Side Hard's 💎25 refresh chip; Fleet Hard's reads
    💎200, so the crop missed and a depleted Fleet node halted instead of skipping."""
    present = {"home", "campaigns_entry", "campaigns_menu", "campaign_fleet", "hard_tab",
               "chapter_tab_1", "node_fleet_1-E", "rewards", "home_button",
               "hard_depleted_200"}     # the 💎200 skin only: no multi_sim, no hard_depleted
    taps, halts = [], []
    s = EnergyDumpTask([FLEET_HARD], scripted_look(present),
                       lambda x, y: taps.append((x, y)), halt=halts.append).run()
    assert halts == []
    assert s.halted is False
    assert s.hard_depleted_nodes == 1
    assert s.sims_done == 0
    assert len(taps) == 6        # same as the 💎25 skin: nav + return home, no panel tap


def test_no_depleted_skin_is_ever_tapped():
    """Both skins are crystal-priced refresh chips. The marker is read, never pressed."""
    task = EnergyDumpTask([FLEET_HARD], scripted_look(set()), lambda x, y: None)
    step = [st for st in task._steps_for(FLEET_HARD) if st.label == "OPEN_MULTISIM"][0]
    assert step.skip_tap is False
    assert "hard_depleted_200" in step.skip_marker_alt


def test_bronzium_finish_screen_cannot_trigger_a_re_buy():
    """The data-card FINISH screen puts 'BUY AGAIN 250' next to FINISH. Verified against the live
    capture: bronzium_skip matches FINISH at 1.000 and nothing matches BUY AGAIN — so promoting it
    to a popup closer cannot spend."""
    from farmbot.tasks import DEFAULT_POPUP_CLOSERS, tap_target
    names = [tap_target(c)[0] for c in DEFAULT_POPUP_CLOSERS]
    assert "bronzium_skip" in names
    assert not any("buy" in n for n in names)


# --- a popup whose marker and dismiss control are different pixels ----------------------------


def test_a_popup_closer_can_tap_at_an_offset_from_its_marker():
    """Coliseum's BATTLE RESULTS screen is recognisable by its title but dismissed by a CONTINUE
    far below it. Tapping the title does nothing, the banner stays up, and every later entry fails
    its HOME check — so a closer has to be able to name a tap offset."""
    look = scripted_look(FLOW, sequences={"home": [False, True], "banner": [True, False]})
    taps = []
    s = EnergyDumpTask([NODE], look, lambda x, y: taps.append((x, y)),
                       popup_closers=(("banner", (0, 464)),)).run()
    assert s.halted is False
    assert taps[0] == (10, 20 + 464)


def test_the_coliseum_results_continue_is_wired_as_an_offset_closer():
    """Captured on 2026-08-04 but left unwired precisely because the engine could only tap a
    closer at its match centre."""
    from farmbot.tasks import DEFAULT_POPUP_CLOSERS, tap_target
    targets = dict(tap_target(c) for c in DEFAULT_POPUP_CLOSERS)
    assert targets["coliseum_results"] == (0, 464)


def test_tap_target_normalises_a_bare_template_name():
    from farmbot.tasks import tap_target
    assert tap_target("popup_close") == ("popup_close", (0, 0))


def test_the_conquest_defeat_upsell_is_dismissed_as_an_offset_closer():
    """A lost Conquest battle stacks an upsell ("Did you know you have upgrades available?") ON TOP
    of the DEFEAT screen. Measured live 2026-08-04: `defeat` scored 0.376 against the upsell and
    0.968 once it was gone, so the outcome marker is unreachable until the upsell is cleared. Its
    only exit is the back arrow at (65,65), far from the match centre — hence an offset closer."""
    from farmbot.tasks import DEFAULT_POPUP_CLOSERS, tap_target
    targets = dict(tap_target(c) for c in DEFAULT_POPUP_CLOSERS)
    assert targets["defeat_upsell"] == (-891, -39)


# --- conquest (hub far-right -> Galactic Battles -> CONQUEST -> sector map) --------------------

# The console lives off the hub's default pan, so every conquest entry recenters and pans right.
CONQUEST = {"kind": "conquest", "name": "conquest", "pan": "far_right"}
CONQUEST_NAV = {"home", "home_button", "hub_anchor", "hub_anchor_open", "galactic_battles",
                "conquest_card", "conquest_header", "conquest_enter", "conquest_feats_panel"}
# 5 taps to reach the sector map: anchor, recenter, the console, the CONQUEST ENTER, the sector.
CONQUEST_NAV_TAPS = 5

CONQUEST_BATTLE = dict(CONQUEST, battles=[{"node": "conquest_node_1a"}])
CONQUEST_BATTLE_FLOW = CONQUEST_NAV | {"conquest_node_1a", "conquest_combat_details",
                                       "conquest_battle_btn", "conquest_squad_prompt",
                                       "battle_auto", "victory", "rewards"}


def test_conquest_navigates_from_the_hub_to_the_sector_map():
    taps = []
    s = EnergyDumpTask([CONQUEST], scripted_look(CONQUEST_NAV),
                       lambda x, y: taps.append((x, y))).run()
    assert s.halted is False
    assert len(taps) == CONQUEST_NAV_TAPS + 1        # + RETURN_HOME


def test_conquest_enter_is_tapped_below_the_conquest_title():
    """The WAR and CONQUEST ENTER buttons are pixel-identical, so an ENTER template is ambiguous
    and would launch Galactic War. The CONQUEST title is unique; its ENTER sits +704px below."""
    taps = []
    EnergyDumpTask([CONQUEST], scripted_look(CONQUEST_NAV),
                   lambda x, y: taps.append((x, y))).run()
    assert (10, 20 + 704) in taps


def test_conquest_halts_when_the_offset_tap_did_not_land_in_conquest():
    """A blind offset can miss. The sector-list header is the proof that we are in Conquest and
    not in Galactic War, and it is checked before anything else is pressed."""
    halts = []
    s = EnergyDumpTask([CONQUEST], scripted_look(CONQUEST_NAV - {"conquest_header"}),
                       lambda x, y: None, halt=halts.append).run()
    assert s.halted is True
    assert halts == ["SECTOR_LIST"]


def test_conquest_takes_the_free_disk_stockpile_in_one_tap():
    """Device-verified: tapping the green hex grants the disk immediately and auto-equips it. The
    "You obtained this Data Disk" side panel that follows is PERSISTENT and has no confirm button
    — a second tap lands on inert map space, so the pickup must be exactly one tap."""
    node = dict(CONQUEST, disks=1)
    present = CONQUEST_NAV | {"conquest_disk_stockpile", "conquest_disk_obtained"}
    taps = []
    s = EnergyDumpTask([node], scripted_look(present),
                       lambda x, y: taps.append((x, y))).run()
    assert s.halted is False
    assert s.collected == 1
    assert len(taps) == CONQUEST_NAV_TAPS + 1 + 1    # + the hex, then RETURN_HOME


def test_the_disk_is_only_booked_once_the_panel_confirms_it():
    """The panel reads "You obtained this Data Disk" the instant the hex is tapped, so it is real
    evidence. Booking on the tap alone would count hexes pressed, not disks taken."""
    node = dict(CONQUEST, disks=1)
    present = CONQUEST_NAV | {"conquest_disk_stockpile"}      # hex tapped, panel never confirms
    halts = []
    s = EnergyDumpTask([node], scripted_look(present), lambda x, y: None,
                       halt=halts.append).run()
    assert s.collected == 0
    assert s.halted is False
    assert halts == []


def test_conquest_disk_already_taken_is_not_a_halt():
    node = dict(CONQUEST, disks=1)
    halts = []
    s = EnergyDumpTask([node], scripted_look(CONQUEST_NAV), lambda x, y: None,
                       halt=halts.append).run()
    assert halts == []
    assert s.collected == 0


def test_the_disk_step_never_retaps_to_force_its_panel():
    """The panel is persistent, not a modal: it does not dismiss on an outside tap and tapping
    another node simply replaces it. Reading it once is fine; re-tapping to force a state change
    would just re-open the same hex forever, and waiting for it to close would hang."""
    task = EnergyDumpTask([], scripted_look(set()), lambda x, y: None)
    disk_steps = [st for st in task._steps_for(dict(CONQUEST, disks=2))
                  if st.label.startswith("DISK")]
    assert len(disk_steps) == 2                       # one step per disk, not a tap + a dismiss
    assert all(st.ensure_retries == 0 for st in disk_steps)


def test_conquest_battle_needs_two_taps_of_the_same_battle_button():
    """`conquest_battle_btn` matches the Combat Details BATTLE ⚡20 AND the squad-select BATTLE.
    A single start step taps the first and strands the run on squad select — the exact bug
    already recorded for Coliseum."""
    taps = []
    s = EnergyDumpTask([CONQUEST_BATTLE], scripted_look(CONQUEST_BATTLE_FLOW),
                       lambda x, y: taps.append((x, y))).run()
    assert s.halted is False
    assert s.battles_won == 1
    # node, BATTLE, BATTLE, AUTO, victory, rewards
    assert len(taps) == CONQUEST_NAV_TAPS + 6 + 1


def test_conquest_start_does_not_retap_when_the_squad_screen_never_appears():
    """If the run was already on squad select, the first BATTLE tap starts the fight. Re-tapping
    to force the squad prompt to appear would land taps inside a live battle."""
    look = scripted_look(CONQUEST_BATTLE_FLOW - {"conquest_squad_prompt"},
                         sequences={"conquest_battle_btn": [True, False]})
    taps, halts = [], []
    s = EnergyDumpTask([CONQUEST_BATTLE], look, lambda x, y: taps.append((x, y)),
                       halt=halts.append).run()
    assert halts == []
    assert s.battles_won == 1
    # ONE battle tap, then node, AUTO, victory, rewards
    assert len(taps) == CONQUEST_NAV_TAPS + 5 + 1


def test_conquest_unreadable_post_battle_screen_halts_instead_of_guessing():
    """Conquest's defeat/retry flow offers crystal-priced Stim Packs and has never been captured.
    Anything the engine cannot read after a battle stops for a human with a screenshot; it never
    taps something plausible."""
    node = dict(CONQUEST_BATTLE, battle_timeout_s=0.01)
    halts = []
    s = EnergyDumpTask([node], scripted_look(CONQUEST_BATTLE_FLOW - {"victory"}),
                       lambda x, y: None, halt=halts.append).run()
    assert s.halted is True
    assert halts == ["OUTCOME_0"]


def test_conquest_never_taps_its_way_past_a_post_battle_screen():
    """The generic battle kind carries `skip_marker=defeat, skip_tap=True`. Conquest must not.

    The original reason was that the defeat/retry flow was uncaptured. The measured reason is
    stronger: `defeat` crops a SEMI-TRANSPARENT banner, so the battle background bleeds through it.
    On a real Conquest loss (2026-08-04) it scored 0.376 under the upsell stacked on top, and still
    only 0.762 — below the 0.85 threshold — once that was cleared, against 0.968 over a dark scene
    in an earlier session. A skip_marker built on it would have MISSED that loss and waited out the
    full battle timeout anyway. `defeat_upsell` (1.000, already a popup closer) is the signal that
    actually works, so the loss path stays a halt-with-screenshot until `defeat` is re-captured.
    """
    task = EnergyDumpTask([], scripted_look(set()), lambda x, y: None)
    steps = task._steps_for(CONQUEST_BATTLE)
    assert all(st.skip_tap is False for st in steps)
    outcome = [st for st in steps if st.label == "OUTCOME_0"][0]
    assert outcome.optional is False        # an unreadable outcome halts, it never skips on
    assert outcome.skip_marker is None      # and there is no "tap this to move past it"


def test_conquest_auto_is_skipped_when_it_is_already_on():
    """`battle_auto` was cropped in its OFF state and drops to 0.59 once AUTO is active, so it
    stops matching. That must skip: matching an ON variant and tapping it would switch AUTO OFF."""
    halts = []
    s = EnergyDumpTask([CONQUEST_BATTLE], scripted_look(CONQUEST_BATTLE_FLOW - {"battle_auto"}),
                       lambda x, y: None, halt=halts.append).run()
    assert halts == []
    assert s.battles_won == 1


def test_conquest_caps_the_battles_per_run():
    """Energy is a non-constraint here (15,649 banked ≈ 780 nodes at ⚡20). STAMINA is the budget:
    -10% per battle per character, +1% per 30 min."""
    node = dict(CONQUEST, max_battles=2,
                battles=[{"node": f"conquest_node_{i}"} for i in range(5)])
    task = EnergyDumpTask([], scripted_look(set()), lambda x, y: None)
    outcomes = [st.label for st in task._steps_for(node) if st.label.startswith("OUTCOME")]
    assert outcomes == ["OUTCOME_0", "OUTCOME_1"]


def test_conquest_has_a_conservative_default_battle_cap():
    from farmbot.tasks import DEFAULT_CONQUEST_MAX_BATTLES
    assert DEFAULT_CONQUEST_MAX_BATTLES <= 2
    node = dict(CONQUEST, battles=[{"node": f"conquest_node_{i}"} for i in range(9)])
    task = EnergyDumpTask([], scripted_look(set()), lambda x, y: None)
    outcomes = [st.label for st in task._steps_for(node) if st.label.startswith("OUTCOME")]
    assert len(outcomes) == DEFAULT_CONQUEST_MAX_BATTLES


def test_conquest_reuses_the_standard_reward_chain():
    """Verified live: the Conquest REWARDS screen matched `rewards` 0.996, `victory` 0.995 and
    `celebration_continue` 0.992, so there is no conquest-specific reward template to add."""
    task = EnergyDumpTask([], scripted_look(set()), lambda x, y: None)
    templates = {st.template for st in task._steps_for(CONQUEST_BATTLE)}
    assert {"victory", "rewards"} <= templates
    assert not any(t.startswith("conquest_") and ("reward" in t or "victory" in t)
                   for t in templates)


def test_a_battle_spec_can_name_the_gold_challenge_path_node():
    """The amber Challenge Path node needs NO engine change — a spec names its own template.

    Measured live 2026-08-04: `conquest_node_gold` scored 0.990 on the reachable Challenge node
    with its next peaks at 0.696/0.652 (the dim, unreachable amber ones) — the same clean
    either-side-of-0.85 split that makes `conquest_node_open` safe. Kept OUT of the default config
    on purpose: gold nodes are harder and the matcher picks blindly, so aiming at one is a
    deliberate act on a rested squad.
    """
    node = dict(CONQUEST, battles=[{"node": "conquest_node_gold"}])
    flow = (CONQUEST_BATTLE_FLOW - {"conquest_node_1a"}) | {"conquest_node_gold"}
    task = EnergyDumpTask([], scripted_look(set()), lambda x, y: None)
    assert [st.template for st in task._steps_for(node) if st.label == "NODE_0"] \
        == ["conquest_node_gold"]
    s = EnergyDumpTask([node], scripted_look(flow), lambda x, y: None).run()
    assert s.halted is False
    assert s.battles_won == 1


def test_the_conquest_disk_step_cannot_cost_anything_while_it_stays_dead():
    """`conquest_disk_stockpile` is the stockpile PANEL's title, not the map hex, so the step can
    never fire (0.000 against a live map showing two stockpiles; 1.000 once the panel was opened by
    hand). That is a missing capability, not a hazard — but only because the step is `optional`
    with no `skip_entry`, so it skips silently instead of halting or cancelling the fights queued
    behind it. Pin that, so a future fix cannot quietly make a dead step into a blocking one."""
    node = dict(CONQUEST, disks=2, battles=[{"node": "conquest_node_1a"}])
    task = EnergyDumpTask([], scripted_look(set()), lambda x, y: None)
    disks = [st for st in task._steps_for(node) if st.label.startswith("DISK_")]
    assert len(disks) == 2
    assert all(st.optional and not st.skip_entry and not st.skip_tap for st in disks)
    # The whole entry still completes with the stockpile panel absent, which is every real run.
    s = EnergyDumpTask([node], scripted_look(CONQUEST_BATTLE_FLOW), lambda x, y: None).run()
    assert s.halted is False
    assert s.collected == 0 and s.battles_won == 1


def test_running_out_of_disks_does_not_cancel_the_battles_behind_them():
    """Free disks are taken first because they cost nothing, but an empty stockpile must not end
    the entry — the node fights queued behind them are the point of the run."""
    node = dict(CONQUEST, disks=2, battles=[{"node": "conquest_node_1a"}])
    look = scripted_look(CONQUEST_BATTLE_FLOW | {"conquest_disk_obtained"},
                         sequences={"conquest_disk_stockpile": [True, False]})
    s = EnergyDumpTask([node], look, lambda x, y: None).run()
    assert s.collected == 1
    assert s.battles_won == 1


def test_a_battle_spec_can_repeat_the_same_node_template():
    """`conquest_node_open` matches EVERY un-cleared node and the engine takes the single best
    match, so 'fight n of them' is one spec with a count, not n copies of a dict. Clearing a node
    dims it below the match threshold, which is what makes the next call pick a different one."""
    node = dict(CONQUEST, max_battles=3,
                battles=[{"node": "conquest_node_open", "count": 3}])
    task = EnergyDumpTask([], scripted_look(set()), lambda x, y: None)
    outcomes = [st.label for st in task._steps_for(node) if st.label.startswith("OUTCOME")]
    assert outcomes == ["OUTCOME_0", "OUTCOME_1", "OUTCOME_2"]


def test_the_battle_cap_applies_after_counts_are_expanded():
    """Otherwise a `count` sails straight past the stamina cap that is the whole point of it."""
    node = dict(CONQUEST, max_battles=2,
                battles=[{"node": "conquest_node_open", "count": 9}])
    task = EnergyDumpTask([], scripted_look(set()), lambda x, y: None)
    outcomes = [st.label for st in task._steps_for(node) if st.label.startswith("OUTCOME")]
    assert outcomes == ["OUTCOME_0", "OUTCOME_1"]


def test_a_counted_battle_spec_fights_each_node_in_turn():
    node = dict(CONQUEST, max_battles=2,
                battles=[{"node": "conquest_node_open", "count": 2}])
    present = (CONQUEST_BATTLE_FLOW - {"conquest_node_1a"}) | {"conquest_node_open"}
    s = EnergyDumpTask([node], scripted_look(present), lambda x, y: None).run()
    assert s.halted is False
    assert s.battles_won == 2


# --- Coliseum: two taps per attempt, and the 💎250 refresh that replaces them -------------------


def positional_look(present):
    """Like `scripted_look`, but every template matches at ITS OWN coordinates.

    That is what lets a test prove WHICH control was pressed rather than just how many presses
    happened — the difference between "two taps occurred" and "the crystal refresh was not one
    of them". Returns (look, coords)."""
    coords = {name: (100 + 7 * i, 200 + 11 * i) for i, name in enumerate(sorted(present))}

    def look(name, timeout):
        return M(*coords[name], 0.99) if name in present else None

    return look, coords


COLISEUM = {"kind": "battle", "name": "coliseum", "nav": ["coliseum_tile"],
            "start": "battle_start", "attempts": 2,
            "victory_alt": ["coliseum_highscore", "attempt_over", "tier_complete"]}
COLISEUM_FLOW = {"home", "home_button", "coliseum_tile", "battle_start", "battle_auto",
                 "victory", "rewards"}


def test_coliseum_each_attempt_takes_two_taps():
    """The Coliseum screen's `BATTLE (n)` and the squad-select `BATTLE` are the SAME template.
    Only attempt 1 ever worked, because the config smuggled its first tap into `nav`; every later
    attempt tapped once and stranded on squad select. Attempts are 5/day against a payout that
    resets daily, so each stranded attempt is value that cannot be recovered."""
    taps = []
    s = EnergyDumpTask([COLISEUM], scripted_look(COLISEUM_FLOW),
                       lambda x, y: taps.append((x, y))).run()
    assert s.halted is False
    assert s.battles_won == 2
    # per attempt: BATTLE, BATTLE, AUTO, victory, rewards = 5; plus the tile and RETURN_HOME
    assert len(taps) == 2 * 5 + 2


def test_coliseum_second_tap_is_skipped_when_the_fight_already_started():
    """Same guard as Conquest: if the first tap went straight into the battle there is no second
    BATTLE to press, and the engine must not go looking for one to tap."""
    look = scripted_look(COLISEUM_FLOW, sequences={"battle_start": [True, False]})
    taps, halts = [], []
    s = EnergyDumpTask([dict(COLISEUM, attempts=1)], look,
                       lambda x, y: taps.append((x, y)), halt=halts.append).run()
    assert halts == []
    assert s.battles_won == 1
    assert len(taps) == 1 + 4 + 1        # tile, ONE battle tap, AUTO, victory, rewards, home


def test_coliseum_exhausted_attempts_never_taps_the_crystal_refresh():
    """When the day's attempts are spent the BATTLE button is REPLACED by a 💎250 refresh sitting
    in the same place. `battle_start` is cropped on the green BATTLE, so it cannot match it — and
    nothing else may fall through to that coordinate either."""
    look, coords = positional_look({"home", "home_button", "coliseum_tile", "coliseum_refresh"})
    taps, halts = [], []
    s = EnergyDumpTask([dict(COLISEUM, attempts=5)], look,
                       lambda x, y: taps.append((x, y)), halt=halts.append).run()
    assert halts == []
    assert s.halted is False
    assert s.battles_won == 0
    assert s.battles_unavailable == 1
    assert coords["coliseum_refresh"] not in taps
    # and positively: the only things pressed were the tile and the recovery home button
    assert set(taps) == {coords["coliseum_tile"], coords["home_button"]}


def test_no_battle_step_can_name_a_refresh_or_crystal_control():
    """Structural companion to the behavioural test: there is no template in the generated steps
    that could match a crystal-priced control, so none can be pressed by accident."""
    task = EnergyDumpTask([], scripted_look(set()), lambda x, y: None)
    templates = {st.template for st in task._steps_for(COLISEUM)}
    templates |= {st.skip_marker for st in task._steps_for(COLISEUM) if st.skip_marker}
    assert not any(bad in t for t in templates
                   for bad in ("refresh", "crystal", "gem", "purchase", "buy"))
