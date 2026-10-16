"""90.57: in `Steering` the first driver's Release hands over, the second driver's Release removes only the Modifier 2 layer, and 264 removes are gone.

Fixture responsibility: releases/neptune. See docs/testing.md and tests/test-map.csv.
"""
from tests.support.fixtures.scenarios_90_57 import *

class Shapes(unittest.TestCase):
    def each(self, frozen=None):
        for variant in ('default', 'alternative'):
            layout = Layout(frozen_layout_data(variant, frozen) if frozen else layout_data(variant))
            yield variant, layout, (lambda title, v=variant: map_title(title, RENAME) if v == 'alternative' else title)

    @staticmethod
    def found(layout, title, control):
        source, name = control
        return list(entries(layout.active(title)[source]['inputs'][name]['activators']))

    @staticmethod
    def commands(layout, title):
        """Every layer command of a layer: (source, input, kind, op, target)."""
        return [(source, name, kind, op, target) for source, group in layout.active(title).items()
                for name, value in (group.get('inputs') or {}).items()
                for kind, entry in entries(value.get('activators') or {}) for op, target in layout.layer_ops(entry)]

    def test_the_second_driver_has_one_release_with_one_remove_and_no_timer(self):
        # On the 90.61 build: since 90.62 that Release also removes the second driver's layer under Modifier 2.
        for variant, layout, name in self.each(frozen='90.61'):
            for _, _, _, second, _, _, modifier in ORDERS:
                found = self.found(layout, name(modifier), INPUT[variant][second])
                self.assertEqual([kind for kind, _ in found], ['release'], modifier)
                self.assertEqual(layout.layer_ops(found[0][1]), [('remove_layer', name(modifier))])
                delays = [entry['settings'] for group in layout.active(name(modifier)).values()
                          for value in (group.get('inputs') or {}).values()
                          for _, entry in entries(value.get('activators') or {})
                          if (entry.get('settings') or {}).get('delay_start')]
                self.assertEqual(delays, [], modifier)

    def test_the_first_driver_keeps_its_key_and_hands_over_with_the_add_stored_last(self):
        # R174. Stored last runs first (A4): the other driver's layer is on before either remove runs.
        # On the 90.61 build: since 90.62 the other driver's layer is on already and the Release only removes.
        for variant, layout, name in self.each(frozen='90.61'):
            for first, own, key, _, other, _, modifier in ORDERS:
                found = self.found(layout, name(modifier), INPUT[variant][first])
                self.assertEqual([kind for kind, _ in found], ['Full_Press', 'release'], modifier)
                press, release = found[0][1], found[1][1]
                self.assertEqual(press['bindings']['binding'].split(',')[0], f'key_press {key}')
                self.assertEqual(press['settings'].get('interruptable'), '0')
                self.assertNotIn('hold_repeats', press['settings'])
                self.assertEqual(layout.layer_ops(release), [('add_layer', name(other)), ('remove_layer', name(modifier)),
                                                             ('remove_layer', name(own))])       # as they run
                self.assertIn('add_layer', release['bindings']['binding'][-1])                   # as they are stored




    def test_the_build_has_264_removes_fewer_than_90_56(self):
        def removes(path):
            layout = Layout(json.loads(path.read_text(encoding='utf-8')))
            return sum(1 for title in layout.presets for group in layout.active(title).values()
                       for value in (group.get('inputs') or {}).values()
                       for _, entry in entries(value.get('activators') or {})
                       for op, _ in layout.layer_ops(entry) if op == 'remove_layer')
        for variant, before, after in (('default', 4277, 4013), ('alternative', 4347, 4083)):
            self.assertEqual(removes(ROOT / f'versions/neptune/90.56/single-set-{variant}_hold-gyro_90.56.json'), before)
            self.assertEqual(removes(BUILD / f'{variant}-candidate.json'), after)


if __name__ == "__main__":
    unittest.main()
