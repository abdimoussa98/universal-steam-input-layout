"""Build separate lean steering candidates; no new Always On actions.

Reuse the frozen baseline's serializer/source extraction, not its generated
exports. Each builder loads its own module so variant title resolution cannot
leak across builders. Native scheduling and held-output gates remain required.
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
from audit_command_budget import audit_layout
from convert_runtime_ids import generate_lookup, titles_to_ids, ids_to_titles

BASELINE = ROOT / 'findings/2026-09-29-steering-implementation/build_candidate.py'
# Modern chord masks (k_eGamepadButtonBitMask_*). Long/Double Press are banned
# repo-wide; hold thresholds are chorded delays instead.
LS_DEFLECT_MASK = 1 << 30
DRIVER_MASK = {'default': 4 | 8, 'alternative': 1 | 2 | (1 << 24) | (1 << 25)}
BANNED_ACTIVATORS = ('Long_Press', 'Double_Press')


class Lean:
    def title(self, *parts):
        if not parts:
            return 'Steering'
        left, right = ('L1', 'R1') if self.variant == 'default' else ('L2', 'R2')
        roles = {
            ('W',): f'{right}: W Key', ('S',): f'{left}: S Key',
            ('Entry Guard',): 'LS: Entry Point', ('Repeat',): 'LS: Double Tap Cover',
            ('Mod 0',): 'LS Down: Modifier 0', ('Mod 1',): 'LS Up: Modifier 1',
            ('Mod2', 'W'): f'{right}!{left}: Modifier 2',
            ('Mod2', 'S'): f'{left}!{right}: Modifier 2',
            
            ('Normal', 'Consumed'): 'LS: Tap Cover',
            ('Mod2', 'Consumed'): 'Modifier 2 | LS: Tap Cover',
        }
        if parts == ('Mod2 Cover', 'W'):
            return f'{left}: Tap Cover'
        if parts == ('Mod2 Cover', 'S'):
            return f'{right}: Tap Cover'
        if parts in roles:
            suffix = roles[parts]
        elif len(parts) == 3 and parts[-1] in ('Stroke', 'Double Window', 'Repeat'):
            context, direction, phase = parts
            scope = '' if context == 'Normal' else 'Modifier 2 | '
            label = {'Stroke': 'Entry Point', 'Double Window': 'Double Tap',
                     'Repeat': 'Double Tap Cover'}[phase]
            suffix = f'{scope}LS {direction}: {label}'
        elif len(parts) == 2 and parts[-1] == 'Repeat':
            suffix = f'LS {parts[0]}: Double Tap Cover'
        else:
            raise ValueError(parts)
        return 'Steering | ' + suffix

    def __init__(self, variant):
        self.variant = variant
        self.m.title = self.title
        self.replaced_groups = set()
        super().__init__(variant)
        t = self.title
        self.stroke = []
        self.windows = [t('Normal', d, 'Double Window') for d in self.m.DIRECTIONS]
        self.repeats = [t('Repeat')]
        self.banks = [t('Mod 0'), t('Mod 1'), t('Mod2', 'W'), t('Mod2', 'S')]
        self.consumed = [t('Normal', 'Consumed')]
        self.mod2_covers = [t('Mod2 Cover', o) for o in self.m.OWNERS]
        self.gestures = self.stroke + self.windows + self.repeats + self.consumed + self.mod2_covers
        self.branch = self.gestures + self.banks + [t(o) for o in self.m.OWNERS] + [t('Entry Guard')]
        self.family = [n for n in self.branch if n not in self.mod2_covers] + [t()]
        self.menu_helpers = []
        # The two orders may have different output payloads in future sources.
        left, right = ('L1', 'R1') if variant == 'default' else ('L2', 'R2')
        self.mod2_maps = {'W': self.sources(f'{right}!{left}: Modifier 2'),
                          'S': self.sources(f'{left}!{right}: Modifier 2')}

    def exit_branch(self, first=None):
        return self.clear(([first] if first else []) + self.branch)

    def group(self, name, source, inputs, settings=None, mode=None):
        p = self.presets[self.by_title[name]]
        self.replaced_groups.update(g for g, b in p['group_source_bindings'].items() if b == source + ' active')
        return super().group(name, source, inputs, settings, mode)

    def chorded_delay(self, binding, mask, delay, **settings):
        return self.m.entry(binding, gyro_ratchet_button_mask=mask,
                            gyro_ratchet_button_requireany_or_all=0, delay_start=delay, **settings)

    def prune_replaced_groups(self):
        # Drop only groups this build unbound; pre-existing orphans are left to
        # prune_dead_groups.py so candidates stay comparable with the source.
        referenced = {g for p in self.cm['preset'] for g in p['group_source_bindings']}
        referenced |= set(re.findall(r'mode_shift \S+ (\d+)', json.dumps(self.cm['group'])))
        dead = self.replaced_groups - referenced
        self.cm['group'] = [g for g in self.cm['group'] if g['id'] not in dead]
        for gid in dead:
            self.groups.pop(gid, None)
        return sorted(dead, key=int)

    def context_enter(self, owner, first=None):
        m = self.m
        return self.clear(([first] if first else []) + self.gestures + self.banks) + [
            m.op('add', self.title('Normal', 'Consumed')),
            m.op('add', self.title('Mod2', owner))]

    def context_leave(self, first=None):
        return self.clear(([first] if first else []) + self.gestures + self.banks) + [
            self.m.op('add', self.title('Normal', 'Consumed'))]

    def selectors(self, owner, context):
        m = self.m
        inputs = self.ls_base()
        for direction, input_name in m.DIRECTIONS.items():
            if context == 'Mod2':
                inputs[input_name] = m.full(m.wheel(direction), hold_repeats=1,
                                           repeat_rate=m.REPEAT_MS, interruptable=0)
            else:
                bank = self.title('Mod ' + ('1' if direction == 'Up' else '0'))
                # The selected bank overrides this whole input, retiring both
                # the pending apply and its interrupted-delay reset.
                inputs[input_name] = m.inp(Full_Press=[
                    m.entry(m.seq(*self.clear(self.banks[:2]), m.op('add', bank)),
                            delay_start=5, interruptable=0),
                    m.entry(m.op('remove', bank), hold_repeats=1,
                            repeat_rate=50, interruptable=0)])
        return inputs

    def acquisition(self):
        m = self.m; t = self.title
        return {owner: m.inp(
            Full_Press=m.entry(m.seq(m.op('remove', t('Entry Guard')),
                m.op('add', t(owner)), m.op('add', t('Normal', 'Consumed'))),
                hold_repeats=1, repeat_rate=50),
            chord=m.entry(m.op('remove', t('Entry Guard')),
                gyro_ratchet_button_mask=self.opposite_mask(owner),
                gyro_ratchet_button_requireany_or_all=0, interruptable=0))
            for owner in m.OWNERS}

    def owner_selectors(self, owner):
        # Mod2 variants own their selectors; ordinary owners only route Normal.
        return self.selectors(owner, 'Normal')

    def add_to_source(self, name, source, inputs, settings=None):
        existing = self.sources(name).get(source)
        merged = copy.deepcopy(existing.get('inputs', {})) if existing else {}
        merged.update(inputs)
        return self.group(name, source, merged,
                          settings if settings is not None else existing.get('settings', {}) if existing else {},
                          existing['mode'] if existing else None)

    def build_core(self):
        m = self.m; t = self.title
        for n in self.family:
            self.layer(n)
        inputs = self.ls_base(vertical=True)
        inputs['touch'] = m.full()
        # Fallback warning/exit: chorded delays on LS deflection. Entry Guard
        # overrides this input, so W carried through entry has no clock.
        inputs['dpad_north'] = m.inp(Full_Press=m.entry(m.key('W'), interruptable=0), chord=[
            self.chorded_delay(m.EMPTY, LS_DEFLECT_MASK, 1000, hold_repeats=1, repeat_rate=250,
                               haptic_intensity=3, interruptable=0),
            self.chorded_delay(m.seq(*self.exit_all(beep=True)), LS_DEFLECT_MASK, 2500,
                               haptic_intensity=3, interruptable=0)])
        self.group(t(), 'joystick', inputs, self.ls_settings())
        self.drives(t(), self.acquisition(), self.menu_switches())
        # Base's RTP touch is the only way into RTP: Double Tap (Always On),
        # which would inherit steering's LS layer commands. Mouse and click stay.
        self.group(t(), 'right_trackpad', {'touch': m.full()})
        guard = self.ls_base(vertical=True)
        guard['edge'] = m.full(m.op('remove', t('Entry Guard')), hold_repeats=1, repeat_rate=50)
        self.group(t('Entry Guard'), 'joystick', guard, self.ls_settings())
        for owner in m.OWNERS:
            ls = self.owner_selectors(owner)
            ls['touch'] = self.owner_recovery(owner)
            self.group(t(owner), 'joystick', ls, self.ls_settings())
            self.drives(t(owner), self.owner_bindings(owner), self.menu_switches())
        for bank in (0, 1):
            self.map_groups(t('Mod ' + str(bank)), bank, consume=True)
        for owner in m.OWNERS:
            old = self.maps[2]
            self.maps[2] = self.mod2_maps[owner]
            self.map_groups(t('Mod2', owner), 2, consume=False)
            self.maps[2] = old
            self.add_to_source(t('Mod2', owner), 'joystick', self.selectors(owner, 'Mod2'), self.ls_settings())

    def build_strokes(self):
        """Normal modifier layers themselves remember the eligible direction."""
        m = self.m; t = self.title
        for direction, input_name in m.DIRECTIONS.items():
            name = t('Mod ' + ('1' if direction == 'Up' else '0'))
            inputs = self.ls_base()
            # Chorded delay plus the scoped interrupted-delay reset (250/300).
            # The applied cover overrides this input and hides the reset. That
            # relies on cover reassertion keeping priority (Deck gate S7); if
            # the bank stayed on top, this reset would strip consumed state.
            consumed = t('Normal', 'Consumed')
            inputs[input_name] = m.inp(
                chord=self.chorded_delay(m.op('add', consumed), LS_DEFLECT_MASK, m.HOLD_MS,
                                         interruptable=0),
                Full_Press=m.entry(m.op('remove', consumed), hold_repeats=1,
                                   repeat_rate=m.HOLD_MS + 50, interruptable=0))
            # Keep the bank until actual center, not the cardinal release.
            inputs['edge'] = m.full(m.seq(*self.start_window('Normal', direction)))
            for other in ('dpad_north', 'dpad_south', 'dpad_east', 'dpad_west'):
                if other == input_name:
                    continue
                payload = m.commands(inputs[other]['activators']['Full_Press'])
                actions = self.clear(self.banks[:2])
                if other in m.DIRECTIONS.values():
                    otherbank = t('Mod ' + ('1' if other == 'dpad_north' else '0'))
                    actions.append(m.op('add', otherbank))
                actions.append(m.op('add', t('Normal', 'Consumed')))
                inputs[other] = m.full(m.seq(*payload, *actions), interruptable=0)
            self.add_to_source(name, 'joystick', inputs, self.ls_settings())

    def start_window(self, context, direction):
        return self.clear(self.stroke + self.consumed + (self.banks[:2] if context == 'Normal' else [])) + [
            self.m.op('add', self.title(context, direction, 'Double Window'))]

    def build_consumed(self):
        """The Tap Cover only means "tap used up": up/down do nothing, and
        center removes Mod 0, Mod 1, then the cover itself, in that order.

        It never adds a modifier. Re-adding an active layer does not move it to
        the top (Valve), so a cover that added a bank above itself would lose
        its center override. It is only ever added fresh, on top of the bank it
        covers, and its empty up/down hide that bank's delayed apply and reset.
        """
        m = self.m; t = self.title
        name = t('Normal', 'Consumed')
        inputs = self.ls_base()
        for input_name in m.DIRECTIONS.values():
            inputs[input_name] = m.full()
        inputs['edge'] = m.full(m.seq(*self.clear(self.banks[:2] + [name])),
                                hold_repeats=1, repeat_rate=50)
        self.group(name, 'joystick', inputs, self.ls_settings())

    def flush_window(self, name, direction, *actions):
        return self.m.seq(self.m.op('remove', name), self.m.wheel(direction), *actions)

    def covers(self):
        """Overlays: only ever added on top of their owner, so they define just
        their own controls and inherit the rest, including touch (DoD §5)."""
        return [self.title('Normal', 'Consumed'), self.title('Repeat')] + [
            self.protected_names(side)[1] for side in ('Left', 'Right')]

    def build_windows(self):
        m = self.m; t = self.title
        for direction, input_name in m.DIRECTIONS.items():
            name = t('Normal', direction, 'Double Window')
            inputs = self.ls_base()
            # The clock runs at center, so it is chorded on the held driver;
            # windows exist only while a driver owns movement.
            inputs['edge'] = m.inp(chord=self.chorded_delay(self.flush_window(name, direction),
                                   DRIVER_MASK[self.variant], m.DOUBLE_MS, interruptable=0))
            for newdir, newinput in m.DIRECTIONS.items():
                if newdir == direction:
                    inputs[newinput] = m.full(m.seq(m.op('remove', name),
                        m.op('add', t('Repeat'))))
                else:
                    bank = t('Mod ' + ('1' if newdir == 'Up' else '0'))
                    inputs[newinput] = m.full(self.flush_window(name, direction,
                        *self.clear(self.banks[:2]), m.op('add', bank)))
            for lateral in ('dpad_east', 'dpad_west'):
                payload = m.commands(inputs[lateral]['activators']['Full_Press'])
                inputs[lateral] = m.full(self.flush_window(name, direction, *payload,
                    m.op('add', t('Normal', 'Consumed'))), interruptable=0)
            clock_settings = self.ls_settings()
            clock_settings['edge_binding_radius'] = '32767'
            # Mapped buttons inherit: none has a layer command underneath, and
            # the clock resolves the pending single on its own.
            self.group(name, 'joystick', inputs, clock_settings)

    def build_repeats(self):
        m = self.m; t = self.title
        name = t('Repeat')
        inputs = {}
        stop = m.seq(m.op('remove', name), m.op('add', t('Normal', 'Consumed')))
        for direction, input_name in m.DIRECTIONS.items():
            # Both directions share one cover. A direction's release tears it
            # down before the opposite direction's delayed wheel can fire.
            # Delayed-output cancellation on reversal is a native release gate.
            inputs[input_name] = m.inp(Full_Press=m.entry(m.wheel(direction),
                hold_repeats=1, repeat_rate=m.REPEAT_MS, delay_start=5, interruptable=0),
                release=m.entry(stop))
        # Sideways inherits the owner's A/D; leaving up/down already stops.
        inputs['edge'] = m.full(stop, hold_repeats=1, repeat_rate=50)
        self.group(name, 'joystick', inputs, self.ls_settings())

    def protected_names(self, side):
        return (f'Steering | Menu {side}: Entry Point', f'Steering | Menu {side}: Tap Cover')

    def transfer(self, side):
        m = self.m
        protected, cover = self.protected_names(side)
        return m.seq(m.op('remove', f'Menu {side}: Entry Point'), m.op('add', protected))

    def build_menu(self):
        m = self.m
        for side in ('Left', 'Right'):
            normal = f'Menu {side}: Entry Point'; fn = f'Menu {side}: Fn Layer'
            protected, cover = self.protected_names(side)
            self.clone(normal, protected); self.layer(cover)
            self.menu_helpers += [protected, cover]
            owner = 'button_menu' if side == 'Left' else 'button_escape'
            other = 'button_escape' if side == 'Left' else 'button_menu'
            legacy = '15' if side == 'Left' else '14'
            explicit = self.patch(fn, 'switch')['inputs'][owner]
            release = explicit['activators']['release']
            release['bindings']['binding'] = m.seq(m.op('remove', cover), m.op('remove', protected),
                                                   *reversed(m.commands(release)))
            # Do not rewrite deliberate Fn click targets or create Fn clones.
            for source, radius in [('joystick', '4915'), ('right_joystick', '7209')]:
                g = self.patch(normal, source)
                g['settings'].update(edge_binding_radius=radius, edge_binding_invert='0')
                g['inputs']['edge'] = m.inp(chord=m.entry(self.transfer(side), chord_button=legacy,
                                                         hold_repeats=1, interruptable=0))
            cleanup = self.clear([cover, protected, normal])
            sw = self.patch(protected, 'switch')['inputs']
            sw[owner] = m.inp(release=m.entry(m.seq(*cleanup, m.key('ESCAPE' if side == 'Left' else 'TAB'))),
                              Full_Press=[m.entry(m.op('add', cover), delay_start=300, interruptable=0),
                                          m.entry(m.op('remove', cover), hold_repeats=1,
                                                  repeat_rate=350, interruptable=0)])
            sw[other] = m.full(); sw['left_stick_click'] = m.full(); sw['right_stick_click'] = m.full()
            for source in ('joystick', 'right_joystick'):
                g = self.patch(protected, source)
                g['inputs']['touch'] = m.full(); g['inputs']['edge'] = m.full()
                dest = 'Transition Set 1' if side == 'Right' and source == 'joystick' else fn
                g['inputs']['click'] = m.inp(chord=m.entry(m.op('add', dest), chord_button=legacy, interruptable=0))
            # The cover only ever sits on its protected entry: it silences the
            # menu release and hides the parent's delayed apply and reset.
            self.group(cover, 'switch', {owner: m.inp(release=m.entry(m.seq(*cleanup)),
                                                      Full_Press=m.entry(m.EMPTY, interruptable=0))})
            if side == 'Right':
                self.patch(normal, 'joystick')['inputs']['click'] = m.inp(chord=m.entry(
                    m.op('add', 'Transition Set 1'), chord_button=14, interruptable=0))
            self.patch('Base', 'switch')['inputs'][owner] = m.inp(
                Full_Press=m.entry(m.op('add', normal), hold_repeats=1),
                chord=m.entry(m.op('add', protected), gyro_ratchet_button_mask=3221225472,
                              gyro_ratchet_button_requireany_or_all=0, interruptable=0))
        # A namespace is not membership: prefixed pre-entry helpers must retire.
        transient = [n for n in self.by_title if n not in ('Base', 'Gyro') and n not in self.family]
        commit = self.clear(transient) + [m.op('add', self.title()), m.op('add', self.title('Entry Guard'))]
        sw = self.patch('Transition Set 1', 'switch')['inputs']
        sw['button_escape'] = m.inp(release=m.entry(m.seq(*commit)))
        sw['button_menu'] = m.full(m.seq(*self.clear(transient)))
        sw['left_stick_click'] = m.full(); sw['right_stick_click'] = m.full()
        for source in ('joystick', 'right_joystick'):
            g = self.patch('Transition Set 1', source)
            for n in ('touch', 'edge', 'click'):
                g['inputs'][n] = m.full()
            if source == 'joystick':
                for n in ('dpad_north', 'dpad_south', 'dpad_east', 'dpad_west'):
                    g['inputs'][n] = m.output_only(self.base_groups['joystick']['inputs'][n])

    def stick_cleanup(self, source):
        prefix = 'LST' if source == 'joystick' else 'RST'
        return self.clear([f'{prefix}: Entry Point', f'{prefix}: Tap Cover',
                           f'{prefix}: Temporary Gyro'])

    def build_touch_cleanup(self):
        """Explicit whole-input touch contracts, with <=3 activator entries.

        Complete a semantic delayed layer transition before side-local removals.
        Wheel/timeout outputs and direction-dependent 5ms routing are not blanket
        early-completion targets. Completed overlays never replay parent adds.
        Existing Always On windows retain their own self-first overrides.
        """
        m = self.m; t = self.title
        for name in self.new:
            if name in self.covers():
                continue
            target = t('Normal', 'Consumed') if name in self.banks[:2] else None
            for o in m.OWNERS:
                if name == t('Mod2', o): target = t('Mod2 Cover', o)
            menu_side = next((side for side in ('Left', 'Right')
                              if name in self.protected_names(side)), None)
            if menu_side and name == self.protected_names(menu_side)[0]:
                target = self.protected_names(menu_side)[1]
            for source in ('joystick', 'right_joystick'):
                if name in (t(), t('Entry Guard')):
                    touch = m.inp()
                elif menu_side:
                    normal = f'Menu {menu_side}: Entry Point'
                    touch = m.inp(Full_Press=m.entry(m.seq(*self.clear(
                        list(self.protected_names(menu_side)) + [normal])), hold_repeats=1),
                        chord=m.entry(m.EMPTY, chord_button=15 if menu_side == 'Left' else 14,
                                      interruptable=0))
                else:
                    owner = next((o for o in m.OWNERS if name in (t(o), t('Mod2', o), t('Mod2 Cover', o))), None)
                    if owner:
                        touch = self.owner_recovery(owner)
                    else:
                        # Shared normal helpers have no encoded owner identity.
                        # Preserve valid driving while either driver is held;
                        # stale complete branch cleanup runs only with neither.
                        touch = m.inp(Full_Press=m.entry(m.seq(*self.exit_branch()), hold_repeats=1),
                            chord=m.entry(m.EMPTY, gyro_ratchet_button_mask=self.mask,
                                          gyro_ratchet_button_requireany_or_all=0, interruptable=0))
                commands = ([m.op('add', target)] if target else []) + self.stick_cleanup(source)
                touch['activators']['release'] = m.entry(m.seq(*commands), haptic_intensity=0)
                self.add_to_source(name, source, {'touch': touch})
        # Commit still excludes touch/edge recovery, but a thumb release must
        # clear its local helpers without triggering Fn or aborting commitment.
        for source in ('joystick', 'right_joystick'):
            touch = m.inp(release=m.entry(m.seq(*self.stick_cleanup(source)), haptic_intensity=0))
            self.add_to_source('Transition Set 1', source, {'touch': touch})

    def build_rs_edge_blocks(self):
        """Clear RS edge while a steering timer is pending (author, 2026-09-30).

        Base's RS edge adds and removes the turn-assist ramp layers, and
        removals can reset a pending timer. The windows (150 ms), Mod 0/1
        (250 ms) and Mod 2 (200 ms) block it; the LS Tap Cover inherits the
        bank's block. Steering and W/S Key keep turn assist: their only
        pending layer timer is the 5 ms selector.
        """
        for name in self.windows + self.banks:
            self.add_to_source(name, 'right_joystick', {'edge': self.m.full()})

    def build_quick_base_exit(self):
        """Reuse the opposite-side single cover without exporting steering state
        into its ordinary Base/Gyro callers. Shared exits only remove layers.
        """
        m = self.m; t = self.title
        self.base_exit_targets = [name for name in self.by_title if name != 'Base']
        for owner in m.OWNERS:
            parent = t('Mod2', owner); cover = t('Mod2 Cover', owner)
            opposite_side = 'left' if owner == 'W' else 'right'
            legacy_owner = (2 if owner == 'W' else 1) if self.variant == 'default' else (8 if owner == 'W' else 7)
            opposite = m.inp(
                release=m.entry(m.seq(*self.clear(self.base_exit_targets)), haptic_intensity=0),
                chord=m.entry(m.op('add', cover), chord_button=legacy_owner,
                              delay_start=200, haptic_intensity=3),
                Full_Press=m.entry(m.op('remove', cover), hold_repeats=1,
                                  repeat_rate=250, interruptable=0))
            source = 'switch' if self.variant == 'default' else opposite_side + '_trigger'
            input_name = opposite_side + '_bumper' if self.variant == 'default' else 'edge'
            settings = None if self.variant == 'default' else {'deadzone_inner_radius': '0', 'adaptive_threshold': '0'}
            self.add_to_source(parent, source, {input_name: opposite}, settings)
            # Extend the original single-side cover's release and stale recovery.
            # Never add Steering/Consumed here: these covers also serve Base.
            for src in (source, 'joystick', 'right_joystick'):
                group = self.patch(cover, src)
                for name, binding in group.get('inputs', {}).items():
                    for kind, e in m.entries(binding):
                        is_driver_release = src == source and name == input_name and kind == 'release'
                        is_recovery = name == 'touch' and kind == 'Full_Press'
                        if is_driver_release or is_recovery:
                            e['bindings']['binding'] = m.seq(*reversed(m.commands(e)),
                                m.op('remove', parent))
            # Mapped actions cover the quick exit, just like existing Mod2.
            for src, group in self.sources(parent).items():
                for name, binding in group.get('inputs', {}).items():
                    for kind, e in m.entries(binding):
                        payload = m.commands(e)
                        if kind == 'chord' and any(c.startswith(('key_press ', 'mouse_button ')) for c in payload):
                            e['bindings']['binding'] = m.seq(m.op('add', cover), *reversed(payload))

    def finish(self):
        self.build_core(); self.build_consumed(); self.build_strokes()
        self.build_repeats(); self.build_menu(); self.build_windows(); self.build_quick_base_exit(); self.build_touch_cleanup()
        self.build_rs_edge_blocks()
        self.cm['title'] += ' | steering lean candidate'
        self.cm['description'] = ('Lean steering candidate; device verification pending. Right Menu + LS click, '
            'release Right Menu to enter. Right driver W, left S; LS Up/Down Modifier 1/0; '
            'opposite Modifier 2. Owner release allows a held opposite to take over; otherwise WASD. Fallback W warns at 1s, exits at 2.5s. '
            'Quick opposite tap in Mod2 clears to Base; hold keeps Mod2. 16 added layers; no new Always On actions. See findings/2026-09-30-steering-lean/README.md.')
        self.pruned_groups = self.prune_replaced_groups()
        touched = set(self.new) | {name for name, _ in self.changed}
        for name in touched:
            for source, g in self.sources(name).items():
                for input_name, binding in g.get('inputs', {}).items():
                    banned = set(binding.get('activators', {})) & set(BANNED_ACTIVATORS)
                    if banned:
                        raise ValueError(f'banned activator {sorted(banned)}: {name} {source} {input_name}')
        report = audit_layout(self.data)
        if report['violations']:
            raise ValueError(report['violations'])
        for name in self.new:
            if any('always_on_action' in g.get('inputs', {}) for g in self.sources(name).values()):
                raise ValueError('new Always On: ' + name)
        return self.data


def Builder(variant):
    spec = importlib.util.spec_from_file_location('steering_baseline_' + variant, BASELINE)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    # Baseline construction computes its old family before Lean replaces it.
    original_title = module.title
    class Concrete(Lean, module.Builder):
        m = module
        def title(self, *parts):
            try:
                return super().title(*parts)
            except ValueError:
                return original_title(*parts)
    return Concrete(variant)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
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
        stem = HERE / f'{variant}-steering-lean'
        stem.with_suffix('.readable.json').write_text(readable)
        stem.with_suffix('.json').write_text(numeric)
        if args.vdf:
            subprocess.run(['node', str(ROOT / 'convert_vdf.mjs'), str(stem.with_suffix('.json'))], check=True)
        rows = []
        for name in b.new:
            for source, group in b.sources(name).items():
                for input_name, binding in group.get('inputs', {}).items():
                    rows.append({'layer': name, 'source': source, 'group': group['id'],
                        'input': input_name, 'source_settings': group.get('settings', {}),
                        'activators': [{'type': kind, 'settings': e.get('settings', {}),
                            'execution_order': list(reversed(b.m.commands(e)))} for kind, e in b.m.entries(binding)]})
        (HERE / f'{variant}-bindings.json').write_text(json.dumps(rows, indent=2) + '\n')
        manifest[variant] = {'source_sha256': hashlib.sha256(b.source.read_bytes()).hexdigest(),
            'baseline_generator_sha256': hashlib.sha256(BASELINE.read_bytes()).hexdigest(),
            'candidate_sha256': hashlib.sha256(numeric.encode()).hexdigest(),
            'new_layers': b.new, 'new_layer_count': len(b.new), 'total_layer_count': len(b.cm['action_layers']),
            'new_always_on_count': 0, 'modified_sources': b.changed, 'resolved_references': count,
            'device_status': 'UNTESTED', 'planned_target': 16,
            'quick_base_exit_targets': b.base_exit_targets, 'reused_mod2_covers': b.mod2_covers,
            'pruned_replaced_groups': b.pruned_groups,
            'timing_ms': {'hold': b.m.HOLD_MS, 'double': b.m.DOUBLE_MS, 'single': b.m.DOUBLE_MS,
                          'repeat': b.m.REPEAT_MS, 'warning': 1000, 'exit': 2500, 'quick_pair': 200}}
    (HERE / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')


if __name__ == '__main__':
    main()
