"""90.55: the Steering stick's four timers are Soft Presses on the left stick's edge, the left edge cleans up with one inverted chord, and the unnecessary removes are gone."""

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
DEFLECT = 1 << 30                # the left stick's deflect in a chord's button mask
THRESHOLD = '13276'              # the timers' Soft Press: the stick's D-pad deadzone, about 40% of its travel (author, 2026-10-11)
CHORD_BUTTONS = ('gyro_ratchet_button_mask', 'gyro_ratchet_button_requireany_or_all', 'chord_button')
MARKER, COVER = 'Steering | LS: Tap Cover', 'Steering | LS: Double Tap Cover'
DRIVERS = ('Steering | R1: W Key', 'Steering | L1: S Key')
MODIFIER_2 = ('Steering | R1!L1: Modifier 2', 'Steering | L1!R1: Modifier 2')
# layer, its direction, what its timer adds, the delay
TIMERS = (('Steering | LS Up: Modifier 1', 'dpad_north', MARKER, '200'),
          ('Steering | LS Down: Modifier 0', 'dpad_south', MARKER, '200'),
          ('Steering | LS Up: Scroll Up', 'dpad_north', COVER, '150'),
          ('Steering | LS Down: Scroll Down', 'dpad_south', COVER, '150'))
STICK_MODIFIERS = tuple(row[0] for row in TIMERS[:2])
SCROLLS = tuple(row[0] for row in TIMERS[2:])
WINDOWS = ('Steering | LS Up: Double Tap', 'Steering | LS Down: Double Tap')
EDGE_CLEANUPS = (*DRIVERS, *STICK_MODIFIERS, MARKER, COVER, *SCROLLS, *MODIFIER_2)     # the ten layers of part 4
DEFAULT_RADIUS = (*EDGE_CLEANUPS[:8], *WINDOWS)                                         # the ten groups that state 13276
RTP = 'controller_action remove_layer {{Base::RTP: '
FULL_CLEAR = 50          # a Release with more removes than this is the Modifier 2 clear to Base (R159): left alone
# driver layer, the Modifier 2 its other driver enters, and the three removes of that entry with nothing to remove:
# the other order's hold marker, the other order's Modifier 2, and the layer the entry then adds (part 3)
ENTRIES = (('Steering | R1: W Key', 'Steering | R1!L1: Modifier 2', ('R1: Tap Cover', 'Steering | L1!R1: Modifier 2', 'Steering | R1!L1: Modifier 2')),
           ('Steering | L1: S Key', 'Steering | L1!R1: Modifier 2', ('L1: Tap Cover', 'Steering | R1!L1: Modifier 2', 'Steering | L1!R1: Modifier 2')))


def command(op, title):
    return f'controller_action {op}_layer {{{{Base::{title}}}}} 0 0, , '


def renamed(variant, title):
    return map_title(title, RENAME) if variant == 'alternative' else title


def named(variant, titles):
    return [renamed(variant, t) for t in titles]


def stick(layout, title):
    return layout.active(title)['joystick']['inputs']


def timers_off(data):
    """Parts 1 and 2: the delayed chord leaves the edge of the stick modifiers and up or down of the scroll layers."""
    layout, changed = Layout(data), []
    for title, own, target, delay in TIMERS:
        inputs = stick(layout, title)
        if title in STICK_MODIFIERS:                 # 90.54: the edge's third entry, with three right pad removes
            found = inputs['edge']['activators']
            assert set(found) == {'Full_Press', 'chord'} and len(found['chord']) == 2, (title, set(found))
            guard, timer = found['chord']
            assert actions(guard) == [EMPTY + ', , ']
            found['chord'] = guard
        else:                                        # as in 90.52: the direction's chord, beside the reset
            found = inputs[own]['activators']
            assert list(found) == ['release', 'chord', 'Full_Press'] and len(found['Full_Press']) == 2, (title, list(found))
            timer = found['chord']
            inputs[own]['activators'] = {kind: entry for kind, entry in found.items() if kind != 'chord'}
        assert timer['settings']['delay_start'] == delay and int(timer['settings']['gyro_ratchet_button_mask']) == DEFLECT
        assert actions(timer)[-1] == command('add', target) and all(a.startswith(RTP) for a in actions(timer)[:-1]), title
        changed.append(title)
    return changed


def timers_on(data):
    """Parts 1 and 2: each timer is one Soft Press on the left stick's edge that adds its one layer.

    The shape of turn assist's `Turning Ramp Up 0`: a Soft Press with a start delay on a stick's edge. Its own
    threshold starts it, so the outer ring radius does not move it. It is not a chord, so it does not shut off
    the edge's cleanup (A27). The reset and the Release stay on the direction, as in 90.54."""
    layout, changed = Layout(data), []
    for title, _, target, delay in TIMERS:
        edge = stick(layout, title)['edge']
        assert set(edge['activators']) == {'chord'}, (title, set(edge['activators']))
        edge['activators']['Soft_Press'] = {
            'bindings': {'binding': command('add', target)},
            'settings': {'delay_start': delay, 'activation_threshold': THRESHOLD, 'interruptable': '0'}}
        changed.append(title)
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
    assert len(changed) == 10, changed               # with the two timers of the stick modifiers: the plan's twelve
    return changed


