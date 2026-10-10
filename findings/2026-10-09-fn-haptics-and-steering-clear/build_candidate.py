"""90.42: Low feedback on every Fn entry and a full-deflection Steering exit."""
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
from steam_layout.model import Layout, always_on_layers, entries, map_title
from tools.convert_runtime_ids import generate_lookup, ids_to_titles, titles_to_ids

spec = importlib.util.spec_from_file_location(
    'fn_feedback_previous', ROOT / 'findings/2026-10-09-low-haptics-and-silent-fn/build_candidate.py')
previous = importlib.util.module_from_spec(spec)
spec.loader.exec_module(previous)

VERSION = '90.42'
GUARD = 'Steering | LS: Fallback Guard'


def steering_targets(layout, variant):
    """Runtime removal order: Steering windows, helpers/covers, then Steering."""
    family = [title for title in layout.presets
              if title == 'Steering' or title.startswith('Steering |')]
    mapping = {'L1': 'L2', 'R1': 'R2'} if variant == 'alternative' else {}
    shared = [map_title(title, mapping) for title in ('L1: Tap Cover', 'R1: Tap Cover')]
    windows = [title for title in family if title in always_on_layers(layout)]
    assert len(family) == 12 and len(windows) == 2
    return windows + [title for title in family if title not in windows and title != 'Steering'] + shared + ['Steering']


def update_bindings(data, variant):
    layout = Layout(data)
    fn = {title for title in layout.presets if title.endswith(': Fn Layer')}
    assert len(fn) == 4
    feedback = []
    # Include dormant groups and disabled banks so every saved Fn add is covered.
    for group in layout.groups.values():
        for name, slot in group.get('inputs', {}).items():
            for bank in ('activators', 'disabled_activators'):
                for kind, entry in entries(slot.get(bank, {})):
                    if any(op == 'add_layer' and target in fn for op, target in layout.layer_ops(entry)):
                        entry.setdefault('settings', {})['haptic_intensity'] = '1'
                        feedback.append({'group': group['id'], 'input': name, 'bank': bank, 'activation': kind})
    assert len(feedback) == 16, feedback

    targets = steering_targets(layout, variant)
    commands = [f'controller_action remove_layer {{{{Base::{title}}}}} 0 {int(title == "Steering")}, , '
                for title in reversed(targets)]
    for name in ('dpad_north', 'dpad_south'):
        acts = layout.active('Steering')['joystick']['inputs'][name]['activators']
        assert list(acts) == ['Soft_Press']
        assert acts['Soft_Press']['settings'] == {
            'hold_repeats': '1', 'repeat_rate': '50', 'interruptable': '0',
            'haptic_intensity': '1', 'activation_threshold': '29031'}
        acts['Soft_Press']['bindings']['binding'] = commands.copy()
    return {'fn_feedback': feedback, 'steering_removal_order': targets}


def build(variant):
    numeric, _ = previous.build(variant)
    readable, _ = ids_to_titles(json.dumps(numeric), generate_lookup(numeric))
    data = json.loads(readable)
    report = {'edits': update_bindings(data, variant)}
    before = copy.deepcopy(data)
    report['fixes'] = apply_all(data)
    report['pipeline_changed_layout'] = data != before
    text, _ = titles_to_ids(json.dumps(data, indent='\t') + '\n', generate_lookup(data))
    assert '{{' not in text
    restored, _ = ids_to_titles(text, generate_lookup(data))
    assert json.loads(restored) == data
    return json.loads(text), report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--install', action='store_true')
    args = parser.parse_args()
    for variant in ('default', 'alternative'):
        data, report = build(variant)
        working = ROOT / f'neptune/single-set-{variant}_hold-gyro_latest.json'
        current = json.loads(working.read_text())['controller_mappings']
        cm = data['controller_mappings']
        cm['title'] = current['title'].rsplit(' :: ', 1)[0] + f' :: {VERSION}'
        cm['description'] = current['description']
        target = working if args.install else HERE / f'{variant}-candidate.json'
        target.write_text(json.dumps(data, indent='\t') + '\n')
        (HERE / f'{variant}-fixes.json').write_text(json.dumps(report, indent=2) + '\n')
        print(target.relative_to(ROOT), flush=True)


if __name__ == '__main__':
    main()
