"""90.56: the left edge's cleanup is the press and its guard chord again in ten Steering layers; only the Entry Guard keeps a chord with Invert Activation."""

import unittest

from steam_layout.model import EMPTY, Layout, actions, entries, map_title
from tests.scenario import RENAME, ScenarioCase, layout_data, scenario

DEFLECT = 1 << 30                                         # the left stick's deflect, bit 30
MARKER, COVER = 'Steering | LS: Tap Cover', 'Steering | LS: Double Tap Cover'
GUARD = 'Steering | LS: Entry Guard'
# driver, its layer, its key
DRIVERS = (('R1', 'Steering | R1: W Key', 'W'), ('L1', 'Steering | L1: S Key', 'S'))
# direction, input, modifier, window, scroll layer
SIDES = (('up', 'dpad_north', 'Steering | LS Up: Modifier 1', 'Steering | LS Up: Double Tap', 'Steering | LS Up: Scroll Up'),
         ('down', 'dpad_south', 'Steering | LS Down: Modifier 0', 'Steering | LS Down: Double Tap', 'Steering | LS Down: Scroll Down'))
STICK_MODIFIERS = tuple(side[2] for side in SIDES)
SCROLLS = tuple(side[4] for side in SIDES)
MODIFIER_2 = ('Steering | R1!L1: Modifier 2', 'Steering | L1!R1: Modifier 2')
FAMILY = tuple(t for side in SIDES for t in side[2:5]) + (MARKER, COVER)
EDGES = (*(d[1] for d in DRIVERS), *STICK_MODIFIERS, MARKER, COVER, *SCROLLS, *MODIFIER_2)
TIMERS = (*STICK_MODIFIERS, *SCROLLS)                     # their edge also holds the timer's Soft Press (90.55)


class EdgeCleanup(ScenarioCase):
    """The author's fault on 90.55: a thumb lifting in the stick modifiers cleared the W or S layer and ended
    `Steering`. The author suspects the chord with Invert Activation fires after a remove_layer call although a
    bumper is held. The simulator never showed it (A61), so these say what the binds are meant to do."""

    def held(self):
        for driver, owner, key in DRIVERS:
            for pad in self.each(start=('Base', 'Steering')):
                pad.hold(driver).touch('LS').wait(300)
                yield pad, driver, owner, key

    @scenario('90.56 E1', rules=('R133', 'R170'), rests=('A27', 'A36'), either=('A9', 'A32'))
    def test_no_stick_movement_removes_the_driver_layer_while_the_driver_is_held(self):
        for pad, _, owner, key in self.held():
            for direction in ('up', 'down', 'up', 'left', 'right', 'down'):
                for ms in (30, 60, 150, 300):
                    pad.flick('LS', direction, ms)
                    self.assertTrue(pad.has('Steering', owner))
                    self.assertIn(key, pad.down())
                    pad.wait(40)
            for _ in range(3):                               # the edge alone, out and back
                pad.hold('LS edge').wait(40).let_go('LS edge').wait(40)
                self.assertTrue(pad.has('Steering', owner))
            pad.wait(400)
            self.assertTrue(pad.has('Steering', owner) and pad.lacks(*FAMILY))
            self.assertEqual(pad.down(), [key])

    @scenario('90.56 E2', rules=('R133',), rests=('A25', 'A27'), either=('A9', 'A32'))
    def test_a_missed_driver_release_clears_when_the_stick_reaches_the_edge(self):
        # The press runs when the edge goes out with no driver held. The inverted chord of 90.55 ran as it came back.
        for pad, driver, owner, _ in self.held():
            pad.miss(driver).wait(300)
            self.assertTrue(pad.has(owner))                  # nothing has told the layout yet
            pad.hold('LS edge').wait(100)
            self.assertTrue(pad.has('Steering') and pad.lacks(owner, *FAMILY))
            pad.let_go('LS edge').wait(100)
            self.assertEqual(pad.down(), [])

    @scenario('90.56 E3', rules=('R133',), rests=('A6', 'A25', 'A27'), either=('A9', 'A32'))
    def test_a_missed_driver_release_during_a_deflect_leaves_no_stick_layer(self):
        for driver, owner, _ in DRIVERS:
            for direction, _, _, _, _ in SIDES:
                for pad in self.each(start=('Base', 'Steering')):
                    pad.hold(driver).touch('LS').wait(300).push('LS', direction).wait(100).miss(driver).wait(600)
                    pad.recentre('LS').wait(400)
                    self.assertTrue(pad.lacks(owner, *FAMILY))
                    pad.lift('LS').wait(300)
                    self.assertEqual(pad.down(), [])

    @scenario('90.56 E4', rules=('R133',), rests=('A7', 'A27', 'A36'), either=('A9', 'A32'))
    def test_a_thumb_lifting_at_any_stage_keeps_the_driver_layer_and_steering(self):
        # The thumbs rest before the driver goes down, so the stick helpers are under the driver's layer and
        # each lift takes real layers off. The right thumb lifts, then the left one loses touch with the stick out.
        for driver, owner, key in DRIVERS:
            for direction, _, modifier, _, layer in SIDES:
                for stage in ('modifier', 'marker', 'scroll', 'cover'):
                    for pad in self.each(start=('Base', 'Steering')):
                        pad.touch('LS').touch('RS').wait(400).hold(driver).wait(300)
                        self.assertTrue(pad.has('LST: Entry Point', 'RST: Entry Point', owner))
                        if stage in ('modifier', 'marker'):
                            pad.push('LS', direction).wait(60 if stage == 'modifier' else 300)
                        else:
                            pad.flick('LS', direction).wait(20).push('LS', direction).wait(60 if stage == 'scroll' else 300)
                        self.assertTrue(pad.has(layer if stage in ('scroll', 'cover') else modifier), stage)
                        pad.lift('RS').wait(60)
                        self.assertTrue(pad.has('Steering', owner) and key in pad.down(), stage)
                        pad.sim.release(('joystick', 'touch'))
                        pad.wait(60)
                        self.assertTrue(pad.has('Steering', owner) and key in pad.down(), stage)
                        pad.recentre('LS').wait(400)
                        self.assertTrue(pad.has('Steering', owner) and pad.lacks(*FAMILY), stage)
                        self.assertEqual(pad.down(), [key])
                        pad.let_go(driver).wait(300)
                        self.assertEqual(pad.down(), [])


