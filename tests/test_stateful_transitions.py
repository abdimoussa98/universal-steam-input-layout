"""The stateful transition structure, checked on the generated candidates.

Builds both variants with the 2026-10-01 builder and runs the fix pipeline, as
the install does (plans/2026-10-01-stateful-transitions-implementation.md).
These verify saved configuration contracts, not Steam's runtime scheduling.
The working layouts are pinned to the build that extends this one
(tests/test_steering_fallback_hold.py).
"""
import importlib.util
import json
from pathlib import Path
import re
import tempfile
import unittest

from tools.audit_command_budget import audit_layout
from tools import audit_flow_inheritance
from steam_layout.fixes import apply_all
from steam_layout.inheritance import audit, check_stack
from steam_layout.model import EMPTY, Layout, actions, always_on_layers, bindings, entries

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    'stateful_transitions', ROOT / 'findings/2026-10-01-stateful-transitions/build_candidate.py')
st = importlib.util.module_from_spec(spec); spec.loader.exec_module(st)

SIDES = {'Left': ('button_menu', '15'), 'Right': ('button_escape', '14')}
STICKS = {'Left': 'joystick', 'Right': 'right_joystick'}
GUARDS = [st.guard(s) for s in STICKS]
ENTRY_POINTS = [st.entry_point(side, steering) for side in SIDES for steering in (False, True)]
FN_LAYERS = [st.fn_layer(side) for side in SIDES]
TRIO = {'joystick': 'LST', 'right_joystick': 'RST'}
LS_COVER, LS_REPEAT = 'Steering | LS: Tap Cover', 'Steering | LS: Double Tap Cover'
MODIFIERS = {'Up': 'Steering | LS Up: Modifier 1', 'Down': 'Steering | LS Down: Modifier 0'}
WINDOWS = {'Up': 'Steering | LS Up: Double Tap', 'Down': 'Steering | LS Down: Double Tap'}
DIRECTIONS = {'Up': 'dpad_north', 'Down': 'dpad_south'}
ANY, ALL = '0', '1'


class StatefulTransitionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.builders, cls.data, cls.layouts = {}, {}, {}
        for variant in ('default', 'alternative'):
            b = cls.builders[variant] = st.Builder(variant)
            data = cls.data[variant] = b.finish()
            apply_all(data)
            cls.layouts[variant] = Layout(data)

    def each(self):
        for variant, layout in self.layouts.items():
            with self.subTest(variant=variant):
                yield self.builders[variant], layout

    def acts(self, layout, layer, source, name):
        return layout.active(layer)[source]['inputs'][name]['activators']

    def ops(self, layout, entry):
        return layout.layer_ops(entry)

    def is_empty(self, activators):
        return [b for b in bindings(activators)] == [EMPTY + ', , ']

    def driver(self, b, layout, layer, owner):
        """The W (right) or S (left) driver's activators: a bumper in the default, a soft pull in the alternative."""
        side = 'right' if owner == 'W' else 'left'
        if b.variant == 'default':
            return self.acts(layout, layer, 'switch', side + '_bumper')
        return self.acts(layout, layer, side + '_trigger', 'edge')

    def steering_layers(self, layout):
        return [name for name in layout.presets if name == 'Steering' or name.startswith('Steering | ')]

    def test_layers_keep_their_positions(self):
        renamed = {'Steering | LS: Entry Point': 'Steering | LS: Entry Guard',
                   'Steering | Menu Left: Tap Cover': GUARDS[0], 'Steering | Menu Right: Tap Cover': GUARDS[1]}
        for b, layout in self.each():
            released = Layout(json.loads((ROOT / f'versions/neptune/90.9/single-set-{b.variant}_hold-gyro_90.9.json')
                                         .read_text()))
            before = [released.titles[k] for k in released.order]
            after = [layout.titles[k] for k in layout.order]
            self.assertEqual(after, [renamed.get(t, t) for t in before] + [st.COVER])

    def test_entry_point_clicks_release_into_their_transition(self):
        targets = {'Menu Left: Entry Point': (st.CLEAR, st.CROSS), 'Menu Right: Entry Point': (st.CROSS, st.CLEAR),
                   'Steering | Menu Left: Entry Point': (st.CLEAR, st.CLEAR),
                   'Steering | Menu Right: Entry Point': (st.CLEAR, st.CLEAR)}
        for b, layout in self.each():
            everything = set(layout.presets) - {'Base', 'Gyro'}
            for name, transitions in targets.items():
                for source, transition in zip(STICKS.values(), transitions):
                    click = self.acts(layout, name, source, 'click')
                    self.assertEqual(list(click), ['release'], (name, source))
                    ops = self.ops(layout, click['release'])
                    # The clear list runs first; the transition is added last.
                    self.assertEqual(ops[-1], ('add_layer', transition), (name, source))
                    self.assertEqual({t for op, t in ops[:-1] if op == 'remove_layer'}, everything)
                    self.assertEqual(len(ops), len(everything) + 1)

    def test_entry_point_sticks_are_dpads_that_add_the_guard(self):
        for b, layout in self.each():
            for name in ENTRY_POINTS:
                side = 'Left' if 'Left' in name else 'Right'
                for stick_side, source in STICKS.items():
                    group = layout.active(name)[source]
                    self.assertEqual(group['mode'], 'dpad')
                    self.assertEqual((group['settings']['edge_binding_radius'], group['settings']['edge_binding_invert']),
                                     ('4915', '0'))
                    edge = self.acts(layout, name, source, 'edge')
                    self.assertEqual(list(edge), ['chord'])
                    # Repeats inside the Fn delay, so a stick that was already out gets its guard in time.
                    self.assertEqual(edge['chord']['settings'], {'chord_button': SIDES[side][1], 'hold_repeats': '1',
                                                                 'repeat_rate': '50', 'interruptable': '0'})
                    self.assertEqual(self.ops(layout, edge['chord']), [('add_layer', st.guard(stick_side))])
                for direction in st.DPAD:
                    self.assertTrue(self.is_empty(self.acts(layout, name, 'right_joystick', direction)))

    def test_entry_points_only_add_fn_and_fn_types_the_key(self):
        for b, layout in self.each():
            for name in ENTRY_POINTS:
                side = 'Left' if 'Left' in name else 'Right'
                button, legacy = SIDES[side]
                other = next(x for x, _ in SIDES.values() if x != button)
                key = 'RETURN' if side == 'Left' else 'BACKSPACE'
                typed = [x for g in layout.active(name).values() for v in g.get('inputs', {}).values()
                         for x in bindings(v.get('activators', {})) if 'BACKSPACE' in x or 'RETURN' in x]
                self.assertEqual(typed, [], name)
                early = self.acts(layout, name, 'switch', other)['chord']
                self.assertEqual(self.ops(layout, early), [('add_layer', st.fn_layer(side))])
                own = self.acts(layout, st.fn_layer(side), 'switch', other)['chord']
                self.assertIn(f'key_press {key}, , ', actions(own))
                hold = self.acts(layout, name, 'switch', button)
                self.assertEqual(hold['chord']['settings'], {'chord_button': legacy, 'delay_start': '200'})
                self.assertEqual(hold['Full_Press']['settings'],
                                 {'hold_repeats': '1', 'repeat_rate': '250', 'interruptable': '0'})
                self.assertEqual(self.ops(layout, hold['release']),
                                 [('remove_layer', name), ('add_layer', f'Menu {side}: Double Tap')])

    def test_fn_layers_and_guards_bind_no_stick_click(self):
        for b, layout in self.each():
            for name in FN_LAYERS + GUARDS + [st.COVER]:
                for source in STICKS.values():
                    self.assertNotIn('click', layout.active(name)[source].get('inputs', {}), (name, source))
            for name in FN_LAYERS:
                switches = layout.active(name)['switch']['inputs']
                self.assertFalse({'left_stick_click', 'right_stick_click'} & set(switches))
                slots = layout.presets[name]['group_source_bindings'].values()
                self.assertFalse([s for s in slots if 'modeshift' in s], name)

    def test_every_layer_of_a_menu_hold_keeps_both_sticks_in_dpad_mode(self):
        # A group in another mode would block the click and touch inheritance.
        for b, layout in self.each():
            for name in ENTRY_POINTS + FN_LAYERS + GUARDS + [st.COVER]:
                for source in STICKS.values():
                    self.assertEqual(layout.active(name)[source]['mode'], 'dpad', (name, source))

    def test_fn_exits_retire_both_entry_points(self):
        # A stick guard cancels Fn's 200 ms delay, so the guards and the menu Tap Cover are never on the
        # stack with Fn. The fix pipeline drops them (cleanup rule 6; no race rule, author 2026-10-02).
        for b, layout in self.each():
            for side, (button, _) in SIDES.items():
                fn = st.fn_layer(side)
                expected = [('remove_layer', t) for t in [st.entry_point(side, steering=True), st.entry_point(side), fn]]
                self.assertEqual(self.ops(layout, self.acts(layout, fn, 'switch', button)['release']), expected)
                recoveries = [self.ops(layout, e) for g in layout.active(fn).values()
                              for v in g.get('inputs', {}).values() for kind, e in entries(v.get('activators', {}))
                              if kind == 'Full_Press' and e.get('settings', {}).get('hold_repeats') == '1']
                self.assertTrue(recoveries)
                self.assertTrue(all(ops == expected for ops in recoveries), fn)

    def test_guards_hold_into_the_tap_cover_and_tap_into_the_window(self):
        # No Fn layer: it is never on the stack with a guard (cleanup rule 6, author 2026-10-02).
        left_behind = {('remove_layer', t) for t in GUARDS + ENTRY_POINTS}
        for b, layout in self.each():
            for stick_side, own in STICKS.items():
                name = st.guard(stick_side)
                for side, (button, legacy) in SIDES.items():
                    acts = self.acts(layout, name, 'switch', button)
                    self.assertEqual(list(acts), ['release', 'chord', 'Full_Press'])
                    release = self.ops(layout, acts['release'])
                    self.assertEqual(set(release[:-1]), left_behind)
                    self.assertEqual(release[-1], ('add_layer', f'Menu {side}: Double Tap'))
                    self.assertEqual(acts['chord']['settings'], {'chord_button': legacy, 'delay_start': '200'})
                    self.assertEqual(self.ops(layout, acts['chord']), [('add_layer', st.COVER)])
                    self.assertEqual(acts['Full_Press']['settings'],
                                     {'hold_repeats': '1', 'repeat_rate': '250', 'interruptable': '0'})
                    self.assertEqual(self.ops(layout, acts['Full_Press']), [('remove_layer', st.COVER)])
                edge = self.acts(layout, name, own, 'edge')
                self.assertEqual(list(edge), ['release'])
                self.assertEqual(self.ops(layout, edge['release']), [('remove_layer', name)])
                other = next(s for s in STICKS.values() if s != own)
                self.assertNotIn('edge', layout.active(name)[other]['inputs'])

    def test_guards_carry_the_touch_recovery_on_both_sticks(self):
        stale = {('remove_layer', t) for t in GUARDS + [st.COVER] + ENTRY_POINTS}
        for b, layout in self.each():
            for name in GUARDS:
                for source, trio in TRIO.items():
                    touch = self.acts(layout, name, source, 'touch')
                    self.assertEqual(set(touch), {'Full_Press', 'chord', 'release'})
                    self.assertEqual(touch['chord']['settings'], {
                        'gyro_ratchet_button_mask': str(st.MENU_ANY), 'gyro_ratchet_button_requireany_or_all': '0',
                        'interruptable': '0'})
                    self.assertEqual(actions(touch['chord']), [EMPTY + ', , '])
                    # Guarded recovery: repeating and interruptible.
                    self.assertEqual(touch['Full_Press']['settings'], {'hold_repeats': '1'})
                    self.assertEqual(set(self.ops(layout, touch['Full_Press'])), stale)
                    # The thumb lift completes the pending hold first, then clears the trio.
                    self.assertEqual(self.ops(layout, touch['release']), [('add_layer', st.COVER)] + [
                        ('remove_layer', f'{trio}: {kind}') for kind in ('Entry Point', 'Tap Cover', 'Temporary Gyro')])

    def test_menu_tap_cover_silences_the_release(self):
        for b, layout in self.each():
            self.assertEqual(set(layout.active(st.COVER)), {'switch', 'joystick', 'right_joystick'})
            for button, _ in SIDES.values():
                acts = self.acts(layout, st.COVER, 'switch', button)
                self.assertEqual(actions(acts['Full_Press']), [EMPTY + ', , '])
                self.assertEqual(acts['Full_Press']['settings'], {'interruptable': '0'})
                release = self.ops(layout, acts['release'])
                self.assertEqual(release[0], ('remove_layer', st.COVER))
                # No Fn layer: it is never on the stack with the cover (cleanup rule 6, author 2026-10-02).
                self.assertEqual(set(release), {('remove_layer', t) for t in [st.COVER] + GUARDS + ENTRY_POINTS})
                self.assertFalse([x for x in actions(acts['release']) if 'key_press' in x])
            for source in STICKS.values():
                # Empty edges: no guard can be added on top of the cover.
                self.assertEqual(list(layout.active(st.COVER)[source]['inputs']), ['edge'])
                self.assertTrue(self.is_empty(self.acts(layout, st.COVER, source, 'edge')))
            self.assertTrue(audit_flow_inheritance.is_cover(st.COVER, audit_flow_inheritance.load_rules(), {}))
            for name in GUARDS:
                self.assertFalse(audit_flow_inheritance.is_cover(name, audit_flow_inheritance.load_rules(), {}))

    def test_transition_menu_releases(self):
        for b, layout in self.each():
            commit = [('remove_layer', st.CROSS), ('add_layer', 'Steering'), ('add_layer', 'Steering | LS: Entry Guard')]
            expected = {(st.CROSS, 'button_escape'): commit, (st.CROSS, 'button_menu'): [('remove_layer', st.CROSS)],
                        (st.CLEAR, 'button_escape'): [('remove_layer', st.CLEAR)],
                        (st.CLEAR, 'button_menu'): [('remove_layer', st.CLEAR)]}
            for (name, button), ops in expected.items():
                acts = self.acts(layout, name, 'switch', button)
                self.assertEqual(list(acts), ['release'], (name, button))
                self.assertEqual(self.ops(layout, acts['release']), ops)

    def test_every_transition_beeps_and_pulses_on_its_menu_release(self):
        # Author, 2026-10-02: every transition has a beep and a high haptic pulse, entering a stateful
        # layer or leaving one. No on-screen notification.
        stateful = {'Steering'}
        for b, layout in self.each():
            entering = 0
            for name in (st.CROSS, st.CLEAR):
                for button, _ in SIDES.values():
                    release = self.acts(layout, name, 'switch', button)['release']
                    self.assertEqual(release['settings'], {'haptic_intensity': '3'}, (name, button))
                    flags = {layout.resolve(m.group(1)): [m.group(2), m.group(3)] for a in actions(release)
                             if (m := re.search(r'_layer (\{\{.+?\}\}|\d+) (\d) (\d)', a))}
                    entered = [t for op, t in self.ops(layout, release) if op == 'add_layer' and t in stateful]
                    entering += bool(entered)
                    # One beep per release: on the stateful layer's add, or on the transition's own
                    # removal when the release only clears.
                    beeping = entered or [name]
                    for title, flag in flags.items():
                        self.assertEqual(flag, ['1' if title in beeping else '0', '0'], (name, button, title))
            self.assertEqual(entering, 1)   # one built gesture so far: Start + LS click into Steering

    def test_nothing_is_entered_from_a_transition(self):
        for b, layout in self.each():
            for name in (st.CROSS, st.CLEAR):
                for stack in (['Base'], ['Base', 'Gyro']):
                    routes, _ = check_stack(layout, name, stack)
                    self.assertEqual([(r['source'], r['input']) for r in routes], [], (name, stack))
                # Its own binds change layers only on the two menu releases and the touch releases.
                for source, group in layout.active(name).items():
                    for input_name, value in group.get('inputs', {}).items():
                        for kind, e in entries(value['activators']):
                            if self.ops(layout, e):
                                self.assertEqual(kind, 'release', (name, source, input_name))
                                self.assertIn(input_name, ('button_escape', 'button_menu', 'touch'))
                for source, trio in TRIO.items():
                    touch = self.acts(layout, name, source, 'touch')
                    self.assertEqual(list(touch), ['release'])
                    self.assertEqual(self.ops(layout, touch['release']), [
                        ('remove_layer', f'{trio}: {kind}') for kind in ('Entry Point', 'Tap Cover', 'Temporary Gyro')])

    def test_transitions_match_across_the_two_layouts(self):
        def shape(layout, name):
            return {source: (g['mode'], g.get('inputs', {})) for source, g in layout.active(name).items()}
        for name in (st.CROSS, st.CLEAR):
            self.assertEqual(shape(Layout(self.builders['default'].data), name),
                             shape(Layout(self.builders['alternative'].data), name))

    def test_base_and_steering_add_their_entry_points_with_a_repeating_press(self):
        for b, layout in self.each():
            for layer, steering in (('Base', False), ('Steering', True)):
                for side, (button, _) in SIDES.items():
                    acts = self.acts(layout, layer, 'switch', button)
                    # Clean entry: no Release, delay or chord on a menu button.
                    self.assertEqual(list(acts), ['Full_Press'], (layer, button))
                    self.assertEqual(acts['Full_Press'].get('settings'), {'hold_repeats': '1'})
                    self.assertEqual(self.ops(layout, acts['Full_Press']),
                                     [('add_layer', st.entry_point(side, steering))])

    def test_steering_drivers_keep_tab_and_escape(self):
        for b, layout in self.each():
            for owner in b.m.OWNERS:
                switches = layout.active(b.title(owner))['switch']['inputs']
                for button, key in (('button_escape', 'TAB'), ('button_menu', 'ESCAPE')):
                    self.assertEqual(switches[button]['activators'], {'Full_Press': {'bindings': {'binding': f'key_press {key}, , '}}})

    def test_steering_hold_exit_covers_w_and_s(self):
        for b, layout in self.each():
            north = self.acts(layout, 'Steering', 'joystick', 'dpad_north')
            south = self.acts(layout, 'Steering', 'joystick', 'dpad_south')
            self.assertEqual(json.loads(json.dumps(north).replace('key_press W', 'key_press S')), south)
            warning, leave = south['chord']
            self.assertEqual((warning['settings']['delay_start'], leave['settings']['delay_start']), ('1000', '2500'))
            self.assertIn(('remove_layer', 'Steering'), self.ops(layout, leave))

    def test_steering_can_sit_under_the_menu_windows(self):
        # The fix pipeline replaces what would show through: the hold-exit clock on left-stick up and down.
        for b, layout in self.each():
            for window in ('Menu Left: Double Tap', 'Menu Right: Double Tap'):
                for direction, key in (('dpad_north', 'W'), ('dpad_south', 'S')):
                    acts = self.acts(layout, window, 'joystick', direction)
                    self.assertEqual(list(bindings(acts)), [f'key_press {key}, , '], (window, direction))

    def test_no_steering_layer_uses_an_inverted_edge(self):
        for b, layout in self.each():
            groups = [(name, layout.active(name)['joystick']) for name in self.steering_layers(layout)
                      if 'joystick' in layout.active(name) and 'Menu' not in name]
            # R111 is about the layers that end on the stick's return to centre; they are among the ones checked.
            self.assertLessEqual({'Steering | LS Up: Modifier 1', 'Steering | LS Down: Modifier 0',
                                  'Steering | LS: Entry Guard'}, {name for name, _ in groups})
            for name, group in groups:
                self.assertEqual((group['settings']['edge_binding_radius'], group['settings']['edge_binding_invert']),
                                 ('4915', '0'), name)
            # Every edge that changes layers does it on the Release: the stick came back to centre.
            for name in self.steering_layers(layout):
                edge = layout.active(name).get('joystick', {}).get('inputs', {}).get('edge')
                for kind, e in entries(edge['activators']) if edge else ():
                    if self.ops(layout, e) and 'Menu' not in name:
                        self.assertEqual(kind, 'release', name)

    def test_ls_tap_cover_is_only_added_inside_modifier_0_and_1(self):
        # So it is always added with the stick out, and its edge Release can always remove it.
        for b, layout in self.each():
            adders = {name for name in layout.presets for g in layout.active(name).values()
                      for v in g.get('inputs', {}).values() for _, e in entries(v.get('activators', {}))
                      if ('add_layer', LS_COVER) in self.ops(layout, e)}
            self.assertEqual(adders, set(MODIFIERS.values()))

    def test_w_and_s_layers_add_the_modifier_with_a_repeating_bind(self):
        for b, layout in self.each():
            for owner in b.m.OWNERS:
                for direction, input_name in DIRECTIONS.items():
                    acts = self.acts(layout, b.title(owner), 'joystick', input_name)
                    self.assertEqual(list(acts), ['Full_Press'])
                    self.assertEqual(acts['Full_Press']['settings'],
                                     {'hold_repeats': '1', 'repeat_rate': '50', 'interruptable': '0'})
                    self.assertEqual(self.ops(layout, acts['Full_Press']), [('add_layer', MODIFIERS[direction])])
                # A driver press adds its layer alone.
                press = self.driver(b, layout, 'Steering', owner)['Full_Press']
                self.assertEqual(self.ops(layout, press), [('remove_layer', 'Steering | LS: Entry Guard'),
                                                           ('add_layer', b.title(owner))])

    def test_modifier_0_and_1_stick_recipe(self):
        for b, layout in self.each():
            drivers = st.lean.DRIVER_MASK[b.variant]
            for direction, name in MODIFIERS.items():
                opposite = DIRECTIONS['Down' if direction == 'Up' else 'Up']
                hold = self.acts(layout, name, 'joystick', DIRECTIONS[direction])
                self.assertEqual(hold['chord']['settings'], {
                    'gyro_ratchet_button_mask': str(drivers), 'gyro_ratchet_button_requireany_or_all': ANY,
                    'delay_start': '250', 'interruptable': '0'})
                self.assertEqual(self.ops(layout, hold['chord']), [('add_layer', LS_COVER)])
                self.assertEqual(hold['Full_Press']['settings'],
                                 {'hold_repeats': '1', 'repeat_rate': '300', 'interruptable': '0'})
                self.assertEqual(self.ops(layout, hold['Full_Press']), [('remove_layer', LS_COVER)])
                # The opposite direction only cleans up; it never adds the other modifier.
                away = self.acts(layout, name, 'joystick', opposite)
                self.assertEqual([self.ops(layout, e) for _, e in entries(away)], [[('remove_layer', name)]])
                for lateral, key in (('dpad_east', 'D'), ('dpad_west', 'A')):
                    e = self.acts(layout, name, 'joystick', lateral)['Full_Press']
                    self.assertEqual(list(reversed(actions(e)))[0], f'key_press {key}, , ')
                    self.assertEqual(self.ops(layout, e), [('add_layer', LS_COVER)])   # the modifier stays
                edge = self.acts(layout, name, 'joystick', 'edge')
                self.assertEqual(list(edge), ['release'])
                ops = self.ops(layout, edge['release'])
                self.assertEqual(ops[-1], ('add_layer', WINDOWS[direction]))   # the Always On window is added last
                # Only its own modifier: the other one is never on the stack with it (cleanup rule 6).
                self.assertEqual(set(ops[:-1]), {('remove_layer', t) for t in (LS_COVER, name)})

    def test_modifier_0_and_1_cleanup_is_guarded_by_two_all_chords(self):
        for b, layout in self.each():
            masks = [str(1 << 30 | 1 << bit) for bit in st.DRIVER_BITS[b.variant]]
            for name in MODIFIERS.values():
                mapped = [(source, n, v['activators']) for source, g in layout.active(name).items()
                          for n, v in g['inputs'].items()
                          if source in ('button_diamond', 'dpad', 'switch') or n == 'click']
                self.assertEqual(len(mapped), 12)   # face buttons, D-pad, Start, Select, both stick clicks
                for source, input_name, acts in mapped:
                    with self.subTest(layer=name, input=(source, input_name)):
                        self.assertEqual(list(acts), ['chord', 'Full_Press'])
                        self.assertEqual([c['settings']['gyro_ratchet_button_mask'] for c in acts['chord']], masks)
                        for chord in acts['chord']:
                            self.assertEqual(chord['settings']['gyro_ratchet_button_requireany_or_all'], ALL)
                            self.assertEqual(chord['settings']['interruptable'], '0')
                            # The key and the Tap Cover add ride in one array.
                            self.assertEqual(self.ops(layout, chord), [('add_layer', LS_COVER)])
                            self.assertEqual(len(actions(chord)), 2)
                        self.assertEqual(acts['chord'][0]['bindings'], acts['chord'][1]['bindings'])
                        cleanup = acts['Full_Press']
                        self.assertEqual(cleanup['settings'], {'hold_repeats': '1'})
                        self.assertIn(('remove_layer', name), self.ops(layout, cleanup))

    def test_steering_covers_end_on_the_edge_release(self):
        for b, layout in self.each():
            expected = {LS_COVER: [('remove_layer', t) for t in (MODIFIERS['Down'], MODIFIERS['Up'], LS_COVER)],
                        LS_REPEAT: [('remove_layer', LS_REPEAT)],
                        'Steering | LS: Entry Guard': [('remove_layer', 'Steering | LS: Entry Guard')]}
            for name, ops in expected.items():
                edge = self.acts(layout, name, 'joystick', 'edge')
                self.assertEqual(list(edge), ['release'], name)
                self.assertEqual(self.ops(layout, edge['release']), ops)
            for input_name in DIRECTIONS.values():
                release = self.acts(layout, LS_REPEAT, 'joystick', input_name)['release']
                self.assertEqual(self.ops(layout, release), [('remove_layer', LS_REPEAT)])   # adds no Tap Cover
            for input_name in DIRECTIONS.values():
                self.assertTrue(self.is_empty(self.acts(layout, LS_COVER, 'joystick', input_name)))

    def test_steering_windows_are_always_on_and_bind_everything_themselves(self):
        for b, layout in self.each():
            windows = always_on_layers(layout)
            # The build adds no Always On layer besides Double Tap windows, and every such window has one.
            self.assertEqual(set(windows), {title for title in layout.presets if title.endswith(': Double Tap')})
            self.assertLessEqual(set(WINDOWS.values()), set(windows))
            for direction, name in WINDOWS.items():
                remove = ('remove_layer', name)
                timeout = self.acts(layout, name, 'switch', 'always_on_action')['Full_Press']
                self.assertEqual(timeout['settings'], {'delay_start': '150', 'interruptable': '0'})
                self.assertEqual(self.ops(layout, timeout), [remove])   # removes only the window
                self.assertIn(f'mouse_wheel SCROLL_{direction.upper()}, , ', actions(timeout))
                own, opposite = DIRECTIONS[direction], DIRECTIONS['Down' if direction == 'Up' else 'Up']
                second = self.acts(layout, name, 'joystick', own)['Full_Press']
                self.assertEqual(self.ops(layout, second), [remove, ('add_layer', LS_REPEAT)])
                away = self.acts(layout, name, 'joystick', opposite)['Full_Press']
                self.assertEqual(actions(away), [f'controller_action remove_layer {{{{Base::{name}}}}} 0 0, , '])
                for lateral, key in (('dpad_east', 'D'), ('dpad_west', 'A')):
                    self.assertEqual(list(bindings(self.acts(layout, name, 'joystick', lateral))),
                                     [f'key_press {key}, , '])
                for owner in b.m.OWNERS:
                    acts = self.driver(b, layout, name, owner)
                    self.assertEqual(list(acts), ['Full_Press', 'release'])   # no chord: no Modifier 2 from a window
                    self.assertEqual(actions(acts['Full_Press']), [f'key_press {owner}, , '])
                    release = self.ops(layout, acts['release'])
                    self.assertEqual(release[0], remove)   # the window first, then the family
                    self.assertTrue(all(op == 'remove_layer' for op, _ in release))
                    self.assertIn(('remove_layer', b.title(owner)), release)
                    self.assertNotIn(('remove_layer', 'Steering'), release)
                for source, trio in TRIO.items():
                    touch = self.acts(layout, name, source, 'touch')
                    self.assertEqual(list(touch), ['release'])
                    self.assertEqual(self.ops(layout, touch['release']), [remove] + [
                        ('remove_layer', f'{trio}: {kind}') for kind in ('Entry Point', 'Tap Cover', 'Temporary Gyro')])

    def test_audits_are_clean(self):
        config = json.loads((ROOT / 'traced_stacks.json').read_text())
        for variant, data in self.data.items():
            with self.subTest(variant=variant):
                budget = audit_layout(data)
                self.assertFalse(budget['violations'] or budget['banned_activators'] or budget['inverted_edges'])
                self.assertTrue(audit(data, config)['ok'])
                with tempfile.NamedTemporaryFile('w', suffix='.json') as f:
                    json.dump(data, f); f.flush()
                    self.assertTrue(audit_flow_inheritance.run(f.name)['clean'])


if __name__ == '__main__':
    unittest.main()
