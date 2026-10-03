"""Differential checks for the full-stack symbolic event relation."""
import importlib.util
import itertools
import json
from pathlib import Path
import unittest

from steam_layout.held_model import HeldModel, SHIFT_TAP, explore
from steam_layout.model import Layout
from test_audit_inheritance import EMPTY, act, add, build, release, remove
from test_held_model import guarded_layout, pad_layout

HAVE_Z3 = importlib.util.find_spec("z3") is not None
if HAVE_Z3:
    import z3
    from steam_layout.symbolic import SymbolicModel


@unittest.skipUnless(HAVE_Z3, "optional z3-solver dependency is not installed")
class SymbolicTests(unittest.TestCase):
    def compare(self, model, states):
        symbolic = SymbolicModel(model)
        transitions = list(symbolic.transitions())
        for state in states:
            self.assertEqual(symbolic.successor_states(state, transitions), model.successors(state), state)
        return symbolic, transitions

    def test_every_valid_state_of_guarded_fixture(self):
        # Include unreachable stacks: induction must also model these correctly.
        model = HeldModel(Layout(guarded_layout()))
        controls = [c for c, owner in enumerate(model.owner) if owner]
        holds = [frozenset(c for c, bit in zip(controls, bits) if bit)
                 for bits in itertools.product((False, True), repeat=len(controls))]
        holds = [h for h in holds if model.valid(h)]
        states = [((0,) + stack, held, False)
                  for length in range(len(model.layer_names))
                  for stack in itertools.permutations(range(1, len(model.layer_names)), length)
                  for held in holds]
        self.compare(model, states)

    def test_pad_touch_hold_layer_delays_and_repeats(self):
        model = HeldModel(Layout(pad_layout()))
        self.compare(model, explore(model))

    def test_disabled_sources_reordering_and_simultaneous_entries(self):
        data = build({
            "Base": {"switch": ("switches", {
                "left_bumper": {"Full_Press": [
                    {"bindings": {"binding": [add("A"), remove("A")]}},
                    {"bindings": {"binding": add("B")}},
                    {"bindings": {"binding": add("A")}}]},
                "right_bumper": act([add("A"), remove("A"), add("B")]),
                "button_menu": act(add("Blocked"))})},
            "A": {}, "B": {},
            "Blocked": {"switch": ("disabled", {})}})
        model = HeldModel(Layout(data))
        states = [((0,) + stack, frozenset(), False)
                  for n in range(4) for stack in itertools.permutations(range(1, 4), n)]
        self.compare(model, states)

    def test_more_than_three_entries_preserves_reference_order(self):
        data = build({"Base": {"switch": ("switches", {"left_bumper": {
            "Full_Press": [{"bindings": {"binding": add(name)}} for name in ("A", "B", "C", "D")]}})},
                      "A": {}, "B": {}, "C": {}, "D": {}})
        model = HeldModel(Layout(data))
        self.compare(model, [model.start(), ((0, 3, 1), frozenset(), False)])

    def test_shift_tap_uses_explicit_entries_through_release(self):
        data = build({
            "Base": {"joystick": ("joystick_mouse", {
                "touch": release([EMPTY]),
                "click": {**act("mode_shift joystick 90, , "), **release([EMPTY])},
                "dpad_north": act(EMPTY)})},
            "A": {}, "B": {}},
            modeshift={"90": ("joystick", "dpad", {"dpad_north": {
                **act(add("A")), **release([add("B"), remove("A")])}})})
        model = HeldModel(Layout(data))
        held = frozenset(model.cid[("joystick", name)] for name in ("touch", "click"))
        state = ((0,), held, False)
        symbolic, transitions = self.compare(model, [model.start(), state, ((0, 2, 1), held, False)])
        self.assertTrue(any(event[1] == SHIFT_TAP for _, event in symbolic.successor_states(state, transitions)))

    def test_noncanonical_rank_gaps_preserve_order(self):
        model = HeldModel(Layout(guarded_layout()))
        symbolic = SymbolicModel(model)
        solver = z3.Solver()
        solver.add(symbolic.domain, symbolic.ranks[0] == 1, symbolic.ranks[1] == 4,
                   symbolic.ranks[2] == 0, symbolic.ranks[3] == 2)
        self.assertEqual(solver.check(), z3.sat)
        solver.add(symbolic.ranks[3] == symbolic.ranks[1])
        self.assertEqual(solver.check(), z3.unsat)

    def test_missed_release_model_rejected(self):
        with self.assertRaisesRegex(ValueError, "missed=False"):
            SymbolicModel(HeldModel(Layout(guarded_layout()), missed=True))

    def test_default_layout_start_and_real_rocking_path(self):
        root = Path(__file__).resolve().parents[1]
        model = HeldModel(Layout(json.loads((root / "neptune/single-set-default_hold-gyro_latest.json").read_text())))
        from steam_layout.held_model import PRESS, LATER, RELEASE
        state = model.start()
        states = [state]
        for button, phase in (("left_bumper", PRESS), ("right_bumper", PRESS),
                              ("right_bumper", LATER), ("left_bumper", RELEASE)):
            control = model.cid[("switch", button)]
            state = sorted((n for n, event in model.successors(state) if event == (control, phase)),
                           key=lambda s: (len(s[0]), s[0]))[-1]
            states.append(state)
        self.compare(model, states)


if __name__ == "__main__":
    unittest.main()
