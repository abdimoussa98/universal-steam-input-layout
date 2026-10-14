"""90.69, a trial off the line: no Hold to Repeat on the cleanup presses in the Steering layers. From 90.68.

The author, 2026-10-13: "we've never tried just making the regular press no longer repeating. Still interruptible,
but no longer repeating", "have all of the cleanup functions no longer have the regular press be repeating and undo
the change to add the layer the entry guard in the cleanup functions for now", scope "all in steering", then "build
90.69 but also build 90.70".

Two changes a layout:
  - the ten left-edge presses lose the add of `Steering | LS: Entry Guard` (90.67): they remove only, as on 90.66;
  - every cleanup press in a Steering layer (90 a layout) loses Hold to Repeat. It stays interruptible, and its
    guard chord is not touched.

It is not installed: 90.70 is built from 90.68 as well and is the working layout. This build is saved under
versions/neptune/90.69/ for the Deck.
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

BEFORE, AFTER = '90.68', '90.69'
GUARD = 'Steering | LS: Entry Guard'


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
    old = Layout(readable('90.66', variant))
    no_add, no_repeat = [], []
    for layer, source, name, entry in found:
        stored = list(actions(entry))
        if any('add_layer' in a for a in stored):
            assert (source, name) == ('joystick', 'edge') and GUARD in stored[-1] and all('remove_layer' in a for a in stored[:-1])
            stored = stored[:-1]
            entry['bindings']['binding'] = stored if len(stored) > 1 else stored[0]
            (_, was), *_ = entries(old.active(layer)['joystick']['inputs']['edge']['activators'])
            assert entry == was, layer                              # 90.66's press again
            no_add.append(layer)
        assert entry['settings'].get('hold_repeats') == '1' and entry['settings'].get('interruptable') != '0'
        del entry['settings']['hold_repeats']
        assert 'repeat_rate' not in entry['settings']
        no_repeat.append(f'{layer} / {source}/{name}')
    assert len(no_add) == 10
    assert len(presses(Layout(data))) == 90, 'the audit no longer reads them as cleanup functions'
    assert count(before, 'remove_layer') == count(data, 'remove_layer')
    assert count(before, 'add_layer') - 10 == count(data, 'add_layer')
    by_hand = copy.deepcopy(data)
    fixes = apply_all(data)
    assert data == by_hand, 'the fix pipeline changed the layout'
    final, _ = titles_to_ids(json.dumps(data, indent='\t') + '\n', generate_lookup(data))
    assert '{{' not in final
    return final, {'the Entry Guard add taken out of the left edge of': no_add, 'Hold to Repeat off on': no_repeat,
                   'removes': {BEFORE: count(before, 'remove_layer'), AFTER: count(data, 'remove_layer')},
                   'adds': {BEFORE: count(before, 'add_layer'), AFTER: count(data, 'add_layer')}, 'fixes': fixes,
                   'pipeline changed the layout': False}


def main():
    argparse.ArgumentParser().parse_args()                  # no --install: this build is off the line
    for variant in ('default', 'alternative'):
        text, report = build(variant)
        (HERE / f'{variant}-candidate.json').write_text(text)
        (HERE / f'{variant}-build-report.json').write_text(json.dumps(report, indent=2, default=str) + '\n')
        print(variant, len(report['Hold to Repeat off on']), 'presses', report['removes'], report['adds'])


if __name__ == '__main__':
    main()
