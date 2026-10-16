"""Steering base's open edges, its four-way stick and the add at once, on the generated candidates (90.34).

Builds both variants with the 2026-10-05 steering-four-way-and-open-edges builder and runs the fix
pipeline, as the install does (findings/2026-10-05-steering-four-way-and-open-edges/README.md).
These verify saved configuration contracts, not Steam's runtime scheduling; the press sequences
are in test_scenarios_90_34.py and test_scenarios_90_33.py.
"""
import copy
import importlib.util
import json
from pathlib import Path
import unittest

from tools.convert_runtime_ids import generate_lookup, titles_to_ids
from steam_layout import changes
from steam_layout.fixes import apply_all
from steam_layout.model import Layout, entries, map_title

ROOT = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location(
    'steering_four_way', ROOT / 'findings/2026-10-05-steering-four-way-and-open-edges/build_candidate.py')
fw4 = importlib.util.module_from_spec(spec); spec.loader.exec_module(fw4)
fg = fw4.fg

BEFORE = '90.33'
STICKS = ('joystick', 'right_joystick')
KEYS = {'dpad_north': 'W', 'dpad_south': 'S'}
COVERS = ('Steering | LS: Double Tap Cover', 'Steering | LS: Tap Cover')    # only ever over a driver's layer
WINDOWS = ('Steering | LS Up: Double Tap', 'Steering | LS Down: Double Tap')
MODIFIER_WINDOWS = ('L1: Double Tap', 'R1: Double Tap')
# What the editor can set (resources/Steam Input JSON Structure.md, "Limits the Steam editor sets").
MAX_MS = 1000
DPAD_RADIUS = (10000, 32000)
DPAD_LAYOUTS = {'0', '1', '2', '3'}     # Radial Without Overlap, Radial With Overlap, Analog Emulation, Cross Gate


def snapshot(variant, version=BEFORE):
    path = ROOT / f'versions/neptune/{version}/single-set-{variant}_hold-gyro_{version}.json'
    return json.loads(path.read_text(encoding='utf-8'))


def shape(layout, title, source):
    """One source of a layer without the reference style: {input: [(activation type, settings, commands)]}."""
    return {name: [(kind, e.get('settings') or {}, layout.layer_ops(e)) for kind, e in entries(slot.get('activators', {}))]
            for name, slot in layout.active(title)[source].get('inputs', {}).items()}


class SteeringFourWayAndOpenEdgesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data, cls.layouts, cls.numeric = {}, {}, {}
        for variant in ('default', 'alternative'):
            data = cls.data[variant] = fw4.Builder(variant).finish()
            apply_all(data)
            cls.layouts[variant] = Layout(data)
            numeric, _ = titles_to_ids(json.dumps(data), generate_lookup(data))
            cls.numeric[variant] = json.loads(numeric)

    def each(self):
        for variant, layout in self.layouts.items():
            with self.subTest(variant=variant):
                yield variant, layout

    def title(self, variant, title):
        return map_title(title, fg.RENAME) if variant == 'alternative' else title

    def test_the_90_34_snapshot_is_this_build(self):
        # The working layouts were this build until 90.35. The newest build's test holds R156.
        for variant in self.data:
            with self.subTest(variant=variant):
                built = copy.deepcopy(self.numeric[variant]['controller_mappings'])
                saved = json.loads((ROOT / f'versions/neptune/90.34/single-set-{variant}_hold-gyro_90.34.json').read_text())[
                    'controller_mappings']
                for cm in (built, saved):
                    cm.pop('title'); cm.pop('description')
                self.assertEqual(built, saved)

    def test_steering_base_and_the_guard_leave_both_edges_open_and_the_other_steering_layers_do_not(self):
        # The author, 2026-10-05: "update the steering base to no longer block the edge binds for left or right
        # stick. I want that to be blocked in the other steering layers"; and "the fallback is not one that would
        # get the edges blocked."
        for variant, layout in self.each():
            steering = [t for t in layout.presets if t == fg.STEERING or t.startswith('Steering | ')]
            self.assertEqual(len(steering), 12)
            is_open = {source: {t for t in steering if 'edge' not in layout.active(t).get(source, {}).get('inputs', {})}
                       for source in STICKS}
            self.assertEqual(is_open['joystick'], {fg.STEERING, fg.GUARD})
            # The two stick covers leave the right edge to the driver's layer under them, which binds it.
            self.assertEqual(is_open['right_joystick'], {fg.STEERING, fg.GUARD, *COVERS})
            for cover in COVERS:
                adders = {t for t in layout.presets for g in layout.active(t).values() for slot in g.get('inputs', {}).values()
                          for _, e in entries(slot.get('activators', {})) if ('add_layer', cover) in layout.layer_ops(e)}
                self.assertTrue(adders and not adders & {fg.STEERING, fg.GUARD}, cover)

    def test_steering_base_is_four_way_and_the_guard_states_eight_way(self):
        # The numbers are the Steam client's: its choices list RadialWithOverlap as 1 and RadialNoOverlap as 0.
        for variant, layout in self.each():
            self.assertEqual(layout.active(fg.STEERING)['joystick']['settings'].get('layout'), '0')
            self.assertEqual(layout.active(fg.GUARD)['joystick']['settings'].get('layout'), '1')
            for title in layout.presets:                                    # no other Steering layer states one
                if title.startswith('Steering | ') and title != fg.GUARD:
                    self.assertNotIn('layout', layout.active(title)['joystick'].get('settings') or {}, title)
            for title in layout.presets:                                    # R173: a value the editor offers
                for group in layout.active(title).values():
                    if group['mode'] == 'dpad' and 'layout' in (group.get('settings') or {}):
                        self.assertIn(group['settings']['layout'], DPAD_LAYOUTS, title)
            # everything else on the two sticks' groups is as in 90.33
            old = Layout(snapshot(variant))
            for title in (fg.STEERING, fg.GUARD):
                before = dict(old.active(title)['joystick']['settings'])
                after = dict(layout.active(title)['joystick']['settings']); after.pop('layout')
                self.assertEqual(after, before, title)

    def test_up_and_down_add_the_guard_at_once_with_a_repeating_press_and_the_pulse(self):
        # The author, 2026-10-05: "the fall back layer should be triggered in the base steering layer by pushing
        # up or down on left stick with a repeated add layer."
        for variant, layout in self.each():
            for direction in KEYS:
                acts = layout.active(fg.STEERING)['joystick']['inputs'][direction]['activators']
                self.assertEqual(list(acts), ['Full_Press'])
                self.assertEqual(layout.layer_ops(acts['Full_Press']), [('add_layer', fg.GUARD)])
                self.assertEqual(acts['Full_Press']['settings'], {
                    'hold_repeats': '1', 'repeat_rate': '50', 'interruptable': '0', 'haptic_intensity': '3'})
            delayed = [(source, name) for source, group in layout.active(fg.STEERING).items()
                       for name, slot in group.get('inputs', {}).items() for _, e in entries(slot.get('activators', {}))
                       if 'delay_start' in (e.get('settings') or {})]
            self.assertEqual(delayed, [])                                   # nothing left for R120 to ask a reset for

    def test_the_guards_binds_are_those_of_90_33(self):
        # The author, 2026-10-05: "in the fallback the gyro mod 0&1 will be chorded based on the stick being
        # deflected and there will be a repeated removal regular press to remove the fallback layer." Built in 90.33.
        for variant, layout in self.each():
            old = Layout(snapshot(variant))
            for source in layout.active(fg.GUARD):
                self.assertEqual(shape(layout, fg.GUARD, source), shape(old, fg.GUARD, source), source)

    def test_no_stick_states_a_radius_the_editor_cannot_set(self):
        for variant, layout in self.each():                                  # R173
            for title in layout.presets:
                for source in STICKS:
                    group = layout.active(title).get(source)
                    radius = ((group or {}).get('settings') or {}).get('edge_binding_radius')
                    if radius is not None and group['mode'] == 'dpad':
                        self.assertTrue(DPAD_RADIUS[0] <= int(radius) <= DPAD_RADIUS[1], (title, source, radius))

    def test_no_delay_or_repeat_rate_is_over_the_editors_1000_ms(self):
        for variant, layout in self.each():                                  # R173
            over = [(title, source, name, key, e['settings'][key])
                    for title in layout.presets for source, group in layout.active(title).items()
                    for name, slot in group.get('inputs', {}).items() for _, e in entries(slot.get('activators', {}))
                    for key in ('delay_start', 'delay_end', 'repeat_rate')
                    if key in (e.get('settings') or {}) and int(e['settings'][key]) > MAX_MS]
            self.assertEqual(over, [])

    def test_against_90_33_the_change_is_steering_the_guard_and_what_the_window_fix_wrote(self):
        # With turn assist back in Steering base a ramp stage can be under a window again, so the fix pipeline
        # writes the firing buttons' mouse buttons into the two Steering stick windows, as it did until 90.12.
        # In the alternative layout it also blocks a trigger's full pull in the two modifier windows: the ramp
        # stages remove themselves there, and a guard that lands over a stage lets a modifier tap through.
        for variant in self.data:
            with self.subTest(variant=variant):
                report = changes.diff(snapshot(variant), self.numeric[variant])
                self.assertEqual((report['added'], report['removed']), ([], []))
                expected = {fg.STEERING, fg.GUARD, *WINDOWS}
                if variant == 'alternative':
                    expected |= {self.title(variant, t) for t in MODIFIER_WINDOWS}
                self.assertEqual(changes.changed_layers(report), expected)
                layout = self.layouts[variant]
                firing = ('left_trigger', 'right_trigger') if variant == 'default' else ('switch',)
                for window in WINDOWS:
                    rows = {(row['source'], row['input']) for row in report['layers'][window]}
                    self.assertTrue(rows and all(source in firing for source, _ in rows), rows)
                    for source, name in rows:
                        press = layout.active(window)[source]['inputs'][name]['activators']['Full_Press']
                        self.assertEqual(layout.layer_ops(press), [])       # an output, no layer command


if __name__ == '__main__':
    unittest.main()
