"""The menu second-press layers type W and S on stick up and down.

Extends the 10-03 `PadClick` builder the way `PadClick` extends `FallbackHold`;
both stay frozen. The gap (found by the 90.14 review, present since 90.11):

- `Menu Left: Escape` and `Menu Right: Tab`, the layers a menu double tap holds,
  left the left stick's up and down open. In Steering they inherited Steering's
  repeating add of the Fallback Hold.
- The Fallback Hold landed on top and answers Start and Select with Tab and
  Escape, so the menu button's Release was missed and the second-press layer
  stayed on.

The fix is the one Steering's Entry Points got in 90.11 and the menu Double Tap
windows have had since 90.10: both layers bind stick up and down to Base's W
and S. Every stack under them gives W or S, so this replaces rather than
blocks. Outside Steering nothing changes.
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

PAD_CLICK = ROOT / 'findings/2026-10-03-pad-middle-click/build_candidate.py'
spec = importlib.util.spec_from_file_location('pad_middle_click', PAD_CLICK)
pc = importlib.util.module_from_spec(spec); spec.loader.exec_module(pc)
fh = pc.fh

SECOND_PRESS = ('Menu Left: Escape', 'Menu Right: Tab')


class SecondPressKeys:
    def build_menu(self):
        super().build_menu()
        base = self.base_groups['joystick']['inputs']
        for name in SECOND_PRESS:
            # The Double Tap Covers sit on these layers and inherit the two binds.
            self.add_to_source(name, 'joystick', {direction: self.m.output_only(base[direction])
                                                  for direction in fh.KEYS})

    def finish(self):
        data = super().finish()
        self.cm['title'] = self.cm['title'].replace('pad middle click candidate', 'menu second press keys candidate')
        self.cm['description'] = (
            'Menu second-press keys candidate; device verification pending. While a menu double tap is held, '
            'stick up and down type W and S and no longer start the Steering fallback exit. '
            'See findings/2026-10-03-menu-second-press-keys/README.md.')
        report = audit_layout(data)
        if report['violations']:
            raise ValueError(report['violations'])
        return data


def Builder(variant):
    return type('Concrete', (SecondPressKeys, type(pc.Builder(variant))), {})(variant)


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
        stem = HERE / f'{variant}-menu-second-press-keys'
        stem.with_suffix('.readable.json').write_text(readable)
        stem.with_suffix('.json').write_text(numeric)
        if args.vdf:
            subprocess.run(['node', str(ROOT / 'tools' / 'convert_vdf.mjs'), str(stem.with_suffix('.json'))], check=True)
        manifest[variant] = {
            'source_sha256': hashlib.sha256(b.source.read_bytes()).hexdigest(),
            'pad_click_generator_sha256': hashlib.sha256(PAD_CLICK.read_bytes()).hexdigest(),
            'candidate_sha256': hashlib.sha256(numeric.encode()).hexdigest(),
            'new_layers': b.new, 'new_layer_count': len(b.new),
            'total_layer_count': len(b.cm['action_layers']), 'changed_layers': list(SECOND_PRESS),
            'resolved_references': count, 'device_status': 'UNTESTED'}
    (HERE / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')


if __name__ == '__main__':
    main()
