"""90.44 contracts: exact cleanup exclusions, explicit silence and inherited response."""
import copy
import functools
import importlib.util
import json
import unittest

from steam_layout.controllers import without_gyro_style
from steam_layout.model import Layout, actions, entries
from tests.scenario import ROOT, Pad, VARIANTS, frozen_layout_data, layout_data
from tests.test_steering_entry_feedback import GUARD, commands
from tools.convert_runtime_ids import generate_lookup, ids_to_titles


def by_title(data):
    """The layout with its layer commands written by title, so two builds compare whatever their layer order (90.64)."""
    data = json.loads(data) if isinstance(data, str) else data
    text, _ = ids_to_titles(json.dumps(data), generate_lookup(data))
    return json.loads(text)


@functools.lru_cache(maxsize=None)
def previous(variant):
    path = ROOT / 'findings/2026-10-09-steering-entry-and-feedback/build_candidate.py'
    spec = importlib.util.spec_from_file_location('quiet_drivers_previous', path)
    builder = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(builder)
    data, _ = builder.build(variant)
    return Layout(by_title(data))


def activators(layout, title):
    for source, group in layout.active(title).items():
        for name, slot in group.get('inputs', {}).items():
            for bank in ('activators', 'disabled_activators'):
                for index, (kind, entry) in enumerate(entries(slot.get(bank) or {})):
                    yield (source, name, bank, kind, index), entry


def without_haptic(entry):
    result = copy.deepcopy(entry)
    result.get('settings', {}).pop('haptic_intensity', None)
    if not result.get('settings'):
        result.pop('settings', None)
    return result


SCROLLS = ('Steering | LS Up: Scroll Up', 'Steering | LS Down: Scroll Down')     # the two stick scroll layers, since 90.52


def without_scroll_layers(layout, entry):
    """The entry without the removals of the two stick scroll layers, which the cover's removal lists have had since 90.52."""
    entry = copy.deepcopy(entry)
    binding = entry.get('bindings', {}).get('binding')
    if isinstance(binding, list):
        entry['bindings']['binding'] = [action for action in binding if not any(
            op == 'remove_layer' and target in SCROLLS for op, target in layout.layer_ops({'bindings': {'binding': action}}))]
    return entry


def without_right_pad(layout, entry):
    """(settings, commands) of an entry without its right pad removals. Since 90.53 the Steering modifier
    layers remove no right pad layer outside the clear to Base (author, 2026-10-10)."""
    kept = [action for action in actions(entry) if not any(
        op == 'remove_layer' and target.startswith('RTP:') for op, target in layout.layer_ops({'bindings': {'binding': action}}))]
    return entry.get('settings', {}), kept


def gyro_settings(layout, stack):
    """The same-mode property inheritance promised by the layout, not a sensor model."""
    settings, mode = {}, None
    for title in stack:
        group = layout.active(title).get('gyro')
        if group:
            if group['mode'] != mode:
                settings = {}
            mode = group['mode']
            settings.update(group.get('settings', {}))
    return mode, settings


