"""Move pad click feedback from entry adds to final click outputs for 90.50."""

import argparse
import copy
import json
from pathlib import Path

from steam_layout.fixes import apply_all
from steam_layout.model import Layout, actions, entries
from tools.convert_runtime_ids import generate_lookup, ids_to_titles, titles_to_ids


ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent


def move_feedback(data):
    layout = Layout(data)
    changed = []
    for title, source in (('Base', 'left_trackpad'), ('Base', 'right_trackpad'),
                          ('RTP: Circular Scroll', 'right_trackpad')):
        entry = layout.active(title)[source]['inputs']['click']['activators']['Soft_Press']
        assert entry['settings']['haptic_intensity'] == '1'
        assert len(layout.layer_ops(entry)) == 1
        assert layout.layer_ops(entry)[0][1].endswith(': Click Entry Point')
        entry['settings']['haptic_intensity'] = '0'
        changed.append((title, source, 'click', 'entry off'))

    for title, source, command in (('LTP: Middle Click', 'left_trackpad', 'key_press CAPSLOCK'),
                                   ('RTP: Middle Click', 'right_trackpad', 'mouse_button MIDDLE')):
        entry = layout.active(title)[source]['inputs']['click']['activators']['Full_Press']
        assert entry['settings']['haptic_intensity'] == '0'
        assert actions(entry)[0].startswith(command)
        entry['settings']['haptic_intensity'] = '1'
        changed.append((title, source, 'click', 'final on'))

    for title, source in (('LTP: Arrow Keys', 'left_trackpad'),
                          ('RTP: Mouse Buttons', 'right_trackpad')):
        group = layout.active(title)[source]
        assert group['settings']['haptic_intensity_override'] == '0'
        for name in ('dpad_north', 'dpad_south', 'dpad_east', 'dpad_west'):
            node = group['inputs'][name]
            final = node['activators']['Full_Press']
            assert final['settings']['haptic_intensity'] == '0'
            assert len(actions(final)) == 1
            assert actions(final)[0].startswith(('key_press ', 'mouse_button ', 'mouse_wheel '))
            final['settings']['haptic_intensity'] = '1'
            changed.append((title, source, name, 'final on'))
            for kind, entry in entries(node['activators']):
                if entry is not final:
                    assert entry.get('settings', {}).get('haptic_intensity', '0') == '0'
    assert len(changed) == 13
    return changed


def build(variant):
    source = ROOT / f'versions/neptune/90.49/single-set-{variant}_hold-gyro_90.49.json'
    numeric = json.loads(source.read_text())
    cm = numeric['controller_mappings']
    order = list(cm['actions']) + list(cm['action_layers'])
    assert cm['title'].endswith(' :: 90.49')
    assert [p['name'] for p in cm['preset']] == order
    assert [p['id'] for p in cm['preset']] == [str(i) for i in range(len(order))]
    assert [int(k.split('_')[1]) for k in cm['action_layers']] == sorted(
        int(k.split('_')[1]) for k in cm['action_layers'])
    assert len({x['title'] for x in cm['action_layers'].values()}) == len(cm['action_layers'])
    readable, _ = ids_to_titles(json.dumps(numeric), generate_lookup(numeric))
    data = json.loads(readable)
    changed = move_feedback(data)
    expected = copy.deepcopy(data)
    fixes = apply_all(data)
    assert data == expected, 'Inspect unexpected automatic fix before installing'
    data['controller_mappings']['title'] = cm['title'].rsplit(' :: ', 1)[0] + ' :: 90.50'
    final, _ = titles_to_ids(json.dumps(data, indent='\t') + '\n', generate_lookup(data))
    assert '{{' not in final
    return final, {'changed': changed, 'fixes': fixes}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--install', action='store_true')
    args = parser.parse_args()
    for variant in ('default', 'alternative'):
        text, report = build(variant)
        (HERE / f'{variant}-candidate.json').write_text(text)
        (HERE / f'{variant}-build-report.json').write_text(json.dumps(report, indent=2) + '\n')
        if args.install:
            (ROOT / f'neptune/single-set-{variant}_hold-gyro_latest.json').write_text(text)
        print(variant, len(report['changed']))


if __name__ == '__main__':
    main()
