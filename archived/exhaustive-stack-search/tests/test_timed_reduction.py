"""Differential complete-graph checks of layer relevance projection."""
from collections import deque
from dataclasses import replace
from decimal import Decimal
import json
from pathlib import Path
import tempfile
import unittest

from steam_layout.model import Layout
from steam_layout.timed_model import TimedModel
from steam_layout.timed_reduction import ReducedTimedQuotient
from steam_layout.timed_search import TimedQuotient, WitnessVerifier, run_search, verify_closure
from steam_layout.timed_store import TimedStore
from test_audit_inheritance import EMPTY, act, add, build, remove


ROOT = Path(__file__).resolve().parents[1]


def graph(quotient):
    found = set(quotient.initial())
    pending = deque(found)
    edges = []
    while pending:
        state = pending.popleft()
        for following, event in quotient.successors(state):
            edges.append((state, following, event))
            if following not in found:
                found.add(following)
                pending.append(following)
        if len(found) > 20000:
            raise AssertionError("fixture unexpectedly large")
    return found, edges


class LayerRelevanceTests(unittest.TestCase):
    def compare(self, layers, shifts=None):
        model = TimedModel(Layout(build(layers, modeshift=shifts)))
        full, reduced = TimedQuotient(model), ReducedTimedQuotient(model)
        states, edges = graph(full)
        reduced_states, _ = graph(reduced)
        self.assertEqual({reduced.normalize(state) for state in states}, reduced_states)
        self.assertEqual({state.stack for state in states},
                         {state.stack for state in reduced_states})
        # Every full event either stutters or has the same projected results.
        # The reverse inclusion follows from reachable-state equality above.
        for state, following, event in edges:
            event_control = next(iter(event.values()))
            if "analog" in event:
                event_control = event_control["control"]
            omitted = ("wait_ms" not in event and
                       tuple(event_control) not in reduced.relevance.retained)
            projected = reduced.normalize(state)
            target = reduced.normalize(following)
            if omitted:
                self.assertEqual(projected, target)
            else:
                self.assertIn(target, reduced.step(projected, event))
        return full, reduced, states, reduced_states

    def test_inert_buttons_removed_without_changing_stack_or_timers(self):
        _, reduced, full_states, states = self.compare({
            "Base": {"switch": ("switches", {
                "left_bumper": {**act(add("A"), delay_start="2"),
                                "release": {"bindings": {"binding": remove("A")}}},
                "right_bumper": act(EMPTY),
                "button_back_left": act("key_press SPACE, , "),
            })}, "A": {}})
        self.assertEqual(reduced.controls, (("switch", "left_bumper"),))
        self.assertEqual(len(full_states), 4 * len(states))

    def test_effectless_chord_that_interrupts_layer_command_is_retained(self):
        _, reduced, _, _ = self.compare({
            "Base": {"switch": ("switches", {
                "left_bumper": {**act(add("A"), delay_start="2"),
                    "chord": {"bindings": {"binding": EMPTY},
                              "settings": {"chord_button": "2"}}},
                "right_bumper": act(EMPTY),
            })}, "A": {}})
        self.assertIn(("switch", "right_bumper"), reduced.controls)

    def test_irrelevant_chord_selector_can_be_removed(self):
        _, reduced, _, _ = self.compare({
            "Base": {"switch": ("switches", {
                "left_bumper": act(add("A"), interruptable="0"),
                "right_bumper": {"chord": {
                    "bindings": {"binding": EMPTY}, "settings": {"chord_button": "1"}}},
            })}, "A": {}})
        self.assertNotIn(("switch", "right_bumper"), reduced.controls)

    def test_deflection_selector_retains_all_direction_controls_and_touch_parent(self):
        _, reduced, _, _ = self.compare({
            "Base": {
                "switch": ("switches", {"left_bumper": {"chord": {
                    "bindings": {"binding": add("A")},
                    "settings": {"gyro_ratchet_button_mask": str(1 << 30)}}}}),
                "joystick": ("dpad", {"touch": act(EMPTY),
                                       "dpad_north": act(EMPTY), "dpad_east": act(EMPTY)})
            }, "A": {}})
        self.assertTrue({("joystick", "edge"), ("joystick", "dpad_north"),
                         ("joystick", "dpad_east"), ("joystick", "touch")} <=
                        set(reduced.controls))

    def test_mode_shift_chord_lifetime_retains_its_selector(self):
        _, reduced, _, _ = self.compare({
            "Base": {"switch": ("switches", {
                "left_bumper": {"chord": {
                    "bindings": {"binding": "mode_shift left_trigger 90, , "},
                    "settings": {"chord_button": "2"}}},
                "right_bumper": act(EMPTY)})}, "A": {}
        }, shifts={"90": ("left_trigger", "trigger", {"edge": act(add("A"))})})
        self.assertIn(("switch", "right_bumper"), reduced.controls)

    def test_touch_parent_retained_and_competing_thumb_output_removed(self):
        _, reduced, _, _ = self.compare({
            "Base": {
                "left_trackpad": ("dpad", {"touch": act(EMPTY), "click": act(add("A"))}),
                "dpad": ("dpad", {"dpad_north": act("key_press W, , ")})
            }, "A": {}})
        self.assertIn(("left_trackpad", "touch"), reduced.controls)
        self.assertNotIn(("dpad", "dpad_north"), reduced.controls)

    def test_trigger_edge_parent_retained(self):
        _, reduced, _, _ = self.compare({
            "Base": {"left_trigger": ("trigger", {
                "edge": act(EMPTY), "click": act(add("A"))})}, "A": {}})
        self.assertEqual(set(reduced.controls), {("left_trigger", "edge"),
                                                 ("left_trigger", "click")})

    def test_hidden_and_shifted_layer_commands_remain_relevant(self):
        _, reduced, _, _ = self.compare({
            "Base": {"switch": ("switches", {
                "left_bumper": act(add("Upper")),
                "right_bumper": act("mode_shift left_trigger 90, , ")})},
            "Upper": {"switch": ("switches", {"button_back_left": act(add("A"))})},
            "A": {}, "B": {}
        }, shifts={"90": ("left_trigger", "trigger", {"edge": act(add("B"))})})
        self.assertIn(("switch", "button_back_left"), reduced.controls)
        self.assertIn(("left_trigger", "edge"), reduced.controls)

    def test_pure_output_analog_thresholds_do_not_split_regions(self):
        layers = {"Base": {"left_trigger": ("trigger", {"edge": {
            "Soft_Press": [
                {"bindings": {"binding": add("A")},
                 "settings": {"activation_threshold": "10"}},
                {"bindings": {"binding": "key_press SPACE, , "},
                 "settings": {"activation_threshold": "20"}},
            ]}})}, "A": {}}
        _, reduced, _, _ = self.compare(layers)
        self.assertEqual(reduced.analog_regions[("left_trigger", "edge")],
                         tuple(map(Decimal, (0, 10, 32767))))

    def test_nonnumeric_soft_press_is_digital_even_when_inverted(self):
        for invert in ("0", "1"):
            with self.subTest(invert=invert):
                _, reduced, _, _ = self.compare({
                    "Base": {"left_trigger": ("trigger", {"edge": {"Soft_Press": {
                        "bindings": {"binding": add("A")},
                        "settings": {"edge_binding_invert": invert}}}})}, "A": {}})
                self.assertEqual(reduced.analog_regions, {})

    def test_simultaneous_shifts_of_distinct_sources_commute(self):
        _, _, full, reduced = self.compare({
            "Base": {"switch": ("switches", {"left_bumper": {"Full_Press": [
                {"bindings": {"binding": "mode_shift left_trigger 90, , "}},
                {"bindings": {"binding": "mode_shift right_trigger 91, , "}},
            ]}})}, "A": {}, "B": {}
        }, shifts={"90": ("left_trigger", "trigger", {"edge": act(add("A"))}),
                   "91": ("right_trigger", "trigger", {"edge": act(add("B"))})})
        self.assertLess(len(reduced), len(full))

    def test_equal_group_shifts_commute_but_distinct_group_priority_remains(self):
        _, _, full, reduced = self.compare({
            "Base": {"switch": ("switches", {
                "left_bumper": act("mode_shift left_trigger 90, , "),
                "right_bumper": act("mode_shift left_trigger 90, , "),
                "button_back_left": act("mode_shift left_trigger 91, , "),
            })}, "A": {}, "B": {}
        }, shifts={"90": ("left_trigger", "trigger", {"edge": act(add("A"))}),
                   "91": ("left_trigger", "trigger", {"edge": act(add("B"))})})
        self.assertLess(len(reduced), len(full))

    def test_fired_flag_erased_but_delayed_add_stage_and_clock_retained(self):
        model = TimedModel(Layout(build({"Base": {"switch": ("switches", {
            "left_bumper": act(add("A"), delay_start="2")})}, "A": {}})))
        reduced = ReducedTimedQuotient(model)
        state = next(iter(model.press(next(iter(model.start())), ("switch", "left_bumper"))))
        flipped = replace(state, activations=tuple(replace(a, fired=not a.fired)
                                                   for a in state.activations))
        self.assertEqual(reduced.normalize(state), reduced.normalize(flipped))
        for event in ({"wait_ms": 1}, {"wait_ms": 2}, {"release": ["switch", "left_bumper"]}):
            self.assertEqual(reduced.step(state, event), reduced.step(flipped, event))
        self.assertEqual(reduced.normalize(state).activations[0].stage, "start")
        self.assertEqual(reduced.normalize(state).activations[0].deadline_ms, 2)

    def test_identity_records_both_full_contract_and_reduced_event_alphabet(self):
        model = TimedModel(Layout(build({"Base": {"switch": ("switches", {
            "left_bumper": act(add("A")), "right_bumper": act(EMPTY)})}, "A": {}})))
        full, reduced = TimedQuotient(model), ReducedTimedQuotient(model)
        self.assertNotEqual(full.identity, reduced.identity)
        self.assertEqual(reduced.identity["reference_quotient"], full.identity)
        self.assertEqual(reduced.identity["runtime"], full.identity["runtime"])
        self.assertEqual(reduced.identity["controls"], [["switch", "left_bumper"]])
        self.assertEqual(reduced.identity["analog_regions"], [])
        self.assertEqual(reduced.identity["reduction"], reduced.relevance.identity)
        self.assertNotEqual(reduced.identity["implementation_sha256"],
                            full.identity["implementation_sha256"])

    def test_reduced_database_closure_witnesses_and_resume_use_existing_search_api(self):
        model = TimedModel(Layout(build({"Base": {"switch": ("switches", {
            "left_bumper": {**act(add("A"), delay_start="2"),
                            "release": {"bindings": {"binding": remove("A")}}},
            "right_bumper": act(EMPTY)})}, "A": {}})))
        full, reduced = TimedQuotient(model), ReducedTimedQuotient(model)
        expected, _ = graph(full)
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "reduced.sqlite"
            with TimedStore(path, model, reduced.identity) as store:
                result = run_search(reduced, store)
                self.assertTrue(result["complete"])
                certificate = verify_closure(reduced, store)
                self.assertTrue(certificate["verified"])
                self.assertEqual({state for _, state in store.iter_states()},
                                 {reduced.normalize(state) for state in expected})
                verifier = WitnessVerifier(reduced, store)
                self.assertTrue(all(verifier(sid) for sid, _ in store.iter_states()))
            with TimedStore(path, model, reduced.identity, resume=True) as store:
                self.assertTrue(run_search(reduced, store)["complete"])
                self.assertTrue(verify_closure(reduced, store)["verified"])
            with self.assertRaises(ValueError):
                TimedStore(path, model, full.identity, resume=True)

    def test_full_normalization_validates_samples_before_relevance_discards_them(self):
        model = TimedModel(Layout(build({"Base": {"left_trigger": ("trigger", {
            "edge": {"Soft_Press": {"bindings": {"binding": EMPTY},
                                     "settings": {"activation_threshold": "10"}}}})}})))
        reduced = ReducedTimedQuotient(model)
        self.assertFalse(reduced.controls)
        initial = next(iter(model.start()))
        invalid = replace(initial, analog_values=((("left_trigger", "edge"), Decimal("NaN")),))
        with self.assertRaisesRegex(ValueError, "invalid analog"):
            reduced.normalize(invalid)

    def test_discarded_control_trace_requires_full_reference_replay(self):
        model = TimedModel(Layout(build({"Base": {"switch": ("switches", {
            "left_bumper": act(add("A")), "right_bumper": act(EMPTY)})}, "A": {}})))
        reduced = ReducedTimedQuotient(model)
        initial = next(iter(reduced.initial()))
        with self.assertRaisesRegex(ValueError, "outside the reduced event alphabet"):
            reduced.step(initial, {"press": ["switch", "right_bumper"]})
        held = next(iter(reduced.reference.step(initial, {"press": ["switch", "right_bumper"]})))
        self.assertEqual(reduced.normalize(held), initial)
        released = next(iter(reduced.reference.step(held, {"release": ["switch", "right_bumper"]})))
        self.assertEqual(reduced.normalize(released), initial)

    def test_new_runtime_contract_requires_review_before_reduction(self):
        model = TimedModel(Layout(build({"Base": {}})))
        model.semantics = {**model.semantics, "version": "geometry-aware-runtime-v2"}
        with self.assertRaisesRegex(ValueError, "reviewed"):
            ReducedTimedQuotient(model)

    def test_current_layout_witness_edges_commute_with_production_reduction(self):
        layout = Layout(json.loads((ROOT / "neptune/single-set-default_hold-gyro_latest.json").read_text()))
        model = TimedModel(layout, ignore_hold_bindings=True, default_repeat_ms=50)
        reduced = ReducedTimedQuotient(model)
        traces = [
            [{"press": ["switch", "button_menu"]}, {"wait_ms": 300},
             {"release": ["switch", "button_menu"]}, {"wait_ms": 1}],
            [{"press": ["left_trackpad", "touch"]},
             {"press": ["right_trackpad", "touch"]}, {"wait_ms": 1},
             {"release": ["left_trackpad", "touch"]},
             {"release": ["right_trackpad", "touch"]}],
            [{"press": ["right_joystick", "touch"]},
             {"analog": {"control": ["right_joystick", "edge"], "value": "27000"}},
             {"wait_ms": 50},
             {"analog": {"control": ["right_joystick", "edge"], "value": "0"}},
             {"release": ["right_joystick", "touch"]}],
        ]
        for trace in traces:
            full_states, projected_states = reduced.reference.initial(), reduced.initial()
            for event in trace:
                with self.subTest(event=event):
                    full_states = frozenset(target for state in full_states
                                            for target in reduced.reference.step(state, event))
                    projected_states = frozenset(target for state in projected_states
                                                 for target in reduced.step(state, event))
                    self.assertEqual({reduced.normalize(state) for state in full_states},
                                     projected_states)


if __name__ == "__main__":
    unittest.main()
