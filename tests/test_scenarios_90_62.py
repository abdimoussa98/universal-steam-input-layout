"""90.62: rocking in Steering the way the bumper modifiers do it.

From 90.61. With one driver held, pressing the other adds the other driver's layer and then Modifier 2 on top of
it. A Release inside Modifier 2 only removes: the layer of the driver still held is underneath already. Until
90.61 the first driver's Release added it (the hand-over of 90.57), and on the Deck W to S worked and S back to W
did not (author, 2026-10-12). The simulator played both directions before and plays them now.
"""

import json
import unittest

from steam_layout.model import Layout, entries, map_title
from tests.scenario import RENAME, ROOT, VARIANTS, ScenarioCase, frozen_layout_data, layout_data, scenario
from tests.test_scenarios_90_57 import INPUT, MODIFIER_2, ORDERS, S, STEERING, W
from tests.test_scenarios_90_61 import inputs

BUILD = ROOT / 'findings/2026-10-12-steering-rocking-like-the-bumper-modifiers'
REMOVES = {'default': (2851, 2885), 'alternative': (2909, 2943)}            # 90.61, 90.62


def built(variant):
    return json.loads((BUILD / f'{variant}-candidate.json').read_text(encoding='utf-8'))


def named(variant):
    return (lambda title: map_title(title, RENAME)) if variant == 'alternative' else (lambda title: title)


def ops_of(layout, title, control, kind):
    source, name = control
    return layout.layer_ops(dict(entries(layout.active(title)[source]['inputs'][name]['activators']))[kind])


class Shapes(unittest.TestCase):
    def test_the_second_drivers_press_adds_its_layer_and_then_modifier_2(self):
        # As `R1: Modifier 1`'s chord on L1 adds `L1: Modifier 0` before `R1!L1: Modifier 2`. As they run (A4).
        for variant in VARIANTS:
            layout, name = Layout(layout_data(variant)), named(variant)
            for first, own, _, second, other, _, modifier in ORDERS:
                ran = ops_of(layout, name(own), INPUT[variant][second], 'chord')
                self.assertEqual(ran[-2:], [('add_layer', name(other)), ('add_layer', name(modifier))], own)
                self.assertTrue(all(op == 'remove_layer' for op, _ in ran[:-2]), own)

    def test_no_release_in_modifier_2_adds_a_layer(self):
        # R174. The first driver's Release removes Modifier 2 and its own layer; the second's removes Modifier 2
        # and its own layer. Either way the layer of the driver still held is left on underneath.
        for variant in VARIANTS:
            layout, name = Layout(layout_data(variant)), named(variant)
            for first, own, key, second, other, _, modifier in ORDERS:
                self.assertEqual(ops_of(layout, name(modifier), INPUT[variant][first], 'release'),
                                 [('remove_layer', name(modifier)), ('remove_layer', name(own))], modifier)
                self.assertEqual(ops_of(layout, name(modifier), INPUT[variant][second], 'release'),
                                 [('remove_layer', name(modifier)), ('remove_layer', name(other))], modifier)
                press = dict(entries(layout.active(name(modifier))[INPUT[variant][first][0]]['inputs']
                                     [INPUT[variant][first][1]]['activators']))['Full_Press']
                self.assertEqual(press['bindings']['binding'].split(',')[0], f'key_press {key}')

    def test_every_cleanup_function_of_modifier_2_removes_both_driver_layers(self):
        # R128: both sit under it, kept alive by its guard's two drivers. Sixteen cleanup functions a layer.
        for variant in VARIANTS:
            layout, name = Layout(layout_data(variant)), named(variant)
            for modifier in MODIFIER_2:
                found = [ops for (title, _, _), rows in inputs(layout).items() if title == name(modifier)
                         for kind, _, ops in rows
                         if kind in ('Full_Press', 'chord') and any(isinstance(op, tuple) and op == ('remove_layer', name(modifier)) for op in ops)]
                self.assertEqual(len(found), 16, modifier)
                for ops in found:
                    self.assertEqual({target for _, target in ops}, {name(modifier), name(W), name(S)}, modifier)

    def test_against_90_61_only_the_two_driver_layers_and_the_two_modifier_2_layers_change(self):
        for variant in VARIANTS:
            name = named(variant)
            old, new = inputs(Layout(frozen_layout_data(variant, '90.61'))), inputs(Layout(built(variant)))
            self.assertEqual(old.keys(), new.keys())
            changed = {key for key in old if old[key] != new[key]}
            self.assertEqual({title for title, _, _ in changed}, {name(t) for t in (W, S, *MODIFIER_2)}, variant)
            self.assertEqual(len(changed), 2 + 2 * 18, variant)        # two chords; per Modifier 2, two Releases and sixteen cleanups
            count = lambda rows: sum(1 for found in rows.values() for _, _, ops in found
                                     for op in ops if isinstance(op, tuple) and op[0] == 'remove_layer')
            self.assertEqual((count(old), count(new)), REMOVES[variant])
            self.assertEqual(inputs(Layout(frozen_layout_data(variant, '90.64'))), new, variant)  # up to 90.64; 90.65 changes ten edges


