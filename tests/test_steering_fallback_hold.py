"""Steering's Fallback Hold layer, checked on the generated candidates.

Builds both variants with the 2026-10-02 builder and runs the fix pipeline, as
the install does (findings/2026-10-02-steering-fallback-hold/README.md).
These verify saved configuration contracts, not Steam's runtime scheduling.
"""
import importlib.util
import json
from pathlib import Path
import re
import unittest

from tools.audit_command_budget import audit_layout
from steam_layout.fixes import apply_all
from steam_layout.model import EMPTY, Layout, bindings, entries

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    'fallback_hold', ROOT / 'findings/2026-10-02-steering-fallback-hold/build_candidate.py')
fh = importlib.util.module_from_spec(spec); spec.loader.exec_module(fh)

HOLD, GUARD = fh.HOLD, 'Steering | LS: Entry Guard'
LS_DEFLECT = str(1 << 30)
LEAVE = [('remove_layer', HOLD)]


class FallbackHoldTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.builders, cls.data, cls.layouts = {}, {}, {}
        for variant in ('default', 'alternative'):
            b = cls.builders[variant] = fh.Builder(variant)
            data = cls.data[variant] = b.finish()
            apply_all(data)
            cls.layouts[variant] = Layout(data)

    def each(self):
        for variant, layout in self.layouts.items():
            with self.subTest(variant=variant):
                yield self.builders[variant], layout

    def acts(self, layout, layer, source, name):
        return layout.active(layer)[source]['inputs'][name]['activators']

    def test_the_hold_is_appended(self):
        for b, layout in self.each():
            released = Layout(json.loads((ROOT / f'versions/neptune/90.10/single-set-{b.variant}_hold-gyro_90.10.json')
                                         .read_text()))
            before = [released.titles[k] for k in released.order]
            self.assertEqual([layout.titles[k] for k in layout.order], before + [HOLD])

    def test_steering_only_adds_the_hold(self):
        # No key and no timer in Steering itself: the timer can't run on A or D.
        for b, layout in self.each():
            stick = layout.active('Steering')['joystick']['inputs']
            for direction in fh.KEYS:
                acts = stick[direction]['activators']
                self.assertEqual(list(acts), ['Full_Press'], direction)
                self.assertEqual(acts['Full_Press']['settings'],
                                 {'hold_repeats': '1', 'repeat_rate': '50', 'interruptable': '0'})
                self.assertEqual(list(bindings(acts)), [f'controller_action add_layer {{{{Base::{HOLD}}}}} 0 0, , '])
            for direction, key in (('dpad_east', 'D'), ('dpad_west', 'A')):
                self.assertEqual(list(bindings(stick[direction]['activators'])), [f'key_press {key}, , '])

    def test_up_and_down_type_exit_and_release(self):
        for b, layout in self.each():
            for direction, key in fh.KEYS.items():
                acts = self.acts(layout, HOLD, 'joystick', direction)
                self.assertEqual(set(acts), {'Full_Press', 'chord', 'release'}, direction)
                self.assertEqual(acts['Full_Press'], {'bindings': {'binding': f'key_press {key}, , '},
                                                      'settings': {'interruptable': '0'}})
                leave = acts['chord']
                self.assertEqual(leave['settings'], {
                    'gyro_ratchet_button_mask': LS_DEFLECT, 'gyro_ratchet_button_requireany_or_all': '0',
                    'delay_start': '1500', 'haptic_intensity': '3', 'interruptable': '0'})
                ops = layout.layer_ops(leave)
                # The hold goes first and Steering last, with the flag meant as the beep: `1 0` in this builder,
                # `0 1` since 90.29 (A49).
                self.assertEqual(ops[0], ('remove_layer', HOLD))
                self.assertEqual(ops[-1], ('remove_layer', 'Steering'))
                self.assertIn('remove_layer {{Base::Steering}} 1 0', leave['bindings']['binding'][0])
                self.assertTrue(all(op == 'remove_layer' for op, _ in ops))
                # Leaving up or down ends the layer, and its timer with it.
                self.assertNotIn('settings', acts['release'])
                self.assertEqual(layout.layer_ops(acts['release']), LEAVE)

    def test_the_edge_pulses_at_once_and_carries_the_reset(self):
        for b, layout in self.each():
            acts = self.acts(layout, HOLD, 'joystick', 'edge')
            self.assertEqual(set(acts), {'chord', 'Full_Press', 'release'})
            pulse, reset = acts['chord'], acts['Full_Press']
            self.assertEqual(pulse['bindings']['binding'], EMPTY + ', , ')
            self.assertEqual(pulse['settings'], {
                'gyro_ratchet_button_mask': LS_DEFLECT, 'gyro_ratchet_button_requireany_or_all': '0',
                'delay_start': '5', 'hold_repeats': '1', 'repeat_rate': '250', 'haptic_intensity': '3',
                'interruptable': '0'})
            # The reset is longer than the exit delay, so a healthy exit lands first.
            self.assertEqual(reset['settings'], {'hold_repeats': '1', 'repeat_rate': '1550', 'interruptable': '0'})
            self.assertEqual(layout.layer_ops(reset), [('remove_layer', GUARD)])
            self.assertEqual(layout.layer_ops(acts['release']), LEAVE)
            self.assertEqual(layout.active(HOLD)['joystick']['settings']['edge_binding_invert'], '0')

    def test_the_hold_inherits_everything_else(self):
        for b, layout in self.each():
            active = layout.active(HOLD)
            self.assertEqual(sorted(active), ['joystick', 'switch'])
            self.assertEqual(set(active['switch']['inputs']), {'button_escape', 'button_menu'})
            self.assertEqual(set(active['joystick']['inputs']), {'dpad_north', 'dpad_south', 'edge'})
            steering = layout.active('Steering')['joystick']
            self.assertEqual(active['joystick']['mode'], steering['mode'])
            self.assertEqual(active['joystick']['settings'], steering['settings'])

    def test_no_menu_layer_lands_on_the_hold_or_the_entry_guard(self):
        # Start and Select type Tab and Escape, the same binds as the driver layers.
        for b, layout in self.each():
            driver = layout.active(b.title('W'))['switch']['inputs']
            for name in (HOLD, GUARD):
                switches = layout.active(name)['switch']['inputs']
                self.assertEqual(set(switches), {'button_escape', 'button_menu'}, name)
                for button in switches:
                    self.assertEqual(switches[button], driver[button], (name, button))
                    self.assertEqual(layout.layer_ops(switches[button]['activators']['Full_Press']), [])

    def test_steering_entry_points_type_w_and_s(self):
        # Pushing up with a menu button held types W; it doesn't add the hold over the menu layers.
        for b, layout in self.each():
            for side in fh.st.MENU:
                stick = layout.active(fh.st.entry_point(side, steering=True))['joystick']['inputs']
                for direction, key in fh.KEYS.items():
                    self.assertEqual(stick[direction]['activators'], {'Full_Press': {
                        'bindings': {'binding': f'key_press {key}, , '}, 'settings': {'interruptable': '0'}}})
                # The base Entry Points inherit Base's W and S.
                self.assertNotIn('dpad_north', layout.active(fh.st.entry_point(side))['joystick']['inputs'])
            # The guards and the menu Tap Cover inherit from the Entry Point under them.
            for name in [fh.st.guard(s) for s in fh.st.STICKS] + [fh.st.COVER]:
                self.assertFalse(set(fh.KEYS) & set(layout.active(name)['joystick']['inputs']), name)

    def test_no_turn_assist_in_steering(self):
        # Author, 2026-10-02: Steering blocks the right-stick edge, so no ramp layer (which binds
        # both bumpers) can land on a driver layer. Every Steering layer inherits the block or binds
        # its own edge without adding a ramp layer.
        ramps = {'Gyro Off Ramp Up', 'Turning Ramp Up 0', 'Turning Ramp Up 1'}
        for b, layout in self.each():
            edge = layout.active('Steering')['right_joystick']['inputs']['edge']['activators']
            self.assertEqual(list(edge), ['Full_Press'])
            self.assertEqual(list(bindings(edge)), [EMPTY + ', , '])
            for name in layout.presets:
                if name == 'Steering' or name.startswith('Steering | '):
                    stick = layout.active(name).get('right_joystick', {}).get('inputs', {})
                    if 'edge' in stick:
                        added = {t for _, e in entries(stick['edge']['activators'])
                                 for op, t in layout.layer_ops(e) if op == 'add_layer'}
                        self.assertFalse(added & ramps, name)

    def test_a_driver_press_retires_the_hold(self):
        for b, layout in self.each():
            for owner, side in (('W', 'right'), ('S', 'left')):
                acts = (self.acts(layout, 'Steering', 'switch', side + '_bumper') if b.variant == 'default'
                        else self.acts(layout, 'Steering', side + '_trigger', 'edge'))
                self.assertEqual(layout.layer_ops(acts['Full_Press']),
                                 LEAVE + [('remove_layer', GUARD), ('add_layer', b.title(owner))])
                self.assertEqual(layout.layer_ops(acts['chord']), [('remove_layer', GUARD)])

    def test_only_steering_the_clears_and_the_hold_name_the_hold(self):
        # The hold can't be on the stack with a driver layer, so their cleanup lists leave it out.
        for b, layout in self.each():
            named = set()
            for title in layout.presets:
                text = json.dumps([g.get('inputs', {}) for g in layout.active(title).values()])
                if HOLD in text or any(layout.resolve(ref) == HOLD
                                       for ref in re.findall(r'_layer (\d+) ', text)):
                    named.add(title)
            self.assertEqual(named - {HOLD, 'Steering'}, {
                'Menu Left: Entry Point', 'Menu Right: Entry Point', 'Steering | Menu Left: Entry Point',
                'Steering | Menu Right: Entry Point', b.title('Mod2', 'W'), b.title('Mod2', 'S')})

    def test_entry_budget(self):
        # The layer list itself is checked by test_the_hold_is_appended: 90.10's layers plus the hold.
        for b, layout in self.each():
            report = audit_layout(self.data[b.variant])
            self.assertEqual(report['violations'], [])


if __name__ == '__main__':
    unittest.main()
