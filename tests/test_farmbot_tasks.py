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


def test_mod_chapter_halts_if_only_generic_tab_present():
    # Proves the scoping is real: with ONLY the generic chapter_tab_2 (no scoped one), mod halts.
    node = {"campaign": "mod", "chapter": 2, "node": "2-F", "sim": "max"}
    present = {"home", "campaigns_entry", "campaigns_menu", "campaign_mod", "chapter_tab_2",
               "node_mod_2-F", "multi_sim", "sim_confirm", "rewards", "home_button"}
    halts = []
    task = EnergyDumpTask([node], scripted_look(present), lambda x, y: None,
                          halt=lambda st: halts.append(st))
    s = task.run()
    assert s.halted is True
    assert s.halt_state == "SELECT_CHAPTER"


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


def test_unknown_kind_raises():
    task = EnergyDumpTask([{"kind": "bogus"}], scripted_look(set()), lambda x, y: None)
    with pytest.raises(ValueError):
        task.run()


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


def test_challenge_sim_happy_path_disjoint_from_sims_done():
    node = {"kind": "challenge_sim", "challenge": "challenge_ability_mats"}
    present = {"home", "challenges_entry", "challenges_menu", "challenge_ability_mats",
              "multi_sim", "sim_confirm", "rewards", "home_button"}
    taps = []
    task = EnergyDumpTask([node], scripted_look(present), lambda x, y: taps.append((x, y)))
    s = task.run()
    assert s.halted is False
    assert s.challenges_simmed == 1
    assert s.sims_done == 0            # disjoint from energy sims
    assert len(taps) == 6             # open, select, multisim, confirm, rewards, home


def test_challenge_not_three_starred_skips_without_battle():
    node = {"kind": "challenge_sim", "challenge": "challenge_ability_mats"}
    present = {"home", "challenges_entry", "challenges_menu", "challenge_ability_mats",
              "challenge_locked", "home_button"}          # no multi_sim/sim_confirm
    taps, halts = [], []
    task = EnergyDumpTask([node], scripted_look(present),
                          lambda x, y: taps.append((x, y)), halt=lambda st: halts.append(st))
    s = task.run()
    assert s.halted is False
    assert halts == []
    assert s.skipped_nodes == 1
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
    assert len(taps) == 6        # tile, start, auto, victory, rewards, home


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
