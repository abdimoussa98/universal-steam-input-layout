"""The menu chain on every press, and the right pad's touch in the Double Tap windows.

Extends the 10-04 pad-bump-removal builder; it stays frozen. Two changes the author
approved on 2026-10-04:

1. **The chorded menu chain runs on every press of the second menu button.** In 90.25
   the chain's Entry Point (`Menu Left!Right: Entry Point`) was added once, with the Fn
   layer, and removed itself on its first Release. Every later press in the same hold
   went to the Fn layer's own bind, which types the key at once, so no tap, hold or
   double tap, and no `Menu Keys` (found by the author on the Deck). Now:
   - The Fn layer's bind for the other menu button adds the chain's Entry Point, where it
     typed Enter or Backspace ("from the FN layer, it'll automatically add the menu
     layer", the author's design of 2026-10-03).
   - The plain Entry Point adds the chain's Entry Point only with the other button's own
     press, the press that comes before the Fn layer is up. Its hold and its two
     stick-touch Releases add the Fn layer alone, as before 90.25.
   - `Steering` and `Cursor Gyro` keep what they had: the `Stateful |` Entry Points add
     their own copies of the Fn layers, `Stateful | Menu Left: Fn Layer` and
     `Stateful | Menu Right: Fn Layer`, which type the key at once. `Menu Keys` is
     entered from Base and `Gyro` only. Two layers, at the end of the list: 89.

2. **In a Double Tap window the right pad's touch follows the stick touches.** It was a
   block: an empty press bind. It is now a Release that removes the window and the pad's
   own layers, `RTP: Entry Point`, `RTP: Tap Cover` and `RTP: Circular Scroll`, as each
   stick's touch Release removes the window and that stick's three. `RTP: Double Tap`
   is left out: it is the pad's own window and binds no touch. The clicks stay blocked
   and the left pad's swipes still type their keys (R149, R172).

The first change is built inside the 90.25 build, before the required cleanups run, so
the two new layers get theirs like any other. The second is a change to the finished
layout.
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
from steam_layout.model import Layout, always_on_layers                                # noqa: E402
from tools.audit_command_budget import audit_layout                                    # noqa: E402
from tools.convert_runtime_ids import generate_lookup, titles_to_ids, ids_to_titles   # noqa: E402

REMOVAL = ROOT / 'findings/2026-10-04-pad-bump-removal/build_candidate.py'
spec = importlib.util.spec_from_file_location('pad_bump_removal_build', REMOVAL)
br = importlib.util.module_from_spec(spec); spec.loader.exec_module(br)
pb, sd = br.pb, br.sd           # the 90.25 and 90.26 builders, as the 90.27 one loaded them
st, rc, tc, cg = pb.st, pb.rc, pb.tc, pb.cg
BUMP = br.BUMP

STATEFUL_FN = {side: f'Stateful | Menu {side}: Fn Layer' for side in st.MENU}
ADDED = list(STATEFUL_FN.values())
# The right pad's own layers, which a touch Release in a window clears with the window.
PAD_TRIO = ('RTP: Entry Point', 'RTP: Tap Cover', 'RTP: Circular Scroll')
PAD_WINDOW = 'RTP: Double Tap'  # the pad's own window: no touch bind


def token(title):
    return '{{Base::' + title + '}}'


class EveryPress:
    """Built inside the 90.25 build: after its chains, before its last step and the required cleanups."""

    def build_every_press(self, first, second):
        m = self.m
        entry = pb.chain(first, second)[0]
        # At this point of the build the key is still an overlay layer's (`Menu Right: Enter`,
        # `Menu Left: Backspace`); the fix pipeline, which runs next, types it in place (R138).
        overlay = f'Menu {second}: {pb.CHAINS[(first, second)][1]}'
        plain, fn = st.entry_point(first), st.fn_layer(first)
        stateful, copy = cg.stateful_entry_point(first), STATEFUL_FN[first]
        second_button = st.MENU[second][0]

        # The Stateful Entry Point gets today's Fn layer for itself, which types the key at once.
        self.copy_layer(fn, copy, {token(fn): token(copy)})
        moved = 0
        for group in self.sources(stateful).values():
            for binding in group.get('inputs', {}).values():
                for _, e in m.entries(binding):
                    commands = m.commands(e)
                    if len(commands) <= 5 and any(token(fn) in c for c in commands):     # its adds and its reset, not the clears
                        swapped = [c.replace(token(fn), token(copy)) for c in commands]
                        e['bindings']['binding'] = swapped if isinstance(e['bindings']['binding'], list) else swapped[0]
                        moved += 1
        if moved != 5:
            raise ValueError(f'{stateful}: expected four adds and one reset of {fn}, found {moved}')

        # The Fn layer's bind for the other button adds the chain's Entry Point, on every press.
        chord = self.sources(fn)['switch']['inputs'][second_button]['activators']['chord']
        if [c for c in m.commands(chord) if c != m.EMPTY] != [m.op('add', overlay)]:
            raise ValueError(f'{fn} {second_button}: expected the chord that adds {overlay}, found {m.commands(chord)}')
        chord['bindings']['binding'] = m.op('add', entry)

        # The plain Entry Point adds it only with the other button's own press, before the Fn layer is up.
        dropped = 0
        for source, group in self.sources(plain).items():
            for name, binding in group.get('inputs', {}).items():
                for _, e in m.entries(binding):
                    commands = m.commands(e)
                    if m.op('add', entry) in commands and (source, name) != ('switch', second_button):
                        left = [c for c in commands if c != m.op('add', entry)]
                        e['bindings']['binding'] = left if len(left) > 1 else left[0]
                        dropped += 1
        if dropped != 3:
            raise ValueError(f'{plain}: expected three other adds of {entry}, found {dropped}')

    def build_chain_cleanups(self, data):
        # The last step of the 90.25 build. After it the required-cleanup fixes number new groups
        # themselves, so every group this class adds has to exist before it runs.
        for first, second in pb.CHAINS:
            self.build_every_press(first, second)
        super().build_chain_cleanups(data)


def window_pad_touch(data):
    """In every window but the pad's own, the right pad's touch is a Release: the window, then the pad's layers."""
    layout, log = Layout(data), []
    mouse = layout.active(layout.base)['right_trackpad']['mode']
    for title in always_on_layers(layout):
        if title == PAD_WINDOW:
            continue
        group = layout.active(title)['right_trackpad']
        touch = group['inputs'].get('touch', {}).get('activators', {})
        if group['mode'] != mouse or list(touch) != ['Full_Press'] or 'empty_binding' not in json.dumps(touch):
            raise ValueError(f'{title}: expected the mouse pad with its touch blocked, found {group["mode"]} {touch}')
        commands = [f'controller_action remove_layer {token(name)} 0 0, , ' for name in (title,) + PAD_TRIO]
        group['inputs']['touch'] = {'activators': {'release': {'bindings': {'binding': list(reversed(commands))},
                                                               'settings': {'haptic_intensity': '0'}}},
                                    'disabled_activators': {}}
        log.append(f'{title} | right_trackpad/touch: a Release that removes the window, ' + ', '.join(PAD_TRIO))
    return log


