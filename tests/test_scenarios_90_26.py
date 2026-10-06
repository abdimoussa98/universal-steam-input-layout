"""Scenarios for 90.26: hold delays of at most 200 ms and the pad clicks' reset.

The record is findings/2026-10-04-standard-delays/README.md.

- A "hold" is a delayed `add_layer` with a reset on the same input (R120): the modifiers' cursor
  and covers, the Fn layers, `Menu Keys`, the second-press covers and the Tap Covers of the stick
  and pad Entry Points. Its reset repeats 50 ms after its delay (R121).
- A hold that nothing disturbs lands at its delay, and its reset never repeats.
- A removal from outside restarts a delay that is counting (A13). Later than 50 ms into a 200 ms
  hold, that pushes it past its own reset, which restarts it once more (A12): it lands at 450 ms.
  The simulator counts a removal that takes nothing off like any other; the right pad's own reset
  is one, and it trades restarts with the hold's reset.
- The Click Entry Points' outer bind, 5 ms, has its reset on the pad's touch.
- 90.26 also changed the touch layers of the pad bump. They are gone since 90.27, with their scenario,
  P1 (findings/2026-10-04-pad-touch-bump/README.md). D1 is now the left pad costing a hold nothing.
"""
import unittest

from tests.scenario import SOURCES, ScenarioCase, scenario

MENU_KEYS = "Menu Keys"
# the button, the layer its 200 ms hold adds
SINGLE = (("L1", "L1: Temp Cursor Gyro"), ("R1", "R1: Temp Cursor Gyro"),
          ("Select", "Menu Left: Fn Layer"), ("Start", "Menu Right: Fn Layer"))
STARTS = (None, ("Base", "Gyro"))
# pad: its Click Entry Point, and the outer layer and its key for a click on the left
PADS = {"RP": ("RTP: Click Entry Point", "RTP: Mouse Buttons", "mouse_button BACK"),
        "LP": ("LTP: Click Entry Point", "LTP: Arrow Keys", "LEFT_ARROW")}


def landed(pad, title, since=0):
    """When the layer was added, in ms after `since`, or None."""
    title = pad.title(title)
    return next((ms - since for ms, _, detail in pad.sim.events("add", since=since) if detail == title), None)


class Holds(ScenarioCase):
    @scenario("90.26 H1", rules=("R121",), rests=("A16",))
    def test_every_single_button_hold_lands_at_200_ms(self):
        for start in STARTS:
            for button, layer in SINGLE:
                for pad in self.each(start=start):
                    pad.hold(button).wait(199)
                    self.assertTrue(pad.lacks(layer), layer)
                    pad.wait(1)
                    self.assertTrue(pad.has(layer), layer)

    @scenario("90.26 H2", rules=("R121",), rests=("A16",))
    def test_modifier_2_and_menu_keys_take_200_ms_from_the_second_button(self):
        for first, second, layer in (("L1", "R1", "L1&R1: Tap Cover"), ("R1", "L1", "L1&R1: Tap Cover"),
                                     ("Select", "Start", MENU_KEYS), ("Start", "Select", MENU_KEYS)):
            for pad in self.each():
                pad.hold(first).wait(40).hold(second).wait(199)
                self.assertTrue(pad.lacks(layer), layer)                     # Menu Keys came at 150 ms in 90.25
                pad.wait(1)
                self.assertTrue(pad.has(layer), layer)

    @scenario("90.26 H3", rules=("R121",), rests=("A16",))
    def test_the_steering_modifiers_take_200_ms(self):
        for driver, direction in (("L1", "down"), ("L1", "up"), ("R1", "down"), ("R1", "up")):
            for pad in self.each():
                pad.enter_steering().hold(driver).wait(400)
                pad.push("LS", direction).wait(199)
                self.assertTrue(pad.lacks("Steering | LS: Tap Cover"))       # 250 ms until 90.25
                pad.wait(1)
                self.assertTrue(pad.has("Steering | LS: Tap Cover"))
        for first, second, cover in (("L1", "R1", "R1: Tap Cover"), ("R1", "L1", "L1: Tap Cover")):
            for pad in self.each():
                pad.enter_steering().hold(first).wait(400)
                pad.hold(second).wait(199)
                self.assertTrue(pad.lacks(cover))
                pad.wait(1)
                self.assertTrue(pad.has(cover))

    @scenario("90.26 H4", rules=("R120", "R121", "R122"), rests=("A6",))
    def test_the_reset_of_a_hold_that_nothing_disturbs_never_removes_its_layer(self):
        for button, layer in SINGLE:
            for pad in self.each():
                pad.hold(button).wait(1500)                                  # six of the reset's intervals
                self.assertEqual(landed(pad, layer), 200)
                self.assertEqual([detail for _, detail in pad.seen("remove")], [])
                self.assertTrue(pad.has(layer))
        for stick, cover in (("LS", "LST: Tap Cover"), ("RS", "RST: Tap Cover"), ("RP", "RTP: Tap Cover")):
            for pad in self.each():
                pad.touch(stick).wait(1500)
                self.assertEqual(landed(pad, cover), 150)                    # its reset is at 200 ms
                self.assertTrue(pad.has(cover))


