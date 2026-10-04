"""The Gamepad layer, entered by the two same-side gestures, and the third transition.

Extends the 10-03 `CursorGyro` builder; it stays frozen. Plan and the author's
decisions (2026-10-03): plans/2026-10-03-cursor-gyro-and-gamepad.md.

- **One closed layer.** `Gamepad` binds every input, so nothing of Base or Gyro
  comes through and no layer can be added over it. The map is the archived
  Gamepad action set's.
- **Start and Select use Steam's own activators** (the author's exception to
  R108, for this layer only): an interruptible Regular Press sends the button,
  a Double Press holds it, and a Long Press is empty and swallows the tap.
- **The exit is a chord on each stick click**, on Start or Select being held.
  It runs the Entry Points' clear list and adds the clear transition. The
  Modifier 2 quick tap doesn't leave Gamepad: the bumpers and triggers are
  gamepad buttons there.
- **A third transition.** A copy of the cross transition whose two menu
  Releases both add `Gamepad`. Base's Entry Points send the same-side click
  there. It takes the title `Transition Set 0`; the clear becomes
  `Transition Set 2`, as the design numbers them.
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

CURSOR_GYRO = ROOT / 'findings/2026-10-03-cursor-gyro/build_candidate.py'
spec = importlib.util.spec_from_file_location('cursor_gyro', CURSOR_GYRO)
cg = importlib.util.module_from_spec(spec); spec.loader.exec_module(cg)
st = cg.st

GAMEPAD = 'Gamepad'
# The design's numbers: 0 same side (Gamepad), 1 cross, 2 clear. Until the frozen
# builders have finished, the clear still has the title the new layer will take.
SAME, CLEAR = 'Transition Set 0', 'Transition Set 2'
PENDING = 'Transition Set 0 (same side)'
# Both times of the native activators on Start and Select (author, 2026-10-03).
LONG_MS = DOUBLE_MS = 200
HOLD_HAPTIC = 1
# The same-side gesture of each menu button: the stick whose click leads to Gamepad.
SAME_SIDE = {'Left': 'joystick', 'Right': 'right_joystick'}
MENU_OUTPUT = {'button_escape': 'START', 'button_menu': 'SELECT'}
FACE = {'button_a': 'A', 'button_b': 'B', 'button_x': 'X', 'button_y': 'Y'}
DPAD = {'dpad_north': 'DPAD_UP', 'dpad_south': 'DPAD_DOWN', 'dpad_east': 'DPAD_RIGHT', 'dpad_west': 'DPAD_LEFT'}
# The archived Gamepad action set's map (archived/universal-layout-default__hold-gyro__latest.json).
SWITCHES = {'left_bumper': 'SHOULDER_LEFT', 'right_bumper': 'SHOULDER_RIGHT',
            'button_back_left': 'B', 'button_back_right': 'Y',
            'button_back_left_upper': 'JOYSTICK_LEFT', 'button_back_right_upper': 'A'}
STICK_CLICKS = {'joystick': 'JOYSTICK_LEFT', 'right_joystick': 'JOYSTICK_RIGHT'}
PAD_CLICKS = {'left_trackpad': 'SELECT', 'right_trackpad': 'START'}
TRIGGERS = {'left_trigger': '1', 'right_trigger': '2'}


def xinput(button):
    return f'xinput_button {button}, , '


class Gamepad:
    def layer(self, name):
        super().layer(name)
        if name == st.COVER:
            # After Cursor Gyro, so no runtime ID shifts, and before the
            # whole-layout clear lists are generated.
            super().layer(PENDING)
            super().layer(GAMEPAD)

    def build_menu(self):
        super().build_menu()
        for name in (PENDING, GAMEPAD):
            self.menu_helpers.remove(name)
        self.build_transition()
        self.build_gamepad()

    def build_transition(self):
        """The same-side transition: the cross transition's blocks, and both menu Releases enter Gamepad."""
        m = self.m
        for source, group in self.sources(st.CROSS).items():
            self.group(PENDING, source, group.get('inputs', {}), group.get('settings', {}), group['mode'])
        switches = self.sources(PENDING)['switch']['inputs']
        for button, _, _ in st.MENU.values():
            switches[button] = m.inp(release=m.entry(
                m.seq(m.op('remove', PENDING), m.op('add', GAMEPAD, beep=1)), haptic_intensity=st.COMMIT_HAPTIC))
        for side, source in SAME_SIDE.items():
            release = self.sources(st.entry_point(side))[source]['inputs']['click']['activators']['release']
            stored = m.commands(release)
            if stored[0] != m.op('add', st.CLEAR):
                raise ValueError(f'{st.entry_point(side)} {source} click: expected the clear transition added last, '
                                 f'found {stored[0]}')
            release['bindings']['binding'] = [m.op('add', PENDING)] + stored[1:]

    def build_gamepad(self):
        m = self.m
        self.group(GAMEPAD, 'button_diamond', {name: m.full(xinput(button)) for name, button in FACE.items()}, {})
        self.group(GAMEPAD, 'dpad', {name: m.full(xinput(button)) for name, button in DPAD.items()},
                   {'requires_click': '0', 'haptic_intensity_override': '0'})
        for source, output in TRIGGERS.items():
            # Analog triggers. The click and the edge are bound empty, so Base's mouse buttons
            # and the alternative layout's modifier entries can't come through.
            self.group(GAMEPAD, source, {'click': m.full(), 'edge': m.full()}, {'output_trigger': output}, 'trigger')
        # The exit: a menu button held, then a stick click. The Entry Points' whole clear, then the clear transition.
        leave = m.entry(m.seq(*self.menu_clear, m.op('add', st.CLEAR)), gyro_ratchet_button_mask=st.MENU_ANY,
                        gyro_ratchet_button_requireany_or_all=0, interruptable=0)
        for source, button in STICK_CLICKS.items():
            self.group(GAMEPAD, source, {'click': m.inp(Full_Press=m.entry(xinput(button)), chord=leave),
                                         'touch': m.full(), 'edge': m.full()}, {}, 'joystick_move')
        for source, button in PAD_CLICKS.items():
            self.group(GAMEPAD, source, {'click': m.inp(Soft_Press=m.entry(xinput(button))), 'touch': m.full()},
                       {}, 'single_button')
        self.group(GAMEPAD, 'gyro', {}, {}, 'disabled')
        # Every switch input Base or Gyro binds is bound here: the rest empty.
        switches = {name: m.full() for layer in ('Base', cg.GYRO) for name in self.sources(layer)['switch']['inputs']}
        switches.update({name: m.full(xinput(button)) for name, button in SWITCHES.items()})
        # The Regular Press only. The Double and Long Press are added in `finish`:
        # the frozen builders refuse them in a layer they build.
        switches.update({name: m.full(xinput(button)) for name, button in MENU_OUTPUT.items()})
        self.group(GAMEPAD, 'switch', switches)

    def build_native_menu(self):
        m = self.m
        switches = self.sources(GAMEPAD)['switch']['inputs']
        for name, button in MENU_OUTPUT.items():
            switches[name] = m.inp(
                Full_Press=m.entry(xinput(button)),
                Double_Press=m.entry(xinput(button), double_tap_time=DOUBLE_MS),
                Long_Press=m.entry(m.EMPTY, long_press_time=LONG_MS, haptic_intensity=HOLD_HAPTIC))

    def build_touch_cleanup(self):
        # Neither layer takes Lean's stick-touch contract: the transition copies the cross
        # transition's Releases, and Gamepad clears both touches.
        everything = self.new
        self.new = [n for n in everything if n not in (PENDING, GAMEPAD)]
        try:
            super().build_touch_cleanup()
        finally:
            self.new = everything

    def retitle(self, old, new):
        if new in self.by_title:
            raise ValueError(f'{new} is taken')
        preset = self.by_title.pop(old)
        self.cm['action_layers'][preset]['title'] = new
        self.by_title[new] = preset
        self.new = [new if name == old else name for name in self.new]
        old, new = '{{Base::' + old + '}}', '{{Base::' + new + '}}'
        for group in self.cm['group']:
            for binding in group.get('inputs', {}).values():
                for _, e in self.m.entries(binding):
                    b = e['bindings']['binding']
                    e['bindings']['binding'] = ([c.replace(old, new) for c in b] if isinstance(b, list)
                                                else b.replace(old, new))

    def finish(self):
        data = super().finish()
        # After the frozen builders have finished: they know the clear by its old title,
        # and they refuse a Long Press or a Double Press.
        self.build_native_menu()
        self.retitle(st.CLEAR, CLEAR)
        self.retitle(PENDING, SAME)
        self.cm['title'] = self.cm['title'].replace('cursor gyro candidate', 'gamepad candidate')
        self.cm['description'] = (
            'Gamepad candidate; device verification pending. Start plus the right-stick click, or Select plus '
            'the left-stick click, enters the Gamepad layer. A menu button held plus a stick click leaves it. '
            'See findings/2026-10-03-gamepad/README.md.')
        # The frozen source has older ones in other layers; the fix pipeline removes those at install.
        # `native=[]`: without the register's exception, so this reads what the layer has.
        native = sorted((row['input'], row['activation']) for row in audit_layout(data, native=[])['banned_activators']
                        if any(owner['title'] == GAMEPAD for owner in row['owners']))
        expected = sorted((name, kind) for name in MENU_OUTPUT for kind in ('Double_Press', 'Long_Press'))
        if native != expected:
            raise ValueError(f'{GAMEPAD}: expected the Long and Double Press on {expected}, found {native}')
        report = audit_layout(data)
        if report['violations']:
            raise ValueError(report['violations'])
        return data


def Builder(variant):
    return type('Concrete', (Gamepad, type(cg.Builder(variant))), {})(variant)


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
        stem = HERE / f'{variant}-gamepad'
        stem.with_suffix('.readable.json').write_text(readable)
        stem.with_suffix('.json').write_text(numeric)
        if args.vdf:
            subprocess.run(['node', str(ROOT / 'tools/convert_vdf.mjs'), str(stem.with_suffix('.json'))], check=True)
        manifest[variant] = {
            'source_sha256': hashlib.sha256(b.source.read_bytes()).hexdigest(),
            'cursor_gyro_generator_sha256': hashlib.sha256(CURSOR_GYRO.read_bytes()).hexdigest(),
            'candidate_sha256': hashlib.sha256(numeric.encode()).hexdigest(),
            'new_layers': b.new, 'new_layer_count': len(b.new),
            'total_layer_count': len(b.cm['action_layers']),
            'renamed_layers': {st.CLEAR: CLEAR},
            'resolved_references': count, 'device_status': 'UNTESTED',
            'timing_ms': {'long_press': LONG_MS, 'double_press': DOUBLE_MS}}
    (HERE / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')


if __name__ == '__main__':
    main()
