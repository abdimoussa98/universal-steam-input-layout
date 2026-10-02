"""Protect settings that exist because of the held-input rule.

Adding a layer over a held input does not fire that layer's immediate layer
command on the input; Fire Start Delay and Hold to Repeat still fire. Several
delays and repeats in these layouts exist only for that reason and look
removable without it.

Whether a removal fires the newly exposed layer command on a held input is
unverified. Every such binding in these layouts also repeats, so the repeat is
the guarantee and is protected here too.

These check saved configuration, not Steam's runtime behavior. Mod 0/1 → Mod 2
entry repeats are covered in test_neptune_cursor. Only active groups are scanned.
"""
import copy
import re
import unittest

from audit_command_budget import command_entries
from test_neptune_cursor import owners, primary_input
from test_neptune_recovery import addition, load_layouts, removal

RULE = "see resources/Steam Input JSON Structure.md#held-inputs-across-layer-changes"
PRESS = {"Full_Press", "chord", "Soft_Press", "Long_Press", "Double_Press", "start_press"}
LAYER_COMMAND = re.compile(r"controller_action (add_layer|remove_layer|hold_layer) \{\{Base::(.+?)\}\}")
GYRO_OFF = "Gyro Off Ramp Up"


def layer_commands(actions):
    return [m.groups() for action in actions if (m := LAYER_COMMAND.search(action))]


def active_inputs(layout, title):
    """Yield (source, input name, input value) for a layer's active groups."""
    for gid, state in layout["presets"][title]["group_source_bindings"].items():
        if state.endswith(" active"):
            for name, value in layout["groups"][gid].get("inputs", {}).items():
                yield state.removesuffix(" active"), name, value


def input_value(layout, title, source, name):
    matches = [value for s, n, value in active_inputs(layout, title) if (s, n) == (source, name)]
    return matches[0] if matches else None


def is_held_press(entry):
    """The activator fires while its input is down, not on release or below an inverted threshold."""
    return entry["activation"] in PRESS and entry["settings"].get("edge_binding_invert") != "1"


def held_input_violations(layout):
    """Find immediate layer commands that could only fire on an input already held.

    For every press that adds (or holds) layers on input I, take the layer that
    ends up on top among those it adds and that defines I. Arrays run
    bottom-to-top, so that is the first such target in stored order. Its binding
    on I must not rely on an immediate layer command: the press that created the
    layer is already down. Re-adding the layer itself is a no-op and is ignored.
    """
    violations = []
    for title in layout["presets"]:
        for source, name, value in active_inputs(layout, title):
            for entry in command_entries(value.get("activators", {}), name):
                if not is_held_press(entry):
                    continue
                targets = [t for kind, t in layer_commands(entry["actions"])
                           if kind in ("add_layer", "hold_layer") and t != title]
                top = next(((t, v) for t in targets
                            if (v := input_value(layout, t, source, name)) is not None), None)
                if not top:
                    continue
                target, target_value = top
                for child in command_entries(target_value.get("activators", {}), name):
                    settings = child["settings"]
                    if (not is_held_press(child) or int(settings.get("delay_start") or 0) > 0
                            or settings.get("hold_repeats") == "1"):
                        continue
                    commands = [c for c in layer_commands(child["actions"])
                                if not (c[0] in ("add_layer", "hold_layer") and c[1] == target)]
                    if commands:
                        violations.append((title, source, name, target, child["path"], commands))
    return violations


def find_entry(layout, title, source, name, predicate):
    value = input_value(layout, title, source, name)
    entries = [e for e in command_entries(value["activators"], name) if predicate(e)]
    return entries


class NeptuneHeldInputTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.layouts = load_layouts()

    def test_ramp_handoffs_keep_their_start_delays(self):
        # The stick is already past 29031 when each ramp layer appears. A
        # zero-delay Soft Press would never fire; the delay is what makes it fire.
        handoffs = ((GYRO_OFF, "Turning Ramp Up 0", "5"), ("Turning Ramp Up 0", "Turning Ramp Up 1", "250"))
        for variant, layout in self.layouts.items():
            for title, target, delay in handoffs:
                with self.subTest(variant=variant, layer=title):
                    entries = find_entry(layout, title, "right_joystick", "edge",
                                         lambda e: addition(target) in e["actions"])
                    self.assertEqual(len(entries), 1)
                    settings = entries[0]["settings"]
                    self.assertEqual(entries[0]["activation"], "Soft_Press")
                    self.assertEqual(settings.get("activation_threshold"), "29031")
                    self.assertNotEqual(settings.get("edge_binding_invert"), "1")
                    self.assertEqual(settings.get("delay_start"), delay,
                                     f"{title} → {target} needs its start delay to fire on the held stick; {RULE}")

    def test_threshold_exits_that_change_layers_repeat(self):
        expected = {GYRO_OFF, "Turning Ramp Up 0", "Turning Ramp Up 1", "LTP: Arrow Keys", "RTP: Mouse Buttons"}
        for variant, layout in self.layouts.items():
            found = set()
            for title in layout["presets"]:
                for source, name, value in active_inputs(layout, title):
                    for entry in command_entries(value.get("activators", {}), name):
                        if entry["settings"].get("edge_binding_invert") == "1" and layer_commands(entry["actions"]):
                            found.add(title)
                            with self.subTest(variant=variant, layer=title, input=name):
                                self.assertEqual(entry["settings"].get("hold_repeats"), "1",
                                                 f"{title} {source}.{name}: an exit already true when "
                                                 f"the layer appears only fires on a repeat; {RULE}")
            self.assertTrue(expected <= found, (variant, expected - found))

    def test_layers_added_over_a_held_modifier_or_click_repeat_their_next_add(self):
        for variant, layout in self.layouts.items():
            # A regular Mod 2 release adds Gyro while the other modifier can still be held.
            for side, (_, _, owner, _, _) in enumerate(owners(variant)):
                source, name = primary_input(variant, side)
                with self.subTest(variant=variant, entry="Gyro | " + owner):
                    entries = find_entry(layout, "Gyro", source, name,
                                         lambda e: addition("Gyro | " + owner) in e["actions"])
                    self.assertEqual(len(entries), 1)
                    self.assertEqual(entries[0]["settings"].get("hold_repeats"), "1", RULE)
            # Menu Entry's stick-click chord adds Fn while that click is still held.
            for fn in ("Menu Left: Fn Layer", "Menu Right: Fn Layer"):
                for source, target in (("joystick", "Transition Set 1"), ("right_joystick", "Transition Set 0")):
                    with self.subTest(variant=variant, layer=fn, source=source):
                        entries = find_entry(layout, fn, source, "click",
                                             lambda e: addition(target) in e["actions"])
                        self.assertEqual(len(entries), 1)
                        self.assertEqual(entries[0]["activation"], "chord")
                        self.assertEqual(entries[0]["settings"].get("hold_repeats"), "1", RULE)

    def test_base_entries_repeat_so_exposure_after_a_removal_is_guaranteed(self):
        # Base is only ever re-exposed by removals. Removal pass-through is
        # unverified, so these repeats are what re-enter a held interaction.
        for variant, layout in self.layouts.items():
            entries = [("switch", "button_escape", "Menu Right: Entry Point"),
                       ("switch", "button_menu", "Menu Left: Entry Point"),
                       ("joystick", "touch", "LST: Entry Point"),
                       ("right_joystick", "touch", "RST: Entry Point"),
                       ("right_trackpad", "touch", "RTP: Entry Point"),
                       ("right_joystick", "edge", GYRO_OFF),
                       ("right_joystick", "edge", "Turning Ramp Up 0")]
            entries += [(*primary_input(variant, side), owner)
                        for side, (_, _, owner, _, _) in enumerate(owners(variant))]
            for source, name, target in entries:
                with self.subTest(variant=variant, source=source, input=name, target=target):
                    found = find_entry(layout, "Base", source, name, lambda e: addition(target) in e["actions"])
                    self.assertEqual(len(found), 1)
                    self.assertEqual(found[0]["settings"].get("hold_repeats"), "1",
                                     f"Base {source}.{name} → {target}: the repeat re-enters after a removal "
                                     f"exposes it; removal pass-through alone is unverified; {RULE}")

    def test_gyro_off_ramp_up_firing_controls_remove_it_with_repeat(self):
        for variant, layout in self.layouts.items():
            inputs = ((("left_trigger", "edge"), ("right_trigger", "edge")) if variant == "default"
                      else (("switch", "left_bumper"), ("switch", "right_bumper")))
            for source, name in inputs:
                with self.subTest(variant=variant, source=source, input=name):
                    entries = command_entries(input_value(layout, GYRO_OFF, source, name)["activators"], name)
                    self.assertEqual(len(entries), 1)
                    self.assertEqual(entries[0]["actions"], [removal(GYRO_OFF)])
                    self.assertEqual(entries[0]["settings"].get("hold_repeats"), "1", RULE)
                    self.assertEqual(entries[0]["settings"].get("interruptable"), "0")

    def test_no_held_input_violations_remain(self):
        # The steering Long Press findings (90.5) are gone: 90.6 replaced them
        # with chorded delays, and Fire Start Delay fires over a held input.
        # Whether the delay counts from the layer add is still a native gate
        # (plans/2026-09-30-steering-chorded-delays.md, C3/C4).
        for variant, layout in self.layouts.items():
            with self.subTest(variant=variant):
                self.assertEqual(held_input_violations(layout), [], RULE)

    def test_held_input_guard_catches_known_regressions(self):
        layout = copy.deepcopy(self.layouts["default"])

        # 1. Dropping the ramp handoff's 5 ms delay. Entry settings are the stored dicts.
        for entry in find_entry(layout, GYRO_OFF, "right_joystick", "edge",
                                lambda e: addition("Turning Ramp Up 0") in e["actions"]):
            entry["settings"].pop("delay_start")

        found = {(title, name, target) for title, _, name, target, _, _ in held_input_violations(layout)}
        self.assertIn(("Base", "edge", GYRO_OFF), found)

    def test_menu_entry_early_chord_types_its_key_itself(self):
        # The entry's opposite-button chord adds Fn while that button is already down, so Fn's
        # own chord can't fire for this press (held-input rule). The entry types the key in
        # the same array, after adding Fn. Since 90.9 the key is direct (no overlay layer).
        for variant, layout in self.layouts.items():
            for entry, button, fn, key in (("Menu Left: Entry Point", "button_escape", "Menu Left: Fn Layer", "RETURN"),
                                           ("Menu Right: Entry Point", "button_menu", "Menu Right: Fn Layer", "BACKSPACE")):
                with self.subTest(variant=variant, entry=entry):
                    chord = input_value(layout, entry, "switch", button)["activators"]["chord"]
                    execution = [b for b in reversed(chord["bindings"]["binding"]) if "empty_binding" not in b]
                    self.assertEqual(execution, [addition(fn), f"key_press {key}, , "])
                    own = input_value(layout, fn, "switch", button)["activators"]["chord"]
                    self.assertIn(f"key_press {key}, , ", own["bindings"]["binding"])


if __name__ == "__main__":
    unittest.main()
