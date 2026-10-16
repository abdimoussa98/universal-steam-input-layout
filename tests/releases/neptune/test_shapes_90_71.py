"""Scenarios for 90.71: the pad click layers on touch, the bump on the final layer's click.

The record is findings/2026-10-14-pad-click-touch-layers/README.md; the plan is
plans/2026-10-14-pad-click-touch-layers.md.

- `Base` (both pads) and `RTP: Circular Scroll` add the Click Entry Point with a repeating Soft Press, silent.
- The D-pad layers have Requires Click off. Each direction and the centre has a Release that removes the layer.
- The final layers' click is a `hold_layer` on themselves, High; the inverted repeating removal is gone.
- The Middle Click layers send their output on a Soft Press of its own, silent.
- The D-pad layout is Radial Without Overlap (`layout` 0): one direction at a time, so a slide on the ring lets the
  old direction go before the new one comes.

The final layer always lands on a click that is held, so its `hold_layer` and its bump don't run (A5): on the
simulator the click's release leaves the layer on until the thumb moves or lifts, and no gesture bumps. The Deck
says whether Steam does the same.

Fixture responsibility: releases/neptune. See docs/testing.md and tests/test-map.csv.
"""
from tests.support.fixtures.scenarios_90_71 import *

class Shape(unittest.TestCase):
    def test_against_90_70_only_the_six_pad_click_layers_differ(self):
        for variant in VARIANTS:
            old, new = Layout(frozen_layout_data(variant, "90.70")), Layout(frozen_layout_data(variant, "90.71"))
            changed = {title for title in new.presets
                       if json.dumps(new.active(title), sort_keys=True) != json.dumps(old.active(title), sort_keys=True)}
            self.assertEqual({map_title(t, BACK) if variant == "alternative" else t for t in changed},
                             {"Base", "RTP: Circular Scroll", "LTP: Arrow Keys", "RTP: Mouse Buttons",
                              "LTP: Middle Click", "RTP: Middle Click"}, variant)

    def test_the_bump_is_on_the_final_click_alone(self):
        for variant in VARIANTS:
            layout = Layout(frozen_layout_data(variant, "90.71"))
            for title, source in (("Base", "left_trackpad"), ("Base", "right_trackpad"),
                                  ("RTP: Circular Scroll", "right_trackpad")):
                soft = layout.active(title)[source]["inputs"]["click"]["activators"]["Soft_Press"]
                self.assertEqual(soft["settings"], {"haptic_intensity": "0", "hold_repeats": "1", "repeat_rate": "50"})
            for title, source in (("LTP: Arrow Keys", "left_trackpad"), ("RTP: Mouse Buttons", "right_trackpad"),
                                  ("LTP: Middle Click", "left_trackpad"), ("RTP: Middle Click", "right_trackpad")):
                group = layout.active(title)[source]
                for name, node in group["inputs"].items():
                    for kind, entry in entries(node["activators"]):
                        hold = any("hold_layer" in a for a in actions(entry))
                        scroll_repeat = kind == "chord"
                        level = "3" if hold else "1" if scroll_repeat else "0"
                        self.assertEqual(entry["settings"].get("haptic_intensity"), level, (title, name, kind))
                        if hold:
                            self.assertEqual((kind, entry["settings"].get("interruptable")), ("Soft_Press", "0"))
                        self.assertNotEqual(entry["settings"].get("edge_binding_invert"), "1", (title, name))
                if group["mode"] == "dpad":
                    self.assertEqual(group["settings"]["requires_click"], "0")
                    for name in ("dpad_north", "dpad_south", "dpad_east", "dpad_west", "edge"):
                        self.assertEqual([op for op, _ in layout.layer_ops(group["inputs"][name]["activators"]["release"])],
                                         ["remove_layer"])


if __name__ == "__main__":
    unittest.main()