class Front:
    """In front of the 90.27 class: the two new layers, and the change to the finished layout."""

    def layer(self, name):
        super().layer(name)
        if name == st.COVER:
            for title in ADDED:
                super(BUMP, self).layer(title)

    def finish(self):
        data = super().finish()
        self.window_log = window_pad_touch(data)
        cm = data['controller_mappings']
        cm['title'] = cm['title'].replace('pad bump removal candidate', 'menu chain and window pads candidate')
        cm['description'] = (
            'Menu chain and window pads candidate; device verification pending. The chorded menu chain runs on '
            "every press, and a Double Tap window's right-pad touch is a Release. "
            'See findings/2026-10-04-menu-chain-and-window-pads/README.md.')
        report = audit_layout(data)
        if report['violations']:
            raise ValueError(report['violations'])
        return data


def Builder(variant):
    bases = (Front, br.PadBumpRemoval, pb.Release, rc.RequiredCleanups, EveryPress, BUMP, type(tc.Builder(variant)))
    return type('Concrete', bases, {})(variant)


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
        stem = HERE / f'{variant}-menu-chain-and-window-pads'
        stem.with_suffix('.readable.json').write_text(readable)
        stem.with_suffix('.json').write_text(numeric)
        (HERE / f'{variant}-windows-changed.txt').write_text('\n'.join(b.window_log) + '\n')
        (HERE / f'{variant}-inputs-changed.txt').write_text('\n'.join(b.required_log) + '\n')
        if args.vdf:
            subprocess.run(['node', str(ROOT / 'tools/convert_vdf.mjs'), str(stem.with_suffix('.json'))], check=True)
        manifest[variant] = {
            'source_sha256': hashlib.sha256(b.source.read_bytes()).hexdigest(),
            'pad_bump_removal_generator_sha256': hashlib.sha256(REMOVAL.read_bytes()).hexdigest(),
            'candidate_sha256': hashlib.sha256(numeric.encode()).hexdigest(),
            'new_layers': ADDED, 'windows_changed': len(b.window_log),
            'inputs_given_a_cleanup': b.required_inputs,
            'total_layer_count': len(data['controller_mappings']['action_layers']),
            'resolved_references': count, 'device_status': 'UNTESTED'}
        print(f'{variant}: {len(data["controller_mappings"]["action_layers"])} layers, '
              f'{len(b.window_log)} windows changed, {b.required_inputs} inputs given a cleanup')
    (HERE / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')


if __name__ == '__main__':
    main()
