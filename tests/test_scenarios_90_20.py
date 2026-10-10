"""Scenarios for 90.20: Base adds the Click Entry Point with one Soft Press per pad click.

The record is findings/2026-10-03-base-pad-click-one-add/README.md. From 90.16 to 90.19 Base had
a second, repeating add beside it.
"""
import unittest

from tests.scenario import ScenarioCase, scenario

ENTRY = {"LP": "LTP: Click Entry Point", "RP": "RTP: Click Entry Point"}


class OneAdd(ScenarioCase):
    @scenario("90.20 B1", rules=("R113",), rests=("A6", "A10"), either=("A9", "A42"))
    def test_a_held_click_adds_the_entry_point_once_and_bumps_once(self):
        for name, where in (("RP", "centre"), ("RP", "left"), ("LP", "centre"), ("LP", "up")):
            for pad in self.each():
                pad.press_pad(name, where).wait(2000)
                adds = [title for _, title in pad.seen("add") if title == pad.title(ENTRY[name])]
                self.assertEqual(len(adds), 1)                                    # nothing puts it back while held
                clicks = [detail for _, detail in pad.seen("haptic") if detail.startswith("1 ")]
                self.assertEqual(len(clicks), 1)                                  # the press; on the Entry Point since 90.25
                self.assertEqual(len(pad.down()), 1)
                pad.let_go_pad(name).wait(400)
                self.assertEqual((pad.stack, len(pad.typed())), (pad.layers("Base"), 1))

    @scenario("90.20 B2", rules=("R113",), rests=("A6", "A10"))
    def test_each_new_click_adds_it_again(self):
        for pad in self.each():
            for _ in range(3):
                pad.click_pad("RP", "left", ms=120).wait(400)
            self.assertEqual((pad.stack, pad.typed()), (pad.layers("Base"), ["mouse_button BACK"] * 3))


if __name__ == "__main__":
    unittest.main()
