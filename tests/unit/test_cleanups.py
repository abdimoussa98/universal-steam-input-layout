"""The Cleanup audit: what a cleanup function and a release may remove.

Tiny layouts, one rule per test, then the frozen 90.10 snapshots. The rules are in
findings/2026-10-02-cleanup-boundaries/README.md; the plan is plans/2026-10-02-cleanup-audit.md.

Fixture responsibility: unit. See docs/testing.md and tests/test-map.csv.
"""
from tests.support.fixtures.cleanups import *

class ReadingTests(unittest.TestCase):
    def test_a_cleanup_function_has_a_guard_and_a_list(self):
        c = Cleanups(Layout(owner()))
        (_, guard, removed), = c.cleanups("P")
        self.assertEqual((guard, removed), (frozenset({"LB"}), frozenset({"P", "C"})))

    def test_the_keeper_is_the_button_whose_release_removes_the_layer(self):
        c = Cleanups(Layout(owner()))
        self.assertEqual(c.keeper("P"), ("button", frozenset({"LB"})))
        self.assertEqual(c.keeper("C"), ("button", frozenset({"LB"})))

    def test_a_window_is_kept_by_its_timer(self):
        data = owner(extra={"W": {"switch": (SW, {"always_on_action": press(remove("W"), delay_start=150)})}})
        self.assertEqual(Cleanups(Layout(data)).keeper("W")[0], "timer")

    def test_a_layer_that_outlives_its_adder_and_has_no_release_is_stateful(self):
        data = owner(base={"button_y": press(add("T"))}, extra={
            "T": {"switch": (SW, {"button_y": release(remove("T"), add("Mode"))})}, "Mode": {}})
        c = Cleanups(Layout(data))
        self.assertEqual(c.keeper("Mode")[0], "mode")
        self.assertEqual(c.keeper("P")[0], "button")

    def test_the_stacks_are_the_backward_chains(self):
        layout = Layout(owner())
        chains = Chains.of(layout)
        expected = set().union(*chains.below("P")) | set(chains.above("P")) | {"P"}
        self.assertEqual(Cleanups(layout).present("P"), expected - {"Base"})

    def test_a_persistent_mode_can_restore_another_mode_without_removing_itself(self):
        data = owner(base={"button_y": press(add("T"))}, extra={
            'T': {'switch': (SW, {'button_y': release(remove('T'), add('Mode'))})},
            'Mode': {'switch': (SW, {'button_a': press(add('Fallback'), remove('Mode'))})},
            'Fallback': {'switch': (SW, {'button_b': press(add('Mode'))})}})
        c = Cleanups(Layout(data))
        self.assertEqual(c.stateful, {'Mode', 'Fallback'})

    def test_an_additive_cycle_without_a_persistent_entry_does_not_create_modes(self):
        data = owner(extra={'A': {'switch': (SW, {'button_a': press(add('B'))})},
                            'B': {'switch': (SW, {'button_b': press(add('A'))})}})
        self.assertFalse({'A', 'B'} & Cleanups(Layout(data)).stateful)

    def test_an_unreachable_additive_source_does_not_change_a_live_modes_keeper(self):
        data = owner(base={"button_y": press(add("T"))}, extra={
            'T': {'switch': (SW, {'button_y': release(remove('T'), add('Mode'))})},
            'Mode': {},
            'Dormant': {'switch': (SW, {'button_b': press(add('Mode'))})}})
        c = Cleanups(Layout(data))
        self.assertFalse(c.reached('Dormant'))
        self.assertEqual(c.keeper('Mode'), ('mode', frozenset()))
        self.assertNotIn('Dormant', c.stateful)
        self.assertEqual(c.adders['Mode'], {'T', 'Dormant'})  # raw inventory is preserved

    def test_a_reachable_additive_source_still_prevents_stateful_classification(self):
        data = owner(base={"button_y": press(add("T")), "button_x": press(add("Held"))}, extra={
            'T': {'switch': (SW, {'button_y': release(remove('T'), add('Mode'))})},
            'Mode': {},
            'Held': {'switch': (SW, {'button_b': press(add('Mode')),
                                      'button_x': release(remove('Held'))})}})
        c = Cleanups(Layout(data))
        self.assertTrue(c.reached('Held'))
        self.assertNotIn('Mode', c.stateful)


