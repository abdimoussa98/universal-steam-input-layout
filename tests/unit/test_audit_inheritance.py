"""Inheritance/blocking audit (Layer Definition of Done, section 8).

Fixture responsibility: unit. See docs/testing.md and tests/test-map.csv.
"""
from tests.support.fixtures.audit_inheritance import *

class RouteTests(unittest.TestCase):
    def test_inherited_layer_command_is_an_open_route(self):
        data = build({"Base": {"switch": ("switches", {"button_a": act(add("Mod"))})},
                      "Mod": {}, "Win": {}})
        report = audit(data, config([["Base"]]))
        self.assertEqual(routes(report, "open"), {("switch", "button_a")})
        self.assertFalse(report["ok"])

    def test_plain_output_is_not_a_route(self):
        data = build({"Base": {"switch": ("switches", {"button_a": act("key_press A, , ")})}, "Win": {}})
        report = audit(data, config([["Base"]]))
        self.assertEqual(routes(report), set())
        self.assertTrue(report["ok"])

    def test_clear_and_replace_block_the_whole_input(self):
        data = build({"Base": {"switch": ("switches", {"button_a": act(add("Mod")),
                                                       "button_b": act(remove("Mod"))})},
                      "Mod": {},
                      "Win": {"switch": ("switches", {"button_a": act(EMPTY),
                                                      "button_b": act("mouse_wheel SCROLL_UP, , ")})}})
        report = audit(data, config([["Base"]]))
        self.assertEqual(routes(report), set())
        blocked = {(b["input"], b["kind"]) for b in report["targets"]["Win"]["blocked"]}
        self.assertEqual(blocked, {("button_a", "cleared"), ("button_b", "replaced")})

    def test_empty_activators_are_not_a_block(self):
        data = build({"Base": {"switch": ("switches", {"button_a": act(add("Mod"))})},
                      "Mod": {}, "Win": {"switch": ("switches", {"button_a": {}})}})
        self.assertEqual(routes(audit(data, config([["Base"]])), "open"), {("switch", "button_a")})

    def test_topmost_lower_definer_wins(self):
        data = build({"Base": {"switch": ("switches", {"button_a": act(add("Mod")),
                                                       "button_b": act("key_press B, , ")})},
                      "Mod": {"switch": ("switches", {"button_a": act("key_press A, , "),
                                                      "button_b": act(remove("Mod"))})},
                      "Win": {}})
        report = audit(data, config([["Base", "Mod"]]))
        rows = report["targets"]["Win"]["routes"]
        self.assertEqual([(r["input"], r["from_layer"]) for r in rows], [("button_b", "Mod")])

    def test_disabled_source_blocks_in_the_target_or_below_it(self):
        base = {"right_trackpad": ("absolute_mouse", {"click": act(add("Mod"))})}
        in_target = build({"Base": base, "Mod": {}, "Win": {"right_trackpad": ("disabled", {})}})
        self.assertEqual(routes(audit(in_target, config([["Base"]]))), set())
        below = build({"Base": base, "Mod": {"right_trackpad": ("disabled", {})}, "Win": {}})
        self.assertEqual(routes(audit(below, config([["Base", "Mod"]]))), set())

    def test_mode_shift_to_a_group_with_layer_commands_is_a_route(self):
        data = build({"Base": {"joystick": ("joystick_mouse", {"click": act("mode_shift joystick 90, , ")}),
                               "switch": ("switches", {"button_b": act("mode_shift joystick 91, , ")})},
                      "Mod": {}, "Win": {}},
                     modeshift={"90": ("joystick", "dpad", {"dpad_north": act(add("Mod"))}),
                                "91": ("joystick", "dpad", {"dpad_north": act("key_press W, , ")})})
        rows = audit(data, config([["Base"]]))["targets"]["Win"]["routes"]
        self.assertEqual([(r["source"], r["input"], r["via"]) for r in rows],
                         [("joystick", "click", "mode_shift joystick 90")])

    def test_a_different_source_mode_above_the_definer_blocks_inheritance(self):
        # Author rule, 2026-10-01: a mode change blocks; the lower mode's inputs don't carry over.
        for win, mod in [("dpad", {}), ("absolute_mouse", {"right_trackpad": ("dpad", {})})]:
            data = build({"Base": {"right_trackpad": ("absolute_mouse", {"touch": act(add("Mod"))})},
                          "Mod": mod, "Win": {"right_trackpad": (win, {"dpad_north": act(EMPTY)})}})
            report = audit(data, config([["Base", "Mod"]]))
            self.assertEqual(routes(report), set())
            self.assertEqual({(b["input"], b["kind"]) for b in report["targets"]["Win"]["blocked"]},
                             {("touch", "mode replaced")})
            self.assertTrue(report["ok"])

    def test_decisions_allow_or_defer_routes_and_stale_ones_are_reported(self):
        data = build({"Base": {"switch": ("switches", {"button_a": act(add("Mod")),
                                                       "button_b": act(add("Mod"))})},
                      "Mod": {}, "Win": {}})
        cfg = config([["Base"]], [
            {"source": "switch", "input": "button_a", "status": "allow", "why": "intended"},
            {"source": "switch", "input": "button_b", "status": "todo", "why": "awaiting author"},
            {"source": "switch", "input": "button_x", "status": "allow", "why": "old"}])
        report = audit(data, cfg)
        self.assertEqual(routes(report, "allowed"), {("switch", "button_a")})
        self.assertEqual(routes(report, "todo"), {("switch", "button_b")})
        self.assertTrue(report["ok"])
        self.assertEqual([(d["input"]) for d in report["targets"]["Win"]["stale_decisions"]], ["button_x"])

    def test_decision_without_reason_or_bad_status_is_rejected(self):
        data = build({"Base": {}, "Win": {}})
        for bad in ({"source": "switch", "input": "button_a", "status": "allow"},
                    {"source": "switch", "input": "button_a", "status": "maybe", "why": "x"}):
            with self.subTest(bad), self.assertRaises(ValueError):
                audit(data, config([["Base"]], [bad]))

    def test_each_stack_is_checked_and_routes_record_their_stack(self):
        data = build({"Base": {"switch": ("switches", {"button_a": act("key_press A, , ")})},
                      "Gyro": {"switch": ("switches", {"button_a": act(add("Mod"))})},
                      "Mod": {}, "Win": {}})
        rows = audit(data, config([["Base"], ["Base", "Gyro"]]))["targets"]["Win"]["routes"]
        self.assertEqual([r["stack"] for r in rows], [["Base", "Gyro"]])


