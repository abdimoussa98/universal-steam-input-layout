"""The 90.24 build: the required cleanups (R169 to R171), checked on the generated candidates.

Builds both variants with the 2026-10-04 builder and runs the fix pipeline, as the install does
(findings/2026-10-04-required-cleanups/README.md). These verify saved configuration contracts, not
Steam's runtime scheduling; the press sequences are in tests/scenarios/neptune/test_scenarios_90_24.py.
"""
import importlib.util
import json
from pathlib import Path
import unittest

from tools.audit_command_budget import audit_layout
from tools.convert_runtime_ids import generate_lookup, titles_to_ids
from steam_layout import changes, exceptions, required_cleanups as required
from steam_layout.cleanups import Cleanups
from steam_layout.fixes import apply_all
from steam_layout.model import Layout, always_on_layers, bindings, entries

ROOT = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location(
    'required_cleanups_builder', ROOT / 'findings/2026-10-04-required-cleanups/build_candidate.py')
rb = importlib.util.module_from_spec(spec); spec.loader.exec_module(rb)

BEFORE = '90.23'
BLOCK = 'controller_action empty_binding, , '
NEW_GROUPS = {'L1&R1: Tap Cover': 2, 'RTP: Tap Cover': 2, 'L1: Double Tap Cover': 2, 'R1: Double Tap Cover': 2,
              'Menu Left: Double Tap Cover': 2, 'Menu Right: Double Tap Cover': 2, 'Steering | LS: Tap Cover': 1,
              'Steering | LS: Double Tap Cover': 1, 'Steering | LS: Fallback Hold': 1}
UNTOUCHED = ('Base', 'Gyro', 'Steering', 'Cursor Gyro', 'Gamepad', 'Turning Ramp Up 0', 'Turning Ramp Up 1',
             'Gyro Off Ramp Up', 'LST: Entry Point', 'RST: Entry Point', 'LTP: Arrow Keys', 'RTP: Mouse Buttons',
             'L1: Tap Cover', 'R1: Tap Cover', 'L1: Double Tap', 'Menu Left: Double Tap')


class RequiredCleanupsBuildTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data, cls.layouts, cls.before, cls.paths = {}, {}, {}, {}
        for variant in ('default', 'alternative'):
            data = cls.data[variant] = rb.Builder(variant).finish()
            apply_all(data)
            cls.layouts[variant] = Layout(data)
            cls.paths[variant] = ROOT / f'versions/neptune/{BEFORE}/single-set-{variant}_hold-gyro_{BEFORE}.json'
            cls.before[variant] = json.loads(cls.paths[variant].read_text())

    def each(self):
        for variant, layout in self.layouts.items():
            with self.subTest(variant=variant):
                yield variant, layout

    def title(self, variant, title):
        return title if variant == 'default' else title.replace('L1', 'L2').replace('R1', 'R2')

    def acts(self, layout, layer, source, name):
        return layout.active(layer)[source]['inputs'][name]['activators']

    def test_the_90_24_snapshot_is_this_build(self):
        # The working layouts were this build until 90.25. The newest build's test holds R156.
        for variant, data in self.data.items():
            with self.subTest(variant=variant):
                numeric, _ = titles_to_ids(json.dumps(data), generate_lookup(data))
                built = json.loads(numeric)['controller_mappings']
                snapshot = json.loads((ROOT / f'versions/neptune/90.24/single-set-{variant}_hold-gyro_90.24.json').read_text())[
                    'controller_mappings']
                for cm in (built, snapshot):
                    cm.pop('title'); cm.pop('description')
                self.assertEqual(built, snapshot)

    def test_every_required_cleanup_is_there_within_three_entries(self):
        config = exceptions.load_config()
        for variant, layout in self.each():
            report = required.audit(Cleanups(layout), config)
            self.assertEqual((report['findings'], report['stale_decisions']), ([], []))
            self.assertEqual(audit_layout(self.data[variant])['violations'], [])

    def test_the_builder_gave_174_and_196_inputs_a_cleanup(self):
        manifest = json.loads((ROOT / 'findings/2026-10-04-required-cleanups/manifest.json').read_text())
        self.assertEqual({v: m['inputs_given_a_cleanup'] for v, m in manifest.items()},
                         {'default': 174, 'alternative': 196})

    def test_an_empty_binding_is_stored_in_full(self):
        # The first build wrote the guard chords as "controller_action empty_binding", without the two
        # empty fields every stored binding ends in.
        for variant, layout in self.each():
            for group in layout.groups.values():
                for name, value in group.get('inputs', {}).items():
                    for command in bindings(value.get('activators', {})):
                        self.assertNotEqual(command.strip(), BLOCK.split(',')[0], (group['id'], name))

    def test_fifteen_new_stick_groups_in_bases_mode_with_no_direction_bound(self):
        for variant, layout in self.each():
            before = Layout(self.before[variant])
            base = {source: layout.active('Base')[source]['mode'] for source in ('joystick', 'right_joystick')}
            found = {}
            for title in layout.presets:
                new = set(layout.active(title)) - set(before.active(title))
                for source in new:
                    group = layout.active(title)[source]
                    self.assertEqual(group['mode'], base[source], title)
                    self.assertLessEqual(set(group['inputs']), {'touch', 'edge'}, title)
                if new:
                    found[title] = len(new)
            self.assertEqual(found, {self.title(variant, t): n for t, n in NEW_GROUPS.items()})

    def test_a_full_pull_block_stays_and_has_a_cleanup(self):                        # decision 1
        for variant, layout in self.each():
            modifier = self.title(variant, 'Menu Left: Escape')
            for source in ('left_trigger', 'right_trigger'):
                acts = self.acts(layout, modifier, source, 'click')
                self.assertEqual(set(acts), {'Full_Press', 'chord'})
                self.assertEqual(acts['chord']['bindings']['binding'], BLOCK)

    def test_the_other_driver_adds_the_modifier_2_layer_from_the_guard_chord(self):   # decision 3
        for variant, layout in self.each():
            for own, other, driver in (('R1', 'L1', 'W Key'), ('L1', 'R1', 'S Key')):
                layer = self.title(variant, f'Steering | {own}: {driver}')
                control = {('default', 'L1'): ('switch', 'left_bumper'), ('default', 'R1'): ('switch', 'right_bumper'),
                           ('alternative', 'L1'): ('left_trigger', 'edge'), ('alternative', 'R1'): ('right_trigger', 'edge')}
                acts = self.acts(layout, layer, *control[(variant, other)])
                self.assertEqual([kind for kind, _ in entries(acts)].count('chord'), 1)
                self.assertEqual(set(acts), {'Full_Press', 'chord', 'release'})
                modifier = self.title(variant, f'Steering | {own}!{other}: Modifier 2')
                self.assertEqual(layout.layer_ops(acts['chord'])[-1], ('add_layer', modifier))
                self.assertEqual(acts['chord']['settings']['interruptable'], '0')
                cleanup = layout.layer_ops(acts['Full_Press'])
                self.assertTrue(all(op == 'remove_layer' for op, _ in cleanup))
                self.assertIn(('remove_layer', layer), cleanup)
                self.assertEqual(acts['Full_Press']['settings'], {'hold_repeats': '1'})

    def test_the_steering_stick_windows_type_tab_and_escape_themselves(self):
        for variant, layout in self.each():
            driver = self.title(variant, 'Steering | R1: W Key')
            for window in ('Steering | LS Up: Double Tap', 'Steering | LS Down: Double Tap'):
                self.assertIn(window, always_on_layers(layout))
                for name, key in (('button_escape', 'TAB'), ('button_menu', 'ESCAPE')):
                    acts = self.acts(layout, window, 'switch', name)
                    self.assertEqual(set(acts), {'Full_Press'})
                    self.assertIn(f'key_press {key}', acts['Full_Press']['bindings']['binding'])
                    self.assertEqual(layout.layer_ops(acts['Full_Press']), [])
                    self.assertTrue(layout.layer_ops(self.acts(layout, driver, 'switch', name)['Full_Press']))

    def test_the_entry_guard_and_the_fallback_hold_are_guarded_by_the_left_stick_being_out(self):
        for variant, layout in self.each():
            for layer in ('Steering | LS: Entry Guard', 'Steering | LS: Fallback Hold'):
                for source, name in (('joystick', 'touch'), ('right_joystick', 'touch'), ('right_joystick', 'edge'),
                                     ('switch', 'button_escape'), ('switch', 'button_menu')):
                    chord = self.acts(layout, layer, source, name)['chord']
                    self.assertEqual(chord['settings'], {'gyro_ratchet_button_mask': str(1 << 30),
                                                         'gyro_ratchet_button_requireany_or_all': '0', 'interruptable': '0'})

    def test_the_layers_the_rules_leave_out_and_the_ones_that_passed_did_not_change(self):
        for variant, layout in self.each():
            changed = changes.changed_since(self.data[variant], self.paths[variant])
            for title in UNTOUCHED:
                self.assertNotIn(self.title(variant, title), changed)
            self.assertEqual(len(layout.presets), len(Layout(self.before[variant]).presets))     # no layer was added


if __name__ == '__main__':
    unittest.main()
