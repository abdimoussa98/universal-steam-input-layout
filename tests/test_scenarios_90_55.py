"""90.55: the Steering stick's four timers are Soft Presses on the left stick's edge, the left edge cleans up with one inverted chord, and the unnecessary removes are gone."""

# Since 90.56 the edge cleanup scenarios (C1 to C4) and the edge's shape test run on the 90.55 candidate (`frozen`):
# the ten edges are back to the cleanup press and its guard chord (tests/test_scenarios_90_56.py). The rest of this
# file still describes the working layout.

import unittest

from steam_layout.model import Layout, actions, entries, map_title
from tests.scenario import RENAME, ScenarioCase, frozen_layout_data, layout_data, scenario

DEFLECT = 1 << 30                                         # the left stick's deflect, bit 30
THRESHOLD = '13276'                                       # the timers' Soft Press: the stick's D-pad deadzone
MARKER, COVER = 'Steering | LS: Tap Cover', 'Steering | LS: Double Tap Cover'
# driver, its layer, its key
DRIVERS = (('R1', 'Steering | R1: W Key', 'W'), ('L1', 'Steering | L1: S Key', 'S'))
# direction, input, modifier, window, scroll layer, wheel
SIDES = (('up', 'dpad_north', 'Steering | LS Up: Modifier 1', 'Steering | LS Up: Double Tap', 'Steering | LS Up: Scroll Up', 'SCROLL_UP'),
         ('down', 'dpad_south', 'Steering | LS Down: Modifier 0', 'Steering | LS Down: Double Tap', 'Steering | LS Down: Scroll Down', 'SCROLL_DOWN'))
STICK_MODIFIERS = tuple(side[2] for side in SIDES)
SCROLLS = tuple(side[4] for side in SIDES)
MODIFIER_2 = ('Steering | R1!L1: Modifier 2', 'Steering | L1!R1: Modifier 2')
FAMILY = tuple(t for side in SIDES for t in side[2:5]) + (MARKER, COVER)
EDGE_CHORDS = (*(d[1] for d in DRIVERS), *STICK_MODIFIERS, MARKER, COVER, *SCROLLS, *MODIFIER_2)
# layer, its direction, what its timer adds, the delay, the reset's repeat
TIMERS = tuple((side[2], side[1], MARKER, '200', '250') for side in SIDES) + tuple((side[4], side[1], COVER, '150', '200') for side in SIDES)
RIGHT_PAD = ('RTP: Entry Point', 'RTP: Tap Cover')


def wheels(pad):
    return [x for x in pad.typed() if x.startswith('mouse_wheel')]


