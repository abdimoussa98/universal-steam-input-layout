"""90.61: 90.58 with one inverted chord as the left-edge cleanup of ten Steering layers.

On the left stick's edge those layers had a repeating, interruptible Regular Press that removes layers and, beside
it, an empty chord on the drivers that holds it back. On the Deck the driver layer's press ran although its bumper
was held, and `Steering` ended (findings/2026-10-12-steering-ends-on-a-stick-touch). The author, 2026-10-12: "just
use a single inverted chord that is repeating ... all we're doing is updating the edge cleanup bind on the left
stick. And all the steering layers."

The press and its guard become one Chorded Press on the same drivers with Invert Activation: it runs while the
stick is off the rim and no driver is held (A61). Its commands are the press's 90.58 commands, in their order.
Nothing else changes. 90.59 and 90.60, two trials that did not help, are not on the line.
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
from steam_layout.model import EMPTY, Layout, actions, entries  # noqa: E402
from tools.convert_runtime_ids import generate_lookup, ids_to_titles, titles_to_ids  # noqa: E402

BEFORE, AFTER = '90.58', '90.61'
TEN = ('Steering | R1: W Key', 'Steering | L1: S Key', 'Steering | LS Up: Modifier 1', 'Steering | LS Down: Modifier 0',
       'Steering | LS: Tap Cover', 'Steering | LS: Double Tap Cover', 'Steering | LS Up: Scroll Up',
       'Steering | LS Down: Scroll Down', 'Steering | R1!L1: Modifier 2', 'Steering | L1!R1: Modifier 2')
RENAME = {'default': {}, 'alternative': {'R1': 'R2', 'L1': 'L2'}}


def readable(version, variant):
    source = ROOT / f'versions/neptune/{version}/single-set-{variant}_hold-gyro_{version}.json'
    numeric = json.loads(source.read_text())
    assert numeric['controller_mappings']['title'].endswith(f' :: {version}')
    text, _ = ids_to_titles(json.dumps(numeric), generate_lookup(numeric))
    return json.loads(text)


def named(title, variant):
    for old, new in RENAME[variant].items():
        title = title.replace(f'| {old}:', f'| {new}:').replace(f'| {old}!', f'| {new}!').replace(f'!{old}:', f'!{new}:')
    return title


def inverted_edges(data, variant):
    """On the left edge of each of the ten layers: one repeating, interruptible Regular Press of removes and one
    empty chord on the drivers that is not interruptible. They become one chord with the guard's drivers, Invert
    Activation, Hold to Repeat, not interruptible, quiet, carrying the press's commands as they are. A Soft Press
    timer on the same edge stays, stored after it. Returns {layer: the commands}."""
    layout, done = Layout(data), {}
    for title in (named(t, variant) for t in TEN):
        edge = layout.active(title)['joystick']['inputs']['edge']
        found = list(entries(edge['activators']))
        kinds = [kind for kind, _ in found]
        assert kinds[:2] == ['Full_Press', 'chord'] and set(kinds[2:]) <= {'Soft_Press'}, (title, kinds)
        press, guard = found[0][1], found[1][1]
        listed = actions(press)
        assert listed and all('remove_layer' in a for a in listed), title
        assert press['settings'].get('hold_repeats') == '1' and press['settings'].get('interruptable') != '0', title
        assert all(a.startswith(EMPTY) for a in actions(guard)) and guard['settings'].get('interruptable') == '0', title
        assert guard['settings'].get('gyro_ratchet_button_requireany_or_all') == '0', title
        chord = {'bindings': copy.deepcopy(press['bindings']),
                 'settings': {'gyro_ratchet_button_mask': guard['settings']['gyro_ratchet_button_mask'],
                              'gyro_ratchet_button_requireany_or_all': '0', 'edge_binding_invert': '1',
                              'hold_repeats': '1', 'interruptable': '0', 'haptic_intensity': '0'}}
        edge['activators'] = {'chord': chord, **{k: v for k, v in edge['activators'].items()
                                                  if k not in ('Full_Press', 'chord')}}
        done[title] = listed
    assert len(done) == 10
    return done


def differing(a, b, path=()):
    """The paths at which two layouts differ, cut at an input's `activators`."""
    if a == b:
        return []
    if path and path[-1] == 'activators':
        return [path]
    if isinstance(a, dict) and isinstance(b, dict) and a.keys() == b.keys():
        return [found for key in a for found in differing(a[key], b[key], path + (key,))]
    if isinstance(a, list) and isinstance(b, list) and len(a) == len(b):
        return [found for index, (x, y) in enumerate(zip(a, b)) for found in differing(x, y, path + (index,))]
    return [path]


def removes(data):
    layout = Layout(data)
    return sum(1 for title in layout.presets for group in layout.active(title).values()
               for value in group.get('inputs', {}).values() for _, entry in entries(value.get('activators') or {})
               for op, _ in layout.layer_ops(entry) if op == 'remove_layer')


def build(variant):
    before = readable(BEFORE, variant)
    data = copy.deepcopy(before)
    title = data['controller_mappings']['title']
    data['controller_mappings']['title'] = title.rsplit(' :: ', 1)[0] + f' :: {AFTER}'
    done = inverted_edges(data, variant)
    paths = differing(before, data)
    assert len(paths) == 11 and ('controller_mappings', 'title') in paths, paths            # ten edges and the title
    assert all(p[-2:] == ('edge', 'activators') for p in paths if p != ('controller_mappings', 'title')), paths
    assert removes(before) == removes(data)                                                # the lists are 90.58's
    layout = Layout(data)
    for layer, listed in done.items():
        (kind, chord), *rest = entries(layout.active(layer)['joystick']['inputs']['edge']['activators'])
        assert kind == 'chord' and actions(chord) == listed, layer
    by_hand = copy.deepcopy(data)
    fixes = apply_all(data)
    assert data == by_hand, 'the fix pipeline changed the layout'
    final, _ = titles_to_ids(json.dumps(data, indent='\t') + '\n', generate_lookup(data))
    assert '{{' not in final
    return final, {'left edges that changed': {layer: len(listed) for layer, listed in done.items()},
                   'removes': {BEFORE: removes(before), AFTER: removes(data)}, 'fixes': fixes,
                   'pipeline changed the layout': False}


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
        print(variant, len(report['left edges that changed']), 'left edges,', report['removes'])


if __name__ == '__main__':
    main()
