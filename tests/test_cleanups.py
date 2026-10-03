"""The Cleanup audit: what a cleanup function and a release may remove.

Tiny layouts, one rule per test, then the frozen 90.10 snapshots. The rules are in
findings/2026-10-02-cleanup-boundaries/README.md; the plan is plans/2026-10-02-cleanup-audit.md.
"""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from steam_layout.chains import Chains
from steam_layout.cleanups import Cleanups, audit
from steam_layout.fixes import cleanup_lists
from steam_layout.model import Layout, entries
from tests.test_audit_inheritance import EMPTY, add, build, remove
from tests.test_chains import SW, on, press, release

ROOT = Path(__file__).resolve().parents[1]
KEY = "key_press K, , "
HOLD = "controller_action hold_layer {{Base::%s}} 0 0, , "


def guarded(*removes, chord=1):
    """A cleanup function: a chord with the owner's button (1 = LB, 2 = RB) beside a repeating removal."""
    return {**on("chord", EMPTY, chord_button=chord), **press(*removes, hold_repeats=1)}


def owner(p_inputs=None, cover=None, base=None, extra=None):
    """Base's LB adds P. P's button_b adds the cover C, which only binds LB. P ends on the LB release."""
    p = {"left_bumper": release(remove("P")), "button_b": press(add("C")),
         "button_a": guarded(remove("P"), remove("C"))}
    p.update(p_inputs or {})
    layers = {"Base": {"switch": (SW, {"left_bumper": press(add("P")), **(base or {})})},
              "P": {"switch": (SW, p)},
              "C": {"switch": (SW, cover or {"left_bumper": release(remove("P"), remove("C"))})}}
    layers.update(extra or {})
    return build(layers)


def found(data, check=None, config=None):
    """{(check, layer, removed or hiding layer)} of the failing findings."""
    report = audit(data, config or {})
    return {(f["check"], f["layer"], f["target"]) for f in report["findings"] if check in (None, f["check"])}


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


class ScopeTests(unittest.TestCase):
    def test_a_clean_layout_has_no_findings(self):
        self.assertEqual(found(owner()), set())
        self.assertTrue(audit(owner(), {})["ok"])

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
        self.assertEqual(found(data, "hidden exit"), {("hidden exit", "C", "P")})
        finding = next(f for f in audit(data, {})["findings"] if f["check"] == "hidden exit")
        self.assertEqual((finding["inputs"], finding["kind"], finding["keeper"]), (["LB"], "layer", "button LB"))
        self.assertFalse(audit(data, {})["ok"])

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
        self.assertEqual(found(data, "hidden exit"), set())
        self.assertEqual([(i["layer"], i["target"], i["inputs"]) for i in report["information"]["hidden exit"]],
                         [("C", "P", ["joystick/edge"])])

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
        self.assertEqual(found(self.touchpad(), "hidden exit", config), set())
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


class HiddenExitSnapshotTests(unittest.TestCase):
    """The frozen 90.13 snapshots: the check reproduces the prototype's result of 2026-10-02."""

    @classmethod
    def setUpClass(cls):
        cls.data = {v: json.loads((ROOT / f"versions/neptune/90.13/single-set-{v}_hold-gyro_90.13.json")
                                  .read_text(encoding="utf-8")) for v in ("default", "alternative")}

    def test_no_finding_outside_the_touchpad_exception(self):
        for variant, data in self.data.items():
            with self.subTest(variant):
                report = audit(data, {"cleanups": {"touchpad_exits": "set aside"}})
                self.assertEqual([f for f in report["findings"] if f["check"] == "hidden exit"], [])
                self.assertEqual(len([e for e in report["excepted"] if e["on_keeper"]]), 68)
                self.assertEqual(len([e for e in report["excepted"] if not e["on_keeper"]]), 26)
                self.assertEqual({(i["layer"], i["target"]) for i in report["information"]["hidden exit"]},
                                 {("Menu Buttons: Tap Cover", "Menu Buttons: Left Stick Guard"),
                                  ("Menu Buttons: Tap Cover", "Menu Buttons: Right Stick Guard")})

    def test_the_touchpad_pairs_fail_without_the_exception(self):
        report = audit(self.data["default"], {})
        self.assertEqual(len([f for f in report["findings"] if f["check"] == "hidden exit"]), 68)


class NeverThereTests(unittest.TestCase):
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


