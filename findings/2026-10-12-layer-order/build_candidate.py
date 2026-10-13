"""90.64: the layer list in a new order. From 90.63.

The author, 2026-10-12: "reorder all the layers keep the initial order ramp up 0, ramp up 1. then the stateful
base layers: gyro, steering, cursor gyro, menu, gamepad. then the other layer still separate by the parent
statful layers, so all the base then gyro, so on so forth. Within that group of stateful leftover layers, i want
you to determine the order yourself".

No bind, setting or group changes. The 90 layers keep their titles and their groups; `action_layers`, the preset
blocks and the `Preset_` keys are put in the new order together (R104), and every layer command, written by
title, is converted to the new positions. The builder stops unless each layer is bind for bind what it was.
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
from steam_layout.model import Layout, map_title  # noqa: E402
from tools.convert_runtime_ids import generate_lookup, ids_to_titles, titles_to_ids  # noqa: E402

BEFORE, AFTER = '90.63', '90.64'
RENAME = {'L1': 'L2', 'R1': 'R2'}                 # the alternative layout's drivers

# Default-layout titles. Inside a group: by input, and for one input in the order its gesture runs
# (Entry Point, Tap Cover, Double Tap, what the double tap gives, Double Tap Cover).
ORDER = (
    ('The ramp', (
        'Turning Ramp Up 0', 'Turning Ramp Up 1')),
    ('The stateful layers', (
        'Gyro', 'Steering', 'Cursor Gyro', 'Menu Keys', 'Gamepad')),
    ('Base: the bumpers', (
        'L1: Modifier 0', 'R1: Modifier 1', 'L1!R1: Modifier 2', 'R1!L1: Modifier 2',
        'L1: Tap Cover', 'R1: Tap Cover', 'L1&R1: Tap Cover',
        'L1: Temp Cursor Gyro', 'R1: Temp Cursor Gyro',
        'L1: Double Tap', 'R1: Double Tap', 'L1: Scroll Down', 'R1: Scroll Up',
        'L1: Double Tap Cover', 'R1: Double Tap Cover')),
    ('Base: the sticks', (
        'Gyro Off Ramp Up',
        'LST: Entry Point', 'RST: Entry Point', 'LST: Tap Cover', 'RST: Tap Cover',
        'LST: Double Tap', 'RST: Double Tap', 'LST: Temporary Gyro', 'RST: Temporary Gyro')),
    ('Base: the trackpads', (
        'RTP: Entry Point', 'RTP: Tap Cover', 'RTP: Double Tap', 'RTP: Circular Scroll',
        'LTP: Click Entry Point', 'RTP: Click Entry Point', 'LTP: Arrow Keys', 'RTP: Mouse Buttons',
        'LTP: Middle Click', 'RTP: Middle Click')),
    ('Base: the held keys', (
        'Escape', 'Tab', 'Backspace', 'Enter')),
    ('Base: the menu buttons', (
        'Menu Left: Entry Point', 'Menu Right: Entry Point',
        'Menu Buttons: Left Stick Guard', 'Menu Buttons: Right Stick Guard', 'Menu Buttons: Tap Cover',
        'Menu Left: Fn Layer', 'Menu Right: Fn Layer',
        'Menu Left: Double Tap', 'Menu Right: Double Tap', 'Menu Left: Escape', 'Menu Right: Tab',
        'Menu Left: Double Tap Cover', 'Menu Right: Double Tap Cover',
        'Menu Left!Right: Entry Point', 'Menu Left!Right: Double Tap', 'Menu Left!Right: Enter',
        'Menu Left!Right: Double Tap Cover',
        'Menu Right!Left: Entry Point', 'Menu Right!Left: Double Tap', 'Menu Right!Left: Backspace',
        'Menu Right!Left: Double Tap Cover')),
    ('Base: the transitions', (
        'Transition Set 0', 'Transition Set 1', 'Transition Set 2')),
    ('Gyro', (
        'Gyro | L1: Modifier 0', 'Gyro | R1: Modifier 1', 'Gyro | L1!R1: Modifier 2', 'Gyro | R1!L1: Modifier 2')),
    ('Steering', (
        'Steering | LS: Entry Guard',
        'Steering | R1: W Key', 'Steering | L1: S Key', 'Steering | R1!L1: Modifier 2', 'Steering | L1!R1: Modifier 2',
        'Steering | LS Up: Modifier 1', 'Steering | LS Down: Modifier 0', 'Steering | LS: Tap Cover',
        'Steering | LS Up: Double Tap', 'Steering | LS Down: Double Tap',
        'Steering | LS Up: Scroll Up', 'Steering | LS Down: Scroll Down', 'Steering | LS: Double Tap Cover')),
    ('Steering and Cursor Gyro: the menu buttons', (
        'Stateful | Menu Left: Entry Point', 'Stateful | Menu Right: Entry Point',
        'Stateful | Menu Left: Fn Layer', 'Stateful | Menu Right: Fn Layer')),
)


def readable(version, variant):
    source = ROOT / f'versions/neptune/{version}/single-set-{variant}_hold-gyro_{version}.json'
    numeric = json.loads(source.read_text())
    assert numeric['controller_mappings']['title'].endswith(f' :: {version}')
    text, _ = ids_to_titles(json.dumps(numeric), generate_lookup(numeric))
    return json.loads(text)


def order(variant):
    titles = [title for _, group in ORDER for title in group]
    return [map_title(title, RENAME) for title in titles] if variant == 'alternative' else titles


def reorder(data, variant):
    cm = data['controller_mappings']
    layers = cm['action_layers']
    by_title = {value['title']: key for key, value in layers.items()}
    wanted = order(variant)
    assert len(wanted) == len(set(wanted)) == len(layers) and set(wanted) == set(by_title), set(wanted) ^ set(by_title)
    keys = sorted(layers, key=lambda key: int(key.split('_')[1]))
    assert keys == list(layers)                                   # R104 held before
    renamed = {by_title[title]: key for title, key in zip(wanted, keys)}     # old key -> its new one
    cm['action_layers'] = {renamed[by_title[title]]: layers[by_title[title]] for title in wanted}
    sets = [preset for preset in cm['preset'] if preset['name'] not in renamed]
    assert [preset['name'] for preset in sets] == list(cm['actions']) and cm['preset'][:len(sets)] == sets
    blocks = {preset['name']: preset for preset in cm['preset'] if preset['name'] in renamed}
    assert len(blocks) == len(layers)
    cm['preset'] = sets + [blocks[by_title[title]] for title in wanted]
    for index, preset in enumerate(cm['preset']):
        preset['id'] = str(index)
        preset['name'] = renamed.get(preset['name'], preset['name'])
    return wanted


def layers_by_title(data):
    """{title: its groups, bind for bind}, with layer commands by title: the same whatever the order."""
    layout = Layout(data)
    return {title: {source: {key: value for key, value in group.items() if key != 'id'}
                    for source, group in layout.active(title).items()} for title in layout.presets}


def build(variant):
    before = readable(BEFORE, variant)
    data = copy.deepcopy(before)
    title = data['controller_mappings']['title']
    data['controller_mappings']['title'] = title.rsplit(' :: ', 1)[0] + f' :: {AFTER}'
    wanted = reorder(data, variant)
    by_hand = copy.deepcopy(data)
    apply_all(data)
    assert data == by_hand, 'the fix pipeline changed something'
    assert layers_by_title(before) == layers_by_title(data)                  # every layer is what it was
    assert data['controller_mappings']['group'] == before['controller_mappings']['group']
    final, _ = titles_to_ids(json.dumps(data, indent='\t') + '\n', generate_lookup(data))
    assert '{{' not in final
    back, _ = ids_to_titles(final, generate_lookup(json.loads(final)))
    assert json.loads(back) == data                                          # the numbers resolve to the same titles
    old = [value['title'] for value in before['controller_mappings']['action_layers'].values()]
    return final, {'order': [f'{i} (was {old.index(t) + 1}): {t}' for i, t in enumerate(wanted, 1)],
                   'moved': sum(1 for i, t in enumerate(wanted) if old[i] != t)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--install', action='store_true')
    args = parser.parse_args()
    for variant in ('default', 'alternative'):
        text, report = build(variant)
        (HERE / f'{variant}-candidate.json').write_text(text)
        (HERE / f'{variant}-build-report.json').write_text(json.dumps(report, indent=2) + '\n')
        if args.install:
            (ROOT / f'neptune/single-set-{variant}_hold-gyro_latest.json').write_text(text)
        print(variant, 'layers moved:', report['moved'])


if __name__ == '__main__':
    main()
