"""Independent runtime expectations for timed layer commands and held inputs."""
from itertools import permutations
import unittest

from steam_layout.model import Layout
from steam_layout.timed_model import TimedModel
from test_audit_inheritance import EMPTY, act, add, build, remove


LB = ("switch", "left_bumper")
RB = ("switch", "right_bumper")


def entry(binding, **settings):
    return {"bindings": {"binding": binding}, "settings": settings}


def switches(inputs):
    return {"switch": ("switches", inputs)}


class TimedModelTests(unittest.TestCase):
    def model(self, layers, shifts=None):
        return TimedModel(Layout(build(layers, modeshift=shifts)))

    def one(self, states):
        self.assertEqual(len(states), 1)
        return next(iter(states))

    def stack(self, model, state):
        return model.names_of(state.stack)

    def test_independent_100_and_500_ms_deadlines_fire_once(self):
        model = self.model({"Base": switches({"left_bumper": {"Full_Press": [
            entry(add("Early"), delay_start="100"), entry(add("Late"), delay_start="500")
        ]}}), "Early": {}, "Late": {}})
        state = self.one(model.press(self.one(model.start()), LB))
        self.assertEqual(sorted(a.deadline_ms for a in state.activations), [100, 500])
        state = self.one(model.wait(state, 99))
        self.assertEqual(self.stack(model, state), ("Base",))
        state = self.one(model.wait(state, 1))
        self.assertEqual(self.stack(model, state), ("Base", "Early"))
        state = self.one(model.wait(state, 399))
        self.assertEqual(self.stack(model, state), ("Base", "Early"))
        state = self.one(model.wait(state, 1))
        self.assertEqual(self.stack(model, state), ("Base", "Early", "Late"))
        self.assertTrue(all(a.fired and a.deadline_ms is None for a in state.activations))
        after = self.one(model.wait(state, 1000))
        self.assertEqual(after.stack, state.stack)
        self.assertEqual(after.activations, state.activations)
        self.assertEqual(after.now_ms, 1500)

    def test_removal_at_200_restarts_300_ms_delay_even_for_absent_target(self):
        for present in (False, True):
            with self.subTest(target_present=present):
                inputs = {"left_bumper": act(add("Late"), delay_start="300"),
                          "right_bumper": act(remove("Other"))}
                if present:
                    inputs["always_on_action"] = act(add("Other"))
                model = self.model({"Base": switches(inputs), "Late": {}, "Other": {}})
                state = self.one(model.press(self.one(model.start()), LB))
                state = self.one(model.wait(state, 200))
                state = self.one(model.press(state, RB))
                self.assertEqual(self.stack(model, state), ("Base",))
                delayed = [a for a in state.activations if a.deadline_ms is not None]
                self.assertEqual([a.deadline_ms for a in delayed], [500])
                state = self.one(model.wait(state, 299))
                self.assertEqual(self.stack(model, state), ("Base",))
                state = self.one(model.wait(state, 1))
                self.assertEqual(self.stack(model, state), ("Base", "Late"))

    def test_removing_completed_delayed_add_target_rearms_it(self):
        model = self.model({"Base": switches({
            "left_bumper": act(add("Late"), delay_start="300"),
            "right_bumper": act(remove("Late"))}), "Late": {}})
        state = self.one(model.press(self.one(model.start()), LB))
        state = self.one(model.wait(state, 300))
        self.assertEqual(self.stack(model, state), ("Base", "Late"))
        state = self.one(model.press(state, RB))
        self.assertEqual(self.stack(model, state), ("Base",))
        state = self.one(model.wait(state, 299))
        self.assertEqual(self.stack(model, state), ("Base",))
        state = self.one(model.wait(state, 1))
        self.assertEqual((state.now_ms, self.stack(model, state)), (600, ("Base", "Late")))

    def test_unrelated_removal_preserves_repeat_clock(self):
        model = self.model({"Base": switches({
            "left_bumper": act(add("Repeated"), hold_repeats="1", repeat_rate="100"),
            "right_bumper": act(remove("Other"))}), "Repeated": {}, "Other": {}})
        state = self.one(model.press(self.one(model.start()), LB))
        state = self.one(model.wait(state, 50))
        state = self.one(model.press(state, RB))
        repeating = [a for a in state.activations if a.stage == "repeat"]
        self.assertEqual([a.deadline_ms for a in repeating], [100])
        state = self.one(model.wait(state, 50))
        repeating = [a for a in state.activations if a.stage == "repeat"]
        self.assertEqual([a.deadline_ms for a in repeating], [200])

    def test_four_simultaneous_entries_preserve_all_24_orders(self):
        names = ("A", "B", "C", "D")
        model = self.model({"Base": switches({"left_bumper": {"Full_Press": [
            entry(add(name), delay_start="100") for name in names
        ]}}), **{name: {} for name in names}})
        state = self.one(model.press(self.one(model.start()), LB))
        states = model.wait(state, 100)
        self.assertEqual(len(states), 24)
        self.assertEqual({self.stack(model, result) for result in states},
                         {("Base", *order) for order in permutations(names)})

    def test_exposed_held_input_suppresses_immediate_and_starts_delay_and_repeat(self):
        model = self.model({
            "Base": switches({"left_bumper": act(EMPTY), "right_bumper": act(add("Upper"))}),
            "Upper": switches({"left_bumper": {"Full_Press": [
                entry(add("Immediate")), entry(add("Delayed"), delay_start="300"),
                entry(add("Repeated"), hold_repeats="1", repeat_rate="100")
            ]}}), "Immediate": {}, "Delayed": {}, "Repeated": {}})
        state = self.one(model.press(self.one(model.start()), LB))
        state = self.one(model.wait(state, 25))
        state = self.one(model.press(state, RB))
        self.assertEqual(self.stack(model, state), ("Base", "Upper"))
        self.assertEqual(sorted(a.deadline_ms for a in state.activations if a.deadline_ms is not None),
                         [125, 325])
        state = self.one(model.wait(state, 99))
        self.assertEqual(self.stack(model, state), ("Base", "Upper"))
        state = self.one(model.wait(state, 1))
        self.assertEqual(self.stack(model, state), ("Base", "Upper", "Repeated"))
        state = self.one(model.wait(state, 200))
        self.assertEqual(self.stack(model, state), ("Base", "Upper", "Repeated", "Delayed"))
        state = self.one(model.release(state, LB))
        states = model.press(state, LB)
        self.assertTrue(all("Immediate" in self.stack(model, result) for result in states))

    def test_release_uses_current_binding_after_layer_override(self):
        model = self.model({
            "Base": switches({"left_bumper": {**act(add("Upper")),
                "release": entry(add("Wrong"))}}),
            "Upper": switches({"left_bumper": {"release": entry([add("Right"), remove("Upper")])}}),
            "Right": {}, "Wrong": {}})
        state = self.one(model.press(self.one(model.start()), LB))
        self.assertEqual(self.stack(model, state), ("Base", "Upper"))
        state = self.one(model.release(state, LB))
        self.assertEqual(self.stack(model, state), ("Base", "Right"))
        self.assertFalse(state.held)

    def test_identical_binding_preserves_clock_when_owner_changes(self):
        binding = act(add("Late"), delay_start="300")
        model = self.model({"Base": switches({"left_bumper": binding,
                                               "right_bumper": act(add("Upper"))}),
                            "Upper": switches({"left_bumper": binding}), "Late": {}})
        state = self.one(model.press(self.one(model.start()), LB))
        original_id = state.activations[0].entry_id
        state = self.one(model.wait(state, 200))
        state = self.one(model.press(state, RB))
        delayed = [a for a in state.activations if a.deadline_ms is not None]
        self.assertEqual([a.deadline_ms for a in delayed], [300])
        self.assertNotEqual(delayed[0].entry_id, original_id)
        state = self.one(model.wait(state, 99))
        self.assertEqual(self.stack(model, state), ("Base", "Upper"))
        state = self.one(model.wait(state, 1))
        self.assertEqual(self.stack(model, state), ("Base", "Upper", "Late"))

    def test_chord_blocks_regular_until_its_condition_ends(self):
        model = self.model({"Base": switches({"left_bumper": {
            **act(add("Regular")), "chord": entry(add("Chord"), chord_button="2")
        }, "right_bumper": act(EMPTY)}), "Regular": {}, "Chord": {}})
        state = self.one(model.press(self.one(model.start()), RB))
        state = self.one(model.press(state, LB))
        self.assertEqual(self.stack(model, state), ("Base", "Chord"))
        state = self.one(model.release(state, RB))
        self.assertEqual(self.stack(model, state), ("Base", "Chord", "Regular"))
        self.assertEqual(state.held, frozenset({LB}))

    def test_noninterruptible_regular_fires_alongside_chord(self):
        model = self.model({"Base": switches({"left_bumper": {
            **act(add("Regular"), interruptable="0"),
            "chord": entry(add("Chord"), chord_button="2")
        }, "right_bumper": act(EMPTY)}), "Regular": {}, "Chord": {}})
        state = self.one(model.press(self.one(model.start()), RB))
        states = model.press(state, LB)
        self.assertEqual({self.stack(model, result) for result in states},
                         {("Base", "Regular", "Chord"), ("Base", "Chord", "Regular")})

    def test_mode_shift_latches_across_binding_override_and_ends_on_release(self):
        north = ("joystick", "dpad_north")
        model = self.model({
            "Base": switches({"left_bumper": act("mode_shift joystick 90, , "),
                              "right_bumper": act(add("Upper"))}),
            "Upper": switches({"left_bumper": act(EMPTY)}), "Shifted": {}},
            shifts={"90": ("joystick", "dpad", {"dpad_north": act(add("Shifted"))})})
        self.assertIn(north, model.controls)
        state = self.one(model.press(self.one(model.start()), LB))
        self.assertEqual(len(state.shifts), 1)
        state = self.one(model.press(state, RB))
        self.assertEqual(len(state.shifts), 1)
        state = self.one(model.press(state, north))
        self.assertEqual(self.stack(model, state), ("Base", "Upper", "Shifted"))
        state = self.one(model.release(state, north))
        state = self.one(model.release(state, LB))
        self.assertFalse(state.shifts)
        # Shift-only inputs stay physical controls, but no binding is selected now.
        state = self.one(model.press(state, north))
        self.assertFalse(state.shifts)
        self.assertEqual(self.stack(model, state), ("Base", "Upper", "Shifted"))

    def test_chord_mode_shift_ends_when_selector_is_released(self):
        model = self.model({"Base": switches({"left_bumper": {
            "chord": entry("mode_shift joystick 90, , ", chord_button="2")
        }, "right_bumper": act(EMPTY)})},
            shifts={"90": ("joystick", "dpad", {"dpad_north": act(EMPTY)})})
        state = self.one(model.press(self.one(model.start()), RB))
        state = self.one(model.press(state, LB))
        self.assertEqual(len(state.shifts), 1)
        state = self.one(model.release(state, RB))
        self.assertFalse(state.shifts)
        self.assertEqual(state.held, frozenset({LB}))

    def test_switch_alias_and_pad_touch_are_one_physical_control(self):
        touch = ("left_trackpad", "touch")
        alias = ("switch", "left_trackpad_touch")
        model = self.model({"Base": {
            **switches({"left_trackpad_touch": act(add("Touched"))}),
            "left_trackpad": ("dpad", {"touch": act(EMPTY)})}, "Touched": {}})
        for control in (alias, touch):
            with self.subTest(control=control):
                state = self.one(model.press(self.one(model.start()), control))
                self.assertEqual(state.held, frozenset({touch}))
                self.assertEqual(self.stack(model, state), ("Base", "Touched"))
                with self.assertRaisesRegex(ValueError, "already held"):
                    model.press(state, alias)
                state = self.one(model.release(state, touch))
                self.assertFalse(state.held)

    def test_raw_analog_threshold_and_inverted_equality_are_complementary(self):
        edge = ("right_trackpad", "edge")
        model = self.model({"Base": {"right_trackpad": ("dpad", {"edge": {"Soft_Press": [
            entry(add("Outside"), activation_threshold="26610"),
            entry(remove("Outside"), activation_threshold="26610", edge_binding_invert="1")
        ]}})}, "Outside": {}})
        state = self.one(model.start())
        state = self.one(model.analog(state, edge, "26610"))
        self.assertEqual(self.stack(model, state), ("Base",))
        state = self.one(model.analog(state, edge, "26610.001"))
        self.assertEqual(self.stack(model, state), ("Base", "Outside"))
        state = self.one(model.analog(state, edge, "26610"))
        self.assertEqual(self.stack(model, state), ("Base",))
        state = self.one(model.analog(state, edge, "32767"))
        self.assertEqual(self.stack(model, state), ("Base", "Outside"))
        state = self.one(model.analog(state, edge, "0"))
        self.assertEqual(self.stack(model, state), ("Base",))
        for invalid in ("32768", "-1", "NaN", "Infinity"):
            with self.subTest(value=invalid), self.assertRaisesRegex(ValueError, "32767"):
                model.analog(state, edge, invalid)

    def test_numeric_threshold_requires_an_analog_sample(self):
        edge = ("right_trackpad", "edge")
        model = self.model({"Base": {"right_trackpad": ("dpad", {"edge": {
            "Soft_Press": entry(add("Outside"), activation_threshold="26610")
        }})}, "Outside": {}})
        state = self.one(model.press(self.one(model.start()), edge))
        self.assertEqual(self.stack(model, state), ("Base",))

    def test_digital_inverted_click_cleans_up_on_release(self):
        click = ("left_trackpad", "click")
        model = self.model({"Base": {"left_trackpad": ("dpad", {"click": {"Soft_Press": [
            entry(add("Clicked")), entry(remove("Clicked"), edge_binding_invert="1")
        ]}})}, "Clicked": {}})
        state = self.one(model.press(self.one(model.start()), click))
        self.assertEqual(self.stack(model, state), ("Base", "Clicked"))
        state = self.one(model.release(state, click))
        self.assertEqual(self.stack(model, state), ("Base",))

    def test_disabled_source_blocks_lower_layer_commands(self):
        north = ("joystick", "dpad_north")
        model = self.model({
            "Base": {**switches({"left_bumper": act(add("Upper"))}),
                     "joystick": ("dpad", {"dpad_north": act(add("LowerRoute"))})},
            "Upper": {"joystick": ("disabled", {})}, "LowerRoute": {}})
        state = self.one(model.press(self.one(model.start()), LB))
        state = self.one(model.press(state, north))
        self.assertEqual(self.stack(model, state), ("Base", "Upper"))

    def test_analog_return_to_zero_fires_release_and_keeps_zero_sample(self):
        edge = ("left_trigger", "edge")
        model = self.model({"Base": {"left_trigger": ("trigger", {"edge": {
            **act(add("Pressed")), "release": entry(remove("Pressed"))
        }})}, "Pressed": {}})
        state = self.one(model.analog(self.one(model.start()), edge, 20000))
        self.assertEqual(self.stack(model, state), ("Base", "Pressed"))
        state = self.one(model.analog(state, edge, 0))
        self.assertEqual(self.stack(model, state), ("Base",))
        self.assertFalse(state.held)
        self.assertEqual(dict(state.analog_values)[edge], 0)

    def test_delayed_repeat_keeps_its_repeat_deadline_after_target_removal(self):
        model = self.model({"Base": switches({
            "left_bumper": act(add("A"), delay_start="100", hold_repeats="1", repeat_rate="300"),
            "right_bumper": act(remove("A"))}), "A": {}})
        state = self.one(model.press(self.one(model.start()), LB))
        state = self.one(model.wait(state, 150))
        state = self.one(model.press(state, RB))
        self.assertEqual(self.stack(model, state), ("Base",))
        self.assertEqual([a.deadline_ms for a in state.activations if a.stage == "repeat"], [400])
        state = self.one(model.wait(state, 249))
        self.assertEqual(self.stack(model, state), ("Base",))
        state = self.one(model.wait(state, 1))
        self.assertEqual(self.stack(model, state), ("Base", "A"))

    def test_release_before_deadline_cancels_the_physical_press(self):
        model = self.model({"Base": switches({"left_bumper": act(add("A"), delay_start="300")}),
                            "A": {}})
        state = self.one(model.press(self.one(model.start()), LB))
        state = self.one(model.wait(state, 200))
        state = self.one(model.release(state, LB))
        state = self.one(model.wait(state, 1000))
        self.assertEqual(self.stack(model, state), ("Base",))
        self.assertFalse(state.activations)

    def test_atomic_same_deadline_batch_preserves_selected_commands(self):
        model = self.model({"Base": switches({"left_bumper": {"Full_Press": [
            entry(add("A"), delay_start="300"), entry(remove("Absent"), delay_start="300")
        ]}}), "A": {}, "Absent": {}})
        state = self.one(model.press(self.one(model.start()), LB))
        state = self.one(model.wait(state, 300))
        self.assertEqual(self.stack(model, state), ("Base", "A"))

    def test_convergent_orders_are_not_a_zero_time_cycle(self):
        model = self.model({"Base": switches({"left_bumper": {"Full_Press": [
            entry(add("A")), entry(add("B"))
        ]}}), "A": {}, "B": switches({"always_on_action": act(remove("B"))})})
        states = model.press(self.one(model.start()), LB)
        self.assertEqual({self.stack(model, state) for state in states}, {("Base", "A")})

    def test_zero_time_cycle_and_unsupported_behavior_fail_explicitly(self):
        model = self.model({"Base": switches({"always_on_action": act(add("A"))}),
                            "A": switches({"always_on_action": act(remove("A"))})})
        with self.assertRaisesRegex(ValueError, "zero-time"):
            model.start()
        for settings in ({"delay_end": "20"}, {"toggle": "1"}, {"cycle_bindings": "1"}):
            with self.subTest(settings=settings), self.assertRaises(ValueError):
                self.model({"Base": switches({"left_bumper": act(add("A"), **settings)}), "A": {}})
        with self.assertRaisesRegex(ValueError, "release activators"):
            self.model({"Base": switches({"left_bumper": {
                "release": entry(add("A"), delay_start="20")}}), "A": {}})


if __name__ == "__main__":
    unittest.main()
