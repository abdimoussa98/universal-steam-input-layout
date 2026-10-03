"""Additional physical-event obligations for the timed proof envelope."""
from dataclasses import replace
import importlib.util
import unittest

from steam_layout.model import Layout
from steam_layout.timed_model import TimedModel, TimedState
from test_audit_inheritance import EMPTY, act, add, build, remove


HAVE_Z3 = importlib.util.find_spec("z3") is not None
if HAVE_Z3:
    import z3
    from steam_layout.timed_envelope import TimedEnvelope


@unittest.skipUnless(HAVE_Z3, "optional z3-solver dependency is not installed")
class TimedEnvelopeReviewTests(unittest.TestCase):
    def relation(self, model, kind, before, after):
        envelope = TimedEnvelope(model)
        transition = next(t for t in envelope.transitions() if t.label == kind)
        solver = z3.Solver()
        solver.add(envelope.domain, envelope.state_formula(before), transition.guard,
                   envelope.state_formula(after, transition.ranks, transition.held, transition.analog))
        return solver

    def test_release_cannot_skip_mandatory_cleanup_as_a_missed_release(self):
        model = TimedModel(Layout(build({"Base": {"switch": ("switches", {
            "left_bumper": {**act(add("A")),
                            "release": {"bindings": {"binding": remove("A")}}}})}, "A": {}})))
        before = next(iter(model.press(next(iter(model.start())), ("switch", "left_bumper"))))
        after = next(iter(model.release(before, ("switch", "left_bumper"))))
        self.assertEqual(self.relation(model, "release", before, after).check(), z3.sat)
        missed = replace(after, stack=before.stack)
        self.assertEqual(self.relation(model, "release", before, missed).check(), z3.unsat)

    def test_dependent_click_blocks_touch_release_in_the_transition_guard(self):
        model = TimedModel(Layout(build({"Base": {"left_trackpad": ("dpad", {
            "touch": act(EMPTY), "click": act(EMPTY)})}})))
        before = TimedState(held=frozenset({("left_trackpad", "touch"), ("left_trackpad", "click")}))
        impossible = replace(before, held=frozenset({("left_trackpad", "click")}))
        self.assertFalse(model._valid(impossible.held))
        self.assertEqual(self.relation(model, "release", before, impossible).check(), z3.unsat)

    def test_press_can_immediately_enable_chord_on_another_held_control(self):
        model = TimedModel(Layout(build({"Base": {"switch": ("switches", {
            "left_bumper": act(EMPTY),
            "right_bumper": {"chord": {"bindings": {"binding": add("A")},
                                         "settings": {"chord_button": "1"}}}})}, "A": {}})))
        before = next(iter(model.press(next(iter(model.start())), ("switch", "right_bumper"))))
        after = next(iter(model.press(before, ("switch", "left_bumper"))))
        self.assertEqual(after.stack, (0, 1))
        self.assertEqual(self.relation(model, "press", before, after).check(), z3.sat)


if __name__ == "__main__":
    unittest.main()
