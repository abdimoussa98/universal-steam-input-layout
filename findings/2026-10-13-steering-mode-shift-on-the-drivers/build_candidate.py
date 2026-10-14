"""90.66: in `Steering` each driver mode-shifts the left stick to a group whose up and down are empty. From 90.65.

Confirmed by the author on the Deck, 2026-10-13 (A69): a burst of `remove_layer` calls makes a chord evaluate again
and an evaluation can fail, so the interruptible press beside a guard chord runs. In `Steering` that took the
driver's layer off with the driver held, and `Steering`'s exit on up or down underneath then ended `Steering`.

The author: "We need to have steering have a mode shift on bumper/trigger dependent on the layout. in steering base
if you are pressing bumper/triggers the up and down on left stick will be empty binds ... I also want you to remove
the 5sec delay that you added", then "Just build it".

Three changes a layout:
  - one new left stick group in `Steering`, a mode-shift target: `Steering`'s own stick with up and down empty;
  - on each driver in `Steering`, a Regular Press, not interruptible, that mode-shifts the left stick to it,
    stored before the driver's chord;
  - the 5 ms start delay of 90.65 comes off the cleanup press on the left edge of ten Steering layers.
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

BEFORE, AFTER = '90.65', '90.66'
STEERING = 'Steering'
# variant -> the drivers' names, and where each is bound in `Steering`: (source, input)
DRIVERS = {'default': (('R1', 'L1'), (('switch', 'right_bumper'), ('switch', 'left_bumper'))),
           'alternative': (('R2', 'L2'), (('right_trigger', 'edge'), ('left_trigger', 'edge')))}


def readable(version, variant):
    source = ROOT / f'versions/neptune/{version}/single-set-{variant}_hold-gyro_{version}.json'
    numeric = json.loads(source.read_text())
    assert numeric['controller_mappings']['title'].endswith(f' :: {version}')
    text, _ = ids_to_titles(json.dumps(numeric), generate_lookup(numeric))
    return json.loads(text)


def ten(variant):
    right, left = DRIVERS[variant][0]
    return (f'Steering | {right}: W Key', f'Steering | {left}: S Key',
            'Steering | LS Up: Modifier 1', 'Steering | LS Down: Modifier 0',
            'Steering | LS: Tap Cover', 'Steering | LS: Double Tap Cover',
            'Steering | LS Up: Scroll Up', 'Steering | LS Down: Scroll Down',
            f'Steering | {right}!{left}: Modifier 2', f'Steering | {left}!{right}: Modifier 2')


def owners(layout, group):
    return [title for title in layout.presets if any(g is group for g in layout.active(title).values())]


def shift_group(data):
    """A copy of `Steering`'s left stick group with up and down empty, listed in `Steering`'s preset as a
    mode-shift target. Returns its id."""
    cm, layout = data['controller_mappings'], Layout(data)
    stick = layout.active(STEERING)['joystick']
    assert owners(layout, stick) == [STEERING] and stick['mode'] == 'dpad'
    assert set(stick['inputs']) == {'dpad_north', 'dpad_south', 'dpad_east', 'dpad_west'}, set(stick['inputs'])
    for name in ('dpad_north', 'dpad_south'):                   # the exit: the only layer commands on this stick
        assert layout.layer_ops(next(entries(stick['inputs'][name]['activators']))[1]) == [('remove_layer', STEERING)]
    group = copy.deepcopy(stick)
    group['id'] = str(max(int(g['id']) for g in cm['group']) + 1)
    for name in ('dpad_north', 'dpad_south'):
        group['inputs'][name]['activators'] = {'Full_Press': {'bindings': {'binding': f'{EMPTY}, , '},
                                                              'settings': {'haptic_intensity': '0'}}}
    cm['group'].append(group)
    slots = layout.presets[STEERING]['group_source_bindings']
    assert not any('modeshift' in state for state in slots.values())
    slots[group['id']] = 'joystick inactive modeshift'
    return group['id']


def shift_on_the_drivers(data, variant, gid):
    """On each driver in `Steering`: the one repeating chord on itself that adds the driver's layer gets a Regular
    Press before it, not interruptible (the chord is active whenever the driver is held, A27), quiet, that
    mode-shifts the left stick."""
    layout, done = Layout(data), []
    for (source, name), driver in zip(DRIVERS[variant][1], DRIVERS[variant][0]):
        group = layout.active(STEERING)[source]
        assert owners(layout, group) == [STEERING], (source, owners(layout, group))
        value = group['inputs'][name]
        found = list(entries(value['activators']))
        assert [kind for kind, _ in found] == ['chord'], (name, found)
        chord = found[0][1]
        assert chord['settings'].get('hold_repeats') == '1' and [op for op, _ in layout.layer_ops(chord)] == ['add_layer']
        value['activators'] = {'Full_Press': {'bindings': {'binding': f'mode_shift joystick {gid}'},
                                              'settings': {'interruptable': '0', 'haptic_intensity': '0'}},
                               'chord': value['activators']['chord']}
        done.append(f'{STEERING} / {driver} ({source}/{name}): mode shift of the left stick to group {gid}')
    return done


def no_delay(data, variant):
    layout, done = Layout(data), []
    for title in ten(variant):
        (kind, press), (second, _), *_ = entries(layout.active(title)['joystick']['inputs']['edge']['activators'])
        assert (kind, second) == ('Full_Press', 'chord') and press['settings'].get('delay_start') == '5', title
        assert all('remove_layer' in a for a in actions(press)), title
        del press['settings']['delay_start']
        done.append(title)
    assert len(done) == 10
    return done


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
    gid = shift_group(data)
    drivers = shift_on_the_drivers(data, variant, gid)
    edges = no_delay(data, variant)
    assert removes(before) == removes(data)
    assert len(data['controller_mappings']['group']) == len(before['controller_mappings']['group']) + 1
    by_hand = copy.deepcopy(data)
    fixes = apply_all(data)
    assert data == by_hand, 'the fix pipeline changed the layout'
    final, _ = titles_to_ids(json.dumps(data, indent='\t') + '\n', generate_lookup(data))
    assert '{{' not in final
    return final, {'the mode-shift group': gid, 'drivers': drivers, 'start delay taken off the left edge of': edges,
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
        print(variant, 'group', report['the mode-shift group'], report['removes'])


if __name__ == '__main__':
    main()
