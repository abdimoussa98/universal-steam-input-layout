"""90.39 candidate scenarios; explicit candidate data, separate from live coverage.

F1–F9/G1 and R1–R4 preserve the archived 90.31/90.32 gestures. Other
scenarios exercise later fixes against the restored fallback window."""
from tests.support.fixtures.scenarios_90_39 import *

class BackportedInteractions(ScenarioCase):
    @scenario('90.39 M1', rules=('R133',), rests=('A16', 'A27', 'A36'))
    def test_menu_holds_with_resting_thumbs_in_each_entry_context(self):
        for owner in ('Base', 'Gyro', 'Steering', 'Cursor Gyro'):
            for button, side in (('Select', 'Left'), ('Start', 'Right')):
                for stick in ('LS', 'RS'):
                    for pad in self.each(start=('Base', owner) if owner != 'Base' else None):
                        prefix = 'Stateful | ' if owner in ('Steering', 'Cursor Gyro') else ''
                        target = prefix + f'Menu {side}: Fn Layer'
                        pad.touch(stick).wait(400).hold(button).wait(199)
                        self.assertTrue(pad.lacks(target))
                        pad.wait(1)
                        self.assertTrue(pad.has(target))
                        pad.let_go(button).wait(400)
                        self.assertTrue(pad.lacks(target))

    @scenario('90.39 M2', rules=('R114',), rests=('A16', 'A25', 'A36'), either=('A9',))
    def test_held_menu_after_rtp_window_and_missed_release(self):
        for owner in ('Steering', 'Cursor Gyro'):
            for button, side in (('Select', 'Left'), ('Start', 'Right')):
                for pad in self.each(start=('Base', owner)):
                    target = f'Stateful | Menu {side}: Fn Layer'
                    pad.touch('RP').wait(30).lift('RP').hold(button).wait(600)
                    self.assertTrue(pad.has(target))
                    pad.miss(button).touch('RS').wait(150)
                    self.assertTrue(pad.lacks(target))
                    pad.hold(button).wait(300)
                    self.assertTrue(pad.has(target))

    @scenario('90.39 M3', rests=('A16', 'A36'))
    def test_opposite_menu_button_repeats_in_entry_and_fn_contexts(self):
        for first, second, key in (('Select', 'Start', 'RETURN'), ('Start', 'Select', 'BACKSPACE')):
            for owner in ('Base', 'Steering', 'Cursor Gyro'):
                for held in (50, 250):
                    for pad in self.each(start=None if owner == 'Base' else ('Base', owner)):
                        pad.hold(first).wait(held).mark()
                        for _ in range(2):
                            pad.tap(second).wait(400)
                        self.assertEqual(pad.typed().count(key), 2)

    @scenario('90.39 P1', rules=('R139',), rests=('A16',))
    def test_rtp_hold_and_scroll_work_in_ordinary_steering_and_entry_guard(self):
        for stack in (('Base', 'Steering'), ('Base', 'Steering', GUARD)):
            for pad in self.each(start=stack):
                pad.touch('RP').wait(170)
                self.assertTrue(pad.has('RTP: Entry Point', 'RTP: Tap Cover'))
                self.assertEqual(pad.seen('haptic'), [])
                pad.lift('RP').wait(250).touch('RP').wait(30).lift('RP')
                self.assertTrue(pad.has('RTP: Double Tap'))
                pad.sim.press(('right_trackpad', 'dpad_north'))
                self.assertTrue(pad.has('RTP: Circular Scroll'))

    @scenario('90.39 P2', rules=('R140', 'R148'), rests=('A16',), either=('A9',))
    def test_rtp_window_exits_before_a_held_direction_enters_fallback(self):
        for direction in ('up', 'down'):
            for pad in self.each(start='steering'):
                pad.touch('RP').wait(30).lift('RP').push('LS', direction).wait(100)
                self.assertTrue(pad.has('RTP: Double Tap') and pad.lacks(WINDOW, HOLD))
                pad.mark().wait(200)
                self.assertTrue(pad.has(WINDOW, HOLD))
                events = [(kind, target) for _, kind, target in pad.sim.log[pad._mark:] if kind in ('add', 'remove')]
                self.assertLess(events.index(('remove', 'RTP: Double Tap')), events.index(('add', WINDOW)))

    @scenario('90.39 P3', rules=('R140', 'R148'), rests=('A7', 'A8', 'A16'), either=('A9',))
    def test_rtp_before_and_during_fallback_keeps_the_timer_isolated(self):
        for before in (True, False):
            for pad in self.each(start='steering'):
                if before:
                    pad.touch('RP').wait(200)
                pad.push('LS', 'up').wait(400)
                if not before:
                    pad.touch('RP')
                pad.wait(599)
                self.assertTrue(pad.has(WINDOW))
                pad.wait(1)
                self.assertTrue(pad.has(HOLD) and pad.lacks(WINDOW))
                pad.wait(400)  # re-exposed repeating touch entry, then its 150 ms hold
                self.assertTrue(pad.has('RTP: Entry Point', 'RTP: Tap Cover'))
                pad.recentre('LS').lift('RP').wait(500)
                self.assertTrue(pad.lacks('Steering', HOLD, WINDOW, 'RTP: Entry Point'))

    @scenario('90.39 P4', rules=('R148',), rests=('A7', 'A8'), either=('A9',))
    def test_pad_release_inside_fallback_removes_window_before_other_helpers(self):
        for pad in self.each(start='steering'):
            pad.touch('RP').wait(200).push('LS', 'up').wait(400).mark().lift('RP')
            events = [(kind, target) for _, kind, target in pad.sim.log[pad._mark:] if kind in ('add', 'remove')]
            self.assertEqual(events[0], ('remove', WINDOW))
            self.assertIn(('remove', HOLD), events)
            pad.wait(60)
            self.assertTrue(pad.has('Steering', WINDOW))
            self.assertTrue(pad.lacks('RTP: Entry Point', 'RTP: Tap Cover'))

    @scenario('90.39 P5', rules=('R148',), rests=('A7', 'A8'), either=('A9',))
    def test_scroll_and_touch_helpers_clear_on_pad_release_in_each_steering_window(self):
        for route in ('fallback', 'up', 'down'):
            for scroll in (False, True):
                for pad in self.each(start='steering'):
                    if scroll:
                        pad.touch('RP').wait(30).lift('RP').touch('RP')
                        pad.sim.press(('right_trackpad', 'dpad_north'))
                        pad.wait(50)
                        self.assertTrue(pad.has('RTP: Circular Scroll'))
                    else:
                        pad.touch('RP').wait(170)
                    if route == 'fallback':
                        pad.push('LS', 'up').wait(50)
                        window = WINDOW
                    else:
                        pad.hold('R1').flick('LS', route).wait(30)
                        window = f'Steering | LS {route.title()}: Double Tap'
                    self.assertTrue(pad.has(window))
                    pad.mark().lift('RP')
                    events = [(kind, t) for _, kind, t in pad.sim.log[pad._mark:] if kind in ('add', 'remove')]
                    self.assertEqual(events[0], ('remove', window))
                    self.assertTrue(pad.lacks('RTP: Entry Point', 'RTP: Tap Cover', 'RTP: Circular Scroll'))

    @scenario('90.39 P6', rules=('R140',), rests=('A16',))
    def test_pad_clicks_during_the_window_cannot_change_its_timer(self):
        for where in ('centre', 'up'):
            for pad in self.each(start='steering'):
                pad.push('LS', 'up').wait(200).press_pad('RP', where).wait(100).let_go_pad('RP', lift=False)
                self.assertTrue(pad.has(WINDOW))
                self.assertTrue(pad.lacks('RTP: Click Entry Point', 'RTP: Mouse Buttons', 'RTP: Middle Click'))
                pad.wait(699)
                self.assertTrue(pad.has(WINDOW))
                pad.wait(1)
                self.assertTrue(pad.lacks(WINDOW))

    @scenario('90.39 D1', rules=('R123',), rests=('A13', 'A16'))
    def test_menu_and_directional_delays_apply_before_rtp_cleanup(self):
        for route in ('menu-left', 'menu-right', 'up', 'down', 'both-left', 'both-right'):
            for pad in self.each(start='steering'):
                pad.touch('RP').wait(170)
                if route.startswith('menu'):
                    side = 'Left' if route == 'menu-left' else 'Right'
                    pad.hold('Select' if side == 'Left' else 'Start')
                    target = f'Stateful | Menu {side}: Fn Layer'
                elif route.startswith('both'):
                    first, second = ('L1', 'R1') if route == 'both-left' else ('R1', 'L1')
                    pad.hold(first).wait(30).hold(second)
                    target = f'{second}: Tap Cover'
                else:
                    pad.hold('R1').push('LS', route)
                    target = 'Steering | LS: Tap Cover'
                pad.wait(199).mark().wait(1)
                self.assertTrue(pad.has(target))
                events = [(kind, t) for _, kind, t in pad.sim.log[pad._mark:] if kind in ('add', 'remove')]
                self.assertLess(events.index(('add', pad.title(target))), events.index(('remove', 'RTP: Entry Point')))

    @scenario('90.39 D2', rules=('R123',), rests=('A7', 'A13', 'A16'))
    def test_stick_touch_completions_preserve_target_before_rtp_cleanup(self):
        for stick in ('LS', 'RS'):
            for route in ('menu-left', 'menu-right', 'up', 'down', 'both-left', 'both-right'):
                for pad in self.each(start='steering'):
                    pad.touch(stick).touch('RP').wait(170)
                    if route.startswith('menu'):
                        side = 'Left' if route == 'menu-left' else 'Right'
                        pad.hold('Select' if side == 'Left' else 'Start')
                        target = f'Stateful | Menu {side}: Fn Layer'
                    elif route.startswith('both'):
                        first, second = ('L1', 'R1') if route == 'both-left' else ('R1', 'L1')
                        pad.hold(first).wait(30).hold(second)
                        target = f'{second}: Tap Cover'
                    else:
                        pad.hold('R1').push('LS', route)
                        target = 'Steering | LS: Tap Cover'
                    pad.wait(50).mark()
                    # Release only the capacitive touch: preserve the direction
                    # that conditions the pending directional completion.
                    pad.sim.release(pad.control(stick + ' touch'))
                    self.assertTrue(pad.has(target))
                    events = [(kind, t) for _, kind, t in pad.sim.log[pad._mark:] if kind in ('add', 'remove')]
                    self.assertLess(events.index(('add', pad.title(target))), events.index(('remove', 'RTP: Entry Point')))

    @scenario('90.39 C1', rules=('R159',), rests=('A16',))
    def test_gyro_two_driver_quick_clear_both_orders_and_release_orders(self):
        for first, second in (('L1', 'R1'), ('R1', 'L1')):
            for release in (first, second):
                for pad in self.each(start=('Base', 'Gyro')):
                    pad.hold(first).wait(30).hold(second).wait(30).let_go(release)
                    self.assertTrue(pad.lacks('Gyro', 'Steering', GUARD, HOLD, WINDOW))
                    pad.let_go(second if release == first else first).wait(500)
                    self.assertEqual(pad.stack, pad.layers('Base'))

    @scenario('90.39 C2', rules=('R159',), rests=('A16',))
    def test_menu_plus_stick_clear_preserves_gyro(self):
        for button in ('Start', 'Select'):
            for stick in ('LS', 'RS'):
                for pad in self.each(start=('Base', 'Gyro', 'Steering')):
                    pad.hold(button).click(stick).let_go(button).lift(stick).wait(500)
                    self.assertEqual(pad.stack, pad.layers('Base', 'Gyro'))

    @scenario('90.39 C3', rules=('R159',), rests=('A16',))
    def test_gyro_clear_removes_stale_steering_helpers(self):
        for first, second, owner in (('L1', 'R1', 'Gyro | L1!R1: Modifier 2'),
                                     ('R1', 'L1', 'Gyro | R1!L1: Modifier 2')):
            for pad in self.each(start=('Base', 'Gyro', 'Steering', GUARD, HOLD, owner)):
                pad.hold(first, second).wait(30).let_go(second).let_go(first).wait(500)
                self.assertEqual(pad.stack, pad.layers('Base'))

    @scenario('90.39 O1', rules=('R133',), rests=('A16', 'A25', 'A36'))
    def test_reordered_modifier_cursor_scroll_and_two_driver_inputs(self):
        for driver, cursor, scroll in (('L1', 'L1: Temp Cursor Gyro', 'L1: Scroll Down'),
                                       ('R1', 'R1: Temp Cursor Gyro', 'R1: Scroll Up')):
            for pad in self.each():
                pad.hold(driver).wait(200)
                self.assertTrue(pad.has(cursor))
                pad.tap('A').wait(50)
                self.assertTrue(pad.lacks(cursor))
                pad.miss(driver).touch('RS').wait(300)
                self.assertTrue(pad.lacks('L1: Modifier 0', 'R1: Modifier 1'))
                pad.lift('RS').wait(300).tap(driver).wait(30).hold(driver).wait(50)
                self.assertTrue(pad.has(scroll))
                pad.let_go(driver).wait(400)
        for first, second, owner in (('L1', 'R1', 'L1!R1: Modifier 2'), ('R1', 'L1', 'R1!L1: Modifier 2')):
            for pad in self.each():
                pad.hold(first).wait(30).hold(second).wait(100)
                self.assertTrue(pad.has(owner))
                pad.wait(150)
                self.assertTrue(pad.has('L1&R1: Tap Cover'))
                pad.let_go(second).let_go(first).wait(400)
                self.assertTrue(pad.lacks(owner, 'L1&R1: Tap Cover'))

    @scenario('90.39 E1', rests=('A16',))
    def test_turn_assist_is_cleared_on_steering_entry_and_stays_blocked(self):
        for stage in (0, 10, 400):
            for pad in self.each():
                pad.push('RS').wait(stage)
                pad.hold('Start').click('LS').let_go('Start').wait(100)
                self.assertTrue(pad.has('Steering'))
                self.assertTrue(pad.lacks('Gyro Off Ramp Up', 'Turning Ramp Up 0', 'Turning Ramp Up 1'))
                pad.hold('R1').wait(100)
                self.assertTrue(pad.has('Steering | R1: W Key'))
                self.assertTrue(pad.lacks('Gyro Off Ramp Up', 'Turning Ramp Up 0', 'Turning Ramp Up 1'))


