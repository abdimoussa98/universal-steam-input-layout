"""90.70: every cleanup function in the Steering layers adds the Entry Guard before it removes.

From 90.68. The author, 2026-10-13: "for 90.70 keep the changes from 90.68 and have all the steering cleanups add the
entry steering guard." 90.67 had the add on the left stick's edge of ten Steering layers; a cleanup press can run past
its guard chord on any input (A69), so the other 80 cleanup presses of those layers carry it too.

The simulator never runs a press past its guard and is not made to (the author, on 90.67). The scenarios state the
ordinary cleanup, which carries the same add.
"""

import unittest

from steam_layout.flow_model import Inventory
from steam_layout.model import Layout, actions, entries
from tests.scenario import VARIANTS, ScenarioCase, frozen_layout_data, layout_data, scenario
from tests.test_scenarios_90_55 import DRIVERS, EDGE_CHORDS
from tests.test_scenarios_90_61 import inputs, named

GUARD = 'Steering | LS: Entry Guard'
KEYS = {'up': 'W', 'down': 'S'}


def cleanups(layout):
    return [t for t in Inventory.of(layout).transitions if t.role == 'recovery']


class Shape(unittest.TestCase):

    def test_every_steering_cleanup_press_repeats_and_stores_the_entry_guard_add_last(self):
        for variant in VARIANTS:
            layout, name = Layout(layout_data(variant)), named(variant)
            found = [t for t in cleanups(layout) if t.layer.startswith('Steering')]
            self.assertEqual(len(found), 90, variant)
            self.assertEqual({t.layer for t in found}, {name(title) for title in EDGE_CHORDS})
            for t in found:
                _, entry = list(entries(layout.active(t.layer)[t.source]['inputs'][t.input]['activators']))[t.index]
                self.assertEqual(t.ops[0], ('add_layer', GUARD), t)                       # in run order
                self.assertTrue(all(op == 'remove_layer' for op, _ in t.ops[1:]) and len(t.ops) > 1, t)
                self.assertIn('add_layer', actions(entry)[-1], t)                         # stored last (A4)
                self.assertEqual((entry['settings'].get('hold_repeats'), t.interruptible), ('1', True), t)

    def test_no_cleanup_function_outside_the_steering_layers_adds_a_layer(self):
        for variant in VARIANTS:
            found = [t for t in cleanups(Layout(layout_data(variant))) if not t.layer.startswith('Steering')]
            # 439 and 465 until 90.71; 90.72 adds the pad layers' sixteen stick-edge cleanups.
            self.assertEqual(len(found), {'default': 455, 'alternative': 481}[variant])
            self.assertFalse([t for t in found if any(op == 'add_layer' for op, _ in t.ops)], variant)

    def test_against_90_68_eighty_presses_gain_the_add_and_nothing_else_differs(self):
        for variant in VARIANTS:
            name = named(variant)
            old, new = inputs(Layout(frozen_layout_data(variant, '90.68'))), inputs(Layout(frozen_layout_data(variant, '90.70')))
            self.assertEqual(old.keys(), new.keys())
            differ = {key for key in old if old[key] != new[key]}
            self.assertTrue(all(key[0] in {name(title) for title in EDGE_CHORDS} for key in differ), variant)
            self.assertFalse([key for key in differ if key[1:] == ('joystick', 'edge')], variant)       # 90.67 did those
            gained = 0
            for key in differ:
                for (kind, settings, ops), (was_kind, was_settings, was) in zip(new[key], old[key]):
                    self.assertEqual((kind, settings), (was_kind, was_settings), key)
                    if ops != was:
                        self.assertEqual(ops, [('add_layer', GUARD)] + was, key)
                        gained += 1
            self.assertEqual(gained, 80, variant)


class TheGuardInEveryCleanup(ScenarioCase):
    """A driver's release is missed (A25), so its layer stays on with no driver held, and a cleanup function on
    another input than the left stick's edge clears it."""

    @scenario('90.70 J1', rules=('R176',), rests=('A4', 'A25', 'A61'), either=('A9', 'A32'))
    def test_with_the_stick_at_centre_the_guard_comes_and_leaves_at_once(self):
        # The guard's own inverted chord takes it off: the stick is inside the ring and no driver is held.
        for driver, owner, _ in DRIVERS:
            for pad in self.each(start=('Base', 'Steering')):
                pad.hold(driver).wait(300).miss(driver).wait(100).mark()
                pad.touch('RS').wait(20)
                self.assertTrue(pad.has('Steering') and pad.lacks(owner, GUARD), driver)
                self.assertEqual(pad.down(), [])

    @scenario('90.70 J2', rules=('R176',), rests=('A4', 'A10', 'A25', 'A61'), either=('A9', 'A32'))
    def test_with_the_stick_up_or_down_a_button_cleanup_leaves_the_guard_and_steering_stays(self):
        # A's cleanup function is the stick modifier's and removes only that layer, so the stale driver layer
        # stays under the guard until the stick comes back. On 90.68 the driver layer's left edge then ran and
        # left the guard by itself; here the guard is over that edge.
        for pad, driver, owner, direction in self.out():
            self.assertTrue(pad.has('Steering', GUARD), (driver, direction))
            self.assertFalse([title for title in pad.stack if 'Modifier' in title], (driver, direction))
            self.assertIn(KEYS[direction], pad.down())
            pad.let_go('A').recentre('LS').wait(300)
            self.assertTrue(pad.has('Steering') and pad.lacks(GUARD, owner), (driver, direction))
            self.assertEqual(pad.down(), [])

    def out(self):
        # The stick goes out with the driver held, so the left edge's own press is held back; then the release is
        # missed and a face button's cleanup function clears the stale layers.
        for driver, owner, _ in DRIVERS:
            for direction in KEYS:
                for pad in self.each(start=('Base', 'Steering')):
                    pad.touch('LS').hold(driver).push('LS', direction).wait(60).miss(driver).hold('A').wait(100)
                    yield pad, driver, pad.title(owner), direction


if __name__ == '__main__':
    unittest.main()
