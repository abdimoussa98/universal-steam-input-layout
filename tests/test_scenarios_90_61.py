"""90.61: on the left stick's edge of ten Steering layers the cleanup is one chord with Invert Activation again.

From 90.58, one change: the repeating Regular Press and its guard chord become one repeating chord on the same
drivers with Invert Activation, carrying the press's list. For an open Deck fault
(findings/2026-10-12-steering-ends-on-a-stick-touch): the driver layer's press ran although its bumper was held.
The simulator does not reproduce the fault, so nothing here shows it fixed.
"""

import json
import unittest

from steam_layout.model import Layout, actions, entries, map_title
from tests.scenario import RENAME, ROOT, VARIANTS, ScenarioCase, frozen_layout_data, scenario
from tests.test_scenarios_90_55 import DRIVERS, EDGE_CHORDS, FAMILY, SIDES, TIMERS

BUILD = ROOT / 'findings/2026-10-12-inverted-chord-on-the-steering-left-edge'
GUARD = 'Steering | LS: Entry Guard'
DEFLECT = 1 << 30                                         # the left stick's deflect, bit 30
REMOVES = {'default': 2851, 'alternative': 2909}          # 90.58's, unchanged


def built(variant):
    return json.loads((BUILD / f'{variant}-candidate.json').read_text(encoding='utf-8'))


def named(variant):
    return (lambda title: map_title(title, RENAME)) if variant == 'alternative' else (lambda title: title)


def inputs(layout):
    """{(layer, source, input): [(kind, settings, actions)]} of every live input."""
    return {(title, source, control): [(kind, entry.get('settings') or {}, layout.layer_ops(entry) or actions(entry))
                                       for kind, entry in entries(value.get('activators') or {})]
            for title in layout.presets for source, group in layout.active(title).items()
            for control, value in (group.get('inputs') or {}).items()}


class OnlyTheTenEdgesChange(unittest.TestCase):
    """The author, 2026-10-12: "all we're doing is updating the edge cleanup bind on the left stick. And all the
    steering layers." And, before the build: "you're going to be keeping the removal lists from ninety fifty eight"."""

    def test_against_90_58_ten_left_edges_differ_and_nothing_else(self):
        for variant in VARIANTS:
            name = named(variant)
            old, new = inputs(Layout(frozen_layout_data(variant, '90.58'))), inputs(Layout(built(variant)))
            self.assertEqual(old.keys(), new.keys())
            self.assertEqual({key for key in old if old[key] != new[key]},
                             {(name(title), 'joystick', 'edge') for title in EDGE_CHORDS}, variant)

    def test_each_chord_carries_the_list_its_press_had_on_90_58_command_for_command(self):
        for variant in VARIANTS:
            name = named(variant)
            old, new = Layout(frozen_layout_data(variant, '90.58')), Layout(built(variant))
            count = lambda layout: sum(1 for found in inputs(layout).values() for _, _, ops in found
                                       for op in ops if isinstance(op, tuple) and op[0] == 'remove_layer')
            self.assertEqual((count(old), count(new)), (REMOVES[variant],) * 2)
            for title in EDGE_CHORDS:
                edge = lambda layout: list(entries(layout.active(name(title))['joystick']['inputs']['edge']['activators']))
                (_, press), (_, guard), *_ = edge(old)
                (_, chord), *_ = edge(new)
                self.assertEqual(old.layer_ops(press), new.layer_ops(chord), title)
                self.assertEqual(len(actions(press)), len(actions(chord)), title)
                self.assertEqual(guard['settings']['gyro_ratchet_button_mask'], chord['settings']['gyro_ratchet_button_mask'])

    def test_the_left_edge_is_one_inverted_chord_and_the_timer_stays_a_soft_press(self):
        timers = {layer: (target, delay) for layer, _, target, delay, _ in TIMERS}
        for variant in VARIANTS:
            layout, name = Layout(frozen_layout_data(variant, '90.64')), named(variant)   # 90.65 put the press back
            for title in EDGE_CHORDS:
                found = list(entries(layout.active(name(title))['joystick']['inputs']['edge']['activators']))
                self.assertEqual([kind for kind, _ in found], ['chord', 'Soft_Press'] if title in timers else ['chord'], title)
                settings = dict(found[0][1]['settings'])
                mask = int(settings.pop('gyro_ratchet_button_mask'))
                self.assertEqual(settings, {'gyro_ratchet_button_requireany_or_all': '0', 'edge_binding_invert': '1',
                                            'hold_repeats': '1', 'interruptable': '0', 'haptic_intensity': '0'}, title)
                self.assertFalse(mask & DEFLECT)
                ops = layout.layer_ops(found[0][1])
                self.assertIn(('remove_layer', name(title)), ops)
                self.assertTrue(all(op == 'remove_layer' for op, _ in ops), title)
                if title in timers:
                    self.assertEqual(layout.layer_ops(found[1][1]), [('add_layer', timers[title][0])], title)

    def test_the_two_driver_layers_chords_have_one_sub_command(self):
        # A repeating chord with more than one sub-command does not fire its repeat (author, 2026-10-10). The
        # driver layers' chords have one; the other eight keep 90.58's lists of two to five.
        for variant in VARIANTS:
            layout, name = Layout(built(variant)), named(variant)        # 90.62 adds one to the two Modifier 2 lists
            sizes = {title: len(actions(list(entries(layout.active(name(title))['joystick']['inputs']['edge']['activators']))[0][1]))
                     for title in EDGE_CHORDS}
            self.assertEqual([sizes[owner] for _, owner, _ in DRIVERS], [1, 1])
            self.assertEqual(sorted(set(sizes.values())), [1, 2, 3, 5], variant)

    def test_inverted_chords_are_on_the_left_edge_of_the_ten_layers_and_the_entry_guard_only(self):
        for variant in VARIANTS:
            layout, name = Layout(frozen_layout_data(variant, '90.64')), named(variant)   # 90.65 put the press back
            found = {(title, source, control) for title in layout.presets
                     for source, group in layout.active(title).items()
                     for control, value in (group.get('inputs') or {}).items()
                     for kind, entry in entries(value.get('activators', {}))
                     if kind == 'chord' and (entry.get('settings') or {}).get('edge_binding_invert') == '1'}
            self.assertEqual(found, {(name(t), 'joystick', 'edge') for t in (*EDGE_CHORDS, GUARD)}, variant)


