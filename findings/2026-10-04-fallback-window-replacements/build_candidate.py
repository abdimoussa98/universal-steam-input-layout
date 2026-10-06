"""In the fallback's window the drivers and the menu buttons take replacements.

Extends the 10-04 fallback-window builder; it stays frozen. One change to the finished layout,
the author's decision of 2026-10-04 after 90.31 was built:

In `Steering | LS: Fallback Window`, 90.31 had a driver or a menu button remove the window, so
that `Steering | LS: Fallback Hold` underneath answered the button and cleared the Steering
layers. Now the window blocks them until it ends, as every other window does: Start and Select
type Tab and Escape, and the two drivers are the scroll wheel, down on the S driver and up on
the W driver. No layer changes on them.

The Fallback Hold is as it was. So a driver or a menu button pressed after the second still
clears the Steering layers, and one pressed inside the second and still held when the window
ends is answered by the Fallback Hold at that moment.
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
from steam_layout.model import Layout, actions, entries                                # noqa: E402
from tools.audit_command_budget import audit_layout                                    # noqa: E402
from tools.convert_runtime_ids import generate_lookup, titles_to_ids, ids_to_titles   # noqa: E402

WINDOWED = ROOT / 'findings/2026-10-04-fallback-window/build_candidate.py'
spec = importlib.util.spec_from_file_location('fallback_window_build', WINDOWED)
fw = importlib.util.module_from_spec(spec); spec.loader.exec_module(fw)

WINDOW, STEERING = fw.WINDOW, fw.STEERING
# Start is button_escape and Select is button_menu; their keys are the ones the two Steering windows use.
MENU_KEYS = {('switch', 'button_escape'): 'TAB', ('switch', 'button_menu'): 'ESCAPE'}
# The driver whose layer is the S key scrolls down and the W driver scrolls up, as the bumpers do in the
# modifier windows.
DRIVER_SCROLL = {'S Key': 'SCROLL_DOWN', 'W Key': 'SCROLL_UP'}


def replacements(data, variant):
    """The window's drivers and menu buttons: a key or a scroll step where 90.31 removed the window."""
    layout, log = Layout(data), []
    window, alone = layout.active(WINDOW), [fw.remove(WINDOW)]
    drivers = {}
    for source, group in layout.active(STEERING).items():           # which input drives which way
        for name, value in group.get('inputs', {}).items():
            for _, e in entries(value.get('activators', {})):
                for op, target in layout.layer_ops(e):
                    for suffix, wheel in DRIVER_SCROLL.items():
                        if op == 'add_layer' and target.startswith('Steering | ') and target.endswith(suffix):
                            drivers[(source, name)] = wheel
    if sorted(drivers.values()) != sorted(DRIVER_SCROLL.values()):
        raise ValueError(f'{STEERING}: expected one driver for W and one for S, found {drivers}')
    wanted = {**{control: f'key_press {key}, , ' for control, key in MENU_KEYS.items()},
              **{control: f'mouse_wheel {wheel}, , ' for control, wheel in drivers.items()}}
    for (source, name), output in wanted.items():
        acts = window[source]['inputs'][name]['activators']
        if list(acts) != ['Full_Press'] or actions(acts['Full_Press']) != alone:
            raise ValueError(f'{WINDOW} {source}/{name}: expected the press that removes the window, found {acts}')
        window[source]['inputs'][name] = fw.slot(Full_Press={'bindings': {'binding': output}, 'settings': {}})
        log.append(f'{WINDOW} | {source}/{name}: {output.split(",")[0]}, where it removed the window')
    return log


class Replacements:
    """In front of the 90.31 classes: one change to the finished layout."""

    def finish(self):
        data = super().finish()
        self.replacement_log = replacements(data, self.variant)
        cm = data['controller_mappings']
        cm['title'] = cm['title'].replace('fallback window candidate', 'fallback window replacements candidate')
        cm['description'] = (
            'Fallback window replacements candidate; device verification pending. In the fallback\'s window the '
            'drivers scroll and Start and Select type Tab and Escape. '
            'See findings/2026-10-04-fallback-window-replacements/README.md.')
        report = audit_layout(data)
        if report['violations']:
            raise ValueError(report['violations'])
        return data


def Builder(variant):
    return type('Concrete', (Replacements, type(fw.Builder(variant))), {})(variant)


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
        stem = HERE / f'{variant}-fallback-window-replacements'
        stem.with_suffix('.readable.json').write_text(readable)
        stem.with_suffix('.json').write_text(numeric)
        (HERE / f'{variant}-binds-changed.txt').write_text('\n'.join(b.replacement_log) + '\n')
        (HERE / f'{variant}-inputs-changed.txt').write_text('\n'.join(b.required_log) + '\n')
        if args.vdf:
            subprocess.run(['node', str(ROOT / 'tools/convert_vdf.mjs'), str(stem.with_suffix('.json'))], check=True)
        manifest[variant] = {
            'source_sha256': hashlib.sha256(b.source.read_bytes()).hexdigest(),
            'fallback_window_generator_sha256': hashlib.sha256(WINDOWED.read_bytes()).hexdigest(),
            'candidate_sha256': hashlib.sha256(numeric.encode()).hexdigest(),
            'binds_replaced': len(b.replacement_log), 'inputs_given_a_cleanup': b.required_inputs,
            'total_layer_count': len(data['controller_mappings']['action_layers']),
            'resolved_references': count, 'device_status': 'UNTESTED'}
        print(f'{variant}: {len(data["controller_mappings"]["action_layers"])} layers')
        for line in b.replacement_log:
            print('   ', line)
    (HERE / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')


if __name__ == '__main__':
    main()
