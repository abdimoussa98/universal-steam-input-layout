"""90.52: the Steering stick deflect follows the bumper modifier lifecycle, with a scroll layer for the second deflect."""

import argparse
import copy
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from steam_layout.fixes import apply_all  # noqa: E402
from steam_layout.model import Layout, actions, map_title  # noqa: E402
from tools.convert_runtime_ids import generate_lookup, ids_to_titles, titles_to_ids  # noqa: E402

RENAME = {'L1': 'L2', 'R1': 'R2'}
DEFLECT = {'gyro_ratchet_button_mask': '1073741824', 'gyro_ratchet_button_requireany_or_all': '0'}   # the left stick's deflect, bit 30
MARKER, COVER = 'Steering | LS: Tap Cover', 'Steering | LS: Double Tap Cover'
# modifier, its direction, the opposite one, window, new scroll layer, wheel
SIDES = (('Steering | LS Up: Modifier 1', 'dpad_north', 'dpad_south', 'Steering | LS Up: Double Tap', 'Steering | LS Up: Scroll Up', 'SCROLL_UP'),
         ('Steering | LS Down: Modifier 0', 'dpad_south', 'dpad_north', 'Steering | LS Down: Double Tap', 'Steering | LS Down: Scroll Down', 'SCROLL_DOWN'))
SCROLLS = tuple(side[4] for side in SIDES)
QUIET = {'haptic_intensity': '0'}


def command(op, title):
    return f'controller_action {op}_layer {{{{Base::{title}}}}} 0 0, , '


def wheel(step):
    return f'mouse_wheel {step}, , '


def entry(binding, **settings):
    return {'bindings': {'binding': binding}, 'settings': settings} if settings else {'bindings': {'binding': binding}}


def stick(layout, title):
    return layout.active(title)['joystick']['inputs']


def modifiers(data):
    """The timer chords on the deflect; the tap ends on the direction's own Release, not the ring's."""
    layout, changed = Layout(data), []
    for modifier, own, _, window, _, _ in SIDES:
        inputs = stick(layout, modifier)
        chord = inputs[own]['activators']['chord']
        assert chord['settings']['delay_start'] == '200' and command('add', MARKER) in actions(chord)
        assert 'release' not in inputs[own]['activators']
        for key in ('gyro_ratchet_button_mask', 'gyro_ratchet_button_requireany_or_all', 'chord_button'):
            chord['settings'].pop(key, None)
        chord['settings'] = {**DEFLECT, **chord['settings']}
        release = inputs['edge']['activators'].pop('release')
        assert set(actions(release)) == {command('add', window), command('remove', modifier), command('remove', MARKER)}
        inputs[own]['activators']['release'] = release
        changed.append(modifier)
    return changed


def marker(data):
    """The hold marker ends on up's or down's Release and carries no cleanup function on them."""
    layout = Layout(data)
    inputs = stick(layout, MARKER)
    release = inputs['edge']['activators'].pop('release')
    assert set(actions(release)) == {command('remove', MARKER)} | {command('remove', side[0]) for side in SIDES}
    release.setdefault('settings', {}).update(QUIET)
    for name in ('dpad_north', 'dpad_south'):
        assert set(inputs[name]['activators']) == {'Full_Press', 'chord'}
        inputs[name]['activators'] = {'release': copy.deepcopy(release)}
    return [MARKER]


def windows(data):
    """A window scrolls at 50 ms and closes at 150 ms; its own direction goes to the scroll layer; a lift only closes it."""
    layout, changed = Layout(data), []
    for _, own, _, window, scroll, step in SIDES:
        groups = layout.active(window)
        always = groups['switch']['inputs']['always_on_action']['activators']
        old = always['Full_Press']
        assert actions(old) == [wheel(step), command('remove', window)] and old['settings']['delay_start'] == '150'
        always['Full_Press'] = [entry(command('remove', window), delay_start='150', interruptable='0', haptic_intensity='0'),
                                entry(wheel(step), delay_start='50', interruptable='0', haptic_intensity='0')]
        press = groups['joystick']['inputs'][own]['activators']['Full_Press']
        assert actions(press) == [command('add', COVER), command('remove', window)]
        press['bindings']['binding'] = [command('add', scroll), command('remove', window)]
        for source in ('joystick', 'right_joystick'):
            lift = groups[source]['inputs']['touch']['activators']['release']
            assert wheel(step) in lift['bindings']['binding']
            lift['bindings']['binding'].remove(wheel(step))
        changed.append(window)
    return changed


def cover(data):
    """The cover repeats the scroll with no chord, ends on the direction's Release, and has no cleanup on up or down."""
    layout = Layout(data)
    inputs = stick(layout, COVER)
    del inputs['edge']['activators']['release']
    for _, own, _, _, scroll, step in SIDES:
        old = inputs[own]['activators']
        assert set(old) == {'Full_Press', 'chord', 'release'} and actions(old['chord']) == [wheel(step)]
        inputs[own]['activators'] = {
            'Full_Press': entry(wheel(step), hold_repeats='1', repeat_rate='50', interruptable='0'),
            'release': entry([command('remove', scroll), command('remove', COVER)], **QUIET)}
    return [COVER]


