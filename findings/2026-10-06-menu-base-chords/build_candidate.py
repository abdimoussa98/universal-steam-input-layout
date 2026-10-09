"""90.37: restore July's Base menu self-chords, retaining the current targets.

Extends the frozen 90.36 builder. Run --install to generate working JSON;
audit, export sibling VDFs and save the version snapshot afterwards.
"""
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

spec = importlib.util.spec_from_file_location(
    'menu_chords_previous', ROOT / 'findings/2026-10-06-cleanup-entry-order/build_candidate.py')
previous = importlib.util.module_from_spec(spec)
spec.loader.exec_module(previous)
REFERENCE = ROOT / 'findings/2026-07-11-layer-order-swap/MOST_RECENT_LAYOUT.post-fix.json'
BUTTONS = ('button_menu', 'button_escape')


class Front:
    def finish(self):
        data = super().finish()
        inputs = Layout(data).active('Base')['switch']['inputs']
        reference = Layout(json.loads(REFERENCE.read_text())).active('Base')['switch']['inputs']
        for button in BUTTONS:
            old = inputs[button]['activators']
            assert list(old) == ['Full_Press'], (button, old)
            entry = copy.deepcopy(old['Full_Press'])
            entry['settings'] = copy.deepcopy(reference[button]['activators']['chord']['settings'])
            inputs[button]['activators'] = {'chord': entry}
        return data


def Builder(variant):
    return type('Concrete', (Front, type(previous.Builder(variant))), {})(variant)


def build(variant):
    data = Builder(variant).finish()
    apply_all(data)
    readable = json.dumps(data, indent='\t') + '\n'
    numeric, _ = titles_to_ids(readable, generate_lookup(data))
    assert '{{' not in numeric
    restored, _ = ids_to_titles(numeric, generate_lookup(data))
    assert json.loads(restored) == data
    return json.loads(numeric)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--install', action='store_true')
    args = parser.parse_args()
    for variant in ('default', 'alternative'):
        data = build(variant)
        working = ROOT / f'neptune/single-set-{variant}_hold-gyro_latest.json'
        current = json.loads(working.read_text())['controller_mappings']
        cm = data['controller_mappings']
        cm['title'] = current['title'].rsplit(' :: ', 1)[0] + ' :: 90.37'
        cm['description'] = current['description']
        target = working if args.install else HERE / f'{variant}-menu-base-chords.json'
        target.write_text(json.dumps(data, indent='\t') + '\n')
        print(target.relative_to(ROOT))


if __name__ == '__main__':
    main()
