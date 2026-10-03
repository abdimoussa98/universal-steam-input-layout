"""Move Steering's fallback exit timer into its own layer, `Steering | LS: Fallback Hold`.

Extends the 10-01 `Stateful` builder the way `Stateful` extends `Lean`; both
stay frozen. The author's design (2026-10-02):

- Steering's stick up and down no longer type W or S or carry a timer. Each is
  a repeating add of the Fallback Hold.
- The Fallback Hold binds only the left stick's up, down and edge. Up and down
  type W or S, exit Steering after 1.5 s, and their Release removes the layer,
  so the timer can't run on A or D.
- The edge pulses from the moment the layer is on, and carries the repeating
  removal that restarts a stuck delay (Definition of Done section 6). Its target,
  the Entry Guard, is never on the stack here; only the removal matters.
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
from audit_command_budget import audit_layout
from convert_runtime_ids import generate_lookup, titles_to_ids, ids_to_titles

STATEFUL = ROOT / 'findings/2026-10-01-stateful-transitions/build_candidate.py'
spec = importlib.util.spec_from_file_location('stateful_transitions', STATEFUL)
st = importlib.util.module_from_spec(spec); spec.loader.exec_module(st)
lean = st.lean

HOLD = 'Steering | LS: Fallback Hold'
KEYS = {'dpad_north': 'W', 'dpad_south': 'S'}
# The exit and its reset follow the delay convention: the reset is 50 ms longer,
# so a healthy exit lands before the first reset.
EXIT_MS, RESET_MS = 1500, 1550
# The pulse starts at once. A 5 ms delay fires over an edge that is already
# held when the layer is added, where an immediate bind may not.
PULSE_DELAY_MS, PULSE_MS = 5, 250
ADD_REPEAT_MS = 50


class FallbackHold:
    def layer(self, name):
        super().layer(name)
        if name == st.COVER:
            # Appended after the last 90.10 layer, so no runtime ID shifts, and
            # before the whole-layout clear lists are generated.
            super().layer(HOLD)

    def hold_exit(self, direction):
        """Steering's stick up and down: only the repeating add. The key and the
        exit timer live in the Fallback Hold."""
        m = self.m
        return m.full(m.op('add', HOLD), hold_repeats=1, repeat_rate=ADD_REPEAT_MS, interruptable=0)

    def acquisition(self):
        """A driver press retires the Fallback Hold along with the Entry Guard;
        the W or S layer then owns the stick."""
        m = self.m
        bindings = super().acquisition()
        for binding in bindings.values():
            press = binding['activators']['Full_Press']
            press['bindings']['binding'] = m.seq(m.op('remove', HOLD), *reversed(m.commands(press)))
        return bindings

    def build_menu(self):
        super().build_menu()
        self.menu_helpers.remove(HOLD)
        self.build_fallback_hold()
        # Nothing is added over the Fallback Hold or the Entry Guard, so no
        # layer above can hide their Releases. Start and Select type Tab and
        # Escape, as they do while a driver is held; a driver press still
        # removes either layer before its own add.
        for name in (HOLD, self.title('Entry Guard')):
            self.add_to_source(name, 'switch', self.menu_keys())

    def menu_keys(self):
        return {button: self.m.full(self.m.key(tap)) for button, _, tap in st.MENU.values()}

    def build_entry_point(self, name, side, transitions):
        """Steering's Entry Points type W and S on stick up and down instead of
        inheriting Steering's add of the Fallback Hold, which would land on
        top of the menu layers. Every stack under them gives W or S, so this
        replaces rather than blocks; the stick guards and the menu Tap Cover
        inherit it."""
        super().build_entry_point(name, side, transitions)
        if name == st.entry_point(side, steering=True):
            stick = self.sources(name)['joystick']['inputs']
            for direction in KEYS:
                stick[direction] = self.m.output_only(self.base_groups['joystick']['inputs'][direction])

    def build_fallback_hold(self):
        m = self.m
        leave = m.op('remove', HOLD)
        inputs = {}
        for input_name, key in KEYS.items():
            inputs[input_name] = m.inp(
                Full_Press=m.entry(m.key(key), interruptable=0),
                chord=self.chorded_delay(m.seq(leave, *self.exit_all(beep=True)), lean.LS_DEFLECT_MASK, EXIT_MS,
                                         haptic_intensity=3, interruptable=0),
                release=m.entry(leave))
        # Up and down are full (key, exit, Release), so the pulse and the reset
        # sit on the edge, which is out for as long as this layer is on. Its
        # Release is a backstop for an up or down Release a layer above hid.
        inputs['edge'] = m.inp(
            chord=self.chorded_delay(m.EMPTY, lean.LS_DEFLECT_MASK, PULSE_DELAY_MS, hold_repeats=1,
                                     repeat_rate=PULSE_MS, haptic_intensity=3, interruptable=0),
            release=m.entry(leave),
            Full_Press=m.entry(m.op('remove', self.title('Entry Guard')), hold_repeats=1,
                               repeat_rate=RESET_MS, interruptable=0))
        # Left, right, click and touch are inherited from Steering.
        self.group(HOLD, 'joystick', inputs, self.ls_settings())

    def build_rs_edge_blocks(self):
        """No turn assist anywhere in Steering (author, 2026-10-02). Base's
        right-stick edge adds the ramp layers, which bind both bumpers; with a
        driver held, its trigger chord could put a ramp layer over the W or S
        layer and take the driver's Release. Every Steering layer inherits this
        empty edge or binds its own. It also leaves gyro on while the right
        stick is used (`Gyro Off Ramp Up` isn't added)."""
        super().build_rs_edge_blocks()
        self.add_to_source(self.title(), 'right_joystick', {'edge': self.m.full()})

    def build_touch_cleanup(self):
        everything = self.new
        self.new = [n for n in everything if n != HOLD]
        try:
            super().build_touch_cleanup()
        finally:
            self.new = everything

    def finish(self):
        data = super().finish()
        self.cm['title'] = self.cm['title'].replace('stateful transitions candidate', 'fallback hold candidate')
        self.cm['description'] = (
            'Steering fallback hold candidate; device verification pending. With no driver held, stick up or '
            f'down types W or S, pulses at once and leaves Steering after {EXIT_MS / 1000:g} s. Rolling to A '
            'or D ends the timer. See findings/2026-10-02-steering-fallback-hold/README.md.')
        report = audit_layout(data)
        if report['violations']:
            raise ValueError(report['violations'])
        return data


def Builder(variant):
    return type('Concrete', (FallbackHold, type(st.Builder(variant))), {})(variant)


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
        stem = HERE / f'{variant}-fallback-hold'
        stem.with_suffix('.readable.json').write_text(readable)
        stem.with_suffix('.json').write_text(numeric)
        if args.vdf:
            subprocess.run(['node', str(ROOT / 'convert_vdf.mjs'), str(stem.with_suffix('.json'))], check=True)
        manifest[variant] = {
            'source_sha256': hashlib.sha256(b.source.read_bytes()).hexdigest(),
            'stateful_generator_sha256': hashlib.sha256(STATEFUL.read_bytes()).hexdigest(),
            'candidate_sha256': hashlib.sha256(numeric.encode()).hexdigest(),
            'new_layers': b.new, 'new_layer_count': len(b.new),
            'total_layer_count': len(b.cm['action_layers']),
            'resolved_references': count, 'device_status': 'UNTESTED',
            'timing_ms': {'fallback_exit': EXIT_MS, 'fallback_reset': RESET_MS, 'fallback_pulse': PULSE_MS,
                          'fallback_pulse_delay': PULSE_DELAY_MS, 'fallback_add_repeat': ADD_REPEAT_MS}}
    (HERE / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')


if __name__ == '__main__':
    main()
