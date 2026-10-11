"""90.53: the Steering stick's timers sit on the drivers, its entry carries no cleanup, and the left edge cleans up with one inverted chord."""

# Since 90.55 the stick scenarios and the shape tests here run on the 90.53 candidate (`frozen`): the working
# layout continued from 90.52 through 90.54, with the timers on the stick's edge (tests/test_scenarios_90_55.py).
# The Entry Guard scenarios stay on the working layout; that layer has not changed since 90.44.

import unittest

from steam_layout.model import Layout, actions, entries, map_title
from tests.scenario import RENAME, ScenarioCase, frozen_layout_data, scenario

DEFLECT = 1 << 30                                         # the left stick's deflect, bit 30
MARKER, COVER = 'Steering | LS: Tap Cover', 'Steering | LS: Double Tap Cover'
GUARD = 'Steering | LS: Entry Guard'
# driver, its layer, its key
DRIVERS = (('R1', 'Steering | R1: W Key', 'W'), ('L1', 'Steering | L1: S Key', 'S'))
# direction, input, modifier, window, scroll layer, wheel
SIDES = (('up', 'dpad_north', 'Steering | LS Up: Modifier 1', 'Steering | LS Up: Double Tap', 'Steering | LS Up: Scroll Up', 'SCROLL_UP'),
         ('down', 'dpad_south', 'Steering | LS Down: Modifier 0', 'Steering | LS Down: Double Tap', 'Steering | LS Down: Scroll Down', 'SCROLL_DOWN'))
STICK_MODIFIERS = tuple(side[2] for side in SIDES)
MODIFIER_2 = ('Steering | R1!L1: Modifier 2', 'Steering | L1!R1: Modifier 2')
FAMILY = tuple(t for side in SIDES for t in side[2:5]) + (MARKER, COVER)
EDGE_CHORDS = (*(d[1] for d in DRIVERS), *STICK_MODIFIERS, MARKER, COVER, *(side[4] for side in SIDES), *MODIFIER_2)
RIGHT_PAD = ('RTP: Entry Point', 'RTP: Tap Cover')


def wheels(pad):
    return [x for x in pad.typed() if x.startswith('mouse_wheel')]


class EntryAndEdge(ScenarioCase):
    def held(self):
        """Every driver, on a pad in Steering with the driver held and the thumb on the stick."""
        for driver, owner, key in DRIVERS:
            for pad in self.each(start=('Base', 'Steering')):
                pad.hold(driver).touch('LS').wait(300)
                yield pad, driver, owner, key

    @scenario('90.53 S1', rules=('R133', 'R170'), rests=('A61', 'A62'), either=('A9', 'A32'), frozen='90.53')
    def test_no_stick_movement_removes_the_driver_layer_while_the_driver_is_held(self):
        # The fault of 2026-10-10: a flick could drop the W layer under a held driver and leave Steering.
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

    @scenario('90.53 S2', rules=('R130',), rests=('A60', 'A62'), either=('A9', 'A32'), frozen='90.53')
    def test_every_deflect_in_one_driver_hold_adds_its_modifier_and_scrolls_once(self):
        for pad, _, owner, _ in self.held():
            for direction, _, modifier, _, _, wheel in SIDES * 3:
                pad.mark().push('LS', direction).wait(60)
                self.assertTrue(pad.has(owner, modifier))
                pad.recentre('LS').wait(400)
                self.assertEqual(wheels(pad), [f'mouse_wheel {wheel}'])
                self.assertTrue(pad.has(owner) and pad.lacks(*FAMILY))

    @scenario('90.53 S3', rules=('R133',), rests=('A25', 'A61'), either=('A9', 'A32'), frozen='90.53')
    def test_a_missed_driver_release_clears_when_the_edge_comes_back(self):
        # With no driver held the edge's inverted chord runs as the stick comes back from the rim.
        for pad, driver, owner, _ in self.held():
            pad.miss(driver).wait(300)
            self.assertTrue(pad.has(owner))                  # nothing has told the layout yet
            pad.hold('LS edge').wait(100)
            self.assertTrue(pad.has(owner))                  # the chord's own input is pressed: off
            pad.let_go('LS edge').wait(100)
            self.assertTrue(pad.has('Steering') and pad.lacks(owner, *FAMILY))
            self.assertEqual(pad.down(), [])

    @scenario('90.53 S4', rules=('R133',), rests=('A61',), either=('A9', 'A32'), frozen='90.53')
    def test_pressing_the_driver_again_shuts_the_edge_chord_off(self):
        for pad, driver, owner, key in self.held():
            pad.miss(driver).wait(100).hold(driver).wait(100)
            pad.hold('LS edge').wait(60).let_go('LS edge').wait(200)
            self.assertTrue(pad.has('Steering', owner))
            self.assertIn(key, pad.down())

    @scenario('90.53 S5', rests=('A10', 'A60'), either=('A9', 'A32'), frozen='90.53')
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

    @scenario('90.53 S6', rests=('A59',), either=('A9', 'A32'), frozen='90.53')
    def test_the_right_pad_layers_stay_when_the_hold_marker_lands(self):
        # No right pad removes in the Steering modifier layers (author, 2026-10-10).
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


