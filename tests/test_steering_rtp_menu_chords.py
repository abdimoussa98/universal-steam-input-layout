"""90.38 generated configuration, ordering, and narrow inverted-edge exception.

The contracts were last written against 90.42. 90.43 replaced `Steering | LS: Fallback Guard` with
`Steering | LS: Entry Guard`, and the tests below name the Entry Guard where the requirement still holds.
"""
import copy
import importlib.util
import json
from pathlib import Path
import unittest

from steam_layout import controllers
from steam_layout.model import Layout, entries
from tools.audit_command_budget import audit_layout

ROOT = Path(__file__).resolve().parents[1]
ENTRY_GUARD = 'Steering | LS: Entry Guard'
STATEFUL_MENU = ('Stateful | Menu Left: Entry Point', 'Stateful | Menu Right: Entry Point')
FN_STEERING_CLEAR = ROOT / 'findings/2026-10-09-fn-haptics-and-steering-clear'          # the 90.42 build


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    loaded = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loaded)
    return loaded


def release_builder(version, controller_type='controller_neptune'):
    """The builder of the findings folder whose stored build carries this version for this controller, newest folder
    first."""
    for folder in sorted(ROOT.glob('findings/*'), reverse=True):
        stored, script = folder / 'default-candidate.json', folder / 'build_candidate.py'
        if not (stored.exists() and script.exists()):
            continue
        mappings = json.loads(stored.read_text())['controller_mappings']
        if mappings['title'].endswith(f' :: {version}') and mappings.get('controller_type') == controller_type:
            return module(script, 'release_build')
    return None


build = module(ROOT / 'findings/2026-10-08-steering-rtp-and-menu-chords/build_candidate.py', 'steering_rtp_build')


