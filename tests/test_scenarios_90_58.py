"""90.58: 90.57 without the removes that never take a layer off. Nothing is added, and nothing plays differently."""

import hashlib
import importlib.util
import itertools
import json
import random
import sys
import unittest
from collections import Counter

from steam_layout.cleanups import Cleanups
from steam_layout.model import Layout, entries, map_title
from tests.scenario import RENAME, ROOT, VARIANTS, ScenarioCase, frozen_layout_data, layout_data, scenario

BUILD = ROOT / 'findings/2026-10-12-removes-that-never-take-a-layer-off'
AUDIT = ROOT / 'findings/2026-10-12-remove-list-audit'
TAKEN = {'default': (4013, 1162, 2851), 'alternative': (4083, 1174, 2909)}      # 90.57, taken out, 90.58
MODES = ('Steering', 'Steering | LS: Entry Guard', 'Cursor Gyro', 'Gamepad')
# The removes a cleanup function still has beyond what its rules ask for (R128, R129): the right pad's two click
# layers, which come on by `hold_layer`. Neither the chains nor the simulator follow that, so the audit of every
# remove could not show them unnecessary and they stay.
HELD_PAD_LAYERS = {(host, stick, target) for host in ('RTP: Circular Scroll', 'RTP: Entry Point')
                   for stick in ('joystick', 'right_joystick') for target in ('RTP: Middle Click', 'RTP: Mouse Buttons')}


def built(variant):
    return json.loads((BUILD / f'{variant}-candidate.json').read_text(encoding='utf-8'))


