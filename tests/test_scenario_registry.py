"""The scenario tests against the rule registry, the assumptions, the layers that changed, and the
sorting of the retired Deck checklist."""
import contextlib
import copy
import importlib.util
import io
import json
from pathlib import Path
import re
import tempfile
import unittest

from steam_layout import rules
from tests import scenario

ROOT = Path(__file__).resolve().parents[1]
SORTING = ROOT / "findings/2026-10-03-deck-check-sorting/sorting.py"


def sorting():
    spec = importlib.util.spec_from_file_location("deck_check_sorting", SORTING)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ScenarioRegistryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = scenario.report()                 # imports every tests/test_scenarios_*.py
        cls.scenarios = list(scenario.SCENARIOS)
        cls.sort = sorting().SORT
        cls.rules, cls.assumptions = rules.load(), rules.load_assumptions()

    def test_a_label_from_the_retired_checklist_names_a_check_sorted_as_a_scenario(self):
        """A scenario written since carries its own label (the release and a number), which the sorting doesn't know."""
        self.assertTrue(self.scenarios)
        sections = {section for section, _ in self.sort}
        for meta in self.scenarios:
            section, check = meta.check.rsplit(" ", 1)
            with self.subTest(meta.name):
                if section in sections:
                    self.assertEqual(self.sort.get((section, check), ("missing",))[0], "Scenario", meta.check)

    def test_a_label_names_one_scenario(self):
        labels = [meta.check for meta in self.scenarios]
        self.assertEqual(sorted(labels), sorted(set(labels)))

    def test_a_rule_lists_the_scenario_tests_exactly_when_a_scenario_names_it(self):
        named = {rule for meta in self.scenarios for rule in meta.rules}
        listed = {rule.id for rule in self.rules.values() if any(c.kind == "scenario" for c in rule.checked_by)}
        self.assertEqual(sorted(named - listed), [], 'add "Scenario tests (part)" to these rules\' "Checked by"')
        self.assertEqual(sorted(listed - named), [], "no scenario names these rules")
        self.assertEqual([meta.check for meta in scenario.for_rule("R136")], ["90.11 F8", "90.13 N2", "90.15 M1"])

    def test_the_rules_and_assumptions_a_scenario_names_exist(self):
        for meta in self.scenarios:
            with self.subTest(meta.name):
                self.assertFalse(set(meta.rules) - set(self.rules))
                self.assertFalse(set(meta.rests) - set(self.assumptions))

    def test_an_either_way_assumption_is_run_both_ways(self):
        for meta in self.scenarios:
            switches = set(meta.rests) & set(scenario.SWITCHES)
            with self.subTest(meta.name):
                self.assertEqual(switches, set(meta.either))

    def test_every_migrated_check_went_somewhere_that_exists(self):
        """The migration record (phase 14): a check leaves the Deck checklist only for something real."""
        went = sorting().WENT
        replaced = {meta.check for meta in self.scenarios}
        notes = rules.ASSUMPTIONS.read_text(encoding="utf-8").split("## Tuning notes")[-1]
        for (section, check), where in went.items():
            kind, key = self.sort[(section, check)][0], f"{section} {check}"
            with self.subTest(key):
                self.assertTrue(where.strip())
                if kind == "Scenario":
                    same = re.match(r"Same as (.+)$", where)
                    self.assertIn(same.group(1) if same else key, replaced)
                elif kind == "Static":
                    named = re.findall(r"`(test_\w+)\.(test_\w+)`", where)
                    self.assertTrue(named, where)
                    for name, test in named:
                        self.assertRegex((ROOT / "tests" / f"{name}.py").read_text(encoding="utf-8"), rf"def {test}\(")
                elif kind == "Assumption":
                    named = rules.assumption_references(where)
                    self.assertTrue(named and named <= set(self.assumptions), where)
                elif kind == "Tuning":
                    self.assertIn(key, notes)

    def test_every_check_of_the_retired_checklist_went_somewhere(self):
        module = sorting()
        self.assertEqual(len(module.checks()), 137)                   # the checklist as it was frozen
        self.assertEqual(set(module.WENT), set(module.SORT))
        self.assertEqual(module.remaining(), set())                   # manual-testing.md holds no check any more

    def test_the_record_and_the_checklist_agree(self):
        module = sorting()
        left = module.remaining()
        self.assertFalse([key for key in module.WENT if key in left])               # migrated, but still listed
        self.assertFalse([key for key in module.SORT if key not in module.WENT and key not in left])   # lost

    def test_the_report_lists_the_scenarios_that_rest_on_something_unverified(self):
        self.assertIn("Resting on an assumption that isn't verified", self.report)
        unverified = {a for meta in self.scenarios for a in meta.rests if not self.assumptions[a].verified}
        for assumption in unverified:
            self.assertIn(f"\n{assumption} (", self.report)

    def test_the_report_lists_every_assumption_that_is_not_verified_with_the_rules_resting_on_it(self):
        """R167: this is the list a release's record carries."""
        for entry in self.assumptions.values():
            with self.subTest(entry.id):
                self.assertEqual(f"\n{entry.id} (" in self.report, not entry.verified)
        self.assertIn("\nA8 (unverified; relies on it)", self.report)
        self.assertIn("  Rules: R111, R137\n  90.10 T5  MenuAndTransitions.", self.report)

    def test_the_release_list_is_written_into_the_record(self):
        with tempfile.TemporaryDirectory() as folder, contextlib.redirect_stdout(io.StringIO()) as shown:
            scenario.main(["--out", folder])
            self.assertIn("Changed since the newest snapshot and in no scenario (R165): none", shown.getvalue())
            self.assertEqual((Path(folder) / scenario.RELEASE_LIST).read_text(encoding="utf-8"), self.report + "\n")


class ReachTests(unittest.TestCase):
    """R165: a layer that is new or changed since the newest snapshot is on the stack in some scenario."""

    @classmethod
    def setUpClass(cls):
        cls.reached = scenario.reached()               # runs every scenario test once

    def test_every_changed_layer_is_on_the_stack_in_a_scenario(self):
        for variant in scenario.VARIANTS:
            with self.subTest(variant):
                self.assertEqual(scenario.uncovered(variant), [], "write a scenario that reaches these layers")

    def test_the_scenarios_reach_the_layers_they_are_about(self):
        for variant in scenario.VARIANTS:
            pad = scenario.Pad(variant)
            with self.subTest(variant):
                self.assertTrue(pad.has("Base"))
                for title in ("Steering", "Steering | LS: Fallback Hold", "L1: Modifier 0", "Menu Right: Entry Point"):
                    self.assertIn(pad.title(title), self.reached[variant])
                self.assertLessEqual(self.reached[variant], set(pad.layout.titles.values()))

    def test_a_changed_layer_that_no_scenario_reaches_is_reported(self):
        """`Tab` is added by a left-pad swipe, which no scenario makes."""
        title = "Tab"
        for variant in scenario.VARIANTS:
            before = copy.deepcopy(scenario.layout_data(variant))
            layers = before["controller_mappings"]["action_layers"]
            key = next(key for key, layer in layers.items() if layer["title"] == title)
            layers[key]["title"] = "An older name"
            with self.subTest(variant), tempfile.TemporaryDirectory() as folder:
                baseline = Path(folder) / "before.json"
                baseline.write_text(json.dumps(before), encoding="utf-8")
                self.assertNotIn(title, self.reached[variant])
                self.assertIn(title, scenario.uncovered(variant, baseline))


if __name__ == "__main__":
    unittest.main()
