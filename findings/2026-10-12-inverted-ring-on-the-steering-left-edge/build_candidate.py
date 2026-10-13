"""90.63: the ring inverted on the left edge of ten Steering layers. From 90.62.

Since 90.61 the left stick's edge of ten Steering layers holds one chord with Invert Activation as the layer's
cleanup function: it runs while the edge is released and no driver is held, so with the stick off the rim. The
author, 2026-10-12: "We need to invert the left stick edge for the chorded inverted clean functions we just added
... every where in steering except in entry steering guard", then "just do it".

One setting in each of the ten layers' left stick groups: Outer Ring Binding Invert goes on. The edge then counts
as pressed inside the ring, so the chord runs with the stick at the rim and no driver held, where the press of
90.58 ran. The Soft Press timers on four of those edges do not follow the ring's setting (author, A67).

No bind, list or activator setting changes. The builder stops at anything else.
"""

import argparse
import copy
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from steam_layout.fixes import apply_all  # noqa: E402
from steam_layout.model import Layout, entries  # noqa: E402
from tools.convert_runtime_ids import generate_lookup, ids_to_titles, titles_to_ids  # noqa: E402

BEFORE, AFTER = '90.62', '90.63'
DRIVERS = {'default': ('R1', 'L1'), 'alternative': ('R2', 'L2')}
GUARD = 'Steering | LS: Entry Guard'


def readable(version, variant):
    source = ROOT / f'versions/neptune/{version}/single-set-{variant}_hold-gyro_{version}.json'
    numeric = json.loads(source.read_text())
    assert numeric['controller_mappings']['title'].endswith(f' :: {version}')
    text, _ = ids_to_titles(json.dumps(numeric), generate_lookup(numeric))
    return json.loads(text)


def ten(variant):
    right, left = DRIVERS[variant]
    return (f'Steering | {right}: W Key', f'Steering | {left}: S Key',
            'Steering | LS Up: Modifier 1', 'Steering | LS Down: Modifier 0',
            'Steering | LS: Tap Cover', 'Steering | LS: Double Tap Cover',
            'Steering | LS Up: Scroll Up', 'Steering | LS Down: Scroll Down',
            f'Steering | {right}!{left}: Modifier 2', f'Steering | {left}!{right}: Modifier 2')


def inverted_chords(layout, title):
    return [entry for kind, entry in entries(layout.active(title)['joystick']['inputs'].get('edge', {}).get('activators') or {})
            if kind == 'chord' and (entry.get('settings') or {}).get('edge_binding_invert') == '1']


def invert_the_ring(data, variant):
    layout, done = Layout(data), []
    with_chord = sorted(title for title in layout.presets if title.startswith('Steering')
                        and 'joystick' in layout.active(title) and inverted_chords(layout, title))
    assert with_chord == sorted((*ten(variant), GUARD)), with_chord        # every one but the Entry Guard
    groups = [id(layout.active(title)['joystick']) for title in layout.presets if 'joystick' in layout.active(title)]
    for title in ten(variant):
        group = layout.active(title)['joystick']
        assert groups.count(id(group)) == 1, title                          # the group is this layer's alone
        assert group['mode'] == 'dpad' and group['settings']['edge_binding_invert'] == '0', title
        assert len(inverted_chords(layout, title)) == 1, title
        group['settings']['edge_binding_invert'] = '1'
        done.append(f'{title}: the left stick\'s ring is inverted')
    assert layout.active(GUARD)['joystick']['settings']['edge_binding_invert'] == '0'
    return done


def removes(data):
    layout = Layout(data)
    return sum(1 for title in layout.presets for group in layout.active(title).values()
               for value in group.get('inputs', {}).values() for _, entry in entries(value.get('activators') or {})
               for op, _ in layout.layer_ops(entry) if op == 'remove_layer')


def differing(a, b, path=''):
    if isinstance(a, dict) and isinstance(b, dict):
        return [p for key in sorted(set(a) | set(b)) for p in differing(a.get(key), b.get(key), f'{path}/{key}')]
    if isinstance(a, list) and isinstance(b, list) and len(a) == len(b):
        return [p for i, (x, y) in enumerate(zip(a, b)) for p in differing(x, y, f'{path}/{i}')]
    return [] if a == b else [path]


def build(variant):
    before = readable(BEFORE, variant)
    data = copy.deepcopy(before)
    title = data['controller_mappings']['title']
    data['controller_mappings']['title'] = title.rsplit(' :: ', 1)[0] + f' :: {AFTER}'
    done = invert_the_ring(data, variant)
    by_hand = copy.deepcopy(data)
    apply_all(data)
    assert data == by_hand, 'the fix pipeline changed something'
    paths = differing(before, data)
    assert len(paths) == 11 and sum(p.endswith('/settings/edge_binding_invert') for p in paths) == 10, paths
    assert removes(data) == removes(before)
    final, _ = titles_to_ids(json.dumps(data, indent='\t') + '\n', generate_lookup(data))
    assert '{{' not in final
    return final, {'by hand': done, 'removes': {BEFORE: removes(before), AFTER: removes(data)}}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--install', action='store_true')
    args = parser.parse_args()
    for variant in ('default', 'alternative'):
        text, report = build(variant)
        (HERE / f'{variant}-candidate.json').write_text(text)
        (HERE / f'{variant}-build-report.json').write_text(json.dumps(report, indent=2, default=str) + '\n')
        if args.install:
            (ROOT / f'neptune/single-set-{variant}_hold-gyro_latest.json').write_text(text)
        print(variant, report['removes'])


if __name__ == '__main__':
    main()
