"""Inheritance/blocking audit (Layer Definition of Done, section 8)."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from audit_inheritance import Layout, audit, entries, explore, map_title

ROOT = Path(__file__).resolve().parents[1]
EMPTY = "controller_action empty_binding, , "


def act(binding, **settings):
    return {"Full_Press": {"bindings": {"binding": binding}, "settings": settings}}


def add(title):
    return f"controller_action add_layer {{{{Base::{title}}}}} 0 0, , "


def remove(title):
    return f"controller_action remove_layer {{{{Base::{title}}}}} 0 0, , "


def build(layers, modeshift=None):
    """layers: {title: {source: (mode, {input: activators})}}; the first title is the action set."""
    cm = {"title": "single-set-default :: test :: 1", "actions": {}, "action_layers": {},
          "preset": [], "group": []}
    gid = 0
    for index, (title, sources) in enumerate(layers.items()):
        key = f"Preset_{1000001 + index}"
        (cm["actions"] if index == 0 else cm["action_layers"])[key] = {"title": title}
        bindings = {}
        for source, (mode, inputs) in sources.items():
            gid += 1
            cm["group"].append({"id": str(gid), "mode": mode,
                                "inputs": {name: {"activators": a} for name, a in inputs.items()}})
            bindings[str(gid)] = f"{source} active"
        cm["preset"].append({"id": str(index), "name": key, "group_source_bindings": bindings})
    for group_id, (source, mode, inputs) in (modeshift or {}).items():
        cm["group"].append({"id": group_id, "mode": mode,
                            "inputs": {name: {"activators": a} for name, a in inputs.items()}})
        cm["preset"][0]["group_source_bindings"][group_id] = f"{source} inactive modeshift"
    return {"controller_mappings": cm}


def config(stacks, decisions=()):
    return {"variants": {"alternative": {"L1": "L2", "R1": "R2"}},
            "targets": {"Win": {"stacks": [{"layers": s, "why": "test"} for s in stacks],
                                "decisions": list(decisions)}}}


def routes(report, status=None):
    rows = report["targets"]["Win"]["routes"]
    return {(r["source"], r["input"]) for r in rows if status is None or r["status"] == status}


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

    def test_a_different_source_mode_above_the_definer_is_flagged_not_trusted(self):
        data = build({"Base": {"right_trackpad": ("absolute_mouse", {"touch": act(add("Mod"))})},
                      "Mod": {}, "Win": {"right_trackpad": ("dpad", {"dpad_north": act(EMPTY)})}})
        report = audit(data, config([["Base"]]))
        self.assertEqual(routes(report, "mode_replaced"), {("right_trackpad", "touch")})
        self.assertFalse(report["ok"])

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


def release(binding):
    return {"release": {"bindings": {"binding": binding}}}


class ExploreTests(unittest.TestCase):
    """Stacks below a layer are derived from the layout's own transitions."""

    def below(self, data, title, depth=5):
        return set(explore(Layout(data), depth)["below"].get(title, {}))

    def test_window_entry_removes_the_parent_first(self):
        data = build({"Base": {"switch": ("switches", {"left_bumper": act(add("Mod"))})},
                      "Mod": {"switch": ("switches", {"left_bumper": release([add("Win"), remove("Mod")])})},
                      "Win": {}})
        self.assertEqual(self.below(data, "Win"), {("Base",)})

    def test_every_context_the_parent_can_be_in_is_found(self):
        data = build({"Base": {"switch": ("switches", {"left_bumper": act(add("Mod")),
                                                       "button_a": act(add("Gyro"))})},
                      "Gyro": {},
                      "Mod": {"switch": ("switches", {"left_bumper": release([add("Win"), remove("Mod")])})},
                      "Win": {}})
        self.assertEqual(self.below(data, "Win"), {("Base",), ("Base", "Gyro")})

    def test_an_upper_override_stops_lower_transitions(self):
        data = build({"Base": {"switch": ("switches", {"button_a": act(add("Cover")),
                                                       "button_b": act(add("Win"))})},
                      "Cover": {"switch": ("switches", {"button_b": act("key_press B, , ")})},
                      "Win": {}})
        self.assertEqual(self.below(data, "Win"), {("Base",)})

    def test_disabled_source_stops_lower_transitions(self):
        data = build({"Base": {"right_trackpad": ("absolute_mouse", {"touch": act(add("Win"))}),
                               "switch": ("switches", {"button_a": act(add("Quiet"))})},
                      "Quiet": {"right_trackpad": ("disabled", {})},
                      "Win": {}})
        self.assertEqual(self.below(data, "Win"), {("Base",)})

    def test_reapplying_an_active_layer_does_not_reorder_it(self):
        data = build({"Base": {"switch": ("switches", {"button_a": act(add("A"))})},
                      "A": {"switch": ("switches", {"button_b": act(add("B"))})},
                      "B": {"switch": ("switches", {"button_x": act([add("Win"), add("A")])})},
                      "Win": {}})
        self.assertEqual(self.below(data, "Win"), {("Base", "A", "B")})

    def test_hold_layer_can_be_released_and_mode_shift_groups_can_fire(self):
        data = build({"Base": {"left_trackpad": ("absolute_mouse", {"click": act("controller_action hold_layer {{Base::Held}} 0 0, , ")}),
                               "joystick": ("joystick_mouse", {"click": act("mode_shift joystick 90, , ")})},
                      "Held": {}, "Win": {}},
                     modeshift={"90": ("joystick", "dpad", {"dpad_north": act(add("Win"))})})
        self.assertEqual(self.below(data, "Win"), {("Base",), ("Base", "Held")})

    def test_depth_limits_the_search(self):
        chain = {"Base": {"switch": ("switches", {"button_a": act(add("A"))})},
                 "A": {"switch": ("switches", {"button_a": act([add("B"), remove("A")])})},
                 "B": {"switch": ("switches", {"button_a": act([add("Win"), remove("B")])})},
                 "Win": {}}
        self.assertEqual(self.below(build(chain), "Win", depth=2), set())
        self.assertEqual(self.below(build(chain), "Win", depth=3), {("Base",)})


