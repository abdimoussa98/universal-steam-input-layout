"""90.43: Steering entry protection, owner-preserving recovery, and single beeps."""
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
from tools.convert_runtime_ids import generate_lookup, ids_to_titles, titles_to_ids

VERSION = '90.43'
PREVIOUS = ROOT / 'findings/2026-10-09-fn-haptics-and-steering-clear/build_candidate.py'


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    loaded = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loaded)
    return loaded


previous = module('entry_feedback_previous', PREVIOUS)


def preflight(data):
    cm = data['controller_mappings']
    order = list(cm['actions']) + list(cm['action_layers'])
    numbers = [int(key.split('_')[1]) for key in cm['action_layers']]
    titles = [layer['title'] for layer in cm['action_layers'].values()]
    assert numbers == sorted(numbers)
    assert [preset['name'] for preset in cm['preset']] == order
    assert [preset['id'] for preset in cm['preset']] == [str(i) for i in range(len(order))]
    assert len(titles) == len(set(titles)) == 88


def build(variant):
    numeric, _ = previous.build(variant)
    return build_from(numeric, variant)


def build_from(numeric, variant):
    """Apply this release to a verified90.42 rebuild (also useful for inspection)."""
    preflight(numeric)
    readable, _ = ids_to_titles(json.dumps(numeric), generate_lookup(numeric))
    data = json.loads(readable)
    original_order = list(data['controller_mappings']['action_layers'])
    report = {'previous_builder_sha256': hashlib.sha256(PREVIOUS.read_bytes()).hexdigest()}
    for name in ('entry_guard', 'modifier_recovery', 'beeps'):
        report[name] = module('entry_feedback_' + name, HERE / (name + '.py')).apply(data, variant)
    before = copy.deepcopy(data)
    report['fixes'] = apply_all(data)
    report['pipeline_changed_layout'] = data != before
    fixed = copy.deepcopy(data)
    apply_all(data)
    assert data == fixed, 'The complete fix pipeline must reach a fixed point'
    preflight(data)
    assert list(data['controller_mappings']['action_layers']) == original_order
    cm = data['controller_mappings']
    live = json.loads((ROOT / f'neptune/single-set-{variant}_hold-gyro_latest.json').read_text())['controller_mappings']
    cm['title'] = live['title'].rsplit(' :: ', 1)[0] + f' :: {VERSION}'
    # Reviewed for 90.43: the concise overview still describes both variants accurately.
    cm['description'] = live['description']
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
        target = (ROOT / f'neptune/single-set-{variant}_hold-gyro_latest.json'
                  if args.install else HERE / f'{variant}-candidate.json')
        target.write_text(json.dumps(data, indent='\t') + '\n')
        (HERE / f'{variant}-fixes.json').write_text(json.dumps(report, indent=2) + '\n')
        print(target.relative_to(ROOT), flush=True)


if __name__ == '__main__':
    main()
