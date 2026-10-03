"""Elapsed-only repeat restrictions and the immediate activation exceptions."""
from dataclasses import replace
import importlib.util
import unittest

from steam_layout.model import Layout
from steam_layout.timed_model import TimedModel, TimedState
from test_audit_inheritance import EMPTY, act, add, build, remove
from test_timed_phase_envelope import entry, switches

HAVE_Z3 = importlib.util.find_spec("z3") is not None
if HAVE_Z3:
    import z3
    from steam_layout.timed_elapsed_envelope import TimedElapsedEnvelope

LB = ("switch", "left_bumper")
RB = ("switch", "right_bumper")
REPEAT = {"hold_repeats": "1", "repeat_rate": "50"}


@unittest.skipUnless(HAVE_Z3, "optional z3-solver dependency is not installed")
class TimedElapsedEnvelopeTests(unittest.TestCase):
    def make(self, layers):
        model = TimedModel(Layout(build(layers)))
        return model, TimedElapsedEnvelope(model)

    def one(self, states):
        self.assertEqual(len(states), 1)
        return next(iter(states))

    def relation(self, envelope, kind, before, after, layers=None):
        transitions = (envelope.transitions() if layers is None else
                       envelope.project_transitions(layers))
        transition = next(t for t in transitions if t.label == kind)
        solver = z3.Solver()
        solver.add(envelope.domain, envelope.state_formula(before), transition.guard,
                   envelope.state_formula(after, transition.ranks, transition.held,
                                          transition.analog))
        return solver, transition

    def assert_batches(self, model, envelope, operation):
        batches = []
        execute = model._execute

        def record(before, entries):
            entries = tuple(entries)
            after = execute(before, entries)
            batches.append((before, entries, after))
            return after

        model._execute = record
        try:
            result = operation()
        finally:
            model._execute = execute
        for before, entries, after in batches:
            if not entries or any(entry.kind == "release" for entry in entries):
                continue
            solver, transition = self.relation(envelope, "automatic", before, after)
            chosen = {entry.id for entry in entries}
            solver.add(*(take == (eid in chosen) for eid, take in transition.selected))
            self.assertEqual(solver.check(), z3.sat)
        return result, batches

    def test_automatic_elapsed_full_and_new_once_cannot_cofire(self):
        _, envelope = self.make({"Base": switches({
            "left_bumper": act(add("Repeated"), **REPEAT),
            "always_on_action": act(add("Once"))}), "Repeated": {}, "Once": {}})
        self.assertIn("0/switch/left_bumper/Full_Press/0", envelope.elapsed_full_entries)
        before = TimedState(held=frozenset({LB}))
        for layers in (None, {1, 2}):
            for stack in ((0, 1, 2), (0, 2, 1)):
                solver, _ = self.relation(envelope, "automatic", before,
                                          replace(before, stack=stack), layers)
                self.assertEqual(solver.check(), z3.unsat)
            for stack in ((0, 1), (0, 2)):
                solver, _ = self.relation(envelope, "automatic", before,
                                          replace(before, stack=stack), layers)
                self.assertEqual(solver.check(), z3.sat)

    def test_own_press_can_cofire_unconditional_repeat_and_once(self):
        model, envelope = self.make({"Base": switches({"left_bumper": {"Full_Press": [
            entry(add("Once")), entry(add("Repeated"), **REPEAT)]}}),
            "Once": {}, "Repeated": {}})
        before = self.one(model.start())
        afters = model.press(before, LB)
        self.assertEqual(len(afters), 2)
        for after in afters:
            solver, _ = self.relation(envelope, "press", before, after)
            self.assertEqual(solver.check(), z3.sat)

    def test_nonown_press_can_cofire_new_positive_chord_repeat_and_once(self):
        model, envelope = self.make({"Base": switches({
            "left_bumper": {"chord": entry(add("Repeated"), chord_button="2", **REPEAT)},
            "right_bumper": act(add("Once"))}), "Repeated": {}, "Once": {}})
        self.assertIn("0/switch/left_bumper/chord/0", envelope.elapsed_chord_entries)
        before = self.one(model.press(self.one(model.start()), LB))
        afters = model.press(before, RB)
        self.assertEqual(len(afters), 2)
        for after in afters:
            solver, _ = self.relation(envelope, "press", before, after)
            self.assertEqual(solver.check(), z3.sat)

    def test_soft_chord_support_can_start_repeat_and_once_in_automatic_prefix(self):
        control = ("left_trigger", "edge")
        model, envelope = self.make({"Base": {
            "switch": ("switches", {"left_bumper": {"chord": entry(
                add("Repeated"), chord_button="7", **REPEAT)}}),
            "left_trigger": ("trigger", {"edge": {"Soft_Press": entry(
                add("Once"), activation_threshold="10")}})}, "Repeated": {}, "Once": {}})
        self.assertNotIn("0/switch/left_bumper/chord/0", envelope.elapsed_chord_entries)
        before = self.one(model.press(self.one(model.start()), LB))
        _, batches = self.assert_batches(model, envelope, lambda: model.analog(before, control, 20))
        self.assertTrue(any(len(entries) == 2 for _, entries, _ in batches))

    def test_conditional_full_repeat_can_unblock_with_once_after_release(self):
        model, envelope = self.make({"Base": switches({
            "left_bumper": {"Full_Press": [entry(add("Repeated"), **REPEAT), entry(add("Once"))],
                            "chord": entry(EMPTY, chord_button="2")},
            "right_bumper": act(EMPTY)}), "Repeated": {}, "Once": {}})
        self.assertNotIn("0/switch/left_bumper/Full_Press/0", envelope.elapsed_full_entries)
        before = self.one(model.press(self.one(model.press(self.one(model.start()), RB)), LB))
        _, batches = self.assert_batches(model, envelope, lambda: model.release(before, RB))
        self.assertTrue(any(len(entries) == 2 for _, entries, _ in batches))

    def test_conditional_copy_exempts_entire_transferred_fingerprint_family(self):
        binding = {"Full_Press": [entry(add("Repeated"), **REPEAT), entry(add("Once"))]}
        model, envelope = self.make({
            "Base": switches({"left_bumper": binding, "right_bumper": act(add("Upper"))}),
            "Upper": switches({"left_bumper": {**binding, "chord": entry(EMPTY, chord_button="2")},
                               "right_bumper": {"release": entry(remove("Upper"))}}),
            "Repeated": {}, "Once": {}})
        repeaters = [e for e in model.spec.entries.values() if e.repeat_ms is not None]
        self.assertEqual(len({e.fingerprint for e in repeaters}), 1)
        self.assertTrue(all(e.id not in envelope.elapsed_full_entries for e in repeaters))
        before = self.one(model.press(self.one(model.press(self.one(model.start()), RB)), LB))
        _, batches = self.assert_batches(model, envelope, lambda: model.release(before, RB))
        self.assertTrue(any(len(entries) == 2 for _, entries, _ in batches))

    def test_new_always_on_repeat_and_once_can_cofire_after_exposure(self):
        model, envelope = self.make({
            "Base": switches({"left_bumper": act(add("Upper"), delay_start="100")}),
            "Upper": switches({"always_on_action": {"Full_Press": [
                entry(add("Repeated"), **REPEAT), entry(add("Once"))]}}),
            "Repeated": {}, "Once": {}})
        self.assertFalse(envelope.elapsed_full_entries)
        before = self.one(model.press(self.one(model.start()), LB))
        _, batches = self.assert_batches(model, envelope, lambda: model.wait(before, 100))
        self.assertTrue(any(len(entries) == 2 for _, entries, _ in batches))

    def test_elapsed_repeats_can_cofire_without_an_immediate_once(self):
        model, envelope = self.make({"Base": switches({
            "left_bumper": {"Full_Press": [entry(add("A"), **REPEAT), entry(add("B"), **REPEAT)]}}),
            "A": {}, "B": {}})
        before = next(iter(model.press(self.one(model.start()), LB)))
        _, batches = self.assert_batches(model, envelope, lambda: model.wait(before, 50))
        self.assertTrue(any(len(entries) == 2 for _, entries, _ in batches))


if __name__ == "__main__":
    unittest.main()
