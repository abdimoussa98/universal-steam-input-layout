"""90.53: the Steering stick's timers sit on the drivers, its entry carries no cleanup, and the left edge cleans up with one inverted chord."""

import argparse
import copy
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from steam_layout.cleanups import Cleanups  # noqa: E402
from steam_layout.fixes import apply_all  # noqa: E402
from steam_layout.model import EMPTY, Layout, actions, entries, map_title  # noqa: E402
from tools.convert_runtime_ids import generate_lookup, ids_to_titles, titles_to_ids  # noqa: E402

RENAME = {'L1': 'L2', 'R1': 'R2'}
DEFLECT = 1 << 30                # the left stick's deflect in a chord's button mask
CHORD_BUTTONS = ('gyro_ratchet_button_mask', 'gyro_ratchet_button_requireany_or_all', 'chord_button')
MARKER, COVER = 'Steering | LS: Tap Cover', 'Steering | LS: Double Tap Cover'
DRIVERS = ('Steering | R1: W Key', 'Steering | L1: S Key')
# stick modifier, its direction
SIDES = (('Steering | LS Up: Modifier 1', 'dpad_north'), ('Steering | LS Down: Modifier 0', 'dpad_south'))
STICK_MODIFIERS = tuple(side[0] for side in SIDES)
MODIFIER_2 = ('Steering | R1!L1: Modifier 2', 'Steering | L1!R1: Modifier 2')
SCROLLS = ('Steering | LS Up: Scroll Up', 'Steering | LS Down: Scroll Down')
WINDOWS = ('Steering | LS Up: Double Tap', 'Steering | LS Down: Double Tap')
EDGE_CLEANUPS = (*DRIVERS, *STICK_MODIFIERS, MARKER, COVER, *SCROLLS, *MODIFIER_2)     # the ten layers of part 6
DEFAULT_RADIUS = (*EDGE_CLEANUPS[:8], *WINDOWS)                                         # the ten groups that stated 13276
RTP = 'controller_action remove_layer {{Base::RTP: '
FULL_CLEAR = 50          # a Release with more removes than this is the Modifier 2 clear to Base (R159): left alone


def command(op, title):
    return f'controller_action {op}_layer {{{{Base::{title}}}}} 0 0, , '


def named(variant, titles):
    return [map_title(t, RENAME) if variant == 'alternative' else t for t in titles]


def stick(layout, title):
    return layout.active(title)['joystick']['inputs']


def entry_step(data, variant):
    """Part 1: up and down in the W and S layers add the stick modifier with one chord and carry no cleanup.

    The chord needs the driver and the left stick's deflect, both (author, 2026-10-10). The deflect alone was
    the first decision: with a driver's release missed and the stick held out, a button's cleanup in the stick
    modifier then removed the modifier and the W layer's up added it again, without end. The stick modifiers'
    stick clicks already chord on the same two."""
    layout, changed = Layout(data), []
    for driver in named(variant, DRIVERS):
        inputs = stick(layout, driver)
        for modifier, own in SIDES:
            found = inputs[own]['activators']
            assert set(found) == {'Full_Press', 'chord'}, (driver, own)
            chord = found['chord']
            assert actions(chord) == [command('add', modifier)]
            assert chord['settings']['hold_repeats'] == '1' and chord['settings']['interruptable'] == '0'
            assert command('remove', driver) in actions(found['Full_Press'])            # the cleanup that goes
            mask = int(chord['settings']['gyro_ratchet_button_mask'])
            assert bin(mask).count('1') == 1 and chord['settings']['gyro_ratchet_button_requireany_or_all'] == '0'
            chord['settings'].update(gyro_ratchet_button_mask=str(mask | DEFLECT), gyro_ratchet_button_requireany_or_all='1')
            inputs[own]['activators'] = {'chord': chord}
            changed.append(f'{driver} {own}')
    return changed


