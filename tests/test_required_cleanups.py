"""The required cleanups (R169 to R171): where a layer must have a cleanup function.

Tiny layouts, one rule per test, then the frozen 90.23 snapshots and the working layouts. The rules are
the author's of 2026-10-04; the record is findings/2026-10-04-required-cleanups/README.md.
"""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from steam_layout import exceptions, required_cleanups as required
from steam_layout.cleanups import Cleanups
from steam_layout.model import Layout
from tests.test_audit_inheritance import EMPTY, add, build, remove
from tests.test_chains import SW, on, press, release
from tests.test_cleanups import guarded

ROOT = Path(__file__).resolve().parents[1]
KEY = "key_press K, , "
TOUCH, EDGE, BUTTON = required.CHECKS
CLEANUP = guarded(remove("P"))                      # a chord with LB beside a repeating removal of P
CANCEL = press(remove("P"), hold_repeats=1, interruptable=0)
LEFT, RIGHT = ("joystick", "dpad"), ("right_joystick", "joystick_mouse")
FACE, DPAD, TRIGGER = ("button_diamond", "four_buttons"), ("dpad", "dpad"), ("left_trigger", "trigger")


def layout(p=None, base=None, extra=None, touches=True):
    """Base's LB adds P and LB's Release removes it. P has a cleanup function on both stick touches.

    `p` and `base` add inputs: {(source, mode): {input: activators}}. `extra` adds whole layers."""
    def sources(start, more):
        found = {source: (mode, dict(inputs)) for (source, mode), inputs in start.items()}
        for (source, mode), inputs in (more or {}).items():
            found.setdefault(source, (mode, {}))[1].update(inputs)
        return found

    own = {("switch", SW): {"left_bumper": release(remove("P"))}}
    if touches:
        own.update({LEFT: {"touch": CLEANUP}, RIGHT: {"touch": CLEANUP}})
    layers = {"Base": sources({("switch", SW): {"left_bumper": press(add("P"))}}, base), "P": sources(own, p)}
    layers.update(extra or {})
    return build(layers)


def audit(data, config=None, only=None):
    return required.audit(Cleanups(Layout(data)), config, only)


def found(data, config=None):
    """{(check, layer, input, reason)} of the failing findings."""
    return {(f["check"], f["layer"], name, f["reason"])
            for f in audit(data, config)["findings"] for name in f["inputs"]}


def inputs(data, check, layer="P"):
    return {name for c, where, name, _ in found(data) if c == check and where == layer}


class StateTests(unittest.TestCase):
    def test_how_a_layer_answers_an_input(self):
        data = layout({FACE: {"button_a": CLEANUP, "button_b": press(KEY), "button_x": press(EMPTY), "button_y": CANCEL},
                       DPAD: {"dpad_north": guarded(remove("Q"))}}, extra={"Q": {}})
        c = Cleanups(Layout(data))
        answers = {name: required.state(c, "P", control) for name, control in {
            "LB": ("switch", "left_bumper"), "RB": ("switch", "right_bumper"), "A": ("button_diamond", "button_a"),
            "B": ("button_diamond", "button_b"), "X": ("button_diamond", "button_x"), "Y": ("button_diamond", "button_y"),
            "up": ("dpad", "dpad_north"), "LT": ("left_trigger", "edge")}.items()}
        self.assertEqual(answers, {"LB": "own", "RB": "open", "A": "cleanup", "B": "bound", "X": "empty", "Y": "cancel",
                                   "up": "bound",          # a cleanup function that doesn't remove the layer itself
                                   "LT": "open"})          # no group for the source

    def test_a_disabled_group_answers_every_input_of_its_source(self):
        c = Cleanups(Layout(layout({("left_trigger", "disabled"): {}})))
        self.assertEqual(required.state(c, "P", ("left_trigger", "edge")), "disabled")


