"""90.51: the ring pads bump by their own binds, and the stick modifiers lose the cleanup on their own direction."""

import argparse
import copy
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from steam_layout.fixes import apply_all  # noqa: E402
from steam_layout.model import Layout, actions, map_title  # noqa: E402
from tools.convert_runtime_ids import generate_lookup, ids_to_titles, titles_to_ids  # noqa: E402

RENAME = {'L1': 'L2', 'R1': 'R2'}
RING = (('LTP: Arrow Keys', 'left_trackpad'), ('RTP: Mouse Buttons', 'right_trackpad'))
MODIFIERS = (('Steering | LS Up: Modifier 1', 'dpad_north'), ('Steering | LS Down: Modifier 0', 'dpad_south'))


def ring_bump(data):
    """The two ring pads' override goes from Off to Use Activator Settings; the ring's block states Off."""
    layout, changed = Layout(data), []
    for title, source in RING:
        group = layout.active(title)[source]
        assert group['mode'] == 'dpad' and group['settings']['haptic_intensity_override'] == '0'
        group['settings']['haptic_intensity_override'] = '5'
        block = group['inputs']['edge']['activators']['Full_Press']
        assert actions(block) == ['controller_action empty_binding, , ']
        assert 'haptic_intensity' not in block.get('settings', {})
        block.setdefault('settings', {})['haptic_intensity'] = '0'
        changed.append((title, source))
    return changed


def modifier_direction(data, variant):
    """Each stick modifier's own direction keeps its delayed hold marker and the reset, and loses the cleanup."""
    layout, changed = Layout(data), []
    for title, name in MODIFIERS:
        title = map_title(title, RENAME) if variant == 'alternative' else title
        activators = layout.active(title)['joystick']['inputs'][name]['activators']
        presses = activators['Full_Press']
        assert isinstance(presses, list) and len(presses) == 2
        cleanup = [e for e in presses if e['settings'].get('interruptable') != '0']
        reset = [e for e in presses if e['settings'].get('interruptable') == '0']
        assert len(cleanup) == 1 and len(reset) == 1
        assert {t for _, t in layout.layer_ops(cleanup[0])} >= {title, 'Steering | LS: Tap Cover'}
        assert layout.layer_ops(reset[0]) == [('remove_layer', 'Steering | LS: Tap Cover')]
        assert activators['chord']['settings']['delay_start'] == '200'
        activators['Full_Press'] = reset[0]
        changed.append((title, name))
    return changed


def build(variant):
    source = ROOT / f'versions/neptune/90.50/single-set-{variant}_hold-gyro_90.50.json'
    numeric = json.loads(source.read_text())
    cm = numeric['controller_mappings']
    order = list(cm['actions']) + list(cm['action_layers'])
    assert cm['title'].endswith(' :: 90.50')
    assert [p['name'] for p in cm['preset']] == order
    assert [p['id'] for p in cm['preset']] == [str(i) for i in range(len(order))]
    assert [int(k.split('_')[1]) for k in cm['action_layers']] == sorted(
        int(k.split('_')[1]) for k in cm['action_layers'])
    assert len({x['title'] for x in cm['action_layers'].values()}) == len(cm['action_layers'])
    readable, _ = ids_to_titles(json.dumps(numeric), generate_lookup(numeric))
    data = json.loads(readable)
    changed = {'ring': ring_bump(data), 'modifiers': modifier_direction(data, variant)}
    expected = copy.deepcopy(data)
    fixes = apply_all(data)
    assert data == expected, 'Inspect unexpected automatic fix before installing'
    data['controller_mappings']['title'] = cm['title'].rsplit(' :: ', 1)[0] + ' :: 90.51'
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
        print(variant, report['changed'])


if __name__ == '__main__':
    main()