class TimersOnTheEdge(ScenarioCase):
    """The timers moved off stick up and down because a start delay owned by a stick direction misfires
    (A63). On the edge it held on the Deck (A64, 90.54). Here each is a Soft Press there (A65). The simulator
    never showed the fault, and it presses the edge with the direction, so a shallow push is for the Deck."""

    def held(self):
        """Every driver, on a pad in Steering with the driver held and the thumb on the stick."""
        for driver, owner, key in DRIVERS:
            for pad in self.each(start=('Base', 'Steering')):
                pad.hold(driver).touch('LS').wait(300)
                yield pad, driver, owner, key
                pad.let_go(driver).lift('LS').wait(300)
                self.assertEqual(pad.down(), [])
                self.assertTrue(pad.lacks(owner, *FAMILY))

    @scenario('90.55 T1', rules=('R120',), rests=('A6', 'A16', 'A60', 'A64', 'A65'), either=('A9', 'A32'))
    def test_taps_and_holds_in_any_order_keep_their_meaning(self):
        # The modifier lands with the stick already past the threshold: the timer starts on a held edge.
        for pad, _, _, key in self.held():
            for direction, _, modifier, _, _, wheel in SIDES:
                for gesture in ('tap', 'tap', 'hold', 'tap', 'hold', 'hold', 'tap', 'tap'):
                    pad.mark().push('LS', direction).wait(60)
                    self.assertTrue(pad.has(modifier) and pad.lacks(MARKER))
                    if gesture == 'hold':
                        pad.wait(139)
                        self.assertTrue(pad.lacks(MARKER))                 # the full 200 ms, every time
                        pad.wait(1)
                        self.assertTrue(pad.has(MARKER))
                        pad.wait(200)
                    pad.recentre('LS').wait(400)
                    self.assertEqual(wheels(pad), [f'mouse_wheel {wheel}'] if gesture == 'tap' else [], gesture)
                    self.assertEqual(pad.down(), [key])                    # the key never lets go
                    self.assertTrue(pad.lacks(*FAMILY))

    @scenario('90.55 T2', rules=('R120',), rests=('A6', 'A16', 'A60', 'A64', 'A65'), either=('A9', 'A32'))
    def test_second_deflects_chain_and_the_cover_waits_its_150_ms_every_time(self):
        for pad, _, _, _ in self.held():
            for direction, _, _, window, layer, wheel in SIDES:
                pad.mark().flick('LS', direction).wait(30)
                for _ in range(3):                                         # three quick second deflects
                    pad.push('LS', direction).wait(60)
                    self.assertTrue(pad.has(layer) and pad.lacks(COVER))
                    pad.recentre('LS').wait(30)
                    self.assertTrue(pad.has(window))
                self.assertEqual(wheels(pad), [f'mouse_wheel {wheel}'] * 3)          # one on each press
                pad.push('LS', direction).wait(149)
                self.assertTrue(pad.lacks(COVER))
                pad.wait(251)
                self.assertTrue(pad.has(layer, COVER))
                self.assertGreater(len(wheels(pad)), 8)
                pad.recentre('LS').wait(400)
                self.assertTrue(pad.lacks(*FAMILY))

    @scenario('90.55 T3', rests=('A10', 'A65'), either=('A9', 'A32'))
    def test_a_press_during_the_deflect_makes_it_a_hold_at_once(self):
        for pad, _, _, key in self.held():
            for direction, _, modifier, _, _, _ in SIDES:
                for press in ('A', 'LS', 'RS'):
                    pad.mark().push('LS', direction).wait(60)
                    pad.click(press) if press in ('LS', 'RS') else pad.tap(press)
                    pad.wait(50)
                    self.assertTrue(pad.has(modifier, MARKER))
                    pad.recentre('LS').wait(400)
                    self.assertEqual(wheels(pad), [])
                    self.assertEqual(pad.down(), [key])
                    self.assertTrue(pad.lacks(*FAMILY))

    @scenario('90.55 T4', rests=('A10', 'A60'), either=('A9', 'A32'))
    def test_a_side_key_never_adds_the_hold_marker(self):
        # Left and right send A and D only (author, 2026-10-10). A roll inside 200 ms is a tap of up or
        # down: the window opens and scrolls once. Past 200 ms the marker is on and nothing scrolls.
        for pad, _, _, _ in self.held():
            for direction, _, _, window, _, wheel in SIDES:
                pad.mark().push('LS', direction).wait(60).roll('LS', 'left').wait(20)
                self.assertTrue(pad.has(window) and pad.lacks(MARKER))
                self.assertIn('A', pad.down())
                pad.wait(300)
                self.assertEqual(wheels(pad), [f'mouse_wheel {wheel}'])
                pad.recentre('LS').wait(300)
                pad.mark().push('LS', direction).wait(300).roll('LS', 'right').wait(100)
                self.assertIn('D', pad.down())
                pad.recentre('LS').wait(300)
                self.assertEqual(wheels(pad), [])
                self.assertTrue(pad.lacks(*FAMILY))

    @scenario('90.55 T5', rests=('A65',), either=('A9', 'A32'))
    def test_the_right_pad_layers_stay_when_the_hold_marker_lands(self):
        # No right pad removes in the Steering modifier layers (author, 2026-10-10 and 2026-10-11).
        for pad, _, _, _ in self.held():
            for direction, _, modifier, _, _, _ in SIDES:
                pad.hold('RP touch').wait(300)
                self.assertTrue(pad.has(*RIGHT_PAD))
                pad.push('LS', direction).wait(300)
                self.assertTrue(pad.has(modifier, MARKER, *RIGHT_PAD))
                pad.recentre('LS').wait(300)
                self.assertTrue(pad.has(*RIGHT_PAD) and pad.lacks(*FAMILY))
                pad.let_go('RP touch').wait(300)
                self.assertTrue(pad.lacks(*RIGHT_PAD))

    @scenario('90.55 T6', rules=('R113',), rests=('A6', 'A10', 'A37'), either=('A9', 'A32'))
    def test_the_other_driver_enters_modifier_2_at_once_from_any_stick_layer(self):
        # The stick layers bind no driver, so the driver layer underneath answers the other one: its
        # Modifier 2 entry, now nine removes and the add.
        for driver, owner, key in DRIVERS:
            other = 'L1' if driver == 'R1' else 'R1'
            second = f'Steering | {driver}!{other}: Modifier 2'
            for direction, _, modifier, _, layer, _ in SIDES:
                for stage in ('modifier', 'marker', 'scroll'):
                    for pad in self.each(start=('Base', 'Steering')):
                        pad.hold(driver).touch('LS').wait(300)
                        if stage == 'scroll':
                            pad.flick('LS', direction).wait(20).push('LS', direction).wait(40)
                        else:
                            pad.push('LS', direction).wait(100 if stage == 'modifier' else 300)
                        self.assertTrue(pad.has(owner, layer if stage == 'scroll' else modifier) and pad.lacks(second))
                        pad.mark().hold(other).wait(20)
                        self.assertTrue(pad.has(owner, second) and pad.lacks(*FAMILY), stage)
                        self.assertEqual(pad.down(), [key])
                        self.assertEqual([x for x in pad.typed() if not x.startswith('mouse_wheel')], [])
                        pad.recentre('LS').let_go(other).wait(100).let_go(driver).lift('LS').wait(300)
                        self.assertEqual(pad.stack, pad.layers('Base', 'Steering'))
                        self.assertEqual(pad.down(), [])

    @scenario('90.55 T7', rests=('A7', 'A10'), either=('A9', 'A32'))
    def test_the_driver_let_go_ends_the_stick_layers_wherever_the_sequence_is(self):
        for driver, owner, _ in DRIVERS:
            for direction, _, modifier, window, layer, _ in SIDES:
                for stage, on in (('modifier', modifier), ('marker', MARKER), ('window', window), ('scroll', layer), ('cover', COVER)):
                    for pad in self.each(start=('Base', 'Steering')):
                        pad.hold(driver).touch('LS').wait(300)
                        if stage == 'modifier':
                            pad.push('LS', direction).wait(60)
                        elif stage == 'marker':
                            pad.push('LS', direction).wait(300)
                        else:
                            pad.flick('LS', direction).wait(20)
                            if stage != 'window':
                                pad.push('LS', direction).wait(60 if stage == 'scroll' else 300)
                        self.assertTrue(pad.has(on), stage)
                        pad.let_go(driver).wait(50)
                        self.assertTrue(pad.lacks(owner, *FAMILY), stage)
                        pad.recentre('LS').lift('LS').wait(300)
                        self.assertEqual(pad.down(), [], stage)


