"""Base's pad clicks add the Click Entry Point with one Soft Press, not two.

Extends the 10-03 `Holds` builder; it stays frozen. Since 90.16 each of Base's
two pad clicks had two Soft Presses that both add the Click Entry Point: the
first with the bump and no repeat, the second silent and repeating every 50 ms.
The author saw the pair in Steam and asked for one (2026-10-03): the first is
kept as it is, the repeating one goes.

That is the shape of 90.14 and 90.15, and of 90.13's hold: one add per press.
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

HOLDS = ROOT / 'findings/2026-10-03-pad-click-holds/build_candidate.py'
spec = importlib.util.spec_from_file_location('pad_click_holds', HOLDS)
hd = importlib.util.module_from_spec(spec); spec.loader.exec_module(hd)
pc = hd.pc


class OneAdd:
    def build_one_add(self):
        m = self.m
        for pad, (source, _, _) in pc.PADS.items():
            click = self.sources('Base')[source]['inputs']['click']['activators']
            found = click['Soft_Press']
            add = [m.op('add', pc.entry_point(pad))]
            if not isinstance(found, list) or len(found) != 2 or any(m.commands(e) != add for e in found):
                raise ValueError(f'Base {source} click: expected two adds of the Click Entry Point, found {found}')
            first, again = found
            if 'hold_repeats' in first.get('settings', {}) or again['settings'].get('hold_repeats') != '1':
                raise ValueError(f'Base {source} click: expected the bump first and the repeat second, found {found}')
            click['Soft_Press'] = first

    def finish(self):
        data = super().finish()
        self.build_one_add()
        self.cm['title'] = self.cm['title'].replace('pad click holds candidate', 'base pad click one add candidate')
        self.cm['description'] = (
            'Base pad click one add candidate; device verification pending. Each pad click adds the Click '
            'Entry Point with one Soft Press. See findings/2026-10-03-base-pad-click-one-add/README.md.')
        report = audit_layout(data)
        if report['violations']:
            raise ValueError(report['violations'])
        return data


def Builder(variant):
    return type('Concrete', (OneAdd, type(hd.Builder(variant))), {})(variant)


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
        stem = HERE / f'{variant}-base-pad-click-one-add'
        stem.with_suffix('.readable.json').write_text(readable)
        stem.with_suffix('.json').write_text(numeric)
        if args.vdf:
            subprocess.run(['node', str(ROOT / 'tools/convert_vdf.mjs'), str(stem.with_suffix('.json'))], check=True)
        manifest[variant] = {
            'source_sha256': hashlib.sha256(b.source.read_bytes()).hexdigest(),
            'holds_generator_sha256': hashlib.sha256(HOLDS.read_bytes()).hexdigest(),
            'candidate_sha256': hashlib.sha256(numeric.encode()).hexdigest(),
            'new_layers': b.new, 'new_layer_count': len(b.new),
            'total_layer_count': len(b.cm['action_layers']),
            'resolved_references': count, 'device_status': 'UNTESTED'}
    (HERE / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')


if __name__ == '__main__':
    main()
