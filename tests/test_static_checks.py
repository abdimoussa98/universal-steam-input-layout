"""Static checks that came from the retired Deck checklist and had no test yet.

Each asks what a binding or a setting is, with no presses. The check it replaces is named in
findings/2026-10-03-deck-check-sorting.
"""
import json
from pathlib import Path
import unittest

from steam_layout.cleanups import Cleanups
from steam_layout.model import Layout, entries
from tests.scenario import VARIANTS, layout_data

ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / "findings/2026-07-11-layer-order-swap/MOST_RECENT_LAYOUT.post-fix.json"


class StaticChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.layouts = {v: Layout(layout_data(v)) for v in VARIANTS}

    def base(self, variant, source):
        layout = self.layouts[variant]
        return layout.active(layout.base)[source]

    def test_bases_right_stick_edge_has_three_entries_with_any_chords_and_no_haptic(self):   # TR2, TR12
        for variant in VARIANTS:
            found = list(entries(self.base(variant, "right_joystick")["inputs"]["edge"]["activators"]))
            with self.subTest(variant):
                self.assertEqual([kind for kind, _ in found], ["Full_Press", "chord", "chord"])
                for kind, entry in found:
                    settings = entry.get("settings") or {}
                    self.assertIn(settings.get("haptic_intensity"), (None, "0"))
                    if kind == "chord":
                        self.assertEqual(settings["gyro_ratchet_button_requireany_or_all"], "0")       # Any

    def test_the_defaults_base_triggers_match_the_july_reference(self):                      # DT1
        reference = Layout(json.loads(REFERENCE.read_text(encoding="utf-8")))
        for source, button in (("left_trigger", "LEFT"), ("right_trigger", "RIGHT")):
            ours, theirs = self.base("default", source), reference.active(reference.base)[source]
            with self.subTest(source):
                self.assertEqual(ours["settings"], theirs["settings"])
                self.assertEqual(ours["inputs"], theirs["inputs"])
                self.assertEqual(ours["inputs"]["edge"]["activators"]["Full_Press"]["bindings"]["binding"],
                                 f"mouse_button {button}, , ")

    def test_bases_left_stick_edge_is_the_empty_wasd_modifier(self):                         # WM1
        for variant in VARIANTS:
            group = self.base(variant, "joystick")
            with self.subTest(variant):
                self.assertEqual(group["inputs"]["edge"]["activators"], {"Soft_Press": {
                    "bindings": {"binding": "controller_action empty_binding, WASD Modifier, , "},
                    "settings": {"haptic_intensity": "0", "soft_press_sytle": "2", "activation_threshold": "26610",
                                 "interruptable": "0", "edge_binding_invert": "1"}}})
                self.assertEqual({k: group["settings"][k] for k in ("edge_binding_radius", "deadzone", "requires_click")},
                                 {"edge_binding_radius": "21700", "deadzone": "13276", "requires_click": "0"})

    def test_the_two_modifier_2_orders_are_never_on_the_stack_together(self):                # MR2
        for variant in VARIANTS:
            layout = self.layouts[variant]
            cleanups = Cleanups(layout)
            orders = [t for t in layout.presets if "Modifier 2" in t and "Steering" not in t]
            with self.subTest(variant):
                self.assertEqual(len(orders), 4)                              # two orders, regular and Gyro
                for title in orders:
                    first = title.split(": ")[0].split("| ")[-1]              # L1!R1 or R1!L1
                    others = {t for t in cleanups.present(title) if "Modifier 2" in t and first not in t}
                    self.assertEqual(others, set(), title)


if __name__ == "__main__":
    unittest.main()
