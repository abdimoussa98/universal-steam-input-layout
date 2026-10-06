"""The fallback's timer moves into a window, and the outer ring is fixed in every layer.

Extends the 10-04 window-releases-and-tap-cover-resets builder; it stays frozen. The plan is
plans/2026-10-04-fallback-window.md, the author's design of 2026-10-04. Three parts, all changes
to the finished layout:

1. **The fallback window.** `Steering`'s up and down add `Steering | LS: Fallback Hold` and, on
   top, the new `Steering | LS: Fallback Window`, a window that types W and S and removes
   itself after 1000 ms. Letting up or down go, or the edge, inside that second removes both
   and `Steering` stays. After the second the Fallback Hold is on top: it types W and S, and
   its Release on up and down clears the Steering layers. A driver or a menu button removes
   the window alone, and the Fallback Hold, where they clear the Steering layers, answers
   them. The 1500 ms exit, its reset and the pulse leave the Fallback Hold; the pulse is on
   up and down in the window. One layer, at the end of the list: 90.

2. **No stick group states 4915 or 7209 as its outer ring radius.** The editor's D-pad radius
   starts at 10,000, so 4915 was never a value it could set. Every such group, in every
   layer, states no radius and "not inverted", and Steam's default applies.

3. **The Entry Guard ends on any direction's Release** as well as on the edge's, which with
   the default radius is only pressed near the rim.
"""
import argparse
import copy
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
from steam_layout.model import Layout, actions, entries, map_title                     # noqa: E402
from tools.audit_command_budget import audit_layout                                    # noqa: E402
from tools.convert_runtime_ids import generate_lookup, titles_to_ids, ids_to_titles   # noqa: E402

RELEASES = ROOT / 'findings/2026-10-04-window-releases-and-tap-cover-resets/build_candidate.py'
spec = importlib.util.spec_from_file_location('window_releases_build', RELEASES)
wr = importlib.util.module_from_spec(spec); spec.loader.exec_module(wr)

RENAME = wr.RENAME
STEERING = 'Steering'
HOLD = wr.HOLD
WINDOW = 'Steering | LS: Fallback Window'
TEMPLATE = 'Steering | LS Up: Double Tap'      # the window the new one is copied from
GUARD = 'Steering | LS: Entry Guard'
DRIVER_LAYERS = ('Steering | R1: W Key', 'Steering | L1: S Key')
WINDOW_MS = 1000                # the most a start delay can be in the editor
PULSE_MS = 250
LS_OUT = '1073741824'           # the chord mask bit for the left stick being out (bit 30)
BAD_RADII = ('4915', '7209')    # below what the editor's Outer Ring Command Radius can be set to
STICKS = ('joystick', 'right_joystick')
DIRECTIONS = ('dpad_north', 'dpad_south', 'dpad_east', 'dpad_west')
KEYS = {'dpad_north': 'W', 'dpad_south': 'S'}
TOUCH_LAYERS = {'joystick': 'LST', 'right_joystick': 'RST'}
MENU = (('switch', 'button_menu'), ('switch', 'button_escape'))
PRESET = re.compile(r'Preset_(\d+)$')


def token(title):
    return '{{Base::' + title + '}}'


def remove(title):
    return f'controller_action remove_layer {token(title)} 0 0, , '


def add(title):
    return f'controller_action add_layer {token(title)} 0 0, , '


def entry(commands, **settings):
    """One entry. `commands` is in the order they run; an array is stored the other way round (A4)."""
    stored = list(reversed(commands))
    return {'bindings': {'binding': stored if len(stored) > 1 else stored[0]},
            'settings': {key: str(value) for key, value in settings.items()}}


def slot(**activators):
    return {'activators': activators, 'disabled_activators': {}}


def ran(found):
    """An entry's commands in the order they run."""
    return list(reversed(actions(found)))


