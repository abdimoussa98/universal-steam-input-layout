"""90.57: 90.56 with both drivers held in Steering handing over, a one-remove second driver, and 264 removes fewer.

Plan: plans/2026-10-11-two-drivers-in-steering.md. Parts 1, 3 and 6 are built; part 2 (the stick windows) is not.
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
from steam_layout.model import TARGET, Layout, actions, entries, map_title  # noqa: E402
from tools.convert_runtime_ids import generate_lookup, ids_to_titles, titles_to_ids  # noqa: E402

RENAME = {'L1': 'L2', 'R1': 'R2'}
STEERING, GUARD = 'Steering', 'Steering | LS: Entry Guard'
W, S = 'Steering | R1: W Key', 'Steering | L1: S Key'
# Modifier 2 layer -> (first driver, its layer, second driver, the second driver's layer, the second driver's cover)
MOD2 = {'Steering | R1!L1: Modifier 2': ('R1', W, 'L1', S, 'L1: Tap Cover'),
        'Steering | L1!R1: Modifier 2': ('L1', S, 'R1', W, 'R1: Tap Cover')}
COVERS = ('L1: Tap Cover', 'R1: Tap Cover')
WINDOWS = ('Steering | LS Up: Double Tap', 'Steering | LS Down: Double Tap')
GYRO_MOD2 = ('Gyro | L1!R1: Modifier 2', 'Gyro | R1!L1: Modifier 2')
# What the Gyro Modifier 2 Releases stop naming, beside the other Gyro Modifier 2 layer (the R132 entries of 90.43).
GYRO_NEVER = (STEERING, GUARD, 'L1: Modifier 0', 'R1: Modifier 1', 'L1!R1: Modifier 2', 'R1!L1: Modifier 2')
INPUT = {'default': {'R1': ('switch', 'right_bumper'), 'L1': ('switch', 'left_bumper')},
         'alternative': {'R1': ('right_trigger', 'edge'), 'L1': ('left_trigger', 'edge')}}


def readable(version, variant):
    source = ROOT / f'versions/neptune/{version}/single-set-{variant}_hold-gyro_{version}.json'
    numeric = json.loads(source.read_text())
    cm = numeric['controller_mappings']
    order = list(cm['actions']) + list(cm['action_layers'])
    assert cm['title'].endswith(f' :: {version}')
    assert [p['name'] for p in cm['preset']] == order
    assert [p['id'] for p in cm['preset']] == [str(i) for i in range(len(order))]
    assert [int(k.split('_')[1]) for k in cm['action_layers']] == sorted(
        int(k.split('_')[1]) for k in cm['action_layers'])
    assert len({x['title'] for x in cm['action_layers'].values()}) == len(cm['action_layers'])
    text, _ = ids_to_titles(json.dumps(numeric), generate_lookup(numeric))
    return json.loads(text)


def named(title, variant):
    return map_title(title, RENAME) if variant == 'alternative' else title


def command(op, title, variant):
    return f'controller_action {op}_layer {{{{Base::{named(title, variant)}}}}} 0 0, , '


def store(entry, found):
    entry['bindings']['binding'] = found[0] if len(found) == 1 else found


def drop(layout, title, control, kinds, targets, op='remove_layer'):
    """Take the commands of this kind that name `targets` out of the entries of `kinds` on one input.
    Returns how many went."""
    source, name = control
    gone = 0
    for kind, entry in entries(layout.active(title)[source]['inputs'][name]['activators']):
        if kind not in kinds:
            continue
        found = actions(entry)
        left = [a for a in found if not ((m := TARGET.search(a)) and m.group(1) == op and layout.resolve(m.group(2)) in targets)]
        if len(left) != len(found):
            assert left, (title, control, kind)
            store(entry, left)
            gone += len(found) - len(left)
    return gone


def group_of(data, layout, title, source, like):
    """The layer's active group on a source. The alternative's Modifier 2 layers have none on the first
    driver's trigger, so one is made with the settings of `like`'s group there."""
    active = layout.active(title)
    if source in active:
        return active[source]
    cm = data['controller_mappings']
    group = copy.deepcopy(layout.active(like)[source])
    group['id'] = str(max(int(g['id']) for g in cm['group']) + 1)
    group['inputs'] = {}
    cm['group'].append(group)
    layout.groups[group['id']] = group
    layout.presets[title]['group_source_bindings'][group['id']] = f'{source} active'
    layout._active.pop(title, None)
    return group


def handover(data, variant):
    """Part 1 (author's report, 2026-10-11): R1 held for W, L1 pressed for Modifier 2, and letting go of R1 with
    the stick at the rim ended `Steering` although L1 was held.

    Each Steering Modifier 2 layer now binds its first driver: the driver's key, and a Release that adds the
    second driver's layer and then removes the Modifier 2 layer and the first driver's layer. The add is stored
    last, so it runs first (A4) and `Steering` is never the top layer inside the array (R174)."""
    layout, done = Layout(data), []
    for title, (first, own, second, other, _) in MOD2.items():
        source, name = INPUT[variant][first]
        model = layout.active(named(own, variant))[source]['inputs'][name]['activators']
        press = model['Full_Press']
        assert press['settings'].get('interruptable') == '0' and 'hold_repeats' not in press['settings'], title
        assert len(actions(press)) == 1 and 'key_press' in actions(press)[0], title
        group = group_of(data, layout, named(title, variant), source, like=named(own, variant))
        assert name not in group['inputs'], (title, name)
        release = copy.deepcopy(model['release'])
        release['bindings']['binding'] = [command('remove', own, variant), command('remove', title, variant),
                                          command('add', other, variant)]
        group['inputs'][name] = {'activators': {'Full_Press': copy.deepcopy(press), 'release': release},
                                 'disabled_activators': {}}
        done.append(f'{title}: {first}')
    return done


def second_driver(data, variant):
    """Part 3 (author, 2026-10-12): "I don't want to be cleared out of steering in mod 2".

    The second driver keeps one bind in each Steering Modifier 2 layer: a Release that removes that layer. Its
    88-remove list is gone (it left `Gyro` and the first driver's layer alone: D1, D2), and so are the 200 ms
    Chorded Press that added the cover and the repeating press that reset it (D4). With no timer left, the
    twelve command binds and the two stick touch Releases stop adding the cover."""
    layout, done = Layout(data), {}
    for title, (first, own, second, other, cover) in MOD2.items():
        host, source_name = named(title, variant), INPUT[variant][second]
        slot = layout.active(host)[source_name[0]]['inputs'][source_name[1]]
        found = slot['activators']
        assert set(found) == {'release', 'chord', 'Full_Press'}, (title, set(found))
        assert found['chord']['settings'].get('delay_start') == '200' and layout.layer_ops(found['chord']) == [
            ('add_layer', named(cover, variant))], title
        assert layout.layer_ops(found['Full_Press']) == [('remove_layer', named(cover, variant))], title
        release = found['release']
        removed = [t for op, t in layout.layer_ops(release)]
        assert len(removed) == 88 and host in removed and STEERING not in removed and 'Cursor Gyro' not in removed, title
        store(release, [a for a in actions(release) if layout.resolve(TARGET.search(a).group(2)) == host])
        slot['activators'] = {'release': release}
        adds = 0
        for source, group in layout.active(host).items():
            for name in group.get('inputs', {}):
                adds += drop(layout, host, (source, name), ('chord', 'release', 'Full_Press', 'Soft_Press'),
                             {named(cover, variant)}, op='add_layer')
        assert adds == 14, (title, adds)                      # twelve command binds and two stick touch Releases
        done[title] = {'second driver': second, 'removes left': 1, 'adds of the cover taken out': adds}
    return done


def cover_out(data, variant):
    """The cover can no longer sit over a Steering Modifier 2 layer. The fix pipeline takes it out of the lists
    it reads (R132). These four binds it does not read: the Modifier 2 entry of the W and of the S layer, and
    `Steering`'s exit on up and on down, which lists both covers."""
    layout, covers, gone = Layout(data), {named(c, variant) for c in COVERS}, {}
    for title, (first, own, second, _, _) in MOD2.items():
        gone[f'{own}: the Modifier 2 entry'] = drop(layout, named(own, variant), INPUT[variant][second], ('chord',), covers)
    for direction in ('dpad_north', 'dpad_south'):
        gone[f'{STEERING}: {direction}'] = drop(layout, STEERING, ('joystick', direction),
                                                ('Soft_Press', 'Full_Press', 'chord'), covers)
    assert sorted(gone.values()) == [1, 1, 2, 2], gone
    return gone


def never_there(data, variant):
    """Part 6 (author, 2026-10-12: "remember i still want to reduce unnecessay removals"). R132 as tightened:
    a list names only layers that can be on the stack when its bind fires.

    In the W and in the S layer three binds on the drivers named layers that bind the same driver themselves:
    the two stick windows, and the Modifier 2 layer over them. Such a layer answers the driver whenever it is on
    (A1, A7), so those binds never fired with it on the stack. Sixteen removes."""
    layout, windows, gone = Layout(data), {named(w, variant) for w in WINDOWS}, {}
    for title, (first, own, second, _, _) in MOD2.items():
        layer, host = named(own, variant), named(title, variant)
        gone[f'{own}: the Modifier 2 entry'] = drop(layout, layer, INPUT[variant][second], ('chord',), windows)
        for driver in (first, second):
            gone[f'{own}: the Release on {driver}'] = drop(layout, layer, INPUT[variant][driver], ('release',), windows | {host})
    assert sorted(gone.values()) == [2, 2, 3, 3, 3, 3], gone
    return gone


def gyro_modifier_2(data, variant):
    """The Gyro Modifier 2 Releases (author, 2026-10-12: "ok", then "yes"). Each of the four named `Steering`, its
    Entry Guard, the two plain modifiers, the two plain Modifier 2 layers and the other Gyro Modifier 2 layer.
    None can be on the stack when the Release fires; two R132 register entries of 90.43 kept them, from the
    author's 2026-10-04 request for the Steering fallback, which went in 90.42. Twenty-eight removes."""
    layout, gone = Layout(data), {}
    for title in GYRO_MOD2:
        other = next(t for t in GYRO_MOD2 if t != title)
        targets = {named(t, variant) for t in (*GYRO_NEVER, other)}
        for driver in ('L1', 'R1'):
            gone[f'{title}: the Release on {driver}'] = drop(layout, named(title, variant), INPUT[variant][driver],
                                                             ('release',), targets)
    assert set(gone.values()) == {7}, gone
    return gone


def removes(data):
    layout = Layout(data)
    return sum(1 for title in layout.presets for group in layout.active(title).values()
               for value in group.get('inputs', {}).values() for _, entry in entries(value.get('activators') or {})
               for op, _ in layout.layer_ops(entry) if op == 'remove_layer')


def build(variant):
    data = readable('90.56', variant)
    before = removes(data)
    title = data['controller_mappings']['title']
    # The release first: two register entries end at 90.56, and the pipeline reads the title for that.
    data['controller_mappings']['title'] = title.rsplit(' :: ', 1)[0] + ' :: 90.57'
    changed = {'part 1, the first driver hands over': handover(data, variant),
               'part 3, the second driver': second_driver(data, variant),
               'part 3, the cover out of four binds': cover_out(data, variant),
               'part 6, never there when the bind fires': never_there(data, variant),
               'part 6, the Gyro Modifier 2 Releases': gyro_modifier_2(data, variant)}
    by_hand = copy.deepcopy(data)
    fixes = apply_all(data)
    final, _ = titles_to_ids(json.dumps(data, indent='\t') + '\n', generate_lookup(data))
    assert '{{' not in final
    return final, {'changed': changed, 'fixes': fixes, 'pipeline changed the layout': data != by_hand,
                   'removes': {'90.56': before, 'before the pipeline': removes(by_hand), '90.57': removes(data)}}


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
        print(variant, {k: len(v) for k, v in report['changed'].items()}, report['removes'],
              'pipeline changed the layout:', report['pipeline changed the layout'])


if __name__ == '__main__':
    main()