class TouchTests(unittest.TestCase):
    def test_a_layer_with_a_cleanup_function_on_both_touches_passes(self):
        report = audit(layout())
        self.assertTrue(report["ok"])
        self.assertEqual(report["findings"], [])

    def test_a_touch_left_to_the_layer_below_fails(self):
        self.assertEqual(found(layout(touches=False)), {
            (TOUCH, "P", "left-stick touch", "it leaves this touch to the layer below"),
            (TOUCH, "P", "right-stick touch", "it leaves this touch to the layer below")})

    def test_a_touch_with_only_a_release_fails(self):
        data = layout({RIGHT: {"touch": release(remove("H"))}}, extra={"H": {}})
        self.assertEqual(found(data), {(TOUCH, "P", "right-stick touch", "it binds this touch without a cleanup function")})

    def test_the_cleanup_function_has_to_remove_the_layer_itself(self):
        data = layout({RIGHT: {"touch": guarded(remove("Q"))}}, extra={"Q": {}})
        self.assertEqual(inputs(data, TOUCH), {"right-stick touch"})

    def test_a_release_beside_the_cleanup_function_is_fine(self):
        data = layout({RIGHT: {"touch": {**CLEANUP, **release(remove("H"))}}}, extra={"H": {}})
        self.assertEqual(found(data), set())

    def test_one_finding_for_each_layer_and_reason_with_its_inputs(self):
        finding, = audit(layout(touches=False))["findings"]
        self.assertEqual((finding["check"], finding["layer"], finding["bindings"]), (TOUCH, "P", 2))
        self.assertEqual(finding["controls"], ["joystick/touch", "right_joystick/touch"])
        self.assertEqual((finding["keeper"], finding["states"]), ("button LB", ["open"]))


class LeftOutTests(unittest.TestCase):
    """A window, a stateful layer and a ramp layer are left out of all three; a stick-touch helper of R169 only."""
    BOUND = {FACE: {"button_a": press(KEY)}}          # one retyped button and nothing else

    def types(self, data):
        return audit(data)["left_out"]

    def test_a_window(self):
        window = {"switch": (SW, {"always_on_action": press(remove("W"), delay_start=150), "button_escape": press(EMPTY)})}
        data = layout(base={("switch", SW): {"right_bumper": press(add("W"))}}, extra={"W": window})
        self.assertEqual((found(data), self.types(data)), (set(), {"window": ["W"]}))

    def test_a_stateful_layer(self):
        """S outlives T, the layer whose Release adds it, and has no Release of its own."""
        data = layout(base={("switch", SW): {"right_bumper": press(add("T"))}}, touches=True, extra={
            "T": {"switch": (SW, {"right_bumper": release(remove("T"), add("S")), "button_escape": CLEANUP_T}),
                  "joystick": ("dpad", {"touch": CLEANUP_T, "edge": CLEANUP_T}),
                  "right_joystick": ("joystick_mouse", {"touch": CLEANUP_T, "edge": CLEANUP_T})},
            "S": {"switch": (SW, {"button_escape": press(KEY)})}})
        self.assertEqual((found(data), self.types(data)), (set(), {"stateful": ["S"]}))

    def test_a_ramp_layer(self):
        """R ends on a threshold: no button, thumb or stick keeps it on."""
        ramp = {"right_joystick": ("joystick_mouse", {"edge": press(remove("R"), hold_repeats=1, interruptable=0)}),
                "switch": (SW, {"button_escape": press(KEY)})}
        data = layout(base={RIGHT: {"edge": press(add("R"))}}, extra={"R": ramp})
        self.assertEqual((found(data), self.types(data)), (set(), {"ramp": ["R"]}))

    def test_a_layer_that_nothing_ends_is_not_a_ramp_layer(self):
        data = layout(base={("switch", SW): {"right_bumper": press(add("Q"))}}, extra={"Q": {}})
        self.assertEqual(self.types(data), {})
        self.assertEqual({(check, name) for check, layer, name, _ in found(data) if layer == "Q"}, {
            (TOUCH, "left-stick touch"), (TOUCH, "right-stick touch")})

    def test_a_stick_touch_helper_is_left_out_of_the_touch_check_only(self):
        helper = {"joystick": ("dpad", {"touch": release(remove("H"))}), "button_diamond": ("four_buttons", {"button_a": press(KEY)})}
        data = layout(base={LEFT: {"touch": press(add("H"))}}, extra={"H": helper})
        self.assertEqual(self.types(data), {"helper": ["H"]})
        self.assertEqual({(check, name) for check, layer, name, _ in found(data) if layer == "H"}, {
            (EDGE, "left-stick edge"), (EDGE, "right-stick edge"), (BUTTON, "A")})


