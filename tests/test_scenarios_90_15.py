"""Scenarios for 90.15: the menu second-press layers type W and S on stick up and down.

Until 90.14, `Menu Left: Escape` and `Menu Right: Tab` left the left stick's up and down open.
In Steering they inherited the add of `Steering | LS: Fallback Hold`, which landed on top and
took the menu button's Release. The record is findings/2026-10-03-menu-second-press-keys/README.md.
90.33 replaced the Fallback Hold by the fallback guard; M1 is rewritten for it, and M2, which was about
the hold's exit timer, is retired.
"""
import unittest

from tests.scenario import ScenarioCase, scenario

GUARD = "Steering | LS: Fallback Guard"
MENU = (("Select", "Menu Left: Escape", "ESCAPE"), ("Start", "Menu Right: Tab", "TAB"))
STICK = (("up", "W"), ("down", "S"))


class MenuSecondPressKeys(ScenarioCase):
    def second_press(self, pad, button):
        """Double-tap a menu button and keep it down: the second-press layer is on."""
        pad.tap(button).wait(40).hold(button).wait(20)
        return pad

    @scenario("90.15 M1", rules=("R136",), rests=("A10", "A14"))
    def test_the_fallback_stays_off_the_second_press_layer_and_the_release_is_not_hidden(self):
        """Until 90.32 the layer kept off was the Fallback Hold. Since 90.33 it is the fallback guard, which
        comes on once the menu button is let go with the stick still out, and then stays (90.33 G2)."""
        for button, layer, tap in MENU:
            for direction, key in STICK:
                for pad in self.each(start="steering"):
                    self.second_press(pad, button).push("LS", direction).wait(100)
                    self.assertEqual((pad.top, pad.down()), (layer, sorted([tap, key])))
                    pad.wait(3000)
                    self.assertTrue(pad.lacks(GUARD))                             # until 90.14 the fallback landed here
                    pad.let_go(button).wait(400)
                    self.assertTrue(pad.lacks(layer))                             # the Release was not hidden
                    self.assertEqual((pad.top, pad.down()), (GUARD, [key]))       # the stick is still out
                    pad.recentre("LS").wait(300)
                    self.assertEqual(pad.names()[:2], ("Base", GUARD))            # it stays, in Steering's place (90.35);
                    self.assertEqual(len(pad.names()), 2 + len([t for t in pad.names() if t.startswith("LST: ")]))   # nothing else

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
                self.assertEqual((pad.top, pad.lacks(GUARD)), (layer, True))
                pad.recentre("LS").lift("LS").wait(400).tap(button).wait(500)
                self.assertEqual(pad.names(), ("Base", "Steering"))


if __name__ == "__main__":
    unittest.main()