class Rocking(ScenarioCase):
    @scenario('90.62 R1', rules=('R174',), rests=('A4', 'A7', 'A9', 'A10', 'A37'), either=('A9', 'A32'))
    def test_rocking_the_drivers_follows_the_held_one_and_steering_stays(self):
        # R1, L1, R1 up (S), R1 down, L1 up (W), L1 down, and round again. While both are held the first one's
        # key stays: Modifier 2 answers both drivers, and the second driver's layer waits underneath.
        for direction in (None, 'up'):
            for pad in self.each(start=('Base', STEERING)):
                pad.hold('R1').wait(300)
                if direction:
                    pad.push('LS', direction).wait(300)
                pad.hold('L1').wait(120)
                for _ in range(3):
                    self.assertEqual(pad.stack[-3:], pad.layers(W, S, 'Steering | R1!L1: Modifier 2'))
                    self.assertEqual(pad.down(), ['W'])
                    pad.let_go('R1').wait(120)
                    self.assertTrue(pad.has(STEERING, S) and pad.lacks(W, *MODIFIER_2))
                    self.assertEqual(pad.down(), ['S'])
                    pad.hold('R1').wait(120)
                    self.assertEqual(pad.stack[-3:], pad.layers(S, W, 'Steering | L1!R1: Modifier 2'))
                    self.assertEqual(pad.down(), ['S'])
                    pad.let_go('L1').wait(120)
                    self.assertTrue(pad.has(STEERING, W) and pad.lacks(S, *MODIFIER_2))
                    self.assertEqual(pad.down(), ['W'])
                    pad.hold('L1').wait(120)
                pad.let_go('L1').wait(120).recentre('LS').wait(300).let_go('R1').wait(300).lift('LS').wait(300)
                self.assertEqual(pad.stack, pad.layers('Base', STEERING))
                self.assertEqual(pad.down(), [])

    @scenario('90.62 R2', rules=('R174',), rests=('A7', 'A9', 'A10'), either=('A9', 'A32'))
    def test_the_second_driver_let_go_first_leaves_the_first_ones_layer_and_key(self):
        for first, own, own_key, second, other, _, modifier in ORDERS:
            for hold in (60, 400):
                for pad in self.each(start=('Base', STEERING)):
                    pad.hold(first).wait(300).hold(second).wait(hold)
                    self.assertTrue(pad.has(own, other, modifier))
                    self.assertEqual(pad.down(), [own_key])                  # no flash of the other key
                    pad.let_go(second).wait(200)
                    self.assertEqual(pad.stack, pad.layers('Base', STEERING, own))
                    self.assertEqual(pad.down(), [own_key])
                    pad.let_go(first).wait(300)
                    self.assertEqual((pad.stack, pad.down()), (pad.layers('Base', STEERING), []))

    @scenario('90.62 R3', rules=('R174',), rests=('A7', 'A9', 'A10'), either=('A9', 'A32'))
    def test_the_other_key_is_never_typed_while_the_first_driver_is_held(self):
        for first, own, own_key, second, other, other_key, modifier in ORDERS:
            for pad in self.each(start=('Base', STEERING)):
                pad.hold(first).wait(300).mark()
                for gap in (20, 60, 250):
                    pad.hold(second).wait(gap).let_go(second).wait(gap)
                self.assertNotIn(other_key, [key for kind, key in pad.seen('down')] if pad.seen('down') else [])
                self.assertEqual(pad.down(), [own_key])


class MissedReleases(ScenarioCase):
    @scenario('90.62 M1', rules=('R128', 'R169'), rests=('A7', 'A25', 'A61'), either=('A9', 'A32'))
    def test_a_missed_release_of_the_second_driver_leaves_its_layer_until_a_thumb_is_on_a_stick(self):
        # The second driver's layer was added under Modifier 2 by its press. Its release never arrives; the first
        # driver's Release uncovers it with nobody holding it. It types nothing. (On 90.61 the hand-over added it
        # there and its edge chord, landing with no driver held, took it off at once.)
        for first, own, _, second, other, _, modifier in ORDERS:
            for stick in ('LS', 'RS'):
                for pad in self.each(start=('Base', STEERING)):
                    pad.hold(first).wait(300).hold(second).wait(300).miss(second).wait(500).let_go(first).wait(300)
                    self.assertEqual((pad.stack, pad.down()), (pad.layers('Base', STEERING, other), []))
                    pad.touch(stick).wait(300).lift(stick).wait(600)
                    self.assertEqual((pad.stack, pad.down()), (pad.layers('Base', STEERING), []))

    @scenario('90.62 M2', rules=('R128', 'R169'), rests=('A7', 'A25'), either=('A9', 'A32'))
    def test_both_releases_missed_a_button_clears_modifier_2_and_both_driver_layers(self):
        for first, own, _, second, other, _, modifier in ORDERS:
            for pad in self.each(start=('Base', STEERING)):
                pad.hold(first).wait(300).hold(second).wait(300).miss(first, second).wait(100)
                self.assertTrue(pad.has(own, other, modifier))
                pad.tap('A', 120).wait(200).tap('A', 120).wait(200)
                self.assertEqual((pad.stack, pad.down()), (pad.layers('Base', STEERING), []))


if __name__ == '__main__':
    unittest.main()
