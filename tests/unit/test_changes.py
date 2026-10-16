"""The change report: what differs between two layouts, by layer and input (steam_layout/changes.py).

Fixture responsibility: unit. See docs/testing.md and tests/test-map.csv.
"""
from tests.support.fixtures.changes import *

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


if __name__ == "__main__":
    unittest.main()