class FallbackWindow(ScenarioCase):
    @scenario("90.39 F1", rules=("R137", "R161"), rests=("A8", "A10", "A11", "A16"))
    def test_holding_past_the_second_and_letting_go_leaves_steering(self):
        for direction, key, _ in BOTH:
            for pad in self.each(start="steering"):
                pad.mark().push("LS", direction)
                self.assertEqual((pad.names()[-2:], pad.down()), ((HOLD, WINDOW), [key]))   # the hold, the window on top
                pad.wait(999)
                self.assertEqual(pad.top, WINDOW)
                self.assertEqual(len(pad.seen("haptic")), 4)                # the pulse: at once, then every 250 ms
                pad.wait(2)
                self.assertEqual((pad.top, pad.down()), (HOLD, [key]))      # the window is gone and the key carries on (A11)
                pad.mark().wait(2000)
                self.assertTrue(pad.has("Steering", HOLD))                  # nothing leaves while the stick is held
                self.assertEqual((pad.seen("haptic", "beep"), pad.down()), ([], [key]))
                pad.mark().recentre("LS")
                self.assertTrue(left_steering(pad))
                self.assertEqual([what for what, _ in pad.seen("haptic", "beep")], ["haptic", "beep"])
                self.assertEqual(pad.seen("beep"), [("beep", "Steering")])

    @scenario("90.39 F2", rules=("R137",), rests=("A8", "A10"))
    def test_letting_go_inside_the_second_keeps_steering_every_time(self):
        for direction, key, control in BOTH:
            for pad in self.each(start="steering"):
                for held in (100, 500, 990):
                    pad.push("LS", direction).wait(held)
                    self.assertEqual((pad.top, pad.down()), (WINDOW, [key]))
                    pad.sim.release(control)                                 # up or down lets go before the edge does
                    self.assertEqual((pad.stack, pad.down()), (pad.layers("Base", "Steering"), []))
                    pad.recentre("LS").wait(300)
                    self.assertEqual(pad.stack, pad.layers("Base", "Steering"))

    @scenario("90.39 F3", rules=("R137",), rests=("A8", "A10", "A16"))
    def test_a_roll_to_the_side_ends_the_second_and_coming_back_starts_a_new_one(self):
        for pad in self.each(start="steering"):
            pad.push("LS", "up").wait(600).roll("LS", "left")
            self.assertEqual((pad.stack, pad.down()), (pad.layers("Base", "Steering"), ["A"]))
            pad.wait(2000)                                                   # no timer runs on A
            self.assertEqual(pad.stack, pad.layers("Base", "Steering"))
            pad.roll("LS", "up").wait(999)
            self.assertEqual(pad.top, WINDOW)                                # a full second again
            pad.wait(2).recentre("LS")
            self.assertTrue(left_steering(pad))

    @scenario("90.39 F4", rules=("R137",), rests=("A16",), either=("A9",))
    def test_a_driver_or_a_menu_button_leaves_steering_once_the_second_is_over(self):
        """In 90.31 the button also left Steering inside the second: the window removed itself and the Fallback
        Hold answered. Since 90.32 the window blocks it with a replacement (test_scenarios_90_32.py), so a button
        pressed inside the second leaves Steering only if it is still held when the second ends."""
        for button in ("R1", "L1", "Start", "Select"):
            for held in (400, 1500):
                for pad in self.each(start="steering"):
                    pad.push("LS", "up").wait(held)
                    self.assertEqual(pad.top, WINDOW if held < 1000 else HOLD)
                    pad.mark().hold(button).wait(60)                         # the Fallback Hold's bind repeats every 50 ms
                    if held < 1000:
                        self.assertTrue(pad.has("Steering", WINDOW), (button, held))
                        pad.wait(600)                                        # past the end of the second
                    self.assertTrue(left_steering(pad), (button, held))
                    self.assertEqual(pad.seen("beep"), [("beep", "Steering")])
                    pad.let_go(button).lift("LS").wait(600)
                    self.assertEqual(pad.stack, pad.layers("Base"))

    @scenario("90.39 F5", rules=("R137",), rests=("A7", "A16"), either=("A9",))
    def test_a_thumb_leaving_a_stick_starts_the_second_over(self):
        for pad in self.each(start="steering"):
            pad.touch("RS").wait(300).push("LS", "up").wait(600)
            pad.lift("RS").wait(60)                                          # the window's touch Release takes both layers
            self.assertEqual(pad.names()[-2:], (HOLD, WINDOW))               # and Steering's repeating add puts them back
            pad.wait(900)
            self.assertEqual(pad.top, WINDOW)                                # 600 ms in when the thumb lifted: still counting
            pad.wait(150)
            self.assertEqual(pad.top, HOLD)
            pad.recentre("LS")
            self.assertTrue(left_steering(pad))

    @scenario("90.39 F6", rules=("R133",), rests=("A16", "A36"))
    def test_thumbs_resting_on_both_sticks_do_nothing_as_the_window_closes(self):
        """At 1000 ms the Fallback Hold's cleanup binds start answering both stick touches. The chord on
        the left stick being out holds them back (A36); if it didn't, Steering would end here."""
        for pad in self.each(start="steering"):
            pad.touch("RS").wait(300).mark().push("LS", "up").wait(3000)
            self.assertEqual((pad.names()[-2:], pad.down()), (("Steering", HOLD), ["W"]))
            self.assertEqual(pad.seen("beep"), [])
            pad.push("RS").wait(500)                                         # the right stick pushed out as well: still held back
            self.assertTrue(pad.has("Steering", HOLD))

    @scenario("90.39 F7", rules=("R133",), rests=("A17", "A25"))
    def test_after_a_missed_release_a_fresh_stick_touch_leaves_steering(self):
        for stick in ("LS", "RS"):
            for pad in self.each(start="steering"):
                pad.push("LS", "up").wait(1500)
                pad.sim.lose(NORTH)                                          # the Steam menu was open: no Release was seen
                pad.recentre("LS").wait(500)
                self.assertEqual(pad.top, HOLD)                              # left on; the guard chord latched (A17)
                pad.lift("LS").wait(300).mark().touch(stick).wait(150)
                self.assertTrue(left_steering(pad))                          # the cleanup bind does what the Release would have
                self.assertEqual(pad.seen("beep"), [("beep", "Steering")])

    @scenario("90.39 F8", rules=("R137",), rests=("A25",))
    def test_a_release_missed_inside_the_second_leaves_steering_alone(self):
        for pad in self.each(start="steering"):
            pad.push("LS", "up").wait(400)
            pad.sim.lose(NORTH)
            pad.recentre("LS").wait(2000)                                    # the edge's Release still clears both
            self.assertEqual(pad.stack, pad.layers("Base", "Steering"))


    @scenario("90.39 F9", rests=("A7",))
    def test_after_leaving_by_the_stick_the_left_sticks_touch_gestures_work(self):
        for pad in self.each(start="steering"):
            pad.push("LS", "up").wait(1100).recentre("LS").wait(50)
            self.assertTrue(left_steering(pad))
            self.assertEqual(pad.top, "LST: Entry Point")                    # Base's touch add, on the thumb that is still down
            pad.lift("LS")
            self.assertEqual(pad.top, "LST: Double Tap")                     # lifted inside 150 ms: the stick's window
            pad.wait(50).touch("LS")
            self.assertTrue(pad.has("LST: Temporary Gyro"))                  # the double touch
            pad.lift("LS").wait(600)
            self.assertEqual(pad.stack, pad.layers("Base"))