CLEANUP_T = guarded(remove("T"), chord=2)          # T's own cleanup function, guarded by RB


class EdgeTests(unittest.TestCase):
    OPEN = "it binds or blocks a button and leaves this edge open"

    def test_a_layer_that_binds_no_edge_and_no_button_needs_none(self):
        self.assertEqual(inputs(layout(), EDGE), set())

    def test_a_blocked_edge_needs_a_cleanup_function_on_that_edge_only(self):
        data = layout({RIGHT: {"edge": press(EMPTY)}})
        self.assertEqual(found(data), {(EDGE, "P", "right-stick edge", "it blocks this edge with an empty binding")})

    def test_a_bound_edge_needs_one_even_when_it_holds_the_layers_exit(self):
        data = layout({LEFT: {"edge": release(remove("P"))}})
        self.assertEqual(found(data), {(EDGE, "P", "left-stick edge", "it binds this edge without a cleanup function")})
        self.assertEqual(found(layout({LEFT: {"edge": {**CLEANUP, **release(remove("P"))}}})), set())

    def test_a_face_dpad_menu_or_back_button_asks_for_both_edges(self):
        for group, name in ((FACE, "button_a"), (DPAD, "dpad_west"), (("switch", SW), "button_escape"),
                            (("switch", SW), "button_menu"), (("switch", SW), "button_back_left_upper")):
            with self.subTest(name):
                data = layout({group: {name: CLEANUP}})
                self.assertEqual(found(data), {(EDGE, "P", "left-stick edge", self.OPEN), (EDGE, "P", "right-stick edge", self.OPEN)})
                both = layout({group: {name: CLEANUP}, LEFT: {"edge": CLEANUP}, RIGHT: {"edge": CLEANUP}})
                self.assertEqual(found(both), set())

    def test_a_block_on_such_a_button_asks_for_them_too(self):
        data = layout({FACE: {"button_a": press(EMPTY)}})
        self.assertEqual(inputs(data, EDGE), {"left-stick edge", "right-stick edge"})

    def test_a_bumper_or_a_trigger_asks_for_no_edge(self):
        data = layout({("switch", SW): {"right_bumper": CLEANUP}, TRIGGER: {"edge": CLEANUP, "click": CLEANUP}})
        self.assertEqual(found(data), set())

    def test_the_layers_own_menu_button_asks_for_both_edges(self):
        """Why a menu stick guard needs its exception: Start and Select are its own buttons, and it still
        answers them."""
        data = build({"Base": {"switch": (SW, {"button_escape": press(add("P"))})},
                      "P": {"switch": (SW, {"button_escape": release(remove("P"))}),
                            "joystick": ("dpad", {"touch": guarded(remove("P"), chord=14)}),
                            "right_joystick": ("joystick_mouse", {"touch": guarded(remove("P"), chord=14)})}})
        self.assertEqual({(check, name) for check, _, name, _ in found(data)}, {
            (EDGE, "left-stick edge"), (EDGE, "right-stick edge")})


