"""A selected non-Soft entry still requires held input on a Soft-capable control."""
import importlib.util
import unittest

from steam_layout.model import Layout
from steam_layout.timed_model import TimedModel
from test_audit_inheritance import EMPTY, act, add, build, remove
from test_timed_phase_envelope import entry

HAVE_Z3 = importlib.util.find_spec("z3") is not None
if HAVE_Z3:
    from steam_layout.timed_progress_envelope import TimedProgressEnvelope
    from steam_layout.timed_elapsed_envelope import TimedElapsedEnvelope


@unittest.skipUnless(HAVE_Z3, "optional z3-solver dependency is not installed")
class TimedPhysicalProgressEnvelopeTests(unittest.TestCase):
    def make(self, soft_repeater=False):
        repeated = entry(remove("Other"), hold_repeats="1", repeat_rate="50",
                         **({"activation_threshold": "10", "edge_binding_invert": "1"}
                            if soft_repeater else {"chord_button": "14"}))
        edge = ({"Soft_Press": repeated} if soft_repeater else {
            "chord": repeated, "Soft_Press": entry(EMPTY, activation_threshold="10")})
        model = TimedModel(Layout(build({"Base": {
            "switch": ("switches", {"button_escape": act(add("Delayed"), delay_start="100")}),
            "joystick": ("dpad", {"touch": act(EMPTY), "edge": edge}),
            "right_trackpad": ("dpad", {"touch": act("mode_shift joystick 90, , ")})},
            "Delayed": {}, "Other": {}}, modeshift={"90": (
                "joystick", "dpad", {"touch": act(EMPTY), "edge": act(EMPTY)})})))
        return model, TimedElapsedEnvelope(model)

    def one(self, states):
        self.assertEqual(len(states), 1)
        return next(iter(states))

    def test_chord_on_globally_soft_control_uses_physical_shift_exclusion(self):
        model, envelope = self.make()
        delayed = "0/switch/button_escape/Full_Press/0"
        repeater = "0/joystick/edge/chord/0"
        pair = (delayed, repeater)
        self.assertIn(envelope.cid[("joystick", "edge")], envelope.analog_controls)
        self.assertIn(pair, {(r.delayed, r.repeater) for r in TimedProgressEnvelope(model).progress_rules})
        self.assertIn(pair, {(r.delayed, r.repeater) for r in envelope.progress_rules})
        self.assertNotIn(repeater, envelope.elapsed_chord_entries)
        state = self.one(model.press(self.one(model.start()), ("switch", "button_escape")))
        state = self.one(model.press(state, ("joystick", "touch")))
        state = self.one(model.analog(state, ("joystick", "edge"), 20))
        state = self.one(model.wait(state, 300))
        self.assertEqual(state.stack, (0,))
        state = self.one(model.analog(state, ("joystick", "edge"), 0))
        self.assertEqual(self.one(model.wait(state, 100)).stack, (0, 1))

    def test_actual_soft_entry_retains_physical_shift_exemption(self):
        _, envelope = self.make(soft_repeater=True)
        self.assertNotIn(("0/switch/button_escape/Full_Press/0", "0/joystick/edge/Soft_Press/0"),
                         {(r.delayed, r.repeater) for r in envelope.progress_rules})


if __name__ == "__main__":
    unittest.main()
