"""90.44: Entry Guard edge exit, quiet drivers and stateful-preserving releases."""
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

VERSION = '90.44'
PREVIOUS = ROOT / 'findings/2026-10-09-steering-entry-and-feedback/build_candidate.py'


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    loaded = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loaded)
    return loaded


previous = module('quiet_drivers_previous', PREVIOUS)
followup = module('quiet_drivers_followup', HERE / 'followup.py')
preflight = previous.preflight
transform = followup.transform


def build(variant):
    numeric, _ = previous.build(variant)
    return build_from(numeric, variant)


def build_from(numeric, variant):
    preflight(numeric)
    readable, _ = ids_to_titles(json.dumps(numeric), generate_lookup(numeric))
    data = json.loads(readable)
    before_layout = Layout(copy.deepcopy(data))
    report = {'previous_builder_sha256': hashlib.sha256(PREVIOUS.read_bytes()).hexdigest(),
              'changes': transform(data, variant)}
    before = copy.deepcopy(data)
    report['fixes'] = apply_all(data)
    report['pipeline_changed_layout'] = data != before
    assert data == before, 'The pipeline must preserve the approved exact changes'
    apply_all(data)
    assert data == before, 'The complete fix pipeline must remain at a fixed point'
    preflight(data)
    layout = Layout(data)
    assert layout.order == before_layout.order
    assert layout.titles == before_layout.titles
    for title in ('Base', 'Turning Ramp Up 0', 'Turning Ramp Up 1', 'Gyro Off Ramp Up'):
        assert layout.active(title)['right_joystick'] == before_layout.active(title)['right_joystick']
    cm = data['controller_mappings']
    cm['title'] = cm['title'].rsplit(' :: ', 1)[0] + f' :: {VERSION}'
    # The complete concise descriptions were reviewed for both variants. Their
    # feature overview and physical modifier/mouse-button mappings remain valid.
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
