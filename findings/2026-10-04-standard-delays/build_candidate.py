"""Standard hold delays, a reset for the pad clicks' outer bind, and touch layers with no delay.

Extends the 10-04 pad-bumps-and-menu-keys builder; it stays frozen. The author's
decisions (2026-10-04), after the audit of every delayed add in the README here:

1. **Every hold delay over 200 ms is 200 ms**: the bumper Modifier 0 and 1 (300 ms, also
   their `Gyro |` copies) and the Steering Modifier 0 and 1 (250 ms).
2. **Both menu buttons into `Menu Keys` take 200 ms**, not 150.
3. **Every reset repeats at its delay + 50 ms** (R121). The first build of this release
   had + 5; the author took it back the same day.
4. **The two Click Entry Points get a reset for their outer ring bind**, the one with the
   5 ms delay that gives the centre priority. It is on the pad's touch, not on the ring
   ("you can put it on the touch bind it doesn't need to be on the edge"): a Regular Press
   that removes only the layer the outer bind adds, every 55 ms.
5. **The two touch hand-over layers lose that delay.** Their outer bind starts at the inner
   bind's radius, so the two ranges no longer overlap and neither needs priority. The bump
   stays where a click is the centre click. No delayed add, so no reset.

Left alone: the 150 ms delays (the second-press layers' covers, the Tap Covers of the
stick and pad Entry Points) and the ramp-up layers ("The ramp ups we will not touch").

A "hold delay" here is a delayed `add_layer` that has a reset on the same input: a
Hold to Repeat entry that removes only the layer the delay adds (R120). A delayed
activator with no such reset is not one and keeps its time: the ring binds' 5 ms, the
Double Tap windows' own timers, the 1500 ms Fallback Hold.
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

BEFORE = ROOT / 'findings/2026-10-04-pad-bumps-and-menu-keys/build_candidate.py'
spec = importlib.util.spec_from_file_location('pad_bumps_and_menu_keys_build', BEFORE)
pb = importlib.util.module_from_spec(spec); spec.loader.exec_module(pb)

HOLD_MS = 200                   # the longest hold delay, and both menu buttons into Menu Keys
RESET_MARGIN_MS = 50            # a reset repeats this long after its delay (R121)
RING_DELAY_MS = 5               # the outer ring bind's delay in the Click Entry Points
UNTOUCHED = 'Ramp Up'           # in a layer's title: the ramp-up layers keep their delay and reset
# a pad's Click Entry Point, its source, and the layer its delayed outer bind adds
CLICK_LAYERS = (('RTP: Click Entry Point', 'right_trackpad', 'RTP: Mouse Buttons'),
                ('LTP: Click Entry Point', 'left_trackpad', 'LTP: Arrow Keys'))
TOUCH_LAYERS = (('RTP: Touch Entry Point', 'right_trackpad'), ('LTP: Touch Entry Point', 'left_trackpad'))


def delay_of(entry):
    return int((entry.get('settings') or {}).get('delay_start') or 0)


def holds(layout):
    """Every hold delay: (layer, source, input, the delayed entry, its resets), outside the ramp-up layers."""
    for title in layout.presets:
        if UNTOUCHED in title:
            continue
        for source, group in layout.active(title).items():
            for name, slot in group.get('inputs', {}).items():
                found = [(entry, layout.layer_ops(entry)) for _, entry in entries(slot.get('activators', {}))]
                for entry, ops in found:
                    adds = [layer for op, layer in ops if op == 'add_layer']
                    resets = [reset for reset, removed in found
                              if (reset.get('settings') or {}).get('hold_repeats') == '1' and not delay_of(reset)
                              and any(removed == [('remove_layer', target)] for target in adds)]
                    if delay_of(entry) and resets:
                        yield title, source, name, entry, adds, resets


def standardize(data):
    """Set the hold delays and the reset rates in place; returns what changed, as lines."""
    log = []
    for title, source, name, entry, adds, resets in holds(Layout(data)):
        before = delay_of(entry)
        delay = HOLD_MS if before > HOLD_MS or pb.MENU_KEYS in adds else before
        entry['settings']['delay_start'] = str(delay)
        rates = {reset['settings'].get('repeat_rate') for reset in resets}
        for reset in resets:
            reset['settings']['repeat_rate'] = str(delay + RESET_MARGIN_MS)
        if before != delay or rates != {str(delay + RESET_MARGIN_MS)}:
            log.append(f'{title} | {source}/{name}: delay {before} -> {delay} ms, '
                       f'reset {"/".join(sorted(map(str, rates)))} -> {delay + RESET_MARGIN_MS} ms')
    return log


def ring(layout, title, source):
    """A pad layer's two ring Soft Presses: the inverted inner one, and the outer one with the 5 ms delay."""
    inner, outer = layout.active(title)[source]['inputs']['edge']['activators']['Soft_Press']
    if inner['settings'].get('edge_binding_invert') != '1' or delay_of(inner) \
            or outer['settings'].get('edge_binding_invert') == '1' or delay_of(outer) != RING_DELAY_MS:
        raise ValueError(f'{title}: the ring binds are not the two this build expects')
    return inner, outer


