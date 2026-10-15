"""90.72: stick-edge cleanups on the pad layers, and pad-click stand-ins for what they hide. From 90.71.

The author, 2026-10-14 (plans/2026-10-14-pad-stick-edge-cleanups.md):

1. Every left-pad and right-pad click layer has a cleanup function on both stick edges, and the four left-pad key layers
   on the left edge only, because "not all controllers that might use this layout will have stick touch". Each edge
   copies the layer's stick-touch cleanup: the same repeating removal and list, guarded by the pad's touch (legacy chord
   IDs 16 and 17). The right pad's touch layers get none.
2. While a pad layer is on with its thumb on the pad, its guard hides the other stick's edge below it. Cleanups and
   cancellations may wait. What would be lost is done on the pad's click instead, by the layer that owns it: a stick
   timer that adds a cover adds that cover on the click, and the ramp layers remove themselves on the left pad's click
   and add its Click Entry Point. Each cover that a click can add binds that pad's click as Base does, so the click carries on into
   its Click Entry Point. Every stand-in is silent. The L1/R1 modifiers get none: their stick-edge chords need the other
   stick deflected too, which a thumb on a pad rules out.
3. The menu Entry Points, and the two menu chord layers that can also land on Base, block both pad clicks, and the
   left pad's swipes type their keys, as the windows do (R172).
4. Every layer that blocks the right pad's click binds its touch to a Release that removes the right pad's touch layers;
   a window removes itself first, no other layer does.
"""

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
from steam_layout.fixes.window_pads import cleared, swipe_keys  # noqa: E402
from steam_layout.model import EMPTY, Layout, actions, always_on_layers, entries, map_title  # noqa: E402
from tools.convert_runtime_ids import generate_lookup, ids_to_titles, titles_to_ids  # noqa: E402

BEFORE, AFTER = '90.71', '90.72'
STICKS = ('joystick', 'right_joystick')
LP, RP = 'left_trackpad', 'right_trackpad'
# layer: (its pad's touch guard, the stick edges that get a cleanup)
EDGES = {**{t: ('16', STICKS) for t in ('LTP: Click Entry Point', 'LTP: Arrow Keys', 'LTP: Middle Click')},
         **{t: ('16', ('joystick',)) for t in ('Escape', 'Tab', 'Backspace', 'Enter')},
         **{t: ('17', STICKS) for t in ('RTP: Click Entry Point', 'RTP: Mouse Buttons', 'RTP: Middle Click')}}
# layer: [(pad, what its click does)], in default-layout names. A stand-in completes what the stick would have done.
COVER_ON_CLICK = {
    'Steering | LS Up: Modifier 1': [(RP, 'Steering | LS: Tap Cover')],
    'Steering | LS Down: Modifier 0': [(RP, 'Steering | LS: Tap Cover')],
    'Steering | LS Up: Scroll Up': [(RP, 'Steering | LS: Double Tap Cover')],
    'Steering | LS Down: Scroll Down': [(RP, 'Steering | LS: Double Tap Cover')],
}
RAMPS = ('Gyro Off Ramp Up', 'Turning Ramp Up 0', 'Turning Ramp Up 1')
TOUCH_LAYERS = ('RTP: Entry Point', 'RTP: Tap Cover', 'RTP: Double Tap', 'RTP: Circular Scroll')
MENU_ENTRIES = ('Menu Left: Entry Point', 'Menu Right: Entry Point',
                'Stateful | Menu Left: Entry Point', 'Stateful | Menu Right: Entry Point',
                # These two can also land straight on Base; with the blocks they match the rest of the menu chain.
                'Menu Left!Right: Enter', 'Menu Right!Left: Backspace')


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


