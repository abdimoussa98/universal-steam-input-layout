"""90.52: the Steering stick deflect follows the bumper modifier lifecycle, with a scroll layer for the second deflect."""

import unittest

from steam_layout.model import Layout, entries
from tests.scenario import ScenarioCase, layout_data, scenario

DEFLECT = '1073741824'                                    # the left stick's deflect, bit 30
MARKER, COVER = 'Steering | LS: Tap Cover', 'Steering | LS: Double Tap Cover'
# direction, input, modifier, window, scroll layer, wheel
SIDES = (('up', 'dpad_north', 'Steering | LS Up: Modifier 1', 'Steering | LS Up: Double Tap', 'Steering | LS Up: Scroll Up', 'SCROLL_UP'),
         ('down', 'dpad_south', 'Steering | LS Down: Modifier 0', 'Steering | LS Down: Double Tap', 'Steering | LS Down: Scroll Down', 'SCROLL_DOWN'))
FAMILY = tuple(t for side in SIDES for t in side[2:5]) + (MARKER, COVER)


def wheels(pad):
    return [x for x in pad.typed() if x.startswith('mouse_wheel')]


class StickDeflect(ScenarioCase):
    def held(self):
        """Every driver and direction, on a pad in Steering with the driver held and the thumb on the stick."""
        for driver in ('R1', 'L1'):
            for side in SIDES:
                for pad in self.each(start=('Base', 'Steering')):
                    pad.hold(driver).touch('LS').wait(300)
                    yield pad, driver, side
                    pad.let_go(driver).lift('LS').wait(300)
                    self.assertEqual(pad.down(), [])
                    self.assertTrue(pad.lacks(*FAMILY))

    @scenario('90.52 S1', rules=('R130',), rests=('A6', 'A60'), either=('A9', 'A32'))
    def test_four_quick_deflects_scroll_once_each_at_50_ms(self):
        for pad, _, (direction, _, modifier, window, _, wheel) in self.held():
            for _ in range(4):
                pad.mark().push('LS', direction).wait(60)
                self.assertTrue(pad.has(modifier))
                pad.recentre('LS').wait(40)
                self.assertTrue(pad.has(window))
                self.assertEqual(wheels(pad), [])
                pad.wait(20)
                self.assertEqual(wheels(pad), [f'mouse_wheel {wheel}'])
                pad.wait(540)
                self.assertEqual(wheels(pad), [f'mouse_wheel {wheel}'])
                self.assertTrue(pad.has('Steering') and pad.lacks(*FAMILY))

    @scenario('90.52 S2', rules=('R120',), rests=('A6', 'A60'), either=('A9', 'A32'))
    def test_a_second_deflect_scrolls_on_the_press_and_reopens_the_window(self):
        for pad, _, (direction, _, _, window, layer, wheel) in self.held():
            for _ in range(2):
                pad.mark().flick('LS', direction).wait(30).push('LS', direction).wait(20)
                self.assertTrue(pad.has(layer) and pad.lacks(window, COVER))
                self.assertEqual(wheels(pad), [f'mouse_wheel {wheel}'])
                pad.recentre('LS').wait(20)
                self.assertTrue(pad.has(window) and pad.lacks(layer))
                pad.wait(500)
                self.assertEqual(wheels(pad), [f'mouse_wheel {wheel}'] * 2)
                self.assertTrue(pad.lacks(*FAMILY))

    @scenario('90.52 S3', rules=('R120',), rests=('A6', 'A59', 'A60'), either=('A9', 'A32'))
    def test_a_second_deflect_held_past_150_ms_repeats_and_ends_on_its_release(self):
        for pad, _, (direction, _, _, _, layer, wheel) in self.held():
            for _ in range(2):
                pad.mark().flick('LS', direction).wait(30).push('LS', direction).wait(400)
                self.assertTrue(pad.has(layer, COVER))
                self.assertGreater(len(wheels(pad)), 4)
                self.assertEqual(set(wheels(pad)), {f'mouse_wheel {wheel}'})
                pad.recentre('LS').wait(20)
                count = len(wheels(pad))
                pad.wait(400)
                self.assertEqual(len(wheels(pad)), count)
                self.assertTrue(pad.lacks(*FAMILY))

    @scenario('90.52 S4', rules=('R120',), rests=('A59', 'A60'), either=('A9', 'A32'))
    def test_a_hold_past_200_ms_adds_the_marker_and_does_not_scroll(self):
        for pad, _, (direction, _, modifier, _, _, _) in self.held():
            for _ in range(2):
                pad.mark().push('LS', direction).wait(300)
                self.assertTrue(pad.has(modifier, MARKER))
                pad.recentre('LS').wait(400)
                self.assertEqual(wheels(pad), [])
                self.assertTrue(pad.lacks(*FAMILY))

    @scenario('90.52 S5', rests=('A10', 'A60'), either=('A9', 'A32'))
    def test_a_roll_into_a_side_ends_the_modifier_without_a_scroll(self):
        # Past 200 ms the marker is on, and the roll ends a hold. Until 90.52 a side also added the marker, so
        # a roll inside 200 ms was a hold too; since 90.53 a side sends only its key and that roll is a tap,
        # which scrolls once (author, 2026-10-10; 90.53 S5).
        for pad, _, (direction, _, _, _, _, _) in self.held():
            for before in (300,):
                pad.mark().push('LS', direction).wait(before).roll('LS', 'left').wait(100)
                self.assertTrue(pad.lacks(*FAMILY))
                self.assertIn('A', pad.down())
                pad.recentre('LS').wait(300)
                self.assertEqual(wheels(pad), [])

    @scenario('90.52 S6', rules=('R125',), rests=('A60',), either=('A9', 'A32'))
    def test_a_thumb_lifted_in_the_window_only_closes_it(self):
        for pad, _, (direction, _, _, _, _, wheel) in self.held():
            pad.mark().flick('LS', direction).wait(20).lift('LS').wait(300)
            self.assertEqual(wheels(pad), [])
            pad.touch('LS').wait(300)
            pad.mark().flick('LS', direction).wait(80).lift('LS').wait(300)
            self.assertEqual(wheels(pad), [f'mouse_wheel {wheel}'])
            self.assertTrue(pad.lacks(*FAMILY))
            pad.touch('LS').wait(300)

    @scenario('90.52 S7', rules=('R123',), rests=('A60',), either=('A9', 'A32'))
    def test_a_thumb_that_leaves_the_stick_in_a_second_deflect_ends_it_clean(self):
        for pad, _, (direction, _, _, _, _, wheel) in self.held():
            pad.mark().flick('LS', direction).wait(30).push('LS', direction).wait(40).lift('LS').wait(400)
            self.assertEqual(wheels(pad), [f'mouse_wheel {wheel}'])
            self.assertTrue(pad.lacks(*FAMILY))
            pad.touch('LS').wait(300)

    @scenario('90.52 S8', rules=('R130', 'R133'), rests=('A25', 'A36', 'A59', 'A60'), either=('A9',))
    def test_a_missed_driver_release_with_the_stick_held_clears_as_the_marker_lands(self):
        for direction, _, _, _, _, _ in SIDES:
            for pad in self.each(start=('Base', 'Steering')):
                pad.hold('R1').touch('LS').wait(300).push('LS', direction).wait(60).miss('R1').wait(300)
                # The marker lands at 200 ms, with no driver held, and its cleanup clears the family; the stick
                # is then on Steering's own binds. So until 90.52 and again since 90.55, where the timer is on
                # the stick's edge. In 90.53 it was on the driver and went with it (tests/test_scenarios_90_53.py).
                self.assertTrue(pad.lacks('Steering | R1: W Key', *FAMILY))
                pad.recentre('LS').wait(300)
                self.assertTrue(pad.lacks('Steering | R1: W Key', *FAMILY))
                pad.lift('LS').wait(300)
                self.assertEqual(pad.down(), [])


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
                # the cleanup press and its guard chord (one inverted chord in 90.53 and 90.55), and since 90.55 the
                # timer's Soft Press in the four timer layers
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

    def test_the_two_scroll_layers_are_the_last_layers(self):
        for layout in self.each():
            self.assertEqual([layout.titles[key] for key in layout.order[-2:]], [side[4] for side in SIDES])


