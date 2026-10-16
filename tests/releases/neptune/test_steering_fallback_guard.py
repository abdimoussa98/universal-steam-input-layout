"""The Steering fallback guard, on the generated candidates (90.33).

Builds both variants with the 2026-10-05 steering-fallback-guard builder and runs the fix pipeline,
as the install does (findings/2026-10-05-steering-fallback-guard/README.md). These verify saved
configuration contracts, not Steam's runtime scheduling; the press sequences are in
test_scenarios_90_33.py.
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
    'steering_fallback_guard', ROOT / 'findings/2026-10-05-steering-fallback-guard/build_candidate.py')
fg = importlib.util.module_from_spec(spec); spec.loader.exec_module(fg)

BEFORE = '90.32'
STICKS = ('joystick', 'right_joystick')
# the modifier pair, which are also Steering's drivers: (input, its Gyro modifier, its Steering layer)
PAIR = {'default': ((('switch', 'left_bumper'), 'Gyro | L1: Modifier 0', 'Steering | L1: S Key'),
                    (('switch', 'right_bumper'), 'Gyro | R1: Modifier 1', 'Steering | R1: W Key')),
        'alternative': ((('left_trigger', 'edge'), 'Gyro | L2: Modifier 0', 'Steering | L2: S Key'),
                        (('right_trigger', 'edge'), 'Gyro | R2: Modifier 1', 'Steering | R2: W Key'))}
KEYS = {'dpad_north': 'W', 'dpad_south': 'S'}
LS_OUT = str(1 << 30)
# What the editor can set (resources/Steam Input JSON Structure.md, "Limits the Steam editor sets").
MAX_MS = 1000
DPAD_RADIUS = (10000, 32000)


def snapshot(variant, version=BEFORE):
    path = ROOT / f'versions/neptune/{version}/single-set-{variant}_hold-gyro_{version}.json'
    return json.loads(path.read_text(encoding='utf-8'))


def keys(entry):
    return [a.split(',')[0] for a in actions(entry)]


def flags(entry, title_id):
    """The two flags of the command that removes the layer with this runtime id, or None."""
    for action in actions(entry):
        parts = action.split(',')[0].split()
        if parts[:3] == ['controller_action', 'remove_layer', str(title_id)]:
            return tuple(parts[3:5])
    return None


class SteeringFallbackGuardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data, cls.layouts, cls.numeric = {}, {}, {}
        for variant in ('default', 'alternative'):
            data = cls.data[variant] = fg.Builder(variant).finish()
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

    def test_the_90_33_snapshot_is_this_build(self):
        # The working layouts were this build until 90.34. The newest build's test holds R156.
        for variant in self.data:
            with self.subTest(variant=variant):
                built = copy.deepcopy(self.numeric[variant]['controller_mappings'])
                saved = json.loads((ROOT / f'versions/neptune/90.33/single-set-{variant}_hold-gyro_90.33.json').read_text())[
                    'controller_mappings']
                for cm in (built, saved):
                    cm.pop('title'); cm.pop('description')
                self.assertEqual(built, saved)

    def test_two_layers_are_deleted_and_the_entry_guard_is_the_fallback_guard(self):
        for variant, layout in self.each():
            cm = self.data[variant]['controller_mappings']
            titles = [value['title'] for value in cm['action_layers'].values()]
            self.assertEqual(len(titles), 88)
            self.assertIn(fg.GUARD, titles)
            for gone in (fg.HOLD, fg.WINDOW, fg.ENTRY_GUARD):
                self.assertNotIn(gone, titles)
                self.assertNotIn(fg.token(gone), json.dumps(cm['group']), gone)        # no command names it
            # The presets stay numbered in a row and in the order of the layer keys: Steam swaps layers otherwise
            # (findings/2026-07-11-layer-order-swap).
            self.assertEqual([p['id'] for p in cm['preset']], [str(n) for n in range(len(cm['preset']))])
            self.assertEqual([p['name'] for p in cm['preset']], list(cm['actions']) + list(cm['action_layers']))
            used = {gid for p in cm['preset'] for gid in p['group_source_bindings']}
            self.assertEqual(used, {g['id'] for g in cm['group']})                     # no group was left behind

    def test_steerings_up_and_down_add_the_guard_after_100_ms_with_a_pulse_and_a_reset(self):
        # July's bind. The author, 2026-10-05: "first I want W or S to get into the fallback to have a strong
        # haptic bump so you know you're in the fallback."
        for variant, layout in self.each():
            for direction in KEYS:
                acts = self.acts(layout, fg.STEERING, 'joystick', direction)
                self.assertEqual(sorted(acts), ['Full_Press', 'chord'])
                add, reset = acts['chord'], acts['Full_Press']
                self.assertEqual(layout.layer_ops(add), [('add_layer', fg.GUARD)])
                self.assertEqual(add['settings'], {
                    'gyro_ratchet_button_mask': LS_OUT, 'gyro_ratchet_button_requireany_or_all': '0',
                    'delay_start': '100', 'haptic_intensity': '3', 'interruptable': '0'})
                # R120: the reset removes only that target, repeats, is uninterruptible, and has the delay plus 50.
                self.assertEqual(layout.layer_ops(reset), [('remove_layer', fg.GUARD)])
                self.assertEqual(reset['settings'], {
                    'hold_repeats': '1', 'repeat_rate': '150', 'interruptable': '0', 'haptic_intensity': '0'})

    def test_a_driver_only_adds_its_own_layer(self):
        # With the guard on, the guard's bind answers the button, so Steering's has nothing to take away.
        for variant, layout in self.each():
            for control, _, layer in PAIR[variant]:
                acts = self.acts(layout, fg.STEERING, *control)
                self.assertEqual(sorted(acts), ['Full_Press', 'chord'])
                self.assertEqual(layout.layer_ops(acts['Full_Press']), [('add_layer', layer)])
                self.assertEqual(acts['Full_Press']['settings'].get('hold_repeats'), '1')
                self.assertEqual(layout.layer_ops(acts['chord']), [])                  # the other driver is held

    def test_entering_steering_adds_no_guard(self):
        # Steering's own up and down bring the guard in, at entry too. A guard added at entry with the stick held
        # left would turn a bumper into a modifier.
        for variant, layout in self.each():
            adders = {title for title in layout.presets for group in layout.active(title).values()
                      for slot in group.get('inputs', {}).values() for _, e in entries(slot.get('activators', {}))
                      if ('add_layer', fg.GUARD) in layout.layer_ops(e)}
            self.assertEqual(adders, {fg.STEERING})
            commit = self.acts(layout, fg.ENTERS, 'switch', 'button_escape')['release']
            self.assertEqual(layout.layer_ops(commit)[-1], ('add_layer', fg.STEERING))

    def test_the_guard_types_w_and_s_and_nothing_on_the_stick_ends_it(self):
        # The author, 2026-10-05: "we'll override up and down on the fallback layer. That'll be W and S. So pushing
        # the stick will get you into the fallback layer, but releasing it won't."
        for variant, layout in self.each():
            guard = layout.active(fg.GUARD)
            stick = guard['joystick']['inputs']
            self.assertEqual(sorted(stick), ['dpad_north', 'dpad_south', 'touch'])     # A, D and the edge are open
            for direction, key in KEYS.items():
                acts = stick[direction]['activators']
                self.assertEqual(list(acts), ['Full_Press'])
                self.assertEqual(keys(acts['Full_Press']), [f'key_press {key}'])
                self.assertEqual(acts['Full_Press']['settings'], {'interruptable': '0'})
            self.assertEqual(sorted(guard['right_joystick']['inputs']), ['touch'])
            releases = [(source, name) for source, group in guard.items() for name, slot in group.get('inputs', {}).items()
                        for kind, e in entries(slot.get('activators', {}))
                        if kind == 'release' and ('remove_layer', fg.GUARD) in layout.layer_ops(e)]
            self.assertEqual(releases, [])
            # Start and Select are open, so Steering's add of its Entry Point comes through (author, 2026-10-04).
            bound = {(source, name) for source, group in guard.items() for name in group.get('inputs', {})}
            self.assertEqual(bound, {('joystick', 'dpad_north'), ('joystick', 'dpad_south'), ('joystick', 'touch'),
                                     ('right_joystick', 'touch')} | {control for control, _, _ in PAIR[variant]})

    def test_the_modifier_pair_adds_its_gyro_modifier_with_the_stick_out_and_ends_the_guard_at_centre(self):
        # The author, 2026-10-04: "in there we'll have the gyro mod 0 & 1 add layer on their respective
        # bumpers/triggers"; 2026-10-05: "the bumpers themselves will release the fallback guard if you're going
        # into steering."
        for variant, layout in self.each():
            for control, modifier, _ in PAIR[variant]:
                acts = self.acts(layout, fg.GUARD, *control)
                self.assertEqual(sorted(acts), ['Full_Press', 'chord'])
                self.assertEqual(layout.layer_ops(acts['chord']), [('add_layer', modifier)])
                self.assertEqual(acts['chord']['settings'], {
                    'gyro_ratchet_button_mask': LS_OUT, 'gyro_ratchet_button_requireany_or_all': '0',
                    'hold_repeats': '1', 'repeat_rate': '50', 'interruptable': '0'})
                # The cleanup function's shape (R133, R171): interruptible, repeating, beside the chord.
                self.assertEqual(layout.layer_ops(acts['Full_Press']), [('remove_layer', fg.GUARD)])
                self.assertEqual(acts['Full_Press']['settings'], {
                    'hold_repeats': '1', 'repeat_rate': '50', 'haptic_intensity': '3'})

    def test_both_stick_touches_carry_the_guards_cleanup_function(self):
        for variant, layout in self.each():
            for source in STICKS:                                                       # R169
                acts = self.acts(layout, fg.GUARD, source, 'touch')
                self.assertEqual(sorted(acts), ['Full_Press', 'chord', 'release'])
                self.assertEqual(layout.layer_ops(acts['Full_Press']), [('remove_layer', fg.GUARD)])
                self.assertEqual(acts['Full_Press']['settings'], {'hold_repeats': '1'})
                self.assertEqual(acts['chord']['settings'].get('gyro_ratchet_button_mask'), LS_OUT)
                self.assertEqual(layout.layer_ops(acts['chord']), [])
                self.assertNotIn(('remove_layer', fg.GUARD), layout.layer_ops(acts['release']))

    def test_nothing_the_modifier_pair_brings_in_binds_the_left_sticks_up_or_down(self):
        # So under a held modifier the guard's W and S answer the stick, and Steering's add stays covered.
        for variant, layout in self.each():
            seen, todo = set(), [modifier for _, modifier, _ in PAIR[variant]]
            while todo:
                title = todo.pop()
                if title in seen or title.startswith(fg.STEERING) or title == fg.GYRO:
                    continue
                seen.add(title)
                for group in layout.active(title).values():
                    for slot in group.get('inputs', {}).values():
                        for _, e in entries(slot.get('activators', {})):
                            todo += [target for op, target in layout.layer_ops(e) if op == 'add_layer']
            self.assertGreater(len(seen), 8)
            for title in sorted(seen):
                stick = (layout.active(title).get('joystick') or {}).get('inputs', {})
                self.assertFalse({'dpad_north', 'dpad_south'} & set(stick), title)
                self.assertIn((layout.active(title).get('joystick') or {'mode': 'dpad'})['mode'], ('dpad',), title)

    def test_the_gyro_modifier_2_quick_tap_clears_to_base(self):
        # The author, 2026-10-04: "update gyro mod 2 to also clear the related steering layers and base mod layers
        # too ... it'll take you to the base layer every time."
        for variant, layout in self.each():
            numeric = Layout(self.numeric[variant])
            lookup = {numeric.titles[key]: number + 1 for number, key in enumerate(numeric.order)}   # runtime ids
            taps = [self.title(variant, t) for t in fg.GYRO_QUICK_TAPS]
            base = [self.title(variant, t) for t in fg.BASE_MODIFIERS]
            modifiers = [self.title(variant, t) for t in fg.GYRO_MODIFIERS]
            for title in taps:
                for control, _, _ in PAIR[variant]:
                    release = self.acts(layout, title, *control)['release']
                    removed = [target for op, target in layout.layer_ops(release) if op == 'remove_layer']
                    for wanted in taps + base + modifiers + [fg.GUARD, fg.STEERING, 'Cursor Gyro', fg.GYRO]:
                        self.assertIn(wanted, removed, (title, control))
                    self.assertEqual(removed[-1], fg.GYRO)
                    self.assertEqual([op for op, _ in layout.layer_ops(release) if op != 'remove_layer'], [])
                    # R161: leaving Steering beeps, also when Gyro was never on. Gyro's own toggle shows its name.
                    stored = self.acts(numeric, title, *control)['release']
                    self.assertEqual(flags(stored, lookup[fg.STEERING]), ('0', '1'))
                    self.assertEqual(flags(stored, lookup[fg.GYRO]), ('1', '1'))

    def test_no_stick_states_a_radius_the_editor_cannot_set(self):
        # R173. The author, 2026-10-04: the D-pad's Outer Ring Command Radius goes from 10,000 to 32,000.
        for variant, layout in self.each():
            for title in layout.presets:
                for source in STICKS:
                    group = layout.active(title).get(source)
                    radius = ((group or {}).get('settings') or {}).get('edge_binding_radius')
                    if radius is not None and group['mode'] == 'dpad':
                        self.assertTrue(DPAD_RADIUS[0] <= int(radius) <= DPAD_RADIUS[1], (title, source, radius))
            for source in STICKS:                                           # the guard leaves it to Steam's default
                self.assertNotIn('edge_binding_radius', layout.active(fg.GUARD)[source].get('settings') or {})

    def test_no_delay_or_repeat_rate_is_over_the_editors_1000_ms(self):
        for variant, layout in self.each():                                  # R173
            over = [(title, source, name, key, e['settings'][key])
                    for title in layout.presets for source, group in layout.active(title).items()
                    for name, slot in group.get('inputs', {}).items() for _, e in entries(slot.get('activators', {}))
                    for key in ('delay_start', 'delay_end', 'repeat_rate')
                    if key in (e.get('settings') or {}) and int(e['settings'][key]) > MAX_MS]
            self.assertEqual(over, [])

    def test_against_90_32_the_change_is_the_fallback_the_quick_tap_and_the_lists(self):
        for variant in self.data:
            with self.subTest(variant=variant):
                old = Layout(snapshot(variant))
                report = changes.diff(snapshot(variant), self.numeric[variant])
                self.assertEqual(report['added'], [fg.GUARD])
                self.assertEqual(sorted(report['removed']), sorted([fg.ENTRY_GUARD, fg.HOLD, fg.WINDOW]))
                gone = {fg.ENTRY_GUARD, fg.HOLD, fg.WINDOW}
                named = {title for title in old.presets if title not in gone for group in old.active(title).values()
                         for slot in group.get('inputs', {}).values() for _, e in entries(slot.get('activators', {}))
                         if gone & {target for _, target in old.layer_ops(e)}}
                taps = {self.title(variant, t) for t in fg.GYRO_QUICK_TAPS}
                self.assertEqual(changes.changed_layers(report), named | taps | {fg.GUARD})


if __name__ == '__main__':
    unittest.main()
