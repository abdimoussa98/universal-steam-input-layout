"""SearchModel: the stack-search rules exported for the compiled engine."""
import json
from pathlib import Path
import tempfile
import unittest

from steam_layout.model import Layout
from steam_layout.search_model import SearchModel
from steam_layout.stacks import StackSpace
from test_audit_inheritance import EMPTY, act, add, build, release, remove

ROOT = Path(__file__).resolve().parents[1]


def synthetic():
    return build({
        "Base": {"switch": ("switches", {"left_bumper": act(add("L")), "right_bumper": act(add("R"))}),
                 "left_trackpad": ("absolute_mouse", {"click": act("controller_action hold_layer {{Base::H}} 0 0, , ")}),
                 "joystick": ("joystick_mouse", {"click": act("mode_shift joystick 90, , ")})},
        "R": {"switch": ("switches", {"left_bumper": act([add("M"), add("L")])})},
        "L": {"switch": ("switches", {"left_bumper": release([add("Win"), remove("L")])})},
        "M": {"switch": ("switches", {"left_bumper": release([remove("L"), remove("R"), remove("M")])}),
              "right_trackpad": ("disabled", {})},
        "H": {}, "Win": {"switch": ("switches", {"always_on_action": act(remove("Win")), "left_bumper": act(EMPTY)})}},
        modeshift={"90": ("joystick", "dpad", {"dpad_north": act(add("H"))})})


class SearchModelTests(unittest.TestCase):
    def assert_same_moves(self, layout, stacks):
        model = SearchModel(layout)
        space = StackSpace(layout, depth=0)
        holds = {t for t in model.layer_names if t in model.hold_names}
        for stack in stacks:
            expected = space._successors(stack, holds)
            got = {model.names_of(s) for s, _ in model.successors(model.ids_of(stack))}
            self.assertEqual(got, expected, stack)

    def test_synthetic_moves_match_the_python_simulator(self):
        layout = Layout(synthetic())
        self.assert_same_moves(layout, StackSpace(layout, depth=10).stacks)

    def test_real_layout_moves_match_for_every_stack_within_3_events(self):
        for variant in ("default", "alternative"):
            layout = Layout(json.loads((ROOT / f"neptune/single-set-{variant}_hold-gyro_latest.json").read_text()))
            with self.subTest(variant=variant):
                self.assert_same_moves(layout, StackSpace(layout, depth=3).stacks)

    def test_events_are_labelled_and_the_file_round_trips(self):
        model = SearchModel(Layout(synthetic()))
        self.assertEqual(model.layer_names[0], "Base")
        labels = [e["label"] for e in model.events]
        self.assertIn("Base switch/left_bumper Full_Press", labels)
        self.assertIn("release hold layer H", labels)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp, "model.txt")
            model.write(path)
            text = path.read_text().splitlines()
            self.assertEqual(text[0], f"layers {len(model.layer_names)}")
            self.assertTrue(any(line.startswith("event ") for line in text))


if __name__ == "__main__":
    unittest.main()
