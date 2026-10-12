"""90.39 candidate contracts; live 90.38 and frozen 90.32 remain independent."""
import copy
import importlib.util
import json
from pathlib import Path
import unittest

from steam_layout import changes
from steam_layout.model import Layout, actions, entries
from tools.audit_command_budget import audit_layout
from tests.test_scenarios_90_39 import candidate, HERE

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('fallback_backport', HERE / 'build_candidate.py')
build = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build)


class FallbackBackport(unittest.TestCase):
    def each(self):
        for variant in build.VARIANTS:
            data = candidate(variant)
            yield variant, data, Layout(data)

    def test_candidates_are_reproducible_including_stored_order(self):
        for variant, data, _ in self.each():
            _, numeric, rules, _ = build.build(variant)
            self.assertEqual(json.dumps(numeric), json.dumps(data))
            # The builder starts from the live exceptions register, which has grown since 90.39, and adds three
            # entries of its own. Only those three are the candidate's.
            stored = json.loads((HERE / 'candidate-rules.json').read_text())
            live = json.loads(build.exceptions.REGISTER.read_text())
            self.assertEqual(rules['exceptions'][:-3], live['exceptions'])
            self.assertEqual(rules['exceptions'][-3:], stored['exceptions'][-3:])

    def test_original_fallback_timing_entry_threshold_and_menu_overrides_survive(self):
        for variant, data, layout in self.each():
            build.preflight(data)
            old = Layout(json.loads(build.snapshot(variant).read_text()))
            self.assertEqual(list(layout.presets), list(old.presets))
            self.assertNotIn('Steering | LS: Fallback Guard', layout.presets)
            for title in ('Steering', build.GUARD, build.HOLD, build.WINDOW):
                self.assertEqual(layout.active(title)['joystick']['settings'], old.active(title)['joystick']['settings'])
            for name in ('dpad_north', 'dpad_south'):
                acts = layout.active('Steering')['joystick']['inputs'][name]['activators']
                self.assertEqual(list(acts), ['Full_Press'])
                self.assertNotIn('activation_threshold', acts['Full_Press']['settings'])
                self.assertEqual(layout.layer_ops(acts['Full_Press']), [('add_layer', build.HOLD), ('add_layer', build.WINDOW)])
            for owner in (build.GUARD, build.HOLD, build.WINDOW):
                for source, group in layout.active(owner).items():
                    for name, slot in group.get('inputs', {}).items():
                        if name in ('button_menu', 'button_escape', 'left_bumper', 'right_bumper') or source.endswith('_trigger'):
                            # All these keys/scrolls/guarded exits are deliberately
                            # NOT converted to the new self-chord entry pattern.
                            a = old.active(owner)[source]['inputs'][name]
                            self.assertEqual(changes.describe(old, a, {})[0], changes.describe(layout, slot, {})[0])
            timer = layout.active(build.WINDOW)['switch']['inputs']['always_on_action']['activators']['Full_Press']
            self.assertEqual(timer['settings']['delay_start'], '1000')
            self.assertEqual(layout.layer_ops(timer), [('remove_layer', build.WINDOW)])

    def test_cleanup_order_and_command_budget(self):
        for _, data, layout in self.each():
            report = audit_layout(data)
            self.assertFalse(report['violations'])
            for owner, source, name in build.ordering.cleanup_inputs(layout):
                acts = layout.active(owner)[source]['inputs'][name]['activators']
                self.assertEqual(list(acts), [kind for kind in build.ordering.ORDER if kind in acts])
                for kind, entry in entries(acts):
                    if kind == 'Full_Press':
                        self.assertNotEqual(entry.get('settings', {}).get('interruptable'), '0')

    def test_menu_conditions_and_six_delays_complete_before_rtp_cleanup(self):
        for variant, _, layout in self.each():
            for owner in ('Base', 'Steering', 'Cursor Gyro'):
                for button, mask in (('button_menu', '4096'), ('button_escape', '16384')):
                    acts = layout.active(owner)['switch']['inputs'][button]['activators']
                    self.assertEqual(list(acts), ['chord'])
                    self.assertEqual(acts['chord']['settings'], {
                        'gyro_ratchet_button_mask': mask, 'hold_repeats': '1', 'interruptable': '0'})
            for side, button, selector in (('Left', 'button_escape', '15'), ('Right', 'button_menu', '14')):
                for owner in (f'Menu {side}: Entry Point', f'Menu {side}: Fn Layer', f'Stateful | Menu {side}: Entry Point'):
                    settings = layout.active(owner)['switch']['inputs'][button]['activators']['chord']['settings']
                    self.assertEqual(settings, {'chord_button': selector, 'hold_repeats': '1', 'interruptable': '0'})
            log = json.loads((HERE / f'{variant}-fixes.json').read_text())
            self.assertEqual(len(log['rtp_completions']), 18)
            for owner, source, name, kind in log['rtp_completions']:
                e = layout.active(owner)[source]['inputs'][name]['activators'][kind]
                ops = layout.layer_ops(e)
                self.assertEqual(ops[0][0], 'add_layer')
                self.assertEqual({t for k, t in ops if k == 'remove_layer' and t in build.RTP}, set(build.RTP))
                self.assertNotIn(('remove_layer', 'RTP: Double Tap'), ops)

    def test_new_pad_routes_preserve_window_first_exits(self):
        for _, _, layout in self.each():
            self.assertNotIn('right_trackpad', layout.active('Steering'))
            for owner in (build.WINDOW, 'Steering | LS Up: Double Tap', 'Steering | LS Down: Double Tap'):
                acts = layout.active(owner)['right_trackpad']['inputs']['touch']['activators']
                self.assertEqual(list(acts), ['release'])
                ops = layout.layer_ops(acts['release'])
                self.assertEqual(ops[0], ('remove_layer', owner))
                self.assertIn(('remove_layer', 'RTP: Entry Point'), ops)
            for name in ('dpad_north', 'dpad_south', 'dpad_east', 'dpad_west'):
                acts = layout.active('RTP: Double Tap')['joystick']['inputs'][name]['activators']
                self.assertEqual(actions(acts['Full_Press']), ['controller_action empty_binding, , '])

    def test_gyro_full_clear_targets_retained_family_and_leaves_windows_first(self):
        for variant, _, layout in self.each():
            windows = {build.WINDOW, 'Steering | LS Up: Double Tap', 'Steering | LS Down: Double Tap'}
            wanted = {'Steering'} | {t for t in layout.presets if t.startswith('Steering |')}
            for owner in ('Gyro | L1!R1: Modifier 2', 'Gyro | R1!L1: Modifier 2'):
                releases = [e for g in layout.active(build.title(variant, owner)).values()
                            for slot in g.get('inputs', {}).values() for kind, e in entries(slot.get('activators', {}))
                            if kind == 'release' and ('remove_layer', 'Gyro') in layout.layer_ops(e)]
                self.assertEqual(len(releases), 2)
                for e in releases:
                    ops = layout.layer_ops(e)
                    self.assertEqual({t for _, t in ops[:3]}, windows)
                    self.assertTrue(wanted <= {t for k, t in ops if k == 'remove_layer'})

    def test_live_snapshot_lineage_is_separate_from_testing_candidate(self):
        for variant, _, _ in self.each():
            working = ROOT / f'neptune/single-set-{variant}_hold-gyro_latest.json'
            current = json.loads(working.read_text())
            latest = changes.newest_snapshot(working.name)
            self.assertEqual(json.loads(latest.read_text()), current)
            self.assertNotEqual(current['controller_mappings']['title'], candidate(variant)['controller_mappings']['title'])


if __name__ == '__main__':
    unittest.main()
