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
"""
import json
import unittest

from steam_layout.model import Layout, actions, entries, map_title
from tests.scenario import BACK, SOURCES, VARIANTS, ScenarioCase, frozen_layout_data, scenario

# pad: its Click Entry Point, its D-pad layer, its Middle Click layer, the outputs for left and up, the centre's
PADS = {"LP": ("LTP: Click Entry Point", "LTP: Arrow Keys", "LTP: Middle Click", "LEFT_ARROW", "UP_ARROW", "CAPSLOCK"),
        "RP": ("RTP: Click Entry Point", "RTP: Mouse Buttons", "RTP: Middle Click", "mouse_button BACK",
               "mouse_wheel SCROLL_UP", "mouse_button MIDDLE")}
PAD_LAYERS = {title for values in PADS.values() for title in values[:3]}


def ring_slide(pad, name, old, new):
    """Move a clicked thumb along the ring: the old direction lets go, then the new one presses (layout 0)."""
    source = SOURCES[name]
    pad.sim.release((source, old))
    pad.sim.press((source, new))
    return pad


def let_go_click(pad, name):
    pad.sim.release((SOURCES[name], "click"))
    return pad


def bumps(pad):
    return [detail for _, detail in pad.seen("haptic")]


def on_pad(pad):
    return {t for t in pad.names() if t in PAD_LAYERS}


class PadClickTouchLayers(ScenarioCase):
    @scenario("90.71 P1", rules=("R113",), rests=("A5", "A6", "A10"))
    def test_a_click_on_a_direction_sends_it_once_through_the_entry_point(self):
        for name, (entry, dpad, _, left, _, _) in PADS.items():
            for pad in self.each():
                pad.mark().press_pad(name, "left").wait(4)
                self.assertEqual(on_pad(pad), {entry})
                pad.wait(1)
                self.assertEqual(on_pad(pad), {dpad})
                pad.wait(200)
                self.assertEqual(pad.typed(), [left])
                self.assertEqual(bumps(pad), [], "the add and the hand-over are silent; the hold lands on a held click")

    @scenario("90.71 P2", rules=("R114",), rests=("A5", "A6", "A10"), either=("A9",))
    def test_a_ring_slide_with_the_click_held_leaves_and_re_enters_once_per_direction(self):
        """The author, 2026-10-14: a clicked pad isn't slid ("that release would never fire unless that layer is
        stuck"). This is the record of what a slide would do.

        If Steam fires the exposed add (A9), the entry point is back at once and the new direction comes 5 ms
        later. If not, the add waits for its next repeat (50 ms): on the right pad the mouse moves meanwhile, on
        the left pad Base's swipe of the new direction runs first, so a slide up adds `Tab` and types it."""
        for name, (entry, dpad, _, left, up, _) in PADS.items():
            for pad in self.each():
                pad.press_pad(name, "left").wait(100).mark()
                ring_slide(pad, name, "dpad_west", "dpad_north")
                if not pad.sim.exposed_fires:
                    self.assertEqual(on_pad(pad), set(), "the Release took the layer off")
                    pad.wait(150)
                    # Until 90.72 the left pad stayed in `Tab` and typed Tab. Since 90.73 the key layer's repeating
                    # click removes it at once and Base's click carries on, as on the right pad.
                    self.assertEqual((on_pad(pad), pad.typed()), ({dpad}, [up]))
                    continue
                self.assertEqual(on_pad(pad), {entry}, "the Release took the layer off; the repeating add is back")
                pad.wait(5)
                self.assertEqual(on_pad(pad), {dpad})
                pad.wait(100)
                self.assertEqual(pad.typed(), [up])
                self.assertEqual([d for w, d in pad.seen("add") if not d.startswith(("LTP", "RTP"))], [],
                                 "Base's swipes don't run in the gap")

    @scenario("90.71 P3", rests=("A5",))
    def test_letting_go_of_the_click_leaves_the_layer_until_the_thumb_moves(self):
        for name, (_, dpad, _, _, _, _) in PADS.items():
            for pad in self.each():
                pad.press_pad(name, "left").wait(100)
                let_go_click(pad, name).wait(300).mark()
                self.assertEqual(on_pad(pad), {dpad})
                self.assertEqual(pad.typed(), [])
                pad.lift(name).wait(100)
                self.assertEqual(on_pad(pad), set())

    @scenario("90.71 P4", rules=("R114",), rests=("A5", "A6", "A10"), either=("A9",))
    def test_a_slide_through_the_centre_with_the_click_held_hands_over_to_middle_click(self):
        for name, (_, _, middle, _, _, centre) in PADS.items():
            for pad in self.each():
                pad.press_pad(name, "left").wait(100).mark()
                pad.slide_pad(name, "centre").wait(100)
                self.assertEqual(on_pad(pad), {middle})
                self.assertEqual(pad.typed(), [centre])
                pad.slide_pad(name, "up").wait(100)
                self.assertEqual(on_pad(pad), {middle}, "a single button has no directions to leave by")
                self.assertEqual(pad.typed(), [centre])
                let_go_click(pad, name).lift(name).wait(100)
                self.assertEqual(on_pad(pad), set())

    @scenario("90.71 P5", rules=("R113",), rests=("A5", "A6", "A10"))
    def test_a_centre_click_sends_the_middle_output_once_and_lifting_ends_it(self):
        for name, (_, _, middle, _, _, centre) in PADS.items():
            for pad in self.each():
                pad.mark().press_pad(name, "centre").wait(200)
                self.assertEqual(on_pad(pad), {middle})
                self.assertEqual(pad.typed(), [centre])
                let_go_click(pad, name).wait(100)
                self.assertEqual(on_pad(pad), {middle})
                pad.lift(name).wait(100)
                self.assertEqual(on_pad(pad), set())

    @scenario("90.71 P6", rests=("A6",))
    def test_a_held_scroll_bumps_low_on_its_repeats_only(self):
        for pad in self.each():
            pad.mark().press_pad("RP", "up").wait(400)
            self.assertGreater(pad.typed().count("mouse_wheel SCROLL_UP"), 1)
            self.assertTrue(bumps(pad))
            self.assertEqual({b.split()[0] for b in bumps(pad)}, {"1"})
            self.assertTrue(all(b.endswith("right_trackpad/dpad_north") for b in bumps(pad)))


    # The 90.70 scenarios these replace are pinned to the 90.70 build (90.14 P4, P8, P10 to P12; 90.16 X1, X2;
    # 90.17; 90.18; 90.19 K1 to K3). A stuck final layer is the author's accepted case (2026-10-14): the touch
    # Release, or a direction's Release, takes it off the next time the pad is used.

    @scenario("90.71 P7", rests=("A5", "A25"), either=("A9",))
    def test_a_missed_click_release_leaves_the_layer_until_the_thumb_lifts(self):
        for where, layer in (("centre", "RTP: Middle Click"), ("left", "RTP: Mouse Buttons")):
            for pad in self.each():
                pad.press_pad("RP", where).wait(100)
                self.assertTrue(pad.has(layer))
                pad.recentre("RP").miss("RP click").wait(300)
                # Nothing on the click takes it off now. Off a direction, its Release does; the click still seems
                # held, so if Steam fires the exposed add (A9) the entry point is back and hands over at the centre.
                stays = where == "centre" or pad.sim.exposed_fires
                self.assertEqual(bool(on_pad(pad)), stays)
                pad.lift("RP").wait(300)
                self.assertEqual((pad.stack, pad.down()), (pad.layers("Base"), []))

    @scenario("90.71 P8", rests=("A5", "A6", "A10"), either=("A9",))
    def test_a_touch_release_before_the_click_lets_go_is_cleared_by_the_next_touch(self):
        """The thumb lifts and the touch Release is seen before the click's. If Steam fires the exposed add (A9),
        the entry point is back under the held click with no thumb on the pad, hands over to Middle Click (the
        thumb is nowhere, so the centre), which sends its output and stays. The next touch and lift take it off."""
        for name, (_, _, middle, _, _, centre) in PADS.items():
            source = SOURCES[name]
            for where in ("centre", "left"):
                for pad in self.each():
                    pad.press_pad(name, where).wait(100).mark()
                    pad.recentre(name)
                    pad.sim.release((source, "touch"))
                    pad.wait(20)
                    let_go_click(pad, name).wait(300)
                    if pad.sim.exposed_fires:
                        self.assertEqual(on_pad(pad), {middle})
                        self.assertEqual(pad.typed(), [] if where == "centre" else [centre])
                    else:
                        self.assertEqual(on_pad(pad), set())
                    pad.mark().touch(name).wait(100).lift(name).wait(300)
                    self.assertEqual((on_pad(pad), pad.typed(), pad.down()), (set(), [], []))

    @scenario("90.71 P9", rules=("R113",), rests=("A5", "A6", "A10"))
    def test_a_modifier_and_a_pad_click_leave_each_other_alone(self):
        for pad in self.each():                                                           # the modifier first
            pad.hold("L1").wait(50).press_pad("RP", "centre").wait(100)
            self.assertEqual((pad.top, pad.down()), ("RTP: Middle Click", ["mouse_button MIDDLE"]))
            self.assertTrue(pad.has("L1: Modifier 0"))
            pad.let_go_pad("RP").wait(300)
            self.assertTrue(pad.has("L1: Modifier 0") and not on_pad(pad))
            pad.let_go("L1").wait(400)
            self.assertEqual((pad.stack, pad.down()), (pad.layers("Base"), []))
        for pad in self.each():                                                           # the click first
            pad.press_pad("RP", "centre").wait(100).hold("L1").wait(100)
            self.assertEqual((pad.top, pad.down()), ("L1: Modifier 0", ["mouse_button MIDDLE"]))
            pad.let_go_pad("RP").wait(300)
            self.assertEqual((pad.top, pad.down()), ("L1: Modifier 0", []))               # the pad's exit wasn't hidden
            pad.let_go("L1").wait(400)
            self.assertEqual(pad.stack, pad.layers("Base"))

    @scenario("90.71 P10", rules=("R113",), rests=("A5", "A6", "A10"))
    def test_a_pad_click_in_steering_ends_on_the_lift_and_steering_stays(self):
        for where, output in (("centre", "mouse_button MIDDLE"), ("left", "mouse_button BACK")):
            for pad in self.each(start="steering"):
                pad.mark().press_pad("RP", where).wait(100)
                self.assertTrue(pad.has("Steering") and on_pad(pad))
                pad.let_go_pad("RP").wait(300)
                self.assertEqual((pad.names(), pad.typed(), pad.down()), (("Base", "Steering"), [output], []))

    @scenario("90.71 P11", rules=("R113",), rests=("A5", "A6", "A10"))
    def test_a_click_in_circular_scroll_stays_middle_click_until_the_thumb_lifts(self):
        """In 90.70 the click's release went back to scrolling. Now the Middle Click layer stays until the lift
        (A5: its self-hold doesn't run on the click it landed on)."""
        touch = ("right_trackpad", "touch")
        for pad in self.each():
            pad.sim.press(touch).wait(60).release(touch)                                  # a tap, then a swipe up
            pad.wait(50)
            pad.sim.press(touch).press(("right_trackpad", "dpad_north")).release(("right_trackpad", "dpad_north"))
            self.assertEqual(pad.top, "RTP: Circular Scroll")
            pad.wait(200).mark().hold("RP click").wait(100)
            self.assertEqual((pad.names()[-2:], pad.down()),
                             (("RTP: Circular Scroll", "RTP: Middle Click"), ["mouse_button MIDDLE"]))
            pad.let_go("RP click").wait(100)
            self.assertEqual(pad.top, "RTP: Middle Click")
            pad.sim.release(touch)
            pad.wait(300)
            self.assertEqual(pad.stack, pad.layers("Base"))


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
