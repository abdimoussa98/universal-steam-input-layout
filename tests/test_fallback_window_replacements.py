"""The replacements in the fallback's window, on the generated candidates (90.32).

Builds both variants with the 2026-10-04 fallback-window-replacements builder and runs the fix
pipeline, as the install does (findings/2026-10-04-fallback-window-replacements/README.md). These
verify saved configuration contracts, not Steam's runtime scheduling. The press sequences were in
test_scenarios_90_32.py, retired with 90.33 (archived/fallback-window/).
"""
import copy
import importlib.util
import json
from pathlib import Path
import unittest

from tools.convert_runtime_ids import generate_lookup, titles_to_ids
from steam_layout import changes
from steam_layout.fixes import apply_all
from steam_layout.model import Layout, actions, entries

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    'fallback_window_replacements', ROOT / 'findings/2026-10-04-fallback-window-replacements/build_candidate.py')
rp = importlib.util.module_from_spec(spec); spec.loader.exec_module(rp)
fw = rp.fw

BEFORE = '90.31'
# the output each of the four inputs has in the window
OUTPUTS = {
    'default': {('switch', 'button_escape'): 'key_press TAB', ('switch', 'button_menu'): 'key_press ESCAPE',
                ('switch', 'right_bumper'): 'mouse_wheel SCROLL_UP', ('switch', 'left_bumper'): 'mouse_wheel SCROLL_DOWN'},
    'alternative': {('switch', 'button_escape'): 'key_press TAB', ('switch', 'button_menu'): 'key_press ESCAPE',
                    ('right_trigger', 'edge'): 'mouse_wheel SCROLL_UP', ('left_trigger', 'edge'): 'mouse_wheel SCROLL_DOWN'},
}
# every way the window changes a layer: its timer and the Releases that take the Fallback Hold along
EXITS = {('switch', 'always_on_action', 'Full_Press'), ('joystick', 'dpad_north', 'release'), ('joystick', 'dpad_south', 'release'),
         ('joystick', 'edge', 'release'), ('joystick', 'touch', 'release'), ('right_joystick', 'touch', 'release'),
         ('right_trackpad', 'touch', 'release')}


def snapshot(variant, version=BEFORE):
    path = ROOT / f'versions/neptune/{version}/single-set-{variant}_hold-gyro_{version}.json'
    return json.loads(path.read_text(encoding='utf-8'))


def shape(layout, title):
    """A layer's binds without the reference style: {(source, input): [(activation type, settings, commands or outputs)]}."""
    return {(source, name): [(kind, e.get('settings') or {}, layout.layer_ops(e) or actions(e))
                             for kind, e in entries(slot.get('activators', {}))]
            for source, group in layout.active(title).items() for name, slot in group.get('inputs', {}).items()}


class FallbackWindowReplacementsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data, cls.layouts, cls.numeric = {}, {}, {}
        for variant in ('default', 'alternative'):
            data = cls.data[variant] = rp.Builder(variant).finish()
            apply_all(data)
            cls.layouts[variant] = Layout(data)
            numeric, _ = titles_to_ids(json.dumps(data), generate_lookup(data))
            cls.numeric[variant] = json.loads(numeric)

    def each(self):
        for variant, layout in self.layouts.items():
            with self.subTest(variant=variant):
                yield variant, layout

    def test_the_90_32_snapshot_is_this_build(self):
        # The working layouts were this build until 90.33. The newest build's test holds R156.
        for variant in self.data:
            with self.subTest(variant=variant):
                built = copy.deepcopy(self.numeric[variant]['controller_mappings'])
                saved = json.loads((ROOT / f'versions/neptune/90.32/single-set-{variant}_hold-gyro_90.32.json').read_text())[
                    'controller_mappings']
                for cm in (built, saved):
                    cm.pop('title'); cm.pop('description')
                self.assertEqual(built, saved)

    def test_in_the_window_the_drivers_scroll_and_the_menu_buttons_type_their_keys(self):
        # The author, 2026-10-04: "we should just be blocking until the window is completed ... tab and escape ...
        # can be an override. And then we can have the bumpers be scroll override."
        for variant, layout in self.each():
            window = layout.active(fw.WINDOW)
            for (source, name), output in OUTPUTS[variant].items():
                acts = window[source]['inputs'][name]['activators']
                self.assertEqual(list(acts), ['Full_Press'], (source, name))
                self.assertEqual([a.split(',')[0] for a in actions(acts['Full_Press'])], [output], (source, name))
                self.assertEqual(layout.layer_ops(acts['Full_Press']), [], (source, name))

    def test_only_the_timer_and_the_releases_change_a_layer_in_the_window(self):
        for variant, layout in self.each():
            found = {(source, name, kind) for source, group in layout.active(fw.WINDOW).items()
                     for name, slot in group.get('inputs', {}).items()
                     for kind, e in entries(slot.get('activators', {})) if layout.layer_ops(e)}
            self.assertEqual(found, EXITS)
            for source, name, kind in EXITS - {('switch', 'always_on_action', 'Full_Press')}:
                ops = layout.layer_ops(layout.active(fw.WINDOW)[source]['inputs'][name]['activators'][kind])
                self.assertEqual(ops[:2], [('remove_layer', fw.WINDOW), ('remove_layer', fw.HOLD)], (source, name))

    def test_the_fallback_hold_is_as_it_was(self):
        # A driver or a menu button after the second still clears the Steering layers, with a repeating bind:
        # that bind also answers a button that was pressed inside the second and is still held when it ends.
        for variant, layout in self.each():
            self.assertEqual(shape(layout, fw.HOLD), shape(Layout(snapshot(variant)), fw.HOLD))
            hold = layout.active(fw.HOLD)
            for source, name in OUTPUTS[variant]:
                press = hold[source]['inputs'][name]['activators']['Full_Press']
                self.assertEqual(press['settings'].get('hold_repeats'), '1')
                self.assertEqual(layout.layer_ops(press)[-1], ('remove_layer', fw.STEERING))

    def test_against_90_31_only_the_four_inputs_of_the_window_change(self):
        for variant in self.data:
            with self.subTest(variant=variant):
                report = changes.diff(snapshot(variant), self.numeric[variant])
                self.assertEqual((report['added'], report['removed']), ([], []))
                self.assertEqual(changes.changed_layers(report), {fw.WINDOW})
                rows = {(row['source'], row['input']) for row in report['layers'][fw.WINDOW]}
                self.assertEqual(rows, set(OUTPUTS[variant]))


if __name__ == '__main__':
    unittest.main()