class Fallback:
    """The three parts, on one finished layout."""

    def __init__(self, data, variant):
        self.data, self.cm, self.variant = data, data['controller_mappings'], variant
        self.name = (lambda title: map_title(title, RENAME)) if variant == 'alternative' else (lambda title: title)
        self.log = []

    def layout(self):
        return Layout(self.data)                    # rebuilt after each structural change: it caches

    def active(self, title):
        return self.layout().active(title)

    def new_group(self, title, source, shell):
        """A new group for `title` on `source`, with `shell`'s mode and settings and no inputs."""
        cm = self.cm
        gid = str(max(int(g['id']) for g in cm['group']) + 1)
        group = {'id': gid, 'mode': shell['mode'], 'name': '', 'description': '', 'inputs': {},
                 'settings': copy.deepcopy(shell.get('settings') or {})}
        cm['group'].append(group)
        key = next(k for k, v in cm['action_layers'].items() if v['title'] == title)
        preset = next(p for p in cm['preset'] if p['name'] == key)
        preset['group_source_bindings'][gid] = f'{source} active'
        return group

    def drivers(self):
        """The two driver inputs: the ones `Steering` turns into its W and S layers."""
        layout, found = self.layout(), []
        wanted = {self.name(title) for title in DRIVER_LAYERS}
        for source, group in layout.active(STEERING).items():
            for name, value in group.get('inputs', {}).items():
                for _, e in entries(value.get('activators', {})):
                    if any(op == 'add_layer' and target in wanted for op, target in layout.layer_ops(e)):
                        found.append((source, name))
        if len(found) != 2:
            raise ValueError(f'{STEERING}: expected two driver inputs, found {found}')
        return found

    # --- part 1 ----------------------------------------------------------------------------------

    def exit_list(self):
        """The commands of today's 1.5 s exit, in the order they run: the Steering layers, `Steering` last with the beep."""
        stick = self.active(HOLD)['joystick']['inputs']
        north, south = (stick[d]['activators'] for d in ('dpad_north', 'dpad_south'))
        for direction, acts in (('up', north), ('down', south)):
            if sorted(acts) != ['Full_Press', 'chord', 'release'] or acts['chord']['settings'].get('delay_start') != '1500':
                raise ValueError(f'{HOLD} {direction}: expected the key, the 1500 ms exit and the Release, found {sorted(acts)}')
        commands = ran(north['chord'])
        if commands != ran(south['chord']) or commands[0] != remove(HOLD) or 'remove_layer ' + token(STEERING) + ' 0 1' not in commands[-1]:
            raise ValueError(f'{HOLD}: expected one exit list that starts with the layer and ends with {STEERING} and the beep')
        return commands

    def add_window(self):
        """The new layer, at the end of the list, as a copy of a Steering window's groups."""
        cm = self.cm
        if any(v['title'] == WINDOW for v in cm['action_layers'].values()):
            raise ValueError(f'{WINDOW} is already there')
        last = max(int(PRESET.match(k).group(1)) for k in list(cm['actions']) + list(cm['action_layers']))
        key = f'Preset_{last + 1}'
        template_key = next(k for k, v in cm['action_layers'].items() if v['title'] == TEMPLATE)
        cm['action_layers'][key] = {**cm['action_layers'][template_key], 'title': WINDOW}
        template = next(p for p in cm['preset'] if p['name'] == template_key)
        groups = {g['id']: g for g in cm['group']}
        bindings, next_id = {}, max(int(g['id']) for g in cm['group']) + 1
        for gid, state in template['group_source_bindings'].items():
            group = json.loads(json.dumps(groups[gid]).replace(token(TEMPLATE), token(WINDOW)))
            group['id'] = str(next_id)
            cm['group'].append(group)
            bindings[str(next_id)] = state
            next_id += 1
        cm['preset'].append({'id': str(max(int(p['id']) for p in cm['preset']) + 1), 'name': key,
                             'group_source_bindings': bindings})
        self.log.append(f'{WINDOW}: a new layer at the end of the list, from {TEMPLATE}')

    def build_window(self, drivers):
        window = self.active(WINDOW)
        leave = [remove(WINDOW), remove(HOLD)]                 # every way out by hand takes the Fallback Hold along
        alone = [remove(WINDOW)]
        switch = window['switch']['inputs']
        timer = switch['always_on_action']['activators']['Full_Press']
        if timer['settings'].get('delay_start') != '150':
            raise ValueError(f'{WINDOW}: expected the template\'s 150 ms timer, found {timer["settings"]}')
        switch['always_on_action'] = slot(Full_Press=entry(alone, delay_start=WINDOW_MS, interruptable=0))
        # A driver or a menu button removes the window alone: the Fallback Hold underneath answers the button.
        for source, name in list(MENU) + drivers:
            window[source]['inputs'][name] = slot(Full_Press=entry(alone, haptic_intensity=0))
        stick = window['joystick']['inputs']
        for direction, key in KEYS.items():
            stick[direction] = slot(
                Full_Press=entry([f'key_press {key}, , '], interruptable=0),
                chord=entry(['controller_action empty_binding, , '], gyro_ratchet_button_mask=LS_OUT,
                            gyro_ratchet_button_requireany_or_all=0, hold_repeats=1, repeat_rate=PULSE_MS,
                            haptic_intensity=3, interruptable=0),
                release=entry(leave, haptic_intensity=0))
        if any(sorted(stick[d]['activators']) != ['Full_Press'] for d in ('dpad_east', 'dpad_west')):
            raise ValueError(f'{WINDOW}: expected plain A and D from the template')
        stick['edge'] = slot(release=entry(leave, haptic_intensity=0))
        for source, prefix in TOUCH_LAYERS.items():
            touch = window[source]['inputs']['touch']['activators']
            want = [remove(WINDOW)] + [remove(f'{prefix}: {part}') for part in ('Entry Point', 'Tap Cover', 'Temporary Gyro')]
            if list(touch) != ['release'] or ran(touch['release']) != want:
                raise ValueError(f'{WINDOW} {source} touch: expected the template\'s Release, found {touch}')
            window[source]['inputs']['touch'] = slot(release=entry(leave + want[1:], haptic_intensity=0))
        pad = window['right_trackpad']['inputs']['touch']['activators']
        if list(pad) != ['release'] or ran(pad['release'])[0] != remove(WINDOW):
            raise ValueError(f'{WINDOW} right pad touch: expected the template\'s Release, found {pad}')
        # The template's list names the pad's own layers too; the fix pipeline drops those here, as in the template.
        window['right_trackpad']['inputs']['touch'] = slot(release=entry(leave + ran(pad['release'])[1:], haptic_intensity=0))
        self.log.append(f'{WINDOW}: {WINDOW_MS} ms; W and S with the pulse; up, down, the edge and the touches let go '
                        f'remove it and the Fallback Hold; a driver or a menu button removes it alone')

    def build_steering(self):
        stick = self.active(STEERING)['joystick']['inputs']
        for direction in KEYS:
            acts = stick[direction]['activators']
            if list(acts) != ['Full_Press'] or actions(acts['Full_Press']) != [add(HOLD)] \
                    or acts['Full_Press']['settings'].get('hold_repeats') != '1':
                raise ValueError(f'{STEERING} {direction}: expected the repeating add of the Fallback Hold, found {acts}')
            acts['Full_Press']['bindings']['binding'] = [add(WINDOW), add(HOLD)]            # the hold, then the window on top
        self.log.append(f'{STEERING} | joystick up and down: adds the Fallback Hold, then {WINDOW}')

    def build_hold(self, drivers, leave):
        hold = self.active(HOLD)
        stick = hold['joystick']['inputs']
        for direction, key in KEYS.items():
            stick[direction] = slot(Full_Press=entry([f'key_press {key}, , '], interruptable=0),
                                    release=entry(leave, haptic_intensity=3))
        edge = stick['edge']['activators']
        if sorted(edge) != ['Full_Press', 'chord'] or 'delay_start' not in edge['chord']['settings']:
            raise ValueError(f'{HOLD} edge: expected the pulse and the reset, found {edge}')
        del stick['edge']                                           # the pulse is in the window; no delay is left to reset
        # The cleanup binds of 90.24 run the exit: what the missed Release would have done.
        cleanups = [('joystick', 'touch'), ('right_joystick', 'touch'), ('right_joystick', 'edge')]
        for source, name in cleanups:
            acts = hold[source]['inputs'][name]['activators']
            press, guard = acts.get('Full_Press'), acts.get('chord')
            if not isinstance(press, dict) or ran(press) != [remove(HOLD)] or press['settings'] != {'hold_repeats': '1'} \
                    or not isinstance(guard, dict) or guard['settings'].get('gyro_ratchet_button_mask') != LS_OUT:
                raise ValueError(f'{HOLD} {source}/{name}: expected the cleanup bind and its guard, found {acts}')
            press['bindings']['binding'] = list(reversed(leave))
        # A driver or a menu button clears the Steering layers, with the stick out or not. The bind repeats,
        # so it fires on a button that was already down when the window above went (A6, A9).
        for source, name in MENU:
            acts = hold[source]['inputs'][name]['activators']
            if sorted(acts) != ['Full_Press', 'chord'] or ran(acts['Full_Press']) != [remove(HOLD)]:
                raise ValueError(f'{HOLD} {source}/{name}: expected the cleanup bind and the key chord, found {acts}')
        steering = self.active(STEERING)
        for source, name in list(MENU) + drivers:
            if source not in hold:
                self.new_group(HOLD, source, steering[source])
                hold = self.active(HOLD)
            hold[source]['inputs'][name] = slot(Full_Press=entry(leave, hold_repeats=1, repeat_rate=50, interruptable=0,
                                                                 haptic_intensity=3))
        self.log.append(f'{HOLD}: W and S with a Release that clears the Steering layers; a driver or a menu button '
                        f'clears them too; the cleanup binds clear them; nothing on the edge')

    # --- part 2 ----------------------------------------------------------------------------------

    def default_radius(self):
        layout, count = self.layout(), 0
        for title in layout.presets:
            for source, group in layout.active(title).items():
                settings = group.get('settings') or {}
                if source in STICKS and settings.get('edge_binding_radius') in BAD_RADII:
                    if settings.get('edge_binding_invert') != '0':
                        raise ValueError(f'{title} {source}: expected the low radius with "not inverted" stated')
                    del settings['edge_binding_radius']
                    count += 1
        if count != 62:
            raise ValueError(f'expected 62 stick groups with a radius of 4915 or 7209, found {count}')
        self.log.append(f'{count} stick groups: the outer ring radius is no longer stated; "not inverted" stays')

    # --- part 3 ----------------------------------------------------------------------------------

    def guard_releases(self):
        stick = self.active(GUARD)['joystick']['inputs']
        for direction in DIRECTIONS:
            acts = stick[direction]['activators']
            if list(acts) != ['Full_Press']:
                raise ValueError(f'{GUARD} {direction}: expected one key, found {list(acts)}')
            acts['release'] = entry([remove(GUARD)], haptic_intensity=0)
        self.log.append(f'{GUARD}: up, down, left and right each get a Release that removes it')

    def clears(self):
        """A bind that clears both Steering windows clears the new one too."""
        up, down = remove(TEMPLATE), remove('Steering | LS Down: Double Tap')
        count = 0
        for group in self.cm['group']:
            for value in group.get('inputs', {}).values():
                for _, e in entries(value.get('activators', {})):
                    stored = e['bindings']['binding']
                    if isinstance(stored, list) and up in stored and down in stored and remove(WINDOW) not in stored:
                        stored.insert(stored.index(up) + 1, remove(WINDOW))        # runs just before the template's
                        count += 1
        self.log.append(f'{count} binds that clear both Steering windows clear {WINDOW} as well')

    def run(self):
        leave = self.exit_list()
        drivers = self.drivers()
        self.default_radius()                       # first, so the new window is copied from a fixed template
        self.add_window()
        self.build_window(drivers)
        self.build_steering()
        self.build_hold(drivers, leave)
        self.clears()
        self.guard_releases()
        return self.log


