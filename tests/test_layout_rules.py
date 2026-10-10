"""Static checks for rules that nothing checked before (rule registry plan, phase 15).

Each asks what the layouts hold, with no presses. The rule is named beside the test, and the test is named
under that rule's "Checked by" in resources/Layer Definition of Done.md.
"""
import json
import re
import unittest

from steam_layout import changes, exceptions
from steam_layout.cleanups import Cleanups
from steam_layout.model import Layout, bindings, entries, map_title
from tests.scenario import RENAME, VARIANTS, layout_data

LEGACY_HOLDS = {"LTP: Arrow Keys", "RTP: Mouse Buttons", "LTP: Middle Click", "RTP: Middle Click"}   # R101's entry in the register


class LayoutRules(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.layouts = {v: Layout(layout_data(v)) for v in VARIANTS}

    def test_hold_layer_is_used_only_where_the_register_says(self):                         # R101
        registered = bool(exceptions.of(exceptions.load(), "R101"))
        for variant, layout in self.layouts.items():
            held = {layout.resolve(match.group(1)) for group in layout.groups.values()
                    for slot in group.get("inputs", {}).values() for binding in bindings(slot.get("activators", {}))
                    if (match := re.search(r"controller_action hold_layer (\S+)", binding))}
            with self.subTest(variant):
                self.assertEqual(held, LEGACY_HOLDS if registered else set())

    def test_no_binding_switches_action_sets_and_there_is_one_set(self):                    # R102
        for variant in VARIANTS:
            data = layout_data(variant)
            with self.subTest(variant):
                self.assertEqual(len(data["controller_mappings"]["actions"]), 1)
                self.assertNotIn("CHANGE_PRESET", json.dumps(data).upper())

    def test_layer_titles_are_unique(self):                                                 # R105
        for variant in VARIANTS:
            cm = layout_data(variant)["controller_mappings"]
            titles = [value["title"] for section in ("actions", "action_layers") for value in cm[section].values()]
            with self.subTest(variant):
                self.assertEqual(sorted(titles), sorted(set(titles)))

    def test_the_alternative_has_the_defaults_layers_with_l2_and_r2(self):                  # R106
        default, alternative = (self.layouts[variant] for variant in VARIANTS)
        self.assertEqual([map_title(default.titles[key], RENAME) for key in default.order],
                         [alternative.titles[key] for key in alternative.order])

    def test_a_reset_repeats_more_slowly_than_its_delay(self):                              # R121
        for variant, layout in self.layouts.items():
            pairs = set()
            for title in layout.presets:
                for group in layout.active(title).values():
                    for slot in group.get("inputs", {}).values():
                        found = [(entry.get("settings") or {}, layout.layer_ops(entry))
                                 for _, entry in entries(slot.get("activators", {}))]
                        for settings, ops in found:
                            delay = int(settings.get("delay_start") or 0)
                            for target in [layer for op, layer in ops if op == "add_layer"] if delay else []:
                                for reset, removed in found:
                                    if reset.get("hold_repeats") == "1" and removed == [("remove_layer", target)]:
                                        with self.subTest(variant, layer=title, target=target):
                                            self.assertGreater(int(reset.get("repeat_rate") or 0), delay)
                                        pairs.add((delay, reset.get("repeat_rate")))
            self.assertTrue(pairs, variant)

    def test_a_cleanup_input_stores_the_regular_press_then_the_guard_then_the_release(self):   # R133
        # The author, 2026-10-06: "the order: repeated removal of a regular press, then the guard, then a release.
        # That's how it should always be." The stored order is the order the Steam editor lists the entries in.
        for variant, layout in self.layouts.items():
            inputs = {(t.layer, t.source, t.input) for t in Cleanups(layout).inv.transitions if t.role == "recovery"}
            self.assertGreater(len(inputs), 500, variant)
            for layer, source, name in sorted(inputs):
                stored = list(layout.active(layer)[source]["inputs"][name]["activators"])
                with self.subTest(variant, layer=layer, input=f"{source}/{name}"):
                    self.assertEqual(stored, [kind for kind in ("Full_Press", "chord", "release") if kind in stored])

    def test_every_value_is_one_the_editor_can_set(self):                                   # R173
        # resources/Steam Input JSON Structure.md, "Limits the Steam editor sets": at most 1000 ms; a D-pad outer
        # ring radius from 10,000 to 32,000; a D-pad layout from 0 to 3.
        for variant, layout in self.layouts.items():
            for title in layout.presets:
                for source, group in layout.active(title).items():
                    settings = group.get("settings") or {}
                    with self.subTest(variant, layer=title, source=source):
                        if group["mode"] == "dpad" and "edge_binding_radius" in settings and "joystick" in source:
                            self.assertTrue(10000 <= int(settings["edge_binding_radius"]) <= 32000)
                        if group["mode"] == "dpad" and "layout" in settings:
                            self.assertIn(settings["layout"], {"0", "1", "2", "3"})
                        for slot in group.get("inputs", {}).values():
                            for _, entry in entries(slot.get("activators", {})):
                                for key in ("delay_start", "delay_end", "repeat_rate"):
                                    self.assertLessEqual(int((entry.get("settings") or {}).get(key) or 0), 1000)

    def test_every_snapshot_holds_both_layouts_under_its_own_version(self):                 # R151
        folders = [folder for folder in changes.VERSIONS.iterdir() if folder.is_dir() and changes.version(folder.name)]
        self.assertTrue(folders)
        for folder in folders:
            for variant in VARIANTS:
                with self.subTest(folder.name, variant=variant):
                    # A named testing candidate has its own filename lineage;
                    # saving it must not advance the live layout's baseline.
                    snapshots = list(folder.glob(f"single-set-{variant}*_hold-gyro_{folder.name}.json"))
                    self.assertTrue(snapshots)
                    for snapshot in snapshots:
                        self.assertTrue(snapshot.with_suffix('.vdf').exists())
                        title = json.loads(snapshot.read_text(encoding="utf-8"))["controller_mappings"]["title"]
                        self.assertEqual(title.rsplit(" :: ", 1)[-1], folder.name)
        for variant in VARIANTS:
            working = layout_data(variant)["controller_mappings"]["title"]
            with self.subTest(variant):
                newest = changes.newest_snapshot(f"single-set-{variant}_hold-gyro_latest.json")
                self.assertGreaterEqual(changes.version(working), changes.version(newest.parent.name))


if __name__ == "__main__":
    unittest.main()