class ScopeTests(unittest.TestCase):
    def test_a_clean_layout_has_no_findings(self):
        report = audit(owner(), {})
        self.assertEqual(finding_pairs(report), set())
        self.assertTrue(report["ok"])

    def test_a_cover_the_owner_added_and_left_is_left_above(self):
        data = owner({"button_a": guarded(remove("P"))})
        self.assertEqual(found(data), {("left above", "P", "C")})

    def test_a_layer_above_that_binds_the_input_with_its_own_cleanup_is_not_the_owners(self):
        cover = {"left_bumper": release(remove("P"), remove("C")), "button_a": guarded(remove("C"), remove("P"))}
        data = owner({"button_a": guarded(remove("P"))}, cover=cover)
        self.assertEqual(found(data), set())

    def test_a_cleanup_that_leaves_the_layer_below_is_left_below(self):
        cover = {"left_bumper": release(remove("P"), remove("C")), "button_a": guarded(remove("C"))}
        self.assertEqual(found(owner(cover=cover)), {("left below", "C", "P")})

    def test_a_layer_another_button_keeps_is_outside_the_guard(self):
        data = owner({"button_a": guarded(remove("P"), remove("C"), remove("R"))},
                     base={"right_bumper": press(add("R"))},
                     extra={"R": {"switch": (SW, {"right_bumper": release(remove("R"))})}})
        self.assertEqual(found(data), {("outside the guard", "P", "R")})

    def test_a_layer_another_button_keeps_is_not_expected_either(self):
        data = owner(base={"right_bumper": press(add("R"))},
                     extra={"R": {"switch": (SW, {"right_bumper": release(remove("R"))})}})
        self.assertEqual(found(data), set())

    def test_a_cleanup_never_lists_a_window(self):
        data = owner({"button_a": guarded(remove("P"), remove("C"), remove("W"))},
                     extra={"W": {"switch": (SW, {"always_on_action": press(remove("W"), delay_start=150)})}})
        self.assertEqual(found(data, "outside the guard"), {("outside the guard", "P", "W")})

    def test_a_cleanup_never_lists_a_stateful_layer(self):
        data = owner({"button_a": guarded(remove("P"), remove("C"), remove("Mode"))},
                     base={"button_y": press(add("T"))},
                     extra={"T": {"switch": (SW, {"button_y": release(remove("T"), add("Mode"))})}, "Mode": {}})
        self.assertEqual(found(data, "outside the guard"), {("outside the guard", "P", "Mode")})

    def test_a_layer_that_lives_inside_the_owners_hold_takes_the_owners_keeper(self):
        # D ends when the stick is released, but only P adds it, so P's cleanup removes it.
        stick = {"joystick": ("dpad", {"dpad_north": press(add("D"))})}
        d = {"joystick": ("dpad", {"dpad_north": release(remove("D"))})}
        ok = build({"Base": {"switch": (SW, {"left_bumper": press(add("P"))})},
                    "P": {"switch": (SW, {"left_bumper": release(remove("P"), remove("D")),
                                          "button_a": guarded(remove("P"), remove("D"))}), **stick},
                    "D": d})
        self.assertEqual(found(ok), set())
        left = build({"Base": {"switch": (SW, {"left_bumper": press(add("P"))})},
                      "P": {"switch": (SW, {"left_bumper": release(remove("P"), remove("D")),
                                            "button_a": guarded(remove("P"))}), **stick},
                      "D": d})
        self.assertEqual(found(left), {("left above", "P", "D")})


