"""Base menu self-chords: resting thumbs, re-exposure and lost releases.

These protect expected flows; they cannot establish that Regular Press caused
the author's missing Fn layer in Steam.
"""
import unittest
from tests.scenario import ScenarioCase, scenario

MENUS = (('Select', 'Menu Left'), ('Start', 'Menu Right'))


class BaseMenuChords(ScenarioCase):
    @scenario('90.37 M1', rules=('R133',), rests=('A27', 'A36', 'A16'))
    def test_menu_hold_with_a_thumb_already_resting(self):
        for button, menu in MENUS:
            for stick in ('LS', 'RS'):
                for start in (None, ('Base', 'Gyro')):
                    for pad in self.each(start=start):
                        pad.touch(stick).wait(400).hold(button).wait(199)
                        self.assertTrue(pad.has(menu + ': Entry Point'))
                        self.assertTrue(pad.lacks(menu + ': Fn Layer'))
                        pad.wait(1)
                        self.assertTrue(pad.has(menu + ': Fn Layer'))
                        pad.let_go(button).wait(300)
                        self.assertTrue(pad.lacks(menu + ': Entry Point', menu + ': Fn Layer'))

    @scenario('90.37 M2', rules=('R114',), rests=('A36', 'A16'), either=('A9',))
    def test_held_menu_button_reenters_when_a_stick_window_expires(self):
        for button, menu in MENUS:
            for stick in ('LS', 'RS'):
                for pad in self.each():
                    pad.touch(stick).wait(30).lift(stick).hold(button)
                    self.assertTrue(pad.lacks(menu + ': Entry Point'))
                    pad.wait(600)
                    self.assertTrue(pad.has(menu + ': Fn Layer'))
                    pad.let_go(button).wait(300)
                    self.assertEqual(pad.stack, pad.layers('Base'))

    @scenario('90.37 M3', rules=('R169', 'R133'), rests=('A25', 'A36', 'A27'))
    def test_a_missed_menu_release_clears_and_the_next_hold_works(self):
        for button, menu in MENUS:
            for pad in self.each():
                pad.hold(button).wait(50).miss(button).touch('RS').wait(100)
                self.assertTrue(pad.lacks(menu + ': Entry Point', menu + ': Fn Layer'))
                pad.hold(button).wait(250)
                self.assertTrue(pad.has(menu + ': Fn Layer'))


if __name__ == '__main__':
    unittest.main()