class UntracedTests(unittest.TestCase):
    """Inputs other layers use for layer commands that the target leaves open,
    outside the traced stacks: a call-out list, not a failure."""

    def test_layer_command_inputs_elsewhere_are_called_out(self):
        data = build({"Base": {"joystick": ("dpad", {"click": act("key_press Q, , ")})},
                      "Fn": {"joystick": ("dpad", {"click": act(add("Mod")), "touch": act(add("Mod"))})},
                      "Mod": {"switch": ("switches", {"button_a": act(remove("Mod"))})},
                      "Win": {"joystick": ("dpad", {"touch": act(EMPTY)})}})
        report = audit(data, config([["Base"]]))
        untraced = report["targets"]["Win"]["untraced"]
        self.assertEqual([(u["source"], u["input"], u["layers"]) for u in untraced],
                         [("joystick", "click", ["Fn"]), ("switch", "button_a", ["Mod"])])
        self.assertTrue(report["ok"])

    def test_disabled_sources_and_traced_routes_are_not_repeated(self):
        data = build({"Base": {"switch": ("switches", {"button_a": act(add("Mod"))})},
                      "Mod": {"right_trackpad": ("absolute_mouse", {"click": act(add("Mod"))})},
                      "Win": {"right_trackpad": ("disabled", {})}})
        report = audit(data, config([["Base"]]))
        self.assertEqual(report["targets"]["Win"]["untraced"], [])


