"""Positive analog samples execute every newly eligible immediate command."""
from dataclasses import replace
from decimal import Decimal
import importlib.util
import unittest

from steam_layout.model import Layout
from steam_layout.timed_model import TimedModel, TimedState
from test_audit_inheritance import EMPTY, act, add, build, remove
from test_timed_envelope import entry, switches

HAVE_Z3 = importlib.util.find_spec("z3") is not None
if HAVE_Z3:
    import z3
    from steam_layout.timed_analog_envelope import TimedAnalogEnvelope
    from steam_layout.timed_proof import TimedProof

LB = ("switch", "left_bumper")
RB = ("switch", "right_bumper")
EDGE = ("left_trigger", "edge")


@unittest.skipUnless(HAVE_Z3, "optional z3-solver dependency is not installed")
class TimedAnalogEnvelopeTests(unittest.TestCase):
    def make(self, layers, shifts=None):
        model = TimedModel(Layout(build(layers, modeshift=shifts)))
        return model, TimedAnalogEnvelope(model)

    def one(self, states):
        self.assertEqual(len(states), 1)
        return next(iter(states))

    def relation(self, envelope, kind, before, after, layers=None):
        transitions = envelope.transitions() if layers is None else envelope.project_transitions(layers)
        tr = next(t for t in transitions if t.label == kind)
        solver = z3.Solver()
        if layers is None:
            post = envelope.state_formula(after, tr.ranks, tr.held, tr.analog)
        else:
            positions = {x: i for i, x in enumerate(after.stack)}
            constraints = [tr.ranks[x] > 0 if x in positions else tr.ranks[x] == 0 for x in layers]
            constraints.extend((tr.ranks[x] < tr.ranks[y]) == (positions[x] < positions[y])
                               for x in layers for y in layers if x != y and x in positions and y in positions)
            constraints.extend(h == (control in after.held) for control, h in zip(envelope.controls, tr.held))
            constraints.extend(tr.analog[i] == z3.RealVal(str(dict(after.analog_values).get(envelope.controls[i], -1)))
                               for i in envelope.analog_controls)
            post = z3.And(*constraints)
        solver.add(envelope.domain, envelope.state_formula(before), tr.guard, post)
        return solver, tr

    def test_positive_sample_forces_full_and_soft_entries_in_every_order(self):
        model, env = self.make({"Base": {"left_trigger": ("trigger", {"edge": {
            "Full_Press": entry(add("Full")),
            "Soft_Press": entry(add("Soft"), activation_threshold="10")}})}, "Full": {}, "Soft": {}})
        before = self.one(model.start())
        afters = model.analog(before, EDGE, 20)
        self.assertEqual(len(afters), 2)
        for after in afters:
            for layers in (None, {1, 2}, {1}, {2}):
                solver, _ = self.relation(env, "analog_positive", before, after, layers)
                self.assertEqual(solver.check(), z3.sat)
        partial = replace(next(iter(afters)), stack=(0, 1))
        solver, _ = self.relation(env, "analog_positive", before, partial)
        self.assertEqual(solver.check(), z3.unsat)

    def test_sample_does_not_refire_an_already_eligible_repeat(self):
        model, env = self.make({"Base": {
            "switch": ("switches", {"right_bumper": act(remove("A"))}),
            "left_trigger": ("trigger", {"edge": {
                "Full_Press": entry(add("A"), hold_repeats="1", repeat_rate="50"),
                "Soft_Press": entry(EMPTY, activation_threshold="10")}})}, "A": {}})
        state = self.one(model.analog(self.one(model.start()), EDGE, 20))
        before = self.one(model.press(state, RB))
        after = self.one(model.analog(before, EDGE, 30))
        self.assertEqual(after.stack, (0,))
        solver, _ = self.relation(env, "analog_positive", before, after)
        self.assertEqual(solver.check(), z3.sat)
        solver, _ = self.relation(env, "analog_positive", before, replace(after, stack=(0, 1)))
        self.assertEqual(solver.check(), z3.unsat)

    def test_fractional_crossings_while_held_activate_normal_and_inverted_soft(self):
        model, env = self.make({"Base": {"left_trigger": ("trigger", {"edge": {
            "Soft_Press": [entry(add("Outside"), activation_threshold="0.25"),
                           entry(add("Inside"), activation_threshold="0.25", edge_binding_invert="1")]}})},
            "Outside": {}, "Inside": {}})
        before = self.one(model.start())
        for value in ("0.125", "0.25", "0.5", "0.125"):
            after = self.one(model.analog(before, EDGE, value))
            solver, _ = self.relation(env, "analog_positive", before, after)
            self.assertEqual(solver.check(), z3.sat, value)
            before = after

    def test_positive_sample_forces_new_nonown_chord_and_forbids_automatic_refire(self):
        model, env = self.make({"Base": {
            "switch": ("switches", {"left_bumper": {"chord": entry(add("Chord"), chord_button="7")}}),
            "left_trigger": ("trigger", {"edge": {"Soft_Press": entry(add("Soft"), activation_threshold="10")}})},
            "Chord": {}, "Soft": {}})
        before = self.one(model.press(self.one(model.start()), LB))
        afters = model.analog(before, EDGE, 20)
        self.assertEqual(len(afters), 2)
        for after in afters:
            solver, _ = self.relation(env, "analog_positive", before, after)
            self.assertEqual(solver.check(), z3.sat)
        intermediate = replace(before, held=before.held | {EDGE}, analog_values=((EDGE, Decimal(20)),))
        solver, tr = self.relation(env, "automatic", intermediate, replace(intermediate, stack=(0, 1)))
        self.assertEqual(solver.check(), z3.unsat)
        self.assertIn("0/switch/left_bumper/chord/0", env.chord_press_entries)

    def test_zero_sample_keeps_release_prefix_and_inverted_soft_automatic_followup(self):
        model, env = self.make({"Base": {"left_trigger": ("trigger", {"edge": {
            "release": entry(add("Released")),
            "Soft_Press": entry(add("Inside"), activation_threshold="10", edge_binding_invert="1")}})},
            "Released": {}, "Inside": {}})
        before = self.one(model.analog(self.one(model.start()), EDGE, 20))
        after = self.one(model.analog(before, EDGE, 0))
        prefix = replace(after, stack=(0, 1))
        solver, _ = self.relation(env, "analog_zero", before, prefix)
        self.assertEqual(solver.check(), z3.sat)
        solver, _ = self.relation(env, "automatic", prefix, after)
        self.assertEqual(solver.check(), z3.sat)
        solver, _ = self.relation(env, "analog_zero", before, replace(prefix, stack=(0,)))
        self.assertEqual(solver.check(), z3.unsat)

    def test_release_unblock_full_family_remains_automatic(self):
        model, env = self.make({"Base": switches({
            "left_bumper": {"Full_Press": entry(add("Unblocked")), "chord": entry(EMPTY, chord_button="2")},
            "right_bumper": act(EMPTY)}), "Unblocked": {}})
        before = self.one(model.press(self.one(model.press(self.one(model.start()), RB)), LB))
        after = self.one(model.release(before, RB))
        prefix = replace(after, stack=(0,))
        solver, _ = self.relation(env, "release", before, prefix)
        self.assertEqual(solver.check(), z3.sat)
        solver, _ = self.relation(env, "automatic", prefix, after)
        self.assertEqual(solver.check(), z3.sat)

    def test_aliases_share_analog_rising_edge_and_both_bindings_fire(self):
        control = ("joystick", "click")
        model, env = self.make({"Base": {
            "switch": ("switches", {"left_stick_click": act(add("Alias"))}),
            "joystick": ("dpad", {"touch": act(EMPTY), "click": {
                "Full_Press": entry(add("Direct")), "Soft_Press": entry(EMPTY, activation_threshold="10")}})},
            "Alias": {}, "Direct": {}})
        before = self.one(model.press(self.one(model.start()), ("joystick", "touch")))
        afters = model.analog(before, ("switch", "left_stick_click"), 20)
        self.assertEqual(len(afters), 2)
        for after in afters:
            solver, _ = self.relation(env, "analog_positive", before, after)
            self.assertEqual(solver.check(), z3.sat)
            self.assertIn(control, after.held)

    def test_existing_mode_shift_supplies_the_positive_first_batch(self):
        model, env = self.make({"Base": {
            "switch": ("switches", {"left_bumper": act("mode_shift joystick 90, , ")}),
            "joystick": ("dpad", {"touch": act(EMPTY), "edge": {
                "Soft_Press": entry(add("Wrong"), activation_threshold="10")}})}, "Wrong": {}, "Shifted": {}},
            shifts={"90": ("joystick", "dpad", {"touch": act(EMPTY), "edge": {
                "Soft_Press": entry(add("Shifted"), activation_threshold="10")}})})
        before = self.one(model.press(self.one(model.press(self.one(model.start()), LB)), ("joystick", "touch")))
        after = self.one(model.analog(before, ("joystick", "edge"), 20))
        solver, tr = self.relation(env, "analog_positive", before, after)
        solver.add(dict(tr.lookup_choices)["joystick"] == 1)
        self.assertEqual(solver.check(), z3.sat)
        self.assertEqual(after.stack, (0, 2))

    def test_projection_preserves_mixed_batch_orders_and_groups_pure_removals(self):
        model, env = self.make({"Base": {
            "switch": ("switches", {"left_bumper": act([add("A"), add("Outside")])}),
            "left_trigger": ("trigger", {"edge": {
                "Full_Press": [entry([add("B"), remove("A")]), entry([remove("B"), add("A")]),
                               entry(remove("Outside")), entry(remove("Outside"))],
                "Soft_Press": entry(EMPTY, activation_threshold="10")}})}, "A": {}, "B": {}, "Outside": {}})
        before = self.one(model.press(self.one(model.start()), LB))
        afters = model.analog(before, EDGE, 20)
        self.assertGreater(len(afters), 1)
        for after in afters:
            for layers in ({1, 2}, {1}, {2}, {3}):
                solver, _ = self.relation(env, "analog_positive", before, after, layers)
                self.assertEqual(solver.check(), z3.sat, (after.stack, layers))
        tr = next(t for t in env.project_transitions({3}) if t.label == "analog_positive")
        self.assertTrue(any(len(group) > 1 for group in tr.order_groups))

    def test_five_transition_slots_and_generic_induction_reuse(self):
        model, env = self.make({"Base": {"left_trigger": ("trigger", {"edge": {
            "Soft_Press": entry(add("A"), activation_threshold="10")}})}, "A": {}, "Never": {}})
        self.assertEqual(tuple(t.label for t in env.transitions()), env.KINDS)
        self.assertEqual(tuple(t.label for t in env.project_transitions({1})), env.KINDS)
        for value in ({True}, {-1}, {99}):
            with self.assertRaises(ValueError):
                tuple(env.project_transitions(value))
        proof = TimedProof(model)
        proof.symbolic = env
        proof.run()
        self.assertTrue(proof.validate()["verified"])


if __name__ == "__main__":
    unittest.main()
