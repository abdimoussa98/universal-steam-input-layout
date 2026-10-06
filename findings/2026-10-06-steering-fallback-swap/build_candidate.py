"""`Steering` and its fallback guard swap places: one is on the stack, never both.

Extends the 10-05 steering-four-way-and-open-edges builder; it stays frozen. The author's design
of 2026-10-06, after trying 90.34 on the Deck: the guard's eight-way left stick did not take
effect over `Steering`'s four-way one. "So what I'm going to do is just remove the layer in
between ... the fallback layer will be added first, then it'll remove the steering layer. In the
same way in the fallback layer." Changes to the finished layout:

1. **`Steering`'s up and down hand over.** The repeating press adds the guard and then removes
   `Steering`.

2. **Every bind in the guard that removes it hands back.** It adds `Steering` first and then
   removes the guard: each of the modifier pair pressed with the left stick at centre, and the
   cleanup function on both stick touches (the author: "it would keep them and they would first
   add steering back and remove fallback").

3. **The guard carries what it took from `Steering` underneath**: Start and Select add the
   `Stateful |` Entry Points, and the right pad is the mouse with its touch blocked.

4. **The Gyro Modifier 2 quick tap beeps on the guard's removal too.** `Steering` is not on
   while the guard is, so the beep on `Steering`'s removal alone would stay silent there.

5. **A driver's press in `Steering` removes the three ramp layers before it adds its layer.**
   Since 90.34 turn assist runs in Steering base, and the driver's layer binds the right
   stick's edge, which is where a ramp layer ends. A ramp layer under it stayed on, with the
   gyro off, until the driver was let go: when the driver came inside the 5 ms before the first
   ramp stage, and, since this build, when `Steering` is handed back over a ramp stage.
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
from steam_layout.model import entries                                                 # noqa: E402
from tools.audit_command_budget import audit_layout                                    # noqa: E402
from tools.convert_runtime_ids import generate_lookup, titles_to_ids, ids_to_titles   # noqa: E402

FOUR_WAY = ROOT / 'findings/2026-10-05-steering-four-way-and-open-edges/build_candidate.py'
spec = importlib.util.spec_from_file_location('steering_four_way_build', FOUR_WAY)
fw4 = importlib.util.module_from_spec(spec); spec.loader.exec_module(fw4)
fg = fw4.fg

STEERING, GUARD, KEYS = fg.STEERING, fg.GUARD, fg.KEYS
STICKS = ('joystick', 'right_joystick')
MENU = ('button_menu', 'button_escape')
PAD = 'right_trackpad'
RAMP = ('Gyro Off Ramp Up', 'Turning Ramp Up 0', 'Turning Ramp Up 1')
add, remove, entry, ran, token = fg.add, fg.remove, fg.entry, fg.ran, fg.token


class Swap(fg.Guard):
    """The four changes, on one finished layout. Uses the 90.33 class for its reading helpers."""

    def hand_over(self):
        stick = self.active(STEERING)['joystick']['inputs']
        for direction in KEYS:
            acts = stick[direction]['activators']
            if list(acts) != ['Full_Press'] or ran(acts['Full_Press']) != [add(GUARD)]:
                raise ValueError(f'{STEERING} {direction}: expected the repeating add of 90.34, found {acts}')
            acts['Full_Press']['bindings']['binding'] = list(reversed([add(GUARD), remove(STEERING)]))
        self.log.append(f'{STEERING} | joystick up and down: adds {GUARD}, then removes {STEERING}')

    def hand_back(self, pair):
        guard, back = self.active(GUARD), [add(STEERING), remove(GUARD)]
        controls = list(pair) + [(source, 'touch') for source in STICKS]
        for source, name in controls:
            press = guard[source]['inputs'][name]['activators'].get('Full_Press')
            if not isinstance(press, dict) or ran(press) != [remove(GUARD)] or press['settings'].get('hold_repeats') != '1':
                raise ValueError(f'{GUARD} {source}/{name}: expected the repeating removal of the guard, found {press}')
            press['bindings']['binding'] = list(reversed(back))
        self.log.append(f'{GUARD} | the modifier pair and both stick touches: the removal of the guard adds {STEERING} '
                        f'first ({len(controls)} binds)')

    def carry(self):
        """What the guard got from `Steering` underneath, as its own binds."""
        steering, guard = self.active(STEERING), self.active(GUARD)
        for name in MENU:
            acts = steering['switch']['inputs'][name]['activators']
            adds = [target for _, e in entries(acts) for op, target in self.layout().layer_ops(e) if op == 'add_layer']
            if list(acts) != ['Full_Press'] or len(adds) != 1 or not adds[0].startswith('Stateful | '):
                raise ValueError(f'{STEERING} {name}: expected the add of its Stateful Entry Point, found {acts}')
            if name in guard['switch']['inputs']:
                raise ValueError(f'{GUARD} {name}: already bound')
            guard['switch']['inputs'][name] = copy.deepcopy(steering['switch']['inputs'][name])
        if PAD in guard:
            raise ValueError(f'{GUARD}: already has a right pad group')
        shell = steering[PAD]
        if sorted(shell.get('inputs', {})) != ['touch']:
            raise ValueError(f'{STEERING} right pad: expected only the blocked touch, found {sorted(shell.get("inputs", {}))}')
        group = self.new_group(GUARD, PAD, shell)
        group['inputs'] = copy.deepcopy(shell['inputs'])
        self.log.append(f'{GUARD}: Start and Select add the Stateful Entry Points and the right pad is the mouse with its '
                        f'touch blocked, as in {STEERING}')

    new_group = fg.fw.Fallback.new_group

    def drivers_end_turn_assist(self, pair):
        steering = self.active(STEERING)
        for source, name in pair:
            press = steering[source]['inputs'][name]['activators']['Full_Press']
            commands = ran(press)
            if len(commands) != 1 or 'add_layer ' + token('Steering | ') [:-2] not in commands[0]:
                raise ValueError(f'{STEERING} {source}/{name}: expected the add of the driver\'s layer alone, found {commands}')
            press['bindings']['binding'] = list(reversed([remove(title) for title in RAMP] + commands))
        self.log.append(f'{STEERING} | the two drivers: the press removes the three ramp layers, then adds its layer')

    def quick_tap_beep(self):
        count = 0
        for found in self.every_entry():
            stored = found['bindings']['binding']
            if isinstance(stored, list) and remove(GUARD) in stored and fg.beeping(STEERING) in stored:
                stored[stored.index(remove(GUARD))] = fg.beeping(GUARD)
                count += 1
        if count != 4:
            raise ValueError(f'expected four Gyro Modifier 2 quick taps, found {count}')
        self.log.append(f'{count} Gyro Modifier 2 quick taps beep on the removal of {GUARD} as well')

    def run(self):
        pair = self.pair()
        self.hand_over()
        self.hand_back(pair)
        self.carry()
        self.quick_tap_beep()
        self.drivers_end_turn_assist(pair)
        return self.log


class Front:
    """In front of the 90.34 classes: the changes to the finished layout."""

    def finish(self):
        data = super().finish()
        self.swap_log = Swap(data, self.variant).run()
        cm = data['controller_mappings']
        cm['title'] = cm['title'].replace('four-way and open edges candidate', 'fallback swap candidate')
        cm['description'] = (
            'Fallback swap candidate; device verification pending. Steering and its fallback guard swap places, so '
            'the guard\'s eight-way stick is never over Steering\'s four-way one. '
            'See findings/2026-10-06-steering-fallback-swap/README.md.')
        report = audit_layout(data)
        if report['violations']:
            raise ValueError(report['violations'])
        return data


def Builder(variant):
    return type('Concrete', (Front, type(fw4.Builder(variant))), {})(variant)


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
        stem = HERE / f'{variant}-fallback-swap'
        stem.with_suffix('.readable.json').write_text(readable)
        stem.with_suffix('.json').write_text(numeric)
        (HERE / f'{variant}-binds-changed.txt').write_text('\n'.join(b.swap_log) + '\n')
        (HERE / f'{variant}-inputs-changed.txt').write_text('\n'.join(b.required_log) + '\n')
        if args.vdf:
            subprocess.run(['node', str(ROOT / 'tools/convert_vdf.mjs'), str(stem.with_suffix('.json'))], check=True)
        manifest[variant] = {
            'source_sha256': hashlib.sha256(b.source.read_bytes()).hexdigest(),
            'four_way_generator_sha256': hashlib.sha256(FOUR_WAY.read_bytes()).hexdigest(),
            'candidate_sha256': hashlib.sha256(numeric.encode()).hexdigest(),
            'inputs_given_a_cleanup': b.required_inputs,
            'total_layer_count': len(data['controller_mappings']['action_layers']),
            'resolved_references': count, 'device_status': 'UNTESTED'}
        print(f'{variant}: {len(data["controller_mappings"]["action_layers"])} layers')
        for line in b.swap_log:
            print('   ', line)
    (HERE / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')


if __name__ == '__main__':
    main()
