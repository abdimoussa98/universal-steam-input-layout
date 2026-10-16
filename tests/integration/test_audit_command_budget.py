"""audit command budget

Fixture responsibility: integration. See docs/testing.md and tests/test-map.csv.
"""
from tests.support.fixtures.audit_command_budget import *

class CommandBudgetTests(unittest.TestCase):












    def test_cli_pass_fail_and_parse_error_exit_codes(self):
        root = Path(__file__).resolve().parents[2]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "layout.json"
            for content, expected in (
                (json.dumps(layout({"chord": [command()] * 3})), 0),
                (json.dumps(layout({"chord": [command()] * 4})), 1),
                (json.dumps(layout({"Long_Press": command()})), 1),
                ("not json", 2),
            ):
                path.write_text(content)
                result = subprocess.run([sys.executable, "-m", "tools.audit_command_budget", str(path), "--json"],
                                        capture_output=True, cwd=root)
                self.assertEqual(result.returncode, expected)
                if expected != 2:
                    self.assertEqual(len(json.loads(result.stdout)), 1)

    def test_cli_prints_the_rule_id_next_to_each_finding(self):
        root = Path(__file__).resolve().parents[2]
        over = layout({"chord": [command()] * 4, "Long_Press": command()})
        inverted = layout({"Full_Press": command("controller_action remove_layer 9 0 0, , ")})
        inverted["controller_mappings"]["group"][0].update(mode="dpad", settings={"edge_binding_invert": "1"})
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "layout.json"
            for data, expected in ((over, ("over the entry budget [R109]", "banned Long_Press [R108]")),
                                   (inverted, ("inverted D-pad edge [R111]",))):
                path.write_text(json.dumps(data))
                out = subprocess.run([sys.executable, "-m", "tools.audit_command_budget", str(path)],
                                     capture_output=True, text=True, cwd=root).stdout
                for text in expected:
                    self.assertIn(text, out)


if __name__ == "__main__":
    unittest.main()