class TimersOnTheDrivers(ScenarioCase):
    """The fault of 90.50 to 90.52 (author, on the Deck): the 200 ms hold timer was owned by the stick's
    direction, and after one tap it landed at once on every later deflect. The simulator never showed it."""

    def held(self):
        for driver, owner, key in DRIVERS:
            for pad in self.each(start=('Base', 'Steering')):
                pad.hold(driver).touch('LS').wait(300)
                yield pad, driver, owner, key
                pad.let_go(driver).lift('LS').wait(300)
                self.assertEqual(pad.down(), [])
                self.assertTrue(pad.lacks(owner, *FAMILY))

    @scenario('90.53 T1', rules=('R120',), rests=('A6', 'A16', 'A36', 'A59', 'A60', 'A63'), either=('A9', 'A32'), frozen='90.53')
    def test_taps_and_holds_in_any_order_keep_their_meaning(self):
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

    @scenario('90.53 T2', rules=('R120',), rests=('A6', 'A16', 'A36', 'A59', 'A60', 'A63'), either=('A9', 'A32'), frozen='90.53')
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

    @scenario('90.53 T3', rules=('R113',), rests=('A5', 'A10', 'A37', 'A59'), either=('A9', 'A32'), frozen='90.53')
    def test_the_other_driver_enters_modifier_2_at_once_from_any_stick_layer(self):
        # One shared stick modifier binds both drivers (author, 2026-10-10), and Modifier 2 has to stay in
        # reach while the stick is out (author, 2026-10-11). The held driver's key press never runs its layer
        # commands (A5); the other driver's fresh press does. Its key shows for that moment only.
        for driver, owner, key in DRIVERS:
            other, other_key = ('L1', 'S') if driver == 'R1' else ('R1', 'W')
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
                        self.assertEqual(pad.down(), [key])                # landing ran no layer command
                        pad.mark().hold(other).wait(20)
                        self.assertTrue(pad.has(owner, second) and pad.lacks(*FAMILY), stage)
                        self.assertEqual(pad.down(), [key])
                        self.assertEqual([x for x in pad.typed() if not x.startswith('mouse_wheel')], [other_key])
                        pad.recentre('LS').let_go(other).wait(100).let_go(driver).lift('LS').wait(300)
                        self.assertEqual(pad.stack, pad.layers('Base', 'Steering'))
                        self.assertEqual(pad.down(), [])

    @scenario('90.53 T4', rests=('A7', 'A10'), either=('A9', 'A32'), frozen='90.53')
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
                        pad.lift('LS').wait(300)
                        self.assertEqual(pad.down(), [], stage)


