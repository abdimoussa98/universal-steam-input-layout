"""The menu Tap Cover binds both stick touches itself.

Extends the 10-03 `Gamepad` builder; it stays frozen. Since 90.10 the Tap Cover
had its own stick groups in D-pad mode with nothing on the touch, and inherited
the touch from the menu stick guard under it. Seven layers can land between the
guard and the cover and keep the right stick in mouse mode, and nothing is
inherited across a mode change (A2): the right-stick touch Release was lost,
and `RST: Entry Point`, `RST: Tap Cover` and `RST: Temporary Gyro` stayed on.
The hidden-exit check with six extra presses found it (2026-10-04, R136);
the author chose this fix the same day:
findings/2026-10-03-simultaneous-cap/suggested-fixes.md, fix A.

On each stick the cover takes the guard's touch input as it is, without the
guard's add of the cover in the Release. This is R116 with no exception for
this layer.
"""
import argparse
import copy
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

GAMEPAD = ROOT / 'findings/2026-10-03-gamepad/build_candidate.py'
spec = importlib.util.spec_from_file_location('gamepad', GAMEPAD)
gp = importlib.util.module_from_spec(spec); spec.loader.exec_module(gp)
st = gp.st


class StickTouches:
    def build_cover_touches(self):
        m = self.m
        for stick_side, source in st.STICKS.items():
            found = self.sources(st.COVER)[source]
            if found['mode'] != 'dpad' or list(found['inputs']) != ['edge']:
                raise ValueError(f'{st.COVER} {source}: expected a D-pad group with the edge alone, found {found}')
            touch = copy.deepcopy(self.sources(st.guard(stick_side))[source]['inputs']['touch'])
            release = touch['activators']['release']
            stored = m.commands(release)
            cleanup = [c for c in stored if c != m.op('add', st.COVER)]
            if sorted(touch['activators']) != ['Full_Press', 'chord', 'release'] or len(cleanup) != len(stored) - 1:
                raise ValueError(f'{st.guard(stick_side)} {source} touch: expected the cleanup, its chord and a '
                                 f'Release that adds the cover once, found {touch}')
            release['bindings']['binding'] = cleanup
            found['inputs']['touch'] = touch

    def finish(self):
        data = super().finish()
        self.build_cover_touches()
        self.cm['title'] = self.cm['title'].replace('gamepad candidate', 'tap cover stick touches candidate')
        self.cm['description'] = (
            'Tap cover stick touches candidate; device verification pending. The menu Tap Cover binds both '
            'stick touches itself. See findings/2026-10-04-tap-cover-stick-touches/README.md.')
        report = audit_layout(data)
        if report['violations']:
            raise ValueError(report['violations'])
        return data


def Builder(variant):
    return type('Concrete', (StickTouches, type(gp.Builder(variant))), {})(variant)


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
        stem = HERE / f'{variant}-tap-cover-stick-touches'
        stem.with_suffix('.readable.json').write_text(readable)
        stem.with_suffix('.json').write_text(numeric)
        if args.vdf:
            subprocess.run(['node', str(ROOT / 'tools/convert_vdf.mjs'), str(stem.with_suffix('.json'))], check=True)
        manifest[variant] = {
            'source_sha256': hashlib.sha256(b.source.read_bytes()).hexdigest(),
            'gamepad_generator_sha256': hashlib.sha256(GAMEPAD.read_bytes()).hexdigest(),
            'candidate_sha256': hashlib.sha256(numeric.encode()).hexdigest(),
            'new_layers': b.new, 'new_layer_count': len(b.new),
            'total_layer_count': len(b.cm['action_layers']),
            'resolved_references': count, 'device_status': 'UNTESTED'}
    (HERE / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')


if __name__ == '__main__':
    main()
