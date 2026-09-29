"""Check saved Temp Cursor Gyro contracts, not Steam's timer/chord scheduling.

The numeric layouts are converted before inspecting targets. Runtime races,
physical deflection thresholds, and overlapping chords still need Deck testing.
"""
import unittest

from audit_command_budget import command_entries
from test_neptune_recovery import EMPTY, addition, load_layouts, removal, recovery_specs


CURSOR_PROFILE = {
    "gyro_precision_speed": "750",
    "haptic_intensity": "3",
    "flickstick_haptic_bump_per_angle": "1",
    "mouse_move_threshold": "10",
}
NORMAL_PROFILE = {
    "gyro_precision_speed": "0",
    "haptic_intensity": "0",
    "flickstick_haptic_bump_per_angle": "5",
    "mouse_move_threshold": "0",
}


def owners(variant):
    buttons = ("L1", "R1") if variant == "default" else ("L2", "R2")
    selectors = ("1", "2") if variant == "default" else ("7", "8")
    for index, (button, selector) in enumerate(zip(buttons, selectors)):
        title = f"{button}: Modifier {index}"
        source, name = primary_input(variant, index)
        yield button, selector, title, source, name


def primary_input(variant, side):
    direction = ("left", "right")[side]
    return ("switch", direction + "_bumper") if variant == "default" else (direction + "_trigger", "edge")


def bindings(entry):
    value = entry["bindings"]["binding"]
    return value if isinstance(value, list) else [value]


def stick_family(prefix):
    return {prefix + ": " + suffix for suffix in ("Entry Point", "Tap Cover", "Temporary Gyro")}


class NeptuneCursorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.layouts = load_layouts()

    def active_groups(self, layout, title):
        return [(state.removesuffix(" active"), layout["groups"][gid])
                for gid, state in layout["presets"][title]["group_source_bindings"].items()
                if state.endswith(" active")]

    def source(self, layout, title, source):
        groups = [g for name, g in self.active_groups(layout, title) if name == source]
        self.assertEqual(len(groups), 1, (title, source))
        return groups[0]

    def entries(self, layout, title):
        for source, group in self.active_groups(layout, title):
            for name, value in group.get("inputs", {}).items():
                for entry in command_entries(value.get("activators", {}), name):
                    yield source, name, entry

    def assert_removals(self, actions, targets):
        self.assertCountEqual(actions, [removal(title) for title in targets])

    def test_cursor_profile_preserves_sensitivity_and_owner_activation(self):
        for variant, layout in self.layouts.items():
            cursor_titles = {title for title in layout["presets"] if title.endswith(": Temp Cursor Gyro")}
            expected = {button + ": Temp Cursor Gyro" for button, *_ in owners(variant)}
            self.assertEqual(cursor_titles, expected)
            base = self.source(layout, "Base", "gyro")["settings"]
            self.assertEqual(base["gyro_natural_sensitivity"], "300")
            self.assertEqual(base["gyro_ratchet_button_mask"], "211109453778944")
            self.assertEqual(base["gyro_ratchet_button_requireany_or_all"], "1")
            for button, _, owner, _, _ in owners(variant):
                with self.subTest(variant=variant, owner=owner):
                    cursor = self.source(layout, button + ": Temp Cursor Gyro", "gyro")
                    self.assertEqual(cursor["mode"], "gyro_to_mouse")
                    self.assertEqual(cursor.get("inputs", {}), {})
                    self.assertEqual(cursor["settings"], {"layer": "1", **CURSOR_PROFILE})
                    gyro_owner = self.source(layout, "Gyro | " + owner, "gyro")["settings"]
                    self.assertEqual(gyro_owner["gyro_ratchet_button_mask"], "211109453758464")
                    self.assertEqual(gyro_owner["gyro_ratchet_button_requireany_or_all"], "0")
                    for suffix in (": Tap Cover", ": Temp Cursor Gyro"):
                        title = button + suffix
                        settings = self.source(layout, title, "gyro")["settings"]
                        for inherited in ("gyro_natural_sensitivity", "gyro_ratchet_button_mask",
                                          "gyro_ratchet_button_requireany_or_all", "flickstick_rotation_sensitivity",
                                          "gyro_vertical_horizontal_ratio"):
                            self.assertNotIn(inherited, settings, (title, inherited))
                        self.assertFalse(any("always_on_action" in group.get("inputs", {})
                                             for _, group in self.active_groups(layout, title)))

    def test_only_primary_delay_and_touch_completion_enter_cursor(self):
        for variant, layout in self.layouts.items():
            for button, selector, regular, source, name in owners(variant):
                cursor_add = addition(button + ": Temp Cursor Gyro")
                for title in (regular, "Gyro | " + regular):
                    with self.subTest(variant=variant, layer=title):
                        routes = {(s, n, e["activation"]) for s, n, e in self.entries(layout, title)
                                  if cursor_add in e["actions"]}
                        self.assertEqual(routes, {(source, name, "chord"),
                                                  ("joystick", "touch", "release"),
                                                  ("right_joystick", "touch", "release")})
                        primary = self.source(layout, title, source)["inputs"][name]["activators"]
                        delayed = primary["chord"]
                        self.assertEqual(bindings(delayed), [cursor_add])
                        self.assertEqual(delayed["settings"]["delay_start"], "300")
                        self.assertEqual(delayed["settings"]["chord_button"], selector)
                        self.assertEqual(delayed["settings"]["interruptable"], "0")
                        release = bindings(primary["release"])
                        self.assertEqual(release[0], addition(button + ": Double Tap"))
                        self.assertIn(removal(button + ": Temp Cursor Gyro"), release[1:])
                        for stick, prefix in (("joystick", "LST"), ("right_joystick", "RST")):
                            touch = self.source(layout, title, stick)["inputs"]["touch"]["activators"]
                            actions = bindings(touch["release"])
                            # Arrays run bottom-to-top: complete the apply before removing helpers.
                            self.assertEqual(actions[-1], cursor_add)
                            self.assert_removals(actions[:-1], stick_family(prefix))

    def test_normal_covers_explicitly_restore_every_cursor_property(self):
        for variant, layout in self.layouts.items():
            for button, _, _, _, _ in owners(variant):
                title = button + ": Tap Cover"
                with self.subTest(variant=variant, layer=title):
                    normal = self.source(layout, title, "gyro")
                    self.assertEqual(normal["mode"], "gyro_to_mouse")
                    self.assertEqual(normal.get("inputs", {}), {})
                    # Omitting a field here inherits its cursor value; it does not reset it.
                    self.assertEqual(normal["settings"], {"layer": "1", **NORMAL_PROFILE})
                    self.assertEqual(set(NORMAL_PROFILE), set(CURSOR_PROFILE))

    def test_override_inputs_keep_applying_normal_cover(self):
        for variant, layout in self.layouts.items():
            for side, (button, _, regular, _, _) in enumerate(owners(variant)):
                opposite_primary = primary_input(variant, 1 - side)
                expected = {("button_diamond", "button_" + key) for key in "abxy"}
                expected |= {("dpad", "dpad_" + direction) for direction in ("north", "south", "east", "west")}
                expected |= {("switch", "button_escape"), ("switch", "button_menu"), opposite_primary}
                expected |= {(stick, name) for stick in ("joystick", "right_joystick") for name in ("click", "edge")}
                self.assertEqual(len(expected), 15)
                for title in (regular, "Gyro | " + regular):
                    with self.subTest(variant=variant, layer=title):
                        routes = [(s, n) for s, n, e in self.entries(layout, title)
                                  if addition(button + ": Tap Cover") in e["actions"]]
                        self.assertCountEqual(routes, expected)

    def test_overlays_replace_primary_and_touch_inputs_without_hiding_edges(self):
        for variant, layout in self.layouts.items():
            for button, selector, owner, source, name in owners(variant):
                targets = recovery_specs(variant)[owner][1]
                for suffix in (": Tap Cover", ": Temp Cursor Gyro"):
                    title = button + suffix
                    with self.subTest(variant=variant, layer=title):
                        primary = self.source(layout, title, source)["inputs"][name]
                        self.assertEqual(set(primary["activators"]), {"release"})
                        self.assertFalse(primary.get("disabled_activators"))
                        self.assert_removals(bindings(primary["activators"]["release"]), targets)
                        for stick, prefix in (("joystick", "LST"), ("right_joystick", "RST")):
                            group = self.source(layout, title, stick)
                            self.assertEqual(group["mode"], "dpad" if stick == "joystick" else "joystick_mouse")
                            self.assertEqual(group["settings"], {"layer": "1"})
                            self.assertEqual(set(group["inputs"]), {"touch"})
                            touch = group["inputs"]["touch"]
                            entries = command_entries(touch["activators"], "touch")
                            self.assertEqual(len(entries), 3)
                            self.assertFalse(touch.get("disabled_activators"))
                            guard = touch["activators"]["chord"]
                            self.assertEqual(bindings(guard), [EMPTY])
                            self.assertEqual(guard["settings"]["chord_button"], selector)
                            self.assertEqual(guard["settings"]["interruptable"], "0")
                            fallback = touch["activators"]["Full_Press"]
                            self.assertEqual(fallback["settings"]["hold_repeats"], "1")
                            self.assertNotEqual(fallback["settings"].get("interruptable"), "0")
                            self.assert_removals(bindings(fallback), targets)
                            self.assert_removals(bindings(touch["activators"]["release"]), stick_family(prefix))
                        self.assertFalse(any(addition(button + ": Temp Cursor Gyro") in e["actions"]
                                             for _, _, e in self.entries(layout, title)))

    def test_family_removals_include_cursor_and_combined_release_preserves_other_side(self):
        for variant, layout in self.layouts.items():
            specs = list(owners(variant))
            left, right = specs[0][0], specs[1][0]
            combined = left + "&" + right + ": Tap Cover"
            mod2 = {name for order in (left + "!" + right, right + "!" + left)
                    for name in (order + ": Modifier 2", "Gyro | " + order + ": Modifier 2")}
            for button, _, owner, source, name in specs:
                release = self.source(layout, combined, source)["inputs"][name]["activators"]["release"]
                actions = [b for b in bindings(release) if b != EMPTY]
                expected = mod2 | recovery_specs(variant)[owner][1] | {combined}
                with self.subTest(variant=variant, side=button):
                    self.assert_removals(actions, expected)
                for title in layout["presets"]:
                    for _, _, entry in self.entries(layout, title):
                        removed_pair = {removal(owner), removal("Gyro | " + owner)}
                        if removed_pair.issubset(entry["actions"]):
                            self.assertIn(removal(button + ": Temp Cursor Gyro"), entry["actions"],
                                          (variant, title, entry["activation"]))


if __name__ == "__main__":
    unittest.main()
