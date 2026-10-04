"""The pad touch bumps, the middle-click mouse, Menu Keys and the Tap Cover resets, on the generated candidates.

Builds both variants with the 2026-10-04 builder and runs the fix pipeline, as the install does
(findings/2026-10-04-pad-bumps-and-menu-keys/README.md). These verify saved configuration
contracts, not Steam's runtime scheduling; the press sequences are in test_scenarios_90_25.py.
"""
import importlib.util
import json
from pathlib import Path
import unittest

from tools.convert_runtime_ids import generate_lookup, titles_to_ids
from steam_layout.cleanups import Cleanups
from steam_layout.fixes import apply_all
from steam_layout.model import EMPTY, Layout, actions, always_on_layers, entries

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    'pad_bumps_and_menu_keys', ROOT / 'findings/2026-10-04-pad-bumps-and-menu-keys/build_candidate.py')
pb = importlib.util.module_from_spec(spec); spec.loader.exec_module(pb)
st = pb.st

BEFORE = '90.24'
BLOCK = EMPTY + ', , '
KEY = 'key_press {}, , '
MENU_BIT = {'Left': 12, 'Right': 14}                    # Select, Start, as chord mask bits


def snapshot(variant):
    path = ROOT / f'versions/neptune/{BEFORE}/single-set-{variant}_hold-gyro_{BEFORE}.json'
    return Layout(json.loads(path.read_text(encoding='utf-8')))


def shape(layout, value):
    """An input's entries without their reference style: (type, layer commands, other commands, settings)."""
    return [(kind, layout.layer_ops(e), [a for a in actions(e) if 'controller_action' not in a], e.get('settings', {}))
            for kind, e in entries(value['activators'])]


class PadBumpsAndMenuKeysTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data, cls.layouts = {}, {}
        for variant in ('default', 'alternative'):
            data = cls.data[variant] = pb.Builder(variant).finish()
            apply_all(data)
            cls.layouts[variant] = Layout(data)

    def each(self):
        for variant, layout in self.layouts.items():
            with self.subTest(variant=variant):
                yield variant, layout

    def acts(self, layout, layer, source, name):
        return layout.active(layer)[source]['inputs'][name]['activators']

    def one(self, layout, layer, source, name, kind):
        found = self.acts(layout, layer, source, name)[kind]
        self.assertIsInstance(found, dict, f'{layer} {source}/{name} {kind}')
        return found

    def test_the_90_25_snapshot_is_this_build(self):
        # The working layouts were this build until 90.26, whose own test now holds R156
        # (test_standard_delays.test_working_layouts_are_this_build).
        for variant, data in self.data.items():
            with self.subTest(variant=variant):
                numeric, _ = titles_to_ids(json.dumps(data), generate_lookup(data))
                built = json.loads(numeric)['controller_mappings']
                snapshot = json.loads((ROOT / f'versions/neptune/90.25/single-set-{variant}_hold-gyro_90.25.json').read_text())[
                    'controller_mappings']
                for cm in (built, snapshot):
                    cm.pop('title'); cm.pop('description')
                self.assertEqual(built, snapshot)

    # --- the layers ---------------------------------------------------------------------------

    def test_twelve_layers_are_added_at_the_end_and_no_runtime_id_moves(self):
        self.assertEqual(len(pb.NEW), 12)
        for variant, layout in self.each():
            before = list(snapshot(variant).presets)
            self.assertEqual(list(layout.presets), before + pb.NEW)
            self.assertEqual(len(layout.presets), 91)                    # Base and 90 layers

    def test_menu_keys_is_stateful_and_the_two_windows_are_always_on(self):
        for variant, layout in self.each():
            self.assertIn(pb.MENU_KEYS, Cleanups(layout).stateful)
            windows = [pb.chain(*sides)[1] for sides in pb.CHAINS]
            self.assertTrue(set(windows) <= set(always_on_layers(layout)))
            self.assertEqual(len(always_on_layers(layout)), 11)

    # --- part 1: the bumps --------------------------------------------------------------------

    def test_a_touch_adds_the_handover_layer_which_reads_the_ring_once(self):
        for variant, layout in self.each():
            for pad, (source, entry, _) in pb.PADS.items():
                name = pb.touch_entry_point(pad)
                touch = self.one(layout, 'Base', source, 'touch', 'Full_Press')
                self.assertEqual(layout.layer_ops(touch), [('add_layer', name)])
                self.assertEqual(touch['settings'], {'hold_repeats': '1', 'haptic_intensity': '0', 'interruptable': '0'})
                self.assertEqual(list(layout.active('Base')[source]['inputs']), ['touch'])     # Base binds nothing else there
                group = layout.active(name)[source]
                self.assertEqual((group['mode'], group['settings'].get('requires_click')), ('dpad', '0'))
                inner, outer = self.acts(layout, name, source, 'edge')['Soft_Press']
                for bind in (inner, outer):                              # the layer goes first, then the Entry Point comes
                    self.assertEqual(layout.layer_ops(bind), [('remove_layer', name), ('add_layer', entry)])
                # The two binds are the Click Entry Point's, setting for setting, so the bump and the click agree
                # at every spot. Only the inner one's haptic differs: the low bump.
                centre, rim = self.acts(layout, pb.PADS[pad][2], source, 'edge')['Soft_Press']
                self.assertEqual(inner['settings'], {**centre['settings'], 'haptic_intensity': '1'})
                self.assertEqual(outer['settings'], rim['settings'])
                # The inner one repeats and has no delay; the 5 ms delay is on the outer one alone (author, 2026-10-04).
                self.assertEqual((inner['settings'].get('edge_binding_invert'), inner['settings'].get('delay_start'),
                                  inner['settings']['hold_repeats'], inner['settings']['repeat_rate']), ('1', None, '1', '50'))
                self.assertEqual((outer['settings'].get('edge_binding_invert'), outer['settings']['delay_start']), (None, '5'))
                release = self.one(layout, name, source, 'touch', 'release')
                self.assertEqual(layout.layer_ops(release), [('remove_layer', name)])

    def test_bases_right_pad_stays_a_mouse_and_the_click_moves_to_the_entry_point(self):
        for variant, layout in self.each():
            base = layout.active('Base')['right_trackpad']
            self.assertEqual(base['mode'], 'absolute_mouse')
            self.assertEqual({k: base['settings'].get(k) for k in ('friction', 'acceleration', 'haptic_intensity')},
                             {'friction': '3', 'acceleration': '1', 'haptic_intensity': '0'})
            for layer, repeat in (('RTP: Entry Point', '50'), ('Steering', None)):
                click = self.one(layout, layer, 'right_trackpad', 'click', 'Soft_Press')
                self.assertEqual(layout.layer_ops(click), [('add_layer', 'RTP: Click Entry Point')])
                # In the Entry Point it repeats, for a click that is already down when the layer lands (A6). No delay.
                self.assertEqual((click['settings'].get('haptic_intensity'), click['settings'].get('repeat_rate'),
                                  click['settings'].get('delay_start')), ('3', repeat, None))
            # Every other layer whose pad is a mouse binds its own click or has the Entry Point under it.
            mice = [t for t in layout.presets if layout.active(t).get('right_trackpad', {}).get('mode') == 'absolute_mouse'
                    and 'click' not in layout.active(t)['right_trackpad'].get('inputs', {})]
            self.assertEqual(mice, ['Base', 'RTP: Tap Cover'])

    def test_bases_left_pad_is_a_dpad_and_the_swipes_are_in_the_entry_point(self):
        for variant, layout in self.each():
            old = snapshot(variant).active('Base')['left_trackpad']
            base = layout.active('Base')['left_trackpad']
            self.assertEqual((base['mode'], base['settings']), ('dpad', {'requires_click': '0', 'haptic_intensity_override': '0'}))
            entry = pb.PADS['LTP'][1]
            group = layout.active(entry)['left_trackpad']
            self.assertEqual((group['mode'], group['settings']), (old['mode'], {**old.get('settings', {}), 'layer': '1'}))
            for direction in pb.SWIPES:
                (added,) = snapshot(variant).layer_ops(old['inputs'][direction]['activators']['Full_Press'])
                swipe = self.one(layout, entry, 'left_trackpad', direction, 'Full_Press')
                self.assertEqual(layout.layer_ops(swipe), [('remove_layer', entry), added])
                self.assertEqual(swipe['settings'], old['inputs'][direction]['activators']['Full_Press']['settings'])
            click = self.one(layout, entry, 'left_trackpad', 'click', 'Soft_Press')
            self.assertEqual((layout.layer_ops(click), click['settings']),
                             ([('add_layer', 'LTP: Click Entry Point')],
                              {'haptic_intensity': '3', 'hold_repeats': '1', 'repeat_rate': '50'}))
            release = self.one(layout, entry, 'left_trackpad', 'touch', 'release')
            self.assertEqual(layout.layer_ops(release), [('remove_layer', entry)])
            for layer in ('LTP: Click Entry Point', 'LTP: Middle Click', 'LTP: Arrow Keys'):     # their thumb lift ends it too
                self.assertIn(('remove_layer', entry), layout.layer_ops(self.one(layout, layer, 'left_trackpad', 'touch', 'release')))

    def test_the_windows_still_read_the_swipe_keys(self):
        keys = {'dpad_west': 'ESCAPE', 'dpad_east': 'RETURN', 'dpad_north': 'TAB', 'dpad_south': 'BACKSPACE'}
        for variant, layout in self.each():
            for window in always_on_layers(layout):
                left = layout.active(window)['left_trackpad']
                self.assertEqual(left['mode'], '2dscroll', window)
                for direction, key in keys.items():
                    self.assertEqual(actions(left['inputs'][direction]['activators']['Full_Press']), [KEY.format(key)], window)

    # --- part 2 --------------------------------------------------------------------------------

    def test_the_middle_click_pad_is_a_mouse_with_its_click_unchanged(self):
        for variant, layout in self.each():
            group = layout.active(pb.MIDDLE)['right_trackpad']
            self.assertEqual(group['mode'], layout.active('Base')['right_trackpad']['mode'])
            old = snapshot(variant).active(pb.MIDDLE)['right_trackpad']
            self.assertEqual(old['mode'], 'single_button')
            self.assertEqual(shape(layout, group['inputs']['click']), shape(snapshot(variant), old['inputs']['click']))
            self.assertIn('mouse_button MIDDLE, , ', actions(group['inputs']['click']['activators']['Full_Press']))

    # --- part 5 --------------------------------------------------------------------------------

    def test_the_three_entry_points_reset_their_delayed_tap_cover(self):                 # R120, R121
        for variant, layout in self.each():
            for prefix, source in (('LST', 'joystick'), ('RST', 'right_joystick'), ('RTP', 'right_trackpad')):
                touch = self.acts(layout, f'{prefix}: Entry Point', source, 'touch')
                self.assertEqual(list(touch), ['release', 'chord', 'Full_Press'])            # three entries (R109)
                cover = f'{prefix}: Tap Cover'
                self.assertEqual((layout.layer_ops(touch['chord']), touch['chord']['settings']['delay_start']),
                                 ([('add_layer', cover)], '150'))
                self.assertEqual(layout.layer_ops(touch['Full_Press']), [('remove_layer', cover)])     # only that target
                self.assertEqual(touch['Full_Press']['settings'], {'hold_repeats': '1', 'repeat_rate': '200', 'interruptable': '0'})
                # R122: the cover binds the touch, so the reset can't reach it once it has landed.
                self.assertIn('touch', layout.active(cover)[source]['inputs'])

    # --- part 3: the chorded chains -------------------------------------------------------------

    def test_only_the_plain_entry_points_add_the_chorded_entry_point(self):
        for variant, layout in self.each():
            for (first, second) in pb.CHAINS:
                entry = pb.chain(first, second)[0]
                fn = st.fn_layer(first)
                adders = {}
                for title in layout.presets:
                    for source, group in layout.active(title).items():
                        for name, value in group.get('inputs', {}).items():
                            for kind, e in entries(value.get('activators', {})):
                                ops = layout.layer_ops(e)
                                if ('add_layer', entry) in ops:
                                    adders.setdefault(title, []).append(ops)
                self.assertEqual(list(adders), [st.entry_point(first)])
                self.assertEqual(len(adders[st.entry_point(first)]), 4)
                for ops in adders[st.entry_point(first)]:                # the Fn layer first, this one on top of it
                    self.assertEqual(ops.index(('add_layer', entry)), ops.index(('add_layer', fn)) + 1)
                stateful = f'Stateful | Menu {first}: Entry Point'
                fn_adds = [1 for g in layout.active(stateful).values() for v in g.get('inputs', {}).values()
                           for _, e in entries(v.get('activators', {})) if ('add_layer', fn) in layout.layer_ops(e)]
                self.assertEqual(len(fn_adds), 4)                        # it shares the Fn layer, and adds nothing else

    def test_the_chorded_entry_point_is_the_menu_chains_parent_for_the_second_button(self):
        for variant, layout in self.each():
            for (first, second) in pb.CHAINS:
                entry, window, _, _ = pb.chain(first, second)
                first_button, first_legacy, _ = st.MENU[first]
                second_button = st.MENU[second][0]
                press = self.acts(layout, entry, 'switch', second_button)
                self.assertEqual(list(press), ['release', 'chord', 'Full_Press'])          # three entries (R109)
                self.assertEqual(layout.layer_ops(press['release']), [('remove_layer', entry), ('add_layer', window)])
                hold = press['chord']
                self.assertEqual({k: hold['settings'].get(k) for k in ('chord_button', 'delay_start', 'haptic_intensity')},
                                 {'chord_button': first_legacy, 'delay_start': '150', 'haptic_intensity': '3'})
                ops = layout.layer_ops(hold)
                self.assertEqual(ops[-1], ('add_layer', pb.MENU_KEYS))                       # added last, with the beep
                self.assertIn(pb.MENU_KEYS + '}} 1 0', actions(hold)[0])
                cleared = {title for op, title in ops[:-1]}
                self.assertEqual({op for op, _ in ops[:-1]}, {'remove_layer'})
                self.assertEqual(cleared, set(layout.presets) - {'Base', pb.MENU_KEYS})       # the whole stack, Gyro included
                self.assertEqual((layout.layer_ops(press['Full_Press']), press['Full_Press']['settings']),
                                 ([('remove_layer', pb.MENU_KEYS)], {'hold_repeats': '1', 'repeat_rate': '200', 'interruptable': '0'}))
                # It binds nothing else on the buttons: the Fn layer's keys come through.
                self.assertEqual(list(layout.active(entry)['switch']['inputs']), [second_button])
                self.assertEqual(sorted(s for s in layout.active(entry) if layout.active(entry)[s].get('inputs')),
                                 ['joystick', 'right_joystick', 'switch'])
                for source in st.STICKS.values():                       # in the Fn layer's stick mode
                    self.assertEqual(layout.active(entry)[source]['mode'], layout.active(st.fn_layer(first))[source]['mode'])
                # The first button's own Release also ends it.
                release = self.one(layout, st.fn_layer(first), 'switch', first_button, 'release')
                self.assertEqual(layout.layer_ops(release)[0], ('remove_layer', entry))

    def test_the_window_types_the_key_and_carries_the_first_buttons_release(self):
        for variant, layout in self.each():
            for (first, second), (key, _, _, _) in pb.CHAINS.items():
                _, window, held, _ = pb.chain(first, second)
                first_button, second_button = st.MENU[first][0], st.MENU[second][0]
                timeout, typed = self.acts(layout, window, 'switch', 'always_on_action')['Full_Press']
                self.assertEqual((layout.layer_ops(timeout), timeout['settings']['delay_start']), ([('remove_layer', window)], '150'))
                self.assertEqual((actions(typed), typed['settings']['delay_start']), ([KEY.format(key)], '50'))
                again = self.one(layout, window, 'switch', second_button, 'Full_Press')
                self.assertEqual(layout.layer_ops(again), [('remove_layer', window), ('add_layer', held)])   # R148
                held_first = self.acts(layout, window, 'switch', first_button)
                self.assertEqual(actions(held_first['Full_Press']), [BLOCK])
                ops = layout.layer_ops(held_first['release'])
                self.assertEqual(ops[0], ('remove_layer', window))                                         # the window first
                self.assertTrue({('remove_layer', st.fn_layer(first)), ('remove_layer', st.entry_point(first))} <= set(ops))

    def test_the_second_press_layer_and_its_cover_hold_the_key(self):
        for variant, layout in self.each():
            for (first, second), (key, _, _, _) in pb.CHAINS.items():
                _, window, held, cover = pb.chain(first, second)
                second_button, second_legacy = st.MENU[second][0], st.MENU[second][1]
                press = self.acts(layout, held, 'switch', second_button)
                self.assertEqual(list(press), ['release', 'chord', 'Full_Press'])
                typed, reset = press['Full_Press']                                         # the reset is a last 4th entry
                self.assertEqual((actions(typed), typed['settings']), ([KEY.format(key)], {'interruptable': '0'}))
                self.assertEqual((layout.layer_ops(reset), reset['settings']['repeat_rate']), ([('remove_layer', cover)], '200'))
                self.assertEqual(layout.layer_ops(press['release']), [('remove_layer', held), ('add_layer', window)])
                self.assertEqual((layout.layer_ops(press['chord']), press['chord']['settings']['delay_start'],
                                  press['chord']['settings']['chord_button']), ([('add_layer', cover)], '150', second_legacy))
                over = self.acts(layout, cover, 'switch', second_button)
                self.assertEqual(actions(over['Full_Press']), [KEY.format(key)])
                self.assertEqual(set(layout.layer_ops(over['release'])), {('remove_layer', held), ('remove_layer', cover)})
                # The right stick stays in the Fn layer's mode: the Entry Point's click under it isn't hidden (A2).
                for layer in (held, cover):
                    self.assertEqual(layout.active(layer)['right_joystick']['mode'], layout.active(st.fn_layer(first))['right_joystick']['mode'])

    # --- part 3: Menu Keys ----------------------------------------------------------------------

    def test_menu_keys_types_the_arrows_and_the_four_keys(self):
        for variant, layout in self.each():
            for source, keys in (('button_diamond', pb.FACE), ('dpad', pb.ARROWS)):
                self.assertEqual(sorted(layout.active(pb.MENU_KEYS)[source]['inputs']), sorted(keys))
                for name, key in keys.items():
                    press = self.acts(layout, pb.MENU_KEYS, source, name)
                    self.assertEqual(list(press), ['Full_Press', 'chord'])
                    self.assertEqual((actions(press['Full_Press']), press['Full_Press'].get('settings', {}).get('interruptable')),
                                     ([KEY.format(key)], None))                            # interruptible: the chord takes over
                    self.assertEqual(layout.layer_ops(press['chord']), [('remove_layer', pb.MENU_KEYS)])
                    self.assertEqual({k: press['chord']['settings'][k] for k in
                                      ('gyro_ratchet_button_mask', 'gyro_ratchet_button_requireany_or_all', 'interruptable')},
                                     {'gyro_ratchet_button_mask': str(pb.EITHER_STICK_OUT),
                                      'gyro_ratchet_button_requireany_or_all': '0', 'interruptable': '0'})
            self.assertEqual(pb.FACE, {'button_a': 'RETURN', 'button_b': 'ESCAPE', 'button_x': 'BACKSPACE', 'button_y': 'TAB'})

    def test_menu_keys_closes_the_modifiers_the_menu_buttons_and_the_stick_touches(self):
        for variant, layout in self.each():
            active = layout.active(pb.MENU_KEYS)
            blocked = [('switch', 'button_escape'), ('switch', 'button_menu'), ('joystick', 'touch'), ('right_joystick', 'touch')]
            for source, name in blocked + pb.MODIFIERS[variant]:
                self.assertEqual([actions(e) for _, e in entries(active[source]['inputs'][name]['activators'])], [[BLOCK]],
                                 f'{source}/{name}')
            # Everything else is Base's: the pads, the back buttons, the firing buttons, the gyro.
            self.assertEqual(sorted(active), sorted({'button_diamond', 'dpad', 'switch', 'joystick', 'right_joystick'}
                                                    | {source for source, _ in pb.MODIFIERS[variant]}))
            self.assertEqual(sorted(active['switch']['inputs']),
                             sorted(['button_escape', 'button_menu'] + [n for s, n in pb.MODIFIERS[variant] if s == 'switch']))

    def test_menu_keys_has_the_two_stick_exits(self):
        for variant, layout in self.each():
            base = layout.active('Base')
            for source, (other, radius) in pb.cg.STICKS.items():
                group = layout.active(pb.MENU_KEYS)[source]
                self.assertEqual((group['settings']['edge_binding_radius'], group['settings']['edge_binding_invert']), (radius, '0'))
                out = self.one(layout, pb.MENU_KEYS, source, 'edge', 'chord')               # both sticks out
                self.assertEqual(layout.layer_ops(out), [('remove_layer', pb.MENU_KEYS)])
                self.assertEqual((out['settings']['gyro_ratchet_button_mask'], out['settings']['hold_repeats']), (str(1 << other), '1'))
                click = self.acts(layout, pb.MENU_KEYS, source, 'click')                    # a menu button held plus the click
                self.assertEqual(actions(click['Full_Press']), actions(base[source]['inputs']['click']['activators']['Full_Press']))
                ops = layout.layer_ops(click['chord'])
                self.assertEqual(ops[-1], ('add_layer', 'Transition Set 2'))
                self.assertIn(('remove_layer', pb.MENU_KEYS), ops)
                self.assertEqual(click['chord']['settings']['gyro_ratchet_button_mask'], str(sum(1 << b for b in MENU_BIT.values())))

    def test_no_double_tap_window_can_land_on_menu_keys_but_the_right_pads(self):
        """A window there must clear the face buttons and the D-pad on every stack (R140). Only RTP: Double Tap,
        which already clears them, can land: the pad does what it does on Base."""
        for variant, layout in self.each():
            cleanups = Cleanups(layout)
            above = cleanups.above(pb.MENU_KEYS) & set(always_on_layers(layout))
            self.assertEqual(above, {'RTP: Double Tap'})


if __name__ == '__main__':
    unittest.main()
