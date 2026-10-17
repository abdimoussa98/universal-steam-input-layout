"""Scenarios for Ibex 1.2 (Neptune 90.78, DSE 1.2): the Entry Point stays under Fn.

The record is findings/2026-10-17-entry-point-stays-under-fn/README.md. On the Deck, 90.77: hold Start, push a stick
inside the 200 ms so the stick guard lands and eats the delay (A15), and the next time Start is held Fn comes on at
once. In 90.77 the bind that brought Fn in when the guard left also removed the Entry Point, the layer whose delay
the guard ate. The simulator doesn't model a delay going stale (A12, A13), so it shows the next hold waiting its
200 ms on 90.77 too; these check the shape 1.2 restores: the Entry Point stays under Fn until the menu button's
Release, and the next hold waits.
"""
import unittest

from tests.scenario import ScenarioCase, scenario

MENU = {"Menu Left": "Select", "Menu Right": "Start"}
GUARDS = {"LS": "Menu Buttons: Left Stick Guard", "RS": "Menu Buttons: Right Stick Guard"}


class EntryPointStaysUnderFn(ScenarioCase):
    @scenario("ibex 1.2 G1", rests=("A12", "A13", "A15", "A16"))
    def test_after_a_guard_eats_the_delay_the_entry_point_stays_and_the_next_hold_waits(self):
        for side, button in MENU.items():
            entry, fn = f"{side}: Entry Point", f"{side}: Fn Layer"
            for stick in ("LS", "RS"):
                for pad in self.each():
                    pad.hold(button).wait(100).push(stick, "up").wait(60)
                    self.assertEqual(pad.top, GUARDS[stick], (side, stick))
                    pad.recentre(stick).wait(50).lift(stick).wait(400)
                    self.assertEqual(pad.names()[-2:], (entry, fn), "the Entry Point stays under Fn")
                    pad.let_go(button).wait(400)
                    self.assertEqual(pad.names(), ("Base",), (side, stick))
                    pad.hold(button).wait(150)
                    self.assertEqual(pad.top, entry, "the next hold waits its 200 ms")
                    pad.wait(100)
                    self.assertEqual(pad.names()[-2:], (entry, fn), (side, stick))
                    pad.let_go(button).wait(400)


if __name__ == "__main__":
    unittest.main()
