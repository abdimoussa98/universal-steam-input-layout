"""The change report: what differs between two layouts, by layer and input (steam_layout/changes.py)."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from steam_layout import changes
from tests.test_audit_inheritance import EMPTY, act, add, build, remove

ROOT = Path(__file__).resolve().parents[1]
KEY = "key_press W, , "


def base():
    return build({"Base": {"switch": ("switches", {"button_a": act(add("P")), "button_b": act(KEY)})},
                  "P": {"switch": ("switches", {"button_a": act(remove("P"))})}})


def group(data, title, source="switch"):
    cm = data["controller_mappings"]
    names = {v["title"]: k for section in ("actions", "action_layers") for k, v in cm[section].items()}
    preset = next(p for p in cm["preset"] if p["name"] == names[title])
    gid = next(g for g, state in preset["group_source_bindings"].items() if state.startswith(source + " "))
    return next(g for g in cm["group"] if g["id"] == gid)


class DiffTests(unittest.TestCase):
    def changed(self, before, after):
        return [(layer, c["source"], c["input"], c["what"])
                for layer, rows in changes.diff(before, after)["layers"].items() for c in rows]

    def test_identical_layouts_have_no_changes(self):
        report = changes.diff(base(), base())
        self.assertEqual((report["added"], report["removed"], report["layers"]), ([], [], {}))
        self.assertEqual(changes.changed_layers(report), set())

    def test_a_changed_binding_is_reported_on_its_layer_and_input(self):
        after = base()
        group(after, "P")["inputs"]["button_a"]["activators"] = act(EMPTY)
        report = changes.diff(base(), after)
        self.assertEqual(self.changed(base(), after), [("P", "switch", "button_a", "binding")])
        row = report["layers"]["P"][0]
        self.assertEqual((row["before"], row["after"]), (["Full_Press: remove_layer P"], ["Full_Press: empty_binding"]))

    def test_added_and_removed_inputs(self):
        after = base()
        inputs = group(after, "Base")["inputs"]
        del inputs["button_b"]
        inputs["button_x"] = {"activators": act(KEY)}
        self.assertEqual(self.changed(base(), after), [("Base", "switch", "button_b", "input removed"),
                                                       ("Base", "switch", "button_x", "input added")])

    def test_a_setting_or_mode_change_is_reported_on_the_group(self):
        after = base()
        group(after, "P").update(mode="dpad", settings={"edge_binding_invert": "1"})
        self.assertEqual(self.changed(base(), after), [("P", "switch", None, "mode"), ("P", "switch", None, "settings")])

    def test_an_activator_setting_counts_as_a_binding_change(self):
        after = base()
        group(after, "P")["inputs"]["button_a"]["activators"] = act(remove("P"), hold_repeats="1")
        row = changes.diff(base(), after)["layers"]["P"][0]
        self.assertEqual(row["after"], ["Full_Press(hold_repeats=1): remove_layer P"])

    def test_new_and_removed_layers_and_sources(self):
        after = build({"Base": {"switch": ("switches", {"button_a": act(add("P")), "button_b": act(KEY)}),
                                "joystick": ("dpad", {"click": act(KEY)})},
                       "P": {"switch": ("switches", {"button_a": act(remove("P"))})},
                       "N": {"switch": ("switches", {"button_a": act(KEY)})}})
        report = changes.diff(base(), after)
        self.assertEqual((report["added"], report["removed"]), (["N"], []))
        self.assertEqual(self.changed(base(), after), [("Base", "joystick", None, "source added")])
        self.assertEqual(changes.changed_layers(report), {"Base", "N"})
        back = changes.diff(after, base())
        self.assertEqual((back["added"], back["removed"]), ([], ["N"]))

    def test_a_shifted_runtime_id_is_not_a_change(self):
        # The same bindings by numeric ID: inserting a layer shifts P from 2 to 3.
        def numeric(layers, target):
            data = build(layers)
            text = json.dumps(data).replace("{{Base::P}}", str(target))
            return json.loads(text)
        before = numeric({"Base": {"switch": ("switches", {"button_a": act(add("P"))})},
                          "P": {"switch": ("switches", {"button_a": act(remove("P"))})}}, 2)
        after = numeric({"Base": {"switch": ("switches", {"button_a": act(add("P"))})},
                         "N": {"switch": ("switches", {"button_b": act(KEY)})},
                         "P": {"switch": ("switches", {"button_a": act(remove("P"))})}}, 3)
        report = changes.diff(before, after)
        self.assertEqual((report["added"], report["layers"]), (["N"], {}))

    def test_a_mode_shift_target_is_compared_by_content_not_group_id(self):
        shifted = {"9": ("joystick", "dpad", {"click": act(KEY)})}
        before = build({"Base": {"switch": ("switches", {"button_a": act("mode_shift joystick 9, , ")})}}, shifted)
        after = copy.deepcopy(before)
        cm = after["controller_mappings"]
        next(g for g in cm["group"] if g["id"] == "9")["id"] = "77"
        cm["preset"][0]["group_source_bindings"]["77"] = cm["preset"][0]["group_source_bindings"].pop("9")
        group(after, "Base")["inputs"]["button_a"]["activators"] = act("mode_shift joystick 77, , ")
        self.assertEqual(changes.diff(before, after)["layers"], {})
        next(g for g in cm["group"] if g["id"] == "77")["inputs"]["click"]["activators"] = act(EMPTY)
        self.assertEqual(self.changed(before, after), [("Base", "joystick mode shift", "click", "binding")])

    def test_text_names_the_layer_the_input_and_both_sides(self):
        after = base()
        group(after, "P")["inputs"]["button_a"]["activators"] = act(EMPTY)
        text = changes.text(changes.diff(base(), after), "before.json", "after.json")
        for part in ("== P", "switch/button_a", "before: Full_Press: remove_layer P", "after:  Full_Press: empty_binding",
                     "1 layer changed, 1 change"):
            self.assertIn(part, text)
        self.assertIn("No changes", changes.text(changes.diff(base(), base()), "a", "b"))


class SnapshotTests(unittest.TestCase):
    def test_the_newest_snapshot_is_found_by_version_number(self):
        with tempfile.TemporaryDirectory() as tmp:
            for version in ("90.9", "90.10", "90.2"):
                folder = Path(tmp, version)
                folder.mkdir()
                (folder / f"single-set-default_hold-gyro_{version}.json").write_text("{}")
            found = changes.newest_snapshot("single-set-default_hold-gyro_latest.json", Path(tmp))
            self.assertEqual(found.name, "single-set-default_hold-gyro_90.10.json")
            self.assertIsNone(changes.newest_snapshot("single-set-alternative_hold-gyro_latest.json", Path(tmp)))

    def test_90_12_to_90_13_shows_the_change_nobody_decided(self):
        # In 90.13 the window_routes fix changed the Steering stick windows; it was only noticed by diffing.
        def snapshot(version):
            path = ROOT / f"versions/neptune/{version}/single-set-default_hold-gyro_{version}.json"
            return json.loads(path.read_text(encoding="utf-8"))
        report = changes.diff(snapshot("90.12"), snapshot("90.13"))
        self.assertEqual((report["added"], report["removed"]), ([], []))
        self.assertIn("Steering", report["layers"])                           # the decided change: no turn assist
        self.assertIn("Steering | LS Up: Double Tap", report["layers"])       # the one the fix made on its own


class ScriptTests(unittest.TestCase):
    def run_script(self, *args):
        return subprocess.run([sys.executable, "-m", "tools.change_report", *args], capture_output=True, text=True,
                              cwd=ROOT)

    def test_two_files_and_out(self):
        after = base()
        group(after, "P")["inputs"]["button_a"]["activators"] = act(EMPTY)
        with tempfile.TemporaryDirectory() as tmp:
            a, b, out = Path(tmp, "a.json"), Path(tmp, "b.json"), Path(tmp, "out")
            a.write_text(json.dumps(base()))
            b.write_text(json.dumps(after))
            result = self.run_script(str(a), str(b), "--out", str(out))
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("== P", result.stdout)
            self.assertIn("== P", (out / "b-changes.txt").read_text())
            report = json.loads(self.run_script(str(a), str(b), "--json").stdout)
            self.assertEqual(list(report[0]["layers"]), ["P"])
            self.assertEqual(self.run_script(str(a), str(Path(tmp, "missing.json"))).returncode, 2)

    def test_the_working_layouts_against_their_newest_snapshot(self):
        result = self.run_script()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.count("Changes from "), 2)      # one report per working layout


if __name__ == "__main__":
    unittest.main()
