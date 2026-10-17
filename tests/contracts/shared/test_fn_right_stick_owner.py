"""Since Ibex 1.1 (Neptune 90.77, DSE 1.1): each Fn layer owns its right stick, and no two chords differ only in a button.

The record is findings/2026-10-16-fn-right-stick-owner/README.md; the plan is
plans/2026-10-16-fn-right-stick-owner.md, part 5.

- A77, the author's rule: above a layer that changed a source's mode, a group in the same mode doesn't answer; the
  owner answers the whole source. Each Fn layer's right stick is a D-pad, so in every stack the chains give, the
  right stick under it must be in another mode (Base's mouse mode), and no menu Entry Point, stick guard or Tap Cover
  may be under it. The simulator and the audits follow A1 and don't model A77; the 1.0 shape, a D-pad Entry Point
  under each Fn layer, fails this test.
- Part 4: where two chords on one input have the same bind and settings, each on one button, they are one chord on a
  mask of both, Any. No input may keep such a pair, nor a pair an Any mask could hold, on any controller.

Source: the six working layouts, read-only. Fixture responsibility: contracts/shared. See docs/testing.md.
"""
import json
import unittest

from steam_layout import controllers, convert
from steam_layout.chains import Chains
from steam_layout.model import Layout, actions, entries
from tests.support.sources import load_json

FN = ("Menu Left: Fn Layer", "Menu Right: Fn Layer", "Stateful | Menu Left: Fn Layer", "Stateful | Menu Right: Fn Layer")
HANDED_OVER = {"Menu Left: Entry Point", "Menu Right: Entry Point", "Stateful | Menu Left: Entry Point",
               "Stateful | Menu Right: Entry Point", "Menu Buttons: Left Stick Guard", "Menu Buttons: Right Stick Guard",
               "Menu Buttons: Tap Cover"}
CHORD_KEYS = ("chord_button", convert.MASK, convert.ANY_OR_ALL)


def owner_problems(layout, chains=None):
    """For each Fn layer, the stacks under it that put a menu layer there or leave its right stick a same-mode group."""
    chains = chains or Chains.of(layout)
    found = {}
    for fn in FN:
        mode = layout.active(fn)["right_joystick"]["mode"]
        stacks = list(chains.below(fn))
        bad = []
        for stack in stacks:
            under = next((layout.active(t)["right_joystick"]["mode"] for t in reversed(stack)
                          if "right_joystick" in layout.active(t)), None)
            if set(stack) & HANDED_OVER or under == mode:
                bad.append(stack)
        found[fn] = (mode, len(stacks), bad)
    return found


def buttons(settings):
    """The mask bits a chord waits for, and whether an Any mask could hold them: one button, or a mask that is Any."""
    if convert.MASK in settings:
        value = int(settings[convert.MASK])
        bits = {bit for bit in range(64) if value >> bit & 1}
        return bits, len(bits) == 1 or settings.get(convert.ANY_OR_ALL) != "1"
    return {convert.BITS[convert.CHORD_INPUTS[settings["chord_button"]]]}, True


def mergeable(layout):
    """Every input with two chords of the same bind and settings that an Any mask could hold as one."""
    found = []
    for title in layout.presets:
        for source, group in layout.active(title).items():
            for name, value in (group.get("inputs") or {}).items():
                shapes = {}
                for kind, entry in entries(value.get("activators") or {}):
                    settings = entry.get("settings") or {}
                    if kind != "chord" or not set(CHORD_KEYS[:2]) & set(settings):
                        continue
                    shape = json.dumps([actions(entry), {k: v for k, v in settings.items() if k not in CHORD_KEYS}])
                    shapes.setdefault(shape, []).append(buttons(settings))
                for same in shapes.values():
                    if len(same) > 1 and all(any_ok for _, any_ok in same):
                        found.append(f"{title} / {source}/{name}")
    return found


class FnOwnsItsRightStick(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.layouts = {path: Layout(convert.readable(load_json(path))) for path in controllers.working_layouts()}

    def test_each_fn_layer_owns_its_right_stick_with_no_menu_layer_under_it(self):        # A77
        for path, layout in self.layouts.items():
            for fn, (mode, count, bad) in owner_problems(layout).items():
                with self.subTest(path.name, layer=fn):
                    self.assertEqual(mode, "dpad")
                    self.assertGreater(count, 0)
                    self.assertEqual(bad, [])

    def test_no_input_keeps_two_chords_an_any_mask_could_hold_as_one(self):                # part 4
        for path, layout in self.layouts.items():
            with self.subTest(path.name):
                self.assertEqual(mergeable(layout), [])


if __name__ == "__main__":
    unittest.main()
