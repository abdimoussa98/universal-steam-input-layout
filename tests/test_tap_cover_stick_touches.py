"""The menu Tap Cover's stick touches, checked on the generated candidates.

Builds both variants with the 2026-10-04 builder and runs the fix pipeline, as the install
does (findings/2026-10-04-tap-cover-stick-touches/README.md). These verify saved configuration
contracts, not Steam's runtime scheduling.
"""
import importlib.util
import json
from pathlib import Path
import unittest

from steam_layout import changes
from steam_layout.fixes import apply_all
from steam_layout.model import EMPTY, Layout, actions

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    'tap_cover_stick_touches', ROOT / 'findings/2026-10-04-tap-cover-stick-touches/build_candidate.py')
tc = importlib.util.module_from_spec(spec); spec.loader.exec_module(tc)
st = tc.st

BEFORE = '90.22'
COVER = st.COVER
TRIO = {'joystick': 'LST', 'right_joystick': 'RST'}
PARTS = ('Entry Point', 'Tap Cover', 'Temporary Gyro')


class TapCoverStickTouchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data, cls.layouts = {}, {}
        for variant in ('default', 'alternative'):
            data = cls.data[variant] = tc.Builder(variant).finish()
            apply_all(data)
            cls.layouts[variant] = Layout(data)

    def each(self):
        for variant, layout in self.layouts.items():
            with self.subTest(variant=variant):
                yield variant, layout

    def acts(self, layout, layer, source, name):
        return layout.active(layer)[source]['inputs'][name]['activators']

    def test_the_cover_binds_both_stick_touches_itself(self):                        # R116
        for variant, layout in self.each():
            for stick_side, source in st.STICKS.items():
                group = layout.active(COVER)[source]
                self.assertEqual((group['mode'], list(group['inputs'])), ('dpad', ['edge', 'touch']))
                # Empty edges, as before: no guard can be added on top of the cover.
                self.assertEqual(actions(group['inputs']['edge']['activators']['Full_Press']), [EMPTY + ', , '])
                touch = self.acts(layout, COVER, source, 'touch')
                self.assertEqual(set(touch), {'Full_Press', 'chord', 'release'})                 # three entries (R108)
                self.assertEqual(touch['release']['settings'], {'haptic_intensity': '0'})
                # The Release clears that side's trio. It doesn't add the cover, which is already on.
                self.assertEqual(layout.layer_ops(touch['release']),
                                 [('remove_layer', f'{TRIO[source]}: {part}') for part in PARTS])

    def test_its_cleanup_is_the_stick_guards(self):                                  # R133
        stale = {('remove_layer', t) for t in [COVER] + [st.guard(s) for s in st.STICKS]
                 + [st.entry_point(side) for side in st.MENU]
                 + [f'Stateful | Menu {side}: Entry Point' for side in st.MENU]}
        for variant, layout in self.each():
            for source in st.STICKS.values():
                touch = self.acts(layout, COVER, source, 'touch')
                for stick_side in st.STICKS:
                    guard = self.acts(layout, st.guard(stick_side), source, 'touch')
                    self.assertEqual((touch['Full_Press'], touch['chord']), (guard['Full_Press'], guard['chord']))
                # Guarded recovery: repeating and interruptible, under a chord on either menu button.
                self.assertEqual(touch['Full_Press']['settings'], {'hold_repeats': '1'})
                self.assertEqual(set(layout.layer_ops(touch['Full_Press'])), stale)
                self.assertEqual(actions(touch['chord']), [EMPTY + ', , '])
                self.assertEqual(touch['chord']['settings'], {
                    'gyro_ratchet_button_mask': str(st.MENU_ANY), 'gyro_ratchet_button_requireany_or_all': '0',
                    'interruptable': '0'})

    def test_what_changed_since_the_last_release(self):
        for variant, data in self.data.items():
            before = json.loads(
                (ROOT / f'versions/neptune/{BEFORE}/single-set-{variant}_hold-gyro_{BEFORE}.json').read_text())
            report = changes.diff(before, data)
            with self.subTest(variant=variant):
                self.assertEqual((report['added'], report['removed']), ([], []))
                self.assertEqual(set(report['layers']), {COVER})                     # one layer, its two stick touches


if __name__ == '__main__':
    unittest.main()
