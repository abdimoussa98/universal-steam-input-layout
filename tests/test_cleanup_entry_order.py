"""The stored order of the entries on every cleanup input, on the generated candidates (90.36).

Builds both variants with the 2026-10-06 cleanup-entry-order builder and runs the fix pipeline, as
the install does (findings/2026-10-06-cleanup-entry-order/README.md). The order of an input's
entries is the order the Steam editor lists them in. The simulator does not read it, so there are
no scenarios for this release; whether it changes anything is a Deck check (A52).
"""
import copy
import importlib.util
import json
from pathlib import Path
import unittest

from tools.convert_runtime_ids import generate_lookup, titles_to_ids
from steam_layout import changes
from steam_layout.fixes import apply_all
from steam_layout.model import Layout, map_title

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    'cleanup_entry_order', ROOT / 'findings/2026-10-06-cleanup-entry-order/build_candidate.py')
co = importlib.util.module_from_spec(spec); spec.loader.exec_module(co)
fg = co.sw.fg

BEFORE = '90.35'
ENTRY_POINTS = ('Menu Left: Entry Point', 'Menu Right: Entry Point',
                'Stateful | Menu Left: Entry Point', 'Stateful | Menu Right: Entry Point')
SCROLL = ('L1: Scroll Down', 'R1: Scroll Up')
TOUCHES = (('joystick', 'touch'), ('right_joystick', 'touch'))
WANTED = ['Full_Press', 'chord', 'release']


def snapshot(variant, version=BEFORE):
    path = ROOT / f'versions/neptune/{version}/single-set-{variant}_hold-gyro_{version}.json'
    return json.loads(path.read_text(encoding='utf-8'))


def orders(layout):
    """{(layer, source, input): the stored order of its activator types}, for every bound input."""
    return {(title, source, name): list(slot.get('activators', {}))
            for title in layout.presets for source, group in layout.active(title).items()
            for name, slot in group.get('inputs', {}).items()}


class CleanupEntryOrderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data, cls.layouts, cls.numeric = {}, {}, {}
        for variant in ('default', 'alternative'):
            data = cls.data[variant] = co.Builder(variant).finish()
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

    def test_working_layouts_are_this_build_entry_for_entry_and_in_the_same_order(self):
        # neptune/ is generated: a hand edit there would be lost on the next install (R156). Comparing the
        # mappings alone would not see a different order, so the stored orders are compared too.
        for variant in self.data:
            with self.subTest(variant=variant):
                built = copy.deepcopy(self.numeric[variant]['controller_mappings'])
                working_data = json.loads((ROOT / f'neptune/single-set-{variant}_hold-gyro_latest.json').read_text())
                working = copy.deepcopy(working_data['controller_mappings'])
                for cm in (built, working):
                    cm.pop('title'); cm.pop('description')
                self.assertEqual(built, working)
                self.assertEqual(orders(Layout(self.numeric[variant])), orders(Layout(working_data)))

    def test_every_cleanup_input_is_regular_press_then_guard_then_release(self):
        # The author, 2026-10-06: "the order: repeated removal of a regular press, then the guard, then a release.
        # That's how it should always be."
        for variant, layout in self.each():
            inputs = co.cleanup_inputs(layout)
            self.assertGreater(len(inputs), 500)
            for layer, source, name in inputs:
                stored = list(layout.active(layer)[source]['inputs'][name]['activators'])
                self.assertEqual(stored, [kind for kind in WANTED if kind in stored], (layer, source, name))

    def test_the_menu_entry_points_and_the_scroll_layers_have_the_release_last_on_both_stick_touches(self):
        # Since 90.24 the Entry Points had the Release between the Regular Press and its guard, and the author
        # suspects the guard then did not hold the Regular Press back (findings/2026-10-06-menu-entry-point-stick-touches).
        for variant, layout in self.each():
            old = Layout(snapshot(variant))
            for title in map(lambda t: self.title(variant, t), ENTRY_POINTS + SCROLL):
                for source, name in TOUCHES:
                    stored = list(layout.active(title)[source]['inputs'][name]['activators'])
                    self.assertEqual(stored, WANTED, (title, source))
                    self.assertNotEqual(list(old.active(title)[source]['inputs'][name]['activators']), WANTED, (title, source))

    def test_121_inputs_move_and_no_bind_changes(self):
        for variant, layout in self.each():
            old = Layout(snapshot(variant))
            before, after = orders(old), orders(layout)
            self.assertEqual(set(before), set(after))
            moved = [key for key in after if before[key] != after[key]]
            self.assertEqual(len(moved), 121)
            self.assertTrue(set(moved) <= set(co.cleanup_inputs(layout)))
            for key in moved:
                self.assertEqual(sorted(before[key]), sorted(after[key]), key)      # the same types, another order
            # The change report reads the entries in their stored order, so it lists exactly the moved inputs.
            report = changes.diff(snapshot(variant), self.numeric[variant])
            self.assertEqual((report['added'], report['removed']), ([], []))
            self.assertEqual(changes.changed_layers(report), {layer for layer, _, _ in moved})
            rows = {(layer, row['source'], row['input']) for layer, found in report['layers'].items() for row in found}
            self.assertEqual(rows, set(moved))


if __name__ == '__main__':
    unittest.main()
