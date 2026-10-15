"""90.71: the pad click layers work on touch again and bump only on the final layer's click. From 90.70.

The author, 2026-10-14 (plans/2026-10-14-pad-click-touch-layers.md): the layers that add a Click Entry Point on a pad
click add it with a repeating Soft Press and no haptic; the entry points stay silent; the only bump is the final layer's
`hold_layer` on the click, High. The D-pad layers have Requires Click off, and each direction and the centre get a
Release that removes the layer, like a touch Release, with no haptic. The scroll repeats in `RTP: Mouse Buttons` bump
Low. The Middle Click layers send their output on a Soft Press of its own, with no haptic, beside the `hold_layer`; both
are not interruptible. No final layer keeps the inverted repeating removal on its click.
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
from steam_layout.model import Layout, actions, entries  # noqa: E402
from tools.convert_runtime_ids import generate_lookup, ids_to_titles, titles_to_ids  # noqa: E402

BEFORE, AFTER = '90.70', '90.71'
REPEAT = '50'
HIGH = '3'
PADS = {'left_trackpad': ('LTP', 'LTP: Arrow Keys', 'LTP: Middle Click'),
        'right_trackpad': ('RTP', 'RTP: Mouse Buttons', 'RTP: Middle Click')}
ADDERS = [('Base', 'left_trackpad'), ('Base', 'right_trackpad'), ('RTP: Circular Scroll', 'right_trackpad')]
DIRECTIONS = ('dpad_north', 'dpad_south', 'dpad_east', 'dpad_west')


def cmd(op, title):
    return f'controller_action {op} {{{{Base::{title}}}}} 0 0, , '


def readable(version, variant):
    source = ROOT / f'versions/neptune/{version}/single-set-{variant}_hold-gyro_{version}.json'
    numeric = json.loads(source.read_text())
    assert numeric['controller_mappings']['title'].endswith(f' :: {version}')
    text, _ = ids_to_titles(json.dumps(numeric), generate_lookup(numeric))
    return json.loads(text)


def release(title):
    return {'bindings': {'binding': cmd('remove_layer', title)}, 'settings': {'haptic_intensity': '0'}}


def own_group(layout, layer, source):
    group = layout.active(layer)[source]
    owners = [t for t in layout.presets if any(g is group for g in layout.active(t).values())]
    assert owners == [layer], (layer, source, owners)
    return group


def final_click(group, layer):
    """The click's two Soft Presses of 90.70: the self-hold, then the inverted repeating removal."""
    soft = group['inputs']['click']['activators']['Soft_Press']
    assert isinstance(soft, list) and len(soft) == 2, layer
    hold, remove = soft
    assert actions(hold) == [cmd('hold_layer', layer)], layer
    assert actions(remove) == [cmd('remove_layer', layer)], layer
    assert remove['settings'].get('edge_binding_invert') == '1' and remove['settings'].get('hold_repeats') == '1'
    return hold


def adders(layout, changed):
    for layer, source in ADDERS:
        group = own_group(layout, layer, source)
        soft = group['inputs']['click']['activators']['Soft_Press']
        target = f'{PADS[source][0]}: Click Entry Point'
        assert isinstance(soft, dict) and actions(soft) == [cmd('add_layer', target)], (layer, source)
        assert soft['settings'].get('haptic_intensity') == '0' and 'hold_repeats' not in soft['settings']
        soft['settings'].update({'hold_repeats': '1', 'repeat_rate': REPEAT})
        changed.append(f'{layer} / {source}/click: repeating add of {target}, every {REPEAT} ms, haptic 0')


def dpad_layer(layout, source, changed):
    _, layer, _ = PADS[source]
    group = own_group(layout, layer, source)
    assert group['mode'] == 'dpad' and 'requires_click' not in group['settings']
    group['settings']['requires_click'] = '0'
    changed.append(f'{layer}: requires_click 0')
    inputs = group['inputs']
    for name in DIRECTIONS:
        acts = inputs[name]['activators']
        assert 'release' not in acts and set(acts) <= {'Full_Press', 'chord'}, (layer, name)
        acts['Full_Press']['settings']['haptic_intensity'] = '0'
        if 'chord' in acts:                                      # the scroll repeats of RTP: Mouse Buttons
            assert acts['chord']['settings'].get('hold_repeats') == '1'
            acts['chord']['settings']['haptic_intensity'] = '1'
        acts['release'] = release(layer)
        assert len(list(entries(acts))) <= 3, (layer, name)
        changed.append(f'{layer} / {name}: Full Press haptic 0{", chord repeat haptic 1" if "chord" in acts else ""},'
                       f' Release removes {layer}')
    edge = inputs['edge']['activators']
    assert list(edge) == ['Full_Press'] and actions(edge['Full_Press']) == ['controller_action empty_binding, , ']
    edge['release'] = release(layer)
    changed.append(f'{layer} / edge: Release removes {layer}')
    hold = final_click(group, layer)
    hold['settings'].update({'haptic_intensity': HIGH, 'interruptable': '0'})
    inputs['click']['activators']['Soft_Press'] = hold
    changed.append(f'{layer} / click: hold_layer haptic {HIGH}; the inverted repeating removal deleted')


def middle_layer(layout, source, changed):
    _, _, layer = PADS[source]
    group = own_group(layout, layer, source)
    click = group['inputs']['click']['activators']
    assert list(click) == ['Full_Press', 'Soft_Press'], layer
    output = click.pop('Full_Press')
    out = actions(output)
    assert len(out) == 1 and out[0].split()[0] in ('key_press', 'mouse_button'), (layer, out)
    hold = final_click(group, layer)
    hold['settings'].update({'haptic_intensity': HIGH, 'interruptable': '0'})
    click['Soft_Press'] = [{'bindings': {'binding': out[0]}, 'settings': {'haptic_intensity': '0', 'interruptable': '0'}},
                           hold]
    changed.append(f'{layer} / click: {out[0].split(",")[0]} on a Soft Press, haptic 0; hold_layer haptic {HIGH};'
                   ' the inverted repeating removal deleted')


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
    changed = []
    adders(layout, changed)
    for source in PADS:
        dpad_layer(layout, source, changed)
        middle_layer(layout, source, changed)
    removes = {BEFORE: count(before, 'remove_layer'), AFTER: count(data, 'remove_layer')}
    assert removes[AFTER] == removes[BEFORE] + 10 - 4, removes   # ten Releases in, four inverted removals out
    assert count(before, 'add_layer') == count(data, 'add_layer')
    assert count(before, 'hold_layer') == count(data, 'hold_layer') == 4
    by_hand = copy.deepcopy(data)
    fixes = apply_all(data)
    pipeline_changed = data != by_hand
    final, _ = titles_to_ids(json.dumps(data, indent='\t') + '\n', generate_lookup(data))
    assert '{{' not in final
    return final, {'changed': changed, 'removes': removes,
                   'adds': {BEFORE: count(before, 'add_layer'), AFTER: count(data, 'add_layer')},
                   'fixes': fixes, 'pipeline changed the layout': pipeline_changed}


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
        print(variant, len(report['changed']), 'changes', report['removes'], 'pipeline changed:',
              report['pipeline changed the layout'])


if __name__ == '__main__':
    main()
