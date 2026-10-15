"""90.74: the right stick of the four Fn layers copies the left stick's group, which works. From 90.73.

The author, 2026-10-14: "in the right stick directions on the stick arent having haptic in the fn layer nor are the
correct binds there either"; 2026-10-15, of `;` `'` `.` `,`: "these are the ones i want now go ahead and build these"
(plans/2026-10-14-key-layer-click-and-fn-right-stick.md, part 2). The left stick in the Fn layer works on the Deck. The
two sticks' groups have the same shape (four chorded keys at haptic 1, a stick-click guard, the edge and touch
cleanups); only the right one states `deadzone` 13276 and `requires_click` 0. Copying the pattern that works, the right
stick's group keeps its own keys, guard (R3, button 20) and cleanups and takes the left stick's settings: those two
are dropped. Every direction keeps haptic 1 (Low).
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

BEFORE, AFTER = '90.73', '90.74'
FN_LAYERS = ('Menu Left: Fn Layer', 'Menu Right: Fn Layer', 'Stateful | Menu Left: Fn Layer',
             'Stateful | Menu Right: Fn Layer')
KEYS = {'dpad_north': 'SEMICOLON', 'dpad_south': 'SINGLE_QUOTE', 'dpad_east': 'PERIOD', 'dpad_west': 'COMMA'}
DROPPED = ('deadzone', 'requires_click')


def readable(version, variant):
    source = ROOT / f'versions/neptune/{version}/single-set-{variant}_hold-gyro_{version}.json'
    numeric = json.loads(source.read_text())
    assert numeric['controller_mappings']['title'].endswith(f' :: {version}')
    text, _ = ids_to_titles(json.dumps(numeric), generate_lookup(numeric))
    return json.loads(text)


def count(data, wanted):
    layout = Layout(data)
    return sum(1 for title in layout.presets for group in layout.active(title).values()
               for value in group.get('inputs', {}).values() for _, entry in entries(value.get('activators') or {})
               for op, _ in layout.layer_ops(entry) if op == wanted)


def directions(group):
    """{direction: (key, haptic, guard chord button)} of a stick D-pad group's four keys."""
    found = {}
    for direction in KEYS:
        chords = group['inputs'][direction]['activators']['chord']
        key, guard = chords
        found[direction] = (key['bindings']['binding'], key['settings'].get('haptic_intensity'),
                            guard['settings'].get('chord_button'))
    return found


def right_sticks(data):
    layout = Layout(data)
    log = []
    for title in FN_LAYERS:
        left, right = layout.active(title)['joystick'], layout.active(title)['right_joystick']
        assert left['mode'] == right['mode'] == 'dpad', title
        assert set(left['inputs']) == set(right['inputs']), title
        for direction, (key, haptic, guard) in directions(right).items():
            assert key == f'key_press {KEYS[direction]}, , ' and haptic == '1' and guard == '20', (title, direction)
        assert all(haptic == '1' and guard == '9' for _, haptic, guard in directions(left).values()), title
        settings = right['settings']
        assert {k: v for k, v in settings.items() if k not in DROPPED} == left['settings'], title
        assert all(k in settings for k in DROPPED), title
        right['settings'] = copy.deepcopy(left['settings'])
        log.append(f'{title} / right_joystick: settings as the left stick\'s, without '
                   f'{", ".join(f"{k} {settings[k]}" for k in DROPPED)}')
    return log


def build(variant):
    before = readable(BEFORE, variant)
    data = copy.deepcopy(before)
    title = data['controller_mappings']['title']
    data['controller_mappings']['title'] = title.rsplit(' :: ', 1)[0] + f' :: {AFTER}'
    log = right_sticks(data)
    assert count(data, 'remove_layer') == count(before, 'remove_layer')
    assert count(data, 'add_layer') == count(before, 'add_layer')
    by_hand = copy.deepcopy(data)
    fixes = apply_all(data)
    final, _ = titles_to_ids(json.dumps(data, indent='\t') + '\n', generate_lookup(data))
    assert '{{' not in final
    return final, {'changed': log,
                   'removes': {BEFORE: count(before, 'remove_layer'), AFTER: count(data, 'remove_layer')},
                   'adds': {BEFORE: count(before, 'add_layer'), AFTER: count(data, 'add_layer')},
                   'fixes': fixes, 'pipeline changed the layout': data != by_hand}


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
        print(variant, len(report['changed']), 'changes', report['removes'], report['adds'],
              'pipeline changed:', report['pipeline changed the layout'])


if __name__ == '__main__':
    main()
