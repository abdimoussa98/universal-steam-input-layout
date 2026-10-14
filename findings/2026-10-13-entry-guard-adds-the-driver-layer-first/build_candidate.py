"""90.68: in the Entry Guard each driver's chord adds the driver's layer first, then removes the guard. From 90.67.

The author, 2026-10-13: "in the steering left stick guard change the execution order so that the first thing that
happens is we add either the W layer on the right bumper slash right trigger depending on the layout then we remove
the guard and then the same for the opposite side", then "Just do the order change".

One change on two inputs a layout: the two commands of each driver's chord in `Steering | LS: Entry Guard` swap
places. A binding array runs bottom to top (A4), so the add is stored last to run first. Between the two commands
the stack is `Steering`, the guard and the driver's layer, where on 90.67 it was `Steering` alone, with its exit on
up and down.
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

BEFORE, AFTER = '90.67', '90.68'
GUARD = 'Steering | LS: Entry Guard'
# variant -> where each driver is bound in the guard (source, input), and the layer it adds
DRIVERS = {'default': ((('switch', 'right_bumper'), 'Steering | R1: W Key'), (('switch', 'left_bumper'), 'Steering | L1: S Key')),
           'alternative': ((('right_trigger', 'edge'), 'Steering | R2: W Key'), (('left_trigger', 'edge'), 'Steering | L2: S Key'))}


def readable(version, variant):
    source = ROOT / f'versions/neptune/{version}/single-set-{variant}_hold-gyro_{version}.json'
    numeric = json.loads(source.read_text())
    assert numeric['controller_mappings']['title'].endswith(f' :: {version}')
    text, _ = ids_to_titles(json.dumps(numeric), generate_lookup(numeric))
    return json.loads(text)


def add_first(data, variant):
    layout, done = Layout(data), []
    for (source, name), owner in DRIVERS[variant]:
        (kind, chord), = entries(layout.active(GUARD)[source]['inputs'][name]['activators'])
        assert kind == 'chord' and chord['settings'].get('hold_repeats') == '1', (name, kind)
        assert layout.layer_ops(chord) == [('remove_layer', GUARD), ('add_layer', owner)], layout.layer_ops(chord)   # run order
        chord['bindings']['binding'] = list(reversed(chord['bindings']['binding']))
        assert layout.layer_ops(chord) == [('add_layer', owner), ('remove_layer', GUARD)]
        done.append(f'{GUARD} / {source}/{name}: adds {owner}, then removes the guard')
    return done


def flat(data):
    """Every bind with its commands sorted: equal on both sides when only an order changed."""
    layout = Layout(data)
    return {(title, source, name): [(kind, entry.get('settings') or {}, sorted(layout.layer_ops(entry)))
                                    for kind, entry in entries(value.get('activators') or {})]
            for title in layout.presets for source, group in layout.active(title).items()
            for name, value in (group.get('inputs') or {}).items()}


def build(variant):
    before = readable(BEFORE, variant)
    data = copy.deepcopy(before)
    title = data['controller_mappings']['title']
    data['controller_mappings']['title'] = title.rsplit(' :: ', 1)[0] + f' :: {AFTER}'
    done = add_first(data, variant)
    assert flat(before) == flat(data), 'more than an order changed'
    by_hand = copy.deepcopy(data)
    fixes = apply_all(data)
    assert data == by_hand, 'the fix pipeline changed the layout'
    final, _ = titles_to_ids(json.dumps(data, indent='\t') + '\n', generate_lookup(data))
    assert '{{' not in final
    return final, {'chords reordered': done, 'fixes': fixes, 'pipeline changed the layout': False}


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
        print(variant, *report['chords reordered'], sep='\n  ')


if __name__ == '__main__':
    main()