class Front:
    """In front of the 90.30 classes: the changes to the finished layout."""

    def finish(self):
        data = super().finish()
        self.fallback_window_log = Fallback(data, self.variant).run()
        cm = data['controller_mappings']
        cm['title'] = cm['title'].replace('window releases and tap cover resets candidate', 'fallback window candidate')
        cm['description'] = (
            'Fallback window candidate; device verification pending. The Steering fallback counts its second in a '
            'window, and no stick group states an outer ring radius below the editor\'s range. '
            'See findings/2026-10-04-fallback-window/README.md.')
        report = audit_layout(data)
        if report['violations']:
            raise ValueError(report['violations'])
        return data


def Builder(variant):
    return type('Concrete', (Front, type(wr.Builder(variant))), {})(variant)


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
        stem = HERE / f'{variant}-fallback-window'
        stem.with_suffix('.readable.json').write_text(readable)
        stem.with_suffix('.json').write_text(numeric)
        (HERE / f'{variant}-binds-changed.txt').write_text('\n'.join(b.fallback_window_log) + '\n')
        (HERE / f'{variant}-inputs-changed.txt').write_text('\n'.join(b.required_log) + '\n')
        if args.vdf:
            subprocess.run(['node', str(ROOT / 'tools/convert_vdf.mjs'), str(stem.with_suffix('.json'))], check=True)
        manifest[variant] = {
            'source_sha256': hashlib.sha256(b.source.read_bytes()).hexdigest(),
            'window_releases_generator_sha256': hashlib.sha256(RELEASES.read_bytes()).hexdigest(),
            'candidate_sha256': hashlib.sha256(numeric.encode()).hexdigest(),
            'new_layers': [WINDOW], 'inputs_given_a_cleanup': b.required_inputs,
            'total_layer_count': len(data['controller_mappings']['action_layers']),
            'resolved_references': count, 'device_status': 'UNTESTED'}
        print(f'{variant}: {len(data["controller_mappings"]["action_layers"])} layers')
        for line in b.fallback_window_log:
            print('   ', line)
    (HERE / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')


if __name__ == '__main__':
    main()