class Disturbed(ScenarioCase):
    """What an outside removal costs a hold that is still counting."""

    @scenario("90.26 D1", rules=("R121",), rests=("A13",))
    def test_a_left_pad_touch_during_a_hold_costs_nothing(self):
        # Base's left pad binds no touch again (90.27), so nothing is removed under the hold. With the
        # touch layers of 90.25 and 90.26 a touch later than 50 ms into the hold moved it to 450 ms.
        for button, layer in SINGLE:
            for at in (30, 51, 100, 190):
                for pad in self.each():
                    pad.hold(button).wait(at).touch("LP").wait(1000)
                    self.assertEqual(landed(pad, layer), 200, (button, at))

    @scenario("90.26 D2", rules=("R121",), rests=("A12", "A13"))
    def test_a_stick_touch_during_a_hold_costs_nothing(self):
        # Every hold layer binds both stick touches, so no Entry Point's removal runs under it.
        for button, layer in SINGLE:
            for stick in ("LS", "RS"):
                for pad in self.each():
                    pad.hold(button).wait(100).touch(stick).wait(1000)
                    self.assertEqual(landed(pad, layer), 200, (button, stick))

    @scenario("90.26 D3", rules=("R121",), rests=("A12", "A13"))
    def test_a_right_pad_touch_around_a_hold_costs_nothing_since_90_30(self):
        # From 90.25 to 90.29 `RTP: Entry Point` had a Tap Cover reset. As the simulator reads A13, a reset's
        # repeat that removes nothing still restarts every delay that is counting, so the pad's reset and the
        # hold's traded restarts: the hold landed between 230 and 950 ms, or up to 700 ms with the pad first.
        # The reset is off since 90.30 (the author, 2026-10-04), and a pad touch does nothing to a hold.
        for button, layer in SINGLE:
            for at in (30, 60, 100, 190):
                for pad in self.each():
                    pad.hold(button).wait(at).touch("RP").wait(2000)
                    self.assertEqual((landed(pad, layer), landed(pad, "RTP: Tap Cover")), (200, at + 150), (button, at))
            for at in (30, 60, 100, 150):                                            # the pad first
                for pad in self.each():
                    pad.touch("RP").wait(at).hold(button).wait(2000)
                    self.assertEqual(landed(pad, layer, since=at), 200, (button, at))


class Pads(ScenarioCase):
    @scenario("90.26 P2", rules=("R120",), rests=("A6", "A40"))
    def test_the_outer_clicks_reset_fires_once_on_nothing_and_leaves_with_its_layer(self):
        for name, (click, outer, outer_key) in PADS.items():
            for pad in self.each():
                pad.touch(name)
                pad.sim.press((SOURCES[name], "edge"))
                pad.wait(50).mark()
                pad.press_pad(name, "left").wait(4)
                self.assertEqual(pad.top, click)                             # the outer bind's 5 ms
                self.assertEqual(pad.seen("remove"), [])                     # the reset found nothing to remove
                pad.wait(1)
                self.assertEqual((pad.top, pad.down()), (outer, [outer_key]))
                pad.wait(600)                                                # eleven of the reset's intervals
                self.assertEqual((pad.top, pad.down()), (outer, [outer_key]))
                self.assertEqual(pad.seen("remove"), [("remove", pad.title(click))])


if __name__ == "__main__":
    unittest.main()
