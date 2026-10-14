"""90.70: every cleanup function in the Steering layers adds the Entry Guard before it removes. From 90.68.

The author, 2026-10-13: "for 90.70 keep the changes from 90.68 and have all the steering cleanups add the entry
steering guard."

90.67 put the add on the left stick's edge of ten Steering layers. A cleanup press can run past its guard chord on
any input (A69), so 90.70 puts it on the other 80 cleanup presses of the same ten layers too: the stick touches,
the right stick's edge, the buttons, the D-pad and the stick clicks. The add is stored last so that it runs first
(A4). Everything else is 90.68's: the presses repeat, and the Entry Guard's driver chords add the driver's layer
first.

90.69, the trial without Hold to Repeat, is a separate build from 90.68 and is not part of this one.
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
from steam_layout.flow_model import Inventory  # noqa: E402
from steam_layout.model import Layout, actions, entries  # noqa: E402
from tools.convert_runtime_ids import generate_lookup, ids_to_titles, titles_to_ids  # noqa: E402

BEFORE, AFTER = '90.68', '90.70'
GUARD = 'Steering | LS: Entry Guard'
ADD = f'controller_action add_layer {{{{Base::{GUARD}}}}} 0 0, , '


def readable(version, variant):
    source = ROOT / f'versions/neptune/{version}/single-set-{variant}_hold-gyro_{version}.json'
    numeric = json.loads(source.read_text())
    assert numeric['controller_mappings']['title'].endswith(f' :: {version}')
    text, _ = ids_to_titles(json.dumps(numeric), generate_lookup(numeric))
    return json.loads(text)


def presses(layout):
    """(layer, source, input, entry) for every cleanup press in a Steering layer, by the Cleanup audit's reading."""
    found, seen = [], set()
    for t in Inventory.of(layout).transitions:
        if t.role != 'recovery' or not t.layer.startswith('Steering') or t.activator != 'Full_Press':
            continue
        kind, entry = list(entries(layout.active(t.layer)[t.source]['inputs'][t.input]['activators']))[t.index]
        assert kind == 'Full_Press'
        if id(entry) not in seen:
            seen.add(id(entry))
            found.append((t.layer, t.source, t.input, entry))
    return found


def count(data, wanted):
    layout = Layout(data)
    return sum(1 for title in layout.presets for group in layout.active(title).values()
               for value in group.get('inputs', {}).values() for _, entry in entries(value.get('activators') or {})
               for op, _ in layout.layer_ops(entry) if op == wanted)


def build(variant):
    before = readable(BEFORE, variant)
    data = copy.deepcopy(before)
    title = data['controller_mappings']['title']
    data['controller_mappings']['title'] = title.rsplit(' :: ', 1)[0] + f' :: {AFTER}'
    layout = Layout(data)
    found = presses(layout)
    assert len(found) == 90 and len({layer for layer, *_ in found}) == 10, len(found)
    had, added = [], []
    for layer, source, name, entry in found:
        stored = list(actions(entry))
        if any('add_layer' in a for a in stored):
            assert (source, name) == ('joystick', 'edge') and stored[-1] == ADD, (layer, source, name)
            had.append(layer)
            continue
        assert all('remove_layer' in a for a in stored) and entry['settings'].get('hold_repeats') == '1'
        entry['bindings']['binding'] = stored + [ADD]              # stored last, so it runs first (A4)
        added.append(f'{layer} / {source}/{name}')
    assert (len(had), len(added)) == (10, 80)
    assert len(presses(Layout(data))) == 90, 'the audit no longer reads them as cleanup functions'
    assert count(before, 'remove_layer') == count(data, 'remove_layer')
    assert count(before, 'add_layer') + 80 == count(data, 'add_layer')
    by_hand = copy.deepcopy(data)
    fixes = apply_all(data)
    assert data == by_hand, 'the fix pipeline changed the layout'
    final, _ = titles_to_ids(json.dumps(data, indent='\t') + '\n', generate_lookup(data))
    assert '{{' not in final
    return final, {'had the add since 90.67': had, 'the Entry Guard added first on': added,
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
        print(variant, len(report['the Entry Guard added first on']), 'presses', report['removes'], report['adds'])


if __name__ == '__main__':
    main()
