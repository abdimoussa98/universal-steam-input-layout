"""Trace parsing, branch preservation and the timed replay command."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from steam_layout.model import Layout
from steam_layout.timed_model import TimedModel
from steam_layout.timed_trace import parse_trace, replay
from test_audit_inheritance import act, add, build, remove


CONTROL = ["switch", "left_bumper"]


def delayed_layout():
    return build({"Base": {"switch": ("switches", {"left_bumper": {
        **act(add("Late"), delay_start="300"),
        "release": {"bindings": {"binding": remove("Late")}},
    }})}, "Late": {}})


class TraceParsingTests(unittest.TestCase):
    def test_valid_trace_normalizes_analog_values(self):
        trace = [{"press": CONTROL}, {"wait_ms": 0},
                 {"analog": {"control": ["left_trigger", "pull"], "value": 0.2}},
                 {"release": CONTROL}]
        result = parse_trace(trace)
        self.assertEqual(result[2]["analog"]["value"], "0.2")
        self.assertEqual(trace[2]["analog"]["value"], 0.2)

    def test_invalid_traces_report_the_step(self):
        for event in ({}, {"press": CONTROL, "wait_ms": 1}, {"tap": CONTROL},
                      {"press": "left_bumper"}, {"release": ["switch", ""]},
                      {"wait_ms": -1}, {"wait_ms": 1.5}, {"wait_ms": True},
                      {"analog": {"control": CONTROL}},
                      {"analog": {"control": CONTROL, "value": "NaN"}},
                      {"analog": {"control": CONTROL, "value": "inf"}},
                      {"analog": {"control": CONTROL, "value": True}},
                      {"analog": {"control": CONTROL, "value": "bad"}}):
            with self.subTest(event=event), self.assertRaisesRegex(ValueError, "trace step 2:"):
                parse_trace([{"wait_ms": 0}, event])
        with self.assertRaisesRegex(ValueError, "JSON list"):
            parse_trace({"press": CONTROL})


class ReplayTests(unittest.TestCase):
    def test_wait_observes_the_exact_delayed_add_deadline(self):
        data = delayed_layout()
        model = TimedModel(Layout(data))
        trace = [{"press": CONTROL}, {"wait_ms": 299}, {"wait_ms": 1}, {"release": CONTROL}]
        report = replay(model, trace, layout_data=data)
        self.assertEqual([[(state["now_ms"], state["stack"]) for state in row["states"]]
                          for row in report["steps"]],
                         [[(0, ["Base"])], [(299, ["Base"])],
                          [(300, ["Base", "Late"])], [(300, ["Base"])]])
        self.assertEqual(report["final_state_count"], 1)
        self.assertIn("not a reachability proof", report["scope"])

    def test_retains_branches_and_their_edges_in_stable_order(self):
        class BranchingModel:
            semantics = {"version": "test"}

            def start(self):
                return frozenset({0})

            def press(self, state, control):
                return frozenset({1, 2})

            def wait(self, state, ms):
                return frozenset({state + 2})

            def snapshot(self, state):
                return {"state": state}

        trace = [{"press": CONTROL}, {"wait_ms": 300}]
        report = replay(BranchingModel(), trace, layout_data={})
        self.assertEqual(report["steps"][0]["states"], [{"state": 1}, {"state": 2}])
        self.assertEqual(report["steps"][0]["transitions"], [{"from": 0, "to": 0},
                                                              {"from": 0, "to": 1}])
        self.assertEqual(report["steps"][1]["states"], [{"state": 3}, {"state": 4}])
        self.assertEqual(report["steps"][1]["transitions"], [{"from": 0, "to": 0},
                                                              {"from": 1, "to": 1}])
        self.assertEqual(report, replay(BranchingModel(), trace, layout_data={}))

    def test_identity_changes_with_layout_semantics_or_scenario(self):
        data = delayed_layout()
        model = TimedModel(Layout(data))
        original = replay(model, [], layout_data=data)
        different_option = replay(model, [], layout_data=data, options={"default_repeat_ms": 50})
        different_layout = replay(model, [], layout_data={**data, "metadata": "different"})
        model.semantics = {**model.semantics, "version": "different-contract"}
        different_semantics = replay(model, [], layout_data=data)
        self.assertEqual(original["model_family"], "TimedModel")
        self.assertNotEqual(original["model_sha256"], different_option["model_sha256"])
        self.assertNotEqual(original["model_sha256"], different_layout["model_sha256"])
        self.assertNotEqual(original["model_sha256"], different_semantics["model_sha256"])


class TraceCommandTests(unittest.TestCase):
    def run_command(self, trace, *arguments, layout=None):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            layout_path, trace_path = path / "layout.json", path / "trace.json"
            layout_path.write_text(json.dumps(delayed_layout() if layout is None else layout))
            trace_path.write_text(json.dumps(trace))
            return subprocess.run([sys.executable, "-m", "steam_layout.timed_trace",
                                   str(layout_path), str(trace_path), *arguments],
                                  capture_output=True, text=True)

    def test_cli_replays_a_delayed_add_without_optional_solver_dependencies(self):
        result = self.run_command([{"press": CONTROL}, {"wait_ms": 300}])
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report["scenario"], {"ignore_hold_bindings": False,
                                              "default_repeat_ms": None})
        self.assertEqual(report["steps"][-1]["state_count"], 1)
        self.assertEqual(report["steps"][-1]["states"][0]["stack"], ["Base", "Late"])
        self.assertEqual(len(report["model_sha256"]), 64)

    def test_cli_rejects_invalid_input_with_exit_two(self):
        result = self.run_command([{"wait_ms": True}])
        self.assertEqual(result.returncode, 2)
        self.assertIn("trace step 1", result.stderr)
        self.assertNotIn("Traceback", result.stderr)
        result = self.run_command([], "--default-repeat-ms", "0")
        self.assertEqual(result.returncode, 2)
        self.assertIn("must be positive", result.stderr)

    def test_missing_repeat_interval_needs_explicit_scenario_option(self):
        layout = build({"Base": {"switch": ("switches", {
            "left_bumper": act(add("Late"), hold_repeats="1")})}, "Late": {}})
        result = self.run_command([], layout=layout)
        self.assertEqual(result.returncode, 2)
        self.assertIn("default_repeat_ms", result.stderr)
        result = self.run_command([], "--default-repeat-ms", "50", layout=layout)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["scenario"]["default_repeat_ms"], 50)


if __name__ == "__main__":
    unittest.main()
