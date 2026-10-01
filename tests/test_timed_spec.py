"""Strict, lossless runtime specification parsing and shift discovery."""
from copy import deepcopy
from dataclasses import FrozenInstanceError
from decimal import Decimal
import json
from pathlib import Path
import unittest

from steam_layout.model import Layout
from steam_layout.timed_spec import TimedSpec, canonical_control, chord_selectors
from test_audit_inheritance import EMPTY, act, add, build, remove

ROOT = Path(__file__).resolve().parents[1]
LB = ("switch", "left_bumper")


def simple(activators):
    return build({"Base": {"switch": ("switches", {"left_bumper": activators})}, "A": {}, "B": {}})


def one(activators, **kwargs):
    return TimedSpec(Layout(simple(activators)), **kwargs).bindings[(0, LB)][0]


class TimedSpecTests(unittest.TestCase):
    def test_milliseconds_threshold_and_execution_order_are_preserved(self):
        spec = one(act([add("A"), remove("B")], delay_start="300", delay_end="50",
                       hold_repeats="1", repeat_rate="350", interruptable="0",
                       activation_threshold="26610.25", edge_binding_invert="1"))
        self.assertEqual((spec.delay_start_ms, spec.delay_end_ms, spec.repeat_ms), (300, 50, 350))
        self.assertEqual(spec.threshold, Decimal("26610.25"))
        self.assertFalse(spec.interruptible)
        self.assertTrue(spec.invert)
        self.assertEqual(spec.ops, (("r", 2), ("a", 1)))
        self.assertEqual(dict(spec.settings)["delay_start"], "300")
        with self.assertRaises(FrozenInstanceError):
            spec.delay_start_ms = 5

    def test_missing_repeat_rate_needs_explicit_default(self):
        activators = act(add("A"), hold_repeats="1")
        with self.assertRaisesRegex(ValueError, "hold_repeats has no repeat_rate"):
            one(activators)
        self.assertEqual(one(activators, default_repeat_ms=137).repeat_ms, 137)
        self.assertIsNone(one(act(add("A")), default_repeat_ms=137).repeat_ms)

    def test_explicit_rate_takes_precedence_over_default(self):
        self.assertEqual(one(act(add("A"), hold_repeats="1", repeat_rate="250"),
                             default_repeat_ms=137).repeat_ms, 250)

    def test_reject_invalid_timing_values_with_entry_location(self):
        for setting in ({"delay_start": "1.5"}, {"delay_start": "-1"},
                        {"delay_end": "NaN"}, {"delay_end": True},
                        {"hold_repeats": "1", "repeat_rate": "0"},
                        {"hold_repeats": "true"}, {"repeat_delay": "100"}):
            with self.subTest(setting=setting), self.assertRaisesRegex(ValueError, "left_bumper"):
                one(act(add("A"), **setting))
        for value in (0, -1, "1.5", True):
            with self.subTest(default=value), self.assertRaisesRegex(ValueError, "default_repeat_ms"):
                one(act(add("A")), default_repeat_ms=value)

    def test_unknown_activator_is_not_coerced_to_regular_press(self):
        with self.assertRaisesRegex(ValueError, "unsupported activator kind 'Long_Press'"):
            one({"Long_Press": {"bindings": {"binding": add("A")}}})

    def test_hold_layer_ignored_only_with_explicit_flag_preserving_other_commands(self):
        hold = "controller_action hold_layer {{Base::A}} 0 0, , "
        data = simple(act([hold, add("B")]))
        with self.assertRaisesRegex(ValueError, "hold_layer is excluded"):
            TimedSpec(Layout(data))
        model = TimedSpec(Layout(data), ignore_hold_bindings=True)
        spec = model.bindings[(0, LB)][0]
        self.assertEqual(spec.ops, (("a", 2),))
        self.assertEqual(model.ignored_hold_commands, ((spec.id, hold),))

    def test_hold_only_binding_still_overrides_a_lower_binding(self):
        hold = "controller_action hold_layer {{Base::B}} 0 0, , "
        data = build({"Base": {"switch": ("switches", {"left_bumper": act(add("B"))})},
                      "A": {"switch": ("switches", {"left_bumper": act(hold)})}, "B": {}})
        model = TimedSpec(Layout(data), ignore_hold_bindings=True)
        self.assertIn((1, LB), model.bindings)
        self.assertFalse(model.bindings[(1, LB)][0].ops)

    def test_action_set_switching_and_multiple_sets_rejected(self):
        with self.assertRaisesRegex(ValueError, "CHANGE_PRESET"):
            one(act("controller_action CHANGE_PRESET 2 0 0, , "))
        data = simple(act(EMPTY))
        key, value = next(iter(data["controller_mappings"]["action_layers"].items()))
        data["controller_mappings"]["actions"][key] = value
        del data["controller_mappings"]["action_layers"][key]
        with self.assertRaisesRegex(ValueError, "exactly one Base action set"):
            TimedSpec(Layout(data))

    def test_dangling_and_malformed_layer_targets_rejected(self):
        for target in ("{{Base::Missing}}", "99", "0", "2junk", "not_a_target"):
            with self.subTest(target=target), self.assertRaisesRegex(ValueError, "layer"):
                one(act(f"controller_action add_layer {target} 0 0, , "))
        self.assertEqual(one(act("controller_action add_layer 2 0 0, , ")).ops, (("a", 1),))

    def test_fingerprint_matches_across_owners_but_keeps_nonlayer_outputs(self):
        binding = act([add("B"), "key_press A, , "], delay_start="300")
        data = build({"Base": {"switch": ("switches", {"left_bumper": binding})},
                      "A": {"switch": ("switches", {"left_bumper": deepcopy(binding)})}, "B": {}})
        model = TimedSpec(Layout(data))
        first, second = model.bindings[(0, LB)][0], model.bindings[(1, LB)][0]
        self.assertNotEqual(first.id, second.id)
        self.assertEqual(first.fingerprint, second.fingerprint)
        changed = one(act([add("B"), "key_press B, , "], delay_start="300"))
        self.assertNotEqual(first.fingerprint, changed.fingerprint)
        self.assertEqual(first.id, TimedSpec(Layout(deepcopy(data))).bindings[(0, LB)][0].id)

    def test_distinct_entries_keep_distinct_ids_even_if_identical(self):
        entry = {"bindings": {"binding": add("A")}, "settings": {"delay_start": "300"}}
        model = TimedSpec(Layout(simple({"Full_Press": [entry, deepcopy(entry)]})))
        first, second = model.bindings[(0, LB)]
        self.assertNotEqual(first.id, second.id)
        self.assertEqual(first.fingerprint, second.fingerprint)

    def test_mode_shift_uses_command_source_and_includes_shift_only_controls(self):
        data = build({"Base": {"switch": ("switches", {"left_bumper": act("mode_shift joystick 90, , ")})},
                      "A": {}}, modeshift={"90": ("right_trackpad", "dpad", {
                          "dpad_north": act(add("A"))})})
        # No inactive preset lookup is needed to discover the target source.
        del data["controller_mappings"]["preset"][0]["group_source_bindings"]["90"]
        model = TimedSpec(Layout(data))
        self.assertEqual(model.bindings[(0, LB)][0].shifts, (("joystick", "90"),))
        self.assertIn(("joystick", "dpad_north"), model.controls)
        shifted = model.shifts_by_group[("joystick", "90")][("joystick", "dpad_north")][0]
        self.assertEqual(shifted.owner, "shift:joystick:90")
        self.assertEqual(shifted.ops, (("a", 1),))

    def test_nested_and_cyclic_mode_shifts_discovered_once(self):
        data = build({"Base": {"switch": ("switches", {"left_bumper": act("mode_shift joystick 90, , ")})}},
                     modeshift={"90": ("joystick", "dpad", {"click": act("mode_shift right_joystick 91, , ")}),
                                "91": ("right_joystick", "dpad", {"click": act("mode_shift joystick 90, , ")})})
        model = TimedSpec(Layout(data))
        self.assertEqual(set(model.shifts_by_group), {("joystick", "90"), ("right_joystick", "91")})
        self.assertEqual(len(model.entries), 3)

    def test_dangling_mode_shift_rejected(self):
        with self.assertRaisesRegex(ValueError, "dangling mode-shift group"):
            one(act("mode_shift joystick 999, , "))

    def test_disabled_source_blocks_but_empty_activators_do_not(self):
        data = build({"Base": {"joystick": ("dpad", {"click": act(EMPTY)})},
                      "A": {"joystick": ("disabled", {})},
                      "B": {"joystick": ("dpad", {"click": {}})}})
        model = TimedSpec(Layout(data))
        self.assertEqual(model.blocked[1], frozenset({"joystick"}))
        self.assertIn((0, ("joystick", "click")), model.bindings)
        self.assertNotIn((2, ("joystick", "click")), model.bindings)

    def test_chords_add_controls_even_without_bindings(self):
        entry = {"bindings": {"binding": add("A")}, "settings": {"chord_button": "19"}}
        model = TimedSpec(Layout(simple({"chord": entry})))
        self.assertIn(("right_trackpad", "click"), model.controls)
        self.assertEqual(dict(model.bindings[(0, LB)][0].chord), {"chord_button": "19"})
        entry["settings"] = {"gyro_ratchet_button_mask": str((1 << 30) | (1 << 47)),
                             "gyro_ratchet_button_requireany_or_all": "1"}
        model = TimedSpec(Layout(simple({"chord": entry})))
        self.assertIn(("joystick", "edge"), model.controls)
        self.assertIn(("right_joystick", "touch"), model.controls)
        self.assertTrue(chord_selectors(entry["settings"])[0])

    def test_unknown_chord_encoding_never_silently_satisfied(self):
        for settings in ({}, {"chord_button": "999"}, {"gyro_ratchet_button_mask": "0"},
                         {"gyro_ratchet_button_mask": str(1 << 63)},
                         {"chord_button": "1", "gyro_ratchet_button_mask": "8"}):
            with self.subTest(settings=settings), self.assertRaisesRegex(ValueError, "chord"):
                one({"chord": {"bindings": {"binding": add("A")}, "settings": settings}})

    def test_threshold_is_not_inferred_from_group_settings(self):
        data = simple(act(add("A"), edge_binding_invert="1"))
        data["controller_mappings"]["group"][0]["settings"] = {"activation_threshold": "20000"}
        self.assertIsNone(TimedSpec(Layout(data)).bindings[(0, LB)][0].threshold)

    def test_physical_switch_aliases(self):
        self.assertEqual(canonical_control(("switch", "right_trackpad_touch")), ("right_trackpad", "touch"))
        self.assertEqual(canonical_control(("switch", "left_stick_click")), ("joystick", "click"))
        self.assertEqual(canonical_control(LB), LB)

    def test_current_variants_parse_with_explicit_assumed_repeat_rate_and_ignored_holds(self):
        for variant in ("default", "alternative"):
            with self.subTest(variant=variant):
                layout = Layout(json.loads((ROOT / f"neptune/single-set-{variant}_hold-gyro_latest.json").read_text()))
                model = TimedSpec(layout, ignore_hold_bindings=True, default_repeat_ms=137)
                self.assertEqual(len(model.ignored_hold_commands), 5)
                self.assertEqual(len(model.shifts_by_group), 6)
                self.assertTrue(model.entries)
                self.assertTrue(any(e.repeat_ms == 137 for e in model.entries.values()))


if __name__ == "__main__":
    unittest.main()
