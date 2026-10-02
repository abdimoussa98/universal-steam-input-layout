"""Build the stateful transition structure on top of the lean steering build.

Extends the 09-30 `Lean` builder the way `Lean` extends the 09-29 baseline; both
stay frozen. Plan: plans/2026-10-01-stateful-transitions-implementation.md.
Design: resources/Stateful Layer Transitions.md.

Steps 1 to 5: menu Entry Points, Fn layers, stick guards and the menu Tap
Cover, the two transition layers, Steering's menu behaviour. Step 6: Steering's
left stick ends on a normal edge's Release (no inverted edge changes a layer),
and its two Double Tap windows are Always On windows.
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
from audit_command_budget import audit_layout
from convert_runtime_ids import generate_lookup, titles_to_ids, ids_to_titles

LEAN = ROOT / 'findings/2026-09-30-steering-lean/build_candidate.py'
spec = importlib.util.spec_from_file_location('steering_lean', LEAN)
lean = importlib.util.module_from_spec(spec); spec.loader.exec_module(lean)

# Menu hold and its repeating reset (were 300 and 350).
HOLD_MS, RESET_MS = 200, 250
# D-pad edge: engages near 25% of travel, releases near 5%. Guard and Entry
# Point must agree, or the guard may not see the edge as held when it is added.
EDGE_RADIUS = '4915'
# The guard add must land inside HOLD_MS when the stick is already out: an
# immediate layer command doesn't fire on a held input, only its repeat does.
EDGE_REPEAT_MS = 50
MENU_ANY = (1 << 12) | (1 << 14)  # Menu Left (button_menu) + Menu Right (button_escape)
# side: (button, legacy chord id, the key its tap types while a driver is held)
MENU = {'Left': ('button_menu', '15', 'ESCAPE'), 'Right': ('button_escape', '14', 'TAB')}
STICKS = {'Left': 'joystick', 'Right': 'right_joystick'}
DPAD = ('dpad_north', 'dpad_south', 'dpad_east', 'dpad_west')
# The design's Transition 1 (cross gestures) and Transition 2 (clear). The
# titles get sorted out when Transition 0 arrives with Gamepad.
CROSS, CLEAR = 'Transition Set 1', 'Transition Set 0'
COVER = 'Menu Buttons: Tap Cover'
# LS deflection plus one driver, left then right: the two All-chords that keep
# a Steering modifier's cleanup quiet while the modifier is valid.
DRIVER_BITS = {'default': (3, 2), 'alternative': (25, 24)}
SELECT_REPEAT_MS = 50
# Entering a stateful layer is announced: the beep flag on its add, and a
# high-intensity pulse on the commit.
COMMIT_HAPTIC = 3


def guard(stick_side):
    return f'Menu Buttons: {stick_side} Stick Guard'


def entry_point(side, steering=False):
    return ('Steering | ' if steering else '') + f'Menu {side}: Entry Point'


def fn_layer(side):
    return f'Menu {side}: Fn Layer'


class Stateful:
    def title(self, *parts):
        if parts == ('Entry Guard',):
            return 'Steering | LS: Entry Guard'
        return super().title(*parts)

    def covers(self):
        return [self.title('Normal', 'Consumed'), self.title('Repeat'), COVER]

    def stick_settings(self, source):
        """Edge settings shared by every layer of a menu hold; the right stick
        also needs the D-pad settings it can't inherit from Base's mouse mode."""
        settings = dict(self.rs_dpad) if source == 'right_joystick' else {}
        settings.update(edge_binding_radius=EDGE_RADIUS, edge_binding_invert='0')
        return settings

    def menu_exit(self):
        """What a menu release under a guard or the Tap Cover leaves behind.
        Fn can't be above them (a guard eats its delay); that removal only
        covers a stale Fn."""
        return self.clear([guard(s) for s in STICKS] + [entry_point(side, steering)
                          for side in MENU for steering in (False, True)] + [fn_layer(side) for side in MENU])

    def ls_settings(self, center=True):
        """Every Steering layer uses the D-pad edge of the menu layers: a normal
        outer edge whose Release means the stick is back at centre."""
        settings = super().ls_settings(center)
        settings.update(edge_binding_radius=EDGE_RADIUS, edge_binding_invert='0')
        return settings

    def selectors(self, owner, context):
        """The W and S layers add the modifier with a repeating bind, so a stick
        that is already held when the driver goes down enters it at once, and
        so does one exposed when the other modifier is removed."""
        m = self.m
        inputs = super().selectors(owner, context)
        if context == 'Normal':
            for direction, input_name in m.DIRECTIONS.items():
                bank = self.title('Mod ' + ('1' if direction == 'Up' else '0'))
                inputs[input_name] = m.full(m.op('add', bank), hold_repeats=1,
                                            repeat_rate=SELECT_REPEAT_MS, interruptable=0)
        return inputs

    # The LS Tap Cover is only ever added from inside Modifier 0 or 1, where the
    # stick is out, so its edge Release can always remove it. Neither a driver
    # press nor entering or leaving Modifier 2 adds it.
    def acquisition(self):
        m = self.m; t = self.title
        return {owner: m.inp(
            Full_Press=m.entry(m.seq(m.op('remove', t('Entry Guard')), m.op('add', t(owner))),
                               hold_repeats=1, repeat_rate=50),
            chord=m.entry(m.op('remove', t('Entry Guard')),
                          gyro_ratchet_button_mask=self.opposite_mask(owner),
                          gyro_ratchet_button_requireany_or_all=0, interruptable=0))
            for owner in m.OWNERS}

    def context_enter(self, owner, first=None):
        return self.clear(([first] if first else []) + self.gestures + self.banks) + [
            self.m.op('add', self.title('Mod2', owner))]

    def context_leave(self, first=None):
        return self.clear(([first] if first else []) + self.gestures + self.banks)

    def map_groups(self, name, bank=None, consume=False):
        """Modifier 0 and 1: each mapped input's cleanup is guarded by two
        All-chords (LS deflection plus one driver). Each chord carries the key
        and the Tap Cover add in one array, which keeps the input at three
        entries."""
        m = self.m
        super().map_groups(name, bank, consume)
        if not consume:
            return
        cover = m.op('add', self.title('Normal', 'Consumed'))
        for group in self.sources(name).values():
            for binding in group['inputs'].values():
                chords = binding['activators']['chord']
                output = chords[0] if isinstance(chords, list) else chords
                payload = list(reversed(m.commands(output)))
                settings = {k: v for k, v in output['settings'].items() if not k.startswith('gyro_ratchet')}
                array = m.EMPTY if payload == [m.EMPTY] else m.seq(*payload, cover)
                binding['activators']['chord'] = [
                    m.entry(array, gyro_ratchet_button_mask=lean.LS_DEFLECT_MASK | 1 << bit,
                            gyro_ratchet_button_requireany_or_all=1, **settings)
                    for bit in DRIVER_BITS[self.variant]]

    def hold_exit(self, direction):
        """Steering's fallback warning and exit: chorded delays on LS deflection."""
        m = self.m
        return m.inp(Full_Press=m.entry(m.key(direction), interruptable=0), chord=[
            self.chorded_delay(m.EMPTY, lean.LS_DEFLECT_MASK, 1000, hold_repeats=1, repeat_rate=250,
                               haptic_intensity=3, interruptable=0),
            self.chorded_delay(m.seq(*self.exit_all(beep=True)), lean.LS_DEFLECT_MASK, 2500,
                               haptic_intensity=3, interruptable=0)])

    def build_core(self):
        """Steering keeps its menu buttons: its own Entry Points with no driver
        held, plain Tab and Escape while a driver owns movement."""
        super().build_core()
        m = self.m; t = self.title
        switches = self.sources(t())['switch']['inputs']
        for side, (button, _, _) in MENU.items():
            switches[button] = m.full(m.op('add', entry_point(side, steering=True)), hold_repeats=1)
        for owner in m.OWNERS:
            switches = self.sources(t(owner))['switch']['inputs']
            for button, _, tap in MENU.values():
                switches[button] = m.full(m.key(tap))
        stick = self.sources(t())['joystick']['inputs']
        stick['dpad_north'] = self.hold_exit('W'); stick['dpad_south'] = self.hold_exit('S')
        # With the stick centred at entry the edge isn't out, so the guard stays
        # until the first push and return, or a driver press. It only binds WASD.
        self.sources(t('Entry Guard'))['joystick']['inputs']['edge'] = m.inp(
            release=m.entry(m.op('remove', t('Entry Guard'))))

    def build_strokes(self):
        """Modifier 0 and 1 follow the normal L1 and R1 modifiers. The edge keeps
        the modifier while the stick rolls sideways; its Release ends it and
        opens the Double Tap window."""
        m = self.m; t = self.title
        cover = t('Normal', 'Consumed')
        for direction, input_name in m.DIRECTIONS.items():
            name = t('Mod ' + ('1' if direction == 'Up' else '0'))
            inputs = self.ls_base()
            for other in DPAD:
                if other in m.DIRECTIONS.values():
                    # The opposite direction only cleans up. The W or S layer's
                    # own bind then brings in the other modifier.
                    inputs[other] = m.full(m.op('remove', name), interruptable=0)
                else:
                    # Rolling sideways uses up the tap at once; the modifier stays.
                    payload = m.commands(inputs[other]['activators']['Full_Press'])
                    inputs[other] = m.full(m.seq(*payload, m.op('add', cover)), interruptable=0)
            inputs[input_name] = m.inp(
                chord=self.chorded_delay(m.op('add', cover), lean.DRIVER_MASK[self.variant], m.HOLD_MS,
                                         interruptable=0),
                Full_Press=m.entry(m.op('remove', cover), hold_repeats=1,
                                   repeat_rate=m.HOLD_MS + 50, interruptable=0))
            inputs['edge'] = m.inp(release=m.entry(m.seq(*self.start_window('Normal', direction))))
            self.add_to_source(name, 'joystick', inputs, self.ls_settings())

    def build_consumed(self):
        m = self.m
        super().build_consumed()
        name = self.title('Normal', 'Consumed')
        self.sources(name)['joystick']['inputs']['edge'] = m.inp(
            release=m.entry(m.seq(*self.clear(self.banks[:2] + [name]))))

    def build_repeats(self):
        """The Double Tap Cover's direction release and edge Release remove it
        and add nothing, like L1: Double Tap Cover."""
        m = self.m
        super().build_repeats()
        name = self.title('Repeat')
        inputs = self.sources(name)['joystick']['inputs']
        for input_name in m.DIRECTIONS.values():
            inputs[input_name]['activators']['release'] = m.entry(m.op('remove', name))
        inputs['edge'] = m.inp(release=m.entry(m.op('remove', name)))

    def build_windows(self):
        """The two Double Tap windows as Always On windows. A window binds the
        stick and both drivers itself, so nothing that changes layers is
        inherited; the fix pipeline derives the remaining blocks."""
        m = self.m; t = self.title
        for direction in m.DIRECTIONS:
            name = t('Normal', direction, 'Double Window')
            inputs = self.ls_base()  # left and right: plain A and D, the window stays
            for newdir, newinput in m.DIRECTIONS.items():
                # Own direction: the repeating scroll. Opposite: drop the pending
                # scroll; the W or S layer's bind then adds the other modifier.
                inputs[newinput] = m.full(m.seq(m.op('remove', name), m.op('add', t('Repeat')))
                                          if newdir == direction else m.op('remove', name))
            self.group(name, 'joystick', inputs, self.ls_settings())
            timeout = {'always_on_action': m.inp(Full_Press=m.entry(
                self.flush_window(name, direction), delay_start=m.DOUBLE_MS, interruptable=0))}
            # No chords on the drivers, so Modifier 2 can't be entered during
            # the window. Each release removes the window first, then the family.
            self.drives(name, {owner: m.inp(Full_Press=m.entry(m.key(owner), interruptable=0),
                                            release=m.entry(m.seq(*self.exit_branch(name))))
                               for owner in m.OWNERS}, timeout)
            # Sources window_pads and window_routes write their blocks into.
            for source in ('left_trigger', 'right_trigger'):
                if source not in self.sources(name):
                    self.group(name, source, {}, {}, 'trigger')
            for source in ('left_trackpad', 'right_trackpad'):
                self.group(name, source, {}, {}, 'disabled')

    def build_menu(self):
        m = self.m
        self.rs_dpad = {k: v for k, v in self.sources(fn_layer('Left'))['right_joystick']['settings'].items()
                        if k in ('requires_click', 'layout', 'deadzone')}
        # The two Steering Entry Points and the two guards take the four slots
        # of Lean's protected flow, so no runtime ID shifts; the cover is appended.
        for side, stick_side in zip(MENU, STICKS):
            self.clone(entry_point(side), entry_point(side, steering=True))
            self.retarget(entry_point(side, steering=True), entry_point(side))
            self.layer(guard(stick_side))
        self.layer(COVER)
        self.menu_helpers = [n for n in self.new if n not in self.family]
        # The click's clear list: everything above Base except Gyro, both
        # transitions included. Generated here, once every layer exists.
        self.menu_clear = self.clear([n for n in self.by_title if n not in ('Base', 'Gyro')])
        for side in MENU:
            cross, same = ('right_joystick', 'joystick') if side == 'Left' else ('joystick', 'right_joystick')
            # Same-side gestures clear until Gamepad brings Transition 0.
            self.build_entry_point(entry_point(side), side, {cross: CROSS, same: CLEAR})
            self.build_entry_point(entry_point(side, steering=True), side, dict.fromkeys(STICKS.values(), CLEAR))
            self.build_fn(side)
        for stick_side in STICKS:
            self.build_guard(stick_side)
        self.build_menu_cover()
        self.build_transitions()
        base = self.patch('Base', 'switch')['inputs']
        for side, (button, _, _) in MENU.items():
            base[button] = m.full(m.op('add', entry_point(side)), hold_repeats=1)

    def retarget(self, name, old):
        """Point a clone's references to its original at the clone itself."""
        old, new = '{{Base::' + old + '}}', '{{Base::' + name + '}}'
        for group in self.sources(name).values():
            for binding in group.get('inputs', {}).values():
                for _, e in self.m.entries(binding):
                    b = e['bindings']['binding']
                    e['bindings']['binding'] = ([c.replace(old, new) for c in b] if isinstance(b, list)
                                                else b.replace(old, new))

    def build_entry_point(self, name, side, transitions):
        """All four Entry Points share everything except where the clicks lead."""
        m = self.m
        button, legacy, _ = MENU[side]
        other = next(b for b, _, _ in MENU.values() if b != button)
        switches = self.patch(name, 'switch')['inputs']
        switches[button]['activators']['chord']['settings']['delay_start'] = str(HOLD_MS)
        switches[button]['activators']['Full_Press']['settings']['repeat_rate'] = str(RESET_MS)
        # The other menu button only adds Fn; Backspace and Enter live in Fn alone.
        early = switches[other]['activators']['chord']
        kept = [c for c in m.commands(early) if 'add_layer' not in c or c == m.op('add', fn_layer(side))]
        if len(kept) != len(m.commands(early)) - 1:
            raise ValueError(f'{name}: expected one overlay add on {other}, found {m.commands(early)}')
        early['bindings']['binding'] = kept
        for stick_side, source in STICKS.items():
            inputs = {
                'touch': self.sources(name)[source]['inputs']['touch'],
                # Release only: binding the click replaces the whole input, so
                # Base's Q and E don't fire with a menu button held.
                'click': m.inp(release=m.entry(m.seq(*self.menu_clear, m.op('add', transitions[source])))),
                'edge': m.inp(chord=m.entry(m.op('add', guard(stick_side)), chord_button=legacy,
                                            hold_repeats=1, repeat_rate=EDGE_REPEAT_MS, interruptable=0))}
            if source == 'right_joystick':
                # A D-pad with empty directions: the camera is dead while a menu
                # button is held, and Fn and the guards can inherit the click.
                inputs.update({direction: m.full() for direction in DPAD})
            self.group(name, source, inputs, self.stick_settings(source), 'dpad')
            self.changed.append((name, source))

    def build_fn(self, side):
        """Fn inherits both stick clicks from the Entry Point underneath, and its
        release and recoveries also retire the guards, the cover and Steering's
        Entry Point."""
        m = self.m
        fn = fn_layer(side)
        own = {m.op('remove', entry_point(side)), m.op('remove', fn)}
        stale = self.clear([COVER] + [guard(s) for s in STICKS] + [entry_point(side, steering=True)])
        shifts = set()
        for source in [s for s in self.sources(fn) if s != 'gyro']:
            group = self.patch(fn, source)
            for binding in group['inputs'].values():
                for _, e in m.entries(binding):
                    if set(m.commands(e)) == own:
                        e['bindings']['binding'] = m.seq(*stale, *reversed(m.commands(e)))
            if source in STICKS.values():
                del group['inputs']['click']
                group['settings']['edge_binding_invert'] = '0'
            if source == 'switch':
                for click in ('left_stick_click', 'right_stick_click'):
                    shifts.update(re.findall(r'mode_shift \S+ (\d+)', json.dumps(group['inputs'].pop(click))))
        slots = self.presets[self.by_title[fn]]['group_source_bindings']
        for gid in shifts:
            del slots[gid]
        self.replaced_groups |= shifts

    def build_guard(self, stick_side):
        """A guard behaves like the Entry Point for the menu button that is held,
        but its hold brings in the Tap Cover where the Entry Point brings in Fn.
        One guard per stick serves both menu sides and all four Entry Points."""
        m = self.m
        name = guard(stick_side)
        switches = {}
        for side, (button, legacy, _) in MENU.items():
            switches[button] = m.inp(
                release=m.entry(m.seq(*self.menu_exit(), m.op('add', f'Menu {side}: Double Tap')),
                                haptic_intensity=0),
                chord=m.entry(m.op('add', COVER), chord_button=legacy, delay_start=HOLD_MS),
                Full_Press=m.entry(m.op('remove', COVER), hold_repeats=1, repeat_rate=RESET_MS, interruptable=0))
        self.group(name, 'switch', switches)
        # Stale guard: a touch with no menu button held clears the menu flow.
        recovery = self.clear([guard(s) for s in STICKS] + [COVER] + [entry_point(side, steering)
                              for side in MENU for steering in (False, True)])
        for source in STICKS.values():
            inputs = {'touch': m.inp(
                Full_Press=m.entry(m.seq(*recovery), hold_repeats=1),
                chord=m.entry(m.EMPTY, gyro_ratchet_button_mask=MENU_ANY,
                              gyro_ratchet_button_requireany_or_all=0, interruptable=0),
                release=m.entry(m.seq(m.op('add', COVER), *self.stick_cleanup(source)), haptic_intensity=0))}
            if source == STICKS[stick_side]:
                # The guard is added while the stick is out; recentring ends it.
                inputs['edge'] = m.inp(release=m.entry(m.op('remove', name)))
            self.group(name, source, inputs, self.stick_settings(source), 'dpad')

    def build_menu_cover(self):
        """One cover for both menu buttons, like L1&R1: Tap Cover. It hides the
        guard's hold and reset, and its empty edges keep new guards off it."""
        m = self.m
        release = m.seq(*self.clear([COVER]), *self.menu_exit())
        self.group(COVER, 'switch', {button: m.inp(Full_Press=m.entry(m.EMPTY, interruptable=0),
                                                   release=m.entry(release)) for button, _, _ in MENU.values()})
        for source in STICKS.values():
            self.group(COVER, source, {'edge': m.full()}, self.stick_settings(source), 'dpad')

    def build_transitions(self):
        """Both transitions, written whole. Nothing can be entered from one:
        every layer-adding input of Base and Gyro is empty or disabled. A
        release that commits to a stateful layer beeps and pulses; one that
        only ends the transition is silent."""
        m = self.m
        commit = {CROSS: {'button_escape': [m.op('add', self.title(), beep=1),
                                            m.op('add', self.title('Entry Guard'))]}}
        for name in (CROSS, CLEAR):
            switches = self.patch(name, 'switch')['inputs']
            for button, _, _ in MENU.values():
                adds = commit.get(name, {}).get(button, [])
                feedback = {'haptic_intensity': COMMIT_HAPTIC} if adds else {}
                switches[button] = m.inp(release=m.entry(m.seq(m.op('remove', name), *adds), **feedback))
            switches['left_bumper'] = m.full(); switches['right_bumper'] = m.full()
            for source in ('left_trigger', 'right_trigger'):
                self.patch(name, source)['inputs']['edge'] = m.full()
            for source in STICKS.values():
                group = self.patch(name, source)
                group['inputs'] = {'click': m.full(), 'edge': m.full(), 'touch': m.inp(
                    release=m.entry(m.seq(*self.stick_cleanup(source)), haptic_intensity=0))}
                if source == 'joystick':
                    for direction in DPAD:
                        group['inputs'][direction] = m.output_only(self.base_groups['joystick']['inputs'][direction])

    def build_touch_cleanup(self):
        # Lean's contracts are for the steering family. The menu layers bring
        # their own touch binds (or inherit them, for the cover), so they sit
        # this pass out, and so do the windows.
        m = self.m
        everything = self.new
        self.new = [n for n in everything if n not in self.menu_helpers + self.windows]
        try:
            super().build_touch_cleanup()
        finally:
            self.new = everything
        # An Always On window removes itself first, then that side's trio.
        for name in self.windows:
            for source in STICKS.values():
                self.add_to_source(name, source, {'touch': m.inp(release=m.entry(
                    m.seq(m.op('remove', name), *self.stick_cleanup(source)), haptic_intensity=0))})

    def finish(self):
        self.build_core(); self.build_consumed(); self.build_strokes(); self.build_repeats()
        self.build_menu(); self.build_windows(); self.build_quick_base_exit(); self.build_touch_cleanup()
        self.build_rs_edge_blocks()
        self.cm['title'] += ' | stateful transitions candidate'
        self.cm['description'] = (
            'Stateful transitions candidate; device verification pending. Menu + stick click, release the '
            'click, then the menu button. Right Menu + LS click enters Steering; every gesture inside '
            'Steering clears. Stick out while a menu button is held: no Fn. '
            'See findings/2026-10-01-stateful-transitions/README.md.')
        self.pruned_groups = self.prune_replaced_groups()
        touched = set(self.new) | {name for name, _ in self.changed}
        for name in touched:
            for source, g in self.sources(name).items():
                for input_name, binding in g.get('inputs', {}).items():
                    banned = set(binding.get('activators', {})) & set(lean.BANNED_ACTIVATORS)
                    if banned:
                        raise ValueError(f'banned activator {sorted(banned)}: {name} {source} {input_name}')
        report = audit_layout(self.data)
        if report['violations']:
            raise ValueError(report['violations'])
        always_on = [name for name in self.new if any('always_on_action' in g.get('inputs', {})
                                                      for g in self.sources(name).values())]
        if always_on != self.windows:
            raise ValueError(f'new Always On layers {always_on}, expected {self.windows}')
        return self.data


