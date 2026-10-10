"""90.48: quiet Base/Gyro dual-driver feedback and Steering entry cleanup."""
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
from steam_layout.model import Layout, actions, entries
from tools.convert_runtime_ids import generate_lookup, ids_to_titles, titles_to_ids

PREVIOUS = ROOT / 'findings/2026-10-10-quiet-cursor-and-steering-touch/build_candidate.py'
spec = importlib.util.spec_from_file_location('guard_handoff_previous', PREVIOUS)
previous = importlib.util.module_from_spec(spec)
spec.loader.exec_module(previous)
preflight = previous.preflight
GUARD = 'Steering | LS: Entry Guard'


def transform(data, variant):
    layout = Layout(data)
    changes = {'quiet_dual_hold': [], 'driver_entries': []}
    for title in layout.presets:
        if ': Modifier 2' not in title or title.startswith('Steering | '):
            continue
        for source, group in layout.active(title).items():
            for name, node in group.get('inputs', {}).items():
                for kind, entry in entries(node.get('activators', {})):
                    if entry.get('settings', {}).get('haptic_intensity') == '1':
                        assert kind == 'chord' and entry['settings']['delay_start'] == '200'
                        assert len(layout.layer_ops(entry)) == 1
                        assert layout.layer_ops(entry)[0][1].endswith(': Tap Cover')
                        entry['settings']['haptic_intensity'] = '0'
                        changes['quiet_dual_hold'].append([title, source, name])
    assert len(changes['quiet_dual_hold']) == 4
    for owner in ('Steering',):
        for source, name, side, key, mask in previous.previous.drivers(variant):
            entry = layout.active(owner)[source]['inputs'][name]['activators']['chord']
            assert layout.layer_ops(entry) == [('remove_layer', GUARD),
                                              ('add_layer', f'Steering | {side}: {key} Key')]
            entry['bindings']['binding'] = next(c for c in actions(entry)
                if ('add_layer' in c) == (owner == 'Steering'))
            changes['driver_entries'].append([owner, source, name])
    return changes


def build_from(numeric, variant):
    preflight(numeric)
    assert numeric['controller_mappings']['title'].endswith(' :: 90.47')
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
    assert after.active(GUARD) == before.active(GUARD)
    for source in ('joystick', 'right_joystick'):
        assert after.active('Steering')[source] == before.active('Steering')[source]
    for title in ('Base', 'Gyro', 'Gyro Off Ramp Up', 'Turning Ramp Up 0', 'Turning Ramp Up 1'):
        assert after.active(title) == before.active(title)
    data['controller_mappings']['title'] = data['controller_mappings']['title'].rsplit(' :: ', 1)[0] + ' :: 90.48'
    # Descriptions still accurately identify variant controls and supported modes.
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
    parser.add_argument('--from-working', action='store_true')
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
