"""Test fixture reuse preserves independent mutations, source revisions and stored order."""
import json
from pathlib import Path
import tempfile
import unittest

from tests.support.sources import load_json, neptune_bundle, without_release_text


class SourceTests(unittest.TestCase):
    def test_neptune_bundles_isolate_mutations_and_keep_their_indexes_connected(self):
        data = {"controller_mappings": {
            "actions": {"Preset_1": {"title": "Base"}},
            "action_layers": {"Preset_2": {"title": "Layer", "parent_set_name": "Preset_1"}},
            "group": [{"id": "7", "mode": "switches", "inputs": {"button_a": {
                "activators": {"Full_Press": {"bindings": {
                    "binding": "controller_action add_layer 2 0 0, , "}}}}}}],
            "preset": [{"id": "0", "name": "Preset_1", "group_source_bindings": {"7": "switch active"}},
                       {"id": "1", "name": "Preset_2", "group_source_bindings": {}}],
        }}
        raw = json.dumps(data)
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "layout.json"
            path.write_text(raw, encoding="utf-8")
            first, second = neptune_bundle(path), neptune_bundle(path)
            baseline = json.dumps(second)
            for bundle in (first, second):
                self.assertIs(bundle["groups"]["7"], bundle["cm"]["group"][0])
                self.assertIs(bundle["presets"]["Base"], bundle["cm"]["preset"][0])
                self.assertEqual(bundle["count"], 1)
                self.assertIn("controller_action add_layer {{Base::Layer}} 0 0", bundle["readable"])

            # Mutants use these indexes: they must edit their own readable view, never another load.
            bindings = first["groups"]["7"]["inputs"]["button_a"]["activators"]["Full_Press"]["bindings"]
            bindings["binding"] = "key_press K, , "
            first["presets"]["Base"]["group_source_bindings"].clear()
            self.assertEqual(first["cm"]["preset"][0]["group_source_bindings"], {})
            self.assertEqual(first["original"], data)
            first["original"]["controller_mappings"]["action_layers"]["Preset_2"]["title"] = "Changed"
            first["lookup"]["detailed"][1]["title"] = "Changed"

            self.assertEqual(json.dumps(second), baseline)
            self.assertEqual(json.dumps(neptune_bundle(path)), baseline)
            self.assertEqual(load_json(path, strict=True), data)
            self.assertEqual(path.read_text(encoding="utf-8"), raw)

    def test_mutating_a_loaded_source_does_not_change_the_next_copy(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "source.json"
            path.write_text('{"second": [2], "first": [1]}', encoding="utf-8")
            first = load_json(path)
            first["second"].append(3)
            second = load_json(path)
            self.assertEqual(second, {"second": [2], "first": [1]})
            self.assertEqual(list(second), ["second", "first"])

    def test_replacing_a_source_at_the_same_path_invalidates_the_parse(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "source.json"
            path.write_text('{"value": 1}', encoding="utf-8")
            self.assertEqual(load_json(path)["value"], 1)
            path.write_text('{"value": 2}', encoding="utf-8")
            self.assertEqual(load_json(path)["value"], 2)

    def test_duplicate_key_detection_is_not_bypassed_by_a_permissive_parse(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "source.json"
            path.write_text('{"value": 1, "value": 2}', encoding="utf-8")
            self.assertEqual(load_json(path)["value"], 2)
            with self.assertRaises(ValueError):
                load_json(path, strict=True)

    def test_release_normalization_preserves_the_source_and_remaining_order(self):
        data = {"controller_mappings": {"title": "test", "second": [2], "description": "text", "first": [1]}}
        before = json.dumps(data)
        normalized = without_release_text(data)
        self.assertEqual(list(normalized["controller_mappings"]), ["second", "first"])
        normalized["controller_mappings"]["second"].append(3)
        self.assertEqual(json.dumps(data), before)
