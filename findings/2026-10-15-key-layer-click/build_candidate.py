"""90.73: the left pad's click in the four key layers removes the layer, and Base's click carries on. From 90.72.

The author, 2026-10-14 (plans/2026-10-14-key-layer-click-and-fn-right-stick.md, part 1): "Click should remove the layer you
are in and it should be a repeated silent soft press then by default you'll be going through the base left pad click."

In `Escape`, `Tab`, `Backspace` and `Enter` the left pad is a single-button group whose touch types the key and whose
Release removes the layer; the click was not bound, so it did nothing. Each gets a Soft Press on the click that removes
the layer itself, with Base's click settings (silent, Hold to Repeat every 50 ms) and `interruptable` 0. It is the
input's only entry, so nothing could interrupt it; not interruptible, the tools read it as the layer's exit (a cancel)
and not as a cleanup function, which would need the layer's guard. Base's repeating click then fires on
the held click (R114) and adds `LTP: Click Entry Point`, as a click from Base does.
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
from steam_layout.model import Layout, entries, map_title  # noqa: E402
from tools.convert_runtime_ids import generate_lookup, ids_to_titles, titles_to_ids  # noqa: E402

BEFORE, AFTER = '90.72', '90.73'
LP = 'left_trackpad'
KEY_LAYERS = ('Escape', 'Tab', 'Backspace', 'Enter')


def readable(version, variant):
    source = ROOT / f'versions/neptune/{version}/single-set-{variant}_hold-gyro_{version}.json'
    numeric = json.loads(source.read_text())
    assert numeric['controller_mappings']['title'].endswith(f' :: {version}')
    text, _ = ids_to_titles(json.dumps(numeric), generate_lookup(numeric))
    return json.loads(text)


def cmd(op, title):
    return f'controller_action {op} {{{{Base::{title}}}}} 0 0, , '


def count(data, wanted):
    layout = Layout(data)
    return sum(1 for title in layout.presets for group in layout.active(title).values()
               for value in group.get('inputs', {}).values() for _, entry in entries(value.get('activators') or {})
               for op, _ in layout.layer_ops(entry) if op == wanted)


def key_clicks(data):
    layout = Layout(data)
    base = layout.active(layout.base)[LP]['inputs']['click']['activators']['Soft_Press']
    assert layout.layer_ops(base) == [('add_layer', 'LTP: Click Entry Point')]
    assert base['settings'] == {'haptic_intensity': '0', 'hold_repeats': '1', 'repeat_rate': '50'}, base['settings']
    log = []
    for title in KEY_LAYERS:
        group = layout.active(title)[LP]
        assert group['mode'] == 'single_button' and 'click' not in group['inputs'], title
        group['inputs']['click'] = {'activators': {'Soft_Press': {
            'bindings': {'binding': cmd('remove_layer', title)},
            'settings': {**copy.deepcopy(base['settings']), 'interruptable': '0'}}}, 'disabled_activators': {}}
        log.append(f'{title} / left_trackpad/click: repeating silent Soft Press removes {title}')
    return log


def build(variant):
    before = readable(BEFORE, variant)
    data = copy.deepcopy(before)
    title = data['controller_mappings']['title']
    data['controller_mappings']['title'] = title.rsplit(' :: ', 1)[0] + f' :: {AFTER}'
    log = key_clicks(data)
    assert count(data, 'remove_layer') == count(before, 'remove_layer') + len(KEY_LAYERS)
    assert count(data, 'add_layer') == count(before, 'add_layer')
    by_hand = copy.deepcopy(data)
    fixes = apply_all(data)
    final, _ = titles_to_ids(json.dumps(data, indent='\t') + '\n', generate_lookup(data))
    assert '{{' not in final
    return final, {'changed': log,
                   'removes': {BEFORE: count(before, 'remove_layer'), AFTER: count(data, 'remove_layer')},
                   'adds': {BEFORE: count(before, 'add_layer'), AFTER: count(data, 'add_layer')},
                   'fixes': fixes, 'pipeline changed the layout': data != by_hand}


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
        print(variant, len(report['changed']), 'changes', report['removes'], report['adds'],
              'pipeline changed:', report['pipeline changed the layout'])


if __name__ == '__main__':
    main()
