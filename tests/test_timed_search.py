"""Exact finite-state reductions and exhaustive timed transition coverage."""
from dataclasses import replace
from decimal import Decimal
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from steam_layout.model import Layout
from steam_layout.timed_model import TimedModel
from steam_layout.timed_report import timed_layer_report
from steam_layout.timed_search import TimedQuotient, WitnessVerifier, compact_trace, run_search, verify_closure
from steam_layout.timed_store import TimedStore, encode_state
from test_audit_inheritance import EMPTY, act, add, build, remove


LB = ("switch", "left_bumper")
RB = ("switch", "right_bumper")
EDGE = ("left_trigger", "edge")


def entry(binding, **settings):
    return {"bindings": {"binding": binding}, "settings": settings}


def switches(inputs):
    return {"switch": ("switches", inputs)}


class TimedQuotientTests(unittest.TestCase):
    def quotient(self, layers, shifts=None):
        return TimedQuotient(TimedModel(Layout(build(layers, modeshift=shifts))))

    def one(self, values):
        values = frozenset(values)
        self.assertEqual(len(values), 1)
        return next(iter(values))

    def perform(self, quotient, state, event):
        return self.one(quotient.step(state, event))

    def layers(self, quotient, state):
        return quotient.model.names_of(state.stack)

    def test_two_deadlines_allow_a_physical_event_between_press_and_expiry(self):
        quotient = self.quotient({"Base": switches({"left_bumper": {"Full_Press": [
            entry(add("Early"), delay_start="2"), entry(add("Late"), delay_start="3")
        ]}, "right_bumper": act(add("Marker"))}), "Early": {}, "Late": {}, "Marker": {}})
        state = self.perform(quotient, self.one(quotient.initial()), {"press": list(LB)})
        state = self.perform(quotient, state, {"wait_ms": 1})
        self.assertEqual(sorted(a.deadline_ms for a in state.activations), [1, 2])
        successors = list(quotient.successors(state))
        markers = [following for following, event in successors if event == {"press": list(RB)}]
        state = self.one(markers)
        self.assertEqual(self.layers(quotient, state), ("Base", "Marker"))
        state = self.perform(quotient, state, {"wait_ms": 1})
        self.assertEqual(self.layers(quotient, state), ("Base", "Marker", "Early"))
        state = self.perform(quotient, state, {"wait_ms": 1})
        self.assertEqual(self.layers(quotient, state), ("Base", "Marker", "Early", "Late"))
        self.assertEqual(state.now_ms, 0)

    def test_one_tick_keeps_all_orders_of_simultaneous_deadlines(self):
        quotient = self.quotient({"Base": switches({"left_bumper": {"Full_Press": [
            entry(add("A"), delay_start="2"), entry(add("B"), delay_start="2")
        ]}}), "A": {}, "B": {}})
        state = self.perform(quotient, self.one(quotient.initial()), {"press": list(LB)})
        state = self.perform(quotient, state, {"wait_ms": 1})
        following = {next_state for next_state, event in quotient.successors(state)
                     if event == {"wait_ms": 1}}
        self.assertEqual({self.layers(quotient, next_state) for next_state in following},
                         {("Base", "A", "B"), ("Base", "B", "A")})

    def test_repeating_clock_closes_a_finite_cycle(self):
        quotient = self.quotient({"Base": switches({"left_bumper": {
            **act(add("A"), hold_repeats="1", repeat_rate="2"),
            "release": entry(remove("A"))
        }}), "A": {}})
        initial = self.one(quotient.initial())
        pressed = self.perform(quotient, initial, {"press": list(LB)})
        self.assertEqual(self.perform(quotient, pressed, {"wait_ms": 2000}), pressed)
        discovered, frontier = {initial}, [initial]
        while frontier:
            for state, _ in quotient.successors(frontier.pop()):
                self.assertEqual(state.now_ms, 0)
                if state not in discovered:
                    discovered.add(state)
                    frontier.append(state)
            self.assertLess(len(discovered), 10, "absolute time must not make repeat states infinite")
        self.assertEqual(len(discovered), 3)

    def test_without_pending_timers_successors_do_not_include_wait(self):
        quotient = self.quotient({"Base": switches({"left_bumper": act(add("A"))}), "A": {}})
        initial = self.one(quotient.initial())
        pressed = self.perform(quotient, initial, {"press": list(LB)})
        for state in (initial, pressed):
            self.assertFalse(any("wait_ms" in event for _, event in quotient.successors(state)))
            self.assertEqual(self.perform(quotient, state, {"wait_ms": 10**9}), state)

    def test_regions_include_thresholds_in_hidden_layers_and_mode_shifts(self):
        quotient = self.quotient({
            "Base": switches({"left_bumper": act(add("Upper")),
                              "right_bumper": act("mode_shift left_trigger 90, , ")}),
            "Upper": {"left_trigger": ("trigger", {"edge": {"Soft_Press": [
                entry(add("A"), activation_threshold="10.5"),
                entry(add("Never"), activation_threshold="40000")
            ]}})}, "A": {}, "B": {}, "Never": {}
        }, shifts={"90": ("left_trigger", "trigger", {"edge": {
            "Soft_Press": entry(add("B"), activation_threshold="20.25")
        }})})
        self.assertEqual(quotient.analog_regions[EDGE],
                         tuple(map(Decimal, ("0", "10.5", "20.25", "32767"))))
        initial = self.one(quotient.initial())
        samples = [event["analog"]["value"] for _, event in quotient.successors(initial)
                   if "analog" in event and event["analog"]["control"] == list(EDGE)]
        self.assertEqual(set(map(Decimal, samples)), set(quotient.analog_regions[EDGE]))

    def test_upper_boundary_representatives_preserve_strict_decimal_thresholds(self):
        quotient = self.quotient({"Base": {"left_trigger": ("trigger", {"edge": {
            "Soft_Press": entry(add("Outside"), activation_threshold="10.5")
        }})}, "Outside": {}})
        initial = self.one(quotient.model.start())
        for raw, representative, outside in (("0", "0", False), ("0.001", "10.5", False),
                                             ("10.4999", "10.5", False), ("10.5", "10.5", False),
                                             ("10.5001", "32767", True), ("32767", "32767", True)):
            with self.subTest(raw=raw):
                state = self.one(quotient.model.analog(initial, EDGE, raw))
                normalized = quotient.normalize(state)
                self.assertEqual(dict(normalized.analog_values)[EDGE], Decimal(representative))
                self.assertEqual("Outside" in self.layers(quotient, normalized), outside)
                self.assertEqual(quotient.normalize(normalized), normalized)

    def test_missing_sample_and_zero_are_distinct_for_inverted_numeric_threshold(self):
        quotient = self.quotient({"Base": {"left_trigger": ("trigger", {"edge": {
            "Soft_Press": entry(add("Inside"), activation_threshold="10.5", edge_binding_invert="1")
        }})}, "Inside": {}})
        initial = self.one(quotient.initial())
        zero = self.perform(quotient, initial, {"analog": {"control": list(EDGE), "value": "0"}})
        self.assertNotIn(EDGE, dict(initial.analog_values))
        self.assertEqual(dict(zero.analog_values)[EDGE], Decimal(0))
        self.assertFalse(initial.held)
        self.assertFalse(zero.held)
        self.assertEqual(self.layers(quotient, initial), ("Base",))
        self.assertEqual(self.layers(quotient, zero), ("Base", "Inside"))

    def test_nonsoft_analog_samples_reduce_to_digital_state(self):
        quotient = self.quotient({"Base": switches({"left_bumper": act(add("A"))}), "A": {}})
        initial = self.one(quotient.initial())
        sampled = self.one(quotient.model.analog(initial, LB, "123.456"))
        pressed = self.perform(quotient, initial, {"press": list(LB)})
        self.assertEqual(quotient.normalize(sampled), pressed)
        self.assertFalse(pressed.analog_values)
        self.assertNotIn(LB, quotient.analog_regions)
        self.assertFalse(any("analog" in event for _, event in quotient.successors(initial)))

    def test_normalization_commutes_with_time_translation_and_following_events(self):
        quotient = self.quotient({"Base": {
            **switches({"left_bumper": act(add("Later"), delay_start="5")}),
            "left_trigger": ("trigger", {"edge": {
                "Soft_Press": entry(add("Outside"), activation_threshold="10.5")
            }})}, "Later": {}, "Outside": {}})
        model = quotient.model
        raw = self.one(model.analog(self.one(model.start()), EDGE, "4.123"))
        raw = self.one(model.press(raw, LB))
        raw = self.one(model.wait(raw, 2))
        moved = replace(raw, now_ms=raw.now_ms + 10**9, activations=tuple(
            replace(a, deadline_ms=None if a.deadline_ms is None else a.deadline_ms + 10**9)
            for a in raw.activations))
        self.assertEqual(quotient.normalize(raw), quotient.normalize(moved))
        normalized = quotient.normalize(raw)
        self.assertEqual([a.deadline_ms for a in normalized.activations], [3])
        operations = [({"wait_ms": 3}, lambda state: model.wait(state, 3)),
                      ({"release": list(LB)}, lambda state: model.release(state, LB)),
                      ({"analog": {"control": list(EDGE), "value": "10.50001"}},
                       lambda state: model.analog(state, EDGE, "10.50001")),
                      ({"analog": {"control": list(EDGE), "value": "0"}},
                       lambda state: model.analog(state, EDGE, "0"))]
        for event, operation in operations:
            with self.subTest(event=event):
                expected = frozenset(quotient.normalize(state) for state in operation(raw))
                self.assertEqual(quotient.step(normalized, event), expected)
                self.assertEqual(frozenset(quotient.normalize(state) for state in operation(moved)), expected)

    def test_invalid_physical_inputs_are_excluded_without_hiding_runtime_errors(self):
        touch, click = ("left_trackpad", "touch"), ("left_trackpad", "click")
        quotient = self.quotient({"Base": {"left_trackpad": ("dpad", {
            "touch": act(EMPTY), "click": act(add("A"))
        })}, "A": {}})
        initial = self.one(quotient.initial())
        events = [event for _, event in quotient.successors(initial)]
        self.assertIn({"press": list(touch)}, events)
        self.assertNotIn({"press": list(click)}, events)
        state = self.perform(quotient, initial, {"press": list(touch)})
        state = self.perform(quotient, state, {"press": list(click)})
        events = [event for _, event in quotient.successors(state)]
        self.assertIn({"release": list(click)}, events)
        self.assertNotIn({"release": list(touch)}, events)

    def test_zero_time_cycle_in_a_successor_is_an_error_not_a_pruned_edge(self):
        quotient = self.quotient({"Base": switches({"left_bumper": act(add("A"))}),
                                  "A": switches({"always_on_action": act(add("B"))}),
                                  "B": switches({"always_on_action": act(remove("B"))})})
        initial = self.one(quotient.initial())
        with self.assertRaisesRegex(ValueError, "zero-time"):
            list(quotient.successors(initial))

    def test_identity_is_stable_and_changes_with_runtime_scenario(self):
        data = build({"Base": switches({"left_bumper": act(add("A"), hold_repeats="1")}), "A": {}})
        first = TimedQuotient(TimedModel(Layout(data), default_repeat_ms=2))
        same = TimedQuotient(TimedModel(Layout(data), default_repeat_ms=2))
        different = TimedQuotient(TimedModel(Layout(data), default_repeat_ms=3))
        self.assertEqual(first.identity, same.identity)
        self.assertNotEqual(first.identity, different.identity)
        json.dumps(first.identity, allow_nan=False)


class TimedSearchTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)

    def fixture(self):
        data = build({"Base": switches({"left_bumper": {
            **act(add("A"), hold_repeats="1", repeat_rate="2"),
            "release": entry(remove("A"))
        }}), "A": {}})
        return data, TimedQuotient(TimedModel(Layout(data)))

    def store(self, name, quotient, resume=False):
        return TimedStore(self.root / name, quotient.model, quotient.identity, resume=resume)

    def test_budget_stop_and_resume_match_an_uninterrupted_closed_search(self):
        _, quotient = self.fixture()
        with self.store("resumed.sqlite", quotient) as store:
            stopped = run_search(quotient, store, max_states=1)
            self.assertFalse(stopped["complete"])
            self.assertEqual(stopped["stopped"], "max_states")
            self.assertEqual((store.count, store.expanded_count), (1, 0))
            with self.assertRaisesRegex(ValueError, "open frontier"):
                verify_closure(quotient, store)
        with self.store("resumed.sqlite", quotient, resume=True) as store:
            completed = run_search(quotient, store)
            self.assertTrue(completed["complete"])
            self.assertEqual((completed["states"], completed["expanded"], completed["frontier"]), (3, 3, 0))
            resumed_states = {encode_state(state) for _, state in store.iter_states()}
            self.assertTrue(verify_closure(quotient, store)["verified"])
        with self.store("uninterrupted.sqlite", quotient) as store:
            run_search(quotient, store)
            self.assertEqual({encode_state(state) for _, state in store.iter_states()}, resumed_states)

    def test_every_retained_witness_replays_to_its_recorded_state(self):
        _, quotient = self.fixture()
        with self.store("witness.sqlite", quotient) as store:
            run_search(quotient, store)
            verifier = WitnessVerifier(quotient, store)
            for sid, state in store.iter_states():
                self.assertTrue(verifier(sid))
                current = quotient.model.start()
                for event in compact_trace(store.trace(sid)):
                    operation, value = next(iter(event.items()))
                    current = frozenset(following for previous in current
                                        for following in (quotient.model.wait(previous, value)
                                            if operation == "wait_ms" else
                                            getattr(quotient.model, operation)(previous, tuple(value))))
                self.assertIn(state, {quotient.normalize(candidate) for candidate in current})

    def test_complete_flags_cannot_replace_an_independent_closure_check(self):
        _, quotient = self.fixture()
        with self.store("missing-edge.sqlite", quotient) as store:
            initial = next(iter(quotient.initial()))
            sid = store.seed([initial])[0]
            store.commit_expansion(sid, [])
            self.assertTrue(store.complete)
            with self.assertRaisesRegex(ValueError, "not closed"):
                verify_closure(quotient, store)

    def test_unreachable_stored_state_fails_witness_verification(self):
        _, quotient = self.fixture()
        with self.store("bad-witness.sqlite", quotient) as store:
            initial = next(iter(quotient.initial()))
            sid = store.seed([initial])[0]
            forged = replace(initial, stack=(0, 1))
            fake_id, _ = store.add(forged, parent=sid, event={"press": list(LB)})
            with self.assertRaisesRegex(ValueError, "witness fails"):
                WitnessVerifier(quotient, store)(fake_id)

    def test_closure_checks_that_every_initial_branch_is_present(self):
        data = build({"Base": switches({"always_on_action": {"Full_Press": [
            entry(add("A")), entry(add("B"))
        ]}}), "A": {}, "B": {}})
        quotient = TimedQuotient(TimedModel(Layout(data)))
        self.assertEqual(len(quotient.initial()), 2)
        with self.store("missing-root.sqlite", quotient) as store:
            sid = store.seed([next(iter(quotient.initial()))])[0]
            store.commit_expansion(sid, [])
            with self.assertRaisesRegex(ValueError, "missing an initial state"):
                verify_closure(quotient, store)

    def test_runtime_error_keeps_the_failing_state_on_the_frontier(self):
        data = build({"Base": switches({"left_bumper": act(add("A"))}),
                      "A": switches({"always_on_action": act(add("B"))}),
                      "B": switches({"always_on_action": act(remove("B"))})})
        quotient = TimedQuotient(TimedModel(Layout(data)))
        with self.store("cycle.sqlite", quotient) as store:
            with self.assertRaisesRegex(ValueError, "zero-time"):
                run_search(quotient, store)
            self.assertFalse(store.complete)
            self.assertEqual((store.count, store.expanded_count), (1, 0))
            self.assertIsNotNone(store.pending())

    def test_identity_mismatch_rejects_resuming_a_different_scenario(self):
        _, quotient = self.fixture()
        with self.store("identity.sqlite", quotient) as store:
            run_search(quotient, store, max_states=1)
        data = build({"Base": switches({"left_bumper": act(add("A"), delay_start="3")}), "A": {}})
        changed = TimedQuotient(TimedModel(Layout(data)))
        with self.assertRaisesRegex(ValueError, "identity mismatch"):
            self.store("identity.sqlite", changed, resume=True)

    def test_compacting_waits_keeps_events_and_does_not_modify_the_input(self):
        events = [{"press": list(LB)}, {"wait_ms": 1}, {"wait_ms": 1},
                  {"release": list(LB)}, {"wait_ms": 2}, {"wait_ms": 3}]
        before = json.loads(json.dumps(events))
        self.assertEqual(compact_trace(events), [{"press": list(LB)}, {"wait_ms": 2},
                                                 {"release": list(LB)}, {"wait_ms": 5}])
        self.assertEqual(events, before)

    def test_partial_report_never_excludes_and_complete_report_verifies_closure(self):
        _, quotient = self.fixture()
        with self.store("report.sqlite", quotient) as store:
            run_search(quotient, store, max_states=1)
            partial = timed_layer_report(quotient.model, store, "A",
                                         verify_witness=WitnessVerifier(quotient, store))
            self.assertFalse(partial["complete_for_model"])
            self.assertEqual(partial["counts"]["excluded"], 0)
            self.assertGreater(partial["counts"]["possible"], 0)
            run_search(quotient, store)
            with self.assertRaisesRegex(ValueError, "independent closure verifier"):
                timed_layer_report(quotient.model, store, "A",
                                   verify_witness=WitnessVerifier(quotient, store))
            complete = timed_layer_report(quotient.model, store, "A",
                                          verify_witness=WitnessVerifier(quotient, store),
                                          verify_complete=lambda: verify_closure(quotient, store))
            self.assertTrue(complete["complete_for_model"])
            self.assertTrue(complete["closure_certificate"]["verified"])
            self.assertEqual(complete["counts"]["possible"], 0)
            self.assertGreater(complete["counts"]["proven"], 0)
            self.assertGreater(complete["counts"]["excluded"], 0)

    def test_cli_runs_resumes_and_checks_a_complete_timed_graph(self):
        data, _ = self.fixture()
        layout = self.root / "layout.json"
        layout.write_text(json.dumps(data), encoding="utf-8")
        database = self.root / "cli.sqlite"

        def command(operation, *arguments):
            return subprocess.run([sys.executable, "-m", "steam_layout.timed_search", operation,
                                   str(layout), str(database), *arguments],
                                  cwd=Path(__file__).resolve().parents[1], capture_output=True, text=True)

        partial = command("run", "--max-states", "1")
        self.assertEqual(partial.returncode, 0, partial.stderr)
        self.assertFalse(json.loads(partial.stdout)["complete"])
        partial_report = command("show", "A", "--json")
        self.assertEqual(partial_report.returncode, 0, partial_report.stderr)
        self.assertEqual(json.loads(partial_report.stdout)["counts"]["excluded"], 0)
        rejected = command("check")
        self.assertEqual(rejected.returncode, 2)
        self.assertIn("open frontier", rejected.stderr)
        resumed = command("run", "--resume")
        self.assertEqual(resumed.returncode, 0, resumed.stderr)
        self.assertTrue(json.loads(resumed.stdout)["complete"])
        checked = command("check")
        self.assertEqual(checked.returncode, 0, checked.stderr)
        self.assertTrue(json.loads(checked.stdout)["verified"])
        complete_report = command("show", "A", "--json")
        self.assertEqual(complete_report.returncode, 0, complete_report.stderr)
        self.assertTrue(json.loads(complete_report.stdout)["closure_certificate"]["verified"])
        witness = command("witness", "2")
        self.assertEqual(witness.returncode, 0, witness.stderr)
        witness_report = json.loads(witness.stdout)
        self.assertTrue(witness_report["verified"])
        self.assertEqual(witness_report["events"], [{"press": list(LB)}])


if __name__ == "__main__":
    unittest.main()
