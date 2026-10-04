"""Protect reference tuning and deliberate gyro inheritance exceptions.

These compare saved source settings, not Steam's runtime property resolution.
"""
import json
import unittest

from test_neptune_cursor import CURSOR_PROFILE, owners
from test_neptune_recovery import ROOT, load_layouts


REFERENCE = ROOT / "findings/2026-07-11-layer-order-swap/MOST_RECENT_LAYOUT.post-fix.json"


def active_sources(layout, title):
    return {state.removesuffix(" active"): layout["groups"][gid]
            for gid, state in layout["presets"][title]["group_source_bindings"].items()
            if state.endswith(" active")}


class NeptuneGyroTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.layouts = load_layouts()
        # The archived snapshot is already in title form. Only source settings
        # are needed here, so its duplicate DEPRECATED layer titles are irrelevant.
        cm = json.loads(REFERENCE.read_text())["controller_mappings"]
        names = {key: value["title"] for key, value in {**cm["actions"], **cm["action_layers"]}.items()}
        cls.reference = {
            "groups": {group["id"]: group for group in cm["group"]},
            "presets": {names[preset["name"]]: preset for preset in cm["preset"]},
        }

    def test_base_and_ramp_tuning_match_reference_without_replacing_modifier_edges(self):
        reference_sources = (("Base", "gyro"), ("Base", "right_joystick"),
                             ("Turning Ramp Up 0", "right_joystick"),
                             ("Turning Ramp Up 1", "right_joystick"),
                             ("Gyro Off Ramp Up", "right_joystick"))
        for variant, layout in self.layouts.items():
            for title, source in reference_sources:
                with self.subTest(variant=variant, layer=title, source=source):
                    actual = active_sources(layout, title)[source]
                    reference = active_sources(self.reference, title)[source]
                    self.assertEqual(actual["mode"], reference["mode"])
                    self.assertEqual(actual["settings"], reference["settings"])
            for _, _, owner, _, _ in owners(variant):
                for title in (owner, "Gyro | " + owner):
                    with self.subTest(variant=variant, layer=title):
                        sources = active_sources(layout, title)
                        self.assertEqual(sources["right_joystick"]["settings"], {
                            "layer": "1", "sensitivity": "75",
                            "edge_binding_radius": "7209", "edge_binding_invert": "0"})
                        self.assertEqual(sources["joystick"]["settings"], {
                            "layer": "1", "edge_binding_radius": "4915", "edge_binding_invert": "0"})

    def test_gyro_sources_only_override_owned_properties_or_explicitly_disable(self):
        disabled = {"Gyro Off Ramp Up", "Transition Set 0", "Transition Set 1", "Transition Set 2", "Gamepad"}
        disabled |= {"Menu " + side + ": " + suffix
                     for side in ("Left", "Right")
                     for suffix in ("Entry Point", "Fn Layer", "Double Tap", "Double Tap Cover")}
        disabled |= {"Menu Left: Escape", "Menu Right: Tab"}
        # The chorded menu chains (90.25) copy the window, the second-press layer and the cover, gyro included.
        disabled |= {f"Menu {sides}: {part}" for sides, key in (("Left!Right", "Enter"), ("Right!Left", "Backspace"))
                     for part in ("Double Tap", key, "Double Tap Cover")}
        # The steering Menu Tap Covers sit only on their protected entry and
        # inherit its disabled gyro (90.7). Since 90.21 those Entry Points serve
        # every stateful layer and are named Stateful.
        disabled |= {f'Stateful | Menu {side}: Entry Point' for side in ('Left', 'Right')}
        gyro_activation = {"layer": "1", "gyro_ratchet_button_mask": "211109453758464",
                           "gyro_ratchet_button_requireany_or_all": "0"}
        for variant, layout in self.layouts.items():
            expected = {"Base": ("gyro_to_mouse", active_sources(self.reference, "Base")["gyro"]["settings"])}
            expected.update({title: ("disabled", {"layer": "1"}) for title in disabled})
            expected.update({title: ("gyro_to_mouse", gyro_activation)
                             for title in layout["presets"] if title == "Gyro" or title.startswith("Gyro | ")})
            for prefix, mask in (("LST", "70368744177664"), ("RST", "140737488355328")):
                expected[prefix + ": Temporary Gyro"] = (
                    "gyro_to_mouse", {"layer": "1", "gyro_ratchet_button_mask": mask})
            for button, *_ in owners(variant):
                expected[button + ": Temp Cursor Gyro"] = ("gyro_to_mouse", {"layer": "1", **CURSOR_PROFILE})
            # The stateful layer (90.21) states the same response and no gate: Gyro is always under it.
            expected["Cursor Gyro"] = ("gyro_to_mouse", {**CURSOR_PROFILE, "layer": "1"})

            actual = {title: sources["gyro"] for title in layout["presets"]
                      if "gyro" in (sources := active_sources(layout, title))}
            with self.subTest(variant=variant):
                self.assertEqual(set(actual), set(expected))
            for title, (mode, settings) in expected.items():
                with self.subTest(variant=variant, layer=title):
                    self.assertEqual(actual[title]["mode"], mode)
                    self.assertEqual(actual[title]["settings"], settings)
                    self.assertFalse(actual[title].get("inputs"))


if __name__ == "__main__":
    unittest.main()
