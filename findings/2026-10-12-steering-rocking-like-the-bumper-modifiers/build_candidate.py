"""90.62: rocking in Steering the way the bumper modifiers do it. From 90.61.

Since 90.57, with both drivers held, the first driver's Release inside Modifier 2 added the other driver's layer
(the hand-over). On the Deck W to S worked and S back to W did not (author, 2026-10-12). Outside Steering no layer
is added on a Release during a rock: the second bumper's modifier is added by that bumper's own press, under
Modifier 2, and a Release only uncovers it. The author: "if I'm in R1 and I hit L1, it's like adding S ... even
though it's getting overwritten", then "go ahead and write that up. As a fix" and "start building".

By hand, in each layout and for each order of the two drivers:

    the first driver's layer    its chord on the second driver adds the second driver's layer, then Modifier 2
    Modifier 2                  the first driver's Release no longer adds; the second driver's Release also
                                removes the second driver's layer

The fix pipeline then adds the second driver's layer to Modifier 2's sixteen cleanup functions (R128), the
author's choice ("add them"). The builder stops at anything else.
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
from steam_layout.model import TARGET, Layout, actions, entries  # noqa: E402
from tools.convert_runtime_ids import generate_lookup, ids_to_titles, titles_to_ids  # noqa: E402

BEFORE, AFTER = '90.61', '90.62'
DRIVERS = {'default': ('R1', 'L1'), 'alternative': ('R2', 'L2')}
CONTROLS = {'default': {'R': ('switch', 'right_bumper'), 'L': ('switch', 'left_bumper')},
            'alternative': {'R': ('right_trigger', 'edge'), 'L': ('left_trigger', 'edge')}}
BY_HAND, BY_PIPELINE = 2, 32                      # removes added, per layout


def readable(version, variant):
    source = ROOT / f'versions/neptune/{version}/single-set-{variant}_hold-gyro_{version}.json'
    numeric = json.loads(source.read_text())
    assert numeric['controller_mappings']['title'].endswith(f' :: {version}')
    text, _ = ids_to_titles(json.dumps(numeric), generate_lookup(numeric))
    return json.loads(text)


def orders(variant):
    """(the first driver's layer, the second's, which driver each is, their Modifier 2), for both orders."""
    right, left = DRIVERS[variant]
    w, s = f'Steering | {right}: W Key', f'Steering | {left}: S Key'
    return ((w, s, 'R', 'L', f'Steering | {right}!{left}: Modifier 2'),
            (s, w, 'L', 'R', f'Steering | {left}!{right}: Modifier 2'))


def to(layout, command, title):
    """`command` with its target layer replaced by `title`."""
    return command.replace(TARGET.search(command).group(2), '{{%s::%s}}' % (layout.base, title))


def rock_like_the_modifiers(data, variant):
    layout, done = Layout(data), []
    entry = lambda layer, which, kind: dict(entries(
        layout.active(layer)[CONTROLS[variant][which][0]]['inputs'][CONTROLS[variant][which][1]]['activators']))[kind]
    ops = lambda e: layout.layer_ops(e)
    for own, other, me, them, modifier in orders(variant):
        # The first driver's layer: its chord on the second driver adds the second driver's layer under Modifier 2.
        chord = entry(own, them, 'chord')
        listed = actions(chord)
        assert ops(chord)[-1] == ('add_layer', modifier) and ('add_layer', other) not in ops(chord), own
        at = next(i for i, a in enumerate(listed) if 'add_layer' in a)      # stored bottom to top (A4): the entry
        chord['bindings']['binding'] = listed[:at + 1] + [to(layout, listed[at], other)] + listed[at + 1:]   # after it runs before it
        assert ops(chord)[-2:] == [('add_layer', other), ('add_layer', modifier)], own
        # Modifier 2: the first driver's Release only removes.
        release = entry(modifier, me, 'release')
        assert ops(release) == [('add_layer', other), ('remove_layer', modifier), ('remove_layer', own)], modifier
        release['bindings']['binding'] = [a for a in actions(release) if 'add_layer' not in a]
        assert ops(release) == [('remove_layer', modifier), ('remove_layer', own)], modifier
        # Modifier 2: the second driver's Release also removes the second driver's layer.
        release = entry(modifier, them, 'release')
        assert ops(release) == [('remove_layer', modifier)], modifier
        only = actions(release)[0]
        release['bindings']['binding'] = [to(layout, only, other), only]
        assert ops(release) == [('remove_layer', modifier), ('remove_layer', other)], modifier
        done.append(f'{own}: the chord on the other driver adds {other} under {modifier}')
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
    done = rock_like_the_modifiers(data, variant)
    by_hand = copy.deepcopy(data)
    assert removes(by_hand) == removes(before) + BY_HAND
    fixes = apply_all(data)
    added = [line for name, fix in fixes.items() for line in (fix.get('changed') or [])] if isinstance(fixes, dict) else None
    want = {f'{modifier} / ': other for _, other, _, _, modifier in orders(variant)}
    assert added is not None and len(added) == BY_PIPELINE, added
    assert all(any(line.startswith(start) and line.endswith(f': adds {other}') for start, other in want.items())
               for line in added), added                                      # R128, and nothing else
    assert removes(data) == removes(before) + BY_HAND + BY_PIPELINE
    final, _ = titles_to_ids(json.dumps(data, indent='\t') + '\n', generate_lookup(data))
    assert '{{' not in final
    return final, {'by hand': done, 'the fix pipeline added (R128)': added,
                   'removes': {BEFORE: removes(before), 'by hand': removes(by_hand), AFTER: removes(data)}}


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
