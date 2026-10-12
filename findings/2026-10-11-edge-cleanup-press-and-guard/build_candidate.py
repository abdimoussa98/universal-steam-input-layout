"""90.56: 90.55 with the left edge's cleanup back to the press and its guard chord in ten Steering layers."""

import argparse
import copy
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from steam_layout.fixes import apply_all  # noqa: E402
from steam_layout.model import EMPTY, Layout, actions, entries, map_title  # noqa: E402
from tools.convert_runtime_ids import generate_lookup, ids_to_titles, titles_to_ids  # noqa: E402

RENAME = {'L1': 'L2', 'R1': 'R2'}
# The ten layers whose left edge held a chord with Invert Activation in 90.55. The Entry Guard keeps its own.
EDGES = ('Steering | R1: W Key', 'Steering | L1: S Key',
         'Steering | LS Up: Modifier 1', 'Steering | LS Down: Modifier 0',
         'Steering | LS: Tap Cover', 'Steering | LS: Double Tap Cover',
         'Steering | LS Up: Scroll Up', 'Steering | LS Down: Scroll Down',
         'Steering | R1!L1: Modifier 2', 'Steering | L1!R1: Modifier 2')
GUARD = 'Steering | LS: Entry Guard'


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


def edge_cleanups(data, variant):
    """The one change (author, 2026-10-11): "switch back to normal clean ups for all besides the steering entry guard".

    On the left stick's edge of ten Steering layers the chord with Invert Activation goes, and the cleanup press
    and its empty guard chord come back as 90.54 had them. On 90.55 a thumb lifting in the stick modifiers
    cleared the W or S layer; the author suspects the inverted chord fires after a remove_layer call although a
    bumper is held. The timers' Soft Press of 90.55 stays, stored after the cleanup."""
    layout, before, changed = Layout(data), Layout(readable('90.54', variant)), []
    for title in (map_title(t, RENAME) if variant == 'alternative' else t for t in EDGES):
        edge = layout.active(title)['joystick']['inputs']['edge']
        found = edge['activators']
        chord = found['chord']
        assert set(found) <= {'chord', 'Soft_Press'} and chord['settings']['edge_binding_invert'] == '1', (title, set(found))
        old = before.active(title)['joystick']['inputs']['edge']['activators']
        press = old['Full_Press']
        guard = next(e for kind, e in entries(old) if kind == 'chord' and actions(e) == [EMPTY + ', , '])
        assert press['settings'].get('hold_repeats') == '1' and press['settings'].get('interruptable') != '0', title
        assert actions(press) == actions(chord), title               # the same list, in the same order
        assert all(guard['settings'][key] == chord['settings'][key] for key in guard['settings'] if key.startswith('gyro_')), title
        edge['activators'] = {'Full_Press': copy.deepcopy(press), 'chord': copy.deepcopy(guard),
                              **{kind: entry for kind, entry in found.items() if kind == 'Soft_Press'}}
        changed.append(title)
    kept = layout.active(GUARD)['joystick']['inputs']['edge']['activators']
    assert kept['chord']['settings']['edge_binding_invert'] == '1'   # the Entry Guard: as it is
    return changed


def build(variant):
    data = readable('90.55', variant)
    title = data['controller_mappings']['title']
    changed = {'edge cleanups': edge_cleanups(data, variant)}
    before = copy.deepcopy(data)
    fixes = apply_all(data)
    data['controller_mappings']['title'] = title.rsplit(' :: ', 1)[0] + ' :: 90.56'
    final, _ = titles_to_ids(json.dumps(data, indent='\t') + '\n', generate_lookup(data))
    assert '{{' not in final
    return final, {'changed': changed, 'fixes': fixes, 'pipeline changed the layout': data != {**before, 'controller_mappings': {
        **before['controller_mappings'], 'title': data['controller_mappings']['title']}}}


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
        print(variant, {k: len(v) for k, v in report['changed'].items()},
              'pipeline changed the layout:', report['pipeline changed the layout'])


if __name__ == '__main__':
    main()
