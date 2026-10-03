"""Simulation checks for the relaxed timed-entry transition compiler."""
from dataclasses import replace
from decimal import Decimal
import importlib.util
from itertools import combinations, permutations, product
import unittest

from steam_layout.model import Layout
from steam_layout.timed_model import TimedModel, TimedState
from test_audit_inheritance import EMPTY, act, add, build, remove

HAVE_Z3 = importlib.util.find_spec("z3") is not None
if HAVE_Z3:
    import z3
    from steam_layout.timed_envelope import TimedEnvelope


LB = ("switch", "left_bumper")
RB = ("switch", "right_bumper")


def switches(inputs):
    return {"switch": ("switches", inputs)}


def entry(binding, **settings):
    return {"bindings": {"binding": binding}, "settings": settings}


@unittest.skipUnless(HAVE_Z3, "optional z3-solver dependency is not installed")
class TimedEnvelopeTests(unittest.TestCase):
    def make(self, layers, shifts=None):
        runtime = TimedModel(Layout(build(layers, modeshift=shifts)))
        return runtime, TimedEnvelope(runtime)

    def one(self, states):
        self.assertEqual(len(states), 1)
        return next(iter(states))

    def transition(self, envelope, kind):
        return next(t for t in envelope.transitions() if t.label == kind)

    def solver(self, envelope, kind, before, after):
        transition = self.transition(envelope, kind)
        solver = z3.Solver()
        solver.add(envelope.domain, envelope.state_formula(before), transition.guard,
                   envelope.state_formula(after, transition.ranks, transition.held, transition.analog))
        return solver, transition

    def matches(self, envelope, kind, before, after):
        solver, _ = self.solver(envelope, kind, before, after)
        self.assertEqual(solver.check(), z3.sat, (kind, before, after))

    def test_separate_deadlines_and_restart_each_have_abstract_paths(self):
        runtime, envelope = self.make({"Base": switches({
            "left_bumper": {"Full_Press": [entry(add("Early"), delay_start="100"),
                                             entry(add("Late"), delay_start="500")]},
            "right_bumper": act(remove("Other"))}), "Early": {}, "Late": {}, "Other": {}})
        initial = self.one(runtime.start())
        pressed = self.one(runtime.press(initial, LB))
        self.matches(envelope, "press", initial, pressed)
        early = self.one(runtime.wait(pressed, 100))
        self.matches(envelope, "automatic", pressed, early)
        reset = self.one(runtime.press(early, RB))
        self.matches(envelope, "press", early, reset)
        late = self.one(runtime.wait(reset, 500))
        self.matches(envelope, "automatic", reset, late)

    def test_press_forces_all_own_immediate_entries_in_one_snapshot(self):
        runtime, envelope = self.make({"Base": switches({"left_bumper": {"Full_Press": [
            entry(add("A")), entry(add("B"))]}}), "A": {}, "B": {}})
        initial = self.one(runtime.start())
        for after in runtime.press(initial, LB):
            self.matches(envelope, "press", initial, after)
        partial = replace(initial, held=frozenset({LB}), stack=(0, 1))
        solver, _ = self.solver(envelope, "press", initial, partial)
        self.assertEqual(solver.check(), z3.unsat)

    def test_automatic_batch_keeps_entries_whose_owner_another_entry_removes(self):
        runtime, envelope = self.make({
            "Base": switches({"left_bumper": act(remove("Owner"), delay_start="100")}),
            "Owner": switches({"right_bumper": act(add("Result"), delay_start="100")}),
            "Result": {}})
        before = TimedState(stack=(0, 1), held=frozenset({LB, RB}))
        entries = [e for e in runtime.spec.entries.values() if e.ops]
        for order in permutations(entries):
            after = runtime._execute(before, order)
            solver, transition = self.solver(envelope, "automatic", before, after)
            index = {eid: i for i, (eid, _) in enumerate(transition.selected)}
            solver.add(*(choice for _, choice in transition.selected))
            solver.add(transition.orders[index[order[0].id]] < transition.orders[index[order[1].id]])
            self.assertEqual(solver.check(), z3.sat)

    def test_release_uses_pre_release_top_binding_and_every_release_entry(self):
        runtime, envelope = self.make({
            "Base": switches({"left_bumper": {"release": entry(add("Wrong"))}}),
            "Owner": switches({"left_bumper": {"release": [entry(remove("Owner")), entry(add("Right"))]}}),
            "Wrong": {}, "Right": {}})
        before = TimedState(stack=(0, 1), held=frozenset({LB}))
        after = self.one(runtime.release(before, LB))
        self.matches(envelope, "release", before, after)
        incorrect = replace(after, stack=(0,))
        solver, _ = self.solver(envelope, "release", before, incorrect)
        self.assertEqual(solver.check(), z3.unsat)

    def test_shift_can_remain_active_after_origin_binding_is_overridden(self):
        runtime, envelope = self.make({
            "Base": switches({"left_bumper": act([add("Owner"), "mode_shift joystick 90, , "])}),
            "Owner": switches({"left_bumper": act(EMPTY)}), "Result": {}},
            shifts={"90": ("joystick", "dpad", {"dpad_north": act(add("Result"))})})
        initial = self.one(runtime.start())
        shifted = self.one(runtime.press(initial, LB))
        self.assertTrue(shifted.shifts)
        self.matches(envelope, "press", initial, shifted)
        after = self.one(runtime.press(shifted, ("joystick", "dpad_north")))
        self.matches(envelope, "press", shifted, after)

    def test_shift_cannot_supply_commands_when_no_origin_control_is_held(self):
        runtime, envelope = self.make({
            "Base": switches({"left_bumper": act("mode_shift joystick 90, , ")}), "Result": {}},
            shifts={"90": ("joystick", "dpad", {"dpad_north": act(add("Result"))})})
        before = TimedState(held=frozenset({("joystick", "dpad_north")}))
        after = replace(before, stack=(0, 1))
        solver, _ = self.solver(envelope, "automatic", before, after)
        self.assertEqual(solver.check(), z3.unsat)

    def test_nonlayer_chord_blocks_interruptible_regular_layer_command(self):
        runtime, envelope = self.make({"Base": switches({"left_bumper": {
            **act(add("Wrong")), "chord": entry(EMPTY, chord_button="2")},
            "right_bumper": act(EMPTY)}), "Wrong": {}})
        before = TimedState(held=frozenset({LB, RB}))
        solver, _ = self.solver(envelope, "automatic", before, replace(before, stack=(0, 1)))
        self.assertEqual(solver.check(), z3.unsat)

    def test_alias_press_forces_both_raw_binding_entries(self):
        runtime, envelope = self.make({"Base": {
            "switch": ("switches", {"left_stick_click": act(add("A"))}),
            "joystick": ("dpad", {"click": act(add("B")), "touch": act(EMPTY)})},
            "A": {}, "B": {}})
        before = self.one(runtime.press(self.one(runtime.start()), ("joystick", "touch")))
        for after in runtime.press(before, ("switch", "left_stick_click")):
            self.matches(envelope, "press", before, after)
        partial = replace(before, held=before.held | {("joystick", "click")}, stack=(0, 1))
        solver, _ = self.solver(envelope, "press", before, partial)
        self.assertEqual(solver.check(), z3.unsat)

    def test_fractional_inverted_threshold_preserves_analog_truth(self):
        control = ("left_trigger", "edge")
        runtime, envelope = self.make({"Base": {"left_trigger": ("trigger", {
            "edge": {"Soft_Press": entry(add("Inside"), activation_threshold="0.25", edge_binding_invert="1")}})},
            "Inside": {}})
        initial = self.one(runtime.start())
        intermediate = replace(initial, held=frozenset({control}), analog_values=((control, Decimal("0.125")),))
        after = self.one(runtime.analog(initial, control, "0.125"))
        self.matches(envelope, "analog", initial, intermediate)
        self.matches(envelope, "automatic", intermediate, after)
        outside = replace(intermediate, analog_values=((control, Decimal("0.5")),))
        solver, _ = self.solver(envelope, "automatic", outside, replace(outside, stack=(0, 1)))
        self.assertEqual(solver.check(), z3.unsat)

    def test_missing_numeric_sample_is_not_a_fabricated_threshold_crossing(self):
        control = ("left_trigger", "edge")
        _, envelope = self.make({"Base": {"left_trigger": ("trigger", {
            "edge": {"Soft_Press": entry(add("Inside"), activation_threshold="10", edge_binding_invert="1")}})},
            "Inside": {}})
        for held in (frozenset(), frozenset({control})):
            before = TimedState(held=held)
            solver, _ = self.solver(envelope, "automatic", before, replace(before, stack=(0, 1)))
            self.assertEqual(solver.check(), z3.unsat)

    def test_analog_zero_uses_the_same_mandatory_release_binding(self):
        control = ("left_trigger", "edge")
        runtime, envelope = self.make({"Base": {"left_trigger": ("trigger", {"edge": {
            "Soft_Press": entry(EMPTY, activation_threshold="10"),
            "release": entry(add("Released"))}})}, "Released": {}})
        before = TimedState(held=frozenset({control}), analog_values=((control, Decimal(100)),))
        after = self.one(runtime.analog(before, control, 0))
        self.matches(envelope, "analog", before, after)
        solver, _ = self.solver(envelope, "analog", before, replace(after, stack=(0,)))
        self.assertEqual(solver.check(), z3.unsat)

    def test_physical_domain_agrees_with_reference_for_every_control_subset(self):
        runtime, envelope = self.make({"Base": {
            "joystick": ("dpad", {"touch": act(EMPTY), "dpad_north": act(EMPTY), "dpad_south": act(EMPTY)}),
            "left_trackpad": ("dpad", {"touch": act(EMPTY)}),
            "left_trigger": ("trigger", {"edge": act(EMPTY), "click": act(EMPTY)})}})
        controls = envelope.controls
        for size in range(len(controls) + 1):
            for subset in combinations(controls, size):
                solver = z3.Solver()
                solver.add(envelope.domain, envelope.state_formula(TimedState(held=frozenset(subset))))
                self.assertEqual(solver.check() == z3.sat, runtime._valid(frozenset(subset)), subset)

    def test_layer_projection_covers_every_selected_subset_and_entry_order(self):
        runtime, envelope = self.make({"Base": switches({"left_bumper": {"Full_Press": [
            entry([add("B"), add("Outside"), remove("A")]),
            entry([add("A"), remove("B")]), entry(remove("Outside"))]}}),
            "A": {}, "B": {}, "Outside": {}})
        entries = tuple(e for e in runtime.spec.entries.values() if e.ops)
        before = TimedState(stack=(0, 1, 3), held=frozenset({LB}))
        for layers in ({1}, {2}, {1, 2}):
            transition = next(t for t in envelope.project_transitions(layers) if t.label == "automatic")
            self.assertEqual(transition.projected_layers, frozenset(layers))
            for count in range(len(entries) + 1):
                for chosen in combinations(entries, count):
                    for ordered in permutations(chosen):
                        after = runtime._execute(before, ordered)
                        positions = {x: i for i, x in enumerate(after.stack)}
                        expected = [transition.ranks[x] > 0 if x in positions else transition.ranks[x] == 0
                                    for x in layers]
                        if layers == {1, 2} and 1 in positions and 2 in positions:
                            expected.append((transition.ranks[1] < transition.ranks[2]) ==
                                            (positions[1] < positions[2]))
                        selected_ids = {e.id for e in chosen}
                        solver = z3.Solver()
                        solver.add(envelope.domain, envelope.state_formula(before), transition.guard, *expected)
                        solver.add(*(selected == (eid in selected_ids) for eid, selected in transition.selected))
                        self.assertEqual(solver.check(), z3.sat, (layers, chosen, ordered))

    def test_projection_retains_binding_owners_without_relevant_commands(self):
        runtime, envelope = self.make({
            "Base": switches({"left_bumper": act(add("A"))}),
            "Owner": switches({"left_bumper": act(add("Outside"))}), "A": {}, "Outside": {}})
        before = TimedState(stack=(0, 1), held=frozenset({LB}))
        transition = next(t for t in envelope.project_transitions({2}) if t.label == "automatic")
        solver = z3.Solver()
        solver.add(envelope.domain, envelope.state_formula(before), transition.guard, transition.ranks[2] > 0)
        self.assertEqual(solver.check(), z3.unsat)
        self.assertTrue(z3.eq(transition.ranks[3], envelope.ranks[3]))

    def test_projected_physical_event_still_changes_held_state_when_no_relevant_entry_fires(self):
        runtime, envelope = self.make({"Base": switches({"left_bumper": act(add("Outside"))}),
                                      "A": {}, "Outside": {}})
        initial = self.one(runtime.start())
        transition = next(t for t in envelope.project_transitions({1}) if t.label == "press")
        solver = z3.Solver()
        solver.add(envelope.domain, envelope.state_formula(initial), transition.guard,
                   transition.held[envelope.cid[LB]], transition.ranks[1] == 0)
        self.assertEqual(solver.check(), z3.sat)

    def test_projection_rejects_invalid_layer_ids(self):
        _, envelope = self.make({"Base": switches({"left_bumper": act(EMPTY)})})
        for layers in ({-1}, {1}, {True}, {"0"}):
            with self.subTest(layers=layers), self.assertRaises(ValueError):
                envelope.project_transitions(layers)

    def test_projected_removal_groups_preserve_exact_interleaved_batch_results(self):
        fixtures = (
            ([entry([remove("A"), remove("B")]), entry([add("Outside"), add("A")]),
              entry([remove("B"), remove("A")]), entry([remove("Outside"), add("B")]),
              entry([add("A"), add("B")])], 4),
            # Identical add lists must remain separate: a removal between them
            # can make the second add restore A above an already-present B.
            ([entry([add("B"), add("A")]), entry(remove("A")),
              entry([add("B"), add("A")])], 3),
        )
        for inputs, group_count in fixtures:
            runtime, envelope = self.make({"Base": switches({"left_bumper": {"Full_Press": inputs}}),
                                          "A": {}, "B": {}, "Outside": {}})
            entries = tuple(runtime.spec.entries.values())
            before = TimedState(stack=(0, 3), held=frozenset({LB}))
            transition = next(t for t in envelope.project_transitions({1, 2}) if t.label == "automatic")
            self.assertEqual(len(transition.orders), group_count)
            self.assertEqual(len(transition.order_groups), group_count)
            self.assertEqual(len(transition.selected), len(entries))
            for bits in product((False, True), repeat=len(entries)):
                chosen = [e for e, bit in zip(entries, bits) if bit]
                selected_ids = {e.id for e in chosen}
                expected = {tuple(x for x in runtime._execute(before, order).stack if x in (1, 2))
                            for order in permutations(chosen)}
                solver = z3.Solver()
                solver.add(envelope.domain, envelope.state_formula(before), transition.guard)
                solver.add(*(selected == (eid in selected_ids) for eid, selected in transition.selected))
                actual = set()
                while solver.check() == z3.sat:
                    model = solver.model()
                    values = {x: model.eval(transition.ranks[x]).as_long() for x in (1, 2)}
                    reached = tuple(sorted((x for x in values if values[x] > 0), key=values.__getitem__))
                    self.assertNotIn(reached, actual)
                    actual.add(reached)
                    same = [transition.ranks[x] > 0 if x in reached else transition.ranks[x] == 0 for x in (1, 2)]
                    same.extend(transition.ranks[a] < transition.ranks[b] for a, b in zip(reached, reached[1:]))
                    solver.add(z3.Not(z3.And(*same)))
                self.assertEqual(actual, expected, bits)


if __name__ == "__main__":
    unittest.main()
