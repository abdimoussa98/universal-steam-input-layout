"""Ibex 1.1: the Fn layers take over from the Entry Points. From Ibex 1.0.

The author, 2026-10-16, on the Fn layers' right stick, which types nothing on the Deck: "fn is always going to
inherit from entry point for that stick since we've changed the mod from base so we cant have base = mouse -> entry
= dpad -> fn = dpad, and expect a partial inheritence in the fn layer. its just inheriting everything" (A77). The
design, same day: "the entrypoint layers will just inherit the left and right stick modes and just override the stick
clicks for the appropriate fn layers and the edge binds to add the stick guards (which will also just have the
sticks inherited). The fn layers will have the stick click with the correct transition layer and the correct binds
for the stick binds up, down, left, & right. the layers above do not need to be duplicated. Also on fn being apply
we'll remove the stick guards and the entry point layers." (plans/2026-10-16-fn-right-stick-owner.md)

1. No `requires_click` on a stick D-pad: 28 groups, seven of which become mouse groups in 3.
2. `deadzone` 13276 on both sticks of the four Fn layers and on the left stick of the six Entry Points.
3. The hand-over. The four Entry Points' right stick is a mouse group, as Base's, with its edge at 21000, and so is
   the right stick of both stick guards and the Tap Cover. Each Entry Point's stick click adds its Fn layer at the
   press: a Regular Press, silent, not interruptible, repeating every 50 ms ("no bump on this and make it
   repeating"). All six adders of an Fn layer remove its Entry Point after their adds; the two clicks also remove
   both guards and the Tap Cover. The Fn layers get the Entry Point's two click Releases (the transitions) and
   copies of its two trackpad groups, and each stick key's click guard is one Any chord on both stick clicks ("just
   make the guard an any both of the stick clicks").
4. One Any chord where two chords on an input differ only in their button ("we should just have one bind that is
   an any", "yeah lets also make the change for the other layers"): 84 inputs.

Then the fix pipeline.
"""

import argparse
import copy
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from steam_layout import controllers, convert  # noqa: E402
from steam_layout.fixes import apply_all  # noqa: E402
from steam_layout.model import EMPTY, Layout, actions, entries, map_title  # noqa: E402

BEFORE, AFTER = '1.0', '1.1'
STICKS = ('joystick', 'right_joystick')
PADS = ('left_trackpad', 'right_trackpad')
DIRECTIONS = ('dpad_north', 'dpad_south', 'dpad_east', 'dpad_west')
FN = {'Menu Left: Fn Layer': 'Menu Left: Entry Point', 'Menu Right: Fn Layer': 'Menu Right: Entry Point',
      'Stateful | Menu Left: Fn Layer': 'Stateful | Menu Left: Entry Point',
      'Stateful | Menu Right: Fn Layer': 'Stateful | Menu Right: Entry Point'}      # each Fn layer: its Entry Point
COMBO = ('Menu Left!Right: Entry Point', 'Menu Right!Left: Entry Point')
GUARDS = ('Menu Buttons: Left Stick Guard', 'Menu Buttons: Right Stick Guard')
TAP_COVER = 'Menu Buttons: Tap Cover'
DEADZONE = '13276'
MOUSE = {'edge_binding_radius': '21000', 'edge_binding_invert': '0', 'layer': '1'}
CLICK_PRESS = {'hold_repeats': '1', 'repeat_rate': '50', 'haptic_intensity': '0', 'interruptable': '0'}
CLICK_GUARDS = {'joystick': '9', 'right_joystick': '20'}         # each Fn stick key's guard today: its own click
CHORD_KEYS = ('chord_button', convert.MASK, convert.ANY_OR_ALL)
MERGED = {'Menu Left: Fn Layer': 18, 'Menu Right: Fn Layer': 18, 'Stateful | Menu Left: Fn Layer': 18,
          'Stateful | Menu Right: Fn Layer': 18, 'Menu Left!Right: Entry Point': 2, 'Menu Right!Left: Entry Point': 2,
          'L1!R1: Modifier 2': 2, 'R1!L1: Modifier 2': 2, 'Gyro | L1!R1: Modifier 2': 2,
          'Gyro | R1!L1: Modifier 2': 2}                                 # part 4, by default-layout title


def bit(chord_button):
    """The mask bit of a legacy `chord_button` ID (resources/Neptune Chorded Button Ids.md)."""
    return convert.BITS[convert.CHORD_INPUTS[chord_button]]


def mask(*chord_buttons):
    return str(sum(1 << bit(button) for button in chord_buttons))


def any_chord(settings, value):
    """Chord settings on the mask `value`, Any, in place of `chord_button`; the other settings as they were."""
    result = {}
    for key, setting in settings.items():
        if key == 'chord_button':
            result[convert.MASK], result[convert.ANY_OR_ALL] = value, '0'
        elif key not in (convert.MASK, convert.ANY_OR_ALL):
            result[key] = setting
    return result


