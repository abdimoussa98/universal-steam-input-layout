"""Decide a trackpad click once: middle click or the D-pad buttons, through a Click Entry Point.

Extends the 10-02 `FallbackHold` builder the way `FallbackHold` extends
`Stateful`; both stay frozen. The author's design (2026-10-02 and 2026-10-03):

- A pad click no longer goes straight to the D-pad layer (`LTP: Arrow Keys`,
  `RTP: Mouse Buttons`). It adds a Click Entry Point that binds the pad's edge
  with two Soft Presses, both repeating adds with no haptics:
  the centre range, uninterruptible, adds a single-button Middle Click layer;
  the outer range, interruptible, adds the D-pad layer.
- The two ranges are today's sizes. The outer one is the D-pad layer's
  deadzone. The centre one is the D-pad layer's inverted edge radius, which the
  layout never stated: Steam's default, taken as 24996 (README, "The ranges").
- The Middle Click layer binds the whole pad's click to what the centre sent
  (middle mouse on the right pad, Show Keyboard on the left).
- The D-pad layer loses its centre chord. Its edge is an empty binding, so the
  Click Entry Point's two Soft Presses aren't inherited while it is on.
- Every lifetime is `add_layer` and `remove_layer`. The five `hold_layer`
  commands are gone (R101).
- Letting go of the click removes the Click Entry Point first, so its repeating
  adds can't bring a layer back, and then the layer that was chosen.
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

FALLBACK = ROOT / 'findings/2026-10-02-steering-fallback-hold/build_candidate.py'
spec = importlib.util.spec_from_file_location('fallback_hold', FALLBACK)
fh = importlib.util.module_from_spec(spec); spec.loader.exec_module(fh)
st = fh.st

# pad: (source, the D-pad layer its click used to hold, the legacy chord id of a thumb on that pad)
PADS = {'LTP': ('left_trackpad', 'LTP: Arrow Keys', 16), 'RTP': ('right_trackpad', 'RTP: Mouse Buttons', 17)}
SCROLL = 'RTP: Circular Scroll'
STICKS = ('joystick', 'right_joystick')
# The D-pad layers invert their edge and state no radius, so the centre bind used
# Steam's default radius. Valve's bundled templates write 24995 to 24999 on D-pad
# groups that bind no edge at all; the README has the evidence.
CENTRE_RADIUS = 24996
# A Soft Press that is already past its threshold when the layer lands fires on
# its next repeat, not at once (R113).
ADD_REPEAT_MS = 50


def entry_point(pad):
    return f'{pad}: Click Entry Point'


def middle(pad):
    return f'{pad}: Middle Click'


NEW = [entry_point(pad) for pad in PADS] + [middle(pad) for pad in PADS]


class PadClick:
    def layer(self, name):
        super().layer(name)
        if name == st.COVER:
            # After the Fallback Hold, so no runtime ID shifts, and before the
            # whole-layout clear lists are generated.
            for title in NEW:
                super().layer(title)

    def regroup(self, name, source):
        """A layer's own copy of a source, like `patch`, without listing the
        layer as changed: the frozen source's RTP scroll still has the Long
        Press the fix pipeline replaces, and a changed layer is checked for it."""
        old = self.sources(name)[source]
        return self.group(name, source, old.get('inputs', {}), old.get('settings', {}), old['mode'])

    def pressure_exit(self, *names):
        """The pad layers' exit: an inverted Soft Press on the click, so it
        fires while the pad isn't pressed. It repeats, because the pad can
        already be let go when the layer lands."""
        m = self.m
        return m.entry(m.seq(*self.clear(names)), hold_repeats=1, haptic_intensity=0, interruptable=0,
                       edge_binding_invert=1)

    def stick_touch(self, source, chord, *names):
        """The pad layers' stick-touch input: a cleanup function guarded by a
        thumb on the pad, and the Release that clears that stick's helpers."""
        m = self.m
        return m.inp(Full_Press=m.entry(m.seq(*self.clear(names)), hold_repeats=1),
                     chord=m.entry(m.EMPTY, chord_button=chord, interruptable=0),
                     release=m.entry(m.seq(*self.stick_cleanup(source)), haptic_intensity=0))

    def build_menu(self):
        super().build_menu()
        for title in NEW:
            self.menu_helpers.remove(title)
        for pad in PADS:
            self.build_pad(pad)
        self.build_scroll()

    def build_pad(self, pad):
        m = self.m
        source, dpad, chord = PADS[pad]
        entry, centre = entry_point(pad), middle(pad)

        click = self.patch('Base', source)['inputs']['click']['activators']['Soft_Press']
        if m.commands(click) != [m.op('hold', dpad)]:
            raise ValueError(f'Base {source} click: expected a hold of {dpad}, found {m.commands(click)}')
        click['bindings']['binding'] = m.op('add', entry)

        group = self.regroup(dpad, source)
        inputs = group['inputs']
        old = inputs['edge']['activators']['chord']
        if isinstance(old, list) or any('_layer' in c for c in m.commands(old)):
            raise ValueError(f'{dpad} edge: expected one output chord, found {old}')
        output, haptic = old['bindings']['binding'], old['settings']['haptic_intensity']
        if group['settings'].get('edge_binding_invert') != '1' or 'edge_binding_radius' in group['settings']:
            raise ValueError(f'{dpad}: expected an inverted edge at the default radius, found {group["settings"]}')
        outer = group['settings']['deadzone']
        # Empty, not left out: both layers are D-pad pads, so an open edge would
        # inherit the Click Entry Point's Soft Presses.
        inputs['edge'] = m.full()
        inputs['click'] = m.inp(Soft_Press=self.pressure_exit(entry, dpad))

        self.group(entry, source, {
            'edge': m.inp(Soft_Press=[
                m.entry(m.op('add', centre), hold_repeats=1, repeat_rate=ADD_REPEAT_MS, haptic_intensity=0,
                        activation_threshold=CENTRE_RADIUS, interruptable=0, edge_binding_invert=1),
                m.entry(m.op('add', dpad), hold_repeats=1, repeat_rate=ADD_REPEAT_MS, haptic_intensity=0,
                        activation_threshold=outer)]),
            'click': m.inp(Soft_Press=self.pressure_exit(entry))}, {}, 'dpad')
        self.group(centre, source, {'click': m.inp(
            Full_Press=m.entry(output, haptic_intensity=haptic),
            Soft_Press=self.pressure_exit(entry, centre))}, {}, 'single_button')

        for stick in STICKS:
            self.regroup(dpad, stick)['inputs']['touch'] = self.stick_touch(stick, chord, entry, dpad)
            self.group(entry, stick, {'touch': self.stick_touch(stick, chord, entry)})
            self.group(centre, stick, {'touch': self.stick_touch(stick, chord, entry, centre)})

    def build_scroll(self):
        """Circular Scroll's click leads to the Click Entry Point, and what
        removed the D-pad layer with it also removes the two new layers."""
        m = self.m
        entry, centre, dpad = entry_point('RTP'), middle('RTP'), PADS['RTP'][1]
        own = [m.op('remove', SCROLL), m.op('remove', dpad)]          # stored order
        for source in ('right_trackpad',) + STICKS:
            inputs = self.regroup(SCROLL, source)['inputs']
            if source == 'right_trackpad':
                click = inputs['click']['activators']['Soft_Press']
                if m.commands(click) != [m.op('hold', dpad)]:
                    raise ValueError(f'{SCROLL} click: expected a hold of {dpad}, found {m.commands(click)}')
                click['bindings']['binding'] = m.op('add', entry)
            found = [e for _, e in m.entries(inputs['touch']) if m.commands(e) == own]
            if len(found) != 1:
                raise ValueError(f'{SCROLL} {source} touch: expected one removal of the scroll pair, found {found}')
            # The new removals are stored below the existing ones, so they run first (R110).
            found[0]['bindings']['binding'] = own + [m.op('remove', centre), m.op('remove', entry)]

    def build_touch_cleanup(self):
        # The pad layers bring their own stick-touch inputs.
        everything = self.new
        self.new = [n for n in everything if n not in NEW]
        try:
            super().build_touch_cleanup()
        finally:
            self.new = everything

    def finish(self):
        data = super().finish()
        self.cm['title'] = self.cm['title'].replace('fallback hold candidate', 'pad middle click candidate')
        self.cm['description'] = (
            'Pad middle click candidate; device verification pending. A pad click is decided once: pressed '
            'near the centre it is the middle click (Show Keyboard on the left pad), further out it is the '
            'D-pad buttons. See findings/2026-10-03-pad-middle-click/README.md.')
        # Active groups only: the frozen source keeps one in a plain-inactive Base
        # slot, which the fix pipeline prunes (`dead_groups`).
        held = [name for name in self.by_title if 'hold_layer' in json.dumps(self.sources(name))]
        if held:
            raise ValueError(f'a hold_layer command is left in {held}')
        report = audit_layout(data)
        if report['violations']:
            raise ValueError(report['violations'])
        return data


