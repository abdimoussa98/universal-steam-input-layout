"""90.38: menu entry chords, RTP in Steering, and near-rim fallback entry.

Extends the frozen 90.37 builder in title form. --install writes working JSON;
audits, exporter and version snapshot follow separately.
"""
import argparse
import copy
import importlib.util
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
from steam_layout.fixes import apply_all
from steam_layout.model import Layout, actions, entries
from tools.convert_runtime_ids import generate_lookup, ids_to_titles, titles_to_ids

spec = importlib.util.spec_from_file_location(
    'steering_rtp_previous', ROOT / 'findings/2026-10-06-menu-base-chords/build_candidate.py')
previous = importlib.util.module_from_spec(spec)
spec.loader.exec_module(previous)
GUARD = 'Steering | LS: Fallback Guard'
MENU_OWNERS = ('Steering', GUARD, 'Cursor Gyro')
RTP = ('RTP: Entry Point', 'RTP: Tap Cover', 'RTP: Circular Scroll',
       'RTP: Click Entry Point', 'RTP: Mouse Buttons', 'RTP: Middle Click')


def op(kind, title):
    return f'controller_action {kind}_layer {{{{Base::{title}}}}} 0 0, , '


class Front:
    def finish(self):
        data = super().finish()
        layout = Layout(data)
        for title in MENU_OWNERS:
            inputs = layout.active(title)['switch']['inputs']
            for button, mask in (('button_menu', '4096'), ('button_escape', '16384')):
                old = inputs[button]['activators']
                assert list(old) == ['Full_Press'], (title, button, old)
                entry = old['Full_Press']
                entry['settings'] = {'gyro_ratchet_button_mask': mask, 'hold_repeats': '1', 'interruptable': '0'}
                inputs[button]['activators'] = {'chord': entry}

        for side, button in (('Left', 'button_escape'), ('Right', 'button_menu')):
            for title in (f'Menu {side}: Entry Point', f'Menu {side}: Fn Layer',
                          f'Stateful | Menu {side}: Entry Point'):
                chord = layout.active(title)['switch']['inputs'][button]['activators']['chord']
                assert not chord.get('settings', {}).get('delay_start')
                assert all(a.startswith('controller_action ') for a in actions(chord))
                chord['settings'].update(hold_repeats='1', interruptable='0')

        for title in ('Steering', GUARD):
            group = layout.active(title)['right_trackpad']
            assert list(group['inputs']) == ['touch']
            assert actions(group['inputs']['touch']['activators']['Full_Press']) == ['controller_action empty_binding, , ']
            # Remove the redundant active source; dead_groups prunes its unused group.
            del layout.presets[title]['group_source_bindings'][group['id']]

        stick = layout.active('Steering')['joystick']['inputs']
        for name in ('dpad_north', 'dpad_south'):
            old = stick[name]['activators']
            assert list(old) == ['Full_Press']
            entry = old['Full_Press']
            entry['settings']['activation_threshold'] = '29031'
            stick[name]['activators'] = {'Soft_Press': entry}

        guard = layout.active(GUARD)['joystick']['inputs']
        assert 'edge' not in guard
        guard['edge'] = {'activators': {'chord': {
            'bindings': {'binding': op('add', 'Steering')},
            'settings': {'gyro_ratchet_button_mask': '12' if self.variant == 'default' else '50331648',
                         'gyro_ratchet_button_requireany_or_all': '0', 'edge_binding_invert': '1',
                         'hold_repeats': '1', 'interruptable': '0', 'haptic_intensity': '0'}}},
                         'disabled_activators': {}}

        # Complete first, then clean the non-window RTP helpers. The Window fix
        # isolates any Always On RTP window instead of removing it after an add.
        self.rtp_completions = []
        for title in layout.presets:
            if not (title.startswith('Steering |') or title.startswith('Stateful |')):
                continue
            groups = layout.active(title)
            delayed = set()
            for group in groups.values():
                for value in group.get('inputs', {}).values():
                    for _, entry in entries(value.get('activators', {})):
                        if int(entry.get('settings', {}).get('delay_start', '0')):
                            delayed.update(t for kind, t in layout.layer_ops(entry) if kind == 'add_layer')
            if not delayed:
                continue
            for source, group in groups.items():
                for name, value in group.get('inputs', {}).items():
                    for kind, entry in entries(value.get('activators', {})):
                        completes = int(entry.get('settings', {}).get('delay_start', '0')) > 0 or (kind == 'release' and name == 'touch')
                        if completes and any(op == 'add_layer' and target in delayed for op, target in layout.layer_ops(entry)):
                            commands = actions(entry)
                            entry['bindings']['binding'] = [op('remove', t) for t in reversed(RTP)] + commands
                            self.rtp_completions.append((title, source, name, kind))
        return data


def Builder(variant):
    return type('Concrete', (Front, type(previous.Builder(variant))), {})(variant)


def build(variant):
    builder = Builder(variant)
    data = builder.finish()
    report = apply_all(data)
    readable = json.dumps(data, indent='\t') + '\n'
    numeric, _ = titles_to_ids(readable, generate_lookup(data))
    assert '{{' not in numeric
    restored, _ = ids_to_titles(numeric, generate_lookup(data))
    assert json.loads(restored) == data
    return json.loads(numeric), report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--install', action='store_true')
    args = parser.parse_args()
    for variant in ('default', 'alternative'):
        data, report = build(variant)
        working = ROOT / f'neptune/single-set-{variant}_hold-gyro_latest.json'
        current = json.loads(working.read_text())['controller_mappings']
        cm = data['controller_mappings']
        cm['title'] = current['title'].rsplit(' :: ', 1)[0] + ' :: 90.38'
        description = current['description']
        description = description.replace('Pushing it up or down with no driving button held brings in walking at once,',
                                          'Pushing it up or down nearly to the rim with no driving button held brings in walking,')
        for driver in ('bumper', 'trigger'):
            description = description.replace(
                'While steering, right-pad touch modes such as circular scroll are off, so the pad is just the mouse, '
                f'and while a driving {driver} is held right-stick turn assist is off,',
                'Right-pad gestures, including circular scroll, work in Steering; timed double-tap windows '
                f'temporarily restrict layer-changing inputs. While a driving {driver} is held right-stick turn assist is off,')
        cm['description'] = description
        target = working if args.install else HERE / f'{variant}-candidate.json'
        target.write_text(json.dumps(data, indent='\t') + '\n')
        (HERE / f'{variant}-fixes.json').write_text(json.dumps(report, indent=2) + '\n')
        print(target.relative_to(ROOT), flush=True)


if __name__ == '__main__':
    main()
