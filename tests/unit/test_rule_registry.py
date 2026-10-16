"""The rule registry: the rule tables in resources/Layer Definition of Done.md (steam_layout/rules.py).

Fixture responsibility: unit. See docs/testing.md and tests/test-map.csv.
"""
from tests.support.fixtures.rule_registry import *

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


if __name__ == "__main__":
    unittest.main()