class EntryGuard(ScenarioCase):
    @scenario("90.39 G1", rules=("R137",), rests=("A8", "A26"))
    def test_the_entry_guard_ends_when_the_direction_held_at_entry_lets_go(self):
        for direction, key, control in BOTH:
            for pad in self.each():
                pad.push("LS", direction).wait(300).hold("Start").wait(50)
                pad.sim.press(("joystick", "click"))
                pad.wait(30)
                pad.sim.release(("joystick", "click"))
                pad.let_go("Start").wait(50)
                self.assertEqual((pad.names()[-2:], pad.down()), (("Steering", GUARD), [key]))   # the stick was out at entry
                pad.wait(2000)
                self.assertTrue(pad.has("Steering", GUARD))                  # no second, no exit, while the guard is on
                pad.sim.release(control)                                     # the direction lets go; the edge is still out
                self.assertTrue(pad.lacks(GUARD) and pad.has("Steering"))
                pad.recentre("LS").wait(100).push("LS", direction)
                self.assertEqual(pad.names()[-2:], (HOLD, WINDOW))           # the next push starts the fallback's second


class Replacements(ScenarioCase):
    @scenario("90.39 R1", rules=("R137", "R140"), rests=("A16",))
    def test_a_tap_inside_the_second_sends_its_replacement_and_the_second_runs_on(self):
        for button, output in TAPS:
            for pad in self.each(start="steering"):
                pad.push("LS", "up").wait(400).mark().tap(button, 60)
                self.assertEqual(pad.typed(), [output])
                self.assertEqual((pad.top, pad.down()), (WINDOW, ["W"]))    # in 90.31 this left Steering
                pad.wait(539)
                self.assertEqual(pad.top, WINDOW)                            # 999 ms after the push: the tap restarted nothing
                pad.wait(2)
                self.assertEqual(pad.top, HOLD)
                pad.recentre("LS")
                self.assertTrue(pad.lacks("Steering"))

    @scenario("90.39 R2", rules=("R137",), rests=("A8",))
    def test_several_taps_and_then_letting_go_inside_the_second_keeps_steering(self):
        for pad in self.each(start="steering"):
            for _ in range(3):                                              # push, tap all four, let go: again and again
                pad.push("LS", "up").wait(100).mark()
                for button, _ in TAPS:
                    pad.tap(button, 40).wait(40)
                self.assertEqual(pad.typed(), [output for _, output in TAPS])
                pad.recentre("LS").wait(300)
                self.assertEqual(pad.stack, pad.layers("Base", "Steering"))

    @scenario("90.39 R3", rules=("R137",), rests=("A16",), either=("A9",))
    def test_a_button_held_from_inside_the_second_leaves_steering_when_it_ends(self):
        for button, _ in TAPS:
            for pad in self.each(start="steering"):
                pad.push("LS", "up").wait(400).hold(button).wait(599)
                self.assertTrue(pad.has("Steering", WINDOW))                 # blocked for as long as the window is on
                pad.mark().wait(60)                                          # the Fallback Hold's bind repeats every 50 ms
                self.assertTrue(pad.lacks("Steering", HOLD, WINDOW), button)
                self.assertEqual(pad.seen("beep"), [("beep", "Steering")])

    @scenario("90.39 R4", rules=("R137",), rests=("A16",))
    def test_after_the_second_a_driver_or_a_menu_button_leaves_steering_at_once(self):
        for button, output in TAPS:
            for pad in self.each(start="steering"):
                pad.push("LS", "up").wait(1500).mark().hold(button)
                self.assertTrue(pad.lacks("Steering", HOLD), button)
                self.assertNotIn(output, pad.typed())                        # no Tab, Escape or scroll there


if __name__ == "__main__":
    unittest.main()
