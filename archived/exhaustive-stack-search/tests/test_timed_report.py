"""Reachability reports distinguish replayed timed facts from open alternatives."""
import json
import unittest

from steam_layout.model import Layout
from steam_layout.timed_model import TimedModel
from steam_layout.timed_report import format_timed_report, timed_layer_report
from test_audit_inheritance import EMPTY, act, add, build


LB = ("switch", "left_bumper")
RB = ("switch", "right_bumper")
A = ("switch", "button_a")


class MemoryStore:
    """Test store with independently replayable traces instead of fabricated states."""

    def __init__(self, model, traces, complete=False):
        self.model = model
        self.complete = complete
        self.identity = {"fixture": "timed-report"}
        self.traces = traces
        self.states = [self.replay(trace) for trace in traces]
        self.verified = []

    def replay(self, trace):
        states = self.model.start()
        for control in trace:
            states = {result for state in states for result in self.model.press(state, control)}
        if len(states) != 1:
            raise AssertionError("fixture trace should have exactly one result")
        return next(iter(states))

    def iter_states(self):
        return enumerate(self.states)

    def verify(self, state_id):
        self.verified.append(state_id)
        return self.replay(self.traces[state_id]) == self.states[state_id]


def sample_model():
    return TimedModel(Layout(build({
        "Base": {
            "switch": ("switches", {"left_bumper": act(add("X")),
                                     "right_bumper": act(add("Lower")),
                                     "button_a": act(add("Above"))}),
            "dpad": ("dpad", {"dpad_north": act("key_press W, , "),
                              "dpad_east": act("key_press D, , ")}),
            "left_trackpad": ("absolute_mouse", {"click": act(EMPTY)}),
        },
        "Lower": {"dpad": ("disabled", {})},
        "X": {"dpad": ("dpad", {"dpad_east": act(EMPTY)}),
              "switch": ("switches", {"button_a": {}}),
              "left_trackpad": ("disabled", {})},
        "Above": {"dpad": ("dpad", {"dpad_north": act("key_press S, , ")}),
                  "right_trackpad": ("absolute_mouse", {"click": act(EMPTY)})},
        "Unreachable": {},
    })))


def inherited(report, source, name):
    return next(row["values"] for row in report["inherited"]
                if row["source"] == source and row["input"] == name)


