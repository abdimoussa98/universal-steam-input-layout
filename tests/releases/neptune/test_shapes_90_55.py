"""90.55: the Steering stick's four timers are Soft Presses on the left stick's edge, the left edge cleans up with one inverted chord, and the unnecessary removes are gone.

Fixture responsibility: releases/neptune. See docs/testing.md and tests/test-map.csv.
"""
from tests.support.fixtures.scenarios_90_55 import *

class EdgeTimersShape(unittest.TestCase):
    def each(self, frozen=None):
        for variant in ('default', 'alternative'):
            layout = Layout(frozen_layout_data(variant, frozen) if frozen else layout_data(variant))
            yield layout, (lambda title, v=variant: map_title(title, RENAME) if v == 'alternative' else title)


    def test_the_left_edge_cleans_up_with_one_inverted_chord_and_holds_the_timer_as_a_soft_press(self):
        timers = {layer: (target, delay) for layer, _, target, delay, _ in TIMERS}
        for layout, name in self.each(frozen='90.55'):               # 90.56 put the press and its guard back
            for title in EDGE_CHORDS:
                found = list(entries(layout.active(name(title))['joystick']['inputs']['edge']['activators']))
                self.assertEqual([kind for kind, _ in found], ['chord', 'Soft_Press'] if title in timers else ['chord'], title)
                chord = found[0][1]
                settings = dict(chord['settings'])
                mask = int(settings.pop('gyro_ratchet_button_mask'))
                self.assertEqual(settings, {'gyro_ratchet_button_requireany_or_all': '0', 'edge_binding_invert': '1',
                                            'hold_repeats': '1', 'interruptable': '0', 'haptic_intensity': '0'}, title)
                self.assertFalse(mask & DEFLECT)
                ops = layout.layer_ops(chord)
                self.assertIn(('remove_layer', name(title)), ops)
                self.assertTrue(all(op == 'remove_layer' for op, _ in ops), title)
                if title in timers:
                    target, delay = timers[title]
                    timer = found[1][1]
                    self.assertEqual(actions(timer), [a for a in actions(timer) if 'add_layer' in a])
                    self.assertEqual(layout.layer_ops(timer), [('add_layer', target)], title)
                    self.assertEqual(timer['settings'], {'delay_start': delay, 'activation_threshold': THRESHOLD,
                                                         'interruptable': '0'}, title)






    def test_the_modifier_2_entry_removes_the_stick_family_and_its_own_hold_marker_only(self):
        # On the 90.56 build. 90.57 took the hold marker and the two windows out of this list
        # (test_scenarios_90_57: the W and S layers name no layer that answers the same driver).
        windows = tuple(side[3] for side in SIDES)
        for layout, name in self.each(frozen='90.56'):
            for (_, owner, _), (other, _, _), second in zip(DRIVERS, DRIVERS[::-1], MODIFIER_2):
                found = [e for group in layout.active(name(owner)).values() for value in group.get('inputs', {}).values()
                         for kind, e in entries(value.get('activators', {}))
                         if kind == 'chord' and ('add_layer', name(second)) in layout.layer_ops(e)]
                self.assertEqual(len(found), 1, owner)
                ops = layout.layer_ops(found[0])
                self.assertEqual(ops[-1], ('add_layer', name(second)))
                marker = name(f'{other}: Tap Cover')             # the hold marker of the Modifier 2 it enters
                self.assertEqual(sorted(t for _, t in ops[:-1]), sorted((*STICK_MODIFIERS, *windows, *SCROLLS, MARKER, COVER, marker)))


if __name__ == "__main__":
    unittest.main()
