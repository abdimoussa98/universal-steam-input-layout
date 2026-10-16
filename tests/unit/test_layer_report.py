"""The per-layer report: the three questions and the cleanup lists (plan step 6).

Plan: plans/2026-10-01-backward-chain-audit.md.

Fixture responsibility: unit. See docs/testing.md and tests/test-map.csv.
"""
from tests.support.fixtures.layer_report import *

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


if __name__ == "__main__":
    unittest.main()
