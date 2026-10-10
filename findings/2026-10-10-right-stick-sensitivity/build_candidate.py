"""90.45: horizontal sensitivity 150 -> 200 -> 250, vertical target 150."""
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
from steam_layout.model import Layout
from tools.convert_runtime_ids import generate_lookup, ids_to_titles, titles_to_ids

path = ROOT / 'findings/2026-10-10-steering-entry-and-quiet-drivers/build_candidate.py'
spec = importlib.util.spec_from_file_location('sensitivity_previous', path)
previous = importlib.util.module_from_spec(spec)
spec.loader.exec_module(previous)
VALUES = {'Base': '150', 'Turning Ramp Up 0': '200', 'Turning Ramp Up 1': '250'}


def build_from(numeric, variant):
    previous.preflight(numeric)
    text, _ = ids_to_titles(json.dumps(numeric), generate_lookup(numeric))
    data = json.loads(text)
    before = copy.deepcopy(data)
    layout = Layout(data)
    report = {'sensitivity': {}}
    for title, value in VALUES.items():
        group = layout.active(title)['right_joystick']
        assert group['mode'] == 'joystick_mouse'
        assert sum(group['id'] in p['group_source_bindings'] for p in layout.cm['preset']) == 1
        old = group['settings']['sensitivity']
        assert int(old) == int(value) - 50
        group['settings']['sensitivity'] = value
        report['sensitivity'][title] = {'before': old, 'after': value}
        if title != 'Base':
            # Preserve Base's vertical target while horizontal speed increases.
            scale, remainder = divmod(int(VALUES['Base']) * 100, int(value))
            assert remainder == 0, 'Record rounding explicitly if future targets need it'
            report['sensitivity'][title]['vertical_before'] = group['settings']['sensitivity_vert_scale']
            group['settings']['sensitivity_vert_scale'] = str(scale)
            report['sensitivity'][title]['vertical_after'] = str(scale)
    expected = copy.deepcopy(data)
    report['fixes'] = apply_all(data)
    assert data == expected, 'Sensitivity edits must not change any bindings through fixes'
    # Reversing three sensitivities and two scales restores the complete input.
    restored = copy.deepcopy(data)
    old_layout = Layout(restored)
    for title, change in report['sensitivity'].items():
        old_layout.active(title)['right_joystick']['settings']['sensitivity'] = change['before']
        if 'vertical_before' in change:
            old_layout.active(title)['right_joystick']['settings']['sensitivity_vert_scale'] = change['vertical_before']
    assert restored == before
    cm = data['controller_mappings']
    cm['title'] = cm['title'].rsplit(' :: ', 1)[0] + ' :: 90.45'
    # Both concise descriptions were reviewed; no numeric tuning is advertised.
    previous.preflight(data)
    text, _ = titles_to_ids(json.dumps(data, indent='\t') + '\n', generate_lookup(data))
    assert '{{' not in text
    roundtrip, _ = ids_to_titles(text, generate_lookup(data))
    assert json.loads(roundtrip) == data
    return json.loads(text), report


def build(variant):
    data, _ = previous.build(variant)
    return build_from(data, variant)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--install', action='store_true')
    parser.add_argument('--from-working', action='store_true',
                        help='Use the verified 90.44 working layout instead of rebuilding the frozen chain')
    args = parser.parse_args()
    for variant in ('default', 'alternative'):
        live = ROOT / f'neptune/single-set-{variant}_hold-gyro_latest.json'
        if args.from_working:
            old = json.loads(live.read_text())
            frozen = json.loads((previous.HERE / f'{variant}-candidate.json').read_text())
            assert old == frozen and old['controller_mappings']['title'].endswith(' :: 90.44')
            data, report = build_from(old, variant)
        else:
            data, report = build(variant)
        text = json.dumps(data, indent='\t') + '\n'
        (HERE / f'{variant}-candidate.json').write_text(text)
        (HERE / f'{variant}-fixes.json').write_text(json.dumps(report, indent=2) + '\n')
        if args.install:
            live.write_text(text)
        print(variant, report['sensitivity'], flush=True)


if __name__ == '__main__':
    main()