def scroll_layers(data, variant):
    """Two layers for the second deflect, shaped like `R1: Scroll Up`, on a copy of the cover's two stick groups."""
    cm = data['controller_mappings']
    layout = Layout(data)
    source_key = layout.presets[COVER]['name']
    drivers = [map_title(t, RENAME) if variant == 'alternative' else t for t in ('Steering | L1: S Key', 'Steering | R1: W Key')]
    made = []
    for _, own, opposite, window, scroll, step in SIDES:
        key = f"Preset_{max(int(k.split('_')[1]) for k in list(cm['actions']) + list(cm['action_layers'])) + 1}"
        cm['action_layers'][key] = {**copy.deepcopy(cm['action_layers'][source_key]), 'title': scroll}
        bindings, next_id = {}, max(int(g['id']) for g in cm['group']) + 1
        for old_id, state in layout.presets[COVER]['group_source_bindings'].items():
            group = copy.deepcopy(layout.groups[old_id])
            group['id'] = str(next_id)
            cm['group'].append(group)
            bindings[str(next_id)] = state
            next_id += 1
            cleanup = [command('remove', drivers[0]), command('remove', drivers[1]), command('remove', COVER), command('remove', scroll)]
            lift = group['inputs']['touch']['activators']
            assert set(lift) == {'Full_Press', 'chord', 'release'}
            lift['Full_Press']['bindings']['binding'] = list(cleanup)
            lift['release']['bindings']['binding'] = [*lift['release']['bindings']['binding'], command('add', COVER)]
            if state.startswith('joystick '):
                inputs = group['inputs']
                assert 'release' not in inputs['edge']['activators']        # cover() took it off before the copy
                inputs['edge']['activators']['Full_Press']['bindings']['binding'] = list(cleanup)
                inputs[own]['activators'] = {
                    'release': entry([command('add', window), command('remove', scroll)], **QUIET),
                    'chord': entry(command('add', COVER), **DEFLECT, delay_start='150', interruptable='0'),
                    'Full_Press': [entry(wheel(step), hold_repeats='1', interruptable='0'),
                                   entry(command('remove', COVER), hold_repeats='1', repeat_rate='200', interruptable='0')]}
                inputs[opposite]['activators'] = {'Full_Press': entry(command('remove', scroll), interruptable='0', hold_repeats='1')}
        cm['preset'].append({'id': str(len(cm['preset'])), 'name': key, 'group_source_bindings': bindings})
        made.append(scroll)
    return made


def removal_lists(data):
    """Every binding outside the stick family that removes the cover also removes the two scroll layers."""
    layout, changed = Layout(data), []
    own = {COVER, *SCROLLS, *(side[3] for side in SIDES)}
    for title, preset in layout.presets.items():
        if title in own:
            continue
        for gid, state in preset['group_source_bindings'].items():
            for name, item in layout.groups[gid].get('inputs', {}).items():
                for kind, value in item.get('activators', {}).items():
                    for one in value if isinstance(value, list) else [value]:
                        binding = one['bindings']['binding']
                        if isinstance(binding, list) and command('remove', COVER) in binding:
                            at = binding.index(command('remove', COVER))
                            new = [command('remove', s) for s in SCROLLS if command('remove', s) not in binding]
                            binding[at:at] = new
                            if new:
                                changed.append(f"{title} {state.split()[0]}/{name} {kind}")
                        else:
                            assert command('remove', COVER) != binding, (title, name)
    return changed


def build(variant):
    source = ROOT / f'versions/neptune/90.51/single-set-{variant}_hold-gyro_90.51.json'
    numeric = json.loads(source.read_text())
    cm = numeric['controller_mappings']
    order = list(cm['actions']) + list(cm['action_layers'])
    assert cm['title'].endswith(' :: 90.51')
    assert [p['name'] for p in cm['preset']] == order
    assert [p['id'] for p in cm['preset']] == [str(i) for i in range(len(order))]
    assert [int(k.split('_')[1]) for k in cm['action_layers']] == sorted(
        int(k.split('_')[1]) for k in cm['action_layers'])
    assert len({x['title'] for x in cm['action_layers'].values()}) == len(cm['action_layers'])
    readable, _ = ids_to_titles(json.dumps(numeric), generate_lookup(numeric))
    data = json.loads(readable)
    changed = {'modifiers': modifiers(data), 'marker': marker(data), 'windows': windows(data), 'cover': cover(data),
               'scroll layers': scroll_layers(data, variant), 'removal lists': removal_lists(data)}
    before = copy.deepcopy(data)
    fixes = apply_all(data)
    data['controller_mappings']['title'] = cm['title'].rsplit(' :: ', 1)[0] + ' :: 90.52'
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
        print(variant, {k: (len(v) if k == 'removal lists' else v) for k, v in report['changed'].items()},
              'pipeline changed the layout:', report['pipeline changed the layout'])


if __name__ == '__main__':
    main()
