"""The rule registry: the rule tables in resources/Layer Definition of Done.md (steam_layout/rules.py)."""
from pathlib import Path
import re
import subprocess
import sys
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
        scenarios = read(HEAD + row(checked="Build audit; Scenario tests (part)"))["R101"]
        self.assertEqual(scenarios.checked_by[1], rules.Checker("scenario", None, None, True))

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
                ("scenario tests that claim to cover everything", HEAD + row(checked="Scenario tests")),
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
                  *sorted((ROOT / "skills").glob("*/SKILL.md")), *sorted(ROOT.glob("audit_*.py")),
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

    def test_only_the_retired_rule_names_the_deck_checklist(self):
        """Phase 15: nothing in the definition of done waits for a Deck check. R155 keeps its row, retired."""
        self.assertEqual(self.rules["R155"].checked_by[0].kind, "retired")
        lines = rules.REGISTRY.read_text(encoding="utf-8").splitlines()
        named = [line[:40] for line in lines if re.search(r"\bDeck\b|manual-testing|manual testing", line)]
        self.assertEqual(named, [line[:40] for line in lines if line.startswith("| R155 |")])


class DeclarationTests(unittest.TestCase):
    """The audits and fixes say which rules they enforce; the registry says what checks each rule."""

    @classmethod
    def setUpClass(cls):
        cls.rules = rules.load()
        cls.declared = rules.declared()

    def checked_by(self, rule_id, kind):
        return {(c.name, c.check) for c in self.rules[rule_id].checked_by if c.kind == kind}

    def test_every_declared_check_names_a_rule_that_lists_it(self):
        self.assertTrue(self.declared)
        for (kind, name, check), ids in self.declared.items():
            for rule_id in ids:
                with self.subTest(checker=f"{name} {check or ''}".strip(), rule=rule_id):
                    self.assertIn(rule_id, self.rules)
                    self.assertIn((name, check), self.checked_by(rule_id, kind))

    def test_every_audit_and_fix_the_registry_names_declares_that_rule(self):
        for rule in self.rules.values():
            for checker in rule.checked_by:
                if checker.kind in ("audit", "fix"):
                    with self.subTest(rule=rule.id, checker=f"{checker.name} {checker.check or ''}".strip()):
                        self.assertIn(rule.id, self.declared.get((checker.kind, checker.name, checker.check), ()))

    def test_every_audit_and_every_fix_declares_something(self):
        audits = {name for kind, name, _ in self.declared if kind == "audit"}
        self.assertEqual(audits, set(rules.AUDITS))
        self.assertEqual({name for kind, name, _ in self.declared if kind == "fix"}, {name for name, _ in PIPELINE})

    def test_tag_prints_the_ids_in_brackets(self):
        self.assertEqual(rules.tag(("R127", "R131")), "[R127, R131]")

    def test_the_build_audit_prints_its_rule(self):
        out = subprocess.run([sys.executable, str(ROOT / "audit_build.py"), str(ROOT / "no-such-layout.json")],
                             capture_output=True, text=True)
        self.assertEqual(out.returncode, 1)
        self.assertIn("Build audit [R150]: 4 audit(s) failed", out.stdout)

    def test_unchecked_lists_the_rules_nothing_fails_on(self):
        nothing, partly = rules.unchecked(self.rules)
        self.assertIn("R112", nothing)                 # "nothing depends on a chord hand-over" has no check
        self.assertIn("R137", partly)                  # one test, on the two temporary guards only
        self.assertNotIn("R108", nothing + partly)     # the Budget audit fails on it
        self.assertFalse(set(nothing) & set(partly))


AHEAD = ("| ID | Assumption | Status | The layout | How to verify on the Deck | What rests on it |\n"
         "|---|---|---|---|---|---|\n")


def arow(assumption_id="A1", status="Verified by the author, 2026-09-29", layout="Relies on it", rests="R113, R115"):
    return f"| {assumption_id} | Steam does the thing | {status} | {layout} | Hold a button, add a layer | {rests} |\n"


