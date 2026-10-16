"""90.57: in `Steering` the first driver's Release hands over, the second driver's Release removes only the Modifier 2 layer, and 264 removes are gone.

Fixture responsibility: contracts/neptune. See docs/testing.md and tests/test-map.csv.
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



    def test_the_w_and_s_layers_name_no_layer_that_answers_the_same_driver(self):
        # R132 as tightened. A stick window binds both drivers and a Modifier 2 layer binds both since this
        # build, so with one of them on, these three binds of the layer underneath do not run.
        for variant, layout, name in self.each():
            for first, own, _, second, _, _, modifier in ORDERS:
                answering = {name(t) for t in (*WINDOWS, *MODIFIER_2)}
                for driver, kinds in ((first, ('release',)), (second, ('release', 'chord'))):
                    for kind, entry in self.found(layout, name(own), INPUT[variant][driver]):
                        if kind not in kinds:
                            continue
                        removed = {t for op, t in layout.layer_ops(entry) if op == 'remove_layer'}
                        self.assertEqual(removed & answering, set(), (own, driver, kind))
                        self.assertTrue({name(t) for t in STICK} <= removed, (own, driver, kind))   # those stay
                entry = dict(self.found(layout, name(own), INPUT[variant][second]))['chord']
                self.assertEqual(layout.layer_ops(entry)[-1], ('add_layer', name(modifier)))

    def test_no_steering_layer_names_a_bumper_cover_and_no_cover_names_a_steering_layer(self):
        for variant, layout, name in self.each():
            covers = {name(c) for c in COVERS}
            steering = [title for title in layout.presets if title == STEERING or title.startswith('Steering | ')]
            for title in steering:
                self.assertEqual([c for c in self.commands(layout, title) if c[4] in covers], [], title)
            for cover in covers:
                self.assertEqual([c for c in self.commands(layout, cover) if c[4] in steering], [], cover)

    def test_the_gyro_modifier_2_releases_name_only_what_can_be_on_the_stack(self):
        # R132. Until 90.56 they also named `Steering`, its Entry Guard, the plain modifiers and the other order,
        # kept by two register entries that end at 90.56.
        for variant, layout, name in self.each():
            for title in GYRO_MODIFIER_2:
                for driver in ('L1', 'R1'):
                    release = dict(self.found(layout, name(title), INPUT[variant][driver]))['release']
                    ops = layout.layer_ops(release)
                    self.assertEqual({op for op, _ in ops}, {'remove_layer'})
                    self.assertEqual({t for _, t in ops}, {name(t) for t in (
                        title, *COVERS, 'Gyro | L1: Modifier 0', 'Gyro | R1: Modifier 1', 'Gyro')}, (title, driver))
                    self.assertEqual(ops[-1][1], 'Gyro')



if __name__ == "__main__":
    unittest.main()