def audit_script(name):
    """A script of the audit of every remove, which the proofs of this build ran on."""
    tests = str(ROOT / 'tests')
    if tests not in sys.path:
        sys.path.insert(0, tests)                                   # the scripts import `scenario` by that name
    spec = importlib.util.spec_from_file_location(f'remove_list_audit_{name}', AUDIT / f'{name}.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def commands(value):
    return value if isinstance(value, list) else [value]


def differences(a, b, path, lists, other):
    if a == b:
        return
    if path and path[-1] == 'binding':
        lists.append((path, commands(a), commands(b)))
    elif isinstance(a, dict) and isinstance(b, dict):
        for key in a.keys() | b.keys():
            if key in a and key in b:
                differences(a[key], b[key], path + (key,), lists, other)
            else:
                other.append(path + (key,))
    elif isinstance(a, list) and isinstance(b, list) and len(a) == len(b):
        for index, (x, y) in enumerate(zip(a, b)):
            differences(x, y, path + (index,), lists, other)
    else:
        other.append(path)


def removes(layout):
    return [(title, source, name, kind, index, [t for op, t in layout.layer_ops(entry) if op == 'remove_layer'])
            for title in layout.presets for source, group in layout.active(title).items()
            for name, value in (group.get('inputs') or {}).items()
            for index, (kind, entry) in enumerate(entries(value.get('activators') or {}))]


class OnlyRemovesAreGone(unittest.TestCase):
    """The author, 2026-10-12: "I want to make sure that this is reductive and not additive. So we're not going
    to be adding any layer removals right now. We're just reducing them." """

    def test_every_bind_has_its_90_57_commands_less_some_removes_and_nothing_else_differs(self):
        for variant in VARIANTS:
            with self.subTest(variant=variant):
                lists, other = [], []
                differences(frozen_layout_data(variant, '90.57'), built(variant), (), lists, other)
                self.assertEqual(other, [('controller_mappings', 'title')])
                gone = 0
                for path, old, new in lists:
                    lost, gained = Counter(old) - Counter(new), Counter(new) - Counter(old)
                    self.assertFalse(gained, path)
                    self.assertTrue(all('remove_layer' in command for command in lost), path)
                    rest = iter(old)
                    self.assertTrue(all(any(x == y for y in rest) for x in new), path)      # what stays keeps its order
                    self.assertTrue(new, path)
                    gone += sum(lost.values())
                self.assertEqual(gone, TAKEN[variant][1])

    def test_the_count_of_removes(self):
        for variant, (before, taken, after) in TAKEN.items():
            count = lambda data: sum(len(found[5]) for found in removes(Layout(data)))
            self.assertEqual(count(frozen_layout_data(variant, '90.57')), before)
            self.assertEqual(count(built(variant)), after)
            self.assertEqual(before - after, taken)

    def test_the_fourteen_clears_name_5_to_27_layers(self):
        # R163. Until 90.57 each named every layer but one, 89. They keep every layer that was on the stack at
        # least once when the clear fired, and every one the audit could not rule out.
        for variant in VARIANTS:
            old, new = Layout(frozen_layout_data(variant, '90.57')), Layout(built(variant))
            now = {found[:5]: found[5] for found in removes(new)}
            sizes = sorted(len(now[found[:5]]) for found in removes(old) if len(found[5]) == 89)
            self.assertEqual(sizes, [5, 5, 14, 14, 23, 23, 26, 26, 26, 26, 27, 27, 27, 27], variant)


class NothingPlaysDifferently(unittest.TestCase):
    """The proof of the build was 48,000 random walks and every bumper sequence of five steps a layout, with the
    whole log compared (findings/2026-10-12-remove-list-audit). These are samples of both, kept in the suite."""

    def test_seeded_walks_give_the_same_log_on_90_57_and_on_this_build(self):
        walk = audit_script('walk')
        for variant in VARIANTS:
            layouts = [Layout(frozen_layout_data(variant, '90.57')), Layout(built(variant))]
            finished = 0
            for index in range(120):
                missed = 0.10 if index % 2 else 0.0                 # half the walks miss one release in ten (A25)
                found = []
                for layout in layouts:
                    rng = random.Random(58_000 + index)             # the same walk on both
                    pad = walk.new_pad(variant, layout, rng, Counter(), Counter(), Counter())
                    how, left = walk.walk(pad, rng, missed)
                    text = repr(pad.sim.log) + repr(pad.sim.stack)
                    found.append((how, left, hashlib.sha1(text.encode()).hexdigest()))
                self.assertEqual(found[0], found[1], (variant, index))
                finished += found[0][0] == 'done'
            self.assertGreater(finished, 100, variant)

    def test_every_bumper_sequence_of_three_steps_gives_the_same_log(self):
        # L1 or R1 down or up, or a tap of A, then 20 or 210 ms (inside a timer, past the 200 ms hold). From Base
        # with a bind exposed under a held button firing at once, and from `Gyro` with it firing at its next
        # repeat (A9). The build's own sweep played every sequence of five steps, with a 120 ms gap as well.
        rocking = audit_script('rocking')
        steps = list(itertools.product(itertools.product(rocking.ROCK, (20, 210)), repeat=3))
        for variant in VARIANTS:
            layouts = [Layout(frozen_layout_data(variant, '90.57')), Layout(built(variant))]
            played = scrolled = 0
            for start, exposed in ((('Base',), True), (('Base', 'Gyro'), False)):
                for sequence in steps:
                    before, after = (rocking.play(variant, layout, start, exposed, sequence) for layout in layouts)
                    self.assertEqual(before, after, (variant, start, exposed, sequence))
                    played += 1
                    scrolled += before[1]
            self.assertEqual(played, 2 * 6 ** 3)
            self.assertGreater(scrolled, 40, variant)                 # the sequences do reach the scroll layers


class Clears(unittest.TestCase):
    def test_a_clear_names_every_layer_that_is_on_the_stack_when_it_fires(self):
        # R163, since 90.58: a clear names every layer that can be on the stack there. A whole list could not go
        # stale when a layer was added; a short one can, and this is the guard. The fourteen clears are the binds
        # that had 89 removes in 90.57; each kept one layer, `Gyro` or `Menu Keys`.
        walk = audit_script('walk')
        for variant in VARIANTS:
            old, layout = Layout(frozen_layout_data(variant, '90.57')), Layout(layout_data(variant))
            keeps = {(title, (source, name), kind, index): set(old.presets) - set(found) - {'Base'}
                     for title, source, name, kind, index, found in removes(old) if len(found) == 89}
            self.assertEqual(len(keeps), 14)
            self.assertTrue(all(len(keep) == 1 for keep in keeps.values()))
            fired, left = Counter(), []

            class Watching(walk.Watcher):
                def _run(sim, entry, act=None, tap=False, commands=True):
                    key = (entry.layer, entry.control, entry.kind, entry.index)
                    if commands and key in keeps:
                        named = {target for op, target in entry.ops if op == 'remove_layer'}
                        fired[key] += 1
                        extra = set(sim.stack[1:]) - named - keeps[key]
                        if extra:
                            left.append((key, sorted(extra)))
                    return super()._run(entry, act=act, tap=tap, commands=commands)

            for index in range(240):
                rng = random.Random(163_000 + index)
                pad = walk.Pad.__new__(walk.Pad)
                pad.variant, pad.options, pad.layout = variant, {}, layout
                pad.sim = Watching(layout, Counter(), Counter(), Counter(), exposed_fires=rng.random() < 0.5,
                                   reverse_ties=rng.random() < 0.5)
                pad._mark, pad._began = 0, tuple(pad.sim.stack)
                walk.walk(pad, rng, 0.10 if index % 2 else 0.0)
            self.assertEqual(left, [], variant)
            self.assertEqual(len(fired), 14, variant)                 # every one of the fourteen fired
            self.assertGreater(sum(fired.values()), 300, variant)


class CleanupFunctions(unittest.TestCase):
    def test_no_cleanup_function_names_a_layer_its_rules_do_not_ask_for(self):
        # R132 as tightened in 90.57, for cleanup functions. The cleanup rules ask for the host, what is below it
        # inside the guard, and a layer above it that leaves the input alone (R128, R129). A layer above that binds
        # the input answers it first, so the host's bind does not run while it is on. 172 such removes (184 in the
        # alternative) went in 90.58; this keeps them out.
        for variant in VARIANTS:
            layout = Layout(layout_data(variant))
            c = Cleanups(layout)
            name = lambda title: map_title(title, RENAME) if variant == 'alternative' else title
            extra = set()
            for host in layout.presets:
                if host == c.base:
                    continue
                for t in c.inv.by_layer(host):
                    if t.role != 'recovery':
                        continue
                    asked = {x for x, _ in c.left(host, t, c.guard(host, t.source, t.input), frozenset())} | {host}
                    extra |= {(host, t.source, target) for op, target in t.ops
                              if op == 'remove_layer' and target not in asked}
            self.assertEqual(extra, {(name(h), s, name(t)) for h, s, t in HELD_PAD_LAYERS}, variant)


class MissedReleases(ScenarioCase):
    """The author's cases, 2026-10-12: L1's modifier and its cover, and the plain Modifier 2 layers."""

    @scenario('90.58 M1', rules=('R128', 'R135'), rests=('A1', 'A7', 'A25'), either=('A9', 'A32'))
    def test_a_modifier_left_on_with_its_cursor_layer_goes_in_two_presses_of_a_at_most(self):
        # The modifier's cleanup on A named the cursor layer until 90.57. The cursor layer binds A as a cancel, so
        # it answers A while it is on: that remove never took it off. The first press ends the cursor layer. The
        # modifier's own cleanup is then exposed under the held A: it runs on that press or on the next (A9).
        for gyro in (False, True):
            home = ('Base', 'Gyro') if gyro else ('Base',)
            for bumper, modifier in (('L1', 'L1: Modifier 0'), ('R1', 'R1: Modifier 1')):
                for pad in self.each(start=home):
                    pad.hold(bumper).wait(300).miss(bumper).wait(300)
                    self.assertTrue(pad.has(('Gyro | ' if gyro else '') + modifier, f'{bumper}: Temp Cursor Gyro'))
                    pad.tap('A').wait(200)
                    self.assertTrue(pad.lacks(f'{bumper}: Temp Cursor Gyro'))
                    pad.tap('A').wait(200)
                    self.assertEqual((pad.stack, pad.down()), (pad.layers(*home), []))

    @scenario('90.58 M2', rules=('R128', 'R169'), rests=('A1', 'A7', 'A25'), either=('A9', 'A32'))
    def test_both_bumpers_left_on_go_with_a_thumb_on_a_stick(self):
        # Modifier 2 with its three covers and both modifiers. The Modifier 2 layer's cleanup on a stick touch
        # named `L1&R1: Tap Cover` until 90.57; the cover binds both touches and clears the whole stack of them.
        for gyro in (False, True):
            home = ('Base', 'Gyro') if gyro else ('Base',)
            for first, second in (('L1', 'R1'), ('R1', 'L1')):
                for stick in ('LS', 'RS'):
                    for pad in self.each(start=home):
                        pad.hold(first).wait(60).hold(second).wait(300).miss(first).wait(20).miss(second).wait(300)
                        self.assertTrue(pad.has('L1&R1: Tap Cover'))
                        pad.touch(stick).wait(100).lift(stick).wait(600)
                        self.assertEqual((pad.stack, pad.down()), (pad.layers(*home), []))

    @scenario('90.58 M3', rules=('R128', 'R169'), rests=('A1', 'A7', 'A25'), either=('A9', 'A32'))
    def test_a_modifier_left_on_under_its_cover_goes_with_a_thumb_on_a_stick(self):
        # A key typed with the bumper held puts the cover over the modifier. The modifier's cleanup on a stick
        # touch named the cover until 90.57; the cover binds both touches and removes itself and the modifier.
        for gyro in (False, True):
            home = ('Base', 'Gyro') if gyro else ('Base',)
            for bumper, modifier in (('L1', 'L1: Modifier 0'), ('R1', 'R1: Modifier 1')):
                for stick in ('LS', 'RS'):
                    for pad in self.each(start=home):
                        pad.hold(bumper).wait(60).tap('A').wait(100).miss(bumper).wait(400)
                        self.assertTrue(pad.has(('Gyro | ' if gyro else '') + modifier, f'{bumper}: Tap Cover'))
                        pad.touch(stick).wait(100).lift(stick).wait(600)
                        self.assertEqual((pad.stack, pad.down()), (pad.layers(*home), []))


class Modes(ScenarioCase):
    @scenario('90.58 C1', rules=('R163',), rests=('A4', 'A17'), either=('A9', 'A32'))
    def test_entering_and_leaving_a_mode_over_pad_and_stick_layers_leaves_nothing_on(self):
        # The clears name 26 or 27 layers where they named 89. A thumb on each pad is on the stack when the
        # first click lands, and a thumb on the other stick as well when the second one does: its Tap Cover and
        # Temporary Gyro are the removes the register keeps at the Stateful Entry Points (R132).
        for gyro in (False, True):
            home = ('Base', 'Gyro') if gyro else ('Base',)
            for menu, stick in itertools.product(('Start', 'Select'), ('LS', 'RS')):
                other = 'RS' if stick == 'LS' else 'LS'
                for pad in self.each(start=home):
                    allowed = set(pad.layers('Base', 'Gyro', *MODES))
                    pad.touch('LP').touch('RP').wait(100)
                    pad.hold(menu).wait(60).click(stick).wait(40).let_go(menu).wait(100)
                    pad.lift('LP').lift('RP').lift(stick).wait(600)
                    self.assertLessEqual(set(pad.stack), allowed, (menu, stick))
                    self.assertTrue(set(pad.stack) & set(pad.layers(*MODES)), (menu, stick))
                    self.assertEqual(pad.down(), [])
                    pad.touch('LP').touch('RP').touch(other).wait(400)
                    pad.hold(menu).wait(60).click(stick).wait(40).let_go(menu).wait(100)
                    pad.lift('LP').lift('RP').lift(stick).lift(other).wait(600)
                    self.assertLessEqual(set(pad.stack), allowed, (menu, stick))
                    self.assertEqual(pad.down(), [])


if __name__ == '__main__':
    unittest.main()
