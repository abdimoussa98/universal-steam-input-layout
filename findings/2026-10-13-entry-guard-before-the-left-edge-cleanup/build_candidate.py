"""90.67: the mode shift of 90.66 goes; the ten left-edge cleanup presses add the Entry Guard before they remove.

From 90.66. The author, 2026-10-13: "revert the mode shift change. I still want keep the removal of the delays on
the clean up functions though. The other thing i want is for the left stick clean up removals to before cleaning up
i want you to add the left stick steering guard, this is a precaution for the weird edge case where the guard would
fail for repeated removal calls", then "ok start building".

A cleanup press can run past its guard chord in a burst of `remove_layer` calls (A69, confirmed on the Deck). With
the add, what such a press leaves on top is `Steering | LS: Entry Guard`, not `Steering` and its exit on up and
down; the held driver's repeating chord in the guard then removes the guard and adds the driver's layer.

Two changes a layout:
  - `Steering` loses the mode-shift press on each driver and the mode-shift group: it is 90.65's again;
  - on the left stick's edge of ten Steering layers the cleanup press gets one more command, stored last so that
    it runs first (A4): add `Steering | LS: Entry Guard`. No start delay, as on 90.66.
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
from steam_layout.model import MODE_SHIFT, Layout, actions, entries  # noqa: E402
from tools.convert_runtime_ids import generate_lookup, ids_to_titles, titles_to_ids  # noqa: E402

BEFORE, AFTER = '90.66', '90.67'
STEERING, GUARD = 'Steering', 'Steering | LS: Entry Guard'
ADD = f'controller_action add_layer {{{{Base::{GUARD}}}}} 0 0, , '
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


def press_of(layout, title):
    (kind, press), (second, _), *_ = entries(layout.active(title)['joystick']['inputs']['edge']['activators'])
    assert (kind, second) == ('Full_Press', 'chord'), title
    return press


def no_mode_shift(data, variant):
    """`Steering` as on 90.65: each driver keeps only its chord, and the mode-shift group is deleted."""
    cm, layout, done = data['controller_mappings'], Layout(data), []
    slots = layout.presets[STEERING]['group_source_bindings']
    gid, = (g for g, state in slots.items() if 'modeshift' in state)
    for (source, name), driver in zip(DRIVERS[variant][1], DRIVERS[variant][0]):
        activators = layout.active(STEERING)[source]['inputs'][name]['activators']
        assert list(activators) == ['Full_Press', 'chord'], (name, list(activators))
        assert MODE_SHIFT.search(actions(activators['Full_Press'])[0]).groups() == ('joystick', gid)
        del activators['Full_Press']
        done.append(f'{STEERING} / {driver} ({source}/{name}): the mode shift to group {gid} is gone')
    del slots[gid]
    cm['group'] = [group for group in cm['group'] if group['id'] != gid]
    assert gid not in json.dumps(data), 'the mode-shift group is still named'
    return gid, done


def guard_first(data, variant):
    """Each of the ten presses adds the Entry Guard before it removes: the add is stored last (A4)."""
    layout, done = Layout(data), []
    assert GUARD in layout.presets
    for title in ten(variant):
        press = press_of(layout, title)
        assert 'delay_start' not in press['settings'], title
        found = press['bindings']['binding']
        found = [found] if isinstance(found, str) else list(found)
        assert all('remove_layer' in a for a in found), title
        press['bindings']['binding'] = found + [ADD]
        done.append(f'{title}: {len(found)} remove(s), then the add stored last')
    assert len(done) == 10
    return done


def count(data, wanted):
    layout = Layout(data)
    return sum(1 for title in layout.presets for group in layout.active(title).values()
               for value in group.get('inputs', {}).values() for _, entry in entries(value.get('activators') or {})
               for op, _ in layout.layer_ops(entry) if op == wanted)


def without_delay(data, variant):
    data, layout = copy.deepcopy(data), None
    layout = Layout(data)
    for title in ten(variant):
        del press_of(layout, title)['settings']['delay_start']
    return data


def build(variant):
    before = readable(BEFORE, variant)
    data = copy.deepcopy(before)
    title = data['controller_mappings']['title']
    data['controller_mappings']['title'] = title.rsplit(' :: ', 1)[0] + f' :: {AFTER}'
    gid, drivers = no_mode_shift(data, variant)
    older = without_delay(readable('90.65', variant), variant)          # 90.66 without its shift is 90.65 without its delay
    older['controller_mappings']['title'] = data['controller_mappings']['title']
    assert data == older, '90.66 without the mode shift is not 90.65 without the delay'
    edges = guard_first(data, variant)
    assert count(before, 'remove_layer') == count(data, 'remove_layer')
    assert count(before, 'add_layer') + 10 == count(data, 'add_layer')
    assert len(data['controller_mappings']['group']) == len(before['controller_mappings']['group']) - 1
    by_hand = copy.deepcopy(data)
    fixes = apply_all(data)
    assert data == by_hand, 'the fix pipeline changed the layout'
    final, _ = titles_to_ids(json.dumps(data, indent='\t') + '\n', generate_lookup(data))
    assert '{{' not in final
    return final, {'the mode-shift group deleted': gid, 'drivers': drivers, 'the Entry Guard added first on': edges,
                   'removes': {BEFORE: count(before, 'remove_layer'), AFTER: count(data, 'remove_layer')},
                   'adds': {BEFORE: count(before, 'add_layer'), AFTER: count(data, 'add_layer')}, 'fixes': fixes,
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
        print(variant, report['removes'], report['adds'])


if __name__ == '__main__':
    main()