class HeldPadClick(ScenarioCase):
    # Guards the shape only: on the Deck with 90.51 a held click dropped when a thumb lifted from a stick,
    # and the simulator held it (plans/2026-10-10-stick-lifecycle-and-pad-click-after-stick-tap.md, part 2).
    @scenario('90.52 P1', rests=('A10', 'A18'), either=('A42',))
    def test_a_held_pad_click_stays_when_a_thumb_lifts_from_a_stick(self):
        for stick in ('LS', 'RS'):
            for click in (('LP', 'left', 'LEFT_ARROW'), ('RP', 'left', 'mouse_button BACK'),
                                  ('LP', 'centre', 'CAPSLOCK'), ('RP', 'centre', 'mouse_button MIDDLE')):
                for order in ('thumb first', 'short touch', 'click first'):
                    for pad in self.each():
                        if order == 'click first':
                            pad.press_pad(*click[:2]).wait(200).touch(stick).wait(60)
                        else:
                            pad.touch(stick).wait(400 if order == 'thumb first' else 40).press_pad(*click[:2]).wait(40)
                        pad.lift(stick).wait(310)
                        self.assertIn(click[2], pad.down(), (stick, click, order))
                        pad.let_go_pad(click[0]).wait(300)
                        self.assertEqual(pad.down(), [])


if __name__ == '__main__':
    unittest.main()
