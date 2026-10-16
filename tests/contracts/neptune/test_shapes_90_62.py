"""90.62: rocking in Steering the way the bumper modifiers do it.

From 90.61. With one driver held, pressing the other adds the other driver's layer and then Modifier 2 on top of
it. A Release inside Modifier 2 only removes: the layer of the driver still held is underneath already. Until
90.61 the first driver's Release added it (the hand-over of 90.57), and on the Deck W to S worked and S back to W
did not (author, 2026-10-12). The simulator played both directions before and plays them now.

Fixture responsibility: contracts/neptune. See docs/testing.md and tests/test-map.csv.
"""
from tests.support.fixtures.scenarios_90_62 import *

class Shapes(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Current contracts share one inventory; the historical delta below keeps its own sources.
        cls.layouts = {variant: Layout(layout_data(variant)) for variant in VARIANTS}
        cls.rows = {variant: inputs(layout) for variant, layout in cls.layouts.items()}

    def test_the_second_drivers_press_adds_its_layer_and_then_modifier_2(self):
        # As `R1: Modifier 1`'s chord on L1 adds `L1: Modifier 0` before `R1!L1: Modifier 2`. As they run (A4).
        for variant in VARIANTS:
            layout, name = self.layouts[variant], named(variant)
            for first, own, _, second, other, _, modifier in ORDERS:
                ran = ops_of(layout, name(own), INPUT[variant][second], 'chord')
                self.assertEqual(ran[-2:], [('add_layer', name(other)), ('add_layer', name(modifier))], own)
                self.assertTrue(all(op == 'remove_layer' for op, _ in ran[:-2]), own)

    def test_no_release_in_modifier_2_adds_a_layer(self):
        # R174. The first driver's Release removes Modifier 2 and its own layer; the second's removes Modifier 2
        # and its own layer. Either way the layer of the driver still held is left on underneath.
        for variant in VARIANTS:
            layout, name = self.layouts[variant], named(variant)
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
            layout, name = self.layouts[variant], named(variant)
            for modifier in MODIFIER_2:
                found = [ops for (title, _, _), rows in self.rows[variant].items() if title == name(modifier)
                         for kind, _, ops in rows
                         if kind in ('Full_Press', 'chord') and any(isinstance(op, tuple) and op == ('remove_layer', name(modifier)) for op in ops)]
                self.assertEqual(len(found), 16, modifier)
                for ops in found:
                    # 90.67: the left edge's press also adds the Entry Guard (R176)
                    self.assertEqual({target for op, target in ops if op == 'remove_layer'}, {name(modifier), name(W), name(S)}, modifier)



if __name__ == "__main__":
    unittest.main()
