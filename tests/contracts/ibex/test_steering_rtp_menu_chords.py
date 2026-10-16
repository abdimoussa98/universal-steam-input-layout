"""90.38 generated configuration, ordering, and narrow inverted-edge exception.

The contracts were last written against 90.42. 90.43 replaced `Steering | LS: Fallback Guard` with
`Steering | LS: Entry Guard`, and the tests below name the Entry Guard where the requirement still holds.

Fixture responsibility: contracts/ibex. See docs/testing.md and tests/test-map.csv.
"""
from tests.support.fixtures.steering_rtp_menu_chords import *

class SteeringRtpMenu(unittest.TestCase):
    def each(self):
        for variant in ('default', 'alternative'):
            data = json.loads((ROOT / f'neptune/single-set-{variant}_hold-gyro_latest.json').read_text())
            yield variant, data, Layout(data)

    def test_working_layouts_are_generated_including_stored_order(self):
        # R156. The builder is found by the version in the working layout's title, so this follows each
        # release. Until 90.56 it named the 90.42 builder and failed from 90.43 on. Since the base layout (R177)
        # the built layouts are Ibex's; Neptune's are converted from Ibex after 90.74, which test_convert holds (C1).
        built = [(controller, path) for controller in (controllers.IBEX, controllers.NEPTUNE)
                 for path in controller.working()]
        self.assertTrue(any(controller is controllers.IBEX for controller, _ in built))
        for controller, path in built:
            working = json.loads(path.read_text())
            version = working['controller_mappings']['title'].rsplit(' :: ', 1)[-1]
            if not controller.base and controllers.version_key(version) > controllers.version_key(controller.built_until):
                continue
            with self.subTest(path.name):
                builder = release_builder(version, controller.controller_type)
                self.assertIsNotNone(builder, f'no findings folder holds a build_candidate.py and a stored build of {version}')
                generated = builder.build(controller.variant_of(path))[0]
                generated = json.loads(generated) if isinstance(generated, str) else generated
                self.assertEqual(json.dumps(without_release_text(working)),
                                 json.dumps(without_release_text(generated)))







if __name__ == "__main__":
    unittest.main()
