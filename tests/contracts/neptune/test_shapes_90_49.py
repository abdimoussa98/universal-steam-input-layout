"""Steering flick completion and final-output feedback for pad clicks.

Fixture responsibility: contracts/neptune. See docs/testing.md and tests/test-map.csv.
"""
from tests.support.fixtures.scenarios_90_49 import *

class SteeringScroll(ScenarioCase):
    # Retired in 90.52: the window scrolls at 50 ms and a thumb's lift only closes it (90.52 S6).


    def test_the_edge_states_no_radius_since_90_53(self):
        # 90.49 set the ring to the deadzone's 13276 so that a partial flick released it. Since 90.52 nothing
        # ends on the ring, and since 90.53 these groups use Steam's default (author, 2026-10-10).
        for variant in ('default', 'alternative'):
            layout = Layout(layout_data(variant))
            for title in SCROLL_OWNERS:
                actual = title
                if variant == 'alternative':
                    actual = actual.replace('R1:', 'R2:').replace('L1:', 'L2:')
                group = layout.active(actual)['joystick']
                self.assertNotIn('edge_binding_radius', group['settings'])


class PadClicks(ScenarioCase):



    def test_single_configured_bump_is_on_each_final_click_output(self):
        # On the 90.70 build: since 90.71 the bump is on the final layers' self-hold (test_scenarios_90_71 Shape).
        for variant in ('default', 'alternative'):
            layout = Layout(frozen_layout_data(variant, '90.70'))
            for title, source in (('Base', 'left_trackpad'), ('Base', 'right_trackpad'),
                                  ('RTP: Circular Scroll', 'right_trackpad')):
                entry = layout.active(title)[source]['inputs']['click']['activators']['Soft_Press']
                self.assertEqual(entry['settings']['haptic_intensity'], '0')
            for title, source in (('LTP: Middle Click', 'left_trackpad'),
                                  ('RTP: Middle Click', 'right_trackpad')):
                group = layout.active(title)[source]
                self.assertEqual(group['inputs']['click']['activators']['Full_Press']['settings']['haptic_intensity'], '1')
                for kind in ('Soft_Press',):
                    entries = group['inputs']['click']['activators'][kind]
                    for entry in entries if isinstance(entries, list) else [entries]:
                        self.assertEqual(entry['settings']['haptic_intensity'], '0')
            for title, source in (('LTP: Arrow Keys', 'left_trackpad'),
                                  ('RTP: Mouse Buttons', 'right_trackpad')):
                group = layout.active(title)[source]
                self.assertEqual(group['settings']['haptic_intensity_override'], '5')   # Use Activator Settings, 90.51
                for direction in ('north', 'south', 'east', 'west'):
                    activators = group['inputs'][f'dpad_{direction}']['activators']
                    self.assertEqual(activators['Full_Press']['settings']['haptic_intensity'], '1')
                    if 'chord' in activators:
                        self.assertEqual(activators['chord']['settings']['haptic_intensity'], '0')


if __name__ == "__main__":
    unittest.main()