class SnapshotTests(unittest.TestCase):
    """The frozen 90.10 snapshots: the audit reproduces what was measured on 2026-10-02."""

    @classmethod
    def setUpClass(cls):
        cls.reports, cls.cleanups = {}, {}
        for variant in ("default", "alternative"):
            path = ROOT / f"versions/neptune/90.10/single-set-{variant}_hold-gyro_90.10.json"
            data = json.loads(path.read_text(encoding="utf-8"))
            cls.cleanups[variant] = Cleanups(Layout(data))
            cls.reports[variant] = audit(data, {})

    def pairs(self, variant, check):
        return {(f["layer"], f["target"]) for f in self.reports[variant]["findings"] if f["check"] == check}

    def test_the_stateful_layers_are_gyro_and_steering(self):
        for variant, c in self.cleanups.items():
            self.assertEqual({t for t in c.layers if c.keeper(t)[0] == "mode"}, {"Gyro", "Steering"}, variant)

    def test_keepers_of_named_layers(self):
        c = self.cleanups["default"]
        for title, expected in {"L1: Modifier 0": {"LB"}, "L1!R1: Modifier 2": {"LB", "RB"}, "L1: Tap Cover": {"LB"},
                                "L1&R1: Tap Cover": {"LB", "RB"}, "Menu Left: Fn Layer": {"Select"},
                                "Menu Left: Entry Point": {"Select"}, "Steering | R1: W Key": {"RB"},
                                "Menu Buttons: Left Stick Guard": {"Select", "Start"}}.items():
            self.assertEqual(c.keeper(title), ("button", frozenset(expected)), title)
        self.assertEqual(c.keeper("L1: Double Tap")[0], "timer")
        self.assertEqual(c.keeper("LST: Entry Point")[0], "thumb")
        self.assertEqual(c.keeper("Steering | LS Down: Modifier 0")[0], "inside")
        alt = self.cleanups["alternative"]
        self.assertEqual(alt.keeper("L2: Modifier 0"), ("button", frozenset({"LT"})))
        self.assertEqual(alt.keeper("L2!R2: Modifier 2"), ("button", frozenset({"LT", "RT"})))

    def test_only_the_cursor_edges_leave_the_layer_below(self):
        self.assertEqual(self.pairs("default", "left below"),
                         {("L1: Temp Cursor Gyro", "L1: Modifier 0"), ("L1: Temp Cursor Gyro", "Gyro | L1: Modifier 0"),
                          ("R1: Temp Cursor Gyro", "R1: Modifier 1"), ("R1: Temp Cursor Gyro", "Gyro | R1: Modifier 1")})
        self.assertEqual(self.pairs("default", "left above"), set())

    def test_modifier_2_hides_the_touch_cleanup(self):
        hiding = {layer for layer, _ in self.pairs("default", "hidden cleanup")}
        self.assertEqual(hiding, {"L1!R1: Modifier 2", "R1!L1: Modifier 2",
                                  "Gyro | L1!R1: Modifier 2", "Gyro | R1!L1: Modifier 2"})
        inputs = {i for f in self.reports["default"]["findings"] if f["check"] == "hidden cleanup" for i in f["inputs"]}
        self.assertEqual(inputs, {"LSt", "RSt"})

    def test_only_steering_removes_outside_a_guard(self):
        outside = self.pairs("default", "outside the guard")
        self.assertTrue(all(layer.startswith("Steering | ") for layer, _ in outside))
        windows = {"Steering | LS Up: Double Tap", "Steering | LS Down: Double Tap"}
        self.assertEqual(len({layer for layer, target in outside if target in windows}), 6)
        # The other bumper's layers: a driver's cleanup, guarded by its own bumper, lists the
        # Modifier 2 and the Tap Cover that the second bumper keeps.
        self.assertEqual({pair for pair in outside if pair[1] not in windows},
                         {("Steering | R1: W Key", "Steering | R1!L1: Modifier 2"), ("Steering | R1: W Key", "L1: Tap Cover"),
                          ("Steering | L1: S Key", "Steering | L1!R1: Modifier 2"), ("Steering | L1: S Key", "R1: Tap Cover"),
                          ("Steering | R1!L1: Modifier 2", "L1: Tap Cover"), ("Steering | L1!R1: Modifier 2", "R1: Tap Cover")})

    def test_steering_modifier_2_guards_its_touches_differently(self):
        self.assertEqual({layer for layer, _ in self.pairs("default", "guard mismatch")},
                         {"Steering | R1!L1: Modifier 2", "Steering | L1!R1: Modifier 2"})

    def test_the_twin_is_never_there(self):
        never = self.pairs("default", "never there")
        self.assertIn(("L1: Modifier 0", "Gyro | L1: Modifier 0"), never)
        self.assertIn(("Gyro | L1: Modifier 0", "L1: Modifier 0"), never)
        self.assertIn(("Steering | R1: W Key", "Steering | L1: S Key"), never)
        self.assertNotIn(("L1: Tap Cover", "Gyro | L1: Modifier 0"), never)     # a shared layer keeps each parent

    def test_the_hold_layer_layers_are_left_out(self):
        self.assertEqual(self.reports["default"]["omitted"], ["LTP: Arrow Keys", "RTP: Mouse Buttons"])
        self.assertNotIn(("RTP: Circular Scroll", "RTP: Mouse Buttons"), self.pairs("default", "never there"))

    def test_the_variants_agree(self):
        count = lambda v: sorted((f["check"], len(f["inputs"])) for f in self.reports[v]["findings"])  # noqa: E731
        self.assertEqual(count("default"), count("alternative"))


