"""The menu chain on every press and the windows' right-pad touch, on the generated candidates (90.28).

Builds both variants with the 2026-10-04 menu-chain-and-window-pads builder and runs the fix
pipeline, as the install does (findings/2026-10-04-menu-chain-and-window-pads/README.md). These
verify saved configuration contracts, not Steam's runtime scheduling; the press sequences are in
test_scenarios_90_28.py.
"""
import copy
import importlib.util
import json
from pathlib import Path
import unittest

from tools.convert_runtime_ids import generate_lookup, titles_to_ids
from steam_layout import changes
from steam_layout.fixes import apply_all
from steam_layout.model import EMPTY, Layout, actions, always_on_layers, bindings, entries, map_title

ROOT = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location(
    'menu_chain_and_window_pads', ROOT / 'findings/2026-10-04-menu-chain-and-window-pads/build_candidate.py')
mw = importlib.util.module_from_spec(spec); spec.loader.exec_module(mw)

BEFORE = '90.27'
BUTTON = {'Left': 'button_menu', 'Right': 'button_escape'}
# first held, second pressed, the key the chain types
SIDES = (('Left', 'Right', 'RETURN'), ('Right', 'Left', 'BACKSPACE'))
# the windows whose pad touch keeps the pad's three layers; the others can't have them underneath
FULL = ('L1: Double Tap', 'R1: Double Tap', 'Menu Left: Double Tap', 'Menu Right: Double Tap',
        'Menu Left!Right: Double Tap', 'Menu Right!Left: Double Tap')
ALONE = ('LST: Double Tap', 'RST: Double Tap', 'Steering | LS Up: Double Tap', 'Steering | LS Down: Double Tap')


def snapshot(variant):
    path = ROOT / f'versions/neptune/{BEFORE}/single-set-{variant}_hold-gyro_{BEFORE}.json'
    return json.loads(path.read_text(encoding='utf-8'))


def adders(layout, target):
    """{(layer, source/input, activation type)} of every binding that adds `target`."""
    return {(title, f'{source}/{name}', kind)
            for title in layout.presets for source, group in layout.active(title).items()
            for name, slot in group.get('inputs', {}).items() for kind, e in entries(slot.get('activators', {}))
            if ('add_layer', target) in layout.layer_ops(e)}


def outputs(layout, title):
    """Every key or mouse output of a layer, by input."""
    return {(source, name): sorted(a for a in bindings(slot.get('activators', {})) if 'controller_action' not in a)
            for source, group in layout.active(title).items() for name, slot in group.get('inputs', {}).items()}


class MenuChainAndWindowPadsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data, cls.layouts, cls.numeric = {}, {}, {}
        for variant in ('default', 'alternative'):
            data = cls.data[variant] = mw.Builder(variant).finish()
            apply_all(data)
            cls.layouts[variant] = Layout(data)
            numeric, _ = titles_to_ids(json.dumps(data), generate_lookup(data))
            cls.numeric[variant] = json.loads(numeric)

    def each(self):
        for variant, layout in self.layouts.items():
            with self.subTest(variant=variant):
                yield variant, layout

    def title(self, variant, title):
        return map_title(title, {'L1': 'L2', 'R1': 'R2'}) if variant == 'alternative' else title

    def test_the_90_28_snapshot_is_this_build(self):
        # The working layouts were this build until 90.29. The newest build's test holds R156.
        for variant in self.data:
            with self.subTest(variant=variant):
                built = copy.deepcopy(self.numeric[variant]['controller_mappings'])
                saved = json.loads((ROOT / f'versions/neptune/90.28/single-set-{variant}_hold-gyro_90.28.json').read_text())[
                    'controller_mappings']
                for cm in (built, saved):
                    cm.pop('title'); cm.pop('description')
                self.assertEqual(built, saved)

    def test_two_layers_are_added_at_the_end_and_no_runtime_id_moves(self):
        self.assertEqual(mw.ADDED, ['Stateful | Menu Left: Fn Layer', 'Stateful | Menu Right: Fn Layer'])
        for variant, layout in self.each():
            before = list(Layout(snapshot(variant)).presets)
            self.assertEqual(list(layout.presets), before + mw.ADDED)
            self.assertEqual(len(layout.presets), 90)                       # Base and 89 layers

    # --- the chain on every press ---------------------------------------------------------------

    def test_the_fn_layers_bind_for_the_other_button_adds_the_chains_entry_point(self):
        for variant, layout in self.each():
            for first, second, key in SIDES:
                fn, entry = f'Menu {first}: Fn Layer', f'Menu {first}!{second}: Entry Point'
                acts = layout.active(fn)['switch']['inputs'][BUTTON[second]]['activators']
                self.assertEqual(sorted(acts), ['Full_Press', 'chord'])
                self.assertEqual(layout.layer_ops(acts['chord']), [('add_layer', entry)])
                self.assertEqual(acts['chord']['settings'], {'chord_button': {'Left': '15', 'Right': '14'}[first]})
                self.assertNotIn(f'key_press {key}, , ', sum(outputs(layout, fn).values(), []))     # it types nothing itself
                cleanup = acts['Full_Press']                                 # for a press with the first button up (R171)
                self.assertEqual(cleanup['settings'], {'hold_repeats': '1'})
                self.assertTrue(all(op == 'remove_layer' for op, _ in layout.layer_ops(cleanup)))

    def test_the_chains_entry_point_comes_from_the_other_buttons_press_only(self):
        for variant, layout in self.each():
            for first, second, _ in SIDES:
                plain, fn, entry = f'Menu {first}: Entry Point', f'Menu {first}: Fn Layer', f'Menu {first}!{second}: Entry Point'
                self.assertEqual(adders(layout, entry), {(fn, f'switch/{BUTTON[second]}', 'chord'),
                                                         (plain, f'switch/{BUTTON[second]}', 'chord')})
                early = layout.active(plain)['switch']['inputs'][BUTTON[second]]['activators']['chord']
                self.assertEqual(layout.layer_ops(early), [('add_layer', fn), ('add_layer', entry)])    # the Fn layer first
                hold = layout.active(plain)['switch']['inputs'][BUTTON[first]]['activators']['chord']
                self.assertEqual(layout.layer_ops(hold), [('add_layer', fn)])
                for stick in ('joystick', 'right_joystick'):
                    lift = layout.active(plain)[stick]['inputs']['touch']['activators']['release']
                    self.assertEqual([t for op, t in layout.layer_ops(lift) if op == 'add_layer'], [fn])

    def test_the_stateful_entry_points_have_fn_layers_of_their_own_that_type_the_key(self):
        for variant, layout in self.each():
            old = Layout(snapshot(variant))
            for first, second, key in SIDES:
                fn, copy_, stateful = f'Menu {first}: Fn Layer', f'Stateful | Menu {first}: Fn Layer', f'Stateful | Menu {first}: Entry Point'
                self.assertEqual({layer for layer, _, _ in adders(layout, copy_)}, {stateful})
                self.assertEqual(len(adders(layout, copy_)), 4)
                self.assertEqual({layer for layer, _, _ in adders(layout, fn)}, {f'Menu {first}: Entry Point'})
                reset = layout.active(stateful)['switch']['inputs'][BUTTON[first]]['activators']['Full_Press']
                self.assertEqual(layout.layer_ops(reset), [('remove_layer', copy_)])
                chord = layout.active(copy_)['switch']['inputs'][BUTTON[second]]['activators']['chord']
                self.assertEqual([a for a in actions(chord) if a != EMPTY + ', , '], [f'key_press {key}, , '])
                self.assertEqual(outputs(layout, copy_), outputs(old, fn))  # every key of the Fn layer as it was in 90.27
                release = layout.active(copy_)['switch']['inputs'][BUTTON[first]]['activators']['release']
                self.assertEqual(set(layout.layer_ops(release)), {('remove_layer', stateful), ('remove_layer', copy_)})
                self.assertEqual(adders(layout, f'Menu {first}!{second}: Entry Point') & {(stateful, s, k) for _, s, k in adders(layout, copy_)}, set())

    # --- the windows' right pad ----------------------------------------------------------------

    def test_a_windows_right_pad_touch_is_a_release_that_ends_the_window_first(self):
        for variant, layout in self.each():
            windows = always_on_layers(layout)
            self.assertEqual(len(windows), 11)
            self.assertEqual(set(windows), {self.title(variant, t) for t in FULL + ALONE} | {mw.PAD_WINDOW})
            base = layout.active(layout.base)['right_trackpad']
            for title in windows:
                group = layout.active(title)['right_trackpad']
                if title == mw.PAD_WINDOW:                                   # the pad's own window: its D-pad, no touch
                    self.assertEqual((group['mode'], 'touch' in group['inputs']), ('dpad', False))
                    continue
                self.assertEqual((group['mode'], group['settings']), (base['mode'], {'layer': '1'}))
                self.assertEqual(set(group['inputs']), {'click', 'touch'})
                self.assertEqual(list(bindings(group['inputs']['click']['activators'])), [EMPTY + ', , '])
                touch = group['inputs']['touch']['activators']
                self.assertEqual(list(touch), ['release'])
                self.assertEqual(touch['release']['settings'], {'haptic_intensity': '0'})
                removed = [('remove_layer', title)] + [('remove_layer', t) for t in mw.PAD_TRIO]
                full = title in {self.title(variant, t) for t in FULL}
                self.assertEqual(layout.layer_ops(touch['release']), removed if full else removed[:1], title)

    def test_it_is_the_stick_touches_pattern(self):
        for variant, layout in self.each():
            title = self.title(variant, 'L1: Double Tap')
            stick = layout.active(title)['right_joystick']['inputs']['touch']['activators']
            pad = layout.active(title)['right_trackpad']['inputs']['touch']['activators']
            self.assertEqual((list(stick), list(pad)), (['release'], ['release']))
            self.assertEqual(layout.layer_ops(stick['release']), [('remove_layer', title)] + [
                ('remove_layer', f'RST: {name}') for name in ('Entry Point', 'Tap Cover', 'Temporary Gyro')])
            self.assertEqual(stick['release'].get('settings'), pad['release'].get('settings'))

    def test_the_left_pad_and_the_clicks_keep_their_known_replacements(self):
        keys = {'dpad_west': 'ESCAPE', 'dpad_east': 'RETURN', 'dpad_north': 'TAB', 'dpad_south': 'BACKSPACE'}
        for variant, layout in self.each():
            for title in always_on_layers(layout):
                left = layout.active(title)['left_trackpad']['inputs']
                for name in ('click', 'touch'):
                    self.assertEqual(list(bindings(left[name]['activators'])), [EMPTY + ', , '], (title, name))
                self.assertEqual({name: list(bindings(left[name]['activators'])) for name in keys},
                                 {name: [f'key_press {key}, , '] for name, key in keys.items()}, title)

    # --- against 90.27 -----------------------------------------------------------------------

    def test_against_90_27_the_change_is_the_menu_family_the_windows_and_the_clear_lists(self):
        menu = ['Menu Left: Fn Layer', 'Menu Right: Fn Layer', 'Menu Left: Entry Point', 'Menu Right: Entry Point',
                'Stateful | Menu Left: Entry Point', 'Stateful | Menu Right: Entry Point']
        clears = ['Steering | R1!L1: Modifier 2', 'Steering | L1!R1: Modifier 2', 'Gamepad', 'Menu Left!Right: Entry Point',
                  'Menu Right!Left: Entry Point', 'Menu Keys']
        for variant in self.data:
            with self.subTest(variant=variant):
                report = changes.diff(snapshot(variant), self.numeric[variant])
                self.assertEqual((report['added'], report['removed']), (mw.ADDED, []))
                expected = {self.title(variant, t) for t in menu + clears + list(FULL + ALONE)} | set(mw.ADDED)
                self.assertEqual(changes.changed_layers(report), expected)


if __name__ == '__main__':
    unittest.main()