class EntryGuard(ScenarioCase):
    """What `Steering | LS: Entry Guard` does on the corrected simulator, and is meant to do (author,
    2026-10-11): protect a stick that is held at the rim through the entry, and nothing else."""

    def enter(self, pad):
        pad.hold('Start').click('LS').let_go('Start').wait(300)

    @scenario('90.53 G1', rules=('R111',), rests=('A54', 'A61'))
    def test_a_centred_entry_keeps_no_guard_and_the_first_full_push_is_steerings_exit(self):
        for pad in self.each():
            self.enter(pad)
            self.assertTrue(pad.has('Steering') and pad.lacks(GUARD))
            pad.mark().push('LS', 'up').wait(100)
            self.assertTrue(pad.lacks('Steering', GUARD))
            self.assertIn(('beep', 'Steering'), pad.seen('beep'))
            pad.lift('LS').wait(300)
            self.assertEqual(pad.down(), [])

    @scenario('90.53 G2', rules=('R111',), rests=('A8', 'A10', 'A54', 'A61'))
    def test_a_stick_held_at_the_rim_through_the_entry_is_guarded_until_it_comes_back(self):
        for direction, key in (('up', 'W'), ('down', 'S')):
            for pad in self.each():
                pad.push('LS', direction).wait(200)
                self.enter(pad)
                self.assertTrue(pad.has('Steering', GUARD))
                self.assertEqual(pad.down(), [key])                       # the stick still walks, and Steering stays
                pad.wait(1000)
                self.assertTrue(pad.has('Steering', GUARD))
                pad.recentre('LS').wait(100)
                self.assertTrue(pad.has('Steering') and pad.lacks(GUARD))
                self.assertEqual(pad.down(), [])
                pad.lift('LS').wait(300)

    @scenario('90.53 G3', rules=('R111',), rests=('A6', 'A54', 'A61'), either=('A9',))
    def test_a_driver_takes_over_from_the_guard(self):
        for driver, owner, key in DRIVERS:
            for pad in self.each():
                pad.push('LS', 'left').wait(200)
                self.enter(pad)
                self.assertTrue(pad.has('Steering', GUARD))
                pad.hold(driver).wait(100)
                self.assertTrue(pad.has('Steering', owner) and pad.lacks(GUARD))
                self.assertIn(key, pad.down())
                pad.let_go(driver).lift('LS').wait(300)
                self.assertEqual(pad.down(), [])


