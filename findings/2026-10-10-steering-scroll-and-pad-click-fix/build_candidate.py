"""Build 90.49 steering scroll and pad click correction from the live 90.48 files."""

import argparse
import copy
import json
from pathlib import Path

from steam_layout.fixes import apply_all
from steam_layout.model import Layout, actions, entries
from tools.convert_runtime_ids import generate_lookup, ids_to_titles, titles_to_ids


ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
SCROLL = {
    'Steering | R1: W Key', 'Steering | L1: S Key',
    'Steering | R2: W Key', 'Steering | L2: S Key',
    'Steering | LS Up: Modifier 1', 'Steering | LS Down: Modifier 0',
    'Steering | LS: Tap Cover', 'Steering | LS Up: Double Tap',
    'Steering | LS Down: Double Tap', 'Steering | LS: Double Tap Cover',
}
CLICK = {'RTP: Click Entry Point', 'RTP: Middle Click', 'RTP: Mouse Buttons'}


def change(data):
    layout = Layout(data)
    report = {'radius': [], 'click_survival': [], 'thumb_completion': [], 'quiet_click': []}
    for title in layout.presets:
        if title in SCROLL:
            group = layout.active(title)['joystick']
            assert group['settings']['deadzone'] == '13276'
            assert 'edge_binding_radius' not in group['settings']
            group['settings']['edge_binding_radius'] = '13276'
            report['radius'].append(title)

    for title in ('Steering | LS Up: Modifier 1', 'Steering | LS Down: Modifier 0'):
        for source, name in (('joystick', 'dpad_north' if 'Up' in title else 'dpad_south'),
                             ('joystick', 'touch'), ('right_joystick', 'touch')):
            node = layout.active(title)[source]['inputs'][name]
            kind = 'chord' if name.startswith('dpad_') else 'release'
            entry = node['activators'][kind]
            original = actions(entry)
            filtered = [a for a in original if not any(f'{{{{Base::{c}}}}}' in a for c in CLICK)]
            assert len(original) - len(filtered) == 3
            entry['bindings']['binding'] = filtered
            report['click_survival'].append([title, source, name])

    for title, wheel in (('Steering | LS Up: Double Tap', 'SCROLL_UP'),
                         ('Steering | LS Down: Double Tap', 'SCROLL_DOWN')):
        for source in ('joystick', 'right_joystick'):
            entry = layout.active(title)[source]['inputs']['touch']['activators']['release']
            commands = actions(entry)
            assert commands[-1].startswith('controller_action remove_layer') and title in commands[-1]
            # Stored arrays execute bottom to top. Remove the timer owner before its output.
            entry['bindings']['binding'] = commands[:-1] + [f'mouse_wheel {wheel}, , ', commands[-1]]
            report['thumb_completion'].append([title, source])

    for source in ('left_trackpad', 'right_trackpad'):
        owner = 'LTP: Middle Click' if source == 'left_trackpad' else 'RTP: Middle Click'
        entry = layout.active(owner)[source]['inputs']['click']['activators']['Full_Press']
        assert entry['settings']['haptic_intensity'] == '1'
        entry['settings']['haptic_intensity'] = '0'
        report['quiet_click'].append([owner, source, 'click'])
    for title, source in (('LTP: Arrow Keys', 'left_trackpad'),
                          ('RTP: Mouse Buttons', 'right_trackpad')):
        group = layout.active(title)[source]
        assert group['settings']['haptic_intensity_override'] == '1'
        group['settings']['haptic_intensity_override'] = '0'
        for name in ('dpad_north', 'dpad_south', 'dpad_east', 'dpad_west'):
            for kind, entry in entries(group['inputs'][name]['activators']):
                if entry.get('settings', {}).get('haptic_intensity') == '1':
                    entry['settings']['haptic_intensity'] = '0'
                    report['quiet_click'].append([title, source, name, kind])
        report['quiet_click'].append([title, source, 'mode'])
    circular = layout.active('RTP: Circular Scroll')['right_trackpad']['inputs']['click']['activators']['Soft_Press']
    assert circular['settings']['haptic_intensity'] == '0'
    circular['settings']['haptic_intensity'] = '1'
    report['quiet_click'].append(['RTP: Circular Scroll', 'right_trackpad', 'click'])
    assert len(report['radius']) == 8
    assert len(report['click_survival']) == 6
    assert len(report['thumb_completion']) == 4
    return report


def build(variant):
    path = ROOT / f'neptune/single-set-{variant}_hold-gyro_latest.json'
    numeric = json.loads(path.read_text())
    cm = numeric['controller_mappings']
    order = list(cm['actions']) + list(cm['action_layers'])
    assert list(map(lambda k: int(k.split('_')[1]), cm['action_layers'])) == sorted(
        int(k.split('_')[1]) for k in cm['action_layers'])
    assert [p['name'] for p in cm['preset']] == order
    assert [p['id'] for p in cm['preset']] == [str(i) for i in range(len(cm['preset']))]
    assert len({x['title'] for x in cm['action_layers'].values()}) == len(cm['action_layers'])
    assert cm['title'].endswith(' :: 90.48')
    readable, _ = ids_to_titles(json.dumps(numeric), generate_lookup(numeric))
    data = json.loads(readable)
    before = copy.deepcopy(data)
    report = change(data)
    fixed = copy.deepcopy(data)
    report['fixes'] = apply_all(data)
    assert data == fixed, 'Fix pipeline changed the candidate; inspect before publishing'
    assert len(Layout(data).cm['action_layers']) == len(Layout(before).cm['action_layers'])
    data['controller_mappings']['title'] = cm['title'].rsplit(' :: ', 1)[0] + ' :: 90.49'
    final, _ = titles_to_ids(json.dumps(data, indent='\t') + '\n', generate_lookup(data))
    assert '{{' not in final
    return final, report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--install', action='store_true')
    args = parser.parse_args()
    for variant in ('default', 'alternative'):
        final, report = build(variant)
        (HERE / f'{variant}-candidate.json').write_text(final)
        (HERE / f'{variant}-build-report.json').write_text(json.dumps(report, indent=2) + '\n')
        if args.install:
            (ROOT / f'neptune/single-set-{variant}_hold-gyro_latest.json').write_text(final)
        print(variant, {key: len(value) for key, value in report.items()})


if __name__ == '__main__':
    main()