class SteeringEntryQuietDrivers(unittest.TestCase):
    def each(self, frozen=None):
        """The working layout, or a release's stored build for a shape that later releases changed."""
        for variant in VARIANTS:
            data = frozen_layout_data(variant, frozen) if frozen else layout_data(variant)
            yield variant, Pad(variant, data=data), Layout(by_title(data)), previous(variant)

    def test_inverted_edge_is_one_quiet_any_driver_self_removal(self):
        for variant, _, layout, old in self.each():
            with self.subTest(variant=variant):
                group = layout.active(GUARD)['joystick']
                edge = group['inputs']['edge']['activators']
                self.assertEqual(list(edge), ['chord', 'release'])
                self.assertEqual(commands(layout, edge['chord']), [('remove_layer', GUARD, '0', '0')])
                self.assertEqual(edge['chord']['settings'], {
                    'gyro_ratchet_button_mask': '12' if variant == 'default' else '50331648',
                    'gyro_ratchet_button_requireany_or_all': '0',
                    'edge_binding_invert': '1', 'hold_repeats': '1',
                    'interruptable': '0', 'haptic_intensity': '0'})
                self.assertEqual(edge['release'], old.active(GUARD)['joystick']['inputs']['edge']['activators']['release'])
                self.assertEqual(group['settings'], old.active(GUARD)['joystick']['settings'])
                for direction in ('north', 'south', 'east', 'west'):
                    name = 'dpad_' + direction
                    self.assertEqual(group['inputs'][name], old.active(GUARD)['joystick']['inputs'][name])
                # The same layers and the two stick scroll layers of 90.52. Their places changed in 90.64.
                self.assertEqual(set(layout.titles.values()) - set(SCROLLS), set(old.titles.values()))
                self.assertEqual(len(layout.cm['action_layers']), 90)           # 88 until 90.52

    def test_mod2_releases_lose_only_the_requested_stateful_removals(self):
        # On the 90.56 build. In 90.57 a Steering Modifier 2 layer keeps one Release with one remove on its
        # second driver, and the Gyro Modifier 2 Releases lose seven removes (tests/test_scenarios_90_57.py).
        for variant, pad, layout, old in self.each(frozen='90.56'):
            changed = []
            for first, second in (('L1', 'R1'), ('R1', 'L1')):
                for family in ('', 'Gyro | ', 'Steering | '):
                    title = pad.title(f'{family}{first}!{second}: Modifier 2')
                    before = dict(activators(old, title))
                    after = dict(activators(layout, title))
                    if family == 'Steering | ':
                        # 90.53: the left edge's cleanup is one inverted chord (R133, A61); tests/test_scenarios_90_53.py
                        before = {k: v for k, v in before.items() if k[:2] != ('joystick', 'edge')}
                        after = {k: v for k, v in after.items() if k[:2] != ('joystick', 'edge')}
                    self.assertEqual(before.keys(), after.keys())
                    for location, actual in after.items():
                        expected = copy.deepcopy(before[location])
                        source, name, _, kind, _ = location
                        targeted = kind == 'release' and (
                            family == 'Gyro | ' and (source, name) in (pad.control(first), pad.control(second))
                            or family == 'Steering | ' and (source, name) == pad.control(second))
                        if targeted:
                            protected = {'Cursor Gyro'} | ({'Steering'} if family == 'Steering | ' else set())
                            old_commands = actions(expected)
                            expected['bindings']['binding'] = [action for action in old_commands
                                if not any(op == 'remove_layer' and target in protected
                                           for op, target in old.layer_ops({'bindings': {'binding': action}}))]
                            self.assertEqual(len(old_commands) - len(actions(expected)), len(protected))
                            changed.append((title, source, name))
                        # 90.48 also silences the ordinary/Gyro combined-cover
                        # add; the Steering Mod 2 bump remains intentional.
                        if family in ('', 'Gyro | ') and kind == 'chord' and expected.get('settings', {}).get('delay_start') == '200':
                            expected['settings']['haptic_intensity'] = '0'
                        if family == 'Steering | ':
                            self.assertEqual(without_right_pad(layout, without_scroll_layers(layout, actual)),
                                             without_right_pad(old, expected), (variant, title, location))
                        else:
                            self.assertEqual(without_scroll_layers(layout, actual), expected, (variant, title, location))
            self.assertEqual(len(changed), 6)
            self.assertEqual(len({title for title, _, _ in changed}), 4)

    def test_every_driver_owned_activator_is_off_in_the_working_layout(self):
        # What "quiet drivers" still requires. The bind-for-bind comparison with the 90.43 build is the next test.
        for variant, pad, layout, _ in self.each():
            for default_title in ('Steering | R1: W Key', 'Steering | L1: S Key'):
                title = pad.title(default_title)
                found = dict(activators(layout, title))
                self.assertTrue(found, (variant, title))
                for location, entry in found.items():
                    self.assertEqual(entry.get('settings', {}).get('haptic_intensity'), '0', (variant, title, location))
                repeats = [(entry['settings'].get('hold_repeats'), entry['settings'].get('repeat_rate'))
                           for location, entry in found.items() if location[3] == 'chord' and any(
                               op == 'add_layer' and target.endswith(': Modifier 2') for op, target in layout.layer_ops(entry))]
                self.assertEqual(repeats, [('1', '50')], (variant, title))
                self.assertEqual(layout.active(title)['joystick']['settings'].get('haptic_intensity_override'), '0', (variant, title))

    def test_all_driver_owned_activators_are_off_with_only_mod2_repeat_added(self):
        # On the stored 90.48 build: the W and S layers held exactly the 90.43 binds plus this repeat from 90.46
        # to 90.48. 90.49 to 90.55 reshaped them (the ring, then no cleanup function on up and down).
        for variant, pad, layout, old in self.each(frozen='90.48'):
            count = 0
            for default_title in ('Steering | R1: W Key', 'Steering | L1: S Key'):
                title = pad.title(default_title)
                current = dict(activators(layout, title))
                before = dict(activators(old, title))
                self.assertEqual(current.keys(), before.keys())
                for location, entry in current.items():
                    self.assertEqual(entry.get('settings', {}).get('haptic_intensity'), '0', (variant, title, location))
                    expected = without_haptic(before[location])
                    if location[3] == 'chord' and any(op == 'add_layer' and target.endswith(': Modifier 2')
                                                     for op, target in layout.layer_ops(entry)):
                        expected.setdefault('settings', {}).update(hold_repeats='1', repeat_rate='50')
                    self.assertEqual(without_scroll_layers(layout, without_haptic(entry)), expected, (variant, title, location))
                    if location[2] == 'activators':
                        count += 1
                for source, group in layout.active(title).items():
                    expected = copy.deepcopy(old.active(title)[source].get('settings', {}))
                    if source == 'joystick':
                        expected['haptic_intensity_override'] = '0'
                    self.assertEqual(group.get('settings', {}), expected)
            self.assertEqual(count, 50)

    def test_driver_handoffs_modifier_releases_and_delayed_completion_are_quiet(self):
        for variant, pad, layout, old in self.each():
            checks = []
            for owner in ('Steering', GUARD):
                for driver in ('L1', 'R1'):
                    source, name = pad.control(driver)
                    checks.append((owner, source, name, 'chord'))
            for direction, number, own in (('Down', 0, 'dpad_south'), ('Up', 1, 'dpad_north')):
                # Since 90.52 the modifier ends on its own direction's Release, which was the ring's until 90.51.
                modifier = f'Steering | LS {direction}: Modifier {number}'
                release = layout.active(modifier)['joystick']['inputs'][own]['activators']['release']
                self.assertEqual(release['settings'].get('haptic_intensity'), '0', (variant, modifier))
                self.assertEqual(without_haptic(release),
                                 without_haptic(old.active(modifier)['joystick']['inputs']['edge']['activators']['release']))
                self.assertNotIn('release', layout.active(modifier)['joystick']['inputs']['edge']['activators'])
                # Since 90.52 the window has two always-on entries: it closes at 150 ms and scrolls at 50 ms.
                always = layout.active(f'Steering | LS {direction}: Double Tap')['switch']['inputs']['always_on_action']
                for entry in always['activators']['Full_Press']:
                    self.assertEqual(entry['settings'].get('haptic_intensity'), '0', (variant, direction))
            for title, source, name, kind in checks:
                current = layout.active(title)[source]['inputs'][name]['activators'][kind]
                self.assertEqual(current.get('settings', {}).get('haptic_intensity'), '0', (variant, title))
                if title in ('Steering', GUARD):
                    expected_ops = [
                        ('add_layer', pad.title('Steering | R1: W Key' if (source, name) == pad.control('R1')
                                               else 'Steering | L1: S Key'))]
                    if title == GUARD:                  # since 90.68 the add runs first, then the guard goes (R137)
                        expected_ops.append(('remove_layer', GUARD))
                    self.assertEqual(layout.layer_ops(current), expected_ops)
                    expected_mask = ('4' if (source, name) == pad.control('R1') else '8') if variant == 'default' \
                        else ('16777217' if (source, name) == pad.control('R1') else '33554434')
                    self.assertEqual(current['settings'], {'hold_repeats': '1', 'repeat_rate': '50',
                        'haptic_intensity': '0', 'interruptable': '0', 'gyro_ratchet_button_mask': expected_mask,
                        'gyro_ratchet_button_requireany_or_all': '0'})
                else:
                    before = old.active(title)[source]['inputs'][name]['activators'][kind]
                    self.assertEqual(without_haptic(current), without_haptic(before), (variant, title))

    def test_cursor_response_and_deliberate_exits_are_unchanged_with_gyro_on_or_off(self):
        selectors = ('gyro_ratchet_button_mask', 'gyro_ratchet_button_requireany_or_all')
        response = {'gyro_precision_speed': '750', 'haptic_intensity': '0',
                    'flickstick_haptic_bump_per_angle': '1', 'mouse_move_threshold': '5'}
        for variant, _, layout, old in self.each():
            # The gyro style is each controller's own since 90.75 (R179); test_controllers checks it.
            self.assertEqual(without_gyro_style(layout.active('Cursor Gyro')), without_gyro_style(old.active('Cursor Gyro')))
            for stack, activation_owner in ((('Base', 'Gyro', 'Cursor Gyro'), 'Gyro'),
                                             (('Base', 'Cursor Gyro'), 'Base'),
                                             (('Base', 'Cursor Gyro', 'Gyro'), 'Gyro')):
                mode, merged = gyro_settings(layout, stack)
                self.assertEqual(mode, 'gyro_to_mouse')
                for key, value in response.items():
                    self.assertEqual(merged[key], value, (variant, stack, key))
                for key in selectors:
                    self.assertEqual(merged[key], layout.active(activation_owner)['gyro']['settings'][key])
            for title in ('Transition Set 1', 'Transition Set 2'):
                self.assertEqual(layout.active(title), old.active(title))

    def test_base_and_ramps_keep_reference_settings_except_requested_sensitivity(self):
        path = ROOT / 'findings/2026-07-11-layer-order-swap/MOST_RECENT_LAYOUT.post-fix.json'
        reference = Layout(json.loads(path.read_text()))
        titles = ('Base', 'Turning Ramp Up 0', 'Turning Ramp Up 1', 'Gyro Off Ramp Up')
        sensitivities = {'Base': '150', 'Turning Ramp Up 0': '200', 'Turning Ramp Up 1': '250'}
        for variant in VARIANTS:
            layout = Layout(layout_data(variant))
            for title in titles:
                settings = layout.active(title).get('right_joystick', {}).get('settings', {})
                expected = copy.deepcopy(reference.active(title).get('right_joystick', {}).get('settings', {}))
                if title in sensitivities:
                    expected['sensitivity'] = sensitivities[title]
                    if title != 'Base':
                        expected['sensitivity_vert_scale'] = str(15000 // int(sensitivities[title]))
                self.assertEqual(settings, expected, (variant, title))


if __name__ == '__main__':
    unittest.main()
