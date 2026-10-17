"""Ibex 1.2: the Entry Point stays under Fn. From Ibex 1.0, as Ibex 1.1 less one thing.

On the Deck, 90.77 (the author, 2026-10-17): hold Start, push a stick inside the 200 ms so the stick guard lands,
and the next time Start is held the Fn layer comes on at once. 90.76 doesn't do it. The author: "My assumuption is
its the hand over so 3. I think the issue is we are removing the entry point layer. i think everything else is fine".

Ibex 1.1's hand-over had every bind that adds an Fn layer remove its Entry Point: the 200 ms chord on the menu
button, whose delay a guard can eat (A15), the chord on the other menu button, the two stick-touch Releases and the
two stick-click presses. 1.2 is 1.1's build with those six removes per Entry Point left out, so the Entry Point stays
under Fn until its own Release, as up to 1.0. Everything else of 1.1 stays: the Entry Points', guards' and Tap
Cover's right stick in Base's mouse mode (so Fn is still the right stick's owner, A77), the clicks adding Fn at the
press and removing both guards and the Tap Cover, Fn's own click Releases and pad copies, the click guard, the
deadzones and the merged chords. The fix pipeline then keeps the Fn layers' Entry Point cleanups, since the Entry
Point can be under Fn again.
"""

import argparse
import copy
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from steam_layout import controllers, convert  # noqa: E402
from steam_layout.fixes import apply_all  # noqa: E402
from steam_layout.model import Layout, actions, entries  # noqa: E402

spec = importlib.util.spec_from_file_location('ibex_1_1', ROOT / 'findings/2026-10-16-fn-right-stick-owner/build_candidate.py')
ibex_1_1 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ibex_1_1)

BEFORE, AFTER = '1.0', '1.2'


def keep_entry_point(data):
    """Take the Entry Point's remove back out of each bind of an Entry Point that adds its Fn layer."""
    layout, log = Layout(data), []
    for fn, ep in ibex_1_1.FN.items():
        drop = ibex_1_1.command(layout, 'remove_layer', ep)
        kept = []
        for source, group in layout.active(ep).items():
            for name, value in (group.get('inputs') or {}).items():
                for kind, entry in entries(value.get('activators') or {}):
                    if ('add_layer', fn) in layout.layer_ops(entry):
                        commands = list(actions(entry))
                        assert commands.count(drop) == 1, (ep, source, name, kind)
                        ibex_1_1.set_binding(entry, [c for c in commands if c != drop])
                        kept.append(f'{source}/{name} {kind}')
        assert len(kept) == 6, (ep, kept)
        log.append(f'{ep}: stays under {fn}; {", ".join(sorted(kept))}')
    return log


def build(variant):
    source = controllers.IBEX.snapshot(variant, BEFORE)
    numeric = json.loads(source.read_text())
    assert numeric['controller_mappings']['title'].endswith(f' :: {BEFORE}')
    before = convert.readable(numeric)
    data = copy.deepcopy(before)
    cm = data['controller_mappings']
    cm['title'] = cm['title'].rsplit(' :: ', 1)[0] + f' :: {AFTER}'
    parts = {'1 requires_click off': ibex_1_1.no_requires_click(data), '2 deadzone 13276': ibex_1_1.deadzones(data),
             '3 hand-over': ibex_1_1.hand_over(data)}
    merged = ibex_1_1.any_chords(data)
    parts['4 one Any chord'] = {title: len(inputs) for title, inputs in merged.items()}
    parts['5 the Entry Point stays under Fn'] = keep_entry_point(data)
    by_hand = copy.deepcopy(data)
    count = ibex_1_1.count
    counts = {'by hand': {'removes': count(by_hand, 'remove_layer'), 'adds': count(by_hand, 'add_layer')}}
    fixes = apply_all(data)
    final = convert.dumps(data)
    counts[BEFORE] = {'removes': count(before, 'remove_layer'), 'adds': count(before, 'add_layer')}
    counts[AFTER] = {'removes': count(data, 'remove_layer'), 'adds': count(data, 'add_layer')}
    return final, {'from': f'ibex {BEFORE}', 'version': AFTER, 'parts': parts, 'merged': merged, 'counts': counts,
                   'fixes': fixes, 'pipeline changed the layout': data != by_hand}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--install', action='store_true')
    args = parser.parse_args()
    for variant in controllers.VARIANTS:
        text, report = build(variant)
        (HERE / f'{variant}-candidate.json').write_text(text)
        (HERE / f'{variant}-build-report.json').write_text(json.dumps(report, indent=2, default=str) + '\n')
        if args.install:
            controllers.IBEX.working_json(variant).write_text(text)
        print(variant, report['version'], report['counts'], 'pipeline changed:', report['pipeline changed the layout'])


if __name__ == '__main__':
    main()
