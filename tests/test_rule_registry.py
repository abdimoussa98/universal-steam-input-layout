"""The rule registry: the rule tables in resources/Layer Definition of Done.md (steam_layout/rules.py)."""
from pathlib import Path
import re
import tempfile
import unittest

from steam_layout import rules
from steam_layout.fixes import PIPELINE

ROOT = Path(__file__).resolve().parents[1]
HEAD = "| ID | Rule | Example | Decided | Checked by | Rests on | Exceptions |\n|---|---|---|---|---|---|---|\n"


def row(rule_id="R101", checked="Not checked yet", rests="—", statement="Do the thing"):
    return f"| {rule_id} | {statement} | `A` on `B` | Author, 2026-10-02 | {checked} | {rests} | None |\n"


def read(text):
    with tempfile.TemporaryDirectory() as folder:
        path = Path(folder) / "registry.md"
        path.write_text(text, encoding="utf-8")
        return rules.load(path)


class ReaderTests(unittest.TestCase):
    def test_a_rule_table_is_read_with_its_section(self):
        found = read("# Doc\n\n## 3. Activators\n\nText.\n\n" + HEAD + row() + row("R102") + "\nMore text.\n")
        self.assertEqual(list(found), ["R101", "R102"])
        rule = found["R101"]
        self.assertEqual((rule.statement, rule.example, rule.decided, rule.exceptions, rule.section),
                         ("Do the thing", "`A` on `B`", "Author, 2026-10-02", "None", "3. Activators"))
        self.assertEqual(rule.rests_on, ())

    def test_other_tables_are_ignored(self):
        found = read("| Type | Examples |\n|---|---|\n| Owner | Modifiers |\n\n" + HEAD + row())
        self.assertEqual(list(found), ["R101"])

    def test_an_escaped_pipe_stays_in_the_cell(self):
        found = read(HEAD + row(statement=r"`Steering \| LS: Entry Guard` stays"))
        self.assertEqual(found["R101"].statement, "`Steering | LS: Entry Guard` stays")

    def test_checked_by_forms(self):
        cell = ("Budget audit: banned activators; `cleanup_lists` fix; `test_fixes.test_pipeline_order`; "
                "`test_covers` (part); Build audit")
        self.assertEqual(read(HEAD + row(checked=cell))["R101"].checked_by, (
            rules.Checker("audit", "Budget", "banned activators", False),
            rules.Checker("fix", "cleanup_lists", None, False),
            rules.Checker("test", "test_fixes", "test_pipeline_order", False),
            rules.Checker("test", "test_covers", None, True),
            rules.Checker("audit", "Build", None, False)))
        self.assertEqual(read(HEAD + row())["R101"].checked_by, (rules.Checker("none", None, None, False),))
        retired = read(HEAD + row(checked="Retired, 2026-10-02: replaced by scenario tests"))["R101"]
        self.assertEqual(retired.checked_by[0].kind, "retired")

    def test_rests_on_lists_assumption_ids(self):
        self.assertEqual(read(HEAD + row(rests="A3, A12"))["R101"].rests_on, ("A3", "A12"))

    def test_bad_rows_are_rejected(self):
        for label, text in (
                ("a duplicate ID", HEAD + row() + row()),
                ("an ID below 101", HEAD + row("R7")),
                ("a missing cell", HEAD + "| R101 | Do the thing | Author |\n"),
                ("an empty field", HEAD + row(statement="")),
                ("an unknown checker", HEAD + row(checked="The author looks at it")),
                ("not checked beside a checker", HEAD + row(checked="Not checked yet; Build audit")),
                ("a bad assumption ID", HEAD + row(rests="gate 2"))):
            with self.subTest(label):
                with self.assertRaises(ValueError):
                    read(text)

    def test_references_finds_rule_ids_and_skips_buttons(self):
        self.assertEqual(rules.references("R1 held, see R108 and R140 (not R12 or R1000)"), {"R108", "R140"})


class RegistryTests(unittest.TestCase):
    """The Layer Definition of Done itself."""

    @classmethod
    def setUpClass(cls):
        cls.rules = rules.load()

    def test_the_definition_of_done_holds_the_rules(self):
        self.assertTrue(self.rules)
        for rule in self.rules.values():
            with self.subTest(rule.id):
                self.assertTrue(rule.section[0].isdigit(), rule.section)

    def test_named_tests_exist(self):
        for rule in self.rules.values():
            for checker in rule.checked_by:
                if checker.kind != "test":
                    continue
                with self.subTest(rule=rule.id, test=checker.name):
                    path = ROOT / "tests" / f"{checker.name}.py"
                    self.assertTrue(path.exists(), path.name)
                    if checker.check:
                        self.assertRegex(path.read_text(encoding="utf-8"), rf"def {checker.check}\(")

    def test_named_fixes_are_in_the_pipeline(self):
        names = {name for name, _ in PIPELINE}
        for rule in self.rules.values():
            for checker in rule.checked_by:
                if checker.kind == "fix":
                    with self.subTest(rule=rule.id):
                        self.assertIn(checker.name, names)

    def test_rule_ids_named_elsewhere_exist(self):
        places = [ROOT / "README.md", ROOT / "todos.md", *sorted((ROOT / "resources").glob("*.md")),
                  *sorted((ROOT / ".claude" / "skills").glob("*/SKILL.md")), *sorted(ROOT.glob("audit_*.py")),
                  *sorted((ROOT / "steam_layout").rglob("*.py")), *sorted((ROOT / "tests").glob("test_*.py"))]
        for path in places:
            if path.name == Path(__file__).name:
                continue
            unknown = rules.references(path.read_text(encoding="utf-8")) - set(self.rules)
            with self.subTest(path.relative_to(ROOT).as_posix()):
                self.assertFalse(unknown)

    def test_a_rule_names_only_rules_that_exist(self):
        for rule in self.rules.values():
            text = " ".join((rule.statement, rule.example, rule.exceptions))
            with self.subTest(rule.id):
                self.assertFalse(rules.references(text) - set(self.rules))


class SkillTests(unittest.TestCase):
    """A skill restates a rule in one line next to its ID, so an agent has it in front of it."""

    def test_every_skill_names_rules_that_exist(self):
        known = set(rules.load())
        skills = sorted((ROOT / ".claude" / "skills").glob("*/SKILL.md"))
        self.assertTrue(skills)
        for path in skills:
            with self.subTest(path.parent.name):
                self.assertFalse(rules.references(path.read_text(encoding="utf-8")) - known)


if __name__ == "__main__":
    unittest.main()
