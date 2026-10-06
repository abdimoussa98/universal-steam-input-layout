"""The silent Tap Cover resets and the beep on the second flag, on the generated candidates (90.29).

Builds both variants with the 2026-10-04 quiet-resets-and-beeps builder and runs the fix pipeline,
as the install does (findings/2026-10-04-quiet-resets-and-beeps/README.md). These verify saved
configuration contracts, not Steam's runtime scheduling; the press sequences are in
test_scenarios_90_29.py.
"""
import collections
import copy
import importlib.util
import json
from pathlib import Path
import re
import unittest

from tools.convert_runtime_ids import generate_lookup, titles_to_ids
from steam_layout import changes
from steam_layout.fixes import apply_all
from steam_layout.model import Layout, actions, entries, map_title

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    'quiet_resets_and_beeps', ROOT / 'findings/2026-10-04-quiet-resets-and-beeps/build_candidate.py')
qb = importlib.util.module_from_spec(spec); spec.loader.exec_module(qb)

BEFORE = '90.28'
PADS = ('right_trackpad', 'left_trackpad')
# A layer command and its two flags: the on-screen name, then the beep (A49).
FLAGS = re.compile(r'controller_action (add_layer|remove_layer|hold_layer) (\{\{.+?\}\}|\d+) (\d) (\d)')
MENU_KEYS = 'Menu Keys'
CHAIN_ENTRIES = {'Menu Left!Right: Entry Point': 'button_escape', 'Menu Right!Left: Entry Point': 'button_menu'}
# the layers whose bindings 90.29 changes, by the default layout's titles
CHANGED = {'LST: Entry Point', 'RST: Entry Point', 'RTP: Entry Point', 'Transition Set 0', 'Transition Set 1',
           'Transition Set 2', 'Steering | LS: Fallback Hold', 'Cursor Gyro', 'Menu Left!Right: Entry Point',
           'Menu Right!Left: Entry Point', MENU_KEYS}


def snapshot(variant):
    path = ROOT / f'versions/neptune/{BEFORE}/single-set-{variant}_hold-gyro_{BEFORE}.json'
    return json.loads(path.read_text(encoding='utf-8'))


def commands(layout):
    """Every layer command of the layout: (layer, source, input, activation type, entry, op, target, name, beep)."""
    for title in layout.presets:
        for source, group in layout.active(title).items():
            for name, slot in group.get('inputs', {}).items():
                for kind, entry in entries(slot.get('activators', {})):
                    for action in reversed(actions(entry)):
                        match = FLAGS.search(action)
                        if match:
                            yield (title, source, name, kind, entry, match.group(1), layout.resolve(match.group(2)),
                                   match.group(3), match.group(4))


class QuietResetsAndBeepsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data, cls.layouts, cls.numeric = {}, {}, {}
        for variant in ('default', 'alternative'):
            data = cls.data[variant] = qb.Builder(variant).finish()
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

    def test_the_90_29_snapshot_is_this_build(self):
        # The working layouts were this build until 90.30. The newest build's test holds R156.
        for variant in self.data:
            with self.subTest(variant=variant):
                built = copy.deepcopy(self.numeric[variant]['controller_mappings'])
                saved = json.loads((ROOT / f'versions/neptune/90.29/single-set-{variant}_hold-gyro_90.29.json').read_text())[
                    'controller_mappings']
                for cm in (built, saved):
                    cm.pop('title'); cm.pop('description')
                self.assertEqual(built, saved)

    def test_the_tap_cover_resets_state_no_haptic(self):
        # The author, on the Deck with 90.28: a pulse at every touch of the right pad. The reset repeats, so it
        # fires as the Entry Point lands on the thumb (A6), and it stated no haptic. It stays on all three (R120).
        for variant, layout in self.each():
            for prefix, source in qb.COVER_RESETS:
                touch = layout.active(f'{prefix}: Entry Point')[source]['inputs']['touch']['activators']
                reset = touch['Full_Press']
                self.assertEqual(layout.layer_ops(reset), [('remove_layer', f'{prefix}: Tap Cover')], prefix)
                self.assertEqual(reset['settings'], {'hold_repeats': '1', 'repeat_rate': '200', 'interruptable': '0',
                                                     'haptic_intensity': '0'}, prefix)

    def test_every_layer_command_on_a_pad_states_its_haptic(self):
        # A pad bind with no haptic stated pulsed on the Deck. Nothing on a pad is left to Steam's default.
        for variant, layout in self.each():
            unstated = [(title, source, name, kind) for title, source, name, kind, entry, *_ in commands(layout)
                        if source in PADS and 'haptic_intensity' not in (entry.get('settings') or {})]
            self.assertEqual(unstated, [])

    def test_no_layer_command_shows_a_name_without_a_beep(self):
        # A49: the first flag is the name on screen, the second the beep. `1 0` was written for the beep until
        # 90.28. What is left: the beeps (`0 1`) and the author's own Gyro toggle (`1 1`).
        for variant, layout in self.each():
            flags = collections.Counter((op, name, beep) for *_, op, _, name, beep in commands(layout) if (name, beep) != ('0', '0'))
            self.assertEqual(flags, {('add_layer', '0', '1'): 10, ('remove_layer', '0', '1'): 16,
                                     ('add_layer', '1', '1'): 4, ('remove_layer', '1', '1'): 4})
            gyro = self.title(variant, 'Gyro')
            self.assertEqual({target for *_, target, name, beep in commands(layout) if name == '1'}, {gyro})

    def test_every_transition_and_every_stateful_exit_beeps_on_the_second_flag(self):
        # R161: a beep and a strong pulse, and no name on screen.
        stateful = {'Steering', 'Cursor Gyro', 'Gamepad'}
        for variant, layout in self.each():
            for name in ('Transition Set 0', 'Transition Set 1', 'Transition Set 2'):
                for button in ('button_menu', 'button_escape'):
                    release = layout.active(name)['switch']['inputs'][button]['activators']['release']
                    self.assertEqual(release['settings'], {'haptic_intensity': '3'}, (name, button))
                    ops = layout.layer_ops(release)
                    beeping = [t for op, t in ops if op == 'add_layer' and t in stateful] or [name]
                    flags = {layout.resolve(m.group(2)): (m.group(3), m.group(4))
                             for a in actions(release) if (m := FLAGS.search(a))}
                    self.assertEqual(flags, {t: ('0', '1' if t in beeping else '0') for _, t in ops}, (name, button))
            # The stateful layers' own exits: one command with the beep, on the layer's removal.
            exits = collections.Counter((title, target) for title, *_, op, target, name, beep in commands(layout)
                                        if beep == '1' and op == 'remove_layer' and name == '0' and not title.startswith('Transition'))
            self.assertEqual(exits, {('Steering | LS: Fallback Hold', 'Steering'): 2, ('Cursor Gyro', 'Cursor Gyro'): 2,
                                     (MENU_KEYS, MENU_KEYS): 10})

    def test_menu_keys_is_entered_with_the_beep_and_the_pulse_from_both_chains(self):
        # The author, on the Deck with 90.28: no beep entering `Menu Keys`. Both chains' Entry Points add it,
        # last, from the 200 ms hold; the flag was in the name's place.
        for variant, layout in self.each():
            adders = {(title, name, kind) for title, _, name, kind, _, op, target, *_ in commands(layout)
                      if (op, target) == ('add_layer', MENU_KEYS)}
            self.assertEqual(adders, {(title, button, 'chord') for title, button in CHAIN_ENTRIES.items()})
            for title, button in CHAIN_ENTRIES.items():
                hold = layout.active(title)['switch']['inputs'][button]['activators']['chord']
                self.assertEqual((hold['settings']['delay_start'], hold['settings']['haptic_intensity']), ('200', '3'), title)
                self.assertEqual(layout.layer_ops(hold)[-1], ('add_layer', MENU_KEYS))
                flags = [(m.group(3), m.group(4)) for a in actions(hold) if (m := FLAGS.search(a))]
                self.assertEqual(flags[0], ('0', '1'), title)                   # stored first, run last (A4)
                self.assertEqual(set(flags[1:]), {('0', '0')}, title)

    def test_against_90_28_only_the_feedback_changes(self):
        for variant in self.data:
            with self.subTest(variant=variant):
                report = changes.diff(snapshot(variant), self.numeric[variant])
                self.assertEqual((report['added'], report['removed']), ([], []))
                self.assertEqual(changes.changed_layers(report), {self.title(variant, t) for t in CHANGED})
                # 90.28 with its 22 flags moved and its three resets silenced is this build, to the last setting.
                moved, count = re.subn(r'(controller_action (?:add_layer|remove_layer|hold_layer) \d+) 1 0, ', r'\1 0 1, ',
                                       json.dumps(snapshot(variant)))
                self.assertEqual(count, qb.BEEPS)
                expected = json.loads(moved)
                old = Layout(expected)
                for prefix, source in qb.COVER_RESETS:
                    reset = old.active(f'{prefix}: Entry Point')[source]['inputs']['touch']['activators']['Full_Press']
                    reset['settings']['haptic_intensity'] = '0'
                built = copy.deepcopy(self.numeric[variant]['controller_mappings'])
                for cm in (built, expected['controller_mappings']):
                    cm.pop('title'); cm.pop('description')
                self.assertEqual(built, expected['controller_mappings'])


if __name__ == '__main__':
    unittest.main()
