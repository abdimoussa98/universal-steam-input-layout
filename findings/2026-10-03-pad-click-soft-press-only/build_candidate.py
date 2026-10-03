"""Pad clicks after the Deck run of 90.16: Soft Presses only, both adds repeating, Caps Lock on the left.

Extends the 10-03 `PadClickExits` builder; it stays frozen. The author played
90.16 and asked for three changes (2026-10-03):

- **No Release on the pad click.** A Release fires at the pad's full-click
  threshold, and every other bind that moves the click layers is a Soft Press
  at its own, lower threshold. The two don't line up, so the click's Release
  goes from all six pad click layers. The exits are the inverted, repeating
  Soft Press and the Release on the pad's touch.
- **Both Soft Presses of the Click Entry Point repeat.** 90.16 took the repeat
  off the outer one when it got its 5 ms delay. It keeps the delay and repeats
  every 50 ms again.
- **The left pad's centre is Caps Lock**, not Show Keyboard.
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

EXITS = ROOT / 'findings/2026-10-03-pad-click-exits/build_candidate.py'
spec = importlib.util.spec_from_file_location('pad_click_exits', EXITS)
px = importlib.util.module_from_spec(spec); spec.loader.exec_module(px)
pc = px.pc

OUTER_REPEAT_MS = pc.ADD_REPEAT_MS
# pad -> the centre click's output, where it differs from what the 90.13 centre chord sent
CENTRE = {'LTP': 'key_press CAPSLOCK, , '}


class SoftPressOnly:
    def build_pad_exits(self, pad):
        super().build_pad_exits(pad)
        m = self.m
        source, dpad, _ = pc.PADS[pad]
        entry, centre = pc.entry_point(pad), pc.middle(pad)

        for layer in (entry, centre, dpad):
            del self.sources(layer)[source]['inputs']['click']['activators']['release']

        _, outer = self.sources(entry)[source]['inputs']['edge']['activators']['Soft_Press']
        if m.commands(outer) != [m.op('add', dpad)] or 'hold_repeats' in outer['settings']:
            raise ValueError(f'{entry} edge: expected the delayed add of {dpad} with no repeat, found {outer}')
        outer['settings'] = {'hold_repeats': '1', 'repeat_rate': str(OUTER_REPEAT_MS), **outer['settings']}

        if pad in CENTRE:
            press = self.sources(centre)[source]['inputs']['click']['activators']['Full_Press']
            if m.commands(press) != ['controller_action SHOW_KEYBOARD, , ']:
                raise ValueError(f'{centre} click: expected Show Keyboard, found {m.commands(press)}')
            press['bindings']['binding'] = CENTRE[pad]

    def finish(self):
        data = super().finish()
        self.cm['title'] = self.cm['title'].replace('pad click exits candidate', 'pad click soft press only candidate')
        self.cm['description'] = (
            'Pad click Soft Press only candidate; device verification pending. The pad click layers are moved '
            'by Soft Presses and the thumb lifting, never by the click Release; the left pad centre is Caps '
            'Lock. See findings/2026-10-03-pad-click-soft-press-only/README.md.')
        report = audit_layout(data)
        if report['violations']:
            raise ValueError(report['violations'])
        return data


def Builder(variant):
    return type('Concrete', (SoftPressOnly, type(px.Builder(variant))), {})(variant)


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
        stem = HERE / f'{variant}-pad-click-soft-press-only'
        stem.with_suffix('.readable.json').write_text(readable)
        stem.with_suffix('.json').write_text(numeric)
        if args.vdf:
            subprocess.run(['node', str(ROOT / 'tools' / 'convert_vdf.mjs'), str(stem.with_suffix('.json'))], check=True)
        manifest[variant] = {
            'source_sha256': hashlib.sha256(b.source.read_bytes()).hexdigest(),
            'pad_click_exits_generator_sha256': hashlib.sha256(EXITS.read_bytes()).hexdigest(),
            'candidate_sha256': hashlib.sha256(numeric.encode()).hexdigest(),
            'new_layers': b.new, 'new_layer_count': len(b.new),
            'total_layer_count': len(b.cm['action_layers']),
            'resolved_references': count, 'device_status': 'UNTESTED',
            'timing_ms': {'outer_delay': px.OUTER_DELAY_MS, 'outer_repeat': OUTER_REPEAT_MS,
                          'centre_repeat': pc.ADD_REPEAT_MS, 'base_repeat': px.BASE_REPEAT_MS}}
    (HERE / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')


if __name__ == '__main__':
    main()
