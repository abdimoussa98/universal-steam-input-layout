"""Scenarios for 90.15: the menu second-press layers type W and S on stick up and down.

Until 90.14, `Menu Left: Escape` and `Menu Right: Tab` left the left stick's up and down open.
In Steering they inherited the add of `Steering | LS: Fallback Hold`, which landed on top and
took the menu button's Release. The record is findings/2026-10-03-menu-second-press-keys/README.md.
"""
import unittest

from tests.scenario import ScenarioCase, scenario

HOLD = "Steering | LS: Fallback Hold"
MENU = (("Select", "Menu Left: Escape", "ESCAPE"), ("Start", "Menu Right: Tab", "TAB"))
STICK = (("up", "W"), ("down", "S"))


class MenuSecondPressKeys(ScenarioCase):
    def second_press(self, pad, button):
        """Double-tap a menu button and keep it down: the second-press layer is on."""
        pad.tap(button).wait(40).hold(button).wait(20)
        return pad

    @scenario("90.15 M1", rules=("R136",), rests=("A10",), either=("A9",))
    def test_the_fallback_hold_stays_off_the_second_press_layer_and_the_release_clears_it(self):
        for button, layer, tap in MENU:
            for direction, key in STICK:
                for pad in self.each(start="steering"):
                    self.second_press(pad, button).push("LS", direction).wait(100)
                    self.assertEqual((pad.top, pad.down()), (layer, sorted([tap, key])))
                    self.assertTrue(pad.lacks(HOLD))                              # until 90.14 it landed here
                    pad.let_go(button).wait(400)
                    self.assertTrue(pad.lacks(layer))                             # the Release was not hidden
                    self.assertEqual((pad.top, pad.down()), (HOLD, [key]))        # the stick is still out: the hold is back
                    pad.recentre("LS").wait(300).lift("LS").wait(400)
                    self.assertEqual(pad.names(), ("Base", "Steering"))           # nothing left on

    @scenario("90.15 M2", rules=("R137",), rests=("A16",))
    def test_the_steering_exit_waits_for_the_menu_button(self):
        for pad in self.each(start="steering"):
            self.second_press(pad, "Select").push("LS", "down").wait(3000)
            self.assertTrue(pad.has("Steering", "Menu Left: Escape") and pad.lacks(HOLD))   # no timer while it is held
            pad.let_go("Select").wait(1400)
            self.assertEqual(pad.top, HOLD)
            pad.wait(200)
            self.assertTrue(pad.lacks("Steering", HOLD))                          # 1.5 s after the button went up

    @scenario("90.15 M3", rests=("A10",))
    def test_outside_steering_the_second_press_is_as_it_was(self):
        for button, layer, tap in MENU:
            for direction, key in STICK:
                for pad in self.each():
                    self.second_press(pad, button).push("LS", direction).wait(100)
                    self.assertEqual((pad.top, pad.down()), (layer, sorted([tap, key])))
                    pad.let_go(button).wait(400).recentre("LS").lift("LS").wait(400)
                    self.assertEqual((pad.stack, pad.down()), (pad.layers("Base"), []))

    @scenario("90.15 M4", rests=("A25",))
    def test_a_missed_menu_release_clears_on_the_next_tap(self):
        """The second-press layers have no cleanup function (the Cleanup audit lists them). That is unchanged:
        a release missed while the Steam menu is open leaves the layer on until the button is used again."""
        for button, layer, _ in MENU:
            for pad in self.each(start="steering"):
                self.second_press(pad, button).push("LS", "up").wait(100).miss(button).wait(300)
                self.assertEqual((pad.top, pad.lacks(HOLD)), (layer, True))
                pad.recentre("LS").lift("LS").wait(400).tap(button).wait(500)
                self.assertEqual(pad.names(), ("Base", "Steering"))


if __name__ == "__main__":
    unittest.main()
