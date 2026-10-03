"""Pad clicks after the first Deck run of 90.14: more exits, a 5 ms outer delay, quieter haptics.

Extends the 10-03 `SecondPressKeys` builder, which extends `PadClick`; both stay
frozen. The author played 90.14 and 90.15: pad click layers got stuck, and a
click gave three or four bumps. The author's changes (2026-10-03):

- Base's click adds the Click Entry Point with a repeating add as well, so a
  click that is still held brings the layer back if something removed it. The
  first add keeps the one bump; the repeating one is silent.
- The Click Entry Point's two Soft Presses are both uninterruptible. The outer
  one (the D-pad layer) fires after a 5 ms start delay and no longer repeats.
  The centre one has no delay; it keeps Hold to Repeat, because an inverted
  entry that is already true when its layer lands only fires on a repeat (R114).
- Every pad click layer gets two more exits beside the inverted, repeating
  Soft Press: a Release on the click, and a Release on the pad's touch for a
  thumb that lifts. The 90.13 D-pad layers had neither; this is extra insurance.
- The Click Entry Point's pad states `haptic_intensity_override: 0`. It stated
  nothing in 90.14, which left a D-pad pad's haptics to Steam's default.

`hold_layer` stays out (R101). The author will go back to it if this still
leaves layers stuck.
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

SECOND_PRESS = ROOT / 'findings/2026-10-03-menu-second-press-keys/build_candidate.py'
spec = importlib.util.spec_from_file_location('menu_second_press_keys', SECOND_PRESS)
sp = importlib.util.module_from_spec(spec); spec.loader.exec_module(sp)
pc = sp.pc

OUTER_DELAY_MS = 5
BASE_REPEAT_MS = 50
# The layers a thumb on the right pad keeps alive under a click layer. A thumb that lifts off a click
# takes them along: their own touch Release is covered while a click layer is on.
UNDER = {'LTP': (), 'RTP': ('RTP: Circular Scroll', 'RTP: Entry Point', 'RTP: Tap Cover')}


class PadClickExits:
    def build_menu(self):
        super().build_menu()
        for pad in pc.PADS:
            self.build_pad_exits(pad)

    def build_pad_exits(self, pad):
        m = self.m
        source, dpad, _ = pc.PADS[pad]
        entry, centre = pc.entry_point(pad), pc.middle(pad)

        click = self.sources('Base')[source]['inputs']['click']['activators']
        first = click['Soft_Press']
        if isinstance(first, list) or m.commands(first) != [m.op('add', entry)]:
            raise ValueError(f'Base {source} click: expected one add of {entry}, found {first}')
        # The bump stays on the press. The repeat is silent: it only matters when the layer went missing.
        click['Soft_Press'] = [first, m.entry(m.op('add', entry), hold_repeats=1, repeat_rate=BASE_REPEAT_MS,
                                              haptic_intensity=0)]

        group = self.sources(entry)[source]
        group['settings']['haptic_intensity_override'] = '0'
        inner, outer = group['inputs']['edge']['activators']['Soft_Press']
        if m.commands(inner) != [m.op('add', centre)] or m.commands(outer) != [m.op('add', dpad)]:
            raise ValueError(f'{entry} edge: expected the centre and outer adds, found {inner} and {outer}')
        if inner['settings'].get('interruptable') != '0' or inner['settings'].get('hold_repeats') != '1':
            raise ValueError(f'{entry} edge: the centre Soft Press changed: {inner["settings"]}')
        outer['settings'] = {'haptic_intensity': '0', 'activation_threshold': outer['settings']['activation_threshold'],
                             'delay_start': str(OUTER_DELAY_MS), 'interruptable': '0'}

        for layer, names in ((entry, [entry]), (centre, [entry, centre]), (dpad, [entry, dpad])):
            inputs = self.sources(layer)[source]['inputs']
            if 'release' in inputs['click']['activators'] or 'touch' in inputs:
                raise ValueError(f'{layer} {source}: a Release is already there')
            inputs['click']['activators']['release'] = m.entry(m.seq(*self.clear(names)), haptic_intensity=0)
            inputs['touch'] = m.inp(release=m.entry(m.seq(*self.clear(names + list(UNDER[pad]))), haptic_intensity=0))

    def finish(self):
        data = super().finish()
        self.cm['title'] = self.cm['title'].replace('menu second press keys candidate', 'pad click exits candidate')
        self.cm['description'] = (
            'Pad click exits candidate; device verification pending. Pad click layers also end on the click '
            'Release and when the thumb lifts; the outer buttons come after 5 ms. '
            'See findings/2026-10-03-pad-click-exits/README.md.')
        report = audit_layout(data)
        if report['violations']:
            raise ValueError(report['violations'])
        return data


def Builder(variant):
    return type('Concrete', (PadClickExits, type(sp.Builder(variant))), {})(variant)


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
        stem = HERE / f'{variant}-pad-click-exits'
        stem.with_suffix('.readable.json').write_text(readable)
        stem.with_suffix('.json').write_text(numeric)
        if args.vdf:
            subprocess.run(['node', str(ROOT / 'tools' / 'convert_vdf.mjs'), str(stem.with_suffix('.json'))], check=True)
        manifest[variant] = {
            'source_sha256': hashlib.sha256(b.source.read_bytes()).hexdigest(),
            'second_press_generator_sha256': hashlib.sha256(SECOND_PRESS.read_bytes()).hexdigest(),
            'candidate_sha256': hashlib.sha256(numeric.encode()).hexdigest(),
            'new_layers': b.new, 'new_layer_count': len(b.new),
            'total_layer_count': len(b.cm['action_layers']),
            'resolved_references': count, 'device_status': 'UNTESTED',
            'timing_ms': {'outer_delay': OUTER_DELAY_MS, 'base_repeat': BASE_REPEAT_MS,
                          'centre_repeat': pc.ADD_REPEAT_MS}}
    (HERE / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')


if __name__ == '__main__':
    main()
