"""90.47: silent Temp Cursor applies and protected stick-touch gestures in Steering."""
import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
from steam_layout.fixes import apply_all
from steam_layout.model import Layout
from tools.convert_runtime_ids import generate_lookup, ids_to_titles, titles_to_ids

PREVIOUS = ROOT / 'findings/2026-10-10-ramp-menu-and-driver-chords/build_candidate.py'
spec = importlib.util.spec_from_file_location('steering_touch_previous', PREVIOUS)
previous = importlib.util.module_from_spec(spec)
spec.loader.exec_module(previous)
preflight = previous.preflight
WINDOWS = ('LST: Double Tap', 'RST: Double Tap')


def transform(data, variant):
    layout = Layout(data)
    changes = {'quiet_cursor_adds': [], 'inherited_touches': [], 'window_movement': []}
    for index, side in enumerate(('L1', 'R1') if variant == 'default' else ('L2', 'R2')):
        source, name = (('switch', ('left_bumper', 'right_bumper')[index])
                        if variant == 'default' else
                        (('left_trigger', 'right_trigger')[index], 'edge'))
        for prefix in ('', 'Gyro | '):
            title = f'{prefix}{side}: Modifier {index}'
            entry = layout.active(title)[source]['inputs'][name]['activators']['chord']
            assert layout.layer_ops(entry) == [('add_layer', f'{side}: Temp Cursor Gyro')]
            assert entry['settings']['delay_start'] == '200'
            assert entry['settings']['haptic_intensity'] == '1'
            entry['settings']['haptic_intensity'] = '0'
            changes['quiet_cursor_adds'].append([title, source, name])

    for source in ('joystick', 'right_joystick'):
        node = layout.active('Steering')[source]['inputs']['touch']
        assert set(node['activators']) == {'release'}
        assert len(layout.layer_ops(node['activators']['release'])) == 3
        del layout.active('Steering')[source]['inputs']['touch']
        changes['inherited_touches'].append(['Steering', source, 'touch'])

    for title in WINDOWS:
        group = layout.active(title)['joystick']
        for name, key in (('dpad_north', 'W'), ('dpad_south', 'S')):
            assert name not in group.get('inputs', {})
            group.setdefault('inputs', {})[name] = {
                'activators': {'Full_Press': {
                    'bindings': {'binding': f'key_press {key}, , '},
                    'settings': {'interruptable': '0', 'haptic_intensity': '0'},
                }}, 'disabled_activators': {},
            }
            changes['window_movement'].append([title, 'joystick', name, key])
    return changes


def build_from(numeric, variant):
    preflight(numeric)
    assert numeric['controller_mappings']['title'].endswith(' :: 90.46')
    readable, _ = ids_to_titles(json.dumps(numeric), generate_lookup(numeric))
    data = json.loads(readable)
    before = Layout(copy.deepcopy(data))
    report = {'previous_builder_sha256': hashlib.sha256(PREVIOUS.read_bytes()).hexdigest(),
              'changes': transform(data, variant)}
    expected = copy.deepcopy(data)
    report['fixes'] = apply_all(data)
    assert data == expected, 'Inspect unexpected pipeline edits before installation'
    preflight(data)
    after = Layout(data)
    assert after.order == before.order and after.titles == before.titles
    assert len(after.cm['action_layers']) == 88
    assert after.active('Steering | LS: Entry Guard') == before.active('Steering | LS: Entry Guard')
    for name in ('dpad_north', 'dpad_south'):
        assert after.active('Steering')['joystick']['inputs'][name] == before.active('Steering')['joystick']['inputs'][name]
    for title in ('Base', 'Gyro Off Ramp Up', 'Turning Ramp Up 0', 'Turning Ramp Up 1'):
        assert after.active(title) == before.active(title)
    data['controller_mappings']['title'] = data['controller_mappings']['title'].rsplit(' :: ', 1)[0] + ' :: 90.47'
    # Both complete descriptions remain accurate; their variant-specific controls are unchanged.
    text, _ = titles_to_ids(json.dumps(data, indent='\t') + '\n', generate_lookup(data))
    assert '{{' not in text
    restored, _ = ids_to_titles(text, generate_lookup(data))
    assert json.loads(restored) == data
    return json.loads(text), report


def build(variant):
    numeric, _ = previous.build(variant)
    return build_from(numeric, variant)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--install', action='store_true')
    parser.add_argument('--from-working', action='store_true',
                        help='Use working 90.46, requiring equality with its validated candidate')
    args = parser.parse_args()
    for variant in ('default', 'alternative'):
        live = ROOT / f'neptune/single-set-{variant}_hold-gyro_latest.json'
        if args.from_working:
            numeric = json.loads(live.read_text())
            assert numeric == json.loads((previous.HERE / f'{variant}-candidate.json').read_text())
            data, report = build_from(numeric, variant)
        else:
            data, report = build(variant)
        text = json.dumps(data, indent='\t') + '\n'
        (HERE / f'{variant}-candidate.json').write_text(text)
        (HERE / f'{variant}-fixes.json').write_text(json.dumps(report, indent=2) + '\n')
        if args.install:
            live.write_text(text)
        print(variant, report['changes'], flush=True)


if __name__ == '__main__':
    main()
