"""The final pad click layers hold themselves, and the Click Entry Point adds before it removes itself.

Extends the 10-03 `Handoff` builder; it stays frozen. The author's changes after
playing 90.18 (2026-10-03):

- **A hold on the four final layers.** `LTP: Arrow Keys`, `RTP: Mouse Buttons`
  and the two Middle Click layers get the 90.13 self-hold back: a Soft Press on
  the click, uninterruptible, no haptic, `hold_layer` of the layer itself. It is
  meant to take the layer off when the pad is let go. The inverted, repeating
  Soft Press removal stays as the backup, because holds are unreliable. This is
  a deliberate exception to R101, for these four layers only.
- **The 90.13 shape exactly** (author): no start delay and no repeat on the
  hold. It was working there.
- **The Click Entry Point adds first.** Each edge Soft Press adds the chosen
  layer and then removes the Click Entry Point, the other way round from 90.18.
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

HANDOFF = ROOT / 'findings/2026-10-03-pad-click-handoff/build_candidate.py'
spec = importlib.util.spec_from_file_location('pad_click_handoff', HANDOFF)
ho = importlib.util.module_from_spec(spec); spec.loader.exec_module(ho)
pc = ho.pc


def final_layers(pad):
    return (pc.middle(pad), pc.PADS[pad][1])


HELD = [layer for pad in pc.PADS for layer in final_layers(pad)]


class Holds:
    def build_holds(self):
        """After the frozen builders have finished: `PadClick.finish` refuses any `hold_layer`."""
        m = self.m
        for pad, (source, dpad, _) in pc.PADS.items():
            entry = pc.entry_point(pad)
            for soft, target in zip(self.sources(entry)[source]['inputs']['edge']['activators']['Soft_Press'],
                                    final_layers(pad)):
                if m.commands(soft) != m.seq(m.op('remove', entry), m.op('add', target)):
                    raise ValueError(f'{entry} edge: expected the hand-over to {target}, found {m.commands(soft)}')
                # The author's order: the new layer first, then the Click Entry Point goes.
                soft['bindings']['binding'] = m.seq(m.op('add', target), m.op('remove', entry))
            for layer in final_layers(pad):
                click = self.sources(layer)[source]['inputs']['click']['activators']
                backup = click['Soft_Press']
                if isinstance(backup, list) or m.commands(backup) != [m.op('remove', layer)]:
                    raise ValueError(f'{layer} click: expected only the Soft Press removal, found {backup}')
                # The 90.13 pair: the hold first, the inverted repeating removal behind it.
                click['Soft_Press'] = [m.entry(m.op('hold', layer), haptic_intensity=0, interruptable=0), backup]

    def finish(self):
        data = super().finish()
        self.build_holds()
        self.cm['title'] = self.cm['title'].replace('pad click handoff candidate', 'pad click holds candidate')
        self.cm['description'] = (
            'Pad click holds candidate; device verification pending. The final pad click layers hold themselves '
            'on the click Soft Press, with the inverted removal as the backup. '
            'See findings/2026-10-03-pad-click-holds/README.md.')
        held = sorted(name for name in self.by_title if 'hold_layer' in json.dumps(self.sources(name)))
        if held != sorted(HELD):
            raise ValueError(f'hold_layer in {held}, expected {sorted(HELD)}')
        report = audit_layout(data)
        if report['violations']:
            raise ValueError(report['violations'])
        return data


def Builder(variant):
    return type('Concrete', (Holds, type(ho.Builder(variant))), {})(variant)


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
        stem = HERE / f'{variant}-pad-click-holds'
        stem.with_suffix('.readable.json').write_text(readable)
        stem.with_suffix('.json').write_text(numeric)
        if args.vdf:
            subprocess.run(['node', str(ROOT / 'convert_vdf.mjs'), str(stem.with_suffix('.json'))], check=True)
        manifest[variant] = {
            'source_sha256': hashlib.sha256(b.source.read_bytes()).hexdigest(),
            'handoff_generator_sha256': hashlib.sha256(HANDOFF.read_bytes()).hexdigest(),
            'candidate_sha256': hashlib.sha256(numeric.encode()).hexdigest(),
            'new_layers': b.new, 'new_layer_count': len(b.new),
            'total_layer_count': len(b.cm['action_layers']), 'held_layers': HELD,
            'resolved_references': count, 'device_status': 'UNTESTED'}
    (HERE / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')


if __name__ == '__main__':
    main()