class BlocksNeededTests(unittest.TestCase):
    """What the audit recommends for an open route: replace with the one possible keybind, or clear."""

    def test_always_on_layers_are_audited_from_derived_stacks_without_config(self):
        data = build({"Base": {"switch": ("switches", {"left_bumper": act(add("Ramp")),
                                                       "right_bumper": act(add("Win"))}),
                               "left_trigger": ("trigger", {"edge": act("mouse_button LEFT, , ")})},
                      "Ramp": {"left_trigger": ("trigger", {"edge": act([remove("Ramp"), "mouse_button LEFT, , "])})},
                      "Win": {"switch": ("switches", {"always_on_action": act(remove("Win")),
                                                      "left_bumper": act(EMPTY), "right_bumper": act(EMPTY)})}})
        report = audit(data, {"targets": {}})
        row = report["targets"]["Win"]
        self.assertEqual({(r["source"], r["input"], r["from_layer"]) for r in row["routes"]},
                         {("left_trigger", "edge", "Ramp")})
        self.assertFalse(report["ok"])
        self.assertEqual(row["blocks_needed"], [{
            "source": "left_trigger", "input": "edge", "action": "replace", "stacks": 2,
            "activators": {"Full_Press": {"bindings": {"binding": "mouse_button LEFT, , "}}}}])

    def test_a_stack_with_only_a_layer_command_adds_no_keybind(self):
        # Author, 2026-10-01: one possible keybind means replace. Under Ramp the soft pull only
        # removes Ramp, so the only keybind is Base's mouse button.
        def layout(base_edge):
            return build({"Base": {"switch": ("switches", {"left_bumper": act(add("Ramp")),
                                                           "right_bumper": act(add("Win"))}),
                                   "left_trigger": ("trigger", {"edge": act(base_edge)})},
                          "Ramp": {"left_trigger": ("trigger", {"edge": act(remove("Ramp"))})},
                          "Win": {"switch": ("switches", {"always_on_action": act(remove("Win")),
                                                          "left_bumper": act(EMPTY), "right_bumper": act(EMPTY)})}})
        needed = audit(layout("mouse_button LEFT, , "), {"targets": {}})["targets"]["Win"][
            "blocks_needed"]
        self.assertEqual(needed, [{
            "source": "left_trigger", "input": "edge", "action": "replace", "stacks": 2,
            "activators": {"Full_Press": {"bindings": {"binding": "mouse_button LEFT, , "}}}}])
        # No keybind in any stack: nothing to replace with.
        needed = audit(layout(EMPTY), {"targets": {}})["targets"]["Win"]["blocks_needed"]
        self.assertEqual([(b["input"], b["action"], b["activators"]) for b in needed], [("edge", "clear", None)])

    def test_varying_underlying_binds_must_be_cleared(self):
        data = build({"Base": {"switch": ("switches", {"left_bumper": act(add("Mod")),
                                                       "right_bumper": act(add("Win"))}),
                               "joystick": ("dpad", {"click": act("key_press Q, , ")})},
                      "Mod": {"joystick": ("dpad", {"click": act([add("Mod"), "mouse_button MIDDLE, , "])})},
                      "Win": {"switch": ("switches", {"always_on_action": act(remove("Win")),
                                                      "left_bumper": act(EMPTY), "right_bumper": act(EMPTY)})}})
        needed = audit(data, {"targets": {}})["targets"]["Win"]["blocks_needed"]
        self.assertEqual([(b["input"], b["action"], b["activators"]) for b in needed], [("click", "clear", None)])


