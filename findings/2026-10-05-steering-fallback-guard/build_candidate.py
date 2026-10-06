"""The Steering fallback is a layer the stick brings in and the bumpers take out.

Extends the 10-04 fallback-window-replacements builder; it stays frozen. The plan is
plans/2026-10-04-steering-fallback-layer.md, the author's design of 2026-10-04 and 2026-10-05,
after the July layout (findings/2026-10-04-july-stick-clears/README.md). It walks back the
fallback window of 90.31 and 90.32. All changes are to the finished layout:

1. **One guard layer.** `Steering | LS: Entry Guard` becomes `Steering | LS: Fallback Guard`.
   `Steering | LS: Fallback Hold` and `Steering | LS: Fallback Window` are deleted: 88 layers.

2. **`Steering` brings it in.** The left stick's up and down add the guard after 100 ms, with a
   strong pulse, by a chord on the left stick being out; a repeating press on the same input
   is its reset (R120). A driver only adds its own layer. The transition that enters
   `Steering` no longer adds a guard.

3. **The guard.** Up and down type W and S, with no Release: letting the stick go leaves the
   guard on. Each of the modifier pair adds its Gyro modifier while the left stick is out, and
   removes the guard, with a strong pulse, when it is at centre; `Steering`'s driver bind then
   answers the button. Start and Select are not bound, so `Steering`'s menu flow comes through.
   Both stick touches carry a cleanup function that removes the guard, held back while the
   left stick is out.

4. **The Gyro Modifier 2 quick tap clears to Base from there.** Its Release also removes the
   other Gyro Modifier 2 layer, the four Base modifiers, the guard and `Steering`, with the
   beep on `Steering` as well as on `Gyro`.
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
from steam_layout.model import Layout, actions, entries, map_title                     # noqa: E402
from tools.audit_command_budget import audit_layout                                    # noqa: E402
from tools.convert_runtime_ids import generate_lookup, titles_to_ids, ids_to_titles   # noqa: E402

REPLACEMENTS = ROOT / 'findings/2026-10-04-fallback-window-replacements/build_candidate.py'
spec = importlib.util.spec_from_file_location('fallback_window_replacements_build', REPLACEMENTS)
rp = importlib.util.module_from_spec(spec); spec.loader.exec_module(rp)
fw = rp.fw

RENAME = fw.RENAME
STEERING, HOLD, WINDOW = fw.STEERING, fw.HOLD, fw.WINDOW
ENTRY_GUARD = fw.GUARD
GUARD = 'Steering | LS: Fallback Guard'
ENTERS = 'Transition Set 1'                 # its Start Release adds `Steering`
GYRO = 'Gyro'
GYRO_MODIFIERS = ('Gyro | L1: Modifier 0', 'Gyro | R1: Modifier 1')
GYRO_QUICK_TAPS = ('Gyro | L1!R1: Modifier 2', 'Gyro | R1!L1: Modifier 2')
BASE_MODIFIERS = ('L1: Modifier 0', 'R1: Modifier 1', 'L1!R1: Modifier 2', 'R1!L1: Modifier 2')
ADD_MS = 100                    # July's delay on the add: a driver pressed inside it wins
RESET_MS = ADD_MS + 50          # the reset's margin (R120)
REPEAT_MS = 50
LS_OUT = fw.LS_OUT
KEYS = fw.KEYS
EMPTY = 'controller_action empty_binding, , '
token, remove, add, entry, slot, ran = fw.token, fw.remove, fw.add, fw.entry, fw.slot, fw.ran


def beeping(title):
    """A removal that beeps and shows no name: the second flag (A49)."""
    return f'controller_action remove_layer {token(title)} 0 1, , '


class Guard:
    """The four parts, on one finished layout."""

    def __init__(self, data, variant):
        self.data, self.cm, self.variant = data, data['controller_mappings'], variant
        self.name = (lambda title: map_title(title, RENAME)) if variant == 'alternative' else (lambda title: title)
        self.log = []

    def layout(self):
        return Layout(self.data)                    # rebuilt after each structural change: it caches

    def active(self, title):
        return self.layout().active(title)

    def every_entry(self):
        for group in self.cm['group']:
            for value in group.get('inputs', {}).values():
                for _, found in entries(value.get('activators', {})):
                    yield found

    def pair(self):
        """{(source, input): its Gyro modifier}: the modifier pair, read from what `Gyro` adds."""
        layout, found = self.layout(), {}
        wanted = {self.name(title) for title in GYRO_MODIFIERS}
        for source, group in layout.active(GYRO).items():
            for name, value in group.get('inputs', {}).items():
                for _, e in entries(value.get('activators', {})):
                    for op, target in layout.layer_ops(e):
                        if op == 'add_layer' and target in wanted:
                            found[(source, name)] = target
        if sorted(found.values()) != sorted(wanted):
            raise ValueError(f'{GYRO}: expected one input for each Gyro modifier, found {found}')
        return found

    # --- part 1 ----------------------------------------------------------------------------------

    def rename(self):
        key = next(k for k, v in self.cm['action_layers'].items() if v['title'] == ENTRY_GUARD)
        self.cm['action_layers'][key]['title'] = GUARD
        text = json.dumps(self.cm['group'])
        count = text.count(json.dumps(token(ENTRY_GUARD))[1:-1])
        self.cm['group'][:] = json.loads(text.replace(json.dumps(token(ENTRY_GUARD))[1:-1], json.dumps(token(GUARD))[1:-1]))
        self.log.append(f'{ENTRY_GUARD} is renamed {GUARD}: {count} commands')

    def delete(self, title):
        """Take a layer out: its entry, its preset, its groups and every removal of it."""
        cm = self.cm
        key = next(k for k, v in cm['action_layers'].items() if v['title'] == title)
        preset = next(p for p in cm['preset'] if p['name'] == key)
        gone = set(preset['group_source_bindings'])
        shared = gone & {gid for p in cm['preset'] if p is not preset for gid in p['group_source_bindings']}
        if shared:
            raise ValueError(f'{title}: groups {sorted(shared)} belong to another layer too')
        del cm['action_layers'][key]
        cm['preset'].remove(preset)
        for number, left in enumerate(cm['preset']):            # the presets stay numbered in a row, in key order
            left['id'] = str(number)
        cm['group'][:] = [g for g in cm['group'] if g['id'] not in gone]
        shifts = [a for e in self.every_entry() for a in actions(e) if 'mode_shift' in a and a.split()[-1].strip(',') in gone]
        if shifts:
            raise ValueError(f'{title}: a mode shift still points at one of its groups: {shifts}')
        mine, count = 'remove_layer ' + token(title) + ' ', 0
        for found in self.every_entry():
            stored = found['bindings']['binding']
            commands = stored if isinstance(stored, list) else [stored]
            kept = [c for c in commands if mine not in c]
            if len(kept) == len(commands):
                continue
            if not kept:
                raise ValueError(f'{title}: a bind removes only this layer: {commands}')
            found['bindings']['binding'] = kept if len(kept) > 1 else kept[0]
            count += len(commands) - len(kept)
        if token(title) in json.dumps(cm['group']):
            raise ValueError(f'{title}: still named in a command')
        self.log.append(f'{title} is deleted, with {len(gone)} groups and {count} removals of it')

    # --- part 2 ----------------------------------------------------------------------------------

    def steering(self, pair):
        steering = self.active(STEERING)
        stick = steering['joystick']['inputs']
        for direction in KEYS:
            acts = stick[direction]['activators']
            if list(acts) != ['Full_Press'] or ran(acts['Full_Press']) != [add(HOLD), add(WINDOW)]:
                raise ValueError(f'{STEERING} {direction}: expected the add of the Fallback Hold and its window, found {acts}')
            stick[direction] = slot(
                chord=entry([add(GUARD)], gyro_ratchet_button_mask=LS_OUT, gyro_ratchet_button_requireany_or_all=0,
                            delay_start=ADD_MS, haptic_intensity=3, interruptable=0),
                Full_Press=entry([remove(GUARD)], hold_repeats=1, repeat_rate=RESET_MS, interruptable=0,
                                 haptic_intensity=0))
        # A driver only adds its own layer: with the guard on, the guard's bind answers the button.
        for source, name in pair:
            acts = steering[source]['inputs'][name]['activators']
            press, other = acts.get('Full_Press'), acts.get('chord')
            if sorted(acts) != ['Full_Press', 'chord'] or ran(press)[:2] != [remove(HOLD), remove(GUARD)] \
                    or len(ran(press)) != 3 or ran(other) != [remove(GUARD)]:
                raise ValueError(f'{STEERING} {source}/{name}: expected the driver bind of 90.32, found {acts}')
            press['bindings']['binding'] = ran(press)[2]
            other['bindings']['binding'] = EMPTY                # the other driver is held: its layer answers this press
        self.log.append(f'{STEERING} | joystick up and down: a chord on the left stick being out adds {GUARD} after '
                        f'{ADD_MS} ms with a strong pulse; its reset repeats every {RESET_MS} ms')
        self.log.append(f'{STEERING} | the two drivers: each only adds its own layer')

    def commit(self):
        changed = 0
        for source, group in self.active(ENTERS).items():
            for name, value in group.get('inputs', {}).items():
                for kind, e in entries(value.get('activators', {})):
                    commands = ran(e)
                    if add(GUARD) in commands:
                        if kind != 'release' or commands[-1] != add(GUARD) or 'add_layer ' + token(STEERING) not in commands[-2]:
                            raise ValueError(f'{ENTERS} {source}/{name}: expected the commit to end with {STEERING} and its guard')
                        e['bindings']['binding'] = list(reversed(commands[:-1]))
                        changed += 1
        if changed != 1:
            raise ValueError(f'{ENTERS}: expected one commit that adds the guard, found {changed}')
        self.log.append(f'{ENTERS}: entering {STEERING} adds no guard')

    # --- part 3 ----------------------------------------------------------------------------------

    def build_guard(self, pair):
        guard = self.active(GUARD)
        switch = guard['switch']['inputs']
        for name in ('button_menu', 'button_escape'):
            acts = switch[name]['activators']
            if sorted(acts) != ['Full_Press', 'chord'] or ran(acts['Full_Press']) != [remove(GUARD)]:
                raise ValueError(f'{GUARD} {name}: expected the Entry Guard\'s key and cleanup, found {acts}')
            del switch[name]                                    # not bound: Steering's menu flow comes through
        if switch:
            raise ValueError(f'{GUARD}: expected only Start and Select among its buttons, found {sorted(switch)}')
        stick = guard['joystick']['inputs']
        if sorted(stick) != ['dpad_east', 'dpad_north', 'dpad_south', 'dpad_west', 'edge', 'touch']:
            raise ValueError(f'{GUARD} joystick: expected the Entry Guard\'s inputs, found {sorted(stick)}')
        for direction, key in KEYS.items():
            stick[direction] = slot(Full_Press=entry([f'key_press {key}, , '], interruptable=0))   # no Release: it stays
        for name in ('dpad_east', 'dpad_west', 'edge'):
            del stick[name]                                     # A and D come from Steering; nothing ends it on the edge
        right = guard['right_joystick']['inputs']
        if sorted(right) != ['edge', 'touch']:
            raise ValueError(f'{GUARD} right_joystick: expected the edge and the touch, found {sorted(right)}')
        del right['edge']                                       # it binds no button that asks for an edge cleanup (R170)
        for source in ('joystick', 'right_joystick'):
            acts = guard[source]['inputs']['touch']['activators']
            if sorted(acts) != ['Full_Press', 'chord', 'release'] or ran(acts['Full_Press']) != [remove(GUARD)] \
                    or acts['chord']['settings'].get('gyro_ratchet_button_mask') != LS_OUT:
                raise ValueError(f'{GUARD} {source} touch: expected the cleanup function and the helpers\' Release, found {acts}')
        steering = self.active(STEERING)
        for (source, name), modifier in pair.items():
            if source not in guard:
                fw.Fallback.new_group(self, GUARD, source, steering[source])
                guard = self.active(GUARD)
            if name in guard[source]['inputs']:
                raise ValueError(f'{GUARD} {source}/{name}: already bound')
            guard[source]['inputs'][name] = slot(
                chord=entry([add(modifier)], gyro_ratchet_button_mask=LS_OUT, gyro_ratchet_button_requireany_or_all=0,
                            hold_repeats=1, repeat_rate=REPEAT_MS, interruptable=0),
                Full_Press=entry([remove(GUARD)], hold_repeats=1, repeat_rate=REPEAT_MS, haptic_intensity=3))
        self.log.append(f'{GUARD}: W and S with no Release; each of the modifier pair adds its Gyro modifier with the '
                        f'left stick out and removes the guard at centre; Start, Select, A, D and the edges are open; '
                        f'a cleanup function on both stick touches')

    # --- part 4 ----------------------------------------------------------------------------------

    def quick_tap(self):
        count = 0
        for title in map(self.name, GYRO_QUICK_TAPS):
            other = next(t for t in map(self.name, GYRO_QUICK_TAPS) if t != title)
            for source, group in self.active(title).items():
                for name, value in group.get('inputs', {}).items():
                    for kind, e in entries(value.get('activators', {})):
                        commands = ran(e)
                        if kind != 'release' or not any('remove_layer ' + token(GYRO) + ' ' in c for c in commands):
                            continue
                        if commands[0] != remove(title) or 'remove_layer ' + token(GYRO) + ' 1 1' not in commands[-1] \
                                or len(commands) != 8:
                            raise ValueError(f'{title} {source}/{name}: expected the quick tap of 90.32, found {commands}')
                        more = [remove(other)] + [remove(self.name(t)) for t in BASE_MODIFIERS] + [remove(GUARD), beeping(STEERING)]
                        e['bindings']['binding'] = list(reversed(commands[:-1] + more + commands[-1:]))
                        count += 1
        if count != 4:
            raise ValueError(f'expected four Gyro Modifier 2 quick taps, found {count}')
        self.log.append(f'{count} Gyro Modifier 2 quick taps also remove the other Gyro Modifier 2, the Base modifiers, '
                        f'{GUARD} and {STEERING}, with the beep')

    def run(self):
        pair = self.pair()
        self.rename()
        self.steering(pair)                         # before the deletions: it holds the only adds of the two layers
        self.commit()
        self.delete(WINDOW)
        self.delete(HOLD)
        self.build_guard(pair)
        self.quick_tap()
        return self.log


class Front:
    """In front of the 90.32 classes: the changes to the finished layout."""

    def finish(self):
        data = super().finish()
        self.fallback_guard_log = Guard(data, self.variant).run()
        cm = data['controller_mappings']
        cm['title'] = cm['title'].replace('fallback window replacements candidate', 'fallback guard candidate')
        cm['description'] = (
            'Fallback guard candidate; device verification pending. The Steering fallback is a layer the stick '
            'brings in and the bumpers take out. See findings/2026-10-05-steering-fallback-guard/README.md.')
        report = audit_layout(data)
        if report['violations']:
            raise ValueError(report['violations'])
        return data


def Builder(variant):
    return type('Concrete', (Front, type(rp.Builder(variant))), {})(variant)


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
        stem = HERE / f'{variant}-fallback-guard'
        stem.with_suffix('.readable.json').write_text(readable)
        stem.with_suffix('.json').write_text(numeric)
        (HERE / f'{variant}-binds-changed.txt').write_text('\n'.join(b.fallback_guard_log) + '\n')
        (HERE / f'{variant}-inputs-changed.txt').write_text('\n'.join(b.required_log) + '\n')
        if args.vdf:
            subprocess.run(['node', str(ROOT / 'tools/convert_vdf.mjs'), str(stem.with_suffix('.json'))], check=True)
        manifest[variant] = {
            'source_sha256': hashlib.sha256(b.source.read_bytes()).hexdigest(),
            'fallback_window_replacements_generator_sha256': hashlib.sha256(REPLACEMENTS.read_bytes()).hexdigest(),
            'candidate_sha256': hashlib.sha256(numeric.encode()).hexdigest(),
            'deleted_layers': [HOLD, WINDOW], 'renamed_layers': {ENTRY_GUARD: GUARD},
            'inputs_given_a_cleanup': b.required_inputs,
            'total_layer_count': len(data['controller_mappings']['action_layers']),
            'resolved_references': count, 'device_status': 'UNTESTED'}
        print(f'{variant}: {len(data["controller_mappings"]["action_layers"])} layers')
        for line in b.fallback_guard_log:
            print('   ', line)
    (HERE / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')


if __name__ == '__main__':
    main()
