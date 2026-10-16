"""The change report: what differs between two layouts, by layer and input (steam_layout/changes.py).

Fixture responsibility: integration. See docs/testing.md and tests/test-map.csv.
"""
from tests.support.fixtures.changes import *

class ScriptTests(unittest.TestCase):
    def run_script(self, *args):
        return subprocess.run([sys.executable, "-m", "tools.change_report", *args], capture_output=True, text=True,
                              cwd=ROOT)

    def test_two_files_and_out(self):
        after = base()
        group(after, "P")["inputs"]["button_a"]["activators"] = act(EMPTY)
        with tempfile.TemporaryDirectory() as tmp:
            a, b, out = Path(tmp, "a.json"), Path(tmp, "b.json"), Path(tmp, "out")
            a.write_text(json.dumps(base()))
            b.write_text(json.dumps(after))
            result = self.run_script(str(a), str(b), "--out", str(out))
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("== P", result.stdout)
            self.assertIn("== P", (out / "b-changes.txt").read_text())
            report = json.loads(self.run_script(str(a), str(b), "--json").stdout)
            self.assertEqual(list(report[0]["layers"]), ["P"])
            self.assertEqual(self.run_script(str(a), str(Path(tmp, "missing.json"))).returncode, 2)

    def test_the_working_layouts_against_their_newest_snapshot(self):
        result = self.run_script()
        self.assertEqual(result.returncode, 0, result.stderr)
        working = sum(len(controller.working()) for controller in controllers.with_layouts())
        self.assertEqual(working, 6)                                      # Ibex, Neptune and the Edge, two each
        self.assertEqual(result.stdout.count("Changes from "), working)  # one report per working layout


if __name__ == "__main__":
    unittest.main()