class AssumptionReaderTests(unittest.TestCase):
    def read(self, text):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "assumptions.md"
            path.write_text(text, encoding="utf-8")
            return rules.load_assumptions(path)

    def test_an_assumption_table_is_read(self):
        found = self.read("# Doc\n\n" + AHEAD + arow() + arow("A2", "Unverified", "Works either way", "R114; held-input replay"))
        self.assertEqual(list(found), ["A1", "A2"])
        first, second = found["A1"], found["A2"]
        self.assertEqual((first.status, first.verified, first.layout, first.rules), ("Verified by the author, 2026-09-29", True, "Relies on it", ("R113", "R115")))
        self.assertEqual((second.verified, second.layout, second.rules), (False, "Works either way", ("R114",)))

    def test_bad_rows_are_rejected(self):
        for label, text in (("a duplicate ID", AHEAD + arow() + arow()),
                            ("a bad ID", AHEAD + arow("B1")),
                            ("an unknown status", AHEAD + arow(status="Probably")),
                            ("an unknown layout flag", AHEAD + arow(layout="Maybe")),
                            ("an empty field", AHEAD + arow(rests=""))):
            with self.subTest(label):
                with self.assertRaises(ValueError):
                    self.read(text)

    def test_reported_and_refuted_are_statuses_too(self):
        found = self.read(AHEAD + arow(status="Reported by the author, not isolated") + arow("A2", "Refuted on the Deck, 2026-10-03"))
        self.assertEqual([a.verified for a in found.values()], [False, False])


class AssumptionTests(unittest.TestCase):
    """resources/Steam Behaviour Assumptions.md against the rule registry."""

    @classmethod
    def setUpClass(cls):
        cls.rules = rules.load()
        cls.assumptions = rules.load_assumptions()

    def test_every_assumption_a_rule_rests_on_exists(self):
        self.assertTrue(self.assumptions)
        for rule in self.rules.values():
            with self.subTest(rule.id):
                self.assertFalse(set(rule.rests_on) - set(self.assumptions))

    def test_rests_on_and_what_rests_on_it_agree(self):
        for assumption in self.assumptions.values():
            resting = {rule.id for rule in self.rules.values() if assumption.id in rule.rests_on}
            with self.subTest(assumption.id):
                self.assertEqual(set(assumption.rules), resting)

    def test_an_unverified_assumption_says_whether_the_layout_relies_on_it(self):
        for assumption in self.assumptions.values():
            if not assumption.verified:
                with self.subTest(assumption.id):
                    self.assertIn(assumption.layout, ("Relies on it", "Works either way"))

    def test_assumption_ids_named_elsewhere_exist(self):
        places = [ROOT / "README.md", ROOT / "todos.md", *sorted((ROOT / "resources").glob("*.md")),
                  *sorted((ROOT / "skills").glob("*/SKILL.md")), *sorted(ROOT.glob("audit_*.py")),
                  *sorted((ROOT / "steam_layout").rglob("*.py")), *sorted((ROOT / "tests").glob("test_*.py"))]
        for path in places:
            if path.name in (Path(__file__).name, "rules.py"):
                continue                               # their own examples of the ID shape
            unknown = rules.assumption_references(path.read_text(encoding="utf-8")) - set(self.assumptions)
            with self.subTest(path.relative_to(ROOT).as_posix()):
                self.assertFalse(unknown)


class SkillTests(unittest.TestCase):
    """A skill restates a rule in one line next to its ID, so an agent has it in front of it."""

    def test_every_skill_names_rules_that_exist(self):
        known = set(rules.load())
        skills = sorted((ROOT / "skills").glob("*/SKILL.md"))
        self.assertTrue(skills)
        for path in skills:
            with self.subTest(path.parent.name):
                self.assertFalse(rules.references(path.read_text(encoding="utf-8")) - known)


if __name__ == "__main__":
    unittest.main()