class HiddenTests(unittest.TestCase):
    def test_a_cover_that_binds_a_cleanup_input_with_an_output_hides_the_cleanup(self):
        cover = {"left_bumper": release(remove("P"), remove("C")), "button_a": press(KEY)}
        self.assertEqual(found(owner(cover=cover)), {("hidden cleanup", "C", "P")})

    def test_a_cancellation_is_an_accepted_shape(self):
        cover = {"left_bumper": release(remove("P"), remove("C")),
                 "button_a": press(remove("C"), hold_repeats=1, interruptable=0)}
        self.assertEqual(found(owner(cover=cover)), set())

    def test_the_layers_own_button_is_an_accepted_shape(self):
        # C binds LB, where P has no cleanup anyway; a second owner button is the case that matters.
        p = {"right_bumper": guarded(remove("P"), remove("C"))}
        cover = {"left_bumper": release(remove("P"), remove("C")), "right_bumper": release(remove("C"))}
        report = audit(owner(p, cover=cover), {})
        self.assertNotIn("hidden cleanup", {f["check"] for f in report["findings"]})

    def test_a_window_on_top_is_an_accepted_shape(self):
        window = {"always_on_action": press(remove("W"), delay_start=150), "button_a": press(EMPTY)}
        data = owner({"button_x": press(add("W"))}, extra={"W": {"switch": (SW, window)}})
        self.assertEqual(found(data, "hidden cleanup"), set())