def mask_chord(mask):
    return on("chord", EMPTY, gyro_ratchet_button_mask=mask, gyro_ratchet_button_requireany_or_all=0)


def removes(data, layer, source, inp, kind="Full_Press"):
    """The layers a binding removes, in execution order."""
    layout = Layout(data)
    activators = layout.active(layer)[source]["inputs"][inp]["activators"]
    return [t for k, e in entries(activators) if k == kind for op, t in layout.layer_ops(e) if op == "remove_layer"]


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


class FixedSnapshotTests(unittest.TestCase):
    """The fix on the frozen 90.10 snapshots: the six list checks come out clean, within the entry budget.

    The fix doesn't resolve hidden exits (R136), and 90.10 predates that rule."""

    def test_the_audit_is_clean_after_the_fix(self):
        for variant in ("default", "alternative"):
            data = json.loads((ROOT / f"versions/neptune/90.10/single-set-{variant}_hold-gyro_90.10.json").read_text())
            report = cleanup_lists.fix(data, {})
            with self.subTest(variant):
                self.assertEqual([f for f in audit(data, {})["findings"] if f["check"] != "hidden exit"], [])
                self.assertEqual(report["remaining"], 0)
                layout = Layout(data)
                for title in layout.presets:
                    for source, group in layout.active(title).items():
                        for name, value in group.get("inputs", {}).items():
                            count = sum(1 for _ in entries(value.get("activators", {})))
                            self.assertLessEqual(count, 4, f"{title} {source}/{name}")


class ScriptTests(unittest.TestCase):
    def run_script(self, data, *args):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "layout.json"
            path.write_text(json.dumps(data), encoding="utf-8")
            return subprocess.run([sys.executable, str(ROOT / "audit_cleanups.py"), str(path), *args],
                                  capture_output=True, text=True)

    def test_exit_codes(self):
        self.assertEqual(self.run_script(owner()).returncode, 0)
        self.assertEqual(self.run_script(owner({"button_a": guarded(remove("P"))})).returncode, 1)
        self.assertEqual(self.run_script({"not": "a layout"}).returncode, 2)

    def test_json_and_layer_filter(self):
        data = owner({"button_a": guarded(remove("P"))})
        report = json.loads(self.run_script(data, "--json").stdout)
        self.assertEqual([(f["check"], f["layer"], f["target"]) for f in report["findings"]], [("left above", "P", "C")])
        self.assertEqual(json.loads(self.run_script(data, "--json", "--layer", "C").stdout)["findings"], [])

    def test_the_text_names_the_binding_and_the_reason(self):
        text = self.run_script(owner({"button_a": guarded(remove("P"))})).stdout
        self.assertIn("left above", text.lower())
        self.assertIn("C", text)
        self.assertIn("LB", text)

    def test_the_text_names_the_rule_each_check_enforces(self):
        text = self.run_script(owner({"button_a": guarded(remove("P"))})).stdout
        self.assertIn("FAIL  left above [R129]", text)
        self.assertIn("ok    outside the guard [R127, R131]", text)
        self.assertIn("== Left above [R129]", text)


if __name__ == "__main__":
    unittest.main()