class EdgeCleanup(ScenarioCase):
    """What the chord is meant to do (A61): off while a driver is held or the stick is at the rim, running
    otherwise. The scenarios of 90.55, C1 to C4, on this build. Since 90.63 the ring is inverted and the chord
    runs at the rim. 90.65 put the press and its guard back (tests/test_scenarios_90_65.py), so these run on the
    90.64 build, the last one with the chord."""

    def held(self):
        for driver, owner, key in DRIVERS:
            for pad in self.each(start=('Base', 'Steering')):
                pad.hold(driver).touch('LS').wait(300)
                yield pad, driver, owner, key

    @scenario('90.61 E1', rules=('R133', 'R170'), rests=('A61', 'A66'), either=('A9', 'A32'), frozen='90.64')
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

    @scenario('90.61 E2', rules=('R133',), rests=('A25', 'A61'), either=('A9', 'A32'), frozen='90.62')
    def test_a_missed_driver_release_clears_when_the_stick_is_off_the_rim(self):
        # On the 90.62 build: 90.63 inverts the ring, and the chord runs at the rim instead (90.63 G2).
        for pad, driver, owner, _ in self.held():
            pad.miss(driver).wait(300)
            self.assertTrue(pad.has(owner))                  # nothing has told the layout yet
            pad.hold('LS edge').wait(100)
            self.assertTrue(pad.has(owner))                  # the chord's own input is pressed: off
            pad.let_go('LS edge').wait(100)
            self.assertTrue(pad.has('Steering') and pad.lacks(owner, *FAMILY))
            self.assertEqual(pad.down(), [])

    @scenario('90.61 E3', rules=('R133',), rests=('A6', 'A25', 'A61'), either=('A9', 'A32'), frozen='90.64')
    def test_a_missed_driver_release_during_a_deflect_leaves_no_stick_layer(self):
        for driver, owner, _ in DRIVERS:
            for direction, *_ in SIDES:
                for pad in self.each(start=('Base', 'Steering')):
                    pad.hold(driver).touch('LS').wait(300).push('LS', direction).wait(100).miss(driver).wait(600)
                    pad.recentre('LS').wait(400)
                    self.assertTrue(pad.lacks(owner, *FAMILY))
                    pad.lift('LS').wait(300)
                    self.assertEqual(pad.down(), [])

    @scenario('90.61 E4', rules=('R133',), rests=('A61',), either=('A9', 'A32'), frozen='90.64')
    def test_pressing_the_driver_again_shuts_the_edge_chord_off(self):
        for pad, driver, owner, key in self.held():
            pad.miss(driver).wait(100).hold(driver).wait(100)
            pad.hold('LS edge').wait(60).let_go('LS edge').wait(200)
            self.assertTrue(pad.has('Steering', owner))
            self.assertIn(key, pad.down())

    @scenario('90.61 E5', rules=('R133',), rests=('A7', 'A61', 'A66'), either=('A9', 'A32'), frozen='90.64')
    def test_the_reported_gesture_keeps_steering_and_the_driver_layer_on_the_simulator(self):
        # A driver held, the right stick touch tapped, the left stick flicked to the rim and back. On the Deck
        # this ended `Steering` on 90.58. The simulator kept it there too: it never misses a held driver.
        for driver, owner, key in DRIVERS:
            for direction in ('up', 'down', 'left', 'right'):
                for pad in self.each(start=('Base', 'Steering')):
                    pad.touch('LS').hold(driver).wait(100).touch('RS')
                    for step in range(8):
                        pad.wait(35).lift('RS').wait(35).touch('RS')
                        if step % 2:
                            pad.recentre('LS')
                        else:
                            pad.push('LS', direction)
                    pad.lift('RS').recentre('LS').wait(400)
                    self.assertTrue(pad.has('Steering', owner), direction)
                    self.assertEqual(pad.down(), [key])

    @scenario('90.61 E6', rules=('R133',), rests=('A7', 'A61', 'A66'), either=('A9', 'A32'), frozen='90.64')
    def test_a_thumb_lifting_with_the_stick_out_keeps_the_driver_layer_and_steering(self):
        # The fault reported on 90.55, which had this chord with longer lists: a thumb lifting in the stick
        # modifiers cleared the W or S layer. Never isolated on the Deck (A66).
        for driver, owner, key in DRIVERS:
            for direction, _, modifier, *_ in SIDES:
                for wait in (60, 300):                       # before and after the 200 ms cover
                    for pad in self.each(start=('Base', 'Steering')):
                        pad.touch('LS').touch('RS').wait(400).hold(driver).wait(300).push('LS', direction).wait(wait)
                        self.assertTrue(pad.has(modifier))
                        pad.lift('RS').wait(60)
                        self.assertTrue(pad.has('Steering', owner) and key in pad.down(), (direction, wait))
                        pad.sim.release(('joystick', 'touch'))
                        pad.wait(60)
                        self.assertTrue(pad.has('Steering', owner) and key in pad.down(), (direction, wait))

    @scenario('90.61 E7', rules=('R133', 'R174'), rests=('A7', 'A17', 'A25', 'A61'), either=('A9', 'A32'), frozen='90.61')
    def test_the_blind_hand_over_after_a_missed_second_driver_clears_itself(self):
        # Both drivers held, the second one's release missed, the first let go: the hand-over adds the other
        # driver's layer with nobody holding it (90.57 M2). On 90.58 it waited for a thumb on a stick; the
        # inverted chord takes it off with the stick centred and no driver held. On the 90.61 build: 90.62 has no
        # hand-over add, and the layer left there waits for a stick (90.62 M1).
        for first, second, other in (('R1', 'L1', 'Steering | L1: S Key'), ('L1', 'R1', 'Steering | R1: W Key')):
            for pad in self.each(start=('Base', 'Steering')):
                pad.hold(first).wait(300).hold(second).wait(300).miss(second).wait(500).let_go(first).wait(300)
                self.assertEqual(pad.stack, pad.layers('Base', 'Steering'))
                self.assertEqual(pad.down(), [])


if __name__ == '__main__':
    unittest.main()