class HiddenExitTests(unittest.TestCase):
    """R136: a layer on top may not cover an exit on what keeps the lower layer alive, unless it removes it there."""

    def test_a_layer_that_takes_the_release_without_removing_the_layer_below(self):
        data = owner(cover={"left_bumper": release(remove("C"))})
        report = audit(data, {})
        self.assertEqual(finding_pairs(report, "hidden exit"), {("hidden exit", "C", "P")})
        finding = next(f for f in report["findings"] if f["check"] == "hidden exit")
        self.assertEqual((finding["inputs"], finding["kind"], finding["keeper"]), (["LB"], "layer", "button LB"))
        self.assertFalse(report["ok"])

    def test_a_layer_that_removes_the_layer_below_there_is_fine(self):
        self.assertEqual(found(owner(), "hidden exit"), set())

    def test_a_different_source_mode_covers_the_exit_too(self):
        data = build({"Base": {"switch": (SW, {"button_a": press(add("P"))})},
                      "P": {"switch": (SW, {"button_b": press(add("C"))}),
                            "joystick": ("dpad", {"edge": release(remove("P"))})},
                      "C": {"joystick": ("joystick_move", {"click": press(KEY)})}})
        self.assertEqual(found(data, "hidden exit"), {("hidden exit", "C", "P")})

    def test_covering_an_exit_that_is_not_on_the_keeper_is_information(self):
        # LB keeps P. C covers P's stick-edge Release but leaves LB alone, so LB still ends P.
        data = build({"Base": {"switch": (SW, {"left_bumper": press(add("P"))})},
                      "P": {"switch": (SW, {"left_bumper": release(remove("P")), "button_b": press(add("C"))}),
                            "joystick": ("dpad", {"edge": release(remove("P"))})},
                      "C": {"joystick": ("dpad", {"edge": press(EMPTY)})}})
        report = audit(data, {})
        self.assertEqual(finding_pairs(report, "hidden exit"), set())
        self.assertEqual([(i["layer"], i["target"], i["inputs"]) for i in report["information"]["hidden exit"]],
                         [("C", "P", ["joystick/edge"])])

    def landing(self, hold=None, second=None):
        """S is a mode on Base; entering it clears the stack. Its button_x adds H, which takes LB. Base's LB adds
        E (which binds button_x), and E's button_b adds P, which ends on the LB Release and leaves button_x open. P takes two steps to
        arrive, so it is in none of H's chains, and it can't be under S as a bystander. H lands on P through
        S's binding, which P inherits (the Fallback Hold over a menu second-press layer)."""
        clear = press(remove("E"), remove("P"), remove("H"), add("S"))
        return build({"Base": {"switch": (SW, {"button_a": clear, "left_bumper": press(add("E"))})},
                      "S": {"switch": (SW, {"button_a": press(remove("H"), remove("S")), "button_x": press(add("H"))})},
                      "E": {"switch": (SW, {"left_bumper": release(remove("E")), "button_b": press(remove("E"), add("P")),
                                            "button_x": press(KEY)})},
                      "P": {"switch": (SW, {"left_bumper": release(remove("P")), **(second or {})})},
                      "H": {"switch": (SW, {"button_y": release(remove("H")), **(hold or {"left_bumper": press(KEY)})})}})

    def test_a_layer_that_lands_through_a_lower_layers_binding_is_on_top_too(self):
        data = self.landing()
        chains = Chains(Layout(data))
        self.assertNotIn("H", chains.above("P"))                                   # no chain of H's has P under it
        report = audit(data, {})
        self.assertEqual(finding_pairs(report, "hidden exit"), {("hidden exit", "H", "P")})
        finding = next(f for f in report["findings"] if f["check"] == "hidden exit")
        self.assertEqual((finding["example"], finding["inputs"]), ("Base > S > P > H", ["LB"]))
        self.assertIn("S switch/button_x", finding["path"][-1])                    # S's binding puts H on top

    def test_a_landing_that_leaves_the_exit_alone_or_cannot_happen_is_fine(self):
        alone = self.landing(hold={"right_bumper": press(KEY)})                          # H doesn't take LB
        self.assertEqual(found(alone, "hidden exit"), set())
        blocked = self.landing(second={"button_x": press(KEY)})                         # P binds button_x itself
        self.assertEqual(found(blocked, "hidden exit"), set())
        carried = self.landing(hold={"left_bumper": release(remove("P"), remove("H"))})  # H removes P there
        self.assertEqual(found(carried, "hidden exit"), set())

    def test_a_mode_block_is_charged_to_the_layer_that_changed_the_mode(self):
        # P ends on its stick click. M, in the middle, puts the stick in another mode; T on top has P's mode.
        data = build({"Base": {"switch": (SW, {"button_a": press(add("P"))})},
                      "P": {"switch": (SW, {"button_b": press(add("M"))}),
                            "joystick": ("dpad", {"click": release(remove("P"))})},
                      "M": {"switch": (SW, {"button_x": press(add("T"))}),
                            "joystick": ("joystick_move", {"touch": press(KEY)})},
                      "T": {"joystick": ("dpad", {"touch": press(KEY)})}})
        self.assertEqual(found(data, "hidden exit"), {("hidden exit", "M", "P")})        # not T, which only sits on top

    def side_exit(self):
        """LB keeps P. C covers P's stick-edge Release but leaves LB alone."""
        return build({"Base": {"switch": (SW, {"left_bumper": press(add("P"))})},
                      "P": {"switch": (SW, {"left_bumper": release(remove("P")), "button_b": press(add("C"))}),
                            "joystick": ("dpad", {"edge": release(remove("P"))})},
                      "C": {"joystick": ("dpad", {"edge": press(EMPTY)})}})

    def test_a_covered_side_exit_on_a_changed_layer_fails_until_accepted(self):
        data = self.side_exit()
        self.assertEqual(found(data, "exit to review"), set())                     # nothing changed: information
        for changed in ({"C"}, {"P"}):
            report = audit(data, {}, changed=changed)
            self.assertEqual({(f["check"], f["layer"], f["target"]) for f in report["findings"]},
                             {("exit to review", "C", "P")}, changed)
            self.assertFalse(report["ok"])
        self.assertTrue(audit(data, {}, changed={"Base"})["ok"])                   # another layer changed
        config = {"cleanups": {"accepted_exits": [{"upper": "C", "lower": "P", "why": "LB still ends P"}]}}
        report = audit(data, config, changed={"C"})
        self.assertTrue(report["ok"])
        self.assertEqual([(e["layer"], e["target"], e["why"]) for e in report["excepted"]], [("C", "P", "LB still ends P")])
        self.assertEqual(report["stale_decisions"], [])

    def test_an_accepted_exit_that_matches_no_pair_is_stale(self):
        config = {"cleanups": {"accepted_exits": [{"upper": "C", "lower": "P", "why": "old"}]}}
        self.assertEqual(audit(owner(), config)["stale_decisions"], ["C over P"])

    def touchpad(self):
        """The left pad adds T. W, added from T, clears the pad touch that T's Release is on."""
        return build({"Base": {"left_trackpad": ("dpad", {"touch": press(add("T"))})},
                      "T": {"left_trackpad": ("dpad", {"touch": release(remove("T"))}),
                            "switch": (SW, {"button_a": press(add("W"))})},
                      "W": {"left_trackpad": ("dpad", {"touch": press(EMPTY)})}})

    def test_a_touchpad_pair_is_a_finding_without_the_exception(self):
        self.assertEqual(found(self.touchpad(), "hidden exit"), {("hidden exit", "W", "T")})

    def test_the_touchpad_exception_sets_the_pair_aside(self):
        config = {"cleanups": {"touchpad_exits": "set aside for now"}}
        report = audit(self.touchpad(), config)
        self.assertEqual(finding_pairs(report, "hidden exit"), set())
        self.assertEqual([(e["layer"], e["target"], e["why"]) for e in report["excepted"]],
                         [("W", "T", "set aside for now")])
        self.assertEqual(report["stale_decisions"], [])

    def test_an_exception_that_sets_nothing_aside_is_stale(self):
        report = audit(owner(), {"cleanups": {"touchpad_exits": "set aside for now"}})
        self.assertEqual(report["stale_decisions"], ["the touchpad exception to R136"])

    def test_the_register_entry_reaches_the_audit(self):
        from steam_layout import exceptions
        entry = {"rule": "R136", "scope": {"kind": "touchpad"}, "status": "todo", "why": "for now",
                 "decided": "Author, 2026-10-02", "todo": "todos.md"}
        config = exceptions.expand({"exceptions": [entry]})
        self.assertEqual(found(self.touchpad(), "hidden exit", config), set())


