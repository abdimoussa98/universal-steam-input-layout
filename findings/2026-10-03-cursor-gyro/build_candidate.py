"""The stateful Cursor Gyro layer, entered by Select plus the right-stick click.

Extends the 10-03 `OneAdd` builder; it stays frozen. Plan and the author's
decisions (2026-10-03): plans/2026-10-03-cursor-gyro-and-gamepad.md.

- **A thin layer that always sits on `Gyro`.** `Transition Set 1`'s Select
  Release, which only cleared, removes the transition, adds `Gyro` and then
  `Cursor Gyro`. The layer states the temp cursor's gyro response and no gate:
  `Gyro` underneath supplies the gate and the modifiers.
- **Three exits.** Any menu button plus any stick click (Steering's Entry
  Points, reused and renamed `Stateful | …`), the Modifier 2 quick tap (the two
  `Gyro | … Modifier 2` releases also remove it), and both sticks pushed out.
- **The both-sticks exit is only in `Cursor Gyro`.** A chord on each stick edge,
  on the other stick being out, removes the layer and nothing else. No layer on
  top is changed for it.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
from tools.audit_command_budget import audit_layout
from tools.convert_runtime_ids import generate_lookup, titles_to_ids, ids_to_titles

ONE_ADD = ROOT / 'findings/2026-10-03-base-pad-click-one-add/build_candidate.py'
spec = importlib.util.spec_from_file_location('base_pad_click_one_add', ONE_ADD)
oa = importlib.util.module_from_spec(spec); spec.loader.exec_module(oa)
pc = oa.pc
st = pc.st

CURSOR, GYRO = 'Cursor Gyro', 'Gyro'
# The response of the Temp Cursor Gyro layers, which the layer copies (author, 2026-10-03).
RESPONSE = {'gyro_precision_speed': '750', 'haptic_intensity': '0', 'flickstick_haptic_bump_per_angle': '1',
            'mouse_move_threshold': '5'}
# source: (the mask bit of the other stick's deflection, this stick's edge radius).
# The radii are the Temp Cursor Gyro parents': both sticks at about a quarter of their travel.
STICKS = {'joystick': (31, '4915'), 'right_joystick': (30, '7209')}
# The Entry Points whose clicks all lead to the clear. Steering's, now shared by every stateful layer.
RENAMED = {st.entry_point(side, steering=True): f'Stateful | Menu {side}: Entry Point' for side in st.MENU}


def stateful_entry_point(side):
    return RENAMED[st.entry_point(side, steering=True)]


class CursorGyro:
    def layer(self, name):
        super().layer(name)
        if name == st.COVER:
            # After the pad click layers, so no runtime ID shifts, and before
            # the whole-layout clear lists are generated.
            super().layer(CURSOR)

    def build_menu(self):
        super().build_menu()
        self.menu_helpers.remove(CURSOR)
        self.build_cursor()

    def build_cursor(self):
        m = self.m
        modifier = 'L1' if self.variant == 'default' else 'L2'
        temp = self.sources(f'{modifier}: Temp Cursor Gyro')['gyro']
        response = {k: v for k, v in temp['settings'].items() if k != 'layer'}
        if response != RESPONSE:
            raise ValueError(f'{modifier}: Temp Cursor Gyro: expected the response {RESPONSE}, found {response}')
        # No gate: Gyro is always underneath and supplies it, as it does for the temp layers.
        self.group(CURSOR, 'gyro', {}, response, temp['mode'])
        # As Steering: a repeating press, no Release and no delay at entry (R162).
        self.group(CURSOR, 'switch', {button: m.full(m.op('add', st.entry_point(side, steering=True)), hold_repeats=1)
                                      for side, (button, _, _) in st.MENU.items()})
        for source, (other, radius) in STICKS.items():
            # A cancellation (R135): removes only itself, repeats, uninterruptible, no guard.
            self.group(CURSOR, source, {'edge': m.inp(chord=m.entry(
                m.op('remove', CURSOR, beep=1), gyro_ratchet_button_mask=1 << other,
                gyro_ratchet_button_requireany_or_all=1, hold_repeats=1, interruptable=0, haptic_intensity=0))},
                {'edge_binding_radius': radius, 'edge_binding_invert': '0'})

        # Transition Set 1: Select enters. Gyro first; if it is already on, the add does nothing (A3).
        self.sources(st.CROSS)['switch']['inputs']['button_menu'] = m.inp(release=m.entry(
            m.seq(m.op('remove', st.CROSS), m.op('add', GYRO), m.op('add', CURSOR, beep=1)),
            haptic_intensity=st.COMMIT_HAPTIC))

        # The Modifier 2 quick tap: the Gyro pair's uncovered release clears to Base.
        left, right = ('L1', 'R1') if self.variant == 'default' else ('L2', 'R2')
        gone = m.op('remove', GYRO, beep=1).replace(' 1 0, , ', ' ')
        for name in (f'Gyro | {left}!{right}: Modifier 2', f'Gyro | {right}!{left}: Modifier 2'):
            found = [e for group in self.sources(name).values() for binding in group.get('inputs', {}).values()
                     for _, e in m.entries(binding) if any(c.startswith(gone) for c in m.commands(e))]
            if len(found) != 2:
                raise ValueError(f'{name}: expected two releases that remove Gyro, found {len(found)}')
            for e in found:
                stored = m.commands(e)
                if not stored[0].startswith(gone):
                    raise ValueError(f'{name}: expected the Gyro removal stored first, found {stored[0]}')
                # Stored second, so it runs just before Gyro itself goes.
                e['bindings']['binding'] = [stored[0], m.op('remove', CURSOR)] + stored[1:]

    def build_touch_cleanup(self):
        # Cursor Gyro inherits both stick touches from Base, as Gyro does (R116).
        everything = self.new
        self.new = [n for n in everything if n != CURSOR]
        try:
            super().build_touch_cleanup()
        finally:
            self.new = everything

    def rename(self, old, new):
        preset = self.by_title.pop(old)
        self.cm['action_layers'][preset]['title'] = new
        self.by_title[new] = preset
        self.new[self.new.index(old)] = new
        old, new = '{{Base::' + old + '}}', '{{Base::' + new + '}}'
        for group in self.cm['group']:
            for binding in group.get('inputs', {}).values():
                for _, e in self.m.entries(binding):
                    b = e['bindings']['binding']
                    e['bindings']['binding'] = ([c.replace(old, new) for c in b] if isinstance(b, list)
                                                else b.replace(old, new))

    def finish(self):
        data = super().finish()
        # After the frozen builders have finished: they find these layers by their old titles.
        for old, new in RENAMED.items():
            self.rename(old, new)
        if any('{{Base::' + old + '}}' in json.dumps(data) for old in RENAMED):
            raise ValueError('a reference to a renamed Entry Point is left')
        self.cm['title'] = self.cm['title'].replace('base pad click one add candidate', 'cursor gyro candidate')
        self.cm['description'] = (
            'Cursor Gyro candidate; device verification pending. Select plus the right-stick click enters the '
            'stateful Cursor Gyro layer, on top of Gyro. '
            'See findings/2026-10-03-cursor-gyro/README.md.')
        report = audit_layout(data)
        if report['violations']:
            raise ValueError(report['violations'])
        return data


def Builder(variant):
    return type('Concrete', (CursorGyro, type(oa.Builder(variant))), {})(variant)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--vdf', action='store_true')
    args = parser.parse_args()
    manifest = {}
    for variant in ('default', 'alternative'):
        b = Builder(variant); data = b.finish()
        readable = json.dumps(data, indent='\t') + '\n'
        numeric, count = titles_to_ids(readable, generate_lookup(data))
        if '{{' in numeric:
            raise ValueError('unresolved reference')
        restored, _ = ids_to_titles(numeric, generate_lookup(data))
        if json.loads(restored) != data:
            raise ValueError('runtime reference roundtrip')
        stem = HERE / f'{variant}-cursor-gyro'
        stem.with_suffix('.readable.json').write_text(readable)
        stem.with_suffix('.json').write_text(numeric)
        if args.vdf:
            subprocess.run(['node', str(ROOT / 'tools/convert_vdf.mjs'), str(stem.with_suffix('.json'))], check=True)
        manifest[variant] = {
            'source_sha256': hashlib.sha256(b.source.read_bytes()).hexdigest(),
            'one_add_generator_sha256': hashlib.sha256(ONE_ADD.read_bytes()).hexdigest(),
            'candidate_sha256': hashlib.sha256(numeric.encode()).hexdigest(),
            'new_layers': b.new, 'new_layer_count': len(b.new),
            'total_layer_count': len(b.cm['action_layers']),
            'renamed_layers': RENAMED,
            'resolved_references': count, 'device_status': 'UNTESTED'}
    (HERE / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')


if __name__ == '__main__':
    main()
