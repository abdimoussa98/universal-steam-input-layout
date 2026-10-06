"""The Gamepad layer and the third transition, checked on the generated candidates.

Builds both variants with the 2026-10-03 Gamepad builder and runs the fix pipeline, as the
install does (findings/2026-10-03-gamepad/README.md). These verify saved configuration
contracts, not Steam's runtime scheduling.
"""
import importlib.util
import json
from pathlib import Path
import re
import unittest

from tools.audit_command_budget import audit_layout
from steam_layout import changes
from steam_layout.fixes import apply_all
from steam_layout.inheritance import check_stack
from steam_layout.model import EMPTY, Layout, actions, entries, map_title

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    'gamepad', ROOT / 'findings/2026-10-03-gamepad/build_candidate.py')
gp = importlib.util.module_from_spec(spec); spec.loader.exec_module(gp)
cg, st = gp.cg, gp.st

BEFORE = '90.21'
GAMEPAD, SAME, CLEAR, CROSS = gp.GAMEPAD, gp.SAME, gp.CLEAR, st.CROSS
MENU = {'Left': 'button_menu', 'Right': 'button_escape'}
STICKS = ('joystick', 'right_joystick')
TRIO = {'joystick': 'LST', 'right_joystick': 'RST'}


def xinput(button):
    return f'xinput_button {button}, , '


class GamepadTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data, cls.layouts = {}, {}
        for variant in ('default', 'alternative'):
            data = cls.data[variant] = gp.Builder(variant).finish()
            apply_all(data)
            cls.layouts[variant] = Layout(data)

    def each(self):
        for variant, layout in self.layouts.items():
            with self.subTest(variant=variant):
                yield variant, layout

    def acts(self, layout, layer, source, name):
        return layout.active(layer)[source]['inputs'][name]['activators']

    def outputs(self, layout, source, kind='Full_Press'):
        return {name: list(actions(value['activators'][kind]))
                for name, value in layout.active(GAMEPAD)[source]['inputs'].items() if kind in value['activators']}

    def test_two_layers_are_new_and_the_clear_is_renamed(self):
        for variant, data in self.data.items():
            before = json.loads((ROOT / f'versions/neptune/{BEFORE}/single-set-{variant}_hold-gyro_{BEFORE}.json').read_text())
            old, new = (list(d['controller_mappings']['action_layers'].values()) for d in (before, data))
            with self.subTest(variant=variant):
                # The clear keeps its place under its new title, so no runtime ID moves; the new layers are last.
                self.assertEqual([CLEAR if layer['title'] == st.CLEAR else layer['title'] for layer in old],
                                 [layer['title'] for layer in new[:-2]])
                self.assertEqual([layer['title'] for layer in new[-2:]], [SAME, GAMEPAD])
                self.assertEqual(len({layer['title'] for layer in new}), len(new))

    def test_the_two_layouts_have_the_same_gamepad_and_transitions(self):
        def shape(variant, name):
            text = json.dumps({source: (g['mode'], g.get('settings'), g.get('inputs') or {})
                               for source, g in self.layouts[variant].active(name).items()}, sort_keys=True)
            # The clear lists name the modifier layers, which are L2 and R2 in the alternative.
            return re.sub(r'\{\{Base::(.+?)\}\}', lambda m: map_title(m.group(1), {'L2': 'L1', 'R2': 'R1'}), text)
        for name in (GAMEPAD, SAME, CLEAR):
            self.assertEqual(shape('default', name), shape('alternative', name), name)

    def test_gamepad_sends_the_archived_map(self):
        for variant, layout in self.each():
            sources = layout.active(GAMEPAD)
            self.assertEqual({source: group['mode'] for source, group in sources.items()}, {
                'button_diamond': 'four_buttons', 'dpad': 'dpad', 'left_trigger': 'trigger', 'right_trigger': 'trigger',
                'joystick': 'joystick_move', 'right_joystick': 'joystick_move', 'left_trackpad': 'single_button',
                'right_trackpad': 'single_button', 'gyro': 'disabled', 'switch': 'switches'})
            self.assertEqual(self.outputs(layout, 'button_diamond'), {n: [xinput(b)] for n, b in gp.FACE.items()})
            self.assertEqual(self.outputs(layout, 'dpad'), {n: [xinput(b)] for n, b in gp.DPAD.items()})
            switches = self.outputs(layout, 'switch')
            for name, button in {**gp.SWITCHES, **gp.MENU_OUTPUT}.items():
                self.assertEqual(switches[name], [xinput(button)], name)
            for source, button in gp.STICK_CLICKS.items():
                self.assertEqual(self.outputs(layout, source)['click'], [xinput(button)])
            for source, button in gp.PAD_CLICKS.items():
                self.assertEqual(self.outputs(layout, source, 'Soft_Press'), {'click': [xinput(button)]})
            for source, output in gp.TRIGGERS.items():
                self.assertEqual(sources[source]['settings'], {'output_trigger': output, 'layer': '1'})
            self.assertFalse(sources['gyro'].get('inputs'))

    def test_start_and_select_use_three_native_activators(self):
        for variant, layout in self.each():
            for name, button in gp.MENU_OUTPUT.items():
                acts = self.acts(layout, GAMEPAD, 'switch', name)
                self.assertEqual(list(acts), ['Full_Press', 'Double_Press', 'Long_Press'])
                # The tap: interruptible, so the hold swallows it and a second press replaces it.
                self.assertEqual(acts['Full_Press'], {'bindings': {'binding': xinput(button)}})
                self.assertEqual(acts['Double_Press'], {'bindings': {'binding': xinput(button)},
                                                        'settings': {'double_tap_time': str(gp.DOUBLE_MS)}})
                self.assertEqual(acts['Long_Press'], {'bindings': {'binding': EMPTY + ', , '}, 'settings': {
                    'long_press_time': str(gp.LONG_MS), 'haptic_intensity': str(gp.HOLD_HAPTIC)}})

    def test_only_gamepads_menu_buttons_use_a_long_or_double_press(self):
        for variant, data in self.data.items():
            with self.subTest(variant=variant):
                report = audit_layout(data)
                self.assertFalse(report['violations'] or report['banned_activators'] or report['inverted_edges'])
                self.assertEqual(sorted((o['title'], row['input'], row['activation'])
                                        for row in report['allowed_native'] for o in row['owners']),
                                 sorted((GAMEPAD, name, kind) for name in gp.MENU_OUTPUT
                                        for kind in ('Double_Press', 'Long_Press')))
                # Without the exception the same four fail (R108).
                self.assertEqual(len(audit_layout(data, native=[])['banned_activators']), 4)

    def test_gamepad_is_closed(self):
        # R168: nothing of Base or Gyro that changes layers comes through, and its only layer commands are the exit.
        for variant, layout in self.each():
            for stack in (['Base'], ['Base', cg.GYRO]):
                routes, _ = check_stack(layout, GAMEPAD, stack)
                self.assertEqual([(r['source'], r['input']) for r in routes], [], stack)
            commands = {(source, name, kind) for source, group in layout.active(GAMEPAD).items()
                        for name, value in group.get('inputs', {}).items()
                        for kind, e in entries(value['activators']) if layout.layer_ops(e)}
            self.assertEqual(commands, {(source, 'click', 'chord') for source in STICKS})
            # Every input Base or Gyro binds on a shared source is bound here too.
            for below in ('Base', cg.GYRO):
                for source, group in layout.active(below).items():
                    mine = layout.active(GAMEPAD)[source]
                    if mine['mode'] == group['mode'] and mine['mode'] != 'disabled':
                        self.assertLessEqual(set(group.get('inputs', {})), set(mine.get('inputs', {})), (below, source))

    def test_a_stick_click_with_a_menu_button_held_enters_the_clear(self):
        for variant, layout in self.each():
            everything = set(layout.presets) - {'Base', cg.GYRO}
            for source in STICKS:
                acts = self.acts(layout, GAMEPAD, source, 'click')
                self.assertEqual(list(acts), ['Full_Press', 'chord'])
                self.assertNotIn('settings', acts['Full_Press'])            # interruptible: the chord suppresses it (A27)
                self.assertEqual(acts['chord']['settings'], {
                    'gyro_ratchet_button_mask': str(st.MENU_ANY), 'gyro_ratchet_button_requireany_or_all': '0',
                    'interruptable': '0'})
                ops = layout.layer_ops(acts['chord'])
                # The Entry Points' clear list first (R163), then the clear transition.
                self.assertEqual(ops[-1], ('add_layer', CLEAR))
                self.assertEqual({t for op, t in ops[:-1] if op == 'remove_layer'}, everything)
                self.assertEqual(len(ops), len(everything) + 1)

    def test_entry_point_clicks_lead_to_their_transition(self):
        targets = {st.entry_point('Left'): (SAME, CROSS), st.entry_point('Right'): (CROSS, SAME),
                   cg.stateful_entry_point('Left'): (CLEAR, CLEAR), cg.stateful_entry_point('Right'): (CLEAR, CLEAR)}
        for variant, layout in self.each():
            everything = set(layout.presets) - {'Base', cg.GYRO}
            for name, transitions in targets.items():
                for source, transition in zip(STICKS, transitions):
                    ops = layout.layer_ops(self.acts(layout, name, source, 'click')['release'])
                    self.assertEqual(ops[-1], ('add_layer', transition), (name, source))
                    self.assertEqual({t for op, t in ops[:-1] if op == 'remove_layer'}, everything, (name, source))

    def test_transition_menu_releases_and_their_feedback(self):
        steering = [('remove_layer', CROSS), ('add_layer', 'Steering'), ('add_layer', 'Steering | LS: Entry Guard')]
        cursor = [('remove_layer', CROSS), ('add_layer', cg.GYRO), ('add_layer', cg.CURSOR)]
        gamepad = [('remove_layer', SAME), ('add_layer', GAMEPAD)]
        expected = {(SAME, 'button_escape'): gamepad, (SAME, 'button_menu'): gamepad,
                    (CROSS, 'button_escape'): steering, (CROSS, 'button_menu'): cursor,
                    (CLEAR, 'button_escape'): [('remove_layer', CLEAR)], (CLEAR, 'button_menu'): [('remove_layer', CLEAR)]}
        stateful = {'Steering', cg.CURSOR, GAMEPAD}
        for variant, layout in self.each():
            for (name, button), ops in expected.items():
                acts = self.acts(layout, name, 'switch', button)
                self.assertEqual(list(acts), ['release'], (name, button))
                release = acts['release']
                self.assertEqual(layout.layer_ops(release), ops)
                # R161: a strong pulse, and one beep: on the stateful layer's add, or on the transition's own
                # removal when the release only clears. This builder wrote the flag first (`1 0`), which is
                # the on-screen name; 90.29 moves it to the second, the beep (A49).
                self.assertEqual(release['settings'], {'haptic_intensity': '3'}, (name, button))
                flags = {layout.resolve(m.group(1)): m.group(2) for a in actions(release)
                         if (m := re.search(r'_layer (\{\{.+?\}\}|\d+) (\d) \d', a))}
                beeping = [t for op, t in ops if op == 'add_layer' and t in stateful] or [name]
                self.assertEqual({t for t, flag in flags.items() if flag == '1'}, set(beeping), (name, button))

    def test_nothing_is_entered_from_a_transition(self):
        for variant, layout in self.each():
            for name in (SAME, CROSS, CLEAR):
                for stack in (['Base'], ['Base', cg.GYRO]):
                    routes, _ = check_stack(layout, name, stack)
                    self.assertEqual([(r['source'], r['input']) for r in routes], [], (name, stack))
                for source, group in layout.active(name).items():
                    for input_name, value in group.get('inputs', {}).items():
                        for kind, e in entries(value['activators']):
                            if layout.layer_ops(e):
                                self.assertEqual(kind, 'release', (name, source, input_name))
                                self.assertIn(input_name, ('button_escape', 'button_menu', 'touch'))
                for source, trio in TRIO.items():
                    touch = self.acts(layout, name, source, 'touch')
                    self.assertEqual(layout.layer_ops(touch['release']), [
                        ('remove_layer', f'{trio}: {kind}') for kind in ('Entry Point', 'Tap Cover', 'Temporary Gyro')])

    def test_the_new_transition_only_differs_from_the_cross_one_in_its_menu_releases(self):
        for variant, layout in self.each():
            same, cross = layout.active(SAME), layout.active(CROSS)
            self.assertEqual(set(same), set(cross))
            for source in same:
                a, b = (json.loads(json.dumps(layout.active(name)[source])) for name in (SAME, CROSS))
                for group in (a, b):
                    group.pop('id')
                    group['inputs'] = group.get('inputs') or {}
                    for button in MENU.values():
                        group.get('inputs', {}).pop(button, None)
                self.assertEqual(a, b, source)

    def test_only_the_same_side_transition_adds_gamepad(self):
        for variant, layout in self.each():
            adding = {name for name in layout.presets for group in layout.active(name).values()
                      for value in group.get('inputs', {}).values() for _, e in entries(value['activators'])
                      if ('add_layer', GAMEPAD) in layout.layer_ops(e)}
            self.assertEqual(adding, {SAME})

    def test_what_changed_since_the_last_release(self):
        # The report matches layers by title, so the renamed clear shows as added and the new
        # `Transition Set 0` as a change of the old one.
        steering = {'Steering | L1!R1: Modifier 2', 'Steering | R1!L1: Modifier 2'}
        for variant, data in self.data.items():
            before = json.loads((ROOT / f'versions/neptune/{BEFORE}/single-set-{variant}_hold-gyro_{BEFORE}.json').read_text())
            report = changes.diff(before, data)
            names = {map_title(t, {'L1': 'L2', 'R1': 'R2'}) if variant == 'alternative' else t for t in steering}
            with self.subTest(variant=variant):
                self.assertEqual((sorted(report['added']), report['removed']), (sorted([CLEAR, GAMEPAD]), []))
                # The four Entry Points and Steering's whole-layout clear name the two new layers and the new
                # title. Nothing else changed: not Base, Gyro, Cursor Gyro or a modifier.
                self.assertEqual(set(report['layers']), names | {SAME} | {st.entry_point(side) for side in MENU}
                                 | {cg.stateful_entry_point(side) for side in MENU})


if __name__ == '__main__':
    unittest.main()
