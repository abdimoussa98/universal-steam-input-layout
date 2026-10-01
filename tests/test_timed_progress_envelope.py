"""Boundary cases for ordered-owner progress diagnostics."""
from dataclasses import replace
import importlib.util
import unittest

from steam_layout.model import Layout
from steam_layout.timed_model import TimedModel, TimedState
from test_audit_inheritance import EMPTY, act, add, build, remove

HAVE_Z3 = importlib.util.find_spec("z3") is not None
if HAVE_Z3:
    import z3
    from steam_layout.timed_progress_envelope import TimedProgressEnvelope

LB = ("switch", "left_bumper")
RB = ("switch", "right_bumper")


def switches(inputs):
    return {"switch": ("switches", inputs)}


@unittest.skipUnless(HAVE_Z3, "optional z3-solver dependency is not installed")
class TimedProgressEnvelopeTests(unittest.TestCase):
    def make(self, layers, shifts=None):
        model = TimedModel(Layout(build(layers, modeshift=shifts)))
        return model, TimedProgressEnvelope(model)

    def one(self, states):
        self.assertEqual(len(states), 1)
        return next(iter(states))

    def automatic(self, envelope, before, after, layers=None):
        transitions = (envelope.transitions() if layers is None else
                       envelope.project_transitions(layers))
        tr = next(t for t in transitions if t.label == "automatic")
        solver = z3.Solver()
        solver.add(envelope.domain, envelope.state_formula(before), tr.guard,
                   envelope.state_formula(after, tr.ranks, tr.held, tr.analog))
        return solver, tr

    def test_faster_addition_must_be_present_before_delayed_firing(self):
        model, envelope = self.make({"Base": switches({
            "left_bumper": act(add("Earlier"), hold_repeats="1", repeat_rate="50"),
            "right_bumper": act(add("Later"), delay_start="100")}), "Earlier": {}, "Later": {}})
        before = TimedState(held=frozenset({LB, RB}))
        after = replace(before, stack=(0, 2))
        solver, _ = self.automatic(envelope, before, after)
        self.assertEqual(solver.check(), z3.unsat)
        # The repeater's output is omitted from this projection, but its
        # eligibility and absent target remain part of the input guard.
        solver, _ = self.automatic(envelope, before, after, {2})
        self.assertEqual(solver.check(), z3.unsat)
        actual = self.one(model.press(self.one(model.press(self.one(model.start()), LB)), RB))
        final = self.one(model.wait(actual, 100))
        self.assertEqual(final.stack, (0, 1, 2))

    def test_readding_an_existing_layer_does_not_starve_a_delayed_entry(self):
        model, envelope = self.make({"Base": switches({
            "left_bumper": act(add("Earlier"), hold_repeats="1", repeat_rate="50"),
            "right_bumper": act(add("Later"), delay_start="100")}), "Earlier": {}, "Later": {}})
        before = self.one(model.press(self.one(model.press(self.one(model.start()), LB)), RB))
        before = self.one(model.wait(before, 50))
        after = self.one(model.wait(before, 50))
        solver, tr = self.automatic(envelope, before, after)
        solver.add(*(take for _, take in tr.selected))
        self.assertEqual(solver.check(), z3.sat)

    def test_lower_repeater_constrains_a_delayed_entry_in_an_upper_owner(self):
        _, envelope = self.make({
            "Base": switches({"left_bumper": act(add("Earlier"), hold_repeats="1", repeat_rate="50")}),
            "Upper": switches({"right_bumper": act(add("Later"), delay_start="100")}),
            "Earlier": {}, "Later": {}})
        before = TimedState(stack=(0, 1), held=frozenset({LB, RB}))
        solver, _ = self.automatic(envelope, before, replace(before, stack=(0, 1, 3)))
        self.assertEqual(solver.check(), z3.unsat)

    def test_aged_transfer_from_a_lower_owner_keeps_the_order_guard_false(self):
        delayed = act(add("Later"), delay_start="100")
        model, envelope = self.make({
            "Base": switches({"left_bumper": act(EMPTY), "right_bumper": delayed,
                              "button_menu": act(add("Repeater")), "button_escape": act(add("Upper"))}),
            "Repeater": switches({"left_bumper": act(add("Earlier"), hold_repeats="1", repeat_rate="50")}),
            "Upper": switches({"right_bumper": delayed}), "Earlier": {}, "Later": {}})
        before = self.one(model.press(self.one(model.press(self.one(model.start()), LB)), RB))
        before = self.one(model.wait(before, 50))
        before = self.one(model.press(before, ("switch", "button_menu")))
        before = self.one(model.wait(before, 10))
        before = self.one(model.press(before, ("switch", "button_escape")))
        afters = model.wait(before, 40)
        self.assertEqual(len(afters), 2)
        for after in afters:
            solver, tr = self.automatic(envelope, before, after)
            due = {active.entry_id for active in before.activations
                   if active.deadline_ms == before.now_ms + 40}
            solver.add(*(take == (eid in due) for eid, take in tr.selected))
            self.assertEqual(solver.check(), z3.sat)

    def test_every_present_delayed_family_owner_above_repeater_allows_progress_guard(self):
        delayed = act(add("Later"), delay_start="100")
        _, envelope = self.make({
            "Base": switches({"left_bumper": act(add("Earlier"), hold_repeats="1", repeat_rate="50")}),
            "Lower": switches({"right_bumper": delayed}),
            "Upper": switches({"right_bumper": delayed}), "Earlier": {}, "Later": {}})
        before = TimedState(stack=(0, 1, 2), held=frozenset({LB, RB}))
        solver, _ = self.automatic(envelope, before, replace(before, stack=(0, 1, 2, 4)))
        self.assertEqual(solver.check(), z3.unsat)

    def test_shift_reveal_is_excluded_and_can_cofire_with_aged_delay(self):
        model, envelope = self.make({"Base": {
            "switch": ("switches", {"left_bumper": act("mode_shift joystick 90, , "),
                                    "right_bumper": act(add("Later"), delay_start="100")}),
            "joystick": ("dpad", {"touch": act(EMPTY), "click": act(
                add("Earlier"), hold_repeats="1", repeat_rate="50")})}, "Earlier": {}, "Later": {}},
            shifts={"90": ("joystick", "dpad", {"touch": act(EMPTY), "click": act(EMPTY)})})
        self.assertFalse(envelope.progress_rules)
        before = self.one(model.start())
        for control in (LB, ("joystick", "touch"), ("joystick", "click"), RB):
            before = self.one(model.press(before, control))
        before = self.one(model.wait(before, 50))
        before = self.one(model.release(before, LB))
        afters = model.wait(before, 50)
        self.assertEqual(len(afters), 2)
        for after in afters:
            solver, _ = self.automatic(envelope, before, after)
            self.assertEqual(solver.check(), z3.sat)

    def test_equal_period_remains_outside_the_progress_rule(self):
        _, envelope = self.make({"Base": switches({
            "left_bumper": act(add("Earlier"), hold_repeats="1", repeat_rate="50"),
            "right_bumper": act(add("Later"), delay_start="50")}), "Earlier": {}, "Later": {}})
        self.assertFalse(envelope.progress_rules)

    def test_physical_incompatibility_of_every_shift_origin_permits_progress(self):
        model, envelope = self.make({"Base": {
            "switch": ("switches", {
                "button_menu": act(add("Later"), delay_start="100"),
                "left_trackpad_touch": act("mode_shift button_diamond 90, , "),
                "right_trackpad_touch": act("mode_shift button_diamond 90, , ")}),
            "button_diamond": ("buttons", {"button_b": act(
                add("Earlier"), hold_repeats="1", repeat_rate="50")})},
            "Earlier": {}, "Later": {}}, shifts={"90": (
                "button_diamond", "buttons", {"button_b": act(EMPTY)})})
        self.assertEqual(len(envelope.progress_rules), 1)
        before = TimedState(held=frozenset({("switch", "button_menu"),
                                           ("button_diamond", "button_b")}))
        solver, _ = self.automatic(envelope, before, replace(before, stack=(0, 2)))
        self.assertEqual(solver.check(), z3.unsat)
        state = self.one(model.press(self.one(model.start()), ("switch", "button_menu")))
        state = self.one(model.press(state, ("button_diamond", "button_b")))
        self.assertEqual(self.one(model.wait(state, 100)).stack, (0, 1, 2))

    def test_press_must_fire_every_newly_eligible_nonown_chord(self):
        from test_timed_model import entry
        model, envelope = self.make({"Base": switches({
            "left_bumper": {"chord": entry(add("Required"), chord_button="2")},
            "right_bumper": act(add("Own"))}), "Required": {}, "Own": {}})
        before = self.one(model.press(self.one(model.start()), LB))
        afters = model.press(before, RB)
        self.assertEqual(len(afters), 2)
        for layers in (None, {1, 2}):
            transitions = (envelope.transitions() if layers is None else
                           envelope.project_transitions(layers))
            tr = next(t for t in transitions if t.label == "press")
            for after in afters:
                solver = z3.Solver()
                solver.add(envelope.domain, envelope.state_formula(before), tr.guard,
                           envelope.state_formula(after, tr.ranks, tr.held, tr.analog))
                self.assertEqual(solver.check(), z3.sat)
            omitted = replace(next(iter(afters)), stack=(0, 2))
            solver = z3.Solver()
            solver.add(envelope.domain, envelope.state_formula(before), tr.guard,
                       envelope.state_formula(omitted, tr.ranks, tr.held, tr.analog))
            self.assertEqual(solver.check(), z3.unsat)