class Build:
    def __init__(self, data, variant):
        self.data, self.cm = data, data['controller_mappings']
        self.name = (lambda t: map_title(t, {'L1': 'L2', 'R1': 'R2'})) if variant == 'alternative' else (lambda t: t)
        self.log = []

    def layout(self):
        return Layout(self.data)

    def pad_group(self, title, pad):
        """The layer's group on a pad: a new layered group in Base's mode, with no inputs, if it has none."""
        layout = self.layout()
        group = layout.active(title).get(pad)
        if group:
            return group
        base = layout.active(layout.base)[pad]
        gid = str(max(int(g['id']) for g in self.cm['group']) + 1)
        group = {'id': gid, 'mode': base['mode'], 'name': '', 'description': '', 'settings': {'layer': '1'},
                 'inputs': {}}
        self.cm['group'].append(group)
        key = next(k for k, v in self.cm['action_layers'].items() if v['title'] == title)
        next(p for p in self.cm['preset'] if p['name'] == key)['group_source_bindings'][gid] = f'{pad} active'
        return group

    def bind_click(self, title, pad, entry, why):
        group = self.pad_group(title, pad)
        assert 'click' not in group['inputs'], (title, pad)
        group['inputs']['click'] = {'activators': {'Soft_Press': entry}, 'disabled_activators': {}}
        self.log.append(f'{title} / {pad}/click: {why}')

    def edges(self):
        layout = self.layout()
        removes = 0
        for layer, (guard, sticks) in EDGES.items():
            for stick in sticks:
                group = layout.active(layer)[stick]
                assert group['settings'].get('layer') == '1' and 'edge' not in group['inputs'], (layer, stick)
                touch = group['inputs']['touch']['activators']
                press, chord = touch['Full_Press'], touch['chord']
                assert set(touch) == {'Full_Press', 'chord', 'release'} and press['settings'] == {'hold_repeats': '1'}
                assert chord['settings'] == {'chord_button': guard, 'interruptable': '0'}, (layer, stick)
                ops = layout.layer_ops(press)
                assert ops[0] == ('remove_layer', layer) and all(op == 'remove_layer' for op, _ in ops)
                group['inputs']['edge'] = {'activators': {'Full_Press': copy.deepcopy(press),
                                                          'chord': copy.deepcopy(chord)}}
                removes += len(ops)
                self.log.append(f'{layer} / {stick}/edge: cleanup removing {[t for _, t in ops]}, guard {guard}')
        return removes

    def trim_entry_point(self):
        """`RTP: Entry Point`'s right-edge cleanup named `RTP: Click Entry Point`. That layer now answers the right edge
        itself whenever it is on top, so the remove can never take it off (R132, the author's goal of no removes that
        never fire)."""
        layout = self.layout()
        title = 'RTP: Entry Point'
        press = layout.active(title)['right_joystick']['inputs']['edge']['activators']['Full_Press']
        stored = press['bindings']['binding']
        target = cmd('remove_layer', 'RTP: Click Entry Point')
        if target in stored:
            press['bindings']['binding'] = [a for a in stored if a != target]
            self.log.append(f'{title} / right_joystick/edge: no longer removes RTP: Click Entry Point')
            return 1
        return 0

    def stand_ins(self):
        layout = self.layout()
        base_click = {pad: layout.active(layout.base)[pad]['inputs']['click']['activators']['Soft_Press']
                      for pad in (LP, RP)}
        covers = set()
        for owner, clicks in COVER_ON_CLICK.items():
            owner = self.name(owner)
            for pad, cover in clicks:
                cover = self.name(cover)
                self.bind_click(owner, pad, {'bindings': {'binding': cmd('add_layer', cover)},
                                             'settings': {'haptic_intensity': '0'}}, f'adds {cover}, silent')
                covers.add((cover, pad))
        for cover, pad in sorted(covers):
            self.bind_click(cover, pad, copy.deepcopy(base_click[pad]), "as Base's: adds the pad's Click Entry Point")
        for ramp in RAMPS:
            # The removes run first, then the Click Entry Point is added (stored last runs first, A4), so the click
            # carries on whether or not Steam fires Base's exposed add (A9).
            ops = [cmd('add_layer', 'LTP: Click Entry Point')] + [cmd('remove_layer', r) for r in reversed(RAMPS)]
            self.bind_click(ramp, LP, {'bindings': {'binding': ops}, 'settings': {'haptic_intensity': '0'}},
                            'removes the three ramp layers, then adds LTP: Click Entry Point, silent')
        return len(covers)

    def menu_entries(self):
        layout = self.layout()
        base, keys = swipe_keys(layout)
        for title in MENU_ENTRIES:
            title = self.name(title)
            left = self.pad_group(title, LP)
            assert not left['inputs'] and left['mode'] == base['mode']
            left['settings'] = {'layer': '1', **copy.deepcopy(base.get('settings', {}))}
            left['inputs'] = {'click': cleared(), 'touch': cleared()}
            for direction, (key, settings) in keys.items():
                left['inputs'][direction] = {'activators': {'Full_Press': {'bindings': {'binding': key},
                                                                           'settings': copy.deepcopy(settings)}},
                                             'disabled_activators': {}}
            right = self.pad_group(title, RP)
            assert not right['inputs']
            right['inputs']['click'] = cleared()
            self.log.append(f'{title}: both pad clicks blocked, the left swipes type their keys, the left touch cleared')

    def right_touch_releases(self):
        """Every layer that blocks the right pad's click binds the pad's touch to a Release that removes the right pad's
        touch layers (author, 2026-10-14). The touch is then defined, so Base's touch press (`RTP: Entry Point`) does not
        come through: no tap, double tap or Circular Scroll opens over the layer. A window removes itself first (R146);
        no other layer does, so a right-thumb lift never ends a menu hold or the Entry Guard. The cleanup rules trim
        each list to what can be on the stack (R132). `RTP: Double Tap` is one of the touch layers itself."""
        layout = self.layout()
        windows = set(always_on_layers(layout))
        below = Cleanups(layout).below
        touch_layers = [self.name(t) for t in TOUCH_LAYERS]
        for title in layout.presets:
            group = layout.active(title).get(RP)
            click = ((group or {}).get('inputs') or {}).get('click', {}).get('activators') or {}
            if not click or not all(a.startswith(EMPTY) for _, e in entries(click) for a in actions(e)):
                continue
            if title in touch_layers:
                continue
            under = [t for t in touch_layers if t in below(title)]
            if not under and title not in windows:
                # Nothing to clean: `Steering | LS: Entry Guard`, whose touch block already keeps the tap chain out.
                self.log.append(f'{title} / right_trackpad/touch: kept, no touch layer can be under it')
                continue
            run = ([title] if title in windows else []) + under
            have = (group['inputs'].get('touch', {}).get('activators') or {})
            if set(have) == {'release'} and layout.layer_ops(have['release']) == [('remove_layer', t) for t in run]:
                continue                                                  # a window that has this already
            entry = {'bindings': {'binding': [cmd('remove_layer', t) for t in reversed(run)]},
                     'settings': {'haptic_intensity': '0'}}
            group['inputs']['touch'] = {'activators': {'release': entry}, 'disabled_activators': {}}
            self.log.append(f'{title} / right_trackpad/touch: Release removes {run}')


def build(variant):
    before = readable(BEFORE, variant)
    data = copy.deepcopy(before)
    title = data['controller_mappings']['title']
    data['controller_mappings']['title'] = title.rsplit(' :: ', 1)[0] + f' :: {AFTER}'
    b = Build(data, variant)
    removes = b.edges()
    trimmed = b.trim_entry_point()
    covers = b.stand_ins()
    b.menu_entries()
    b.right_touch_releases()
    assert removes == 3 * 2 + 4 + 3 * 4 * 2, removes
    adds = sum(len(v) for v in COVER_ON_CLICK.values())
    assert count(data, 'remove_layer') >= count(before, 'remove_layer') + removes + 3 * len(RAMPS) - trimmed
    assert count(data, 'add_layer') == count(before, 'add_layer') + adds + covers + len(RAMPS)
    by_hand = copy.deepcopy(data)
    fixes = apply_all(data)
    final, _ = titles_to_ids(json.dumps(data, indent='\t') + '\n', generate_lookup(data))
    assert '{{' not in final
    return final, {'changed': b.log,
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
