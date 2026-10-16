"""90.56: the left edge's cleanup is the press and its guard chord again in ten Steering layers; only the Entry Guard keeps a chord with Invert Activation.

Fixture responsibility: releases/neptune. See docs/testing.md and tests/test-map.csv.
"""
from tests.support.fixtures.scenarios_90_56 import *

class EdgeCleanupShape(unittest.TestCase):
    def each(self):
        for variant in ('default', 'alternative'):
            layout = Layout(frozen_layout_data(variant, '90.58'))          # 90.61 has the inverted chord again
            yield layout, (lambda title, v=variant: map_title(title, RENAME) if v == 'alternative' else title)

    def test_the_ten_edges_hold_the_cleanup_press_and_its_guard_chord(self):
        for layout, name in self.each():
            for title in EDGES:
                found = list(entries(layout.active(name(title))['joystick']['inputs']['edge']['activators']))
                kinds = [kind for kind, _ in found]
                self.assertEqual(kinds, ['Full_Press', 'chord', 'Soft_Press'] if title in TIMERS else ['Full_Press', 'chord'], title)
                press, guard = found[0][1], found[1][1]
                self.assertEqual(press['settings'].get('hold_repeats'), '1', title)
                self.assertNotEqual(press['settings'].get('interruptable'), '0', title)          # the guard can hold it back
                ops = layout.layer_ops(press)
                self.assertIn(('remove_layer', name(title)), ops)
                self.assertTrue(all(op == 'remove_layer' for op, _ in ops), title)
                self.assertEqual(actions(guard), [EMPTY + ', , '], title)
                self.assertEqual(guard['settings'].get('interruptable'), '0', title)
                self.assertNotIn('edge_binding_invert', guard['settings'], title)
                self.assertFalse(int(guard['settings']['gyro_ratchet_button_mask']) & DEFLECT, title)

    def test_only_the_entry_guard_has_a_chord_with_invert_activation_and_it_removes_only_itself(self):
        for layout, name in self.each():
            found = [(title, source, control, entry) for title in layout.presets
                     for source, group in layout.active(title).items()
                     for control, value in (group.get('inputs') or {}).items()
                     for kind, entry in entries(value.get('activators', {}))
                     if kind == 'chord' and (entry.get('settings') or {}).get('edge_binding_invert') == '1']
            self.assertEqual([(title, source, control) for title, source, control, _ in found], [(GUARD, 'joystick', 'edge')])
            self.assertEqual(layout.layer_ops(found[0][3]), [('remove_layer', GUARD)])


if __name__ == "__main__":
    unittest.main()
