"""Check saved Temp Cursor Gyro contracts, not Steam's timer/chord scheduling.

The numeric layouts are converted before inspecting targets. Runtime races,
physical deflection thresholds, and overlapping chords still need Deck testing.
"""
import unittest

from tools.audit_command_budget import command_entries
from test_neptune_recovery import EMPTY, addition, load_layouts, removal, recovery_specs


CURSOR_PROFILE = {
    "gyro_precision_speed": "750",
    "haptic_intensity": "0",
    "flickstick_haptic_bump_per_angle": "1",
    "mouse_move_threshold": "5",
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


def ordinary_outputs(side):
    """The twelve existing outputs, independent of default/alternative owner buttons."""
    outputs = {("button_diamond", "button_" + name): "key_press " + key + ", , "
               for name, key in zip("abxy", ("G", "X", "Z", "T") if side == 0 else ("H", "N", "B", "Y"))}
    outputs.update({("dpad", "dpad_" + name): "key_press " + key + ", , "
                    for name, key in zip(("north", "south", "east", "west"),
                                         ("9", "DASH", "0", "EQUALS") if side == 0 else ("5", "7", "6", "8"))})
    outputs.update({
        ("switch", "button_escape"): "key_press " + ("INSERT" if side == 0 else "HOME") + ", , ",
        ("switch", "button_menu"): "key_press " + ("DELETE" if side == 0 else "END") + ", , ",
        ("joystick", "click"): "key_press CAPSLOCK, , " if side == 0 else "mouse_button BACK, , ",
        ("right_joystick", "click"): "mouse_button " + ("MIDDLE" if side == 0 else "FORWARD") + ", , ",
    })
    return outputs


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
                        self.assertEqual(delayed["settings"]["delay_start"], "200")              # 300 until 90.25
                        self.assertEqual(delayed["settings"]["chord_button"], selector)
                        self.assertEqual(delayed["settings"]["interruptable"], "0")
                        self.assertEqual(delayed["settings"]["haptic_intensity"], "3")
                        self.assertNotEqual(delayed["settings"].get("hold_repeats"), "1")
                        release = bindings(primary["release"])
                        self.assertEqual(release[0], addition(button + ": Double Tap"))
                        self.assertIn(removal(button + ": Temp Cursor Gyro"), release[1:])
                        for stick, prefix in (("joystick", "LST"), ("right_joystick", "RST")):
                            touch = self.source(layout, title, stick)["inputs"]["touch"]["activators"]
                            self.assertEqual(touch["release"]["settings"]["haptic_intensity"], "0")
                            actions = bindings(touch["release"])
                            # Arrays run bottom-to-top: complete the apply before removing helpers.
                            self.assertEqual(actions[-1], cursor_add)
                            self.assert_removals(actions[:-1], stick_family(prefix))

    def test_delayed_cursor_reset_is_scoped_and_replaced_by_upper_inputs(self):
        for variant, layout in self.layouts.items():
            timed = [title for title in layout["presets"]
                     if any("always_on_action" in group.get("inputs", {})
                            for _, group in self.active_groups(layout, title))]
            # The Always On layers are exactly the Double Tap windows, so the loop below skips none.
            self.assertEqual(sorted(timed), sorted(t for t in layout["presets"] if t.endswith(": Double Tap")))
            for button, _, regular, source, name in owners(variant):
                target = removal(button + ": Temp Cursor Gyro")
                for title in (regular, "Gyro | " + regular):
                    with self.subTest(variant=variant, layer=title):
                        primary = self.source(layout, title, source)["inputs"][name]["activators"]
                        self.assertEqual(len(command_entries(primary, name)), 3)
                        reset = primary["Full_Press"]
                        self.assertEqual(bindings(reset), [target])
                        self.assertEqual(reset["settings"], {
                            "hold_repeats": "1", "repeat_rate": "250", "interruptable": "0"})    # the delay + 50 ms (R121)
                        self.assertGreater(int(reset["settings"]["repeat_rate"]),
                                           int(primary["chord"]["settings"]["delay_start"]))
                for suffix in (": Tap Cover", ": Temp Cursor Gyro"):
                    title = button + suffix
                    # Both successful cursor entry and a normal override must replace
                    # the whole primary input, retiring its apply AND periodic reset.
                    primary = self.source(layout, title, source)["inputs"][name]["activators"]
                    self.assertEqual(set(primary), {"release"}, (variant, title))
                for title in timed:
                    # A lower reset must not become inherited inside an Always On window.
                    primary = self.source(layout, title, source)["inputs"][name]
                    self.assertTrue(primary["activators"], (variant, title, name))
                    for entry in command_entries(primary["activators"], name):
                        self.assertNotIn(target, entry["actions"], (variant, title, name))

    def test_normal_covers_inherit_gyro_without_any_source_override(self):
        for variant, layout in self.layouts.items():
            for button, _, _, _, _ in owners(variant):
                title = button + ": Tap Cover"
                with self.subTest(variant=variant, layer=title):
                    self.assertNotIn("gyro", {source for source, _ in self.active_groups(layout, title)})

    def test_output_and_cover_chords_are_separate_uninterruptible_entries(self):
        for variant, layout in self.layouts.items():
            checked = 0
            for side, (button, selector, regular, _, _) in enumerate(owners(variant)):
                for title in (regular, "Gyro | " + regular):
                    for (source, name), output in ordinary_outputs(side).items():
                        with self.subTest(variant=variant, layer=title, source=source, input=name):
                            value = self.source(layout, title, source)["inputs"][name]
                            activators = value["activators"]
                            self.assertEqual(set(activators), {"chord", "Full_Press"})
                            self.assertFalse(value.get("disabled_activators"))
                            self.assertEqual(len(command_entries(activators, name)), 3)
                            chords = activators["chord"]
                            self.assertIsInstance(chords, list)
                            self.assertEqual(len(chords), 2)
                            outputs = [c for c in chords if bindings(c) == [output]]
                            covers = [c for c in chords if bindings(c) == [addition(button + ": Tap Cover")]]
                            self.assertEqual(len(outputs), 1)
                            self.assertEqual(len(covers), 1)
                            # Existing outputs do not repeat; only the layer addition does.
                            self.assertEqual(outputs[0]["settings"], {"chord_button": selector, "interruptable": "0"})
                            self.assertEqual(covers[0]["settings"]["chord_button"], selector)
                            self.assertEqual(covers[0]["settings"]["interruptable"], "0")
                            self.assertEqual(covers[0]["settings"]["hold_repeats"], "1")
                            self.assertNotIn("delay_start", covers[0]["settings"])
                            self.assertIn(covers[0]["settings"].get("haptic_intensity"), (None, "0"))
                            fallback = activators["Full_Press"]
                            self.assertEqual(fallback["settings"]["hold_repeats"], "1")
                            self.assertNotEqual(fallback["settings"].get("interruptable"), "0")
                            self.assert_removals(bindings(fallback), recovery_specs(variant)[title][1])
                            checked += 1
            self.assertEqual(checked, 48)

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

    def test_cursor_cancellations_remove_only_themselves_and_leave_outputs_to_parent(self):
        for variant, layout in self.layouts.items():
            for side, (button, _, _, _, _) in enumerate(owners(variant)):
                title = button + ": Temp Cursor Gyro"
                expected = set(ordinary_outputs(side)) | {primary_input(variant, 1 - side)}
                self.assertEqual(len(expected), 13)
                for source, name in expected:
                    with self.subTest(variant=variant, layer=title, source=source, input=name):
                        value = self.source(layout, title, source)["inputs"][name]
                        self.assertEqual(set(value["activators"]), {"Full_Press"})
                        self.assertFalse(value.get("disabled_activators"))
                        entry = value["activators"]["Full_Press"]
                        self.assertEqual(bindings(entry), [removal(title)])
                        self.assertEqual(entry["settings"]["hold_repeats"], "1")
                        self.assertEqual(entry["settings"]["interruptable"], "0")
                        self.assertNotIn("delay_start", entry["settings"])
                        self.assertIn(entry["settings"].get("haptic_intensity"), (None, "0"))
                # Cursor owns cancellations and primary release, never key/cover/Mod 2 outputs. Its two
                # edge cleanups also remove the modifier under it, in one step (author, 2026-10-02), and
                # so do its two stick-touch cleanups since 90.24 (R169).
                owner = list(owners(variant))[side][2]
                for source, name, entry in self.entries(layout, title):
                    if entry["activation"] != "release":
                        allowed = {removal(title), EMPTY}
                        if name in ("edge", "touch") and entry["activation"] == "Full_Press":
                            allowed |= {removal(owner), removal("Gyro | " + owner)}
                        self.assertTrue(set(entry["actions"]) <= allowed, (variant, title, source, name, entry))

    def test_opposite_modifier_transitions_repeat_and_preserve_branch_and_execution_order(self):
        for variant, layout in self.layouts.items():
            specs = list(owners(variant))
            for side, (button, selector, regular, _, _) in enumerate(specs):
                other_button, _, other_owner, source, name = specs[1 - side]
                for prefix in ("", "Gyro | "):
                    title = prefix + regular
                    with self.subTest(variant=variant, layer=title):
                        chord = self.source(layout, title, source)["inputs"][name]["activators"]["chord"]
                        self.assertEqual(chord["settings"]["chord_button"], selector)
                        self.assertEqual(chord["settings"]["interruptable"], "0")
                        self.assertEqual(chord["settings"]["hold_repeats"], "1")
                        # Stored arrays run bottom-to-top, leaving Mod 2 on top.
                        self.assertEqual(bindings(chord), [
                            addition(prefix + button + "!" + other_button + ": Modifier 2"),
                            addition(other_button + ": Tap Cover"),
                            addition(prefix + other_owner),
                            addition(button + ": Tap Cover"),
                        ])

    def test_cursor_edges_preserve_one_stick_hold_and_repeat_self_removal_for_two(self):
        for variant, layout in self.layouts.items():
            for button, selector, owner, _, _ in owners(variant):
                title = button + ": Temp Cursor Gyro"
                for source in ("joystick", "right_joystick"):
                    with self.subTest(variant=variant, layer=title, source=source):
                        group = self.source(layout, title, source)
                        self.assertEqual(group["settings"], {"layer": "1"})
                        value = group["inputs"]["edge"]
                        self.assertFalse(value.get("disabled_activators"))
                        activators = value["activators"]
                        self.assertEqual(len(command_entries(activators, "edge")), 3)
                        guard, dual = activators["chord"]
                        self.assertEqual(bindings(guard), [EMPTY])
                        self.assertEqual(guard["settings"]["chord_button"], selector)
                        self.assertNotEqual(guard["settings"].get("interruptable"), "0")
                        parent_dual = self.source(layout, owner, source)["inputs"]["edge"]["activators"]["chord"][1]
                        self.assertEqual({key: value for key, value in dual["settings"].items()
                                          if key != "haptic_intensity"}, parent_dual["settings"])
                        self.assertIn(dual["settings"].get("haptic_intensity"), (None, "0"))
                        self.assertEqual(dual["settings"]["gyro_ratchet_button_requireany_or_all"], "1")
                        self.assertEqual(dual["settings"]["interruptable"], "0")
                        self.assertEqual(dual["settings"]["hold_repeats"], "1")
                        self.assertEqual(bindings(dual), [removal(title)])
                        # One step (author, 2026-10-02): the cleanup removes the cursor first, then the
                        # modifier it sits on, normal or Gyro. Stored arrays run bottom to top.
                        fallback = activators["Full_Press"]
                        self.assertEqual(bindings(fallback), [removal("Gyro | " + owner), removal(owner), removal(title)])
                        self.assertEqual(fallback["settings"]["hold_repeats"], "1")
                        self.assertNotEqual(fallback["settings"].get("interruptable"), "0")

    def test_overlays_retire_primary_timers_but_only_normal_covers_replace_touches(self):
        for variant, layout in self.layouts.items():
            for button, selector, owner, source, name in owners(variant):
                # An overlay is shared by the normal and the Gyro modifier, so its lists keep both. The
                # cursor and the Tap Cover are never on the stack together, so neither lists the other
                # (cleanup rule 6, author 2026-10-02).
                for suffix in (": Tap Cover", ": Temp Cursor Gyro"):
                    title = button + suffix
                    overlay_targets = {title, owner, "Gyro | " + owner}
                    if suffix == ": Tap Cover":
                        left, right = ('L1', 'R1') if variant == 'default' else ('L2', 'R2')
                        opposite = right if button == left else left
                        overlay_targets.add(f'Steering | {opposite}!{button}: Modifier 2')
                    with self.subTest(variant=variant, layer=title):
                        primary = self.source(layout, title, source)["inputs"][name]
                        self.assertEqual(set(primary["activators"]), {"release"})
                        self.assertFalse(primary.get("disabled_activators"))
                        self.assert_removals(bindings(primary["activators"]["release"]), overlay_targets)
                        for stick, prefix in (("joystick", "LST"), ("right_joystick", "RST")):
                            group = self.source(layout, title, stick)
                            self.assertEqual(group["mode"], "dpad" if stick == "joystick" else "joystick_mouse")
                            self.assertEqual(group["settings"], {"layer": "1"})
                            if suffix == ": Temp Cursor Gyro":
                                # Until 90.23 the cursor left the touch out and inherited the modifier's. Since
                                # 90.24 it has its own cleanup there (R169), beside a Release that clears the trio.
                                self.assertEqual(set(group["inputs"]), {"click", "edge", "touch"})
                                touch = group["inputs"]["touch"]["activators"]
                                self.assertEqual(set(touch), {"Full_Press", "chord", "release"})
                                self.assert_removals(bindings(touch["release"]), [
                                    f"{prefix}: {part}" for part in ("Entry Point", "Tap Cover", "Temporary Gyro")])
                                self.assert_removals(bindings(touch["Full_Press"]), overlay_targets)
                                self.assertEqual(bindings(touch["chord"]), [EMPTY])
                                continue
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
                            self.assert_removals(bindings(fallback), overlay_targets)
                            self.assert_removals(bindings(touch["activators"]["release"]), stick_family(prefix))
                        self.assertFalse(any(addition(button + ": Temp Cursor Gyro") in e["actions"]
                                             for _, _, e in self.entries(layout, title)))

    def test_rtp_timer_replaces_inherited_cancellation_and_repeating_cover_inputs(self):
        # RTP's quick-touch window can remain above a modifier or cursor. An
        # omitted input would expose their mutations beneath Always On.
        expected = set(ordinary_outputs(0)) - {("switch", "button_escape"), ("switch", "button_menu")}
        self.assertEqual(len(expected), 10)
        for variant, layout in self.layouts.items():
            for source, name in expected:
                with self.subTest(variant=variant, source=source, input=name):
                    value = self.source(layout, "RTP: Double Tap", source)["inputs"][name]
                    self.assertFalse(value.get("disabled_activators"))
                    self.assertEqual(set(value["activators"]), {"Full_Press"})
                    entries = command_entries(value["activators"], name)
                    self.assertEqual(len(entries), 1)
                    self.assertEqual(entries[0]["actions"], [EMPTY])
            # New blocks leave the established timer and self-first exits intact.
            title = "RTP: Double Tap"
            timer = self.source(layout, title, "switch")["inputs"]["always_on_action"]["activators"]["Full_Press"]
            self.assertEqual(bindings(timer), [removal(title)])
            self.assertEqual(timer["settings"], {"delay_start": "150", "interruptable": "0"})
            for source, prefix in (("joystick", "LST"), ("right_joystick", "RST")):
                touch = self.source(layout, title, source)["inputs"]["touch"]["activators"]
                self.assertEqual(set(touch), {"release"})
                actions = bindings(touch["release"])
                self.assertEqual(actions[-1], removal(title))
                self.assert_removals(actions[:-1], stick_family(prefix))
            # Left pad swipes send keys directly (no layer API); see test_double_tap_windows.
            left = self.source(layout, title, "left_trackpad")
            self.assertFalse([b for v in left.get("inputs", {}).values()
                              for e in v["activators"].values() for b in bindings(e) if "_layer" in b])
            trackpad = self.source(layout, title, "right_trackpad")
            self.assertEqual(trackpad["mode"], "dpad")
            for direction in ("north", "south"):
                entry = trackpad["inputs"]["dpad_" + direction]["activators"]["Full_Press"]
                self.assertEqual(bindings(entry), [addition("RTP: Circular Scroll"), removal(title)])
            for name in ("dpad_east", "dpad_west", "edge"):
                self.assertEqual(bindings(trackpad["inputs"][name]["activators"]["Full_Press"]), [removal(title)])

    def test_combined_release_removes_only_its_side_and_preserves_the_other(self):
        for variant, layout in self.layouts.items():
            specs = list(owners(variant))
            left, right = specs[0][0], specs[1][0]
            combined = left + "&" + right + ": Tap Cover"
            mod2 = {name for order in (left + "!" + right, right + "!" + left)
                    for name in (order + ": Modifier 2", "Gyro | " + order + ": Modifier 2")}
            for button, _, owner, source, name in specs:
                # The rocking list: the released side's modifiers (normal and Gyro, as the combined cover
                # sits on either) and Tap Cover, both Modifier 2 orders, and itself. No cursor: it is
                # cancelled before Modifier 2 goes on (cleanup rule 6, author 2026-10-02).
                release = self.source(layout, combined, source)["inputs"][name]["activators"]["release"]
                actions = [b for b in bindings(release) if b != EMPTY]
                expected = mod2 | {owner, "Gyro | " + owner, button + ": Tap Cover", combined}
                with self.subTest(variant=variant, side=button):
                    self.assert_removals(actions, expected)


if __name__ == "__main__":
    unittest.main()
