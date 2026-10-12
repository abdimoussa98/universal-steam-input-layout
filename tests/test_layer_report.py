"""The per-layer report: the three questions and the cleanup lists (plan step 6).

Plan: plans/2026-10-01-backward-chain-audit.md.
"""
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest

from steam_layout.layer_report import report
from steam_layout.model import Layout
from tests.test_audit_inheritance import add, build, remove
from tests.test_chains import SW, press, release

ROOT = Path(__file__).resolve().parents[1]
KEY_K, KEY_X = "key_press K, , ", "key_press X, , "


def family(cover=None, exit_ops=None):
    """Base adds P; P's button_b adds a cover C on top; releasing button_a is P's exit. Ghost is never added."""
    return build({"Base": {"switch": (SW, {"button_a": press(add("P")), "button_k": press(KEY_K)})},
                  "P": {"switch": (SW, {"button_b": press(add("C")),
                                        "button_a": release(*(exit_ops or (remove("P"), remove("C"), remove("Ghost"))))})},
                  "C": {"switch": (SW, cover or {"button_x": press(KEY_X)})}, "Ghost": {}})


def rows(result, key):
    return {(row["source"], row["input"]): row for row in result[key]}


class ThreeQuestionTests(unittest.TestCase):
    def test_below_lists_the_layers_under_it_with_a_reason(self):
        result = report(Layout(family()), "C")
        self.assertTrue(result["reached"])
        self.assertEqual(list(result["below"]["layers"]), ["Base", "P"])
        self.assertEqual(result["below"]["stacks"], [{"stack": ["Base", "P"], "reason": [
            "Base switch/button_a Full_Press#0: +P", "P switch/button_b Full_Press#0: +C"]}])
        self.assertEqual(result["below"]["layers"]["P"], result["below"]["stacks"][0]["reason"])

    def test_above_lists_every_layer_that_has_it_underneath(self):
        result = report(Layout(family()), "P")
        self.assertEqual(list(result["above"]), ["C"])
        self.assertEqual(result["above"]["C"]["stack"], ["Base", "P"])

    def test_inherited_inputs_name_the_provider_and_its_binding(self):
        inherited = rows(report(Layout(family()), "C"), "inherited")
        self.assertEqual(set(inherited), {("switch", "button_a"), ("switch", "button_b"), ("switch", "button_k")})
        key = inherited[("switch", "button_k")]
        self.assertEqual(key["providers"], [{"layers": ["Base"], "bindings": [KEY_K], "changes_layers": None}])
        exit_ = inherited[("switch", "button_a")]
        self.assertEqual(exit_["providers"][0]["layers"], ["P"])
        self.assertEqual(exit_["providers"][0]["changes_layers"], "direct")

    def test_an_input_the_layer_binds_is_not_inherited(self):
        inherited = rows(report(Layout(family()), "C"), "inherited")
        self.assertNotIn(("switch", "button_x"), inherited)
        self.assertEqual(set(rows(report(Layout(family()), "P"), "inherited")), {("switch", "button_k")})

    def test_a_layer_never_reached_says_so(self):
        result = report(Layout(family()), "Ghost")
        self.assertFalse(result["reached"])
        self.assertEqual((result["below"], result["above"], result["inherited"], result["exits"]),
                         ({"layers": {}, "stacks": []}, {}, [], []))

    def test_an_unknown_layer_is_an_error(self):
        with self.assertRaises(ValueError):
            report(Layout(family()), "Nope")


class CleanupTests(unittest.TestCase):
    """Report only: what each exit removes against what can be on the stack with the layer."""

    def exit_row(self, data):
        exits = report(Layout(data), "P")["exits"]
        self.assertEqual([e["input"] for e in exits], ["switch/button_a"])
        return exits[0]

    def test_an_exit_lists_what_it_removes_that_is_present(self):
        row = self.exit_row(family())
        self.assertEqual(row["binding"], "P switch/button_a release#0: -P ; -C ; -Ghost")
        self.assertTrue(row["removes_itself"])
        self.assertEqual(row["present_and_removed"], ["C"])
        self.assertEqual(row["present_not_removed"], {"below": [], "above": []})

    def test_a_removal_of_a_layer_that_is_never_present_is_listed(self):
        self.assertEqual(self.exit_row(family())["removed_never_present"], ["Ghost"])

    def test_a_layer_above_that_the_exit_leaves_is_listed(self):
        row = self.exit_row(family(exit_ops=(remove("P"),)))
        self.assertEqual(row["present_not_removed"], {"below": [], "above": ["C"]})
        self.assertEqual(row["intercepted_by"], [])

    def test_a_layer_above_that_binds_the_exit_input_intercepts_it(self):
        row = self.exit_row(family(cover={"button_a": press(KEY_X)}, exit_ops=(remove("P"),)))
        self.assertEqual(row["intercepted_by"], ["C"])
        self.assertEqual(row["present_not_removed"], {"below": [], "above": []})

    def test_the_action_set_is_never_listed_as_left_behind(self):
        row = self.exit_row(family())
        self.assertNotIn("Base", row["present_not_removed"]["below"])


