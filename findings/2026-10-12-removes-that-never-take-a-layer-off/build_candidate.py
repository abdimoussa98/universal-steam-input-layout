"""90.58: 90.57 without the removes that never take a layer off. 1,162 fewer in the default layout, 1,174 in
the alternative.

Plan: plans/2026-10-12-removes-that-never-take-a-layer-off.md. The author, 2026-10-12: "I want to make sure
that this is reductive and not additive. So we're not going to be adding any layer removals right now. We're
just reducing them." The builder holds itself to that: it stops if anything but a `remove_layer` command is
gone, if a command is added or changes place, or if anything else in the layout differs from 90.57.
"""

import argparse
import copy
import json
from collections import Counter
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from steam_layout.fixes import apply_all  # noqa: E402
from steam_layout.model import TARGET, Layout, actions, entries  # noqa: E402
from tools.convert_runtime_ids import generate_lookup, ids_to_titles, titles_to_ids  # noqa: E402

BEFORE, AFTER = '90.57', '90.58'
TAKEN = {'default': 1162, 'alternative': 1174}


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


def take_out(data, variant):
    """The removes of `taken-out-<variant>.json` (select_removes.py), bind by bind. Each bind keeps at least
    one command, and loses exactly the removes its row names. Returns {the rule's word for it: how many}."""
    layout, gone = Layout(data), Counter()
    for row in json.loads((HERE / f'taken-out-{variant}.json').read_text(encoding='utf-8')):
        source, name = row['input'].split('/')
        kind, entry = list(entries(layout.active(row['layer'])[source]['inputs'][name]['activators']))[row['index']]
        assert kind == row['kind'], (row['layer'], row['input'], kind)
        targets = {r['layer'] for r in row['removes']}
        found = actions(entry)
        assert len(found) - len([a for a in found if 'remove_layer' not in a]) == row['listed'], (row['layer'], row['input'])
        left = [a for a in found if not ((m := TARGET.search(a)) and m.group(1) == 'remove_layer'
                                         and layout.resolve(m.group(2)) in targets)]
        assert left and len(found) - len(left) == len(targets), (row['layer'], row['input'], kind)
        entry['bindings']['binding'] = left[0] if len(left) == 1 else left
        gone.update(r['rule'] for r in row['removes'])
    return dict(gone)


def commands(value):
    return value if isinstance(value, list) else [value]


def differences(a, b, path, lists, other):
    if a == b:
        return
    if path and path[-1] == 'binding':
        lists.append((path, commands(a), commands(b)))
    elif isinstance(a, dict) and isinstance(b, dict):
        for key in a.keys() | b.keys():
            if key in a and key in b:
                differences(a[key], b[key], path + (key,), lists, other)
            else:
                other.append(path + (key,))
    elif isinstance(a, list) and isinstance(b, list) and len(a) == len(b):
        for index, (x, y) in enumerate(zip(a, b)):
            differences(x, y, path + (index,), lists, other)
    else:
        other.append(path)


def only_removes_gone(before, after):
    """The constraint. Returns (binds that differ, removes gone); raises if anything else differs."""
    lists, other = [], []
    differences(before, after, (), lists, other)
    assert other == [('controller_mappings', 'title')], other
    gone = 0
    for path, old, new in lists:
        lost, gained = Counter(old) - Counter(new), Counter(new) - Counter(old)
        assert not gained, (path, list(gained))
        assert all('remove_layer' in command for command in lost), (path, list(lost))
        rest = iter(old)
        assert all(any(x == y for y in rest) for x in new), path        # what stays keeps its order
        gone += sum(lost.values())
    return len(lists), gone


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
    gone = take_out(data, variant)
    binds, number = only_removes_gone(before, data)
    assert number == sum(gone.values()) == TAKEN[variant], (number, gone)
    by_hand = copy.deepcopy(data)
    fixes = apply_all(data)
    assert data == by_hand, 'the fix pipeline changed the layout'        # it must neither add nor take
    final, _ = titles_to_ids(json.dumps(data, indent='\t') + '\n', generate_lookup(data))
    assert '{{' not in final
    return final, {'taken out, by what the audit calls the bind': gone, 'binds that changed': binds,
                   'commands added': 0, 'fixes': fixes, 'pipeline changed the layout': data != by_hand,
                   'removes': {BEFORE: removes(before), AFTER: removes(data)}}


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
        print(variant, report['taken out, by what the audit calls the bind'], report['removes'],
              'binds that changed:', report['binds that changed'])


if __name__ == '__main__':
    main()
