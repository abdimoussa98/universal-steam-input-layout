"""The fallback window, the outer ring radius and the Entry Guard's Releases, on the generated candidates (90.31).

Builds both variants with the 2026-10-04 fallback-window builder and runs the fix pipeline, as the
install does (findings/2026-10-04-fallback-window/README.md). These verify saved configuration
contracts, not Steam's runtime scheduling. The press sequences were in test_scenarios_90_31.py, retired with
90.33 (archived/fallback-window/).
"""
import copy
import importlib.util
import json
from pathlib import Path
import unittest

from tools.convert_runtime_ids import generate_lookup, titles_to_ids
from steam_layout import changes
from steam_layout.fixes import apply_all
from steam_layout.model import EMPTY, Layout, actions, always_on_layers, entries, map_title

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    'fallback_window', ROOT / 'findings/2026-10-04-fallback-window/build_candidate.py')
fw = importlib.util.module_from_spec(spec); spec.loader.exec_module(fw)

BEFORE = '90.30'
STICKS = ('joystick', 'right_joystick')
DRIVERS = {'default': (('switch', 'right_bumper'), ('switch', 'left_bumper')),
           'alternative': (('right_trigger', 'edge'), ('left_trigger', 'edge'))}
MENU = (('switch', 'button_menu'), ('switch', 'button_escape'))
KEYS = {'dpad_north': 'W', 'dpad_south': 'S'}
# What the editor can set (resources/Steam Input JSON Structure.md, "Limits the Steam editor sets").
MAX_MS = 1000
DPAD_RADIUS = (10000, 32000)


def snapshot(variant, version=BEFORE):
    path = ROOT / f'versions/neptune/{version}/single-set-{variant}_hold-gyro_{version}.json'
    return json.loads(path.read_text(encoding='utf-8'))


def keys(entry):
    return [a.split(',')[0] for a in actions(entry)]


class FallbackWindowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data, cls.layouts, cls.numeric = {}, {}, {}
        for variant in ('default', 'alternative'):
            data = cls.data[variant] = fw.Builder(variant).finish()
            apply_all(data)
            cls.layouts[variant] = Layout(data)
            numeric, _ = titles_to_ids(json.dumps(data), generate_lookup(data))
            cls.numeric[variant] = json.loads(numeric)

    def each(self):
        for variant, layout in self.layouts.items():
            with self.subTest(variant=variant):
                yield variant, layout

    def title(self, variant, title):
        return map_title(title, fw.RENAME) if variant == 'alternative' else title

    def acts(self, layout, title, source, name):
        return layout.active(title)[source]['inputs'][name]['activators']

    def test_the_90_31_snapshot_is_this_build(self):
        # The working layouts were this build until 90.32. The newest build's test holds R156.
        for variant in self.data:
            with self.subTest(variant=variant):
                built = copy.deepcopy(self.numeric[variant]['controller_mappings'])
                saved = json.loads((ROOT / f'versions/neptune/90.31/single-set-{variant}_hold-gyro_90.31.json').read_text())[
                    'controller_mappings']
                for cm in (built, saved):
                    cm.pop('title'); cm.pop('description')
                self.assertEqual(built, saved)

    def test_the_window_is_one_new_layer_at_the_end(self):
        for variant, layout in self.each():
            before = list(Layout(snapshot(variant)).presets)
            self.assertEqual(list(layout.presets), before + [fw.WINDOW])
            self.assertEqual(len(layout.presets), 91)                        # Base and 90 layers
            layers = list(self.numeric[variant]['controller_mappings']['action_layers'])
            self.assertEqual(layers, sorted(layers))                         # the list order is the Preset_ order (R104)
            self.assertIn(fw.WINDOW, always_on_layers(layout))

    def test_steerings_up_and_down_add_the_hold_and_then_the_window(self):
        for variant, layout in self.each():
            for direction in KEYS:
                acts = self.acts(layout, fw.STEERING, 'joystick', direction)
                self.assertEqual(list(acts), ['Full_Press'])
                self.assertEqual(layout.layer_ops(acts['Full_Press']), [('add_layer', fw.HOLD), ('add_layer', fw.WINDOW)])
                self.assertEqual(acts['Full_Press']['settings'], {'hold_repeats': '1', 'repeat_rate': '50', 'interruptable': '0'})
            adders = {title for title in layout.presets for group in layout.active(title).values()
                      for slot in group.get('inputs', {}).values() for _, e in entries(slot.get('activators', {}))
                      if ('add_layer', fw.WINDOW) in layout.layer_ops(e)}
            self.assertEqual(adders, {fw.STEERING})

    def test_the_window_counts_one_second_and_types_w_and_s_with_the_pulse(self):
        for variant, layout in self.each():
            timer = self.acts(layout, fw.WINDOW, 'switch', 'always_on_action')['Full_Press']
            self.assertEqual(timer['settings'], {'delay_start': '1000', 'interruptable': '0'})
            self.assertEqual(layout.layer_ops(timer), [('remove_layer', fw.WINDOW)])
            for direction, key in KEYS.items():
                acts = self.acts(layout, fw.WINDOW, 'joystick', direction)
                self.assertEqual(sorted(acts), ['Full_Press', 'chord', 'release'])
                self.assertEqual(keys(acts['Full_Press']), [f'key_press {key}'])
                pulse = acts['chord']
                self.assertEqual(keys(pulse), [EMPTY])
                self.assertEqual(pulse['settings'], {
                    'gyro_ratchet_button_mask': fw.LS_OUT, 'gyro_ratchet_button_requireany_or_all': '0',
                    'hold_repeats': '1', 'repeat_rate': '250', 'haptic_intensity': '3', 'interruptable': '0'})
            for direction, key in (('dpad_east', 'D'), ('dpad_west', 'A')):
                self.assertEqual(keys(self.acts(layout, fw.WINDOW, 'joystick', direction)['Full_Press']), [f'key_press {key}'])

    def test_leaving_the_window_by_hand_takes_the_hold_except_for_a_driver_or_a_menu_button(self):
        # The author, 2026-10-04: "if you ever exit the window manually, it'll clear the fallback"; a driver or a
        # menu button "will just remove the window and you'll go into the fallback and it'll clear you out".
        both = [('remove_layer', fw.WINDOW), ('remove_layer', fw.HOLD)]
        for variant, layout in self.each():
            window = layout.active(fw.WINDOW)
            for name in ('dpad_north', 'dpad_south', 'edge'):
                self.assertEqual(layout.layer_ops(window['joystick']['inputs'][name]['activators']['release']), both, name)
            self.assertEqual(list(window['joystick']['inputs']['edge']['activators']), ['release'])
            for source in STICKS + ('right_trackpad',):
                touch = window[source]['inputs']['touch']['activators']
                self.assertEqual(list(touch), ['release'], source)
                self.assertEqual(layout.layer_ops(touch['release'])[:2], both, source)
            for source, name in MENU + DRIVERS[variant]:
                acts = window[source]['inputs'][name]['activators']
                self.assertEqual(list(acts), ['Full_Press'], (source, name))
                self.assertEqual(layout.layer_ops(acts['Full_Press']), [('remove_layer', fw.WINDOW)], (source, name))
            # Nothing in the window adds a layer, and every removal list starts with the window (R146).
            for source, group in window.items():
                for name, slot in group.get('inputs', {}).items():
                    for _, e in entries(slot.get('activators', {})):
                        ops = layout.layer_ops(e)
                        self.assertFalse([op for op, _ in ops if op != 'remove_layer'], (source, name))
                        if ops:
                            self.assertEqual(ops[0], ('remove_layer', fw.WINDOW), (source, name))

    def test_the_hold_types_w_and_s_and_its_release_leaves_steering(self):
        for variant, layout in self.each():
            stick = layout.active(fw.HOLD)['joystick']['inputs']
            self.assertNotIn('edge', stick)                                  # the pulse and the reset are gone
            for direction, key in KEYS.items():
                acts = stick[direction]['activators']
                self.assertEqual(sorted(acts), ['Full_Press', 'release'])
                self.assertEqual(keys(acts['Full_Press']), [f'key_press {key}'])
                release = acts['release']
                self.assertEqual(release['settings'], {'haptic_intensity': '3'})         # R161: the pulse
                ops = layout.layer_ops(release)
                self.assertEqual((ops[0], ops[-1]), (('remove_layer', fw.HOLD), ('remove_layer', fw.STEERING)))
                self.assertRegex(actions(release)[0], r'remove_layer \S+ 0 1,')          # R161: Steering goes with the beep
            # No timer is left in the layer.
            for group in layout.active(fw.HOLD).values():
                for slot in group.get('inputs', {}).values():
                    for _, e in entries(slot.get('activators', {})):
                        self.assertNotIn('delay_start', e.get('settings') or {})

    def test_in_the_hold_a_driver_or_a_menu_button_leaves_steering_and_repeats(self):
        for variant, layout in self.each():
            hold = layout.active(fw.HOLD)
            for source, name in MENU + DRIVERS[variant]:
                acts = hold[source]['inputs'][name]['activators']
                self.assertEqual(list(acts), ['Full_Press'], (source, name))            # no chord: the stick out or not
                press = acts['Full_Press']
                self.assertEqual(press['settings'], {'hold_repeats': '1', 'repeat_rate': '50', 'interruptable': '0',
                                                     'haptic_intensity': '3'})
                ops = layout.layer_ops(press)
                self.assertEqual((ops[0], ops[-1]), (('remove_layer', fw.HOLD), ('remove_layer', fw.STEERING)))
                self.assertEqual({op for op, _ in ops}, {'remove_layer'})

    def test_the_holds_cleanup_binds_leave_steering_held_back_while_the_left_stick_is_out(self):
        # R131 says a cleanup function never removes a stateful layer. The register keeps this one (R132's entry).
        for variant, layout in self.each():
            hold = layout.active(fw.HOLD)
            for source, name in (('joystick', 'touch'), ('right_joystick', 'touch'), ('right_joystick', 'edge')):
                acts = hold[source]['inputs'][name]['activators']
                self.assertEqual(layout.layer_ops(acts['Full_Press']),
                                 [('remove_layer', fw.HOLD), ('remove_layer', fw.STEERING)], (source, name))
                self.assertEqual(acts['Full_Press']['settings'], {'hold_repeats': '1'})
                guard = acts['chord']
                self.assertEqual(keys(guard), [EMPTY])
                self.assertEqual(guard['settings']['gyro_ratchet_button_mask'], fw.LS_OUT)

    def test_no_stick_states_a_radius_the_editor_cannot_set(self):
        # The author, 2026-10-04: the D-pad's Outer Ring Command Radius goes from 10,000 to 32,000. 4915 and 7209
        # were below it, in 62 stick groups.
        for variant, layout in self.each():
            old, fixed = Layout(snapshot(variant)), 0
            for title in layout.presets:
                for source in STICKS:
                    group = layout.active(title).get(source)
                    if group is None:
                        continue
                    settings = group.get('settings') or {}
                    radius = settings.get('edge_binding_radius')
                    self.assertNotIn(radius, fw.BAD_RADII, (title, source))
                    if radius is not None and group['mode'] == 'dpad':
                        self.assertTrue(DPAD_RADIUS[0] <= int(radius) <= DPAD_RADIUS[1], (title, source, radius))
                    before = (old.active(title).get(source) or {}).get('settings') or {} if title in old.presets else {}
                    if before.get('edge_binding_radius') in fw.BAD_RADII:
                        fixed += 1
                        self.assertNotIn('edge_binding_radius', settings, (title, source))
                        self.assertEqual(settings.get('edge_binding_invert'), '0', (title, source))   # stated, not left to Steam
            self.assertEqual(fixed, 62)
            for source in STICKS:                                            # the new window states none either
                settings = layout.active(fw.WINDOW)[source].get('settings') or {}
                self.assertNotIn('edge_binding_radius', settings)

    def test_no_delay_or_repeat_rate_is_over_the_editors_1000_ms(self):
        for variant, layout in self.each():
            over = [(title, source, name, key, e['settings'][key])
                    for title in layout.presets for source, group in layout.active(title).items()
                    for name, slot in group.get('inputs', {}).items() for _, e in entries(slot.get('activators', {}))
                    for key in ('delay_start', 'delay_end', 'repeat_rate')
                    if key in (e.get('settings') or {}) and int(e['settings'][key]) > MAX_MS]
            self.assertEqual(over, [])

    def test_the_entry_guard_ends_on_any_directions_release(self):
        for variant, layout in self.each():
            stick = layout.active(fw.GUARD)['joystick']['inputs']
            for direction, key in (('dpad_north', 'W'), ('dpad_south', 'S'), ('dpad_east', 'D'), ('dpad_west', 'A')):
                acts = stick[direction]['activators']
                self.assertEqual(sorted(acts), ['Full_Press', 'release'])
                self.assertEqual(keys(acts['Full_Press']), [f'key_press {key}'])
                self.assertEqual(layout.layer_ops(acts['release']), [('remove_layer', fw.GUARD)])
            self.assertEqual(layout.layer_ops(stick['edge']['activators']['release']), [('remove_layer', fw.GUARD)])   # kept

    def test_against_90_30_the_change_is_the_fallback_the_radius_the_guard_and_the_clear_lists(self):
        for variant in self.data:
            with self.subTest(variant=variant):
                old = Layout(snapshot(variant))
                report = changes.diff(snapshot(variant), self.numeric[variant])
                self.assertEqual((report['added'], report['removed']), ([fw.WINDOW], []))
                radius = {title for title in old.presets for source in STICKS
                          if ((old.active(title).get(source) or {}).get('settings') or {}).get('edge_binding_radius') in fw.BAD_RADII}
                up, down = self.title(variant, fw.TEMPLATE), self.title(variant, 'Steering | LS Down: Double Tap')
                clears = {title for title in old.presets for group in old.active(title).values()
                          for slot in group.get('inputs', {}).values() for _, e in entries(slot.get('activators', {}))
                          if {('remove_layer', up), ('remove_layer', down)} <= set(old.layer_ops(e))}
                expected = radius | clears | {fw.STEERING, fw.HOLD, fw.GUARD, fw.WINDOW}
                self.assertEqual(changes.changed_layers(report), expected)


if __name__ == '__main__':
    unittest.main()
