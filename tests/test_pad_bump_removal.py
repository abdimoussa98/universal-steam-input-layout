"""The pad touch bump is out again: the pads of 90.24, on the generated candidates (90.27).

Builds both variants with the 2026-10-04 pad-bump-removal builder and runs the fix pipeline, as
the install does (findings/2026-10-04-pad-bump-removal/README.md). How the bump was built is
recorded in findings/2026-10-04-pad-touch-bump/README.md. These verify saved configuration
contracts, not Steam's runtime scheduling; the press sequences are in test_scenarios_90_27.py.
"""
import copy
import importlib.util
import json
from pathlib import Path
import unittest

from tools.convert_runtime_ids import generate_lookup, titles_to_ids
from steam_layout import changes
from steam_layout.fixes import apply_all
from steam_layout.model import Layout, actions, entries, map_title

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    'pad_bump_removal', ROOT / 'findings/2026-10-04-pad-bump-removal/build_candidate.py')
br = importlib.util.module_from_spec(spec); spec.loader.exec_module(br)

PADS = ('right_trackpad', 'left_trackpad')
# the layers 90.27 changes against 90.26, by the default layout's titles
CLEARS = ('Menu Left: Entry Point', 'Menu Right: Entry Point', 'Stateful | Menu Left: Entry Point',
          'Stateful | Menu Right: Entry Point', 'Steering | R1!L1: Modifier 2', 'Steering | L1!R1: Modifier 2', 'Gamepad',
          'Menu Left!Right: Entry Point', 'Menu Right!Left: Entry Point', 'Menu Keys')
PAD_LAYERS = ('Base', 'RTP: Entry Point', 'Steering', 'LTP: Click Entry Point', 'LTP: Middle Click', 'LTP: Arrow Keys')


def snapshot(variant, version):
    path = ROOT / f'versions/neptune/{version}/single-set-{variant}_hold-gyro_{version}.json'
    return json.loads(path.read_text(encoding='utf-8'))


def shape(layout, title, source):
    """A layer's group for one pad without its reference style: mode, settings and each input's entries."""
    group = layout.active(title).get(source)
    if group is None:
        return None
    found = {'mode': group.get('mode'), 'settings': {k: v for k, v in (group.get('settings') or {}).items() if k != 'layer'}}
    for name, slot in group.get('inputs', {}).items():
        found[name] = [(kind, layout.layer_ops(e), [a for a in actions(e) if 'controller_action' not in a], e.get('settings') or {})
                       for kind, e in entries(slot.get('activators', {}))]
    return found


class PadBumpRemovalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data, cls.layouts, cls.numeric = {}, {}, {}
        for variant in ('default', 'alternative'):
            data = cls.data[variant] = br.Builder(variant).finish()
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

    def test_the_90_27_snapshot_is_this_build(self):
        # The working layouts were this build until 90.28. The newest build's test holds R156.
        for variant in self.data:
            with self.subTest(variant=variant):
                built = copy.deepcopy(self.numeric[variant]['controller_mappings'])
                saved = json.loads((ROOT / f'versions/neptune/90.27/single-set-{variant}_hold-gyro_90.27.json').read_text())[
                    'controller_mappings']
                for cm in (built, saved):
                    cm.pop('title'); cm.pop('description')
                self.assertEqual(built, saved)

    def test_the_three_layers_are_gone_and_the_others_keep_their_order(self):
        self.assertEqual(br.GONE, ('RTP: Touch Entry Point', 'LTP: Touch Entry Point', 'LTP: Entry Point'))
        for variant, layout in self.each():
            before = list(Layout(snapshot(variant, '90.26')).presets)
            self.assertEqual(list(layout.presets), [title for title in before if title not in br.GONE])
            self.assertEqual(len(layout.presets), 88)                       # Base and 87 layers
            keys = list(self.numeric[variant]['controller_mappings']['action_layers'])
            self.assertEqual(keys, sorted(keys))                             # the list order is the Preset_ order (R104)

    def test_the_pads_are_those_of_90_24_but_for_three_later_changes(self):
        later = {('RTP: Entry Point', 'right_trackpad'): ['touch'],         # the Tap Cover reset (90.25)
                 ('RTP: Click Entry Point', 'right_trackpad'): ['touch'],   # the outer bind's reset (90.26)
                 ('LTP: Click Entry Point', 'left_trackpad'): ['touch'],
                 ('RTP: Middle Click', 'right_trackpad'): ['mode']}         # a mouse pad (90.25)
        for variant, layout in self.each():
            old, found = Layout(snapshot(variant, '90.24')), {}
            for title in old.presets:
                for source in PADS:
                    a, b = shape(old, title, source), shape(layout, title, source)
                    if a != b:
                        found[(title, source)] = sorted(k for k in set(a or {}) | set(b or {}) if (a or {}).get(k) != (b or {}).get(k))
            self.assertEqual(found, later)

    def test_base_has_the_clicks_the_swipes_and_the_touch_of_90_24(self):
        for variant, layout in self.each():
            base = layout.active(layout.base)
            right, left = base['right_trackpad'], base['left_trackpad']
            self.assertEqual((right['mode'], sorted(right['inputs'])), ('absolute_mouse', ['click', 'touch']))
            touch = right['inputs']['touch']['activators']['Full_Press']
            self.assertEqual(layout.layer_ops(touch), [('add_layer', 'RTP: Entry Point')])
            for group, target in ((right, 'RTP: Click Entry Point'), (left, 'LTP: Click Entry Point')):
                click = group['inputs']['click']['activators']['Soft_Press']
                self.assertEqual((layout.layer_ops(click), click['settings']), ([('add_layer', target)], {'haptic_intensity': '3'}))
            self.assertEqual(left['mode'], '2dscroll')
            self.assertEqual({name: layout.layer_ops(slot['activators']['Full_Press'])[0][1]
                              for name, slot in left['inputs'].items() if name != 'click'},
                             {'dpad_west': 'Escape', 'dpad_east': 'Enter', 'dpad_north': 'Tab', 'dpad_south': 'Backspace'})

    def test_no_other_layer_has_a_copy_of_the_click(self):
        for variant, layout in self.each():
            for title in ('RTP: Entry Point', 'RTP: Tap Cover', 'Steering'):
                self.assertNotIn('click', layout.active(title)['right_trackpad']['inputs'], title)

    def test_what_stays_from_90_25_and_90_26(self):
        for variant, layout in self.each():
            self.assertEqual(layout.active('RTP: Middle Click')['right_trackpad']['mode'], 'absolute_mouse')
            for title, source, target, rate in (('RTP: Entry Point', 'right_trackpad', 'RTP: Tap Cover', '200'),
                                                ('LST: Entry Point', 'joystick', 'LST: Tap Cover', '200'),
                                                ('RST: Entry Point', 'right_joystick', 'RST: Tap Cover', '200'),
                                                ('RTP: Click Entry Point', 'right_trackpad', 'RTP: Mouse Buttons', '55'),
                                                ('LTP: Click Entry Point', 'left_trackpad', 'LTP: Arrow Keys', '55')):
                reset = layout.active(title)[source]['inputs']['touch']['activators']['Full_Press']
                self.assertEqual((layout.layer_ops(reset), reset['settings']['repeat_rate']), ([('remove_layer', target)], rate), title)
            for title in ('Menu Keys', 'Menu Left!Right: Entry Point', 'Menu Right!Left: Backspace'):
                self.assertIn(title, layout.presets)
            hold = layout.active(self.title(variant, 'L1: Modifier 0'))
            delays = [e['settings'].get('delay_start') for group in hold.values() for slot in group.get('inputs', {}).values()
                      for _, e in entries(slot.get('activators', {})) if (e.get('settings') or {}).get('delay_start')]
            self.assertEqual(delays, ['200'])

    def test_against_90_26_only_the_pad_layers_and_the_clear_lists_change(self):
        for variant in self.data:
            with self.subTest(variant=variant):
                report = changes.diff(snapshot(variant, '90.26'), self.numeric[variant])
                self.assertEqual(sorted(report['removed']), sorted(br.GONE))
                self.assertEqual(report['added'], [])
                expected = {self.title(variant, title) for title in CLEARS + PAD_LAYERS}
                self.assertEqual(set(changes.changed_layers(report)) - set(br.GONE), expected)


if __name__ == '__main__':
    unittest.main()
