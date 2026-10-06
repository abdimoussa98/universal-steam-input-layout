"""The pad touch bump comes out: the pads are as in 90.24 again.

The author, 2026-10-04: "I don't like the new trackpad changes. To include that bump."
How the bump was built is recorded in findings/2026-10-04-pad-touch-bump/README.md.

This builder runs the 90.25 build without its two pad steps, then the two steps of the
90.26 build that don't belong to the bump:

1. **No touch layers.** `RTP: Touch Entry Point`, `LTP: Touch Entry Point` and
   `LTP: Entry Point` are not created: 87 layers, not 90. The nine menu layers that came
   after them move up three places.
2. **Base's pads are 90.24's.** The right pad's touch adds `RTP: Entry Point` and its
   click adds `RTP: Click Entry Point`. The left pad is the swipe pad with its click.
   `RTP: Entry Point` and `Steering` have no click of their own again.
3. **Kept from 90.25:** `RTP: Middle Click` as a mouse pad, the Tap Cover resets, the
   chorded menu chains and `Menu Keys`.
4. **Kept from 90.26:** the 200 ms hold delays with resets at their delay + 50 ms, and
   the reset of the Click Entry Points' outer ring bind on the pad's touch. 90.26's
   third step changed the touch layers, which are gone.

The 90.25 and 90.26 builders stay frozen. This class sits in front of the 90.25 one and
answers its pad steps with nothing.
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
from tools.audit_command_budget import audit_layout                                    # noqa: E402
from tools.convert_runtime_ids import generate_lookup, titles_to_ids, ids_to_titles   # noqa: E402

DELAYS = ROOT / 'findings/2026-10-04-standard-delays/build_candidate.py'
spec = importlib.util.spec_from_file_location('standard_delays_build', DELAYS)
sd = importlib.util.module_from_spec(spec); spec.loader.exec_module(sd)
pb = sd.pb                      # the 90.25 builder, as the 90.26 one loaded it
st = pb.st

# The three layers of the bump, and the 90.25 layers that stay.
GONE = (pb.touch_entry_point('RTP'), pb.touch_entry_point('LTP'), pb.PADS['LTP'][1])
NEW = [title for title in pb.NEW if title not in GONE]
BUMP = pb.PadBumpsAndMenuKeys   # the 90.25 class whose pad steps are skipped


class PadBumpRemoval:
    # --- the 90.25 class's list of new layers, without the three ------------------------------

    def layer(self, name):
        super(BUMP, self).layer(name)
        if name == st.COVER:
            for title in NEW:
                super(BUMP, self).layer(title)

    def build_menu(self):
        super(BUMP, self).build_menu()
        for title in NEW:
            self.menu_helpers.remove(title)

    def build_touch_cleanup(self):
        everything = self.new
        self.new = [n for n in everything if n not in NEW]
        try:
            super(BUMP, self).build_touch_cleanup()
        finally:
            self.new = everything

    # --- its two pad steps -------------------------------------------------------------------

    def build_right_pad(self):
        """Base keeps its click and its touch still adds `RTP: Entry Point`."""

    def build_left_pad(self):
        """Base keeps the swipe pad with its click."""

    # --- the 90.26 steps that don't belong to the bump -----------------------------------------

    def finish(self):
        data = super().finish()
        self.delay_log = sd.standardize(data)
        self.pad_log = sd.click_resets(data)
        cm = data['controller_mappings']
        cm['title'] = cm['title'].replace('pad bumps and menu keys candidate', 'pad bump removal candidate')
        cm['description'] = (
            'Pad bump removal candidate; device verification pending. The pads are as in 90.24: no bump on '
            'touch, and Base has the clicks and the swipes. See findings/2026-10-04-pad-bump-removal/README.md.')
        report = audit_layout(data)
        if report['violations']:
            raise ValueError(report['violations'])
        return data


def Builder(variant):
    return type('Concrete', (PadBumpRemoval, type(pb.Builder(variant))), {})(variant)


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
        stem = HERE / f'{variant}-pad-bump-removal'
        stem.with_suffix('.readable.json').write_text(readable)
        stem.with_suffix('.json').write_text(numeric)
        (HERE / f'{variant}-delays-changed.txt').write_text('\n'.join(b.delay_log + b.pad_log) + '\n')
        if args.vdf:
            subprocess.run(['node', str(ROOT / 'tools/convert_vdf.mjs'), str(stem.with_suffix('.json'))], check=True)
        manifest[variant] = {
            'source_sha256': hashlib.sha256(b.source.read_bytes()).hexdigest(),
            'standard_delays_generator_sha256': hashlib.sha256(DELAYS.read_bytes()).hexdigest(),
            'pad_bumps_and_menu_keys_generator_sha256': hashlib.sha256(sd.BEFORE.read_bytes()).hexdigest(),
            'candidate_sha256': hashlib.sha256(numeric.encode()).hexdigest(),
            'layers_removed': list(GONE),
            'total_layer_count': len(data['controller_mappings']['action_layers']),
            'resolved_references': count, 'device_status': 'UNTESTED'}
        print(f'{variant}: {len(data["controller_mappings"]["action_layers"])} layers, '
              f'{len(b.delay_log)} hold delays or resets, {len(b.pad_log)} click resets')
    (HERE / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')


if __name__ == '__main__':
    main()
