"""The Click Entry Point hands over: each edge Soft Press removes it, then adds the chosen layer.

Extends the 10-03 `SoftPressOnly` builder; it stays frozen. The author's changes
after 90.17 (2026-10-03):

- The Click Entry Point's inverted, repeating Soft Press removal on the click
  goes. The layer binds no click at all.
- Its two edge Soft Presses remove the Click Entry Point first and then add the
  Middle Click layer or the D-pad layer. So the entry point is never under the
  layer it chose: it is on from the press until one of the two fires.

What follows from that, and is done here:

- The Middle Click and D-pad layers no longer name the Click Entry Point in
  their own exits and cleanups: it can't be on the stack with them (R132).
- The Click Entry Point's remaining exits are the two hand-overs, the thumb
  lifting off the pad, and the stick-touch cleanup.
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

SOFT = ROOT / 'findings/2026-10-03-pad-click-soft-press-only/build_candidate.py'
spec = importlib.util.spec_from_file_location('pad_click_soft_press_only', SOFT)
so = importlib.util.module_from_spec(spec); spec.loader.exec_module(so)
px, pc = so.px, so.pc


class Handoff:
    def build_pad_exits(self, pad):
        super().build_pad_exits(pad)
        m = self.m
        source, dpad, chord = pc.PADS[pad]
        entry, centre = pc.entry_point(pad), pc.middle(pad)

        inputs = self.sources(entry)[source]['inputs']
        click = inputs.pop('click')['activators']
        if list(click) != ['Soft_Press'] or m.commands(click['Soft_Press']) != [m.op('remove', entry)]:
            raise ValueError(f'{entry} click: expected only the Soft Press removal, found {click}')
        for soft, target in zip(inputs['edge']['activators']['Soft_Press'], (centre, dpad)):
            if m.commands(soft) != [m.op('add', target)]:
                raise ValueError(f'{entry} edge: expected the add of {target}, found {m.commands(soft)}')
            # The removal is stored below the add, so it runs first (R110).
            soft['bindings']['binding'] = m.seq(m.op('remove', entry), m.op('add', target))

        for layer in (centre, dpad):
            own = self.sources(layer)
            own[source]['inputs']['click']['activators']['Soft_Press'] = self.pressure_exit(layer)
            own[source]['inputs']['touch'] = m.inp(release=m.entry(
                m.seq(*self.clear([layer] + list(px.UNDER[pad]))), haptic_intensity=0))
            for stick in pc.STICKS:
                own[stick]['inputs']['touch'] = self.stick_touch(stick, chord, layer)

    def finish(self):
        data = super().finish()
        self.cm['title'] = self.cm['title'].replace('pad click soft press only candidate', 'pad click handoff candidate')
        self.cm['description'] = (
            'Pad click hand-over candidate; device verification pending. The Click Entry Point removes itself '
            'when it adds the Middle Click or D-pad layer. See findings/2026-10-03-pad-click-handoff/README.md.')
        report = audit_layout(data)
        if report['violations']:
            raise ValueError(report['violations'])
        return data


def Builder(variant):
    return type('Concrete', (Handoff, type(so.Builder(variant))), {})(variant)


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
        stem = HERE / f'{variant}-pad-click-handoff'
        stem.with_suffix('.readable.json').write_text(readable)
        stem.with_suffix('.json').write_text(numeric)
        if args.vdf:
            subprocess.run(['node', str(ROOT / 'tools' / 'convert_vdf.mjs'), str(stem.with_suffix('.json'))], check=True)
        manifest[variant] = {
            'source_sha256': hashlib.sha256(b.source.read_bytes()).hexdigest(),
            'soft_press_only_generator_sha256': hashlib.sha256(SOFT.read_bytes()).hexdigest(),
            'candidate_sha256': hashlib.sha256(numeric.encode()).hexdigest(),
            'new_layers': b.new, 'new_layer_count': len(b.new),
            'total_layer_count': len(b.cm['action_layers']),
            'resolved_references': count, 'device_status': 'UNTESTED'}
    (HERE / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')


if __name__ == '__main__':
    main()
