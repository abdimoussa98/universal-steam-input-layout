"""The Tap Cover resets stop pulsing, and the beep moves to the flag that beeps.

Extends the 10-04 menu-chain-and-window-pads builder; it stays frozen. Two changes to the
finished layout, both from the author's Deck run of 90.28 on 2026-10-04:

1. **The Tap Cover reset is silent.** The reset on the touch of `LST: Entry Point`,
   `RST: Entry Point` and `RTP: Entry Point` (90.25) stated no haptic. On the right pad it
   pulsed at every touch: the bind repeats, so it fires as the Entry Point lands on the
   thumb (A6). All three now state `haptic_intensity` 0. The reset itself stays on all
   three, by the author's decision.

2. **The beep is the second flag of a layer command, not the first.** A layer command ends
   in two flags, `add_layer <layer> <first> <second>`. This repo's documentation had the
   first as the beep and the second as the on-screen name. The Steam client's own message
   for the command lists them the other way round: `display`, then `beep` (A49). Every
   transition, the stateful exits and the `Menu Keys` entry were written `1 0` to beep
   without a name (R161), so on the Deck they showed a name and stayed silent. Each `1 0`
   becomes `0 1`. `Gyro`'s toggle is `1 1` and the Fn layers' add is `0 1`, both the
   author's own; they are left alone.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
from steam_layout.model import Layout, actions, entries                                # noqa: E402
from tools.audit_command_budget import audit_layout                                    # noqa: E402
from tools.convert_runtime_ids import generate_lookup, titles_to_ids, ids_to_titles   # noqa: E402

CHAIN = ROOT / 'findings/2026-10-04-menu-chain-and-window-pads/build_candidate.py'
spec = importlib.util.spec_from_file_location('menu_chain_and_window_pads_build', CHAIN)
mw = importlib.util.module_from_spec(spec); spec.loader.exec_module(mw)

# The Entry Points whose touch has the Tap Cover reset, and the source it is on.
COVER_RESETS = (('LST', 'joystick'), ('RST', 'right_joystick'), ('RTP', 'right_trackpad'))
# A layer command and its two flags: the on-screen name, then the beep.
FLAGS = re.compile(r'^(controller_action (?:add_layer|remove_layer|hold_layer) (?:\{\{.+?\}\}|\d+)) (\d) (\d)(, .*)$')
NAME_ONLY, BEEP_ONLY = ('1', '0'), ('0', '1')
BEEPS = 22          # per layout: six adds and sixteen removals


def token(title):
    return '{{Base::' + title + '}}'


def quiet_cover_resets(data):
    """The three Tap Cover resets state `haptic_intensity` 0."""
    layout, log = Layout(data), []
    for prefix, source in COVER_RESETS:
        title = f'{prefix}: Entry Point'
        touch = layout.active(title)[source]['inputs']['touch']['activators']
        reset = touch.get('Full_Press')
        want = f'controller_action remove_layer {token(prefix + ": Tap Cover")} 0 0, , '
        if not isinstance(reset, dict) or actions(reset) != [want] or 'haptic_intensity' in reset['settings'] \
                or reset['settings'].get('hold_repeats') != '1':
            raise ValueError(f'{title}: expected the repeating Tap Cover reset with no haptic stated, found {reset}')
        reset['settings']['haptic_intensity'] = '0'
        log.append(f'{title} | {source}/touch: the reset states haptic_intensity 0')
    return log


def beep_flags(data):
    """Every layer command written `1 0` becomes `0 1`: the beep, and no name on screen."""
    layout, log = Layout(data), []
    for title in layout.presets:
        for source, group in layout.active(title).items():
            for name, slot in group.get('inputs', {}).items():
                for kind, entry in entries(slot.get('activators', {})):
                    commands, changed = actions(entry), []
                    for i, command in enumerate(commands):
                        match = FLAGS.match(command)
                        if match and (match.group(2), match.group(3)) == NAME_ONLY:
                            commands[i] = f'{match.group(1)} {" ".join(BEEP_ONLY)}{match.group(4)}'
                            changed.append(commands[i])
                    if not changed:
                        continue
                    stored = entry['bindings']['binding']
                    entry['bindings']['binding'] = commands if isinstance(stored, list) else commands[0]
                    for command in changed:
                        log.append(f'{title} | {source}/{name} {kind}: {command.split(",")[0][len("controller_action "):]}')
    if len(log) != BEEPS:
        raise ValueError(f'expected {BEEPS} layer commands with the name flag alone, found {len(log)}')
    return log


class Feedback:
    """In front of the 90.28 classes: two changes to the finished layout."""

    def finish(self):
        data = super().finish()
        self.reset_log = quiet_cover_resets(data)
        self.beep_log = beep_flags(data)
        cm = data['controller_mappings']
        cm['title'] = cm['title'].replace('menu chain and window pads candidate', 'quiet resets and beeps candidate')
        cm['description'] = (
            'Quiet resets and beeps candidate; device verification pending. The Tap Cover resets state no '
            'haptic, and the transitions beep on the second flag. '
            'See findings/2026-10-04-quiet-resets-and-beeps/README.md.')
        report = audit_layout(data)
        if report['violations']:
            raise ValueError(report['violations'])
        return data


def Builder(variant):
    return type('Concrete', (Feedback, type(mw.Builder(variant))), {})(variant)


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
        stem = HERE / f'{variant}-quiet-resets-and-beeps'
        stem.with_suffix('.readable.json').write_text(readable)
        stem.with_suffix('.json').write_text(numeric)
        (HERE / f'{variant}-feedback-changed.txt').write_text('\n'.join(b.reset_log + b.beep_log) + '\n')
        (HERE / f'{variant}-inputs-changed.txt').write_text('\n'.join(b.required_log) + '\n')
        if args.vdf:
            subprocess.run(['node', str(ROOT / 'tools/convert_vdf.mjs'), str(stem.with_suffix('.json'))], check=True)
        manifest[variant] = {
            'source_sha256': hashlib.sha256(b.source.read_bytes()).hexdigest(),
            'menu_chain_generator_sha256': hashlib.sha256(CHAIN.read_bytes()).hexdigest(),
            'candidate_sha256': hashlib.sha256(numeric.encode()).hexdigest(),
            'resets_silenced': len(b.reset_log), 'beep_flags_moved': len(b.beep_log),
            'inputs_given_a_cleanup': b.required_inputs,
            'total_layer_count': len(data['controller_mappings']['action_layers']),
            'resolved_references': count, 'device_status': 'UNTESTED'}
        print(f'{variant}: {len(data["controller_mappings"]["action_layers"])} layers, '
              f'{len(b.reset_log)} resets silenced, {len(b.beep_log)} beep flags moved')
    (HERE / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')


if __name__ == '__main__':
    main()