class ButtonTests(unittest.TestCase):
    EDGES = {LEFT: {"edge": CLEANUP}, RIGHT: {"edge": CLEANUP}}

    def test_a_retyped_button_needs_a_cleanup_function(self):
        data = layout({**self.EDGES, FACE: {"button_a": press(KEY)}})
        self.assertEqual(found(data), {(BUTTON, "P", "A", "it retypes this button without a cleanup function")})
        self.assertEqual(found(layout({**self.EDGES, FACE: {"button_a": {**CLEANUP, **on("chord", KEY, chord_button=1)}}})), set())

    def test_the_bumpers_and_both_trigger_inputs_are_buttons(self):
        data = layout({("switch", SW): {"right_bumper": press(KEY)}, TRIGGER: {"edge": press(KEY), "click": press(KEY)}})
        self.assertEqual(inputs(data, BUTTON), {"RB", "LT pull", "LT full pull"})

    def test_the_layers_own_button_passes(self):
        data = layout({("switch", SW): {"left_bumper": {**release(remove("P")), **press(KEY)}}})
        self.assertEqual(found(data), set())

    def test_a_button_that_removes_the_layer_by_cancellation_passes(self):
        data = layout({("switch", SW): {"right_bumper": CANCEL}})
        self.assertEqual(found(data), set())

    def test_a_self_removing_handoff_passes_without_a_second_cleanup(self):
        # Driver acquisition repeats; a fresh menu handoff uses Start Press.
        # Both consume P even though the chain inventory calls them entries.
        for kind, settings in (("Full_Press", {"hold_repeats": 1}), ("Start_Press", {})):
            with self.subTest(activation=kind):
                data = layout({("switch", SW): {"right_bumper": on(
                    kind, remove("P"), add("Q"), **settings)}}, extra={"Q": {}})
                self.assertEqual(inputs(data, BUTTON), set())
                self.assertEqual(required.state(Cleanups(Layout(data)), "P", ("switch", "right_bumper")), "cancel")

    def test_an_entry_that_keeps_or_readds_its_source_still_needs_cleanup(self):
        for commands in ((add("Q"),), (remove("P"), add("P"), add("Q"))):
            with self.subTest(commands=commands):
                data = layout({("switch", SW): {"right_bumper": press(*commands)}}, extra={"Q": {}})
                self.assertEqual(inputs(data, BUTTON), {"RB"})

    def test_a_cancellation_of_another_layer_does_not(self):
        other = press(remove("Q"), hold_repeats=1, interruptable=0)
        data = layout({("switch", SW): {"right_bumper": other}}, extra={"Q": {}})
        self.assertEqual(inputs(data, BUTTON), {"RB"})

    def test_a_block_counts_as_a_retype_and_says_when_it_covers_nothing(self):
        covers = layout({TRIGGER: {"edge": press(EMPTY)}}, base={TRIGGER: {"edge": press(KEY)}})
        self.assertEqual(found(covers), {(BUTTON, "P", "LT pull", "it blocks this button with an empty binding")})
        nothing = layout({TRIGGER: {"click": press(EMPTY)}}, base={TRIGGER: {"edge": press(KEY)}})
        self.assertEqual(found(nothing), {
            (BUTTON, "P", "LT full pull", "it blocks this button with an empty binding that covers nothing")})

    def test_a_block_over_a_binding_of_a_layer_that_can_be_under_it_covers_something(self):
        """Base's RB adds Q, which binds the trigger's full pull and whose button_x adds P on top."""
        data = build({"Base": {"switch": (SW, {"right_bumper": press(add("Q"))})},
                      "Q": {"switch": (SW, {"right_bumper": release(remove("Q")), "left_bumper": press(add("P"))}),
                            "left_trigger": ("trigger", {"click": press(KEY)})},
                      "P": {"switch": (SW, {"left_bumper": release(remove("P"))}),
                            "left_trigger": ("trigger", {"click": press(EMPTY)})}})
        self.assertIn((BUTTON, "P", "LT full pull", "it blocks this button with an empty binding"), found(data))

    def test_a_disabled_button_group_fails_on_each_of_its_buttons(self):
        data = layout({("left_trigger", "disabled"): {}})
        self.assertEqual(found(data), {(BUTTON, "P", name, "its group for this button is disabled")
                                       for name in ("LT pull", "LT full pull")})