def Builder(variant):
    # Lean's factory binds the frozen baseline module for this variant; reuse
    # its class so title resolution can't leak across builders.
    return type('Concrete', (Stateful, type(lean.Builder(variant))), {})(variant)


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
        stem = HERE / f'{variant}-stateful-transitions'
        stem.with_suffix('.readable.json').write_text(readable)
        stem.with_suffix('.json').write_text(numeric)
        if args.vdf:
            subprocess.run(['node', str(ROOT / 'convert_vdf.mjs'), str(stem.with_suffix('.json'))], check=True)
        manifest[variant] = {
            'source_sha256': hashlib.sha256(b.source.read_bytes()).hexdigest(),
            'lean_generator_sha256': hashlib.sha256(LEAN.read_bytes()).hexdigest(),
            'baseline_generator_sha256': hashlib.sha256(lean.BASELINE.read_bytes()).hexdigest(),
            'candidate_sha256': hashlib.sha256(numeric.encode()).hexdigest(),
            'new_layers': b.new, 'new_layer_count': len(b.new),
            'total_layer_count': len(b.cm['action_layers']), 'menu_layers': b.menu_helpers,
            'new_always_on': b.windows, 'modified_sources': b.changed,
            'resolved_references': count, 'pruned_replaced_groups': b.pruned_groups,
            'device_status': 'UNTESTED',
            'timing_ms': {'menu_hold': HOLD_MS, 'menu_reset': RESET_MS, 'edge_repeat': EDGE_REPEAT_MS,
                          'modifier_select_repeat': SELECT_REPEAT_MS, 'hold': b.m.HOLD_MS,
                          'commit_haptic_intensity': COMMIT_HAPTIC,
                          'double': b.m.DOUBLE_MS, 'warning': 1000, 'exit': 2500}}
    (HERE / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')


if __name__ == '__main__':
    main()
