"""The standard hold delays, the pad clicks' reset and the touch layers' ring, on the generated candidates (90.26).

Builds both variants with the 2026-10-04 standard-delays builder and runs the fix pipeline, as
the install does (findings/2026-10-04-standard-delays/README.md). These verify saved
configuration contracts, not Steam's runtime scheduling; the press sequences are in
test_scenarios_90_26.py.

A "hold" here is a delayed `add_layer` with a reset on the same input: a Hold to Repeat entry
that removes only the layer the delay adds (R120).
"""
import copy
import importlib.util
import json
from pathlib import Path
import unittest

from tools.convert_runtime_ids import generate_lookup, titles_to_ids
from steam_layout.fixes import apply_all
from steam_layout.model import Layout, entries, map_title

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    'standard_delays', ROOT / 'findings/2026-10-04-standard-delays/build_candidate.py')
sd = importlib.util.module_from_spec(spec); spec.loader.exec_module(sd)

BEFORE = '90.25'
RAMP = 'Ramp Up'
# layer, source, input: the holds the author named (2026-10-04), by the default layout's titles
AT_200 = (('L1: Modifier 0', 'L1: Temp Cursor Gyro'), ('R1: Modifier 1', 'R1: Temp Cursor Gyro'),
          ('Gyro | L1: Modifier 0', 'L1: Temp Cursor Gyro'), ('Gyro | R1: Modifier 1', 'R1: Temp Cursor Gyro'),
          ('L1!R1: Modifier 2', 'L1&R1: Tap Cover'), ('R1!L1: Modifier 2', 'L1&R1: Tap Cover'),
          ('Steering | LS Down: Modifier 0', 'Steering | LS: Tap Cover'),
          ('Steering | LS Up: Modifier 1', 'Steering | LS: Tap Cover'),
          ('Steering | L1!R1: Modifier 2', 'R1: Tap Cover'), ('Steering | R1!L1: Modifier 2', 'L1: Tap Cover'),
          ('Menu Left: Entry Point', 'Menu Left: Fn Layer'), ('Menu Right: Entry Point', 'Menu Right: Fn Layer'),
          ('Menu Left!Right: Entry Point', 'Menu Keys'), ('Menu Right!Left: Entry Point', 'Menu Keys'))
AT_150 = (('L1: Scroll Down', 'L1: Double Tap Cover'), ('Menu Left: Escape', 'Menu Left: Double Tap Cover'),
          ('Menu Left!Right: Enter', 'Menu Left!Right: Double Tap Cover'),
          ('LST: Entry Point', 'LST: Tap Cover'), ('RST: Entry Point', 'RST: Tap Cover'),
          ('RTP: Entry Point', 'RTP: Tap Cover'))


def snapshot(variant):
    path = ROOT / f'versions/neptune/{BEFORE}/single-set-{variant}_hold-gyro_{BEFORE}.json'
    return json.loads(path.read_text(encoding='utf-8'))


def holds(layout):
    """{(layer, target, input): (delay, reset rate)} for every delayed add that has a reset, the ramp-ups included."""
    found = {}
    for title in layout.presets:
        for source, group in layout.active(title).items():
            for name, slot in group.get('inputs', {}).items():
                each = [(entry.get('settings') or {}, layout.layer_ops(entry)) for _, entry in entries(slot.get('activators', {}))]
                for settings, ops in each:
                    delay = int(settings.get('delay_start') or 0)
                    for target in [layer for op, layer in ops if op == 'add_layer'] if delay else []:
                        for reset, removed in each:
                            if reset.get('hold_repeats') == '1' and removed == [('remove_layer', target)]:
                                found[(title, target, f'{source}/{name}')] = (delay, int(reset['repeat_rate']))
    return found


def leaves(value, path=()):
    if isinstance(value, dict):
        for key, inner in value.items():
            yield from leaves(inner, path + (key,))
    elif isinstance(value, list):
        for index, inner in enumerate(value):
            yield from leaves(inner, path + (index,))
    else:
        yield path, value


class StandardDelaysTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data, cls.layouts, cls.numeric = {}, {}, {}
        for variant in ('default', 'alternative'):
            data = cls.data[variant] = sd.Builder(variant).finish()
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

    def test_working_layouts_are_this_build(self):
        # neptune/ is generated: a hand edit there would be lost on the next install (R156).
        for variant in self.data:
            with self.subTest(variant=variant):
                built = copy.deepcopy(self.numeric[variant]['controller_mappings'])
                working = json.loads((ROOT / f'neptune/single-set-{variant}_hold-gyro_latest.json').read_text())[
                    'controller_mappings']
                for cm in (built, working):
                    cm.pop('title'); cm.pop('description')
                self.assertEqual(built, working)

    def test_what_changed_since_90_25_is_the_timers_and_the_four_pad_layers(self):
        for variant in self.data:
            with self.subTest(variant=variant):
                before = dict(leaves(snapshot(variant)['controller_mappings']))
                after = dict(leaves(self.numeric[variant]['controller_mappings']))
                gone = {path: before[path] for path in set(before) - set(after)}
                self.assertEqual(sorted((path[-1], value) for path, value in gone.items()),
                                 [('delay_start', '5')] * 2)                 # the touch layers' outer bind
                new = set(after) - set(before)
                self.assertEqual(len(new), 10)                               # two resets of five values each
                self.assertTrue(all('touch' in path and 'Full_Press' in path for path in new))
                changed = {path[-1] for path in set(before) & set(after) if before[path] != after[path]}
                self.assertEqual(changed, {'title', 'description', 'delay_start', 'repeat_rate', 'activation_threshold'})

    def test_no_hold_delay_is_over_200_ms(self):
        for variant, layout in self.each():
            found = {key: pair for key, pair in holds(layout).items() if RAMP not in key[0]}
            self.assertEqual(len(found), 31)
            self.assertEqual({delay for delay, _ in found.values()}, {150, sd.HOLD_MS})

    def test_every_reset_repeats_50_ms_after_its_delay(self):                               # R121
        for variant, layout in self.each():
            for (title, target, where), (delay, rate) in holds(layout).items():
                if RAMP not in title:
                    self.assertEqual(rate, delay + sd.RESET_MARGIN_MS, (title, target, where))

    def test_the_holds_the_author_named(self):
        for variant, layout in self.each():
            found = {key[:2]: pair for key, pair in holds(layout).items()}
            for group, delay in ((AT_200, 200), (AT_150, 150)):
                for title, target in group:
                    key = (self.title(variant, title), self.title(variant, target))
                    self.assertEqual(found[key], (delay, delay + 50), key)

    def test_the_ramp_up_layers_are_untouched(self):
        for variant, layout in self.each():
            before = Layout(snapshot(variant))
            after = Layout(self.numeric[variant])
            ramps = [title for title in after.presets if RAMP in title]
            self.assertEqual(len(ramps), 3)
            for title in ramps:
                self.assertEqual(after.active(title), before.active(title), title)
            self.assertEqual({pair for key, pair in holds(layout).items() if RAMP in key[0]}, {(250, 300)})

    def test_a_delay_with_no_reset_is_not_a_hold_and_keeps_its_time(self):
        # The ring binds' 5 ms, the windows' own timers and the 1500 ms Fallback Hold.
        for variant in self.data:
            with self.subTest(variant=variant):
                def delays(data):
                    return sorted(value for path, value in leaves(data['controller_mappings']) if path[-1] == 'delay_start')
                before, after = delays(snapshot(variant)), delays(self.numeric[variant])
                self.assertEqual(before.count('1500'), 2)
                for value in ('50', '1500'):
                    self.assertEqual(after.count(value), before.count(value), value)
                self.assertEqual(after.count('5'), before.count('5') - 2)    # the touch layers' outer binds

    # --- the pads ---------------------------------------------------------------------------

    def ring(self, layout, title, source):
        return layout.active(title)[source]['inputs']['edge']['activators']['Soft_Press']

    def test_the_click_entry_points_outer_bind_has_its_reset_on_the_touch(self):            # R120
        for variant, layout in self.each():
            before = Layout(snapshot(variant))
            for title, source, target in sd.CLICK_LAYERS:
                inner, outer = self.ring(layout, title, source)
                self.assertEqual(outer['settings']['delay_start'], '5')
                self.assertIn(('add_layer', target), layout.layer_ops(outer))
                touch = layout.active(title)[source]['inputs']['touch']['activators']
                self.assertEqual(list(touch), ['release', 'Full_Press'])
                reset = touch['Full_Press']
                self.assertEqual(layout.layer_ops(reset), [('remove_layer', target)])
                self.assertEqual(reset['settings'], {'hold_repeats': '1', 'repeat_rate': '55', 'interruptable': '0',
                                                     'haptic_intensity': '0'})
                was = before.active(title)[source]['inputs']
                self.assertEqual(layout.layer_ops(touch['release']), before.layer_ops(was['touch']['activators']['release']))
                for now, then in zip((inner, outer), was['edge']['activators']['Soft_Press']):
                    self.assertEqual((now['settings'], layout.layer_ops(now)), (then['settings'], before.layer_ops(then)))

    def test_the_touch_layers_two_ring_binds_meet_and_neither_waits(self):
        for variant, layout in self.each():
            for title, source in sd.TOUCH_LAYERS:
                inner, outer = self.ring(layout, title, source)
                click_inner, _ = self.ring(layout, title.replace('Touch', 'Click'), source)
                self.assertEqual(inner['settings'], {**click_inner['settings'], 'haptic_intensity': '1'})
                self.assertEqual(outer['settings'], {'hold_repeats': '1', 'repeat_rate': '50', 'haptic_intensity': '0',
                                                     'activation_threshold': inner['settings']['activation_threshold'],
                                                     'interruptable': '0'})        # the inner one's radius, no delay
                self.assertEqual(layout.layer_ops(outer), layout.layer_ops(inner))
                self.assertEqual(list(layout.active(title)[source]['inputs']['touch']['activators']), ['release'])


if __name__ == '__main__':
    unittest.main()
