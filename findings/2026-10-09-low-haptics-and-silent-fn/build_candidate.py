"""90.41: Low enabled haptics and silent Fn-layer adds, extending 90.40."""
import argparse
import importlib.util
import json
from pathlib import Path
import re
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
from tools.convert_runtime_ids import generate_lookup, ids_to_titles, titles_to_ids

spec = importlib.util.spec_from_file_location(
    'low_haptics_previous', ROOT / 'findings/2026-10-09-circular-scroll-haptics/build_candidate.py')
previous = importlib.util.module_from_spec(spec)
spec.loader.exec_module(previous)
FN_ADD = re.compile(r'(controller_action add_layer \{\{Base::(?:Stateful \| )?Menu (?:Left|Right): Fn Layer\}\} [01] )1(?=,)')


def update_feedback(data):
    """Only explicit enabled intensities and the Fn add's beep flag change."""
    changed = {'haptic_levels': 0, 'fn_beeps': 0}

    def visit(value):
        if isinstance(value, dict):
            for key, item in value.items():
                if key in ('haptic_intensity', 'haptic_intensity_override') and item in ('2', '3'):
                    value[key] = '1'
                    changed['haptic_levels'] += 1
                else:
                    value[key] = visit(item)
        elif isinstance(value, list):
            for i, item in enumerate(value):
                value[i] = visit(item)
        elif isinstance(value, str):
            value, count = FN_ADD.subn(r'\g<1>0', value)
            changed['fn_beeps'] += count
        return value

    visit(data)
    return changed


def build(variant):
    numeric, report = previous.build(variant)
    text, _ = ids_to_titles(json.dumps(numeric), generate_lookup(numeric))
    data = json.loads(text)
    changed = update_feedback(data)
    assert changed == {'haptic_levels': 82 if variant == 'default' else 84, 'fn_beeps': 4}, changed
    assert update_feedback(data) == {'haptic_levels': 0, 'fn_beeps': 0}
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
        cm['title'] = current['title'].rsplit(' :: ', 1)[0] + ' :: 90.41'
        cm['description'] = current['description']
        target = working if args.install else HERE / f'{variant}-candidate.json'
        target.write_text(json.dumps(data, indent='\t') + '\n')
        (HERE / f'{variant}-fixes.json').write_text(json.dumps(report, indent=2) + '\n')
        print(target.relative_to(ROOT), flush=True)


if __name__ == '__main__':
    main()
