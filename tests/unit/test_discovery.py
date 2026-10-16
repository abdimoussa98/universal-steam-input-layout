"""Discovery and historical references: synthetic trees, no test imports or walks."""
import csv
from pathlib import Path
import tempfile
import unittest

from tests.support.discovery import case_map, resolve_tests, test_modules


class DiscoveryTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)

    def write(self, name, text="raise RuntimeError('discovery must not import me')\n"):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def ledger(self, rows):
        path = self.write("tests/test-map.csv", "")
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(("old_id", "new_id"))
            writer.writerows(rows)

    def test_nested_active_modules_are_selected_without_importing_them(self):
        for path in ("tests/unit/test_one.py", "tests/contracts/dse/test_two.py",
                     "tests/support/helper.py", "tests/node/test_export.mjs",
                     "archived/tests/test_old.py", "overlay/tests/test_ignored.py"):
            self.write(path)
        self.assertEqual(test_modules(self.root),
                         ["tests.contracts.dse.test_two", "tests.unit.test_one"])

    def test_ambiguous_basename_requires_explicit_mapping(self):
        self.write("tests/unit/test_same.py")
        self.write("tests/integration/test_same.py")
        with self.assertRaisesRegex(ValueError, "ambiguous"):
            resolve_tests("test_same", root=self.root)
        self.assertEqual(resolve_tests("tests.unit.test_same", root=self.root),
                         [self.root / "tests/unit/test_same.py"])

    def test_old_module_and_method_resolve_across_a_recorded_split(self):
        one = self.write("tests/unit/test_one.py", "class Checks:\n def test_one(self): pass\n")
        two = self.write("tests/integration/test_two.py", "class Checks:\n def test_two(self): pass\n")
        self.ledger([("tests.test_old.Checks.test_one", "tests.unit.test_one.Checks.test_one"),
                     ("tests.test_old.Checks.test_two", "tests.integration.test_two.Checks.test_two")])
        self.assertCountEqual(resolve_tests("test_old", root=self.root), [one, two])
        self.assertEqual(resolve_tests("test_old", "test_two", root=self.root), [two])
        two.write_text("class Checks: pass\n")
        with self.assertRaisesRegex(ValueError, "missing test check"):
            resolve_tests("test_old", "test_two", root=self.root)

    def test_ledger_rejects_duplicate_or_missing_destinations(self):
        self.ledger([("tests.test_old.C.test_a", "tests.unit.test_new.C.test_a"),
                     ("tests.test_old.C.test_b", "tests.unit.test_new.C.test_a")])
        with self.assertRaisesRegex(ValueError, "duplicate"):
            case_map(self.root)
        self.ledger([("tests.test_old.C.test_a", "tests.unit.test_new.C.test_a")])
        with self.assertRaisesRegex(ValueError, "missing test reference"):
            resolve_tests("test_old", root=self.root)
