"""Scenarios for 90.23: the menu Tap Cover binds both stick touches itself.

The record is findings/2026-10-04-tap-cover-stick-touches/README.md. Until 90.22 the cover
inherited the stick touches. A pad layer that landed between the menu stick guard and the cover
kept the right stick in mouse mode, the cover's own right-stick group is in D-pad mode, and
nothing is inherited across a mode change (A2): lifting the right thumb was not seen, and
`RST: Entry Point` stayed on.
"""
import unittest

from tests.scenario import ScenarioCase, scenario

COVER, PAD = "Menu Buttons: Tap Cover", "RTP: Entry Point"
GUARD = {"LS": "Menu Buttons: Left Stick Guard", "RS": "Menu Buttons: Right Stick Guard"}
TRIO = {"LS": ("LST: Entry Point", "LST: Tap Cover", "LST: Temporary Gyro"),
        "RS": ("RST: Entry Point", "RST: Tap Cover", "RST: Temporary Gyro")}
MENU = ("Menu Left: Entry Point", "Menu Right: Entry Point", *GUARD.values(), COVER)


def cover_over_a_pad_layer(pad, menu, pushed="LS"):
    """A menu button held, a stick pushed out, and the right pad touched before the cover lands at 200 ms.

    From 90.25 to 90.29 the menu cover landed about 750 ms after the menu press here: the guard's reset
    and the pad Entry Point's reset each ticked before their own cover had landed, and each tick restarted
    the other's delay (A13). Since 90.30 the pad's reset is off and both covers land on time; the wait is
    kept."""
    pad.hold(menu).wait(50).push(pushed, "up").wait(60).touch("RP").wait(700)
    return pad


class StickTouches(ScenarioCase):
    def over(self, pad, upper, lower):
        self.assertLess(pad.stack.index(pad.title(lower)), pad.stack.index(pad.title(upper)))

    # On the 90.71 build: since 90.72 the menu layers bind the right pad's touch, so its tap chain (RTP: Entry Point,
    # the Double Tap window, Circular Scroll) no longer opens during a menu hold (90.72 E8).
    @scenario("90.23 C1", rules=("R116", "R117", "R136"), rests=("A2", "A7"), frozen="90.71")
    def test_a_thumb_lift_is_seen_with_a_pad_layer_under_the_cover(self):
        for menu in ("Start", "Select"):
            for thumb, pushed in (("RS", "LS"), ("LS", "RS")):                   # the first is the one 90.22 lost
                for pad in self.each():
                    cover_over_a_pad_layer(pad.touch(thumb).wait(50), menu, pushed)
                    self.assertTrue(pad.has(TRIO[thumb][0], GUARD[pushed]))
                    self.over(pad, COVER, PAD)                                   # the pad layer is between guard and cover
                    self.over(pad, PAD, GUARD[pushed])
                    pad.mark().lift(thumb).wait(50)
                    self.assertTrue(pad.lacks(*TRIO[thumb]))                     # the cover's own Release
                    self.assertTrue(pad.has(COVER, PAD, GUARD[pushed]))          # and nothing else moved
                    pad.lift("RP").wait(50).recentre(pushed).wait(50).let_go(menu).wait(400).lift(pushed).wait(600)
                    self.assertEqual((pad.stack, pad.typed()), (pad.layers("Base"), []))

    @scenario("90.23 C2", rules=("R116",), rests=("A27",))
    def test_a_touch_under_a_held_menu_button_moves_no_layer(self):
        for menu in ("Start", "Select"):
            for pad in self.each():
                pad.hold(menu).wait(50).push("LS", "up").wait(400)
                self.assertEqual(pad.top, COVER)
                held = pad.stack
                pad.mark().touch("RS").wait(300)                                 # the chord guards the cleanup
                self.assertEqual(pad.stack, held)
                pad.lift("RS").wait(300)
                self.assertEqual((pad.stack, pad.typed()), (held, []))
                pad.recentre("LS").wait(50).let_go(menu).wait(400).lift("LS").wait(600)
                self.assertEqual((pad.stack, pad.typed()), (pad.layers("Base"), []))

    # On the 90.71 build: since 90.72 the menu layers bind the right pad's touch, so its tap chain (RTP: Entry Point,
    # the Double Tap window, Circular Scroll) no longer opens during a menu hold (90.72 E8).
    @scenario("90.23 C3", rules=("R116", "R133"), rests=("A2", "A25", "A27"), frozen="90.71")
    def test_a_stick_touch_clears_a_stale_cover_over_a_pad_layer(self):
        for stick in ("RS", "LS"):
            for pad in self.each():
                cover_over_a_pad_layer(pad, "Start")
                self.over(pad, COVER, PAD)
                pad.miss("Start").lift("LS").wait(600)
                stale = (COVER, GUARD["LS"], "Menu Right: Entry Point")
                self.assertTrue(pad.has(*stale))                                 # stale: no button is held
                pad.mark().touch(stick).wait(100)
                # On 90.23 this touch cleared the three menu layers. Since 90.24 `RTP: Tap Cover` is on top and
                # binds both stick touches itself (R169): its cleanup is guarded by the thumb on the pad, so it
                # answers the touch and does nothing. The stale menu layers go on the first stick touch after
                # the thumb has left the pad. 90.22 left them on for good. From 90.25 to 90.29 the pad Entry
                # Point's reset made the menu cover land last, so it was on top and they went at once; the
                # reset is off since 90.30.
                self.assertTrue(pad.has(*stale))
                pad.lift(stick).wait(300).lift("RP").wait(600)
                self.assertTrue(pad.has(*stale) and pad.lacks(PAD))
                pad.touch(stick).wait(100).lift(stick).wait(600)
                self.assertEqual((pad.stack, pad.typed()), (pad.layers("Base"), []))
                pad.mark().tap("Start").wait(300)
                self.assertEqual((pad.typed(), pad.stack), (["TAB"], pad.layers("Base")))  # the next tap is normal


if __name__ == "__main__":
    unittest.main()
