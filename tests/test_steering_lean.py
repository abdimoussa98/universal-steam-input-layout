"""Inspect actual lean bindings and execute their ordered command arrays.

These tests do not emulate Steam activator timing or output reference counting.
"""
import importlib.util
import json
from pathlib import Path
import re
import unittest

from audit_command_budget import audit_layout
from convert_runtime_ids import generate_lookup, ids_to_titles, titles_to_ids

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('steering_lean', ROOT / 'findings/2026-09-30-steering-lean/build_candidate.py')
lean = importlib.util.module_from_spec(spec); spec.loader.exec_module(lean)


class LeanTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.builders = {v: lean.Builder(v) for v in ('default', 'alternative')}
        for b in cls.builders.values():
            b.finish()

    def assert_chorded_delay(self, e, mask, delay):
        settings = e['settings']
        self.assertEqual(settings['gyro_ratchet_button_mask'], str(mask))
        self.assertEqual(settings['gyro_ratchet_button_requireany_or_all'], '0')
        self.assertEqual(settings['delay_start'], delay)
        self.assertNotIn('chord_button', settings)
        self.assertNotIn('long_press_time', settings)

    def binding(self, b, layer, source, name, kind='Full_Press'):
        value = b.sources(layer)[source]['inputs'][name]['activators'][kind]
        return value[0] if isinstance(value, list) else value

    def drive(self, b, layer, owner, kind='Full_Press'):
        side = 'right' if owner == 'W' else 'left'
        return self.binding(b, layer, 'switch' if b.variant == 'default' else side + '_trigger',
                            side + '_bumper' if b.variant == 'default' else 'edge', kind)

    def effective(self, b, stack, source, name):
        for layer in reversed(stack):
            binding = b.sources(layer).get(source, {}).get('inputs', {}).get(name)
            if binding is not None:
                return layer, binding
        raise AssertionError((stack, source, name))

    def run_array(self, b, stack, entry):
        outputs = []
        for command in reversed(b.m.commands(entry)):
            match = re.match(r'controller_action (add|remove)_layer {{Base::(.+?)}}', command)
            if match:
                verb, name = match.groups()
                # Valve: applying an already-active layer has no effect and
                # does not move it to the top of the stack.
                if verb == 'add' and name not in stack:
                    stack.append(name)
                elif verb == 'remove' and name in stack:
                    stack.remove(name)
            elif command != b.m.EMPTY:
                outputs.append(command)
        return outputs

    def test_budget_reference_roundtrip_and_layer_ids(self):
        for b in self.builders.values():
            self.assertFalse(audit_layout(b.data)['violations'])
            self.assertEqual(len(b.cm['actions']), 1)
            lookup = generate_lookup(b.data)
            numeric, _ = titles_to_ids(json.dumps(b.data), lookup)
            self.assertNotIn('{{', numeric)
            restored, _ = ids_to_titles(numeric, lookup)
            self.assertEqual(json.loads(restored), b.data)
            keys = list(b.cm['action_layers'])
            self.assertEqual(keys, sorted(keys, key=lambda x: int(x.split('_')[1])))
            self.assertEqual(len(b.new), 16)
            self.assertEqual(len(set(b.new)), 16)

    def test_naming_and_two_required_modifier_orders(self):
        for b in self.builders.values():
            self.assertTrue(all(n == 'Steering' or n.startswith('Steering | ') for n in b.new))
            left, right = ('L1', 'R1') if b.variant == 'default' else ('L2', 'R2')
            self.assertEqual(b.banks[2:], [f'Steering | {right}!{left}: Modifier 2',
                                         f'Steering | {left}!{right}: Modifier 2'])
            self.assertFalse(any('Automatic Fn' in n for n in b.new))
            self.assertEqual(len(b.menu_helpers), 4)
            self.assertNotEqual(self.builders['default'].title('W'), self.builders['alternative'].title('W'))

    def test_no_new_ao_and_existing_ao_sources_unchanged(self):
        for b in self.builders.values():
            for n in b.new:
                self.assertFalse(any('always_on_action' in g.get('inputs', {}) for g in b.sources(n).values()), n)
            fresh = lean.Builder(b.variant)
            for n in fresh.by_title:
                for src, g in fresh.sources(n).items():
                    if 'always_on_action' in g.get('inputs', {}):
                        self.assertEqual(b.sources(n)[src], g)

    def test_dominant_two_entries_inherit_through_every_helper(self):
        for b in self.builders.values():
            for owner in b.m.OWNERS:
                side = 'right' if owner == 'W' else 'left'
                source = 'switch' if b.variant == 'default' else side + '_trigger'
                name = side + '_bumper' if b.variant == 'default' else 'edge'
                for helper in b.gestures + b.banks:
                    if helper in b.banks[2:] and helper != b.title('Mod2', owner): continue
                    if helper in b.mod2_covers and helper != b.title('Mod2 Cover', owner): continue
                    layer, binding = self.effective(b, [b.title(), b.title(owner), helper], source, name)
                    expected = b.title(owner)
                    self.assertEqual(layer, expected, (helper, source, name))
                    self.assertEqual(set(binding['activators']), {'Full_Press', 'release'})
                    self.assertEqual(binding['activators']['Full_Press']['bindings']['binding'], b.m.key(owner))

    def test_owner_release_clears_full_registry_and_preserves_membership(self):
        for b in self.builders.values():
            for owner in b.m.OWNERS:
                stack = ['Gyro', b.title()] + b.branch[:]
                output = self.run_array(b, stack, self.drive(b, b.title(owner), owner, 'release'))
                self.assertEqual(stack, ['Gyro', b.title()])
                self.assertFalse(output)

    def test_context_boundaries_cancel_every_history_and_select_correct_mod2(self):
        for b in self.builders.values():
            for owner in b.m.OWNERS:
                stack = [b.title(), b.title(owner)] + b.gestures + b.banks
                self.run_array(b, stack, b.m.entry(b.m.seq(*b.context_enter(owner))))
                self.assertEqual(stack, [b.title(), b.title(owner), b.title('Normal', 'Consumed'), b.title('Mod2', owner)])
                self.run_array(b, stack, b.m.entry(b.m.seq(*b.context_leave())))
                self.assertEqual(stack, [b.title(), b.title(owner), b.title('Normal', 'Consumed')])

    def test_modifier_banks_own_center_and_reversal_consumption(self):
        for b in self.builders.values():
            self.assertEqual(b.stroke, [])
            for direction, input_name in b.m.DIRECTIONS.items():
                n = b.title('Mod ' + ('1' if direction == 'Up' else '0'))
                g = b.sources(n)['joystick']
                self.assertEqual(g['settings']['edge_binding_invert'], '1')
                self.assertNotIn('release', g['inputs'][input_name]['activators'])
                activators = g['inputs'][input_name]['activators']
                self.assertEqual(set(activators), {'chord', 'Full_Press'})
                hold = activators['chord']
                self.assert_chorded_delay(hold, lean.LS_DEFLECT_MASK, '250')
                self.assertEqual(b.m.commands(hold), [b.m.op('add', b.title('Normal', 'Consumed'))])
                for name, binding in g['inputs'].items():
                    for _, e in b.m.entries(binding):
                        if any(b.m.op('add', w) in b.m.commands(e) for w in b.windows):
                            self.assertEqual(name, 'edge')
                for other in ('dpad_north', 'dpad_south', 'dpad_east', 'dpad_west'):
                    if other == input_name: continue
                    stack = [b.title(), b.title('W'), n]
                    outputs = self.run_array(b, stack, self.binding(b, n, 'joystick', other))
                    self.assertNotIn(n, stack)
                    self.assertEqual(stack[-1], b.title('Normal', 'Consumed'))
                    self.assertFalse(any('mouse_wheel' in c for c in outputs))

    def test_ordinary_single_expiry_and_different_direction_flush_once(self):
        for b in self.builders.values():
            self.assertEqual(len(b.windows), 2)
            for direction in b.m.DIRECTIONS:
                n = b.title('Normal', direction, 'Double Window')
                clock = self.binding(b, n, 'joystick', 'edge', 'chord')
                self.assert_chorded_delay(clock, lean.DRIVER_MASK[b.variant], '150')
                self.assertEqual(b.sources(n)['joystick']['settings']['edge_binding_radius'], '32767')
                stack = [b.title(), b.title('W'), n]
                self.assertEqual(self.run_array(b, stack, clock), [b.m.wheel(direction)])
                self.assertNotIn(n, stack)
                other = 'Down' if direction == 'Up' else 'Up'
                stack.append(n)
                emitted = self.run_array(b, stack, self.binding(b, n, 'joystick', b.m.DIRECTIONS[other]))
                self.assertEqual(emitted, [b.m.wheel(direction)])
                self.assertEqual(stack[-1], b.title('Mod ' + ('1' if other == 'Up' else '0')))
                self.assertNotIn(n, stack)
                # Sideways flushes the single at once and consumes the stick (author, D2).
                for lateral, letter in (('dpad_east', 'D'), ('dpad_west', 'A')):
                    stack = [b.title(), b.title('W'), n]
                    emitted = self.run_array(b, stack, self.binding(b, n, 'joystick', lateral))
                    self.assertEqual(emitted, [b.m.wheel(direction), b.m.key(letter)])
                    self.assertEqual(stack, [b.title(), b.title('W'), b.title('Normal', 'Consumed')])

    def test_one_repeat_cover_delays_ticks_and_consumes_each_exit(self):
        for b in self.builders.values():
            repeat = b.title('Repeat')
            self.assertEqual(b.repeats, [repeat])
            for direction, input_name in b.m.DIRECTIONS.items():
                win = b.title('Normal', direction, 'Double Window')
                stack = [b.title(), b.title('W'), win]
                self.assertFalse(self.run_array(b, stack, self.binding(b, win, 'joystick', input_name)))
                self.assertEqual(stack, [b.title(), b.title('W'), repeat])
                output = self.binding(b, repeat, 'joystick', input_name)
                self.assertEqual(output['bindings']['binding'], b.m.wheel(direction))
                self.assertEqual(output['settings']['delay_start'], '5')
                self.assertEqual(output['settings']['hold_repeats'], '1')
                emitted = self.run_array(b, stack, self.binding(b, repeat, 'joystick', input_name, 'release'))
                self.assertEqual(emitted, [])
                self.assertEqual(stack[-1], b.title('Normal', 'Consumed'))
                self.assertNotIn(repeat, stack)
            self.assertNotIn('mouse_wheel', json.dumps(b.sources(repeat)['joystick']['inputs']['edge']))
            for lateral in ('dpad_east', 'dpad_west'):
                layer, _ = self.effective(b, [b.title(), b.title('W'), repeat], 'joystick', lateral)
                self.assertEqual(layer, b.title('W'))

    def test_mod2_is_direct_repeat_without_gesture_layers(self):
        for b in self.builders.values():
            self.assertFalse(any('Modifier 2 | LS' in n for n in b.new))
            for owner in b.m.OWNERS:
                layer = b.title('Mod2', owner)
                for direction, input_name in b.m.DIRECTIONS.items():
                    binding = b.sources(layer)['joystick']['inputs'][input_name]['activators']
                    self.assertEqual(set(binding), {'Full_Press'})
                    e = binding['Full_Press']
                    self.assertEqual(e['bindings']['binding'], b.m.wheel(direction))
                    self.assertEqual(e['settings']['hold_repeats'], '1')
                    self.assertNotIn('delay_start', e['settings'])
                for kind, e in b.m.entries(b.sources(layer)['button_diamond']['inputs']['button_a']):
                    if kind == 'chord':
                        self.assertEqual([c for c in b.m.commands(e) if 'add_layer' in c],
                                         [b.m.op('add', b.title('Mod2 Cover', owner))])
            for win in b.windows:
                # Mapped buttons inherit plain output; the clock resolves the single.
                self.assertEqual(set(b.sources(win)), {'joystick', 'right_joystick'})
                self.assertNotIn('click', b.sources(win)['right_joystick']['inputs'])
                layer, _ = self.effective(b, ['Base', b.title(), b.title('W'), win], 'button_diamond', 'button_a')
                self.assertNotIn(layer, b.new)

    def test_each_mod2_uses_its_source_order_payloads(self):
        for b in self.builders.values():
            for owner in b.m.OWNERS:
                for src in ('button_diamond', 'dpad', 'switch'):
                    for name, binding in b.sources(b.title('Mod2', owner))[src]['inputs'].items():
                        if name in ('left_bumper', 'right_bumper'): continue
                        expected = b.m.commands(b.m.output_only(b.mod2_maps[owner][src]['inputs'][name])['activators']['Full_Press'])
                        actual = [c for _, e in b.m.entries(binding) for c in b.m.commands(e)
                                  if not c.startswith('controller_action remove_layer') and not c.startswith('controller_action add_layer')]
                        self.assertEqual(actual, expected)

    def test_fn_clicks_not_retargeted_and_menu_helpers_retire_on_commit(self):
        for b in self.builders.values():
            for side in ('Left', 'Right'):
                protected, cover = b.protected_names(side)
                stack = ['Base', f'Menu {side}: Entry Point', protected, cover]
                for depth in (2, 3, 4):
                    _, click = self.effective(b, stack[:depth], 'right_joystick', 'click')
                    self.assertIn(b.m.op('add', f'Menu {side}: Fn Layer'),
                                  b.m.commands(click['activators']['chord']))
                owner = 'button_menu' if side == 'Left' else 'button_escape'
                self.assertNotIn('key_press', json.dumps(self.binding(b, cover, 'switch', owner, 'release')))
                for target in (protected, cover):
                    for src, g in b.sources(target).items():
                        for name, binding in g['inputs'].items():
                            for _, e in b.m.entries(binding):
                                for c in b.m.commands(e):
                                    if 'add_layer' in c and 'Fn Layer' in c:
                                        self.assertEqual(name, 'click')
            stack = ['Gyro'] + b.menu_helpers + ['Transition Set 1']
            self.run_array(b, stack, self.binding(b, 'Transition Set 1', 'switch', 'button_escape', 'release'))
            self.assertEqual(stack, ['Gyro', b.title(), b.title('Entry Guard')])
            for source in ('joystick', 'right_joystick'):
                for n in ('edge', 'click'):
                    self.assertEqual(b.sources('Transition Set 1')[source]['inputs'][n], b.m.full())
                release = self.binding(b, 'Transition Set 1', source, 'touch', 'release')
                self.assertEqual(list(reversed(b.m.commands(release))), b.stick_cleanup(source))

    def test_held_opposite_can_take_over_without_rearm(self):
        for b in self.builders.values():
            self.assertFalse(any('Rearm' in n for n in b.new))
            for owner in b.m.OWNERS:
                other = 'S' if owner == 'W' else 'W'
                stack = [b.title(), b.title(owner), b.title('Normal', 'Consumed'), b.title('Mod2', owner)]
                self.run_array(b, stack, self.drive(b, b.title(owner), owner, 'release'))
                self.assertEqual(stack, [b.title()])
                acquire = self.drive(b, b.title(), other)
                self.assertEqual(acquire['settings']['hold_repeats'], '1')
                self.run_array(b, stack, acquire)
                self.assertEqual(stack, [b.title(), b.title(other), b.title('Normal', 'Consumed')])
                self.assertNotIn(b.title(owner), stack)
                chord = self.drive(b, b.title(), other, 'chord')
                self.assertEqual(chord['bindings']['binding'], b.m.op('remove', b.title('Entry Guard')))
                self.assertNotIn(b.m.op('add', b.title(other)), b.m.commands(chord))
                self.assertEqual(chord['settings']['gyro_ratchet_button_requireany_or_all'], '0')

    def test_tap_cover_blocks_directions_and_clears_on_center(self):
        # User design: hold past 250 ms adds the cover on top of the bank;
        # up/down then do nothing; center removes Mod 0, Mod 1, then the cover.
        for b in self.builders.values():
            cover = b.title('Normal', 'Consumed')
            for direction, input_name in b.m.DIRECTIONS.items():
                bank = b.title('Mod ' + ('1' if direction == 'Up' else '0'))
                stack = [b.title(), b.title('W')]
                self.run_array(b, stack, self.binding(b, b.title('W'), 'joystick', input_name))
                self.assertEqual(stack[-1], bank)
                self.run_array(b, stack, self.binding(b, bank, 'joystick', input_name, 'chord'))
                self.assertEqual(stack[-2:], [bank, cover])
                for name in b.m.DIRECTIONS.values():
                    layer, binding = self.effective(b, stack, 'joystick', name)
                    self.assertEqual(layer, cover)
                    self.assertEqual(b.m.commands(binding['activators']['Full_Press']), [b.m.EMPTY])
                layer, edge = self.effective(b, stack, 'joystick', 'edge')
                self.assertEqual(layer, cover)
                execution = list(reversed(b.m.commands(edge['activators']['Full_Press'])))
                self.assertEqual(execution, [b.m.op('remove', b.title('Mod 0')), b.m.op('remove', b.title('Mod 1')),
                                             b.m.op('remove', cover)])
                self.assertFalse(self.run_array(b, stack, edge['activators']['Full_Press']))
                self.assertEqual(stack, [b.title(), b.title('W')])

    def test_no_binding_adds_a_bank_while_leaving_an_active_cover_below_it(self):
        # A bank added after the cover would sit above it and take center.
        for b in self.builders.values():
            cover = b.title('Normal', 'Consumed')
            for layer in b.new:
                for source, g in b.sources(layer).items():
                    for name, binding in g.get('inputs', {}).items():
                        for _, e in b.m.entries(binding):
                            execution = list(reversed(b.m.commands(e)))
                            for bank in b.banks[:2]:
                                if b.m.op('add', bank) not in execution:
                                    continue
                                with self.subTest(variant=b.variant, layer=layer, input=name):
                                    self.assertNotEqual(layer, cover)
                                    i = execution.index(b.m.op('add', bank))
                                    later_cover_add = b.m.op('add', cover) in execution[i:]
                                    # Safe if the cover overrides this input (the binding can't run
                                    # while the cover is active), or if it removes the cover first.
                                    unreachable = name in b.sources(cover)['joystick']['inputs'] and source == 'joystick'
                                    if later_cover_add and not unreachable:
                                        self.assertIn(b.m.op('remove', cover), execution[:i])

    def test_warning_guard_and_full_exit_preserve_feedback(self):
        for b in self.builders.values():
            binding = b.sources(b.title())['joystick']['inputs']['dpad_north']['activators']
            self.assertEqual(binding['Full_Press']['bindings']['binding'], b.m.key('W'))
            warn, exit_ = binding['chord']
            self.assert_chorded_delay(warn, lean.LS_DEFLECT_MASK, '1000')
            self.assert_chorded_delay(exit_, lean.LS_DEFLECT_MASK, '2500')
            self.assertEqual((warn['settings']['hold_repeats'], warn['settings']['repeat_rate']), ('1', '250'))
            self.assertEqual(warn['bindings']['binding'], b.m.EMPTY)
            self.assertNotIn('hold_repeats', exit_['settings'])
            stack = ['Gyro'] + b.family[:]
            self.run_array(b, stack, exit_)
            self.assertEqual(stack, ['Gyro'])
            # Entry Guard overrides the whole input, so carried W has no clock.
            guard = b.sources(b.title('Entry Guard'))['joystick']['inputs']['dpad_north']['activators']
            self.assertEqual(set(guard), {'Full_Press'})

    def test_no_banned_activators_or_new_orphan_groups(self):
        for b in self.builders.values():
            touched = set(b.new) | {name for name, _ in b.changed}
            for name in touched:
                for source, g in b.sources(name).items():
                    for input_name, binding in g.get('inputs', {}).items():
                        with self.subTest(variant=b.variant, layer=name, source=source, input=input_name):
                            self.assertFalse(set(binding['activators']) & set(lean.BANNED_ACTIVATORS))
            referenced = {g for p in b.cm['preset'] for g in p['group_source_bindings']}
            self.assertFalse(b.replaced_groups & {g['id'] for g in b.cm['group']} - referenced)

    def test_all_new_layers_have_side_local_touch_release_cleanup(self):
        # Covers inherit touch from their owner (DoD §5); see the cover tests.
        for b in self.builders.values():
            for name in b.new:
                if name in b.covers():
                    continue
                for source in ('joystick', 'right_joystick'):
                    with self.subTest(variant=b.variant, layer=name, source=source):
                        e = self.binding(b, name, source, 'touch', 'release')
                        execution = list(reversed(b.m.commands(e)))
                        removes = [c for c in execution if 'remove_layer' in c]
                        self.assertEqual(removes, b.stick_cleanup(source))
                        self.assertFalse(any('key_press' in c or 'mouse_wheel' in c for c in execution))
                        self.assertFalse(any('Fn Layer' in c for c in execution))

    def test_delayed_cover_completion_precedes_touch_removals(self):
        for b in self.builders.values():
            targets = {n: b.title('Normal', 'Consumed') for n in b.banks[:2]}
            targets.update({b.title('Mod2', o): b.title('Mod2 Cover', o) for o in b.m.OWNERS})
            targets.update({b.protected_names(side)[0]: b.protected_names(side)[1]
                            for side in ('Left', 'Right')})
            for name in b.new:
                if name in b.covers():
                    continue
                for source in ('joystick', 'right_joystick'):
                    execution = list(reversed(b.m.commands(self.binding(b, name, source, 'touch', 'release'))))
                    expected = ([b.m.op('add', targets[name])] if name in targets else []) + b.stick_cleanup(source)
                    self.assertEqual(execution, expected, (name, source))

    def test_touch_recovery_preserves_driver_and_menu_guards(self):
        for b in self.builders.values():
            for owner in b.m.OWNERS:
                expected = b.owner_recovery(owner)['activators']
                for name in (b.title(owner), b.title('Mod2', owner)):
                    for source in ('joystick', 'right_joystick'):
                        actual = b.sources(name)[source]['inputs']['touch']['activators']
                        for kind in ('Full_Press', 'chord'):
                            self.assertEqual(actual[kind], expected[kind])
            for side in ('Left', 'Right'):
                stack = ['Base', f'Menu {side}: Entry Point', *b.protected_names(side)]
                for depth in (3, 4):
                    for source in ('joystick', 'right_joystick'):
                        _, touch = self.effective(b, stack[:depth], source, 'touch')
                        chord = touch['activators']['chord']
                        self.assertEqual(chord['settings']['chord_button'], '15' if side == 'Left' else '14')
                        self.assertEqual(chord['bindings']['binding'], b.m.EMPTY)

    def test_mod2_uncovered_release_and_cover_delay_match_existing_pattern(self):
        for b in self.builders.values():
            for owner in b.m.OWNERS:
                other = 'S' if owner == 'W' else 'W'
                parent = b.title('Mod2', owner); cover = b.title('Mod2 Cover', owner)
                delayed = self.drive(b, parent, other, 'chord')
                reset = self.drive(b, parent, other)
                self.assertEqual(delayed['settings']['delay_start'], '200')
                self.assertEqual(delayed['bindings']['binding'], b.m.op('add', cover))
                self.assertNotEqual(delayed['settings'].get('interruptable'), '0')
                self.assertEqual(reset['settings']['repeat_rate'], '250')
                self.assertEqual(reset['settings']['interruptable'], '0')
                self.assertEqual(reset['bindings']['binding'], b.m.op('remove', cover))
                self.assertEqual(set(b.base_exit_targets), set(b.by_title) - {'Base'})
                for control in (other,):
                    stack = ['Base'] + b.base_exit_targets[:]
                    self.run_array(b, stack, self.drive(b, parent, control, 'release'))
                    self.assertEqual(stack, ['Base'])

    def test_reused_covers_preserve_movement_and_distinct_releases(self):
        for b in self.builders.values():
            self.assertEqual(len(b.mod2_covers), 2)
            self.assertTrue(set(b.mod2_covers).isdisjoint(b.new))
            for owner in b.m.OWNERS:
                other = 'S' if owner == 'W' else 'W'
                parent = b.title('Mod2', owner); cover = b.title('Mod2 Cover', owner)
                stack = ['Gyro', b.title(), b.title(owner), b.title('Normal', 'Consumed'), parent]
                self.run_array(b, stack, self.drive(b, parent, other, 'chord'))
                self.assertEqual(stack[-1], cover)
                side = 'right' if owner == 'W' else 'left'
                source = 'switch' if b.variant == 'default' else side + '_trigger'
                name = side + '_bumper' if b.variant == 'default' else 'edge'
                resolved, binding = self.effective(b, stack, source, name)
                self.assertEqual(resolved, b.title(owner))
                self.assertEqual(binding['activators']['Full_Press']['bindings']['binding'], b.m.key(owner))
                self.run_array(b, stack, self.drive(b, cover, other, 'release'))
                self.assertEqual(stack, ['Gyro', b.title(), b.title(owner), b.title('Normal', 'Consumed')])
                stack = ['Gyro', b.title(), b.title(owner), b.title('Normal', 'Consumed'), parent, cover]
                self.run_array(b, stack, binding['activators']['release'])
                self.assertEqual(stack, ['Gyro', b.title()])
                self.run_array(b, stack, self.drive(b, b.title(), other))
                self.assertEqual(stack[-2:], [b.title(other), b.title('Normal', 'Consumed')])
                for src, n in [('button_diamond', 'button_a'), ('joystick', 'dpad_north')]:
                    resolved, _ = self.effective(b, [b.title(), b.title(owner), b.title('Normal', 'Consumed'), parent, cover], src, n)
                    self.assertEqual(resolved, parent)

    def test_reused_cover_base_behavior_is_removal_only_and_side_local(self):
        for b in self.builders.values():
            fresh = lean.Builder(b.variant)
            for owner in b.m.OWNERS:
                cover = b.title('Mod2 Cover', owner)
                for src, group in fresh.sources(cover).items():
                    current = b.sources(cover)[src]
                    self.assertEqual(set(current['inputs']), set(group['inputs']))
                    for name, original in group['inputs'].items():
                        actual = current['inputs'][name]
                        self.assertEqual(set(actual['activators']), set(original['activators']))
                        for kind, e in b.m.entries(actual):
                            original_e = original['activators'][kind]
                            old = list(reversed(b.m.commands(original_e)))
                            now = list(reversed(b.m.commands(e)))
                            self.assertEqual(now[:len(old)], old)
                            changed = (name == 'touch' and kind == 'Full_Press') or (name != 'touch' and kind == 'release')
                            self.assertEqual(now[len(old):], [b.m.op('remove', b.title('Mod2', owner))] if changed else [])
                            self.assertTrue(all(c.startswith('controller_action remove_layer') for c in now[len(old):]))
                            self.assertNotIn(b.m.op('remove', b.title(owner)), now)
                            self.assertNotIn(b.m.op('remove', b.title('Normal', 'Consumed')), now)
                            if name == 'touch' and kind == 'release': self.assertEqual(now, old)
                            self.assertEqual(e.get('settings', {}), original_e.get('settings', {}))

    def test_mod2_actions_apply_matching_cover_before_output(self):
        for b in self.builders.values():
            for owner in b.m.OWNERS:
                parent = b.title('Mod2', owner); cover = b.title('Mod2 Cover', owner)
                e = self.binding(b, parent, 'button_diamond', 'button_a', 'chord')
                self.assertEqual(list(reversed(b.m.commands(e)))[0], b.m.op('add', cover))
                stack = [b.title(), b.title(owner), parent]
                outputs = self.run_array(b, stack, e)
                self.assertIn(cover, stack)
                self.assertTrue(any(c.startswith('key_press ') for c in outputs))

    def test_effective_owner_release_cleans_real_nested_stacks(self):
        """Resolve the topmost whole input before executing its release."""
        for b in self.builders.values():
            t = b.title
            for owner in b.m.OWNERS:
                side = 'right' if owner == 'W' else 'left'
                source = 'switch' if b.variant == 'default' else side + '_trigger'
                control = side + '_bumper' if b.variant == 'default' else 'edge'
                stacks = [[bank, t('Normal', 'Consumed')] for bank in b.banks[:2]]
                stacks += [[window] for window in b.windows] + [[t('Repeat')]]
                stacks += [[t('Normal', 'Consumed'), t('Mod2', owner)],
                           [t('Normal', 'Consumed'), t('Mod2', owner), t('Mod2 Cover', owner)]]
                for overlays in stacks:
                    with self.subTest(variant=b.variant, owner=owner, overlays=overlays):
                        stack = ['Base', 'Gyro', t(), t(owner)] + overlays
                        _, effective = self.effective(b, stack, source, control)
                        self.assertFalse(self.run_array(b, stack, effective['activators']['release']))
                        self.assertEqual(stack, ['Base', 'Gyro', t()])

    def test_every_delayed_layer_apply_has_scoped_reset_hidden_by_target(self):
        for b in self.builders.values():
            checked = 0
            for layer in b.new:
                for source, group in b.sources(layer).items():
                    for name, binding in group.get('inputs', {}).items():
                        entries = list(b.m.entries(binding))
                        for _, delayed in entries:
                            delay = int(delayed.get('settings', {}).get('delay_start', 0))
                            targets = [re.match(r'controller_action add_layer {{Base::(.+?)}}', c)
                                       for c in b.m.commands(delayed)]
                            targets = [match.group(1) for match in targets if match]
                            if not delay or not targets:
                                continue
                            self.assertEqual(len(targets), 1, (layer, name))
                            target = targets[0]
                            resets = [e for kind, e in entries if kind == 'Full_Press'
                                      and b.m.commands(e) == [b.m.op('remove', target)]
                                      and e.get('settings', {}).get('hold_repeats') == '1']
                            self.assertEqual(len(resets), 1, (layer, name, target))
                            reset = resets[0]
                            self.assertEqual(reset['settings']['interruptable'], '0')
                            self.assertNotIn('delay_start', reset['settings'])
                            self.assertEqual(int(reset['settings']['repeat_rate']),
                                             {5: 50, 200: 250, 250: 300, 300: 350}[delay])
                            stack = ['Base', layer]
                            self.run_array(b, stack, reset)
                            self.run_array(b, stack, delayed)
                            resolved, active = self.effective(b, stack, source, name)
                            self.assertEqual(resolved, target)
                            self.assertFalse(any(e == reset for _, e in b.m.entries(active)))
                            checked += 1
            self.assertEqual(checked, 10)  # Four owner selectors, two menus, two Mod 2, two Mod 0/1 consumes.

    def test_protected_menu_release_and_recovery_retire_owned_helpers_only(self):
        for b in self.builders.values():
            for side, button, key in [('Left', 'button_menu', 'ESCAPE'),
                                      ('Right', 'button_escape', 'TAB')]:
                protected, cover = b.protected_names(side)
                normal = f'Menu {side}: Entry Point'
                for top in (protected, cover):
                    stack = ['Base', 'Gyro', normal, protected]
                    if top == cover:
                        stack.append(cover)
                    _, effective = self.effective(b, stack, 'switch', button)
                    emitted = self.run_array(b, stack, effective['activators']['release'])
                    self.assertEqual(emitted, [b.m.key(key)] if top == protected else [])
                    self.assertEqual(stack, ['Base', 'Gyro'])
                    for source in ('joystick', 'right_joystick'):
                        # Execute the recovery branch only; native chord suppression
                        # while the menu is held is checked separately/on device.
                        stack = ['Base', 'Gyro', normal, protected, cover]
                        _, touch = self.effective(b, stack[:stack.index(top) + 1], source, 'touch')
                        self.assertFalse(self.run_array(b, stack, touch['activators']['Full_Press']))
                        self.assertEqual(stack, ['Base', 'Gyro'])

    def steering_stacks(self, b):
        """Canonical steering stacks. The derived stack search in
        audit_inheritance.py cannot reach steering depth, so declare them."""
        t = b.title; stacks = []
        for base in (['Base'], ['Base', 'Gyro']):
            root = base + [t()]
            stacks += [root, root + [t('Entry Guard')]]
            for o in b.m.OWNERS:
                owner = root + [t(o)]
                stacks += [owner, owner + [t('Normal', 'Consumed')], owner + [t('Repeat')]]
                stacks += [owner + [w] for w in b.windows]
                for bank in b.banks[:2]:
                    stacks += [owner + [bank], owner + [bank, t('Normal', 'Consumed')]]
                stacks += [owner + [t('Normal', 'Consumed'), t('Mod2', o)],
                           owner + [t('Normal', 'Consumed'), t('Mod2', o), t('Mod2 Cover', o)]]
        return stacks

    def test_covers_define_only_their_own_controls(self):
        for b in self.builders.values():
            t = b.title
            expected = {t('Normal', 'Consumed'): {'joystick': {'dpad_north', 'dpad_south', 'dpad_east',
                                                               'dpad_west', 'edge'}},
                        t('Repeat'): {'joystick': {'dpad_north', 'dpad_south', 'edge'}}}
            for side, owner in (('Left', 'button_menu'), ('Right', 'button_escape')):
                expected[b.protected_names(side)[1]] = {'switch': {owner}}
            self.assertEqual(set(expected), set(b.covers()))
            for cover, sources in expected.items():
                with self.subTest(variant=b.variant, cover=cover):
                    actual = {src: set(g['inputs']) for src, g in b.sources(cover).items()}
                    self.assertEqual(actual, sources)

    def test_covers_inherit_owner_touch_recovery_and_release(self):
        for b in self.builders.values():
            stacks = [s for s in self.steering_stacks(b) if s[-1] in b.covers()]
            stacks += [['Base', f'Menu {side}: Entry Point', *b.protected_names(side)]
                       for side in ('Left', 'Right')]
            for stack in stacks:
                for source in ('joystick', 'right_joystick'):
                    with self.subTest(variant=b.variant, stack=stack[-2:], source=source):
                        layer, touch = self.effective(b, stack, source, 'touch')
                        self.assertNotIn(layer, b.covers())
                        self.assertEqual(set(touch['activators']), {'Full_Press', 'chord', 'release'})
                        release = list(reversed(b.m.commands(touch['activators']['release'])))
                        self.assertEqual([c for c in release if 'remove_layer' in c], b.stick_cleanup(source))

    def test_steering_never_reaches_an_always_on_window(self):
        for b in self.builders.values():
            t = b.title
            always_on = {n for n in b.by_title
                         if any('always_on_action' in g.get('inputs', {}) for g in b.sources(n).values())}
            # Layers with any binding that adds an Always On window.
            feeders = {n for n in b.by_title for g in b.sources(n).values()
                       if any(f'add_layer {{{{Base::{w}}}}}' in json.dumps(g) for w in always_on)}
            self.assertIn('RTP: Entry Point', feeders)
            self.assertEqual(b.sources(t())['right_trackpad']['inputs'], {'touch': b.m.full()})
            for stack in self.steering_stacks(b):
                inputs = {(src, n) for layer in stack for src, g in b.sources(layer).items()
                          for n in g.get('inputs', {})}
                for src, n in sorted(inputs):
                    _, binding = self.effective(b, stack, src, n)
                    for kind, e in b.m.entries(binding):
                        after = stack[:]
                        self.run_array(b, after, e)
                        if t() not in after:
                            continue  # Steering's own exit; the window then sits on Base/Gyro.
                        with self.subTest(variant=b.variant, stack=stack[2:], input=(src, n, kind)):
                            self.assertFalse(set(after) - set(stack) & (always_on | feeders))

    def test_pending_steering_timers_clear_rs_edge(self):
        for b in self.builders.values():
            for name in b.windows + b.banks:
                self.assertEqual(b.sources(name)['right_joystick']['inputs']['edge'], b.m.full(), name)
            for stack in self.steering_stacks(b):
                layer, _ = self.effective(b, stack, 'right_joystick', 'edge')
                if any(n in stack for n in b.windows + b.banks):
                    self.assertIn(layer, b.windows + b.banks, stack)
                else:
                    # Plain driving keeps Base's turn-assist ramp.
                    self.assertNotIn(layer, b.new, stack)


if __name__ == '__main__':
    unittest.main()