class ChainStackTests(unittest.TestCase):
    """Stacks come from the backward chains (steam_layout/chains.py): no depth cap and no config."""

    def test_a_window_no_stack_reaches_is_not_checked_and_fails(self):
        report = audit(build({"Base": {}, "Win": {"switch": ("switches", AOA)}}), {"targets": {}})
        row = report["targets"]["Win"]
        self.assertEqual(row["stacks"], 0)
        self.assertFalse(row["checked"])
        self.assertFalse(report["ok"])

    def test_chains_check_a_window_three_inputs_deep_with_no_depth(self):
        report = audit(deep_window(), {"targets": {}})
        row = report["targets"]["Win"]
        self.assertTrue(row["checked"])
        self.assertEqual((row["stacks"], row["chain_stacks"]), (1, 1))
        self.assertEqual({(r["source"], r["input"], r["from_layer"], tuple(r["stack"])) for r in row["routes"]},
                         {("switch", "button_y", "Owner", ("Base", "Mode", "Owner"))})
        self.assertEqual([(b["input"], b["action"]) for b in row["blocks_needed"]], [("button_y", "clear")])
        self.assertFalse(report["ok"])

    def test_each_route_carries_the_reason_for_its_stack(self):
        route = audit(deep_window(), {"targets": {}})["targets"]["Win"]["routes"][0]
        self.assertEqual(route["reason"], ["Base switch/button_a Full_Press#0: +Mode",
                                           "Mode switch/button_b Full_Press#0: +Owner",
                                           "Owner switch/button_x Full_Press#0: +Win"])

    def test_a_route_through_a_bystander_names_it(self):
        routes = audit(bystander_window(), {"targets": {}})["targets"]["Win"]["routes"]
        self.assertEqual([(r["input"], r["from_layer"], tuple(r["stack"])) for r in routes],
                         [("button_2", "L60", ("Base", "EP", "L60"))])
        self.assertEqual(routes[0]["reason"], ["Base switch/button_1 Full_Press#0: +L70",
                                               "L70 switch/button_4 Full_Press#0: -L70 ; +Win",
                                               "bystander: L60"])

    def test_a_declared_stack_says_so(self):
        data = build({"Base": {"switch": ("switches", {"button_a": act(add("Mod"))})}, "Mod": {}, "Win": {}})
        route = audit(data, config([["Base"]]))["targets"]["Win"]["routes"][0]
        self.assertEqual(route["reason"], ["declared in the config"])


class ConfigTests(unittest.TestCase):
    def test_unknown_layer_in_a_stack_is_an_error(self):
        with self.assertRaises(ValueError):
            audit(build({"Base": {}, "Win": {}}), config([["Base", "Nope"]]))

    def test_alternative_titles_map_l1_r1_to_l2_r2(self):
        mapping = {"L1": "L2", "R1": "R2"}
        self.assertEqual(map_title("Gyro | L1!R1: Modifier 2", mapping), "Gyro | L2!R2: Modifier 2")
        self.assertEqual(map_title("L1&R1: Tap Cover", mapping), "L2&R2: Tap Cover")
        self.assertEqual(map_title("Menu Left: Double Tap", mapping), "Menu Left: Double Tap")
        data = build({"Base": {"switch": ("switches", {"left_trigger": act(add("L2: Modifier 0"))})},
                      "L2: Modifier 0": {}, "L2: Double Tap": {}})
        data["controller_mappings"]["title"] = "single-set-alternative :: test :: 1"
        cfg = {"variants": {"alternative": {"L1": "L2", "R1": "R2"}},
               "targets": {"L1: Double Tap": {"stacks": [{"layers": ["Base"], "why": "t"}], "decisions": []}}}
        report = audit(data, cfg)
        self.assertEqual(report["variant"], "alternative")
        self.assertIn("L2: Double Tap", report["targets"])


class EntriesTests(unittest.TestCase):
    def test_lists_adds_with_removals_that_run_first(self):
        data = build({"Base": {"switch": ("switches", {"button_a": act([
            add("Win"), remove("Mod"), remove("Gyro | Mod")])})},
                      "Mod": {"switch": ("switches", {"button_b": {"release": {"bindings": {"binding": [
                          remove("Other"), add("Win")]}}}})},
                      "Gyro | Mod": {}, "Other": {}, "Win": {}})
        rows = entries(data, "Win")
        self.assertEqual([(r["layer"], r["input"], r["activation"], r["removes_first"]) for r in rows],
                         [("Base", "button_a", "Full_Press", ["Gyro | Mod", "Mod"]),
                          ("Mod", "button_b", "release", [])])


if __name__ == "__main__":
    unittest.main()