class CliTests(unittest.TestCase):
    def run_cli(self, data, *args):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp, "layout.json")
            path.write_text(json.dumps(data))
            return subprocess.run([sys.executable, "-m", "tools.audit_layer", str(path), *args],
                                  capture_output=True, text=True, cwd=ROOT)

    def test_text_report_has_the_four_sections(self):
        out = self.run_cli(family(), "--layer", "P")
        self.assertEqual(out.returncode, 0, out.stderr)
        for expected in ("Layer: P", "Below", "Above", "  C", "Inherited inputs", "switch/button_k from Base",
                         "Exits", "present and removed: C", "removed, never present: Ghost"):
            self.assertIn(expected, out.stdout)

    def test_exits_with_the_same_removals_and_lists_are_shown_once(self):
        data = build({"Base": {"switch": (SW, {"button_a": press(add("P"))})},
                      "P": {"switch": (SW, {"button_x": press(remove("P"), hold_repeats=1),
                                            "button_y": press(remove("P"), hold_repeats=1)})}})
        out = self.run_cli(data, "--layer", "P")
        self.assertIn("2 recovery bindings removing: P", out.stdout)
        self.assertIn("on: switch/button_x, switch/button_y", out.stdout)

    def test_layer_references_are_shown_as_titles(self):
        # The working layouts store runtime IDs: a layer's position in the list, starting at 1.
        ids = {title: str(index + 1) for index, title in enumerate(("Base", "P", "C", "Ghost"))}
        numeric = json.loads(re.sub(r"\{\{Base::(\w+)\}\}", lambda m: ids[m.group(1)], json.dumps(family())))
        self.assertNotIn("{{", json.dumps(numeric))
        out = self.run_cli(numeric, "--layer", "C")
        self.assertIn("switch/button_b from P: add_layer C  [changes layers]", out.stdout)

    def test_json_report(self):
        out = self.run_cli(family(), "--layer", "C", "--json")
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertEqual(list(json.loads(out.stdout)["below"]["layers"]), ["Base", "P"])

    def test_a_layer_never_reached_is_reported_not_shown_as_empty(self):
        out = self.run_cli(family(), "--layer", "Ghost")
        self.assertEqual(out.returncode, 0)
        self.assertIn("not reached", out.stdout)
        self.assertNotIn("Below", out.stdout)

    def test_an_unknown_layer_exits_2(self):
        self.assertEqual(self.run_cli(family(), "--layer", "Nope").returncode, 2)


class NeptuneReportTests(unittest.TestCase):
    def test_a_modifier_on_the_default_layout(self):
        layout = Layout(json.loads((ROOT / "neptune/single-set-default_hold-gyro_latest.json").read_text()))
        result = report(layout, "L1: Modifier 0")
        self.assertIn("LST: Entry Point", result["below"]["layers"])
        # Since 90.46 a bumper pressed in `Gyro Off Ramp Up` removes the ramps, so no ramp layer is under a
        # bumper modifier. Until 90.45 this test named that ramp layer as one that is.
        self.assertEqual([title for title in result["below"]["layers"] if "Ramp Up" in title], [])
        self.assertIn("L1: Temp Cursor Gyro", result["above"])
        release_exit = next(e for e in result["exits"] if e["input"] == "switch/left_bumper" and e["role"] == "release")
        self.assertIn("L1: Temp Cursor Gyro", release_exit["present_and_removed"])
        # Since 90.12 no list names a layer that can never be on the stack with it (cleanup rule 6);
        # the release used to remove the Gyro twin. The tiny layouts above cover the report itself.
        self.assertEqual(release_exit["removed_never_present"], [])


if __name__ == "__main__":
    unittest.main()
