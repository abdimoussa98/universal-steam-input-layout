"""Steering base opens its stick edges, reads the left stick four ways, and adds the fallback at once.

Extends the 10-05 steering-fallback-guard builder; it stays frozen. The author's design of
2026-10-05, after 90.33 was built: "the behavior is kind of swapping the up and down behavior on
the stick with the left and right behavior on the bumper/triggers. If you deflect the stick up or
down you be in fall out unless you press the bumpers/trigger and if you are in steering base itll
be the opposite." Four changes to the finished layout:

1. **`Steering` no longer blocks the stick edges.** Its empty binding on the left and on the right
   stick's edge goes, so the edge binds of the action set come through in Steering base and in
   the fallback guard, which leaves both edges open (author: "the fallback is not one that would
   get the edges blocked"). Every other Steering layer binds its edges already.

2. **`Steering`'s left stick is four-way**: `layout` 0, "Radial Without Overlap". A diagonal presses
   only the nearest direction, so steering with the stick tilted up a little stays A or D.

3. **Up and down add the fallback guard at once**, with a repeating press and the strong pulse,
   where 90.33 had July's 100 ms chord and its reset.

4. **The fallback guard states eight-way**: `layout` 1, "Radial With Overlap", Steam's default.

The guard's bumpers are as 90.33 built them: a chord on the left stick being out adds the Gyro
modifier, and a repeating press removes the guard.
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
from steam_layout.model import Layout, actions                                        # noqa: E402
from tools.audit_command_budget import audit_layout                                    # noqa: E402
from tools.convert_runtime_ids import generate_lookup, titles_to_ids, ids_to_titles   # noqa: E402

GUARDED = ROOT / 'findings/2026-10-05-steering-fallback-guard/build_candidate.py'
spec = importlib.util.spec_from_file_location('steering_fallback_guard_build', GUARDED)
fg = importlib.util.module_from_spec(spec); spec.loader.exec_module(fg)

STEERING, GUARD, KEYS = fg.STEERING, fg.GUARD, fg.KEYS
STICKS = ('joystick', 'right_joystick')
# The D-pad's Directional Pad Layout, as the Steam client numbers its choices (read on 2026-10-05).
FOUR_WAY, EIGHT_WAY = '0', '1'          # Radial Without Overlap, Radial With Overlap
REPEAT_MS = 50
EMPTY = fg.EMPTY


def changes(data):
    """The four changes, on one finished layout. Returns what each did."""
    layout, log = Layout(data), []
    steering, guard = layout.active(STEERING), layout.active(GUARD)
    for source in STICKS:                                               # 1: the edges
        acts = steering[source]['inputs']['edge']['activators']
        if list(acts) != ['Full_Press'] or actions(acts['Full_Press']) != [EMPTY] or acts['Full_Press'].get('settings'):
            raise ValueError(f'{STEERING} {source} edge: expected the empty block, found {acts}')
        del steering[source]['inputs']['edge']
        if 'edge' in guard[source]['inputs']:
            raise ValueError(f'{GUARD} {source}: expected an open edge')
    log.append(f'{STEERING} | both stick edges: the empty block is gone; the action set\'s edge binds come through')
    for title, group, value in ((STEERING, steering['joystick'], FOUR_WAY), (GUARD, guard['joystick'], EIGHT_WAY)):
        if group['mode'] != 'dpad' or 'layout' in group['settings']:    # 2 and 4: the layout
            raise ValueError(f'{title} joystick: expected a D-pad that states no layout, found {group["settings"]}')
        group['settings']['layout'] = value
    log.append(f'{STEERING} | joystick: four-way (layout {FOUR_WAY}); {GUARD} | joystick: eight-way (layout {EIGHT_WAY})')
    stick = steering['joystick']['inputs']
    for direction in KEYS:                                              # 3: the add
        acts = stick[direction]['activators']
        if sorted(acts) != ['Full_Press', 'chord'] or acts['chord']['settings'].get('delay_start') != str(fg.ADD_MS) \
                or fg.ran(acts['chord']) != [fg.add(GUARD)] or fg.ran(acts['Full_Press']) != [fg.remove(GUARD)]:
            raise ValueError(f'{STEERING} {direction}: expected the delayed add and its reset of 90.33, found {acts}')
        stick[direction] = fg.slot(Full_Press=fg.entry([fg.add(GUARD)], hold_repeats=1, repeat_rate=REPEAT_MS,
                                                       interruptable=0, haptic_intensity=3))
    log.append(f'{STEERING} | joystick up and down: a press repeating every {REPEAT_MS} ms adds {GUARD} at once, with a '
               f'strong pulse')
    return log


class Front:
    """In front of the 90.33 classes: the changes to the finished layout."""

    def finish(self):
        data = super().finish()
        self.four_way_log = changes(data)
        cm = data['controller_mappings']
        cm['title'] = cm['title'].replace('fallback guard candidate', 'four-way and open edges candidate')
        cm['description'] = (
            'Four-way and open edges candidate; device verification pending. Steering base reads the left stick '
            'four ways, leaves both stick edges open and adds the fallback at once. '
            'See findings/2026-10-05-steering-four-way-and-open-edges/README.md.')
        report = audit_layout(data)
        if report['violations']:
            raise ValueError(report['violations'])
        return data


def Builder(variant):
    return type('Concrete', (Front, type(fg.Builder(variant))), {})(variant)


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
        stem = HERE / f'{variant}-four-way-and-open-edges'
        stem.with_suffix('.readable.json').write_text(readable)
        stem.with_suffix('.json').write_text(numeric)
        (HERE / f'{variant}-binds-changed.txt').write_text('\n'.join(b.four_way_log) + '\n')
        (HERE / f'{variant}-inputs-changed.txt').write_text('\n'.join(b.required_log) + '\n')
        if args.vdf:
            subprocess.run(['node', str(ROOT / 'tools/convert_vdf.mjs'), str(stem.with_suffix('.json'))], check=True)
        manifest[variant] = {
            'source_sha256': hashlib.sha256(b.source.read_bytes()).hexdigest(),
            'fallback_guard_generator_sha256': hashlib.sha256(GUARDED.read_bytes()).hexdigest(),
            'candidate_sha256': hashlib.sha256(numeric.encode()).hexdigest(),
            'inputs_given_a_cleanup': b.required_inputs,
            'total_layer_count': len(data['controller_mappings']['action_layers']),
            'resolved_references': count, 'device_status': 'UNTESTED'}
        print(f'{variant}: {len(data["controller_mappings"]["action_layers"])} layers')
        for line in b.four_way_log:
            print('   ', line)
    (HERE / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')


if __name__ == '__main__':
    main()
