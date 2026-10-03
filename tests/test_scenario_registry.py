"""The scenario tests against the sorting of the Deck checks, the rule registry and the assumptions."""
import importlib.util
from pathlib import Path
import re
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


if __name__ == "__main__":
    unittest.main()