def Builder(variant):
    return type('Concrete', (PadClick, type(fh.Builder(variant))), {})(variant)


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
        stem = HERE / f'{variant}-pad-middle-click'
        stem.with_suffix('.readable.json').write_text(readable)
        stem.with_suffix('.json').write_text(numeric)
        if args.vdf:
            subprocess.run(['node', str(ROOT / 'convert_vdf.mjs'), str(stem.with_suffix('.json'))], check=True)
        manifest[variant] = {
            'source_sha256': hashlib.sha256(b.source.read_bytes()).hexdigest(),
            'fallback_hold_generator_sha256': hashlib.sha256(FALLBACK.read_bytes()).hexdigest(),
            'candidate_sha256': hashlib.sha256(numeric.encode()).hexdigest(),
            'new_layers': b.new, 'new_layer_count': len(b.new),
            'total_layer_count': len(b.cm['action_layers']),
            'resolved_references': count, 'device_status': 'UNTESTED',
            'ranges': {'centre_radius': CENTRE_RADIUS,
                       'outer_threshold': {pad: b.sources(dpad)[source]['settings']['deadzone']
                                           for pad, (source, dpad, _) in PADS.items()}},
            'timing_ms': {'click_add_repeat': ADD_REPEAT_MS}}
    (HERE / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')


if __name__ == '__main__':
    main()
