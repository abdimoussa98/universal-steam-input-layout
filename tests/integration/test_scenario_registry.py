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
from unittest.mock import patch

from steam_layout import rules
from tests import scenario
from tests.support.discovery import resolve_tests
from tests.support.evidence import finalize_documents

ROOT = Path(__file__).resolve().parents[2]
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
        # In any order: scenarios register as their modules are imported, and the workflow's test parts import them
        # in another order than one run of the whole suite.
        self.assertCountEqual([meta.check for meta in scenario.for_rule("R136")], ["90.13 N2", "90.15 M1", "90.16 X1", "90.16 X2", "90.18 H3", "90.19 K3", "90.23 C1", "90.24 K6",
                          "90.30 W1", "90.30 W2", "90.30 W3", "90.30 W4", "90.34 E2", "90.34 E3", "90.35 S6"])

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
                        self.assertTrue(any(re.search(rf"def {test}\(", path.read_text(encoding="utf-8"))
                                            for path in resolve_tests(name, test)))
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
        # Candidate static tests can import their scenario module before the
        # live scenarios. Check attribution inside A8, not import order.
        a8 = self.report.split("\nA8 (", 1)[1].split("\n\n", 1)[0]
        self.assertIn("  Rules: R111\n", a8)
        self.assertIn("  90.10 T5  MenuAndTransitions.", a8)

    def test_the_release_list_is_written_into_the_record(self):
        observed = {("neptune", "default"): {"Base"}}
        matrix = [{"controller": "neptune", "variant": "default", "titles": ["Base"], "changed": []}]
        with tempfile.TemporaryDirectory() as folder, contextlib.redirect_stdout(io.StringIO()) as shown, \
                patch.object(scenario, "coverage_manifest", return_value=matrix):
            self.assertEqual(scenario.main(["--out", folder], executor=lambda: observed), 0)
            self.assertIn("Changed since the newest snapshot and in no scenario (R165): none", shown.getvalue())
            self.assertEqual((Path(folder) / scenario.RELEASE_LIST).read_text(encoding="utf-8"), self.report + "\n")


class ReachTests(unittest.TestCase):
    """R165 bookkeeping on explicit synthetic evidence; the full runner gates live reach."""

    def evidence(self, layers=("Base", "Steering"), kind="live"):
        identity = "synthetic.Case.test_gesture"
        contract = {"kind": kind, "controller": "neptune", "source_controller": "neptune",
                    "version": "90.41" if kind == "frozen" else None, "variants": ["default"],
                    "stage": "controller", "rules": [], "rests": [], "either": [], "switches": {}}
        manifest = {"schema": 1, "inputs": "fixture", "tests": {
            identity: {"scenario": "fixture", "expected_failure": False, "contract": contract}}, "coverage": [
                {"controller": "neptune", "variant": "default", "version": "1.0", "fingerprint": "source",
                 "titles": ["Base", "Steering"], "changed": ["Steering"], "required": ["Base"]}]}
        record = {"id": identity, "scenario": "fixture", "expected_failure": False, "outcome": "success",
                  "contract": contract, "cell_count": 1,
                  "cells": [{"controller": "neptune", "source_controller": "neptune", "variant": "default",
                             "kind": kind, "version": "90.41" if kind == "frozen" else "1.0",
                             "stage": "controller", "options": {}, "start": None,
                             "fingerprint": "source", "reached": list(layers)}]}
        artifact = {"schema": 1, "run_id": "fixture", "manifest": manifest, "shard": {"index": 1, "count": 1},
                    "selected": [identity], "successful": True, "records": [record]}
        return artifact, manifest

    def test_every_changed_layer_is_on_the_stack_in_a_scenario(self):
        artifact, manifest = self.evidence()
        self.assertEqual(finalize_documents([artifact], manifest, run_id="fixture"),
                         {("neptune", "default"): {"Base", "Steering"}})

    def test_a_frozen_scenario_does_not_count_as_live_coverage(self):
        class Historical(scenario.ScenarioCase):
            def runTest(self):
                pass

        # Attach metadata directly so this harness test adds no registry entry.
        Historical.runTest.scenario = scenario.Meta('fixture', 'fixture', (), (), (), '90.41')
        historical = Historical()
        # The data source is incidental to this bookkeeping check; historical
        # interaction scenarios separately exercise the actual frozen builder.
        data = {"controller_mappings": {"actions": {"Base": {"title": "Base"}},
                "action_layers": {"Preset_0": {"title": "Steering"}}, "group": [],
                "preset": [{"name": "Base", "group_source_bindings": {}},
                           {"name": "Preset_0", "group_source_bindings": {}}]}}
        with patch.object(scenario, 'REACHED', {}), patch.object(scenario, 'FROZEN_REACHED', {}), \
                patch.object(scenario, 'frozen_layout_data', return_value=data) as frozen:
            for pad in historical.each(start=('Base', 'Steering'), variants=('default',)):
                self.assertTrue(pad.has('Steering'))
            frozen.assert_called_once_with('default', '90.41')
            self.assertEqual(scenario.REACHED, {})
            self.assertIn('Steering', scenario.FROZEN_REACHED['90.41', 'default'])
        artifact, manifest = self.evidence(kind="frozen")
        with self.assertRaisesRegex(ValueError, "No live scenario"):
            finalize_documents([artifact], manifest, run_id="fixture")

    def test_the_scenarios_reach_the_layers_they_are_about(self):
        artifact, manifest = self.evidence(layers=("Base", "Steering", "Missing layer"))
        with self.assertRaisesRegex(ValueError, "Unknown reached layer"):
            finalize_documents([artifact], manifest, run_id="fixture")
        artifact, manifest = self.evidence(layers=("Steering",))
        with self.assertRaisesRegex(ValueError, "Missing established scenario reach"):
            finalize_documents([artifact], manifest, run_id="fixture")

    def test_a_changed_layer_that_no_scenario_reaches_is_reported(self):
        """A changed layer missing from recorded reach must fail coverage.

        Since 90.47 both touch-gyro layers have real double-tap scenarios;
        simulate a missing record instead of depending on a coverage gap.
        """
        artifact, manifest = self.evidence(layers=("Base",))
        with self.assertRaisesRegex(ValueError, "R165.*Steering"):
            finalize_documents([artifact], manifest, run_id="fixture")
        with patch.object(scenario, "REACHED", {("neptune", "default"): {"Base"}}), \
                patch.object(scenario, "layout_data", return_value={}), \
                patch.object(scenario.changes, "baseline_for", return_value=None), \
                patch.object(scenario.changes, "changed_since", return_value={"Steering"}):
            self.assertEqual(scenario.uncovered("default", controller="neptune"), ["Steering"])


if __name__ == "__main__":
    unittest.main()
