"""The scenario tests against the sorting of the Deck checks, the rule registry and the assumptions."""
import importlib.util
from pathlib import Path
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

    def test_every_scenario_replaces_a_check_that_was_sorted_as_a_scenario(self):
        self.assertTrue(self.scenarios)
        for meta in self.scenarios:
            section, check = meta.check.rsplit(" ", 1)
            with self.subTest(meta.name):
                self.assertEqual(self.sort.get((section, check), ("missing",))[0], "Scenario", meta.check)

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

    def test_the_report_lists_the_scenarios_that_rest_on_something_unverified(self):
        self.assertIn("Resting on an assumption that isn't verified", self.report)
        unverified = {a for meta in self.scenarios for a in meta.rests if not self.assumptions[a].verified}
        for assumption in unverified:
            self.assertIn(f"\n{assumption} (", self.report)


if __name__ == "__main__":
    unittest.main()
