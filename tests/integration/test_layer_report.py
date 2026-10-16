"""The per-layer report: the three questions and the cleanup lists (plan step 6).

Plan: plans/2026-10-01-backward-chain-audit.md.

Fixture responsibility: integration. See docs/testing.md and tests/test-map.csv.
"""
from tests.support.fixtures.layer_report import *

class CliTests(unittest.TestCase):
    def run_cli(self, data, *args):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp, "layout.json")
            path.write_text(json.dumps(data))
            return subprocess.run([sys.executable, "-m", "tools.audit_layer", str(path), *args],
                                  capture_output=True, text=True, cwd=ROOT)

    def test_text_report_has_the_four_sections(self):
        out = self.run_cli(family(), "--layer", "P")
        self.assertEqual(out.returncode, 0, out.stderr)
        for expected in ("Layer: P", "Below", "Above", "  C", "Inherited inputs", "switch/button_k from Base",
                         "Exits", "present and removed: C", "removed, never present: Ghost"):
            self.assertIn(expected, out.stdout)

    def test_exits_with_the_same_removals_and_lists_are_shown_once(self):
        data = build({"Base": {"switch": (SW, {"button_a": press(add("P"))})},
                      "P": {"switch": (SW, {"button_x": press(remove("P"), hold_repeats=1),
                                            "button_y": press(remove("P"), hold_repeats=1)})}})
        out = self.run_cli(data, "--layer", "P")
        self.assertIn("2 recovery bindings removing: P", out.stdout)
        self.assertIn("on: switch/button_x, switch/button_y", out.stdout)

    def test_layer_references_are_shown_as_titles(self):
        # The working layouts store runtime IDs: a layer's position in the list, starting at 1.
        ids = {title: str(index + 1) for index, title in enumerate(("Base", "P", "C", "Ghost"))}
        numeric = json.loads(re.sub(r"\{\{Base::(\w+)\}\}", lambda m: ids[m.group(1)], json.dumps(family())))
        self.assertNotIn("{{", json.dumps(numeric))
        out = self.run_cli(numeric, "--layer", "C")
        self.assertIn("switch/button_b from P: add_layer C  [changes layers]", out.stdout)

    def test_json_report(self):
        out = self.run_cli(family(), "--layer", "C", "--json")
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertEqual(list(json.loads(out.stdout)["below"]["layers"]), ["Base", "P"])

    def test_a_layer_never_reached_is_reported_not_shown_as_empty(self):
        out = self.run_cli(family(), "--layer", "Ghost")
        self.assertEqual(out.returncode, 0)
        self.assertIn("not reached", out.stdout)
        self.assertNotIn("Below", out.stdout)

    def test_an_unknown_layer_exits_2(self):
        self.assertEqual(self.run_cli(family(), "--layer", "Nope").returncode, 2)


if __name__ == "__main__":
    unittest.main()