class TimedReportTests(unittest.TestCase):
    def report(self, model, store, title="X"):
        # Fixture states exercise projection logic, not a complete graph. The
        # graph closure verifier has integration coverage in search tests.
        return timed_layer_report(model, store, title, verify_witness=store.verify,
                                  verify_complete=lambda: {"verified": True, "fixture": True})

    def test_finds_layer_below_top_and_uses_only_its_lower_bindings(self):
        model = sample_model()
        store = MemoryStore(model, [(LB, A), (RB, LB, A)], complete=True)
        report = self.report(model, store)
        self.assertEqual({row["layer"] for row in report["below"]}, {"Base", "Lower"})
        self.assertEqual({row["layer"] for row in report["above"]}, {"Above"})
        values = inherited(report, "dpad", "dpad_north")
        self.assertEqual({(row["owner"], row["blocked_by"]) for row in values},
                         {("Base", None), (None, "Lower")})
        base = next(row for row in values if row["owner"] == "Base")
        self.assertEqual(base["activators"], act("key_press W, , "))
        self.assertIn("key_press W", base["summary"])
        self.assertTrue(all(row["status"] == "proven" for row in values))
        self.assertEqual(store.verified, [0, 1])
        self.assertEqual(report["search"]["verified_witnesses"], 2)
        self.assertTrue(report["complete_for_model"])
        self.assertTrue(report["search_complete"])
        self.assertEqual(report["counts"]["possible"], 0)
        self.assertGreater(report["counts"]["excluded"], 0)

    def test_incomplete_search_keeps_all_unseen_static_alternatives_open(self):
        model = sample_model()
        store = MemoryStore(model, [(LB, A)])
        report = self.report(model, store)
        below = {row["layer"]: row for row in report["below"]}
        self.assertEqual(below["Base"]["status"], "proven")
        self.assertEqual(below["Base"]["witness"], 0)
        self.assertEqual(below["Unreachable"]["status"], "possible")
        self.assertIsNone(below["Unreachable"]["witness"])
        values = inherited(report, "dpad", "dpad_north")
        self.assertEqual({(row["owner"], row["blocked_by"]) for row in values},
                         {("Base", None), (None, "Lower"), ("Above", None), (None, None)})
        self.assertTrue(all(row["status"] == "possible" for row in values if row["owner"] != "Base"))
        self.assertEqual(report["counts"]["excluded"], 0)
        self.assertFalse(report["complete_for_model"])
        self.assertFalse(report["search_complete"])

    def test_own_clear_or_disabled_source_is_skipped_but_empty_activators_inherit(self):
        model = sample_model()
        report = self.report(model, MemoryStore(model, [(LB, A)], complete=True))
        inputs = {(row["source"], row["input"]) for row in report["inherited"]}
        self.assertNotIn(("dpad", "dpad_east"), inputs)
        self.assertNotIn(("left_trackpad", "click"), inputs)
        self.assertIn(A, inputs)
        values = inherited(report, "switch", "button_a")
        self.assertEqual([(row["owner"], row["blocked_by"]) for row in values], [("Base", None)])

    def test_unbound_is_a_witnessed_value_when_only_upper_layer_defines_input(self):
        model = sample_model()
        report = self.report(model, MemoryStore(model, [(LB, A)], complete=True))
        values = inherited(report, "right_trackpad", "click")
        self.assertEqual(len(values), 1)
        self.assertEqual(values[0]["status"], "proven")
        self.assertIsNone(values[0]["owner"])
        self.assertIsNone(values[0]["blocked_by"])
        self.assertIsNone(values[0]["activators"])

    def test_unreached_target_excluded_only_when_frontier_is_complete(self):
        model = sample_model()
        for complete in (False, True):
            with self.subTest(complete=complete):
                store = MemoryStore(model, [()], complete=complete)
                report = self.report(model, store, "Unreachable")
                self.assertEqual(report["counts"]["proven"], 0)
                self.assertEqual(report["search"]["states_with_layer"], 0)
                self.assertEqual(store.verified, [])
                self.assertEqual(report["complete_for_model"], complete)
                if complete:
                    self.assertEqual(report["counts"]["possible"], 0)
                    self.assertTrue(all(not row["values"] for row in report["inherited"]))
                    self.assertEqual(set(report["excluded"]["below"]), set(model.spec.layer_names) - {"Unreachable"})
                else:
                    self.assertGreater(report["counts"]["possible"], 0)
                    self.assertEqual(report["counts"]["excluded"], 0)

    def test_complete_flag_cannot_be_inferred_from_empty_projection(self):
        model = TimedModel(Layout(build({"Base": {}})))
        report = self.report(model, MemoryStore(model, [()]), "Base")
        self.assertEqual(report["counts"], {"proven": 0, "possible": 0, "excluded": 0})
        self.assertFalse(report["complete_for_model"])

    def test_same_stack_reuses_first_witness_and_verifies_each_retained_id_once(self):
        model = sample_model()
        store = MemoryStore(model, [(LB,), (LB,), (LB, A), (LB, A)])
        report = self.report(model, store)
        self.assertEqual(store.verified, [0, 2])
        self.assertEqual(report["search"]["states_scanned"], 4)
        self.assertEqual(report["search"]["states_with_layer"], 4)
        self.assertEqual(report["search"]["distinct_stacks_with_layer"], 2)

    def test_failed_verifier_prevents_a_reachability_claim(self):
        model = sample_model()
        store = MemoryStore(model, [(LB,)])
        with self.assertRaisesRegex(ValueError, "replay failed for state 0"):
            timed_layer_report(model, store, "X", verify_witness=lambda state_id: False)
        with self.assertRaisesRegex(ValueError, "verifier is required"):
            timed_layer_report(model, store, "X", verify_witness=None)

    def test_complete_flag_alone_cannot_exclude_unobserved_facts(self):
        model = sample_model()
        store = MemoryStore(model, [(LB,)], complete=True)
        with self.assertRaisesRegex(ValueError, "independent closure verifier"):
            timed_layer_report(model, store, "X", verify_witness=store.verify)
        for certificate in (None, False, {}, {"verified": False}, {"verified": 1}):
            with self.subTest(certificate=certificate):
                with self.assertRaisesRegex(ValueError, "closure verification failed"):
                    timed_layer_report(model, store, "X", verify_witness=store.verify,
                                       verify_complete=lambda: certificate)
        self.assertEqual(store.verified, [])

    def test_complete_report_retains_certificate_and_incomplete_search_skips_verifier(self):
        model = sample_model()
        certificate = {"verified": True, "fixture": True, "states": 1}
        store = MemoryStore(model, [(LB,)], complete=True)
        report = timed_layer_report(model, store, "X", verify_witness=store.verify,
                                    verify_complete=lambda: certificate)
        self.assertEqual(report["closure_certificate"], certificate)
        store.complete = False

        def should_not_verify():
            self.fail("an incomplete search has no closure claim to verify")

        report = timed_layer_report(model, store, "X", verify_witness=store.verify,
                                    verify_complete=should_not_verify)
        self.assertIsNone(report["closure_certificate"])

    def test_rejects_different_model_instance_or_unknown_target(self):
        model = sample_model()
        store = MemoryStore(model, [(LB,)])
        with self.assertRaisesRegex(ValueError, "same TimedModel instance"):
            self.report(sample_model(), store)
        with self.assertRaisesRegex(ValueError, "Unknown layer"):
            self.report(model, store, "Wrong")

    def test_output_is_json_serializable_and_text_names_its_scope(self):
        model = sample_model()
        report = self.report(model, MemoryStore(model, [(LB, A)], complete=True))
        restored = json.loads(json.dumps(report))
        self.assertEqual(restored["model_family"], "TimedModel")
        text = format_timed_report(report)
        self.assertIn("Complete for model: true", text)
        self.assertIn("[proven] Above", text)
        self.assertIn("excluded by exhausted timed search", text)
        self.assertIn("raw bindings", text)
        self.assertIn("do not establish Steam hardware behavior", text)


if __name__ == "__main__":
    unittest.main()