class NeverThereTests(unittest.TestCase):
    def test_kept_removal_presence_scope_excludes_historical_layouts_in_both_variants(self):
        config = {'variants': {'alternative': {'L1': 'L2'}}, 'cleanups': {'keep': [{
            'layers': ['L1: Modifier 0'], 'removes': ['Steering | LS: Entry Guard'],
            'where': 'Stateful | Menu Left: Fn Layer', 'not_where': 'Steering | LS: Fallback Hold',
            'why': 'The new Entry Guard only, not the older Fallback Hold builds',
        }]}}
        modern = {'Stateful | Menu Left: Fn Layer', 'Steering | LS: Entry Guard'}
        for variant, layer in (('default', 'L1: Modifier 0'), ('alternative', 'L2: Modifier 0')):
            with self.subTest(variant=variant):
                self.assertEqual(set(kept(config, variant, modern)), {(layer, 'Steering | LS: Entry Guard')})
                self.assertEqual(kept(config, variant, modern | {'Steering | LS: Fallback Hold'}), {})
                self.assertEqual(kept(config, variant, {'Steering | LS: Entry Guard'}), {})
                self.assertEqual(kept(config, variant), {})

    def test_a_kept_removal_can_end_at_a_release(self):
        # 90.57 took the removes out, and the frozen builders up to 90.56 still rebuild with them (R132's `until`).
        config = {'cleanups': {'keep': [{'layers': ['P'], 'removes': ['Ghost'], 'until': '90.56', 'why': 'gone in 90.57'}]}}
        for version, holds in (('90.56', True), ('90.9', True), ('90.57', False), ('91.0', False), (None, True)):
            with self.subTest(version=version):
                self.assertEqual(set(kept(config, 'default', {'P'}, version)), {('P', 'Ghost')} if holds else set())
        self.assertEqual(release_of('single-set-default :: always-gyro :: 90.57'), '90.57')
        self.assertIsNone(release_of('a toy layout'))

    def test_a_cleanup_that_removes_a_layer_that_is_never_there(self):
        data = owner({"button_a": guarded(remove("P"), remove("C"), remove("Ghost"))},
                     extra={"Ghost": {"switch": (SW, {"left_bumper": release(remove("Ghost"))})}})
        self.assertEqual(found(data), {("never there", "P", "Ghost")})

    def test_a_release_follows_the_same_rule(self):
        data = owner({"left_bumper": release(remove("P"), remove("Ghost"))},
                     extra={"Ghost": {"switch": (SW, {"left_bumper": release(remove("Ghost"))})}})
        self.assertEqual(found(data), {("never there", "P", "Ghost")})

    def test_a_parent_that_removed_itself_is_never_under_the_layer_it_added(self):
        # P's release removes P and adds Q, so P is not under Q (the backward chains' first rule).
        data = owner({"left_bumper": release(remove("P"), add("Q"))},
                     extra={"Q": {"switch": (SW, {"left_bumper": release(remove("Q"), remove("P"))})}})
        self.assertIn(("never there", "Q", "P"), found(data))

    def test_a_deliberate_clear_keeps_its_whole_list(self):
        everything = [remove(t) for t in ("P", "C", "Ghost")]
        data = owner({"button_x": release(*everything)},
                     extra={"Ghost": {"switch": (SW, {"left_bumper": release(remove("Ghost"))})}})
        self.assertEqual(found(data), set())

    def test_the_stick_touch_release_keeps_its_fixed_layers(self):
        touch = {"joystick": ("dpad", {"touch": release(remove("T"), remove("T2"))})}
        helper = lambda t: {"joystick": ("dpad", {"touch": release(remove(t))})}  # noqa: E731
        data = build({"Base": {"switch": (SW, {"left_bumper": press(add("P"))}),
                               "joystick": ("dpad", {"touch": press(add("T"))})},
                      "P": {"switch": (SW, {"left_bumper": release(remove("P"))}), **touch},
                      "T": helper("T"), "T2": helper("T2")})
        self.assertEqual(found(data), set())

    def test_a_recorded_decision_keeps_a_removal(self):
        data = owner({"button_a": guarded(remove("P"), remove("C"), remove("Ghost"))},
                     extra={"Ghost": {"switch": (SW, {"left_bumper": release(remove("Ghost"))})}})
        config = {"cleanups": {"keep": [{"layers": ["P"], "removes": ["Ghost"], "why": "safety net"}]}}
        report = audit(data, config)
        self.assertTrue(report["ok"])
        self.assertEqual([(k["layer"], k["target"], k["why"]) for k in report["kept"]], [("P", "Ghost", "safety net")])

    def test_a_decision_that_matches_nothing_is_stale(self):
        config = {"cleanups": {"keep": [{"layers": ["P"], "removes": ["Ghost"], "why": "old"}]}}
        report = audit(owner(extra={"Ghost": {}}), config)
        self.assertEqual(report["stale_decisions"], ["P removes Ghost"])

    def test_a_layer_only_hold_layer_adds_is_left_out(self):
        data = owner({"button_a": guarded(remove("P"), remove("C"), remove("H"))},
                     base={"button_y": press(HOLD % "H")},
                     extra={"H": {"switch": (SW, {"button_a": guarded(remove("H"), remove("Ghost"), chord=2)})},
                            "Ghost": {}})
        report = audit(data, {})
        self.assertEqual(report["omitted"], ["H"])
        self.assertEqual(report["findings"], [])