def click_resets(data):
    """The reset of the Click Entry Points' outer bind, on the pad's touch (R120)."""
    layout, log = Layout(data), []
    for title, source, target in CLICK_LAYERS:
        _, outer = ring(layout, title, source)
        add = [action for action in actions(outer) if 'add_layer' in action]
        touch = layout.active(title)[source]['inputs']['touch']['activators']
        if ('add_layer', target) not in layout.layer_ops(outer) or len(add) != 1 or list(touch) != ['release']:
            raise ValueError(f'{title}: not the outer bind or the touch this build expects')
        touch['Full_Press'] = {
            'bindings': {'binding': add[0].replace('add_layer', 'remove_layer', 1)},
            'settings': {'hold_repeats': '1', 'repeat_rate': str(RING_DELAY_MS + RESET_MARGIN_MS),
                         'interruptable': '0', 'haptic_intensity': '0'}}
        log.append(f'{title} | {source}/touch: a reset that removes {target} every {RING_DELAY_MS + RESET_MARGIN_MS} ms')
    return log


def touch_rings(data):
    """The touch hand-over layers: the outer bind starts where the inner one ends, with no delay."""
    layout, log = Layout(data), []
    for title, source in TOUCH_LAYERS:
        inner, outer = ring(layout, title, source)
        before = outer['settings']['activation_threshold']
        outer['settings']['activation_threshold'] = inner['settings']['activation_threshold']
        del outer['settings']['delay_start']
        log.append(f'{title} | {source}/edge: the outer bind at {outer["settings"]["activation_threshold"]}, '
                   f'not {before}, with no delay')
    return log


class StandardDelays:
    def finish(self):
        data = super().finish()
        self.delay_log = standardize(data)
        self.pad_log = click_resets(data) + touch_rings(data)
        cm = data['controller_mappings']
        cm['title'] = cm['title'].replace('pad bumps and menu keys candidate', 'standard delays candidate')
        cm['description'] = (
            'Standard delays candidate; device verification pending. No hold delay is over 200 ms, the pad '
            "clicks' outer bind has a reset, and a pad touch at the rim hands over at once. "
            'See findings/2026-10-04-standard-delays/README.md.')
        report = audit_layout(data)
        if report['violations']:
            raise ValueError(report['violations'])
        return data


def Builder(variant):
    return type('Concrete', (StandardDelays, type(pb.Builder(variant))), {})(variant)


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
        stem = HERE / f'{variant}-standard-delays'
        stem.with_suffix('.readable.json').write_text(readable)
        stem.with_suffix('.json').write_text(numeric)
        (HERE / f'{variant}-delays-changed.txt').write_text('\n'.join(b.delay_log + b.pad_log) + '\n')
        if args.vdf:
            subprocess.run(['node', str(ROOT / 'tools/convert_vdf.mjs'), str(stem.with_suffix('.json'))], check=True)
        manifest[variant] = {
            'source_sha256': hashlib.sha256(b.source.read_bytes()).hexdigest(),
            'pad_bumps_and_menu_keys_generator_sha256': hashlib.sha256(BEFORE.read_bytes()).hexdigest(),
            'candidate_sha256': hashlib.sha256(numeric.encode()).hexdigest(),
            'delays_changed': len(b.delay_log), 'pad_layers_changed': len(b.pad_log),
            'total_layer_count': len(data['controller_mappings']['action_layers']),
            'resolved_references': count, 'device_status': 'UNTESTED',
            'timing_ms': {'longest_hold_delay': HOLD_MS, 'menu_keys_hold': HOLD_MS, 'reset_margin': RESET_MARGIN_MS,
                          'click_outer_bind_reset': RING_DELAY_MS + RESET_MARGIN_MS}}
        print(f'{variant}: {len(data["controller_mappings"]["action_layers"])} layers, '
              f'{len(b.delay_log)} hold delays or resets changed, {len(b.pad_log)} pad layers changed')
    (HERE / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')


if __name__ == '__main__':
    main()
