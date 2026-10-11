"""90.54: 90.52 with one change. In the two stick modifiers the 200 ms chord that adds the Tap Cover moves from the stick's direction to the left stick's edge."""

import argparse
import copy
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from steam_layout.fixes import apply_all  # noqa: E402
from steam_layout.model import EMPTY, Layout, actions  # noqa: E402
from tools.convert_runtime_ids import generate_lookup, ids_to_titles, titles_to_ids  # noqa: E402

DEFLECT = 1 << 30                # the left stick's deflect in a chord's button mask
MARKER = 'Steering | LS: Tap Cover'
# stick modifier, its direction
SIDES = (('Steering | LS Up: Modifier 1', 'dpad_north'), ('Steering | LS Down: Modifier 0', 'dpad_south'))


def command(op, title):
    return f'controller_action {op}_layer {{{{Base::{title}}}}} 0 0, , '


def timer_to_the_edge(data):
    """The one change (author, 2026-10-11): the delayed chord that adds the Tap Cover leaves up or down for the edge.

    It moves whole, with its list and its settings, and is appended after the edge's guard chord. The reset
    and the Release stay on the direction. The edge then has three entries: the cleanup press, the guard
    chord and the timer."""
    layout, changed = Layout(data), []
    for title, own in SIDES:
        inputs = layout.active(title)['joystick']['inputs']
        found = inputs[own]['activators']
        assert set(found) == {'Full_Press', 'chord', 'release'}, (title, own, set(found))
        timer = found['chord']
        assert timer['settings']['delay_start'] == '200' and actions(timer)[-1] == command('add', MARKER), (title, own)
        assert int(timer['settings']['gyro_ratchet_button_mask']) == DEFLECT
        edge = inputs['edge']['activators']
        assert set(edge) == {'Full_Press', 'chord'} and actions(edge['chord']) == [EMPTY + ', , '], (title, set(edge))
        inputs[own]['activators'] = {kind: entry for kind, entry in found.items() if kind != 'chord'}
        edge['chord'] = [edge['chord'], timer]
        changed.append(f'{title}: {own} -> edge')
    return changed


def build(variant):
    source = ROOT / f'versions/neptune/90.52/single-set-{variant}_hold-gyro_90.52.json'
    numeric = json.loads(source.read_text())
    cm = numeric['controller_mappings']
    order = list(cm['actions']) + list(cm['action_layers'])
    assert cm['title'].endswith(' :: 90.52')
    assert [p['name'] for p in cm['preset']] == order
    assert [p['id'] for p in cm['preset']] == [str(i) for i in range(len(order))]
    assert [int(k.split('_')[1]) for k in cm['action_layers']] == sorted(
        int(k.split('_')[1]) for k in cm['action_layers'])
    assert len({x['title'] for x in cm['action_layers'].values()}) == len(cm['action_layers'])
    readable, _ = ids_to_titles(json.dumps(numeric), generate_lookup(numeric))
    data = json.loads(readable)
    changed = timer_to_the_edge(data)
    # One change only: the fix pipeline is not applied. What it would do is in the build report.
    fixes = apply_all(copy.deepcopy(data))
    data['controller_mappings']['title'] = cm['title'].rsplit(' :: ', 1)[0] + ' :: 90.54'
    final, _ = titles_to_ids(json.dumps(data, indent='\t') + '\n', generate_lookup(data))
    assert '{{' not in final
    return final, {'changed': changed, 'fixes not applied': fixes}


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
        print(variant, report['changed'])


if __name__ == '__main__':
    main()