class ExceptionTests(unittest.TestCase):
    DATA = layout({RIGHT: {"edge": press(EMPTY)}})

    def config(self, rule="R170", layer="P", name="right_joystick/edge"):
        return {"cleanups": {"required": [{"rule": rule, "layers": [layer], "inputs": [name], "why": "decided"}]}}

    def test_an_accepted_input_is_set_aside(self):
        report = audit(self.DATA, self.config())
        self.assertTrue(report["ok"])
        self.assertEqual(report["excepted"], [{"check": EDGE, "layer": "P", "input": "right-stick edge",
                                               "control": "right_joystick/edge", "why": "decided"}])
        self.assertEqual(report["stale_decisions"], [])

    def test_an_exception_is_for_one_rule_one_layer_and_one_input(self):
        for config in (self.config(rule="R171"), self.config(layer="Q"), self.config(name="joystick/edge")):
            report = audit(self.DATA, config)
            self.assertFalse(report["ok"])
            self.assertEqual(len(report["stale_decisions"]), 1)

    def test_an_exception_needs_a_why(self):
        config = self.config()
        config["cleanups"]["required"][0]["why"] = ""
        with self.assertRaises(ValueError):
            audit(self.DATA, config)

    def test_presence_and_absence_gates_do_not_waive_historical_layouts(self):
        config = self.config()
        config["cleanups"]["required"][0].update(where="New", not_where="Retired")
        key = ("R170", "P", "right_joystick/edge")
        for titles, expected in (({"P"}, {}), ({"P", "New", "Retired"}, {}),
                                 ({"P", "New"}, {key: "decided"})):
            with self.subTest(titles=titles):
                self.assertEqual(required.excepted(config, "default", titles), expected)

    def test_unknown_context_does_not_grant_a_negative_scope_waiver(self):
        # A historical builder once omitted titles and silently treated every
        # newer exception as applicable, skipping its required cleanup writes.
        config = self.config()
        row = config["cleanups"]["required"][0]
        row.update(where="New", not_where="Retired")
        self.assertEqual(required.excepted(config, "default"), {})
        # Existing where-only calls remain compatible with frozen builders.
        del row["not_where"]
        self.assertEqual(required.excepted(config, "default"), {
            ("R170", "P", "right_joystick/edge"): "decided"})

    def test_titles_are_mapped_for_the_alternative_layout(self):
        data = build({"Base": {"switch": (SW, {"left_bumper": press(add("L2: P"))})},
                      "L2: P": {"switch": (SW, {"left_bumper": release(remove("L2: P"))}),
                                "joystick": ("dpad", {"touch": guarded(remove("L2: P"))}),
                                "right_joystick": ("joystick_mouse", {"touch": guarded(remove("L2: P")), "edge": press(EMPTY)})}})
        data["controller_mappings"]["title"] = "single-set-alternative :: test :: 1"
        config = {"variants": {"alternative": {"L1": "L2"}}, **self.config(layer="L1: P")}
        self.assertTrue(audit(data, config)["ok"])

    def test_the_register_fills_the_section_the_audit_reads(self):
        entry = {"rule": "R170", "scope": {"layers": ["P"], "inputs": ["right_joystick/edge"]}, "status": "allow",
                 "why": "decided", "decided": "Author, 2026-10-04", "todo": None}
        config = exceptions.expand({"exceptions": [entry]})
        self.assertTrue(audit(self.DATA, config)["ok"])
        with self.assertRaises(ValueError):
            exceptions.check([{**entry, "scope": {"layers": ["P"]}}])        # the scope names the inputs too

    def test_only_one_layer(self):
        data = layout(touches=False, extra={"Q": {}}, base={("switch", SW): {"right_bumper": press(add("Q"))}})
        self.assertEqual({f["layer"] for f in audit(data)["findings"]}, {"P", "Q"})
        self.assertEqual({f["layer"] for f in audit(data, only=["Q"])["findings"]}, {"Q"})


def counts(report):
    return tuple(report["counts"][check]["bindings"] for check in required.CHECKS)


