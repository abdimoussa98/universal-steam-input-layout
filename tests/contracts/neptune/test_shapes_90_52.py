"""90.52: the Steering stick deflect follows the bumper modifier lifecycle, with a scroll layer for the second deflect.

Fixture responsibility: contracts/neptune. See docs/testing.md and tests/test-map.csv.
"""
from tests.support.fixtures.scenarios_90_52 import *

class StickDeflectShape(unittest.TestCase):
    def each(self):
        for variant in ('default', 'alternative'):
            yield Layout(layout_data(variant))

    def stick(self, layout, title, name):
        return list(entries(layout.active(title)['joystick']['inputs'][name]['activators']))

    def test_a_modifiers_direction_has_the_reset_the_deflect_chord_and_the_release(self):
        # Since 90.53 the 200 ms chord on the deflect sits on the drivers, not on the direction: a start delay
        # owned by a stick direction misfires (A63; tests/test_scenarios_90_53.py). The reset and the Release stay.
        for layout in self.each():
            for _, name, modifier, window, _, _ in SIDES:
                found = self.stick(layout, modifier, name)
                self.assertEqual(sorted(kind for kind, _ in found), ['Full_Press', 'release'])
                by = dict(found)
                self.assertEqual(layout.layer_ops(by['Full_Press']), [('remove_layer', MARKER)])
                self.assertEqual(by['Full_Press']['settings'].get('interruptable'), '0')
                self.assertEqual(layout.layer_ops(by['release'])[-1], ('add_layer', window))

    def test_the_marker_and_the_cover_have_no_cleanup_on_up_or_down(self):
        for layout in self.each():
            for _, name, _, _, layer, wheel in SIDES:
                self.assertEqual([kind for kind, _ in self.stick(layout, MARKER, name)], ['release'])
                found = dict(self.stick(layout, COVER, name))
                self.assertEqual(sorted(found), ['Full_Press', 'release'])
                self.assertEqual(found['Full_Press']['bindings']['binding'], f'mouse_wheel {wheel}, , ')
                self.assertEqual(found['Full_Press']['settings'], {'hold_repeats': '1', 'repeat_rate': '50', 'interruptable': '0'})
                self.assertEqual(layout.layer_ops(found['release']), [('remove_layer', COVER), ('remove_layer', layer)])

    def test_the_ring_has_no_release_in_the_stick_family(self):
        for layout in self.each():
            for title in (MARKER, COVER, *(t for side in SIDES for t in (side[2], side[4]))):
                kinds = [kind for kind, _ in self.stick(layout, title, 'edge')]
                # the cleanup press and its guard chord (one inverted chord in 90.53, 90.55 and 90.61 to 90.64),
                # and since 90.55 the timer's Soft Press in the four timer layers
                timer = title in (side[i] for side in SIDES for i in (2, 4))
                self.assertEqual(kinds, ['Full_Press', 'chord', 'Soft_Press'] if timer else ['Full_Press', 'chord'], title)

    def test_a_window_scrolls_at_50_ms_and_closes_at_150_ms(self):
        for layout in self.each():
            for _, name, _, window, layer, wheel in SIDES:
                always = layout.active(window)['switch']['inputs']['always_on_action']['activators']['Full_Press']
                self.assertEqual([(e['settings']['delay_start'], e['bindings']['binding'].split(',')[0].split(' ')[:2]) for e in always],
                                 [('150', ['controller_action', 'remove_layer']), ('50', ['mouse_wheel', wheel])])
                self.assertEqual(layout.layer_ops(dict(self.stick(layout, window, name))['Full_Press']),
                                 [('remove_layer', window), ('add_layer', layer)])
                for source in ('joystick', 'right_joystick'):
                    lift = layout.active(window)[source]['inputs']['touch']['activators']['release']
                    self.assertFalse(any(a.startswith('mouse_wheel') for a in lift['bindings']['binding']))

    def test_a_scroll_layer_has_the_bumper_scroll_layers_shape(self):
        for layout in self.each():
            for _, name, _, window, layer, wheel in SIDES:
                found = self.stick(layout, layer, name)
                # since 90.53 the 150 ms chord sits on the drivers (A63); the press, the reset and the Release stay
                self.assertEqual([kind for kind, _ in found], ['release', 'Full_Press', 'Full_Press'])
                release, press, reset = (e for _, e in found)
                self.assertEqual(layout.layer_ops(release), [('remove_layer', layer), ('add_layer', window)])
                self.assertEqual(press['bindings']['binding'], f'mouse_wheel {wheel}, , ')
                self.assertEqual(layout.layer_ops(reset), [('remove_layer', COVER)])
                self.assertEqual(reset['settings'], {'hold_repeats': '1', 'repeat_rate': '200', 'interruptable': '0'})

    def test_the_two_scroll_layers_follow_the_steering_double_taps(self):
        # Appended as the last two layers in 90.52 (R103). Since the new order of 90.64 they sit in the Steering
        # group, after the two Double Tap layers that add them.
        for layout in self.each():
            listed = [layout.titles[key] for key in layout.order]
            at = listed.index(SIDES[0][4])
            self.assertEqual(listed[at - 2:at + 2], [side[3] for side in SIDES] + [side[4] for side in SIDES])


if __name__ == "__main__":
    unittest.main()