class SteeringRtpMenu(unittest.TestCase):
    def each(self):
        for variant in ('default', 'alternative'):
            data = json.loads((ROOT / f'neptune/single-set-{variant}_hold-gyro_latest.json').read_text())
            yield variant, data, Layout(data)

    def test_working_layouts_are_generated_including_stored_order(self):
        # R156. The builder is found by the version in the working layout's title, so this follows each
        # release. Until 90.56 it named the 90.42 builder and failed from 90.43 on. Since the base layout (R177)
        # the built layouts are Ibex's; Neptune's are converted from Ibex after 90.74, which test_convert holds (C1).
        built = [(controller, path) for controller in (controllers.IBEX, controllers.NEPTUNE)
                 for path in controller.working()]
        self.assertTrue(any(controller is controllers.IBEX for controller, _ in built))
        for controller, path in built:
            working = json.loads(path.read_text())
            version = working['controller_mappings']['title'].rsplit(' :: ', 1)[-1]
            if not controller.base and controllers.version_key(version) > controllers.version_key(controller.built_until):
                continue
            with self.subTest(path.name):
                builder = release_builder(version, controller.controller_type)
                self.assertIsNotNone(builder, f'no findings folder holds a build_candidate.py and a stored build of {version}')
                generated = builder.build(controller.variant_of(path))[0]
                generated = json.loads(generated) if isinstance(generated, str) else generated
                for data in (working, generated):
                    for field in ('title', 'description'):
                        data['controller_mappings'].pop(field)
                self.assertEqual(json.dumps(working), json.dumps(generated))

    def test_the_90_42_build_is_reproducible_including_stored_order(self):
        # The frozen 90.42 scenarios run on this builder (tests/scenario.py), so it has to keep giving the stored build.
        old = module(FN_STEERING_CLEAR / 'build_candidate.py', 'fn_steering_clear_build')
        for variant in ('default', 'alternative'):
            generated, _ = old.build(variant)
            stored = json.loads((FN_STEERING_CLEAR / f'{variant}-candidate.json').read_text())
            for data in (generated, stored):                 # the release's install wrote these two, not the builder
                for field in ('title', 'description'):
                    data['controller_mappings'].pop(field)
            self.assertEqual(json.dumps(generated), json.dumps(stored))

    def test_menu_entry_conditions_repeat_and_do_not_repeat_key_output(self):
        for _, _, layout in self.each():
            # Not the Entry Guard: it binds both as a silent Start Press (90.43, tests/test_steering_entry_feedback.py).
            for title in ('Base', 'Steering', 'Cursor Gyro'):
                for button, mask in (('button_menu', '4096'), ('button_escape', '16384')):
                    acts = layout.active(title)['switch']['inputs'][button]['activators']
                    self.assertEqual(list(acts), ['chord'])
                    self.assertEqual(acts['chord']['settings'], {
                        'gyro_ratchet_button_mask': mask, 'hold_repeats': '1', 'interruptable': '0'})
            for side, button, selector in (('Left', 'button_escape', '15'), ('Right', 'button_menu', '14')):
                for title in (f'Menu {side}: Entry Point', f'Menu {side}: Fn Layer',
                              f'Stateful | Menu {side}: Entry Point'):
                    chord = layout.active(title)['switch']['inputs'][button]['activators']['chord']
                    expected = {'chord_button': selector, 'interruptable': '0', 'hold_repeats': '1'}
                    if title.endswith(': Entry Point'):
                        expected['haptic_intensity'] = '1'
                    self.assertEqual(chord['settings'], expected)
                key = layout.active(f'Stateful | Menu {side}: Fn Layer')['switch']['inputs'][button]['activators']['chord']
                self.assertNotEqual(key['settings'].get('hold_repeats'), '1')

    def test_steering_inherits_pad_and_direction_soft_presses_leave_steering(self):
        # Until 90.57 up and down removed the whole family, the Entry Guard included. Each of those layers binds
        # up and down itself, so this bind only runs with `Steering` bare; since 90.58 it removes `Steering` alone.
        for _, _, layout in self.each():
            self.assertNotIn('right_trackpad', layout.active('Steering'))      # the Entry Guard blocks both pads, by design
            for name in ('dpad_north', 'dpad_south'):
                acts = layout.active('Steering')['joystick']['inputs'][name]['activators']
                self.assertEqual(list(acts), ['Soft_Press'])
                entry = acts['Soft_Press']
                self.assertEqual(entry['settings'], {'hold_repeats': '1', 'repeat_rate': '50',
                    'interruptable': '0', 'haptic_intensity': '1', 'activation_threshold': '29031'})
                self.assertEqual(layout.layer_ops(entry), [('remove_layer', 'Steering')])
                self.assertIn(name, layout.active(ENTRY_GUARD)['joystick']['inputs'])

    def test_delayed_targets_complete_before_rtp_cleanup_including_touch_completion(self):
        for _, _, layout in self.each():
            found = []
            for title in layout.presets:
                if not title.startswith(('Steering |', 'Stateful |')):
                    continue
                for source, group in layout.active(title).items():
                    for name, value in group.get('inputs', {}).items():
                        for kind, entry in entries(value.get('activators', {})):
                            if not (int(entry.get('settings', {}).get('delay_start', '0'))
                                    or (kind == 'release' and name == 'touch')):
                                continue
                            ops = layout.layer_ops(entry)
                            removed = [target for op, target in ops if op == 'remove_layer' and target in build.RTP]
                            if not removed:
                                continue
                            added = [target for op, target in ops if op == 'add_layer']
                            if not added:
                                continue
                            if added == ['Steering']:
                                continue  # fallback's separate handback/cleanup, not a pending apply
                            self.assertEqual(ops[0][0], 'add_layer', (title, source, name, kind))
                            self.assertEqual(set(removed), set(build.RTP))
                            self.assertNotIn(('remove_layer', 'RTP: Double Tap'), ops)
                            found.append((title, source, name, kind))
            # Two delays and four thumb completions, in the two stateful menu entries. Until 90.48 the four
            # Steering modifier layers had three each (18); they remove no right pad layer any more (author,
            # 2026-10-10 and 2026-10-11; tests/test_scenarios_90_55.py).
            self.assertEqual(len(found), 6)
            self.assertEqual({title for title, _, _, _ in found}, set(STATEFUL_MENU))

    def test_inverted_edge_exception_rejects_changed_action_selector_repeat_or_owner(self):
        for _, data, layout in self.each():
            report = audit_layout(data)
            self.assertEqual(len(report['allowed_inverted']), 1)        # the Entry Guard's; 90.61 to 90.64 had ten left edges too
            self.assertFalse(report['inverted_edges'])
            for change in ('selector', 'repeat', 'target', 'owner'):
                mutant = copy.deepcopy(data)
                m = Layout(mutant)
                group = m.active(ENTRY_GUARD)['joystick']
                edge = group['inputs']['edge']['activators']['chord']
                if change == 'selector': edge['settings']['gyro_ratchet_button_mask'] = '4096'
                if change == 'repeat': edge['settings']['hold_repeats'] = '0'
                if change == 'target': edge['bindings']['binding'] = build.op('add', 'Gyro')
                if change == 'owner': m.presets['Steering']['group_source_bindings'][group['id']] = 'joystick active'
                self.assertTrue(audit_layout(mutant)['inverted_edges'], change)


if __name__ == '__main__':
    unittest.main()
