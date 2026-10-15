"""Scenarios for DSE 1.0: the DualSense Edge's layout, converted from Ibex 1.0 (R180 to R185; C5).

The record is findings/2026-10-15-ibex-base/README.md; the plan is
plans/2026-10-15-controller-dirs-and-release-pipeline.md, part 4. Each runs on the Edge's working layouts
(`self.each(controller="dse")`); the layers they reach count for the Edge, not for Neptune.

- The whole pad, `CP`, has the left pad's gestures: a swipe adds a key layer whose touch types the key, a click on
  the ring gives that direction's arrow key, and a click in the centre gives nothing (R183).
- The mute button is the middle mouse button (R184).
- The gyro has no enable button: it aims in Base and in `Gyro` with both sticks centred, and `Gyro Off Ramp Up`
  turns it off (R185).
- The grips trade places: Shift on the left paddle (L5), Ctrl on the left front button (L4) (R181).
"""
import unittest

from steam_layout.flow_model import chord_condition
from tests.scenario import ScenarioCase, scenario

CP = "center_trackpad"
SWIPES = {"CTP: Escape": ("left", "dpad_west", "ESCAPE"), "CTP: Enter": ("right", "dpad_east", "RETURN"),
          "CTP: Tab": ("up", "dpad_north", "TAB"), "CTP: Backspace": ("down", "dpad_south", "BACKSPACE")}
ARROWS = {"left": "LEFT_ARROW", "right": "RIGHT_ARROW", "up": "UP_ARROW", "down": "DOWN_ARROW"}
PAD_LAYERS = {"CTP: Click Entry Point", "CTP: Arrow Keys", *SWIPES}


def swipe(pad, part):
    """The thumb lands on the whole pad and slides out to a direction, with no click: Base's swipe."""
    pad.touch("CP").wait(20)
    pad.sim.press((CP, "edge"))
    pad.sim.press((CP, part))
    return pad.wait(60)


def on_pad(pad):
    return {title for title in pad.names() if title in PAD_LAYERS}


def gyro_aims(pad):
    """True if the topmost gyro group on the stack turns the gyro into mouse movement now: gyro to mouse, with
    its enable mask, if it has one, met by what is held."""
    for title in reversed(pad.stack):
        group = pad.layout.active(title).get("gyro")
        if group is not None:
            settings = group.get("settings") or {}
            condition = chord_condition(settings) if "gyro_ratchet_button_mask" in settings else None
            return group["mode"] == "gyro_to_mouse" and (condition is None or condition.satisfied(pad.sim.held))
    return False


class WholePad(ScenarioCase):
    @scenario("dse 1.0 E1", rules=("R183",), rests=("A10", "A76"))
    def test_a_swipe_adds_its_key_layer_whose_touch_types_the_key(self):
        for layer, (_, part, key) in SWIPES.items():
            for pad in self.each(controller="dse"):
                swipe(pad, part)
                self.assertEqual(pad.top, layer)
                self.assertEqual(pad.typed(), [key])
                pad.sim.release((CP, part))
                pad.sim.release((CP, "edge"))
                pad.lift("CP").wait(100)
                self.assertEqual(pad.names(), ("Base",))

    @scenario("dse 1.0 E2", rules=("R183",), rests=("A5", "A6", "A10", "A76"))
    def test_a_click_on_the_ring_gives_that_directions_arrow_key(self):
        for where, arrow in ARROWS.items():
            for pad in self.each(controller="dse"):
                pad.press_pad("CP", where).wait(200)
                self.assertEqual(on_pad(pad), {"CTP: Arrow Keys"})
                self.assertEqual(pad.typed(), [arrow])
                pad.let_go_pad("CP").wait(100)
                self.assertEqual(pad.names(), ("Base",))

    @scenario("dse 1.0 E3", rules=("R183",), rests=("A5", "A10", "A76"))
    def test_a_click_in_the_centre_gives_nothing(self):
        for pad in self.each(controller="dse"):
            pad.press_pad("CP", "centre").wait(200)
            self.assertEqual(pad.typed(), [], "no middle click and no Caps Lock")
            self.assertEqual(on_pad(pad), {"CTP: Click Entry Point"})
            pad.let_go_pad("CP").wait(100)
            self.assertEqual(pad.names(), ("Base",))

    @scenario("dse 1.0 E4", rules=("R183",), rests=("A5", "A6", "A76"), either=("A9",))
    def test_a_click_in_a_key_layer_ends_it_and_goes_on_to_the_arrow_keys(self):
        for layer, (where, part, key) in SWIPES.items():
            for pad in self.each(controller="dse"):
                swipe(pad, part)
                pad.sim.press((CP, "click"))
                pad.wait(150)
                self.assertTrue(pad.lacks(layer), "the click removes the key layer")
                self.assertTrue(pad.has("CTP: Arrow Keys"), "Base's click carried on, at the ring")
                self.assertEqual(pad.typed(), [key, ARROWS[where]])
                pad.sim.release((CP, part))
                pad.sim.release((CP, "click"))
                pad.lift("CP").wait(150)
                self.assertEqual(pad.names(), ("Base",))


class TheRest(ScenarioCase):
    @scenario("dse 1.0 E5", rules=("R184",), rests=("A75",))
    def test_mute_is_the_middle_mouse_button_in_base_and_in_a_modifier_layer(self):
        for pad in self.each(controller="dse"):
            pad.tap("Mute")
            self.assertEqual(pad.typed(), ["mouse_button MIDDLE"])
            pad.hold("L1").wait(200).mark()
            self.assertTrue(pad.has("L1: Modifier 0"))
            pad.tap("Mute")
            self.assertEqual(pad.typed(), ["mouse_button MIDDLE"])
            pad.let_go("L1").wait(100)

    @scenario("dse 1.0 E6", rules=("R185",))
    def test_the_gyro_aims_with_the_sticks_centred_and_the_gyro_off_layer_stops_it(self):
        for start in (("Base",), ("Base", "Gyro")):
            for pad in self.each(controller="dse", start=start):
                self.assertTrue(gyro_aims(pad), "no stick touched and no button held")
                pad.push("RS", "right").wait(100)
                self.assertTrue(pad.has("Gyro Off Ramp Up") and not gyro_aims(pad))
                pad.recentre("RS").wait(200)
                self.assertTrue(gyro_aims(pad))

    @scenario("dse 1.0 E7", rules=("R181",))
    def test_shift_is_on_the_left_paddle_and_ctrl_on_the_left_front_button(self):
        paddles = {("switch", "button_back_left"): "LEFT_SHIFT", ("switch", "button_back_right"): "SPACE",
                   ("switch", "button_back_left_upper"): "LEFT_CONTROL", ("switch", "button_back_right_upper"): "LEFT_ALT"}
        for control, key in paddles.items():
            for pad in self.each(controller="dse"):
                pad.sim.press(control)
                pad.wait(30)
                pad.sim.release(control)
                self.assertEqual(pad.typed(), [key], control)


if __name__ == "__main__":
    unittest.main()
