"""`Steering` and its fallback guard swap places, on the generated candidates (90.35).

Builds both variants with the 2026-10-06 steering-fallback-swap builder and runs the fix pipeline,
as the install does (findings/2026-10-06-steering-fallback-swap/README.md). These verify saved
configuration contracts, not Steam's runtime scheduling; the press sequences are in
test_scenarios_90_35.py.
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

ROOT = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location(
    'steering_fallback_swap', ROOT / 'findings/2026-10-06-steering-fallback-swap/build_candidate.py')
sw = importlib.util.module_from_spec(spec); spec.loader.exec_module(sw)
fg = sw.fg

BEFORE = '90.34'
PAIR = {'default': (('switch', 'left_bumper'), ('switch', 'right_bumper')),
        'alternative': (('left_trigger', 'edge'), ('right_trigger', 'edge'))}
TOUCHES = (('joystick', 'touch'), ('right_joystick', 'touch'))
KEYS = ('dpad_north', 'dpad_south')
OVER = [('add_layer', fg.GUARD), ('remove_layer', fg.STEERING)]         # in the order they run
BACK = [('add_layer', fg.STEERING), ('remove_layer', fg.GUARD)]


def snapshot(variant, version=BEFORE):
    path = ROOT / f'versions/neptune/{version}/single-set-{variant}_hold-gyro_{version}.json'
    return json.loads(path.read_text(encoding='utf-8'))


def flags(entry, command, runtime_id):
    """The two flags of this entry's `command` on the layer with this runtime id, or None."""
    for action in actions(entry):
        parts = action.split(',')[0].split()
        if parts[:3] == ['controller_action', command, str(runtime_id)]:
            return tuple(parts[3:5])
    return None


def every_entry(layout):
    for title in layout.presets:
        for source, group in layout.active(title).items():
            for name, slot in group.get('inputs', {}).items():
                for kind, e in entries(slot.get('activators', {})):
                    yield title, source, name, kind, e


class SteeringFallbackSwapTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data, cls.layouts, cls.numeric = {}, {}, {}
        for variant in ('default', 'alternative'):
            data = cls.data[variant] = sw.Builder(variant).finish()
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

    def acts(self, layout, title, source, name):
        return layout.active(title)[source]['inputs'][name]['activators']

    def ids(self, variant):
        numeric = Layout(self.numeric[variant])
        return numeric, {numeric.titles[key]: number + 1 for number, key in enumerate(numeric.order)}

    def test_the_90_35_snapshot_is_this_build(self):
        # The working layouts were this build until 90.36. The newest build's test holds R156.
        for variant in self.data:
            with self.subTest(variant=variant):
                built = copy.deepcopy(self.numeric[variant]['controller_mappings'])
                saved = json.loads((ROOT / f'versions/neptune/90.35/single-set-{variant}_hold-gyro_90.35.json').read_text())[
                    'controller_mappings']
                for cm in (built, saved):
                    cm.pop('title'); cm.pop('description')
                self.assertEqual(built, saved)

    def test_steerings_up_and_down_add_the_guard_and_then_remove_steering(self):
        # The author, 2026-10-06: "the fallback layer will be added first, then it'll remove the steering layer."
        for variant, layout in self.each():
            for direction in KEYS:
                acts = self.acts(layout, fg.STEERING, 'joystick', direction)
                self.assertEqual(list(acts), ['Full_Press'])
                self.assertEqual(layout.layer_ops(acts['Full_Press']), OVER)
                self.assertEqual(acts['Full_Press']['settings'], {
                    'hold_repeats': '1', 'repeat_rate': '50', 'interruptable': '0', 'haptic_intensity': '3'})

    def test_every_bind_in_the_guard_that_removes_it_adds_steering_first(self):
        # The author, 2026-10-06: "when removing the fallback layer to first add back the steering layer"; and of
        # the stick-touch cleanups, "it would keep them and they would first add steering back and remove fallback."
        for variant, layout in self.each():
            numeric, lookup = self.ids(variant)
            removing = {(source, name): e for title, source, name, kind, e in every_entry(layout)
                        if title == fg.GUARD and ('remove_layer', fg.GUARD) in layout.layer_ops(e)}
            self.assertEqual(set(removing), set(PAIR[variant]) | set(TOUCHES))
            for (source, name), found in removing.items():
                self.assertEqual(layout.layer_ops(found), BACK, (source, name))
                self.assertEqual(found['settings'].get('hold_repeats'), '1', (source, name))
                stored = self.acts(numeric, fg.GUARD, source, name)['Full_Press']
                self.assertEqual(flags(stored, 'add_layer', lookup[fg.STEERING]), ('0', '0'))   # a swap: no beep
            for control in PAIR[variant]:                                   # the chord beside it is 90.33's
                self.assertEqual(sorted(self.acts(layout, fg.GUARD, *control)), ['Full_Press', 'chord'])
            for control in TOUCHES:
                self.assertEqual(sorted(self.acts(layout, fg.GUARD, *control)), ['Full_Press', 'chord', 'release'])

    def test_the_two_only_ever_swap(self):
        # Only the entry adds Steering without taking the guard away, and nothing else adds the guard.
        for variant, layout in self.each():
            adds = {target: {(title, tuple(layout.layer_ops(e))) for title, _, _, _, e in every_entry(layout)
                             if ('add_layer', target) in layout.layer_ops(e)} for target in (fg.STEERING, fg.GUARD)}
            self.assertEqual({title for title, _ in adds[fg.GUARD]}, {fg.STEERING})
            self.assertEqual({ops for _, ops in adds[fg.GUARD]}, {tuple(OVER)})
            self.assertEqual({title for title, _ in adds[fg.STEERING]}, {fg.GUARD, fg.ENTERS})
            self.assertEqual({ops for title, ops in adds[fg.STEERING] if title == fg.GUARD}, {tuple(BACK)})

    def test_the_guard_carries_steerings_menu_buttons_and_right_pad(self):
        # Steering is not under the guard any more, so what the guard took from it is its own.
        for variant, layout in self.each():
            steering, guard = layout.active(fg.STEERING), layout.active(fg.GUARD)
            for name in ('button_menu', 'button_escape'):
                self.assertEqual(guard['switch']['inputs'][name], steering['switch']['inputs'][name], name)
                adds = [t for op, t in layout.layer_ops(guard['switch']['inputs'][name]['activators']['Full_Press'])]
                self.assertTrue(adds[0].startswith('Stateful | Menu '), adds)
            self.assertEqual(guard['right_trackpad']['mode'], steering['right_trackpad']['mode'])
            self.assertEqual(guard['right_trackpad']['settings'], steering['right_trackpad']['settings'])
            self.assertEqual(guard['right_trackpad']['inputs'], steering['right_trackpad']['inputs'])
            self.assertEqual(guard['joystick']['settings'].get('layout'), '1')      # eight-way, with nothing four-way under it
            self.assertEqual(steering['joystick']['settings'].get('layout'), '0')

    def test_the_quick_tap_beeps_on_whichever_of_the_two_is_on(self):
        for variant, layout in self.each():
            numeric, lookup = self.ids(variant)
            for tap in (self.title(variant, t) for t in fg.GYRO_QUICK_TAPS):
                for control in PAIR[variant]:
                    stored = self.acts(numeric, tap, *control)['release']
                    self.assertEqual(flags(stored, 'remove_layer', lookup[fg.GUARD]), ('0', '1'))
                    self.assertEqual(flags(stored, 'remove_layer', lookup[fg.STEERING]), ('0', '1'))

    def test_a_drivers_press_removes_the_ramp_layers_before_it_adds_its_layer(self):
        # The driver's layer binds the right stick's edge, where a ramp layer ends. One left under it kept the
        # gyro off until the driver was let go.
        for variant, layout in self.each():
            for control in PAIR[variant]:
                press = self.acts(layout, fg.STEERING, *control)['Full_Press']
                ops = layout.layer_ops(press)
                self.assertEqual(ops[:3], [('remove_layer', title) for title in sw.RAMP])
                self.assertEqual((len(ops), ops[3][0]), (4, 'add_layer'))
                self.assertTrue(ops[3][1].startswith('Steering | '))
                self.assertEqual(press['settings'].get('hold_repeats'), '1')

    def test_against_90_34_the_change_is_steering_the_guard_the_quick_taps_and_the_stick_windows(self):
        # No ramp stage can be under a Steering stick window any more, so the fix pipeline no longer writes the
        # firing buttons into them: they inherit Base's mouse buttons again, as from 90.13 to 90.33.
        for variant in self.data:
            with self.subTest(variant=variant):
                report = changes.diff(snapshot(variant), self.numeric[variant])
                self.assertEqual((report['added'], report['removed']), ([], []))
                taps = {self.title(variant, t) for t in fg.GYRO_QUICK_TAPS}
                windows = {'Steering | LS Up: Double Tap', 'Steering | LS Down: Double Tap'}
                self.assertEqual(changes.changed_layers(report), {fg.STEERING, fg.GUARD} | taps | windows)
                for window in windows:
                    for row in report['layers'][window]:
                        self.assertNotIn((row['source'], row['input']), [
                            (source, name) for source, group in self.layouts[variant].active(window).items()
                            for name in group.get('inputs', {})], row)       # each change is an input that went


if __name__ == '__main__':
    unittest.main()