class EntryAndEdgeShape(unittest.TestCase):
    def each(self):
        for variant in ('default', 'alternative'):
            layout = Layout(frozen_layout_data(variant, '90.53'))
            yield layout, (lambda title, v=variant: map_title(title, RENAME) if v == 'alternative' else title)

    def test_no_steering_layer_states_an_outer_ring_radius_on_the_left_stick(self):
        # The default, as in the Temp Cursor Gyro layers (author, 2026-10-10).
        for layout, _ in self.each():
            steering = [t for t in layout.presets if t.startswith('Steering')]
            self.assertEqual(len(steering), 14)
            for title in steering + [t for t in layout.presets if t.endswith('Temp Cursor Gyro')]:
                self.assertNotIn('edge_binding_radius', layout.active(title)['joystick'].get('settings', {}), title)

    def test_the_left_edge_cleans_up_with_one_inverted_chord_on_the_layers_drivers(self):
        for layout, name in self.each():
            for title in map(name, EDGE_CHORDS):
                edge = layout.active(title)['joystick']['inputs']['edge']['activators']
                self.assertEqual(list(edge), ['chord'], title)
                chord = edge['chord']
                settings = dict(chord['settings'])
                mask = int(settings.pop('gyro_ratchet_button_mask'))
                self.assertEqual(settings, {'gyro_ratchet_button_requireany_or_all': '0', 'edge_binding_invert': '1',
                                            'hold_repeats': '1', 'interruptable': '0', 'haptic_intensity': '0'}, title)
                self.assertFalse(mask & DEFLECT)
                ops = layout.layer_ops(chord)
                self.assertIn(('remove_layer', title), ops)
                self.assertTrue(all(op == 'remove_layer' for op, _ in ops), title)

    def test_the_entry_guard_keeps_its_chord_and_its_release(self):
        for layout, _ in self.each():
            edge = layout.active(GUARD)['joystick']['inputs']['edge']['activators']
            self.assertEqual(sorted(edge), ['chord', 'release'])
            self.assertEqual(edge['chord']['settings']['edge_binding_invert'], '1')
            for kind in edge:
                self.assertEqual(layout.layer_ops(edge[kind]), [('remove_layer', GUARD)])

    def test_up_and_down_in_the_driver_layers_hold_one_chord_and_no_cleanup(self):
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
                    self.assertEqual(settings['gyro_ratchet_button_requireany_or_all'], '1')        # both, not either
                    mask = int(settings['gyro_ratchet_button_mask'])
                    self.assertEqual(bin(mask).count('1'), 2)
                    self.assertTrue(mask & DEFLECT and mask & guard, (owner, direction))
                    self.assertEqual((settings['hold_repeats'], settings['repeat_rate'], settings['interruptable']),
                                     ('1', '50', '0'))

    def test_no_start_delay_is_owned_by_a_stick_direction_in_the_steering_layers(self):
        for layout, _ in self.each():
            for title in (t for t in layout.presets if t.startswith('Steering')):
                for source in ('joystick', 'right_joystick'):
                    for name, value in layout.active(title)[source]['inputs'].items():
                        for kind, entry in entries(value.get('activators', {})):
                            self.assertFalse(entry.get('settings', {}).get('delay_start'), (title, source, name, kind))

    def test_each_driver_carries_its_key_the_timer_and_its_release_in_the_four_timer_layers(self):
        timers = [(side[2], side[1], MARKER, '200', '250') for side in SIDES] + [(side[4], side[1], COVER, '150', '200') for side in SIDES]
        for layout, name in self.each():
            for layer, direction, target, delay, rate in timers:
                on_stick = dict(entries(layout.active(layer)['joystick']['inputs'][direction]['activators']))
                self.assertNotIn('chord', on_stick, layer)
                resets = [e for kind, e in entries(layout.active(layer)['joystick']['inputs'][direction]['activators'])
                          if kind == 'Full_Press' and layout.layer_ops(e) == [('remove_layer', target)]]
                self.assertEqual([e['settings'] for e in resets], [{'hold_repeats': '1', 'repeat_rate': rate, 'interruptable': '0'}], layer)
                for _, owner, key in DRIVERS:
                    home = [(source, control, value['activators']) for source, group in layout.active(name(owner)).items()
                            for control, value in group.get('inputs', {}).items()
                            if any(a == f'key_press {key}, , ' for _, e in entries(value.get('activators', {})) for a in actions(e))]
                    self.assertEqual(len(home), 1)
                    source, control, there = home[0]
                    here = layout.active(layer)[source]['inputs'][control]['activators']
                    self.assertEqual(list(here), ['release', 'chord', 'Full_Press'], (layer, owner))
                    self.assertEqual(here['Full_Press']['settings'], there['Full_Press']['settings'])
                    # the key, then the other driver's way into Modifier 2: the add its own layer has on this
                    # input, and only the two removes that can matter here (R132)
                    other = name(next(o for _, o, _ in DRIVERS if o != owner))
                    entry = layout.active(other)[source]['inputs'][control]['activators']['chord']
                    second = layout.layer_ops(entry)[-1]
                    self.assertEqual(second[0], 'add_layer')
                    self.assertIn('Modifier 2', second[1])
                    self.assertEqual(actions(here['Full_Press'])[0], f'key_press {key}, , ')
                    ops = layout.layer_ops(here['Full_Press'])
                    self.assertEqual(ops[-1], second)
                    self.assertEqual(sorted(ops[:-1]), sorted([('remove_layer', target), ('remove_layer', layer)]))
                    self.assertIn(('remove_layer', name(owner)), layout.layer_ops(here['release']))
                    self.assertIn(('remove_layer', layer), layout.layer_ops(here['release']))
                    self.assertEqual(layout.layer_ops(here['chord']), [('add_layer', target)])
                    self.assertEqual(here['chord']['settings'], {
                        'gyro_ratchet_button_mask': str(DEFLECT), 'gyro_ratchet_button_requireany_or_all': '0',
                        'delay_start': delay, 'interruptable': '0', 'haptic_intensity': '0'}, (layer, owner))

    def test_the_drivers_key_press_in_a_timer_layer_is_a_relay_the_chains_do_not_follow(self):
        from steam_layout.flow_model import layer_transitions
        for layout, _ in self.each():
            for layer in (*STICK_MODIFIERS, *(side[4] for side in SIDES)):
                relays = [t for t in layer_transitions(layout, layer) if t.role == 'relay']
                self.assertEqual(len(relays), 2, layer)
                self.assertEqual({t.activator for t in relays}, {'Full_Press'})

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


if __name__ == '__main__':
    unittest.main()