class DerivedAuditTests(unittest.TestCase):
    def test_always_on_layers_are_audited_from_derived_stacks_without_config(self):
        data = build({"Base": {"switch": ("switches", {"left_bumper": act(add("Ramp")),
                                                       "right_bumper": act(add("Win"))}),
                               "left_trigger": ("trigger", {"edge": act("mouse_button LEFT, , ")})},
                      "Ramp": {"left_trigger": ("trigger", {"edge": act([remove("Ramp"), "mouse_button LEFT, , "])})},
                      "Win": {"switch": ("switches", {"always_on_action": act(remove("Win")),
                                                      "left_bumper": act(EMPTY), "right_bumper": act(EMPTY)})}})
        report = audit(data, {"targets": {}}, depth=4)
        row = report["targets"]["Win"]
        self.assertEqual({(r["source"], r["input"], r["from_layer"]) for r in row["routes"]},
                         {("left_trigger", "edge", "Ramp")})
        self.assertTrue(row["saturated"])
        self.assertFalse(report["ok"])
        self.assertEqual(row["blocks_needed"], [{
            "source": "left_trigger", "input": "edge", "action": "replace", "stacks": 2,
            "activators": {"Full_Press": {"bindings": {"binding": "mouse_button LEFT, , "}, "settings": {}}}}])

    def test_varying_underlying_binds_must_be_cleared(self):
        data = build({"Base": {"switch": ("switches", {"left_bumper": act(add("Mod")),
                                                       "right_bumper": act(add("Win"))}),
                               "joystick": ("dpad", {"click": act("key_press Q, , ")})},
                      "Mod": {"joystick": ("dpad", {"click": act([add("Mod"), "mouse_button MIDDLE, , "])})},
                      "Win": {"switch": ("switches", {"always_on_action": act(remove("Win")),
                                                      "left_bumper": act(EMPTY), "right_bumper": act(EMPTY)})}})
        needed = audit(data, {"targets": {}}, depth=4)["targets"]["Win"]["blocks_needed"]
        self.assertEqual([(b["input"], b["action"], b["activators"]) for b in needed], [("click", "clear", None)])

    def test_routes_found_only_at_the_depth_limit_mean_not_saturated(self):
        chain = build({"Base": {"switch": ("switches", {"button_a": act(add("A")), "button_b": act(add("Win"))})},
                       "A": {"switch": ("switches", {"button_a": act([add("B"), remove("A")])})},
                       "B": {"switch": ("switches", {"button_x": act(remove("B"))})},
                       "Win": {"switch": ("switches", {"always_on_action": act(remove("Win")),
                                                       "button_a": act(EMPTY), "button_b": act(EMPTY)})}})
        shallow = audit(chain, {"targets": {}}, depth=3)["targets"]["Win"]
        self.assertFalse(shallow["saturated"])
        self.assertTrue(audit(chain, {"targets": {}}, depth=5)["targets"]["Win"]["saturated"])


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