def command(layout, op, title):
    return f'controller_action {op} {{{{{layout.base}::{title}}}}} 0 0, , '


def set_binding(entry, commands):
    entry.setdefault('bindings', {})['binding'] = commands[0] if len(commands) == 1 else commands


def count(data, wanted):
    layout = Layout(data)
    return sum(1 for title in layout.presets for group in layout.active(title).values()
               for value in group.get('inputs', {}).values() for _, entry in entries(value.get('activators') or {})
               for op, _ in layout.layer_ops(entry) if op == wanted)


def no_requires_click(data):
    """Part 1: `requires_click` off every stick D-pad group."""
    layout, log = Layout(data), []
    for title, preset in layout.presets.items():
        for gid, state in preset['group_source_bindings'].items():
            source = state.split(' ')[0]
            group = layout.groups[gid]
            if source in STICKS and group['mode'] == 'dpad' and 'requires_click' in (group.get('settings') or {}):
                assert group['settings'].pop('requires_click') == '0', (title, source)
                log.append(f'{title} / {source}')
    assert len(log) == 28, len(log)
    return log


def deadzones(data):
    """Part 2: `deadzone` 13276 on both sticks of the Fn layers and on the left stick of the six Entry Points."""
    layout, log = Layout(data), []
    names = [(fn, stick) for fn in FN for stick in STICKS] + [(ep, 'joystick') for ep in (*FN.values(), *COMBO)]
    for title, source in names:
        group = layout.active(title)[source]
        assert group['mode'] == 'dpad' and 'deadzone' not in group['settings'], (title, source)
        group['settings']['deadzone'] = DEADZONE
        log.append(f'{title} / {source}')
    for title in COMBO:
        assert layout.active(title)['right_joystick']['settings']['deadzone'] == DEADZONE, title
    return log


def to_mouse(group, where):
    """A stick group in Base's mode (mouse), its binds kept, with the Entry Point's edge (part 3)."""
    assert group['mode'] == 'dpad', where
    for direction in DIRECTIONS:
        value = group['inputs'].pop(direction, None)
        found = [] if value is None else list(entries(value['activators']))
        assert value is None or ([kind for kind, _ in found] == ['Full_Press'] and actions(found[0][1]) == [EMPTY + ', , ']
                                 and not found[0][1].get('settings')), (where, direction)
    group['mode'] = 'joystick_mouse'
    group['settings'] = dict(MOUSE)


def hand_over(data):
    """Part 3."""
    layout, log = Layout(data), []
    cm = data['controller_mappings']
    releases = {}
    for fn, ep in FN.items():
        groups = layout.active(ep)
        # Every bind that adds the Fn layer removes the Entry Point after its adds.
        adders = []
        for source, group in groups.items():
            for name, value in (group.get('inputs') or {}).items():
                for kind, entry in entries(value.get('activators') or {}):
                    if ('add_layer', fn) in layout.layer_ops(entry):
                        commands = list(actions(entry))
                        first = next(i for i, a in enumerate(commands) if 'controller_action add_layer' in a)
                        set_binding(entry, commands[:first] + [command(layout, 'remove_layer', ep)] + commands[first:])
                        adders.append(f'{source}/{name} {kind}')
        assert sorted(adders) == ['joystick/touch release', 'right_joystick/touch release', 'switch/button_escape chord',
                                  'switch/button_menu chord'], (ep, adders)
        # The stick clicks: the transition Release goes to the Fn layer, a press that adds Fn takes its place.
        for stick in STICKS:
            click = groups[stick]['inputs']['click']['activators']
            assert list(click) == ['release'] and not click['release'].get('settings'), (ep, stick)
            releases[fn, stick] = copy.deepcopy(click['release'])
            press = [command(layout, 'remove_layer', title) for title in (TAP_COVER, GUARDS[1], GUARDS[0], ep)]
            groups[stick]['inputs']['click']['activators'] = {
                'Full_Press': {'bindings': {'binding': press + [command(layout, 'add_layer', fn)]},
                               'settings': dict(CLICK_PRESS)}}
            adders.append(f'{stick}/click Full_Press')
        to_mouse(groups['right_joystick'], ep)
        log.append(f'{ep}: right stick in mouse mode; both stick clicks add {fn}; {len(adders)} adders hand over')
    for title in (*GUARDS, TAP_COVER):
        group = layout.active(title)['right_joystick']
        assert not set(group['inputs']) & set(DIRECTIONS), title
        to_mouse(group, title)
        log.append(f'{title}: right stick in mouse mode')
    next_id = max(int(group['id']) for group in cm['group']) + 1
    for fn, ep in FN.items():
        groups = layout.active(fn)
        for stick in STICKS:
            group = groups[stick]
            assert 'click' not in group['inputs'], (fn, stick)
            for direction in DIRECTIONS:
                key, guard = group['inputs'][direction]['activators']['chord']
                assert key['settings']['chord_button'] != CLICK_GUARDS[stick], (fn, stick)
                assert guard == {'bindings': {'binding': EMPTY + ', , '},
                                 'settings': {'chord_button': CLICK_GUARDS[stick], 'interruptable': '0'}}, (fn, stick)
                guard['settings'] = any_chord(guard['settings'], mask(*CLICK_GUARDS.values()))
            group['inputs']['click'] = {'activators': {'release': releases[fn, stick]}, 'disabled_activators': {}}
        preset = layout.presets[fn]
        for pad in PADS:
            assert pad not in groups, (fn, pad)
            group = copy.deepcopy(layout.active(ep)[pad])
            group['id'] = str(next_id)
            next_id += 1
            cm['group'].append(group)
            preset['group_source_bindings'][group['id']] = f'{pad} active'
        log.append(f'{fn}: one click guard on both stick clicks; the click Releases of {ep}; its two trackpad groups')
    return log


