"""The rule registry: the rule tables in resources/Layer Definition of Done.md (steam_layout/rules.py).

Fixture responsibility: integration. See docs/testing.md and tests/test-map.csv.
"""
from tests.support.fixtures.rule_registry import *

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
                    paths = resolve_tests(checker.name, checker.check)
                    self.assertTrue(paths)
                    if checker.check:
                        self.assertTrue(any(re.search(rf"def {checker.check}\(", path.read_text(encoding="utf-8"))
                                            for path in paths))

    def test_named_fixes_are_in_the_pipeline(self):
        names = {name for name, _ in PIPELINE}
        for rule in self.rules.values():
            for checker in rule.checked_by:
                if checker.kind == "fix":
                    with self.subTest(rule=rule.id):
                        self.assertIn(checker.name, names)

    def test_rule_ids_named_elsewhere_exist(self):
        places = [ROOT / "README.md", ROOT / "todos.md", *sorted((ROOT / "resources").glob("*.md")),
                  *sorted((ROOT / "docs").glob("*.md")),
                  *sorted((ROOT / "skills").glob("*/SKILL.md")), *sorted((ROOT / "tools").glob("audit_*.py")),
                  *sorted((ROOT / "steam_layout").rglob("*.py")), *sorted((ROOT / "tests").rglob("*.py"))]
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
        out = subprocess.run([sys.executable, "-m", "tools.audit_build", str(ROOT / "no-such-layout.json")],
                             capture_output=True, text=True, cwd=ROOT)
        self.assertEqual(out.returncode, 1)
        self.assertIn("Build audit [R150]: 4 audit(s) failed", out.stdout)

    def test_unchecked_lists_the_rules_nothing_fails_on(self):
        nothing, partly = rules.unchecked(self.rules)
        self.assertIn("R112", nothing)                 # "nothing depends on a chord hand-over" has no check
        self.assertIn("R137", partly)                  # two tests, on the fallback guard only; no temporary guard since 90.33
        self.assertNotIn("R108", nothing + partly)     # the Budget audit fails on it
        self.assertFalse(set(nothing) & set(partly))


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
                  *sorted((ROOT / "docs").glob("*.md")),
                  *sorted((ROOT / "skills").glob("*/SKILL.md")), *sorted((ROOT / "tools").glob("audit_*.py")),
                  *sorted((ROOT / "steam_layout").rglob("*.py")), *sorted((ROOT / "tests").rglob("*.py"))]
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
