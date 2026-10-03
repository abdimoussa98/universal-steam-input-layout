"""Scenarios for the Deck checks of the Temp Cursor Gyro (the checklist's "Temp cursor gyro" section).

The cursor is the overlay a single modifier adds after 300 ms. Its settings and the shape of its
bindings are checked by tests/test_neptune_cursor.py; these scenarios check what happens over time.
"""
import unittest

from tests.scenario import ScenarioCase, scenario

SIDES = (("L1", "R1", "L1: Modifier 0"), ("R1", "L1", "R1: Modifier 1"))
STARTS = (None, ("Base", "Gyro"))


def names(side):
    return f"{side}: Temp Cursor Gyro", f"{side}: Tap Cover"


class TempCursorGyro(ScenarioCase):
    @scenario("Temp cursor gyro TC1", rules=("R120",))
    def test_the_cursor_lands_at_300_ms_and_the_release_sends_nothing(self):
        for start in STARTS:
            for side, _, _ in SIDES:
                cursor, _ = names(side)
                for pad in self.each(start=start):
                    home = pad.stack
                    pad.hold(side).wait(299)
                    self.assertTrue(pad.lacks(cursor))
                    pad.wait(1)
                    self.assertEqual(pad.top, cursor)
                    pad.let_go(side).wait(300)
                    self.assertEqual((pad.stack, pad.typed()), (home, []))   # no tap or scroll

    @scenario("Temp cursor gyro TC3", rules=("R117", "R123"))
    def test_a_thumb_lift_before_300_ms_enters_the_cursor_at_once(self):
        for side, _, _ in SIDES:
            cursor, _ = names(side)
            for stick in ("LS", "RS"):
                for pad in self.each():
                    pad.hold(side).wait(100).touch(stick).wait(20).lift(stick)
                    self.assertEqual(pad.top, cursor)
                    self.assertFalse([t for t in pad.stack if t.startswith(("LST", "RST"))])    # that stick's helpers cleared
                    pad.touch("LS").lift("LS").touch("RS").lift("RS")        # more lifts leave the cursor on
                    self.assertEqual(pad.top, cursor)

    @scenario("Temp cursor gyro TC4", rules=("R122", "R135"), rests=("A11", "A35"), either=("A9",))
    def test_a_cancel_input_puts_the_tap_cover_on_for_the_rest_of_the_hold(self):
        for side, other, _ in SIDES:
            cursor, cover = names(side)
            for when in (100, 300, 600):                                     # before, at and after 300 ms
                for button in ("A", "Up", "Start"):
                    for pad in self.each():
                        pad.hold(side).wait(when).mark().hold(button).wait(100)
                        self.assertEqual(pad.top, cover)
                        self.assertEqual(len(pad.typed()), 1)                # the modifier's own output, once
                        pad.let_go(button).touch("RS").lift("RS").wait(400)
                        self.assertEqual(pad.top, cover)                     # a later thumb lift doesn't bring the cursor back
            for pad in self.each():
                pad.hold(side).wait(350).hold(other).wait(150)               # the opposite modifier: the cursor leaves,
                self.assertTrue(pad.lacks(cursor))                           # and Modifier 2 comes on the parent's repeat
                self.assertIn("Modifier 2", pad.top)

    @scenario("Temp cursor gyro TC6", rules=("R122",), either=("A32",))
    def test_a_cancel_input_and_a_thumb_lift_together_at_300_ms(self):
        for side, _, _ in SIDES:
            cursor, cover = names(side)
            for first in ("button", "thumb"):
                for pad in self.each():
                    pad.hold(side).touch("RS").wait(299)
                    if first == "button":
                        pad.hold("A").lift("RS")
                    else:
                        pad.lift("RS").hold("A")
                    pad.wait(200)
                    self.assertEqual(pad.top, cover)                         # the cover wins either way
                    self.assertTrue(pad.lacks(cursor))

    @scenario("Temp cursor gyro TC8", rests=("A38",))
    def test_one_stick_keeps_the_cursor_and_both_remove_it(self):
        """How far the sticks have to travel is a tuning note; a stick here is in or out."""
        for side, _, _ in SIDES:
            cursor, cover = names(side)
            for first, second in (("RS", "LS"), ("LS", "RS")):
                for pad in self.each():
                    pad.hold(side).wait(350).push(first, "up" if first == "LS" else None).wait(100)
                    self.assertEqual(pad.top, cursor)                        # one stick alone
                    pad.push(second, "up" if second == "LS" else None).wait(100)
                    self.assertEqual(pad.top, cover)                         # both
            for pad in self.each():
                pad.push("LS", "up").push("RS").hold(side).wait(400)         # both out before the modifier
                self.assertEqual(pad.top, cover)

    @scenario("Temp cursor gyro TC9", rules=("R128", "R133"), rests=("A17", "A25", "A38"))
    def test_a_lost_modifier_clears_with_its_overlays(self):
        """The checklist expected the recovery to run while the sticks stay out. A chord latches (A17): the
        guard that was active when the stick went out stays active, so the cleanup function runs on the next
        fresh input instead. Nothing is left over once it has."""
        for side, _, modifier in SIDES:
            cursor, cover = names(side)
            for pad in self.each():
                pad.hold(side).wait(350).push("RS").push("LS", "up").wait(100).miss(side).wait(300)
                self.assertTrue(pad.has(modifier))                           # still on: the guards are latched
                pad.recentre("RS").recentre("LS").wait(100).push("RS")       # a fresh push
                self.assertTrue(pad.lacks(modifier, cursor, cover))
            for pad in self.each():
                pad.touch("RS").hold(side).wait(350).miss(side).lift("RS").touch("RS")   # a thumb on before, lifted after
                self.assertTrue(pad.lacks(modifier, cursor, cover))          # no orphan cursor

    @scenario("Temp cursor gyro TC10", rests=("A3",))
    def test_modifier_2_from_the_cursor_and_back(self):
        for start in STARTS:
            for side, other, modifier in SIDES:
                cursor, cover = names(side)
                for pad in self.each(start=start):
                    home = pad.stack
                    pad.hold(side).wait(350).hold(other).wait(300)
                    self.assertEqual(pad.top, "L1&R1: Tap Cover")
                    pad.let_go(other).wait(400)
                    self.assertEqual(pad.top, cover)                         # the held side survives, with no cursor
                    pad.let_go(side).wait(300)
                    self.assertEqual(pad.stack, home)                        # Gyro as it was

    @scenario("Temp cursor gyro TC11", rules=("R113",), rests=("A6",))
    def test_the_alternatives_modifier_2_entry_over_a_trigger_that_is_already_pulled(self):
        for first, second in (("L1", "R1"), ("R1", "L1")):
            for pad in self.each(variants=("alternative",)):
                pad.hold(first).hold(second).wait(60)
                self.assertIn("Modifier 2", pad.top)                         # without pulling again

    @scenario("Temp cursor gyro TC12", rules=("R120",))
    def test_a_fresh_hold_is_eligible_again_and_a_short_tap_still_double_taps(self):
        for side, _, _ in SIDES:
            cursor, _ = names(side)
            for pad in self.each():
                pad.hold(side).wait(350).let_go(side).wait(300).hold(side).wait(350)
                self.assertEqual(pad.top, cursor)
                pad.let_go(side).wait(300).tap(side).wait(30).hold(side)
                self.assertIn(pad.top, ("L1: Scroll Down", "R1: Scroll Up"))

    @scenario("Temp cursor gyro TC14", rules=("R122",))
    def test_nothing_flickers_while_the_cursor_or_the_cover_is_held(self):
        for side, _, _ in SIDES:
            for setup in (lambda p: p.wait(350), lambda p: p.wait(100).hold("A"),
                          lambda p: p.wait(100).touch("RS").lift("RS")):
                for pad in self.each():
                    setup(pad.hold(side))
                    pad.mark().wait(1500)                                    # several 350 ms reset intervals
                    self.assertEqual(pad.seen("add", "remove"), [])


if __name__ == "__main__":
    unittest.main()