def any_chords(data):
    """Part 4: two chords on one input with the same bind and settings, each on one button, become one Any chord."""
    layout, found = Layout(data), {}
    for title in layout.presets:
        for source, group in layout.active(title).items():
            for name, value in (group.get('inputs') or {}).items():
                activators = value.get('activators') or {}
                chords = activators.get('chord')
                if not isinstance(chords, list):
                    continue
                shapes = {}
                for chord in chords:
                    settings = chord.get('settings') or {}
                    if 'chord_button' not in settings or convert.MASK in settings:
                        continue
                    shape = json.dumps([actions(chord), {k: v for k, v in settings.items() if k not in CHORD_KEYS}])
                    shapes.setdefault(shape, []).append(chord)
                merged = [same for same in shapes.values() if len(same) > 1]
                if not merged:
                    continue
                for same in merged:
                    assert len(same) == 2, (title, source, name)
                    first, other = same
                    value_ = mask(first['settings']['chord_button'], other['settings']['chord_button'])
                    first['settings'] = any_chord(first['settings'], value_)
                    chords.remove(other)
                activators['chord'] = chords[0] if len(chords) == 1 else chords
                found.setdefault(title, []).append(f'{source}/{name}')
    variant = 'alternative' if 'alternative' in data['controller_mappings']['title'] else 'default'
    expected = {map_title(title, {'L1': 'L2', 'R1': 'R2'}) if variant == 'alternative' else title: n
                for title, n in MERGED.items()}
    assert {title: len(inputs) for title, inputs in found.items()} == expected, found
    return found


def build(variant):
    source = controllers.IBEX.snapshot(variant, BEFORE)
    numeric = json.loads(source.read_text())
    assert numeric['controller_mappings']['title'].endswith(f' :: {BEFORE}')
    before = convert.readable(numeric)
    data = copy.deepcopy(before)
    cm = data['controller_mappings']
    cm['title'] = cm['title'].rsplit(' :: ', 1)[0] + f' :: {AFTER}'
    parts = {'1 requires_click off': no_requires_click(data), '2 deadzone 13276': deadzones(data),
             '3 hand-over': hand_over(data)}
    merged = any_chords(data)
    parts['4 one Any chord'] = {title: len(inputs) for title, inputs in merged.items()}
    by_hand = copy.deepcopy(data)
    counts = {'by hand': {'removes': count(by_hand, 'remove_layer'), 'adds': count(by_hand, 'add_layer')}}
    fixes = apply_all(data)
    final = convert.dumps(data)
    counts[BEFORE] = {'removes': count(before, 'remove_layer'), 'adds': count(before, 'add_layer')}
    counts[AFTER] = {'removes': count(data, 'remove_layer'), 'adds': count(data, 'add_layer')}
    return final, {'from': f'ibex {BEFORE}', 'version': AFTER, 'parts': parts, 'merged': merged, 'counts': counts,
                   'fixes': fixes, 'pipeline changed the layout': data != by_hand}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--install', action='store_true')
    args = parser.parse_args()
    for variant in controllers.VARIANTS:
        text, report = build(variant)
        (HERE / f'{variant}-candidate.json').write_text(text)
        (HERE / f'{variant}-build-report.json').write_text(json.dumps(report, indent=2, default=str) + '\n')
        if args.install:
            controllers.IBEX.working_json(variant).write_text(text)
        print(variant, report['version'], report['counts'], 'pipeline changed:', report['pipeline changed the layout'])


if __name__ == '__main__':
    main()