def right_pad_clears(data, variant):
    """Part 3: no right pad removes in the four Steering modifier layers, apart from the Modifier 2 clear to Base."""
    layout, changed = Layout(data), []
    for title in named(variant, STICK_MODIFIERS + MODIFIER_2):
        for source, group in layout.active(title).items():
            for name, value in group.get('inputs', {}).items():
                for kind, one in entries(value.get('activators', {})):
                    binding = actions(one)
                    pads = [b for b in binding if b.startswith(RTP)]
                    if not pads:
                        continue
                    if kind == 'release' and len(binding) > FULL_CLEAR:
                        continue
                    touch = kind == 'release' and source in ('joystick', 'right_joystick') and name == 'touch'
                    hold = kind == 'chord' and one.get('settings', {}).get('delay_start') == '200'
                    assert touch or hold, (title, source, name, kind)
                    kept = [b for b in binding if not b.startswith(RTP)]
                    assert kept, (title, source, name, kind)
                    one['bindings']['binding'] = kept if len(kept) > 1 else kept[0]
                    changed.append(f'{title} {source}/{name} {kind}')
    return changed


def side_keys(data):
    """Part 4: left and right in the stick modifiers send only A and D."""
    layout, changed = Layout(data), []
    for modifier in STICK_MODIFIERS:
        inputs = stick(layout, modifier)
        for name, key in (('dpad_east', 'D'), ('dpad_west', 'A')):
            press = inputs[name]['activators']['Full_Press']
            assert actions(press) == [command('add', MARKER), f'key_press {key}, , '], (modifier, name)
            press['bindings']['binding'] = f'key_press {key}, , '
            changed.append(f'{modifier} {name}')
    return changed


def default_radius(data, variant):
    """Part 6: every Steering layer's left stick uses Steam's default outer ring radius, as the Temp Cursor Gyro layers do."""
    layout, changed = Layout(data), []
    for title in layout.presets:
        if not title.startswith('Steering'):
            continue
        settings = layout.active(title)['joystick'].get('settings', {})
        if settings.pop('edge_binding_radius', None) is not None:
            changed.append(title)
    assert sorted(changed) == sorted(named(variant, DEFAULT_RADIUS)), changed
    return changed


def edge_chords(data, variant):
    """Part 6: on the left stick's edge the cleanup press and its guard become one chord with Invert Activation."""
    layout, changed = Layout(data), []
    for title in named(variant, EDGE_CLEANUPS):
        edge = stick(layout, title)['edge']
        found = edge['activators']
        assert set(found) == {'Full_Press', 'chord'}, (title, set(found))
        press, guard = found['Full_Press'], found['chord']
        assert press['settings'].get('hold_repeats') == '1' and press['settings'].get('interruptable') != '0'
        assert actions(guard) == [EMPTY + ', , '] and command('remove', title) in actions(press)
        buttons = {k: v for k, v in guard['settings'].items() if k in CHORD_BUTTONS}
        assert buttons
        edge['activators'] = {'chord': {
            'bindings': {'binding': list(actions(press))},
            'settings': {**buttons, 'edge_binding_invert': '1', 'hold_repeats': '1', 'interruptable': '0',
                         'haptic_intensity': '0'}}}
        changed.append(title)
    return changed