def side_keys(data):
    """Part 5: left and right in the stick modifiers send only A and D (author, 2026-10-10)."""
    layout, changed = Layout(data), []
    for modifier in STICK_MODIFIERS:
        inputs = stick(layout, modifier)
        for name, key in (('dpad_east', 'D'), ('dpad_west', 'A')):
            press = inputs[name]['activators']['Full_Press']
            assert actions(press) == [command('add', MARKER), f'key_press {key}, , '], (modifier, name)
            press['bindings']['binding'] = f'key_press {key}, , '
            changed.append(f'{modifier} {name}')
    return changed


def driver_directions(data, variant):
    """Part 5: up and down in the W and S layers carry no cleanup press.

    That press could remove the W or S layer under a held driver (the author's fault of 2026-10-10). The chord
    that adds the stick modifier stays as it is, on the driver alone: 90.53 also asked for the deflect, on a
    lead that proved wrong."""
    layout, changed = Layout(data), []
    for driver in named(variant, DRIVERS):
        inputs = stick(layout, driver)
        for modifier, own in (row[:2] for row in TIMERS[:2]):
            found = inputs[own]['activators']
            assert set(found) == {'Full_Press', 'chord'}, (driver, own)
            assert actions(found['chord']) == [command('add', modifier)]
            assert command('remove', driver) in actions(found['Full_Press'])            # the cleanup that goes
            inputs[own]['activators'] = {'chord': found['chord']}
            changed.append(f'{driver} {own}')
    return changed


def default_radius(data, variant):
    """Part 4: every Steering layer's left stick uses Steam's default outer ring radius, as the Temp Cursor Gyro layers do."""
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
    """Part 4: on the left stick's edge the cleanup press and its guard become one chord with Invert Activation,
    the Entry Guard's pattern (author, 2026-10-10 and 2026-10-11)."""
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


def modifier_2_entries(data, variant):
    """Part 3: the Modifier 2 entry of the W and S layers loses the three removes that never have a layer to remove."""
    layout, changed = Layout(data), []
    for driver, target, unneeded in ENTRIES:
        gone = [command('remove', renamed(variant, t)) for t in unneeded]
        add = command('add', renamed(variant, target))
        found = [entry for group in layout.active(renamed(variant, driver)).values()
                 for value in group.get('inputs', {}).values()
                 for kind, entry in entries(value.get('activators', {})) if kind == 'chord' and add in actions(entry)]
        assert len(found) == 1, (driver, len(found))
        binding = actions(found[0])
        assert binding[0] == add and len(binding) == 13 and all(g in binding for g in gone), (driver, binding)   # the add is stored first and runs last
        found[0]['bindings']['binding'] = [b for b in binding if b not in gone]
        changed.append(f'{driver}: {len(binding) - 1} removes -> {len(binding) - 1 - len(gone)}')
    return changed


def build(variant, trim_entries=True):
    source = ROOT / f'versions/neptune/90.54/single-set-{variant}_hold-gyro_90.54.json'
    numeric = json.loads(source.read_text())
    cm = numeric['controller_mappings']
    order = list(cm['actions']) + list(cm['action_layers'])
    assert cm['title'].endswith(' :: 90.54')
    assert [p['name'] for p in cm['preset']] == order
    assert [p['id'] for p in cm['preset']] == [str(i) for i in range(len(order))]
    assert [int(k.split('_')[1]) for k in cm['action_layers']] == sorted(
        int(k.split('_')[1]) for k in cm['action_layers'])
    assert len({x['title'] for x in cm['action_layers'].values()}) == len(cm['action_layers'])
    readable, _ = ids_to_titles(json.dumps(numeric), generate_lookup(numeric))
    data = json.loads(readable)
    changed = {'timers off': timers_off(data), 'right pad clears': right_pad_clears(data, variant),
               'side keys': side_keys(data), 'driver directions': driver_directions(data, variant),
               'default radius': default_radius(data, variant), 'edge chords': edge_chords(data, variant),
               'timers on': timers_on(data),
               'modifier 2 entries': modifier_2_entries(data, variant) if trim_entries else []}
    before = copy.deepcopy(data)
    fixes = apply_all(data)
    data['controller_mappings']['title'] = cm['title'].rsplit(' :: ', 1)[0] + ' :: 90.55'
    final, _ = titles_to_ids(json.dumps(data, indent='\t') + '\n', generate_lookup(data))
    assert '{{' not in final
    return final, {'changed': changed, 'fixes': fixes, 'pipeline changed the layout': data != {**before, 'controller_mappings': {
        **before['controller_mappings'], 'title': data['controller_mappings']['title']}}}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--install', action='store_true')
    parser.add_argument('--keep-entry-removes', action='store_true',
                        help='write <variant>-untrimmed.json, the build before part 3 trims the Modifier 2 entries')
    args = parser.parse_args()
    for variant in ('default', 'alternative'):
        if args.keep_entry_removes:
            text, report = build(variant, trim_entries=False)
            (HERE / f'{variant}-untrimmed.json').write_text(text)
        else:
            text, report = build(variant)
            (HERE / f'{variant}-candidate.json').write_text(text)
            (HERE / f'{variant}-build-report.json').write_text(json.dumps(report, indent=2, default=str) + '\n')
            if args.install:
                (ROOT / f'neptune/single-set-{variant}_hold-gyro_latest.json').write_text(text)
        print(variant, {k: len(v) for k, v in report['changed'].items()},
              'pipeline changed the layout:', report['pipeline changed the layout'])


if __name__ == '__main__':
    main()
