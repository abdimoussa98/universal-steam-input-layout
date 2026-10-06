"""The pad window's Releases, the fallback's edge and the Tap Cover resets off, on the generated candidates (90.30).

Builds both variants with the 2026-10-04 window-releases-and-tap-cover-resets builder and runs the
fix pipeline, as the install does (findings/2026-10-04-window-releases-and-tap-cover-resets/README.md).
These verify saved configuration contracts, not Steam's runtime scheduling; the press sequences are
in test_scenarios_90_30.py.
"""
import copy
import importlib.util
import json
from pathlib import Path
import unittest

from tools.convert_runtime_ids import generate_lookup, titles_to_ids
from steam_layout import changes
from steam_layout.fixes import apply_all
from steam_layout.model import EMPTY, Layout, actions, always_on_layers, entries, map_title

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    'window_releases_and_tap_cover_resets', ROOT / 'findings/2026-10-04-window-releases-and-tap-cover-resets/build_candidate.py')
wr = importlib.util.module_from_spec(spec); spec.loader.exec_module(wr)

BEFORE = '90.29'
# the modifier buttons, which the window turns into the scroll wheel
MODIFIERS = {'default': (('switch', 'left_bumper'), ('switch', 'right_bumper')),
             'alternative': (('left_trigger', 'edge'), ('right_trigger', 'edge'))}
ENTRY_POINTS = (('LST', 'joystick'), ('RST', 'right_joystick'), ('RTP', 'right_trackpad'))
CHANGED = {'LST: Entry Point', 'RST: Entry Point', 'RTP: Entry Point', wr.WINDOW, wr.HOLD}


def snapshot(variant, version=BEFORE):
    path = ROOT / f'versions/neptune/{version}/single-set-{variant}_hold-gyro_{version}.json'
    return json.loads(path.read_text(encoding='utf-8'))


def shape(layout, title, source, name):
    """One input's entries without the reference style: (activation type, settings, layer commands or outputs)."""
    slot = layout.active(title)[source]['inputs'][name]
    return [(kind, e.get('settings') or {}, layout.layer_ops(e) or actions(e)) for kind, e in entries(slot['activators'])]


class WindowReleasesAndTapCoverResetsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data, cls.layouts, cls.numeric = {}, {}, {}
        for variant in ('default', 'alternative'):
            data = cls.data[variant] = wr.Builder(variant).finish()
            apply_all(data)
            cls.layouts[variant] = Layout(data)
            numeric, _ = titles_to_ids(json.dumps(data), generate_lookup(data))
            cls.numeric[variant] = json.loads(numeric)

    def each(self):
        for variant, layout in self.layouts.items():
            with self.subTest(variant=variant):
                yield variant, layout

    def title(self, variant, title):
        return map_title(title, wr.RENAME) if variant == 'alternative' else title

    def test_the_90_30_snapshot_is_this_build(self):
        # The working layouts were this build until 90.31. The newest build's test holds R156.
        for variant in self.data:
            with self.subTest(variant=variant):
                built = copy.deepcopy(self.numeric[variant]['controller_mappings'])
                saved = json.loads((ROOT / f'versions/neptune/90.30/single-set-{variant}_hold-gyro_90.30.json').read_text())[
                    'controller_mappings']
                for cm in (built, saved):
                    cm.pop('title'); cm.pop('description')
                self.assertEqual(built, saved)

    def test_the_pad_window_gives_the_four_buttons_a_release_that_ends_the_window_first(self):
        # The author, on the Deck with 90.29: a pad touch and a menu button together, and the next press was in
        # the Fn layer at once. The window covered the button's Release (R136's touchpad exception).
        for variant, layout in self.each():
            window, old = layout.active(wr.WINDOW), Layout(snapshot(variant)).active(wr.WINDOW)
            families = ((wr.MENU_BUTTONS, wr.MENU_FAMILY), (MODIFIERS[variant], wr.MODIFIER_FAMILY))
            for buttons, family in families:
                for source, button in buttons:
                    acts = window[source]['inputs'][button]['activators']
                    self.assertEqual(list(acts), ['Full_Press', 'release'], (source, button))
                    self.assertEqual(acts['Full_Press'], old[source]['inputs'][button]['activators']['Full_Press'])   # the press is as it was
                    release = acts['release']
                    self.assertEqual(release['settings'], {'haptic_intensity': '0'})
                    ops = layout.layer_ops(release)
                    self.assertEqual(ops[0], ('remove_layer', wr.WINDOW))                  # the window goes first (R146)
                    self.assertEqual([op for op, _ in ops], ['remove_layer'] * len(ops))
                    self.assertEqual({t for _, t in ops[1:]}, {self.title(variant, t) for t in family})
            # Start and Select still do nothing on a press; the modifier buttons still scroll.
            for source, button in wr.MENU_BUTTONS:
                self.assertEqual(actions(window[source]['inputs'][button]['activators']['Full_Press']), [EMPTY + ', , '])
            presses = [actions(window[s]['inputs'][b]['activators']['Full_Press'])[0] for s, b in MODIFIERS[variant]]
            self.assertEqual([p.split(',')[0] for p in presses], ['mouse_wheel SCROLL_DOWN', 'mouse_wheel SCROLL_UP'])

    def test_the_families_leave_out_the_windows_the_stateful_layers_and_steering(self):
        for variant, layout in self.each():
            windows = set(always_on_layers(layout))
            for family in (wr.MENU_FAMILY, wr.MODIFIER_FAMILY):
                titles = {self.title(variant, t) for t in family}
                self.assertFalse(titles & windows)
                self.assertFalse({t for t in titles if t.startswith('Steering')})
            self.assertNotIn('Menu Keys', wr.MENU_FAMILY)
            # Every other layer of the two button pairs is in a family.
            menu = {t for t in layout.presets if 'Menu' in t} - windows - {'Menu Keys'}
            self.assertEqual(menu, set(wr.MENU_FAMILY))
            l1, r1 = self.title(variant, 'L1'), self.title(variant, 'R1')
            modifier = {t for t in layout.presets if (l1 in t or r1 in t) and not t.startswith('Steering')} - windows
            self.assertEqual(modifier, {self.title(variant, t) for t in wr.MODIFIER_FAMILY})

    def test_the_fallback_hold_leaves_by_up_and_down_only(self):
        # The author, 2026-10-04: "The outer edge shouldn't contain the release that removes that layer."
        for variant, layout in self.each():
            stick = layout.active(wr.HOLD)['joystick']['inputs']
            self.assertEqual(sorted(stick['edge']['activators']), ['Full_Press', 'chord'])       # the reset and the pulse
            for direction in ('dpad_north', 'dpad_south'):
                acts = stick[direction]['activators']
                self.assertEqual(sorted(acts), ['Full_Press', 'chord', 'release'])
                self.assertEqual(layout.layer_ops(acts['release']), [('remove_layer', wr.HOLD)])
            self.assertNotIn('dpad_east', stick)                                                    # A and D come from Steering
            self.assertNotIn('dpad_west', stick)
            releases = {(source, name) for source, group in layout.active(wr.HOLD).items()
                        for name, slot in group.get('inputs', {}).items() for kind, e in entries(slot['activators'])
                        if kind == 'release' and ('remove_layer', wr.HOLD) in layout.layer_ops(e)}
            self.assertEqual(releases, {('joystick', 'dpad_north'), ('joystick', 'dpad_south')})

    def test_the_three_entry_points_touch_is_that_of_90_24(self):
        # The author, 2026-10-04: the Tap Cover reset comes off all three, for now (R120's exception).
        for variant, layout in self.each():
            old = Layout(snapshot(variant, '90.24'))
            for prefix, source in ENTRY_POINTS:
                title = f'{prefix}: Entry Point'
                self.assertEqual(shape(layout, title, source, 'touch'), shape(old, title, source, 'touch'), title)
                self.assertEqual(sorted(layout.active(title)[source]['inputs']['touch']['activators']), ['chord', 'release'])

    def test_against_90_29_only_these_five_layers_change(self):
        for variant in self.data:
            with self.subTest(variant=variant):
                report = changes.diff(snapshot(variant), self.numeric[variant])
                self.assertEqual((report['added'], report['removed']), ([], []))
                self.assertEqual(changes.changed_layers(report), CHANGED)
                # In the window only the four buttons change.
                rows = {(row['source'], row['input']) for row in report['layers'][wr.WINDOW]}
                self.assertEqual(rows, set(wr.MENU_BUTTONS) | set(MODIFIERS[variant]))


if __name__ == '__main__':
    unittest.main()