class CliTests(unittest.TestCase):
    def run_cli(self, data, cfg, *extra):
        with tempfile.TemporaryDirectory() as tmp:
            layout, stacks = Path(tmp, "l.json"), Path(tmp, "s.json")
            layout.write_text(json.dumps(data))
            stacks.write_text(json.dumps(cfg))
            return subprocess.run([sys.executable, str(ROOT / "audit_inheritance.py"), str(layout),
                                   "--stacks", str(stacks), *extra], capture_output=True, text=True)

    def test_exit_codes(self):
        clean = build({"Base": {}, "Win": {}})
        leaky = build({"Base": {"switch": ("switches", {"button_a": act(add("Win"))})}, "Win": {}})
        self.assertEqual(self.run_cli(clean, config([["Base"]])).returncode, 0)
        self.assertEqual(self.run_cli(leaky, config([["Base"]])).returncode, 1)
        self.assertEqual(self.run_cli(clean, config([["Base", "Nope"]])).returncode, 2)
        out = self.run_cli(leaky, config([["Base"]]), "--entries", "Win")
        self.assertEqual(out.returncode, 0)
        self.assertIn("button_a", out.stdout)


class NeptuneLayoutTests(unittest.TestCase):
    """The committed traced stacks cover every Always On layer with every route decided."""

    def test_working_layouts_have_no_undecided_routes(self):
        cfg = json.loads((ROOT / "traced_stacks.json").read_text())
        for variant in ("default", "alternative"):
            data = json.loads((ROOT / f"neptune/single-set-{variant}_hold-gyro_latest.json").read_text())
            with self.subTest(variant=variant):
                report = audit(data, cfg)
                self.assertEqual(report["variant"], variant)
                self.assertEqual(len(report["targets"]), 7)
                self.assertTrue(all(row["saturated"] for row in report["targets"].values()))
                undecided = [(t, r["source"], r["input"], r["status"]) for t, row in report["targets"].items()
                             for r in row["routes"] if r["status"] in ("open", "mode_replaced")]
                self.assertEqual(undecided, [])
                self.assertTrue(report["ok"])

    def test_removing_a_window_block_is_caught(self):
        cfg = json.loads((ROOT / "traced_stacks.json").read_text())
        data = json.loads((ROOT / "neptune/single-set-default_hold-gyro_latest.json").read_text())
        cm = data["controller_mappings"]
        key = next(k for k, v in cm["action_layers"].items() if v["title"] == "Menu Left: Double Tap")
        preset = next(p for p in cm["preset"] if p["name"] == key)
        gid = next(g for g, s in preset["group_source_bindings"].items() if s == "right_joystick active")
        del next(g for g in cm["group"] if g["id"] == gid)["inputs"]["edge"]
        report = audit(data, cfg)
        self.assertFalse(report["ok"])
        self.assertIn(("right_joystick", "edge", "open"),
                      {(r["source"], r["input"], r["status"])
                       for r in report["targets"]["Menu Left: Double Tap"]["routes"]})


if __name__ == "__main__":
    unittest.main()