class EdgeCleanup(ScenarioCase):
    """The left stick's edge of ten Steering layers: one chord with Invert Activation on the drivers, the Entry
    Guard's pattern. It runs while the stick is inside the ring and no driver is held (A61)."""

    def held(self):
        for driver, owner, key in DRIVERS:
            for pad in self.each(start=('Base', 'Steering')):
                pad.hold(driver).touch('LS').wait(300)
                yield pad, driver, owner, key

    @scenario('90.55 C1', rules=('R133', 'R170'), rests=('A61',), either=('A9', 'A32'), frozen='90.55')
    def test_no_stick_movement_removes_the_driver_layer_while_the_driver_is_held(self):
        # The fault of 2026-10-10: a flick could drop the W layer under a held driver and leave Steering.
        # Up and down in the W and S layers carry no cleanup any more, and the edge's is off with a driver held.
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

    @scenario('90.55 C2', rules=('R133',), rests=('A25', 'A61'), either=('A9', 'A32'), frozen='90.55')
    def test_a_missed_driver_release_clears_when_the_edge_comes_back(self):
        for pad, driver, owner, _ in self.held():
            pad.miss(driver).wait(300)
            self.assertTrue(pad.has(owner))                  # nothing has told the layout yet
            pad.hold('LS edge').wait(100)
            self.assertTrue(pad.has(owner))                  # the chord's own input is pressed: off
            pad.let_go('LS edge').wait(100)
            self.assertTrue(pad.has('Steering') and pad.lacks(owner, *FAMILY))
            self.assertEqual(pad.down(), [])

    @scenario('90.55 C3', rules=('R133',), rests=('A6', 'A25', 'A61'), either=('A9', 'A32'), frozen='90.55')
    def test_a_missed_driver_release_during_a_deflect_leaves_no_stick_layer(self):
        for driver, owner, _ in DRIVERS:
            for direction, _, _, _, _, _ in SIDES:
                for pad in self.each(start=('Base', 'Steering')):
                    pad.hold(driver).touch('LS').wait(300).push('LS', direction).wait(100).miss(driver).wait(600)
                    pad.recentre('LS').wait(400)
                    self.assertTrue(pad.lacks(owner, *FAMILY))
                    pad.lift('LS').wait(300)
                    self.assertEqual(pad.down(), [])

    @scenario('90.55 C4', rules=('R133',), rests=('A61',), either=('A9', 'A32'), frozen='90.55')
    def test_pressing_the_driver_again_shuts_the_edge_chord_off(self):
        for pad, driver, owner, key in self.held():
            pad.miss(driver).wait(100).hold(driver).wait(100)
            pad.hold('LS edge').wait(60).let_go('LS edge').wait(200)
            self.assertTrue(pad.has('Steering', owner))
            self.assertIn(key, pad.down())