class SnapshotTests(unittest.TestCase):
    """The frozen 90.23 snapshots: what the three checks found when they were written (2026-10-04)."""
    HELPERS = [f"{stick}: {part}" for part in ("Temporary Gyro", "Entry Point", "Tap Cover") for stick in ("LST", "RST")]
    FULL_PULL = {"LT full pull", "RT full pull"}

    @classmethod
    def setUpClass(cls):
        config = exceptions.load_config()
        cls.reports = {}
        for variant in ("default", "alternative"):
            path = ROOT / f"versions/neptune/90.23/single-set-{variant}_hold-gyro_90.23.json"
            cleanups = Cleanups(Layout(json.loads(path.read_text(encoding="utf-8"))))
            cls.reports[variant] = required.audit(cleanups, config)

    def test_the_inputs_without_a_cleanup_function(self):
        self.assertEqual(counts(self.reports["default"]), (48, 42, 84))
        self.assertEqual(counts(self.reports["alternative"]), (48, 42, 106))

    def test_the_layers_left_out(self):
        for variant, report in self.reports.items():
            with self.subTest(variant):
                left = report["left_out"]
                self.assertEqual(left["ramp"], ["Turning Ramp Up 0", "Turning Ramp Up 1", "Gyro Off Ramp Up"])
                self.assertEqual(left["stateful"], ["Gyro", "Steering", "Cursor Gyro", "Gamepad"])
                self.assertEqual(left["helper"], self.HELPERS)
                self.assertEqual(len(left["window"]), 9)
                self.assertTrue(all(title.endswith(": Double Tap") for title in left["window"]))

    def test_the_four_inputs_the_author_accepted(self):
        for variant, report in self.reports.items():
            with self.subTest(variant):
                self.assertEqual({(e["layer"], e["input"]) for e in report["excepted"]}, {
                    ("Menu Buttons: Left Stick Guard", "right-stick edge"), ("Menu Buttons: Right Stick Guard", "left-stick edge"),
                    ("Steering | LS: Entry Guard", "left-stick edge"), ("Steering | LS: Fallback Hold", "left-stick edge")})
                self.assertEqual(report["stale_decisions"], [])

    def test_24_layers_lack_a_touch_cleanup_and_ten_of_them_are_covers(self):
        for variant, report in self.reports.items():
            with self.subTest(variant):
                touch = [f for f in report["findings"] if f["check"] == TOUCH]
                self.assertEqual((len(touch), {f["bindings"] for f in touch}), (24, {2}))
                inherit = [f["layer"] for f in touch if f["reason"] == "it leaves this touch to the layer below"]
                covers = [title for title in inherit if "Cover" in title or "Temp Cursor Gyro" in title]
                self.assertEqual((len(covers), set(inherit) - set(covers)), (10, {"Steering | LS: Fallback Hold"}))

    def test_every_full_pull_block_in_the_default_layout_covers_nothing(self):
        nothing = [f for f in self.reports["default"]["findings"] if f["reason"] == required.NOTHING]
        self.assertEqual((len(nothing), sum(f["bindings"] for f in nothing)), (19, 38))
        self.assertTrue(all(set(f["inputs"]) == self.FULL_PULL for f in nothing))

    def test_the_modifiers_the_pad_layers_and_the_single_tap_covers_pass(self):
        for variant, report in self.reports.items():
            failing = {f["layer"] for f in report["findings"] if f["reason"] != required.NOTHING}
            side = "L1" if variant == "default" else "L2"
            with self.subTest(variant):
                for title in (f"{side}: Tap Cover", "LTP: Arrow Keys", "RTP: Mouse Buttons", "RTP: Circular Scroll", "Escape",
                              "LTP: Click Entry Point", "RTP: Middle Click"):
                    self.assertNotIn(title, failing)


class WorkingLayoutTests(unittest.TestCase):
    def test_the_working_layouts_have_every_required_cleanup(self):
        """It failed on 90.23 on purpose: the rules were enforced before the layouts followed them. 90.24
        applied the fixes (findings/2026-10-04-required-cleanups/README.md)."""
        config = exceptions.load_config()
        for variant in ("default", "alternative"):
            path = ROOT / f"neptune/single-set-{variant}_hold-gyro_latest.json"
            report = required.audit(Cleanups(Layout(json.loads(path.read_text(encoding="utf-8")))), config)
            with self.subTest(variant):
                self.assertEqual(dict(zip(required.CHECKS, counts(report))), dict.fromkeys(required.CHECKS, 0))
                self.assertEqual(report["stale_decisions"], [])


class CommandTests(unittest.TestCase):
    def run_audit(self, data, *args):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "layout.json"
            path.write_text(json.dumps(data), encoding="utf-8")
            return subprocess.run([sys.executable, "-m", "tools.audit_cleanups", str(path), "--extras", "0", *args],
                                  capture_output=True, text=True, cwd=ROOT)

    def test_the_cleanup_audit_fails_on_a_missing_cleanup_and_names_the_rule(self):
        result = self.run_audit(layout(touches=False))
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("FAIL  touch without cleanup [R169]", result.stdout)
        self.assertIn("left-stick touch, right-stick touch: it leaves this touch to the layer below", result.stdout)
        self.assertIn("ok    button without cleanup [R171]", result.stdout)

    def test_it_passes_when_every_required_cleanup_is_there(self):
        result = self.run_audit(layout())
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_json_carries_the_three_checks(self):
        report = json.loads(self.run_audit(layout(touches=False), "--json").stdout)
        self.assertEqual(report["counts"][TOUCH], {"findings": 1, "bindings": 2})
        self.assertFalse(report["ok"])
        self.assertEqual(report["required"], {"excepted": [], "left_out": {}})


if __name__ == "__main__":
    unittest.main()