def timers_on_the_drivers(data, variant):
    """The hold timer and the cover timer leave the stick's direction for the two drivers.

    A start delay owned by a stick direction lands at once after one interruption (author, on the Deck,
    2026-10-10). In the two stick modifiers and the two stick scroll layers each driver now carries what its
    own layer has on it, the key and the Release, and the delayed chord on the left stick's deflect between
    them. The reset stays on the stick's direction, as in the author's test.
    """
    layout, cm, changed = Layout(data), data['controller_mappings'], []

    def own(driver):
        """(source, input, group, activators) of the input that sends the driver layer's key."""
        for source, group in layout.active(driver).items():
            for name, value in group.get('inputs', {}).items():
                found = value.get('activators', {})
                if set(found) == {'Full_Press', 'release'} and isinstance(found['Full_Press'], dict) \
                        and actions(found['Full_Press'])[0].startswith('key_press ') \
                        and command('remove', driver) in actions(found['release']):
                    return source, name, group, found
        raise AssertionError(driver)

    timers = [(modifier, direction, MARKER, '200') for modifier, direction in SIDES] + \
             [(scroll, direction, COVER, '150') for scroll, (_, direction) in zip(SCROLLS, SIDES)]
    for layer, direction, target, delay in timers:
        on_stick = stick(layout, layer)[direction]['activators']
        chord = on_stick.pop('chord')
        assert actions(chord) == [command('add', target)], (layer, actions(chord))
        assert chord['settings']['delay_start'] == delay and int(chord['settings']['gyro_ratchet_button_mask']) == DEFLECT
        assert 'release' in on_stick and 'Full_Press' in on_stick                     # the tap's end, and the reset
        for driver in named(variant, DRIVERS):
            source, name, group, found = own(driver)
            host = layout.active(layer).get(source)
            if host is None:
                host = {**{k: copy.deepcopy(v) for k, v in group.items() if k != 'inputs'},
                        'id': str(max(int(g['id']) for g in cm['group']) + 1), 'inputs': {}}
                cm['group'].append(host)
                layout.groups[host['id']] = host
                layout.presets[layer]['group_source_bindings'][host['id']] = f'{source} active'
                layout._active.pop(layer, None)
            assert not host['inputs'].get(name, {}).get('activators'), (layer, source, name)
            host['inputs'][name] = {'activators': {
                'release': copy.deepcopy(found['release']),
                'chord': {'bindings': {'binding': command('add', target)},
                          'settings': {**chord['settings'], 'haptic_intensity': '0'}},
                'Full_Press': copy.deepcopy(found['Full_Press'])}, 'disabled_activators': {}}
            changed.append(f'{layer} {source}/{name}')
    return changed


def second_driver(data, variant):
    """In the four timer layers a fresh press of the other driver enters the Modifier 2 layer at once.

    The author, 2026-10-11: with both bumpers bound in the stick modifiers "you won't be able to get into mod two
    if you're deflecting the stick". Each driver's key press there also carries what the other driver's layer has
    on that input to enter Modifier 2. A layer that lands on a held input doesn't run its immediate layer command
    (A5), so the held driver only keeps its key down; a fresh press can only be the other driver, and it runs the
    commands. Its key shows for a moment, until the Modifier 2 layer takes the input over.

    The other layer's entry removes twelve layers. Here only those that can be on the stack with the host are
    kept (R132; author, 2026-10-11: "why would we do all of the removes?"): the host and its marker or cover.
    """
    layout, changed = Layout(data), []
    stacks = Cleanups(layout)

    def own(driver):
        for source, group in layout.active(driver).items():
            for name, value in group.get('inputs', {}).items():
                found = value.get('activators', {})
                if set(found) == {'Full_Press', 'release'} and isinstance(found['Full_Press'], dict) \
                        and actions(found['Full_Press'])[0].startswith('key_press '):
                    return source, name
        raise AssertionError(driver)

    drivers = named(variant, DRIVERS)
    where = {driver: own(driver) for driver in drivers}
    for layer in (*STICK_MODIFIERS, *SCROLLS):
        for held, other in (drivers, drivers[::-1]):
            source, name = where[other]
            entry = layout.active(held)[source]['inputs'][name]['activators']['chord']
            second = [a for a in actions(entry) if a.startswith('controller_action add_layer ')]
            assert len(second) == 1 and 'Modifier 2' in second[0], (held, source, name)
            press = layout.active(layer)[source]['inputs'][name]['activators']['Full_Press']
            assert len(actions(press)) == 1 and actions(press)[0].startswith('key_press ')
            there = stacks.present(layer)
            removes = [a for a in actions(entry)
                       if a not in second and layout.layer_ops({'bindings': {'binding': a}})[0][1] in there]
            marker = MARKER if layer in STICK_MODIFIERS else COVER
            assert sorted(removes) == sorted([command('remove', layer), command('remove', marker)]), (layer, removes)
            press['bindings']['binding'] = [*actions(press), *second, *removes]
            changed.append(f'{layer} {source}/{name}')
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
    changed = {'entry': entry_step(data, variant), 'right pad clears': right_pad_clears(data, variant),
               'side keys': side_keys(data), 'default radius': default_radius(data, variant),
               'edge chords': edge_chords(data, variant), 'timers': timers_on_the_drivers(data, variant),
               'second driver': second_driver(data, variant)}
    before = copy.deepcopy(data)
    fixes = apply_all(data)
    data['controller_mappings']['title'] = cm['title'].rsplit(' :: ', 1)[0] + ' :: 90.53'
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