class EdgeTimersShape(unittest.TestCase):
    def each(self, frozen=None):
        for variant in ('default', 'alternative'):
            layout = Layout(frozen_layout_data(variant, frozen) if frozen else layout_data(variant))
            yield layout, (lambda title, v=variant: map_title(title, RENAME) if v == 'alternative' else title)

    def test_no_steering_layer_states_an_outer_ring_radius_on_the_left_stick(self):
        # The default, as in the Temp Cursor Gyro layers (author, 2026-10-10).
        for layout, _ in self.each():
            steering = [t for t in layout.presets if t.startswith('Steering')]
            self.assertEqual(len(steering), 14)
            for title in steering + [t for t in layout.presets if t.endswith('Temp Cursor Gyro')]:
                self.assertNotIn('edge_binding_radius', layout.active(title)['joystick'].get('settings', {}), title)

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

    def test_no_start_delay_is_owned_by_a_stick_direction_in_the_steering_layers(self):
        for layout, _ in self.each():
            for title in (t for t in layout.presets if t.startswith('Steering')):
                for name, value in layout.active(title)['joystick']['inputs'].items():
                    for kind, entry in entries(value.get('activators', {})):
                        if entry.get('settings', {}).get('delay_start'):
                            # since 90.65 the edge's cleanup press starts 5 ms late; the edge owns that one too
                            late = kind == 'Full_Press' and entry['settings']['delay_start'] == '5'
                            self.assertEqual((name, kind), ('edge', 'Full_Press' if late else 'Soft_Press'), title)

    def test_the_direction_keeps_the_reset_and_the_release(self):
        for layout, _ in self.each():
            for layer, direction, target, _, rate in TIMERS:
                found = list(entries(layout.active(layer)['joystick']['inputs'][direction]['activators']))
                kinds = [kind for kind, _ in found]
                self.assertEqual(kinds, ['Full_Press', 'release'] if layer in STICK_MODIFIERS else ['release', 'Full_Press', 'Full_Press'], layer)
                resets = [e for kind, e in found if kind == 'Full_Press' and layout.layer_ops(e) == [('remove_layer', target)]]
                self.assertEqual([e['settings'] for e in resets], [{'hold_repeats': '1', 'repeat_rate': rate, 'interruptable': '0'}], layer)

    def test_up_and_down_in_the_driver_layers_hold_one_chord_on_the_driver_and_no_cleanup(self):
        for layout, name in self.each():
            for _, owner, _ in DRIVERS:
                stick = layout.active(name(owner))['joystick']['inputs']
                guard = int(stick['edge']['activators']['chord']['settings']['gyro_ratchet_button_mask'])
                for _, direction, modifier, _, _, _ in SIDES:
                    found = list(entries(stick[direction]['activators']))
                    self.assertEqual([kind for kind, _ in found], ['chord'], (owner, direction))
                    chord = found[0][1]
                    self.assertEqual(layout.layer_ops(chord), [('add_layer', modifier)])
                    settings = chord['settings']
                    mask = int(settings['gyro_ratchet_button_mask'])
                    self.assertEqual(bin(mask).count('1'), 1)                                   # the driver alone:
                    self.assertTrue(mask & guard and not mask & DEFLECT, (owner, direction))    # no deflect, as 90.53 had
                    self.assertEqual((settings['hold_repeats'], settings['repeat_rate'], settings['interruptable']),
                                     ('1', '50', '0'))

    def test_left_and_right_in_the_stick_modifiers_send_only_their_key(self):
        for layout, _ in self.each():
            for modifier in STICK_MODIFIERS:
                stick = layout.active(modifier)['joystick']['inputs']
                for direction, key in (('dpad_east', 'D'), ('dpad_west', 'A')):
                    self.assertEqual([actions(e) for _, e in entries(stick[direction]['activators'])],
                                     [[f'key_press {key}, , ']])
                clicks = [e for kind, e in entries(stick['click']['activators']) if kind == 'chord']
                self.assertEqual(len(clicks), 2)                 # a stick can be clicked while W is held: these stay
                for chord in clicks:
                    self.assertIn(('add_layer', MARKER), layout.layer_ops(chord))

    def test_only_the_clear_to_base_removes_right_pad_layers_in_the_steering_modifier_layers(self):
        for layout, name in self.each():
            for title in map(name, STICK_MODIFIERS + MODIFIER_2):
                for source, group in layout.active(title).items():
                    for control, value in group.get('inputs', {}).items():
                        for kind, entry in entries(value.get('activators', {})):
                            pads = [t for op, t in layout.layer_ops(entry) if op == 'remove_layer' and t.startswith('RTP:')]
                            if pads:
                                self.assertEqual(kind, 'release', (title, source, control))
                                self.assertGreater(len(actions(entry)), 50, (title, source, control))

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


if __name__ == '__main__':
    unittest.main()
