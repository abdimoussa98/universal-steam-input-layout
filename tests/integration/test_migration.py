"""The 2026-10-15 migration keeps every original check and scenario identity.

This reads collection metadata only; no case or fixture setup runs here.
New tests have their own canonical identities and need no historical alias.
"""
import csv
from pathlib import Path
import unittest

from tests.runner import collect
from tests.support.discovery import case_map

ROOT = Path(__file__).resolve().parents[2]


class MigrationTests(unittest.TestCase):
    def test_every_original_check_has_one_collected_owner(self):
        mapping = case_map()
        self.assertEqual(len(mapping), 1407)
        collected = [test.id() for test in collect()]
        self.assertEqual(len(collected), len(set(collected)))
        self.assertFalse(set(mapping.values()) - set(collected))

    def test_original_scenario_labels_and_expected_failures_are_preserved(self):
        collected = {test.id(): test for test in collect()}
        with (ROOT / "tests/test-map.csv").open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        labels = []
        for row in rows:
            test = collected[row["new_id"]]
            method = getattr(test, test._testMethodName)
            meta = getattr(method, "scenario", None)
            with self.subTest(old=row["old_id"]):
                self.assertEqual(meta.check if meta else "", row["scenario_label"])
                self.assertEqual(bool(getattr(method, "__unittest_expecting_failure__", False)),
                                 row["expected_failure"] == "yes")
            if meta:
                labels.append(meta.check)
        self.assertEqual(len(labels), 449)
        self.assertEqual(len(labels), len(set(labels)))
