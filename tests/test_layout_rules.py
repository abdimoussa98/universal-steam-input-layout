"""Static checks for rules that nothing checked before (rule registry plan, phase 15).

Each asks what the layouts hold, with no presses. The rule is named beside the test, and the test is named
under that rule's "Checked by" in resources/Layer Definition of Done.md.
"""
import json
import re
import unittest

from steam_layout import changes, exceptions
from steam_layout.model import Layout, bindings, entries, map_title
from tests.scenario import RENAME, VARIANTS, layout_data

LEGACY_HOLDS = {"LTP: Arrow Keys", "RTP: Mouse Buttons"}      # R101's entry in the exceptions register


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

    def test_every_snapshot_holds_both_layouts_under_its_own_version(self):                 # R151
        folders = [folder for folder in changes.VERSIONS.iterdir() if folder.is_dir() and changes.version(folder.name)]
        self.assertTrue(folders)
        for folder in folders:
            for variant in VARIANTS:
                stem = folder / f"single-set-{variant}_hold-gyro_{folder.name}"
                with self.subTest(folder.name, variant=variant):
                    self.assertTrue(stem.with_name(stem.name + ".vdf").exists())
                    title = json.loads(stem.with_name(stem.name + ".json").read_text(encoding="utf-8"))["controller_mappings"]["title"]
                    self.assertEqual(title.rsplit(" :: ", 1)[-1], folder.name)
        newest = max(changes.version(folder.name) for folder in folders)
        for variant in VARIANTS:
            working = layout_data(variant)["controller_mappings"]["title"]
            with self.subTest(variant):
                self.assertGreaterEqual(changes.version(working), newest)


if __name__ == "__main__":
    unittest.main()
