"""Scenarios for 90.72: stick-edge cleanups on the pad layers, and pad-click stand-ins for what they hide.

The record is findings/2026-10-14-pad-stick-edge-cleanups/README.md; the plan is
plans/2026-10-14-pad-stick-edge-cleanups.md.

- The pad click layers have a cleanup function on both stick edges, the four left-pad key layers on the left edge only:
  a copy of their stick-touch cleanup, guarded by the pad's touch (legacy chord IDs 16 and 17). With stick touch the
  touch cleanup clears a stuck pad layer first; the edges are for a controller without it (author, 2026-10-14).
- While a pad layer is on and its thumb is on the pad, the guard hides the stick edges below. A layer whose edge bind
  would be lost does it on the pad's click instead: the Steering stick layers add their cover, and the cover carries the
  click on into the Click Entry Point; the ramp layers remove themselves and add the left pad's Click Entry Point.
- The menu Entry Points and the two menu chord layers block both pad clicks; the left swipes type their keys (R172).

Fixture responsibility: releases/neptune. See docs/testing.md and tests/test-map.csv.
"""
from tests.support.fixtures.scenarios_90_72 import *

class Shape(unittest.TestCase):
    def test_against_90_71_only_the_planned_layers_differ(self):
        for variant in VARIANTS:
            old, new = Layout(frozen_layout_data(variant, "90.71")), Layout(frozen_layout_data(variant, "90.72"))
            name = (lambda t: map_title(t, BACK)) if variant == "alternative" else (lambda t: t)
            changed = {name(t) for t in new.presets
                       if json.dumps(new.active(t), sort_keys=True) != json.dumps(old.active(t), sort_keys=True)}
            # `RTP: Entry Point` only loses the remove of `RTP: Click Entry Point` from its right-edge cleanup.
            # `RTP: Double Tap` only loses the menu layers from its Start and Select Releases: it can no longer open over
            # them, since they bind the right pad's touch.
            self.assertEqual(changed, set(CLICK_LAYERS + KEY_LAYERS + RAMPS + MENU + STAND_INS)
                             | {"RTP: Entry Point", "RTP: Double Tap"}, variant)

    def test_the_edges_copy_the_touch_cleanup(self):
        for variant in VARIANTS:
            layout = Layout(frozen_layout_data(variant, "90.72"))
            for layer in CLICK_LAYERS + KEY_LAYERS:
                for stick in ("joystick", "right_joystick"):
                    group = layout.active(layer)[stick]
                    if stick == "right_joystick" and layer in KEY_LAYERS:
                        self.assertNotIn("edge", group["inputs"], layer)
                        continue
                    touch, edge = group["inputs"]["touch"]["activators"], group["inputs"]["edge"]["activators"]
                    self.assertEqual(edge, {"Full_Press": touch["Full_Press"], "chord": touch["chord"]}, (layer, stick))

    def test_every_stand_in_is_silent(self):
        for variant in VARIANTS:
            layout = Layout(frozen_layout_data(variant, "90.72"))
            for layer in STAND_INS + RAMPS:
                for pad in ("left_trackpad", "right_trackpad"):
                    group = layout.active(map_title(layer, {"L1": "L2", "R1": "R2"}) if variant == "alternative"
                                          else layer).get(pad)
                    if group and "click" in group["inputs"]:
                        self.assertEqual(group["inputs"]["click"]["activators"]["Soft_Press"]["settings"]
                                         .get("haptic_intensity"), "0", (layer, pad))

    def test_this_build_is_its_snapshot(self):
        """Until 90.73 this held the installed layout to the build; since then the build to its snapshot."""
        for variant in VARIANTS:
            snapshot = ROOT / f"versions/neptune/90.72/single-set-{variant}_hold-gyro_90.72.json"
            self.assertEqual(json.loads(snapshot.read_text()), frozen_layout_data(variant, "90.72"), variant)


if __name__ == "__main__":
    unittest.main()