class EdgeCleanupShape(unittest.TestCase):
    def each(self):
        for variant in ('default', 'alternative'):
            layout = Layout(layout_data(variant))
            yield layout, (lambda title, v=variant: map_title(title, RENAME) if v == 'alternative' else title)

    def test_the_ten_edges_hold_the_cleanup_press_and_its_guard_chord(self):
        for layout, name in self.each():
            for title in EDGES:
                found = list(entries(layout.active(name(title))['joystick']['inputs']['edge']['activators']))
                kinds = [kind for kind, _ in found]
                self.assertEqual(kinds, ['Full_Press', 'chord', 'Soft_Press'] if title in TIMERS else ['Full_Press', 'chord'], title)
                press, guard = found[0][1], found[1][1]
                self.assertEqual(press['settings'].get('hold_repeats'), '1', title)
                self.assertNotEqual(press['settings'].get('interruptable'), '0', title)          # the guard can hold it back
                ops = layout.layer_ops(press)
                self.assertIn(('remove_layer', name(title)), ops)
                self.assertTrue(all(op == 'remove_layer' for op, _ in ops), title)
                self.assertEqual(actions(guard), [EMPTY + ', , '], title)
                self.assertEqual(guard['settings'].get('interruptable'), '0', title)
                self.assertNotIn('edge_binding_invert', guard['settings'], title)
                self.assertFalse(int(guard['settings']['gyro_ratchet_button_mask']) & DEFLECT, title)

    def test_only_the_entry_guard_has_a_chord_with_invert_activation_and_it_removes_only_itself(self):
        for layout, name in self.each():
            found = [(title, source, control, entry) for title in layout.presets
                     for source, group in layout.active(title).items()
                     for control, value in (group.get('inputs') or {}).items()
                     for kind, entry in entries(value.get('activators', {}))
                     if kind == 'chord' and (entry.get('settings') or {}).get('edge_binding_invert') == '1']
            self.assertEqual([(title, source, control) for title, source, control, _ in found], [(GUARD, 'joystick', 'edge')])
            self.assertEqual(layout.layer_ops(found[0][3]), [('remove_layer', GUARD)])


if __name__ == '__main__':
    unittest.main()
