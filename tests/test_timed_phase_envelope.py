"""Batch-phase lemmas checked against concrete timed execution."""
from dataclasses import replace
import importlib.util
import unittest

from steam_layout.model import Layout
from steam_layout.timed_model import TimedModel, TimedState
from test_audit_inheritance import EMPTY, act, add, build, remove

HAVE_Z3 = importlib.util.find_spec("z3") is not None
if HAVE_Z3:
    import z3
    from steam_layout.timed_phase_envelope import TimedPhaseEnvelope

LB = ("switch", "left_bumper")
RB = ("switch", "right_bumper")


def switches(inputs):
    return {"switch": ("switches", inputs)}


def entry(binding, **settings):
    return {"bindings": {"binding": binding}, "settings": settings}


@unittest.skipUnless(HAVE_Z3, "optional z3-solver dependency is not installed")
class TimedPhaseEnvelopeTests(unittest.TestCase):
    def make(self, layers, shifts=None):
        model = TimedModel(Layout(build(layers, modeshift=shifts)))
        return model, TimedPhaseEnvelope(model)

    def one(self, states):
        self.assertEqual(len(states), 1)
        return next(iter(states))

    def relation(self, envelope, kind, before, after, layers=None):
        transitions = (envelope.transitions() if layers is None else
                       envelope.project_transitions(layers))
        tr = next(t for t in transitions if t.label == kind)
        solver = z3.Solver()
        solver.add(envelope.domain, envelope.state_formula(before), tr.guard,
                   envelope.state_formula(after, tr.ranks, tr.held, tr.analog))
        return solver, tr

    def test_delayed_and_immediate_once_cannot_share_automatic_batch(self):
        model, envelope = self.make({"Base": switches({
            "left_bumper": {"chord": entry(add("Immediate"), chord_button="2")},
            "right_bumper": act(add("Delayed"), delay_start="100")}),
            "Immediate": {}, "Delayed": {}})
        before = TimedState(held=frozenset({LB, RB}))
        after = replace(before, stack=(0, 1, 2))
        for projection in (None, {1, 2}):
            solver, _ = self.relation(envelope, "automatic", before, after, projection)
            self.assertEqual(solver.check(), z3.unsat)
        state = self.one(model.start())
        state = self.one(model.press(state, LB))
        immediate = self.one(model.press(state, RB))
        solver, _ = self.relation(envelope, "press", state, immediate)
        self.assertEqual(solver.check(), z3.sat)
        delayed = self.one(model.wait(immediate, 100))
        solver, _ = self.relation(envelope, "automatic", immediate, delayed)
        self.assertEqual(solver.check(), z3.sat)

    def test_simple_once_requires_its_own_press(self):
        model, envelope = self.make({"Base": switches({
            "left_bumper": act(add("A")), "right_bumper": act(EMPTY)}), "A": {}})
        initial = self.one(model.start())
        actual = self.one(model.press(initial, LB))
        solver, _ = self.relation(envelope, "press", initial, actual)
        self.assertEqual(solver.check(), z3.sat)
        held = replace(initial, held=frozenset({LB}))
        solver, _ = self.relation(envelope, "automatic", held, replace(held, stack=(0, 1)))
        self.assertEqual(solver.check(), z3.unsat)
        solver, _ = self.relation(envelope, "press", held,
                                  replace(held, held=frozenset({LB, RB}), stack=(0, 1)))
        self.assertEqual(solver.check(), z3.unsat)

    def test_release_unblock_transfers_due_fingerprint_to_simple_copy(self):
        binding = act(add("Result"))
        model, envelope = self.make({
            "Base": switches({"left_bumper": binding, "right_bumper": act(add("Upper"))}),
            "Upper": switches({
                "left_bumper": {**binding, "chord": entry(EMPTY, chord_button="2")},
                "right_bumper": {"release": entry(remove("Upper"))}}), "Result": {}})
        copies = [e for e in model.spec.entries.values()
                  if e.source == "switch" and e.input == "left_bumper" and e.ops]
        self.assertEqual(len({e.fingerprint for e in copies}), 1)
        self.assertTrue(all(e.id not in envelope.press_only_entries for e in copies))
        before = self.one(model.press(self.one(model.press(self.one(model.start()), RB)), LB))
        physical = replace(before, held=before.held - {RB})
        ready = model._refresh(physical, before)
        release = [e for e in model._binding(before, RB) if e.kind == "release"]
        prefix = model._execute(ready, release)
        self.assertTrue(any(a.deadline_ms == prefix.now_ms for a in prefix.activations))
        after = self.one(model.release(before, RB))
        self.assertEqual(after.stack, (0, 2))
        solver, _ = self.relation(envelope, "release", before, prefix)
        self.assertEqual(solver.check(), z3.sat)
        solver, _ = self.relation(envelope, "automatic", prefix, after)
        self.assertEqual(solver.check(), z3.sat)

    def test_analog_controls_keep_immediate_full_press_in_automatic_prefix(self):
        control = ("left_trigger", "edge")
        model, envelope = self.make({"Base": {"left_trigger": ("trigger", {
            "edge": {**act(add("A")), "Soft_Press": entry(EMPTY, activation_threshold="10")}})},
            "A": {}})
        initial = self.one(model.start())
        after = self.one(model.analog(initial, control, 20))
        prefix = replace(after, stack=(0,))
        solver, _ = self.relation(envelope, "analog", initial, prefix)
        self.assertEqual(solver.check(), z3.sat)
        solver, _ = self.relation(envelope, "automatic", prefix, after)
        self.assertEqual(solver.check(), z3.sat)

    def test_uninterruptible_full_press_with_chord_remains_press_only(self):
        _, envelope = self.make({"Base": switches({
            "left_bumper": {**act(add("A"), interruptable="0"),
                            "chord": entry(EMPTY, chord_button="2")},
            "right_bumper": act(EMPTY)}), "A": {}})
        self.assertIn("0/switch/left_bumper/Full_Press/0", envelope.press_only_entries)

    def test_repeating_and_immediate_entries_can_share_own_press(self):
        model, envelope = self.make({"Base": switches({"left_bumper": {"Full_Press": [
            entry(add("Once")), entry(add("Repeated"), hold_repeats="1", repeat_rate="50")]}}),
            "Once": {}, "Repeated": {}})
        initial = self.one(model.start())
        for after in model.press(initial, LB):
            solver, _ = self.relation(envelope, "press", initial, after)
            self.assertEqual(solver.check(), z3.sat)

    def test_canonical_aliases_share_the_own_press_exception(self):
        model, envelope = self.make({"Base": {
            "switch": ("switches", {"left_stick_click": act(add("A"))}),
            "joystick": ("dpad", {"click": act(add("B")), "touch": act(EMPTY)})},
            "A": {}, "B": {}})
        before = self.one(model.press(self.one(model.start()), ("joystick", "touch")))
        for after in model.press(before, ("switch", "left_stick_click")):
            solver, _ = self.relation(envelope, "press", before, after)
            self.assertEqual(solver.check(), z3.sat)

    def test_delayed_then_new_always_on_execute_in_separate_automatic_batches(self):
        model, envelope = self.make({
            "Base": switches({"left_bumper": act(add("Upper"), delay_start="100")}),
            "Upper": switches({"always_on_action": act(add("Result"))}), "Result": {}})
        before = self.one(model.press(self.one(model.start()), LB))
        executed = []
        original = model._execute

        def record(state, entries):
            entries = tuple(entries)
            after = original(state, entries)
            executed.append((state, entries, after))
            return after

        model._execute = record
        final = self.one(model.wait(before, 100))
        self.assertEqual(final.stack, (0, 1, 2))
        self.assertEqual(len(executed), 2)
        for state, entries, after in executed:
            solver, transition = self.relation(envelope, "automatic", state, after)
            chosen = {entry.id for entry in entries}
            solver.add(*(take == (eid in chosen) for eid, take in transition.selected))
            self.assertEqual(solver.check(), z3.sat)

    def record_wait(self, model, state, milliseconds):
        batches = []
        original = model._execute

        def record(before, entries):
            entries = tuple(entries)
            batches.append({entry.id for entry in entries})
            return original(before, entries)

        model._execute = record
        try:
            states = model.wait(state, milliseconds)
        finally:
            model._execute = original
        return states, batches

    def test_repeating_removal_starves_longer_singleton_delay_even_when_projected_out(self):
        model, envelope = self.make({"Base": switches({
            "left_bumper": act(remove("Other"), hold_repeats="1", repeat_rate="50"),
            "right_bumper": act(add("A"), delay_start="100")}), "A": {}, "Other": {}})
        self.assertEqual(len(envelope.reset_starvation_pairs), 1)
        before = TimedState(held=frozenset({LB, RB}))
        after = replace(before, stack=(0, 1))
        for layers in (None, {1}):
            solver, _ = self.relation(envelope, "automatic", before, after, layers)
            self.assertEqual(solver.check(), z3.unsat)
        state = self.one(model.press(self.one(model.start()), RB))
        state = self.one(model.wait(state, 49))
        state = self.one(model.press(state, LB))
        state = self.one(model.wait(state, 300))
        self.assertEqual(state.stack, (0,))
        state = self.one(model.release(state, LB))
        self.assertEqual(self.one(model.wait(state, 100)).stack, (0, 1))

    def test_equal_delay_and_period_really_can_cofire_after_owner_is_added(self):
        model, envelope = self.make({
            "Base": switches({"left_bumper": act(EMPTY), "right_bumper": act(EMPTY),
                              "button_menu": act(add("Owner"))}),
            "Owner": switches({
                "left_bumper": act(remove("Other"), hold_repeats="1", repeat_rate="50"),
                "right_bumper": act(add("A"), delay_start="50")}), "A": {}, "Other": {}})
        self.assertFalse(envelope.reset_starvation_pairs)
        state = self.one(model.start())
        for control in (LB, RB, ("switch", "button_menu")):
            state = self.one(model.press(state, control))
        _, batches = self.record_wait(model, state, 50)
        self.assertTrue(any(len(batch) == 2 for batch in batches))

    def test_cross_owner_delayed_fingerprint_transfer_really_can_cofire(self):
        delayed = act(add("A"), delay_start="100")
        model, envelope = self.make({
            "Base": switches({"left_bumper": act(EMPTY), "right_bumper": delayed,
                              "button_menu": act(add("Owner"))}),
            "Owner": switches({
                "left_bumper": act(remove("Other"), hold_repeats="1", repeat_rate="50"),
                "right_bumper": delayed}), "A": {}, "Other": {}})
        self.assertFalse(envelope.reset_starvation_pairs)
        state = self.one(model.press(self.one(model.press(self.one(model.start()), LB)), RB))
        state = self.one(model.wait(state, 50))
        state = self.one(model.press(state, ("switch", "button_menu")))
        _, batches = self.record_wait(model, state, 50)
        self.assertTrue(any(len(batch) == 2 for batch in batches))

    def test_repeating_delayed_entry_really_can_cofire_after_its_first_firing(self):
        model, envelope = self.make({"Base": switches({
            "left_bumper": act(remove("Other"), hold_repeats="1", repeat_rate="50"),
            "right_bumper": act(add("A"), delay_start="100", hold_repeats="1", repeat_rate="50")}),
            "A": {}, "Other": {}})
        self.assertFalse(envelope.reset_starvation_pairs)
        state = self.one(model.press(self.one(model.start()), RB))
        state = self.one(model.wait(state, 100))
        state = self.one(model.press(state, LB))
        _, batches = self.record_wait(model, state, 50)
        self.assertTrue(any(len(batch) == 2 for batch in batches))

    def test_mode_shift_reveal_without_removal_really_can_cofire(self):
        model, envelope = self.make({"Base": {
            "switch": ("switches", {
                "left_bumper": act("mode_shift joystick 90, , "),
                "right_bumper": act(add("A"), delay_start="100")}),
            "joystick": ("dpad", {"touch": act(EMPTY), "click": act(
                remove("Other"), hold_repeats="1", repeat_rate="50")})},
            "A": {}, "Other": {}}, shifts={"90": (
                "joystick", "dpad", {"touch": act(EMPTY), "click": act(EMPTY)})})
        self.assertFalse(envelope.reset_starvation_pairs)
        state = self.one(model.start())
        for control in (LB, ("joystick", "touch"), ("joystick", "click"), RB):
            state = self.one(model.press(state, control))
        state = self.one(model.wait(state, 50))
        state = self.one(model.release(state, LB))
        _, batches = self.record_wait(model, state, 50)
        self.assertTrue(any(len(batch) == 2 for batch in batches))

    def test_chord_unblocking_repeater_immediately_resets_delayed_entry(self):
        model, envelope = self.make({"Base": switches({
            "always_on_action": act(add("A"), delay_start="100"),
            "left_bumper": {**act(remove("Other"), hold_repeats="1", repeat_rate="50"),
                            "chord": entry(EMPTY, chord_button="2")},
            "right_bumper": act(EMPTY)}), "A": {}, "Other": {}})
        self.assertEqual(len(envelope.reset_starvation_pairs), 1)
        state = self.one(model.press(self.one(model.press(self.one(model.start()), RB)), LB))
        state = self.one(model.wait(state, 50))
        state = self.one(model.release(state, RB))
        delayed = next(a for a in state.activations if "always_on_action" in a.entry_id)
        self.assertEqual(delayed.deadline_ms, 150)
        self.assertEqual(self.one(model.wait(state, 200)).stack, (0,))

    def test_soft_press_repeater_activation_immediately_resets_delayed_entry(self):
        control = ("left_trigger", "edge")
        model, envelope = self.make({"Base": {
            "switch": ("switches", {"always_on_action": act(add("A"), delay_start="100")}),
            "left_trigger": ("trigger", {"edge": {"Soft_Press": entry(
                remove("Other"), activation_threshold="10", hold_repeats="1", repeat_rate="50")}})},
            "A": {}, "Other": {}})
        self.assertEqual(len(envelope.reset_starvation_pairs), 1)
        state = self.one(model.wait(self.one(model.start()), 50))
        state = self.one(model.analog(state, control, 20))
        delayed = next(a for a in state.activations if "always_on_action" in a.entry_id)
        self.assertEqual(delayed.deadline_ms, 150)
        self.assertEqual(self.one(model.wait(state, 200)).stack, (0,))

    def test_other_control_press_cannot_fire_an_existing_repeat(self):
        model, envelope = self.make({"Base": switches({
            "left_bumper": act(add("A"), hold_repeats="1", repeat_rate="50"),
            "right_bumper": act(remove("A"))}), "A": {}})
        before = self.one(model.press(self.one(model.start()), LB))
        after = self.one(model.press(before, RB))
        self.assertEqual(after.stack, (0,))
        for layers in (None, {1}):
            solver, _ = self.relation(envelope, "press", before, after, layers)
            self.assertEqual(solver.check(), z3.sat)
            solver, _ = self.relation(envelope, "press", before,
                                      replace(after, stack=(0, 1)), layers)
            self.assertEqual(solver.check(), z3.unsat)

    def test_other_control_press_can_start_a_newly_true_repeating_chord(self):
        model, envelope = self.make({"Base": switches({
            "left_bumper": {"chord": entry(add("A"), chord_button="2",
                                           hold_repeats="1", repeat_rate="50")},
            "right_bumper": act(add("B"))}), "A": {}, "B": {}})
        before = self.one(model.press(self.one(model.start()), LB))
        afters = model.press(before, RB)
        self.assertEqual(len(afters), 2)
        for after in afters:
            solver, _ = self.relation(envelope, "press", before, after)
            self.assertEqual(solver.check(), z3.sat)

    def test_nonrepeating_chord_can_fire_on_other_control_press_but_not_automatically(self):
        model, envelope = self.make({"Base": switches({
            "left_bumper": {"chord": entry(add("A"), chord_button="2")},
            "right_bumper": act(EMPTY)}), "A": {}})
        self.assertIn("0/switch/left_bumper/chord/0", envelope.chord_press_entries)
        before = self.one(model.press(self.one(model.start()), LB))
        after = self.one(model.press(before, RB))
        solver, _ = self.relation(envelope, "press", before, after)
        self.assertEqual(solver.check(), z3.sat)
        prefix = replace(after, stack=(0,))
        solver, _ = self.relation(envelope, "automatic", prefix, after)
        self.assertEqual(solver.check(), z3.unsat)

    def test_soft_control_in_chord_condition_preserves_analog_automatic_prefix(self):
        control = ("left_trigger", "edge")
        model, envelope = self.make({"Base": {
            "switch": ("switches", {"left_bumper": {"chord": entry(add("A"), chord_button="7")}}),
            "left_trigger": ("trigger", {"edge": {"Soft_Press": entry(EMPTY, activation_threshold="10")}})},
            "A": {}})
        self.assertNotIn("0/switch/left_bumper/chord/0", envelope.chord_press_entries)
        before = self.one(model.press(self.one(model.start()), LB))
        after = self.one(model.analog(before, control, 20))
        prefix = replace(after, stack=(0,))
        for kind, source, target in (("analog", before, prefix), ("automatic", prefix, after)):
            solver, _ = self.relation(envelope, kind, source, target)
            self.assertEqual(solver.check(), z3.sat)

    def test_chord_support_uses_canonical_aliases_and_global_soft_entries(self):
        chord = {"chord": entry(add("A"), chord_button="9")}
        _, envelope = self.make({
            "Base": switches({"left_bumper": chord, "right_bumper": act(add("Upper"))}),
            "Upper": {
                "switch": ("switches", {"left_bumper": chord, "left_stick_click": {
                    "Soft_Press": entry(EMPTY, activation_threshold="10")}}),
                "joystick": ("dpad", {"touch": act(EMPTY)})}, "A": {}})
        copies = [entry for entry in envelope.spec.entries.values()
                  if entry.input == "left_bumper" and entry.kind == "chord"]
        self.assertEqual(len(copies), 2)
        self.assertEqual(len({entry.fingerprint for entry in copies}), 1)
        self.assertTrue(all(entry.id not in envelope.chord_press_entries for entry in copies))

    def test_deflection_chord_support_includes_soft_direction_not_only_edge(self):
        control = ("joystick", "dpad_north")
        model, envelope = self.make({"Base": {
            "switch": ("switches", {"left_bumper": {"chord": entry(
                add("A"), gyro_ratchet_button_mask=str(1 << 30))}}),
            "joystick": ("dpad", {"touch": act(EMPTY), "edge": act(EMPTY),
                                  "dpad_north": {"Soft_Press": entry(EMPTY, activation_threshold="10")}})},
            "A": {}})
        self.assertNotIn("0/switch/left_bumper/chord/0", envelope.chord_press_entries)
        before = self.one(model.press(self.one(model.press(self.one(model.start()), LB)),
                                      ("joystick", "touch")))
        after = self.one(model.analog(before, control, 20))
        prefix = replace(after, stack=(0,))
        solver, _ = self.relation(envelope, "automatic", prefix, after)
        self.assertEqual(solver.check(), z3.sat)

    def test_newly_exposed_always_on_chord_keeps_automatic_execution(self):
        model, envelope = self.make({
            "Base": switches({"left_bumper": act(EMPTY), "right_bumper": act(add("Upper"), delay_start="100")}),
            "Upper": switches({"always_on_action": {"chord": entry(add("A"), chord_button="1")}}),
            "A": {}})
        self.assertNotIn("1/switch/always_on_action/chord/0", envelope.chord_press_entries)
        before = self.one(model.press(self.one(model.press(self.one(model.start()), LB)), RB))
        captured = []
        original = model._execute

        def record(state, entries):
            entries = tuple(entries)
            after = original(state, entries)
            captured.append((state, after))
            return after

        model._execute = record
        after = self.one(model.wait(before, 100))
        self.assertEqual(after.stack, (0, 1, 2))
        self.assertEqual(len(captured), 2)
        for source, target in captured:
            solver, _ = self.relation(envelope, "automatic", source, target)
            self.assertEqual(solver.check(), z3.sat)

    def test_press_must_fire_every_newly_eligible_nonown_chord(self):
        model, envelope = self.make({"Base": switches({
            "left_bumper": {"chord": entry(add("Required"), chord_button="2")},
            "right_bumper": act(add("Own"))}), "Required": {}, "Own": {}})
        before = self.one(model.press(self.one(model.start()), LB))
        afters = model.press(before, RB)
        self.assertEqual(len(afters), 2)
        for layers in (None, {1, 2}):
            for after in afters:
                solver, _ = self.relation(envelope, "press", before, after, layers)
                self.assertEqual(solver.check(), z3.sat)
            omitted = replace(next(iter(afters)), stack=(0, 2))
            solver, _ = self.relation(envelope, "press", before, omitted, layers)
            self.assertEqual(solver.check(), z3.unsat)
