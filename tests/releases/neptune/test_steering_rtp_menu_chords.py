"""90.38 generated configuration, ordering, and narrow inverted-edge exception.

The contracts were last written against 90.42. 90.43 replaced `Steering | LS: Fallback Guard` with
`Steering | LS: Entry Guard`, and the tests below name the Entry Guard where the requirement still holds.

Fixture responsibility: releases/neptune. See docs/testing.md and tests/test-map.csv.
"""
from tests.support.fixtures.steering_rtp_menu_chords import *

class SteeringRtpMenu(unittest.TestCase):
    def each(self):
        for variant in ('default', 'alternative'):
            data = json.loads((ROOT / f'neptune/single-set-{variant}_hold-gyro_latest.json').read_text())
            yield variant, data, Layout(data)


    def test_the_90_42_build_is_reproducible_including_stored_order(self):
        # The frozen 90.42 scenarios run on this builder (tests/scenario.py), so it has to keep giving the stored build.
        old = module(FN_STEERING_CLEAR / 'build_candidate.py', 'fn_steering_clear_build')
        for variant in ('default', 'alternative'):
            generated, _ = old.build(variant)
            stored = json.loads((FN_STEERING_CLEAR / f'{variant}-candidate.json').read_text())
            # The release's install wrote title/description, not the builder; leave both inputs intact.
            self.assertEqual(json.dumps(without_release_text(generated)),
                             json.dumps(without_release_text(stored)))






if __name__ == "__main__":
    unittest.main()
