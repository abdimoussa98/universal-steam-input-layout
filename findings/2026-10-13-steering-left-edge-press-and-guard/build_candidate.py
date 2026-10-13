"""90.65: the press and its guard chord back on the left edge of ten Steering layers, the press 5 ms late. From 90.64.

Since 90.61 the left stick's edge of ten Steering layers held one chord with Invert Activation as the layer's
cleanup function, and since 90.63 those ten rings were inverted. The author, 2026-10-13: "change the steering left
stick clean up back to the non inverted chord with interruptible regular press removals pattern we'd had before.
Make the left in those steering layers also no longer have the edge inverted ... the regular press removal to also
have a start delay of 5ms".

On each of the ten edges the inverted chord becomes what 90.58 had there: a repeating, interruptible Regular Press
of removes and, beside it, an empty chord on the drivers that is not interruptible. The press and the guard take
their 90.58 settings; the press carries today's commands, in their order (the Modifier 2 lists gained a remove in
90.62), and a start delay of 5 ms. Outer Ring Binding Invert goes off in the ten groups. Nothing else changes.
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

BEFORE, AFTER, PATTERN = '90.64', '90.65', '90.58'
DELAY = '5'
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


def press_and_guard(data, pattern, variant):
    """On the left edge of each of the ten layers: the one chord with Invert Activation becomes a Regular Press with
    the chord's commands and the 90.58 press's settings plus the start delay, then the 90.58 guard chord. A Soft
    Press timer on the same edge stays, stored after them. The ring's inversion goes off. Returns {layer: commands}."""
    layout, old, done = Layout(data), Layout(pattern), {}
    groups = [id(layout.active(title)['joystick']) for title in layout.presets if 'joystick' in layout.active(title)]
    for title in ten(variant):
        group = layout.active(title)['joystick']
        assert groups.count(id(group)) == 1, title                                   # the group is this layer's alone
        assert group['mode'] == 'dpad' and group['settings']['edge_binding_invert'] == '1', title
        edge = group['inputs']['edge']
        found = list(entries(edge['activators']))
        kinds = [kind for kind, _ in found]
        assert kinds[0] == 'chord' and set(kinds[1:]) <= {'Soft_Press'}, (title, kinds)
        chord, listed = found[0][1], actions(found[0][1])
        assert chord['settings'].get('edge_binding_invert') == '1' and all('remove_layer' in a for a in listed), title
        was = list(entries(old.active(title)['joystick']['inputs']['edge']['activators']))
        assert [kind for kind, _ in was][:2] == ['Full_Press', 'chord'], title
        press, guard = copy.deepcopy(was[0][1]), copy.deepcopy(was[1][1])
        assert press['settings'].get('hold_repeats') == '1' and press['settings'].get('interruptable') != '0', title
        assert 'delay_start' not in press['settings'] and 'edge_binding_invert' not in guard['settings'], title
        assert all(a.startswith(EMPTY) for a in actions(guard)) and guard['settings'].get('interruptable') == '0', title
        assert guard['settings']['gyro_ratchet_button_mask'] == chord['settings']['gyro_ratchet_button_mask'], title
        assert set(actions(press)) <= set(listed), title                             # 90.58's removes are all still there
        press['bindings'] = copy.deepcopy(chord['bindings'])
        press['settings']['delay_start'] = DELAY
        edge['activators'] = {'Full_Press': press, 'chord': guard,
                              **{k: v for k, v in edge['activators'].items() if k != 'chord'}}
        group['settings']['edge_binding_invert'] = '0'
        done[title] = listed
    assert len(done) == 10
    assert layout.active(GUARD)['joystick']['settings']['edge_binding_invert'] == '0'
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
    done = press_and_guard(data, readable(PATTERN, variant), variant)
    paths = differing(before, data)
    edges = [p for p in paths if p[-2:] == ('edge', 'activators')]
    rings = [p for p in paths if p[-2:] == ('settings', 'edge_binding_invert')]
    assert len(edges) == len(rings) == 10 and len(paths) == 21 and ('controller_mappings', 'title') in paths, paths
    assert removes(before) == removes(data)                                          # the lists are 90.64's
    layout = Layout(data)
    for layer, listed in done.items():
        (kind, press), (second, _), *rest = entries(layout.active(layer)['joystick']['inputs']['edge']['activators'])
        assert (kind, second) == ('Full_Press', 'chord') and actions(press) == listed, layer
        assert press['settings']['delay_start'] == DELAY and all(k == 'Soft_Press' for k, _ in rest), layer
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