class GuardTests(unittest.TestCase):
    def test_cleanups_of_one_layer_share_their_guard(self):
        data = owner({"button_x": guarded(remove("P"), remove("C"), chord=2)})
        self.assertIn(("guard mismatch", "P", None), found(data))

    def test_a_guard_button_cant_guard_its_own_input(self):
        # Both buttons hold Q open, like Modifier 2. On RB itself only LB can be the chord.
        q = {"left_bumper": release(remove("Q")), "right_bumper": {**release(remove("Q")), **guarded(remove("Q"))},
             "button_a": {"chord": [{"bindings": {"binding": EMPTY}, "settings": {"chord_button": "1"}},
                                    {"bindings": {"binding": EMPTY}, "settings": {"chord_button": "2"}}],
                          **press(remove("Q"), hold_repeats=1)}}
        data = build({"Base": {"switch": (SW, {"left_bumper": press(add("Q"))})}, "Q": {"switch": (SW, q)}})
        self.assertEqual(found(data, "guard mismatch"), set())


class FixTests(unittest.TestCase):
    """steam_layout.fixes.cleanup_lists: make the audit clean, with the audit's own findings."""

    def fixed(self, data, config=None):
        report = cleanup_lists.fix(data, config or {})
        self.assertEqual(audit(data, config or {})["findings"], [])
        return report

    def test_a_removal_that_is_never_there_is_dropped_and_the_rest_keep_their_order(self):
        data = owner({"button_a": guarded(remove("P"), remove("Ghost"), remove("C")),
                      "left_bumper": release(remove("P"), remove("Ghost"))},
                     extra={"Ghost": {"switch": (SW, {"left_bumper": release(remove("Ghost"))})}})
        self.fixed(data)
        self.assertEqual(removes(data, "P", "switch", "button_a"), ["P", "C"])
        self.assertEqual(removes(data, "P", "switch", "left_bumper", "release"), ["P"])

    def test_a_removal_outside_the_guard_is_dropped(self):
        data = owner({"button_a": guarded(remove("P"), remove("C"), remove("R"))},
                     base={"right_bumper": press(add("R"))},
                     extra={"R": {"switch": (SW, {"right_bumper": release(remove("R"))})}})
        self.fixed(data)
        self.assertEqual(removes(data, "P", "switch", "button_a"), ["P", "C"])

    def test_a_layer_left_below_is_added(self):
        cover = {"left_bumper": release(remove("P"), remove("C")), "button_a": guarded(remove("C"))}
        data = owner(cover=cover)
        self.fixed(data)
        self.assertEqual(removes(data, "C", "switch", "button_a"), ["C", "P"])

    def test_a_layer_left_above_is_added(self):
        data = owner({"button_a": guarded(remove("P"))})
        self.fixed(data)
        self.assertEqual(removes(data, "P", "switch", "button_a"), ["P", "C"])

    def test_a_hidden_cleanup_is_carried_with_one_either_button_chord(self):
        # C binds button_a with a release only, over P's cleanup. C's own cleanup on button_b gives the list.
        cover = {"left_bumper": release(remove("P"), remove("C")), "button_a": release(remove("C")),
                 "button_b": guarded(remove("C"), remove("P"))}
        data = owner(cover=cover, p_inputs={"button_b": guarded(remove("P"), remove("C")), "button_y": press(add("C"))})
        self.fixed(data)
        activators = Layout(data).active("C")["switch"]["inputs"]["button_a"]["activators"]
        self.assertEqual(list(activators), ["Full_Press", "chord", "release"])
        self.assertEqual(activators["chord"]["settings"], {"gyro_ratchet_button_mask": "8",
                                                           "gyro_ratchet_button_requireany_or_all": "0",
                                                           "interruptable": "0"})
        self.assertEqual(activators["Full_Press"]["settings"], {"hold_repeats": "1"})
        self.assertEqual(removes(data, "C", "switch", "button_a"), ["C", "P"])

    def test_a_guard_mismatch_widens_the_odd_chord(self):
        both = {**mask_chord(12), **press(remove("P"), remove("C"), hold_repeats=1)}
        odd = {**mask_chord(4), **press(remove("P"), remove("C"), hold_repeats=1)}
        data = owner({"button_a": both, "button_x": both, "button_y": odd})
        self.fixed(data)
        chord = Layout(data).active("P")["switch"]["inputs"]["button_y"]["activators"]["chord"]
        self.assertEqual(chord["settings"]["gyro_ratchet_button_mask"], "12")

    def test_the_fix_is_idempotent(self):
        data = owner({"button_a": guarded(remove("P"), remove("Ghost"))}, extra={"Ghost": {}})
        self.fixed(data)
        once = json.dumps(data)
        report = cleanup_lists.fix(data, {})
        self.assertEqual(json.dumps(data), once)
        self.assertEqual(report["changed"], [])

    def test_a_kept_removal_stays(self):
        data = owner({"button_a": guarded(remove("P"), remove("C"), remove("Ghost"))}, extra={"Ghost": {}})
        config = {"cleanups": {"keep": [{"layers": ["P"], "removes": ["Ghost"], "why": "safety net"}]}}
        self.fixed(data, config)
        self.assertEqual(removes(data, "P", "switch", "button_a"), ["P", "C", "Ghost"])

    def test_numeric_ids_are_written_as_numeric_ids(self):
        # Base=1, P=2, C=3: the working layouts use runtime IDs, not title tokens.
        data = owner(cover={"left_bumper": release(remove("P"), remove("C")), "button_a": guarded(remove("C"))})
        text = json.dumps(data)
        for title, number in (("P", 2), ("C", 3)):
            text = text.replace("{{Base::%s}}" % title, str(number))
        data = json.loads(text)
        cleanup_lists.fix(data, {})
        binding = Layout(data).active("C")["switch"]["inputs"]["button_a"]["activators"]["Full_Press"]["bindings"]["binding"]
        self.assertEqual(binding, ["controller_action remove_layer 2 0 0, , ", "controller_action remove_layer 3 0 0, , "])


if __name__ == "__main__":
    unittest.main()
