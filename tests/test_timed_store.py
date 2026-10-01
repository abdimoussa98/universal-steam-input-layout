"""Durable frontier, budget boundaries and replayable timed search witnesses."""
from dataclasses import replace
from decimal import Decimal, localcontext
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest

from steam_layout.model import Layout
from steam_layout.timed_model import Activation, Shift, TimedModel, TimedState
from steam_layout.timed_store import TimedStore, decode_state, encode_state
from test_audit_inheritance import act, add, build


LB = ("switch", "left_bumper")
RB = ("switch", "right_bumper")


class TimedStateCodecTests(unittest.TestCase):
    def test_round_trip_every_state_component(self):
        state = TimedState(
            now_ms=7, stack=(0, 3, 1), held=frozenset({LB, RB}),
            analog_values=((LB, Decimal("123.12345678901234567890123456789012345")),),
            activations=(Activation("entry1", 10, "start"),
                         Activation("entry2", 17, "repeat", True),
                         Activation("entry3", None, "done", True)),
            shifts=(Shift(LB, "joystick", "90", "entry4"),))
        with localcontext() as context:
            context.prec = 3
            restored = decode_state(encode_state(state))
        self.assertEqual(restored, state)
        self.assertIsInstance(restored.analog_values[0][1], Decimal)

    def test_equal_decimal_values_have_identical_keys(self):
        for values in (("0", "-0.00", "0E+2"), ("100", "1E+2", "100.00"),
                       ("0.01", "0.010000")):
            encoded = {encode_state(TimedState(analog_values=((LB, Decimal(v)),))) for v in values}
            self.assertEqual(len(encoded), 1)

    def test_held_order_is_canonical_but_stack_and_shift_order_are_preserved(self):
        first = TimedState(stack=(0, 1, 2), held=frozenset((LB, RB)))
        second = replace(first, held=frozenset((RB, LB)))
        self.assertEqual(encode_state(first), encode_state(second))
        self.assertNotEqual(encode_state(first), encode_state(replace(first, stack=(0, 2, 1))))
        shifts = (Shift(LB, "joystick", "90", "e1"), Shift(RB, "joystick", "91", "e2"))
        self.assertNotEqual(encode_state(replace(first, shifts=shifts)),
                            encode_state(replace(first, shifts=shifts[::-1])))

    def test_reject_malformed_records(self):
        payload = json.loads(encode_state(TimedState()))
        malformed = [dict(payload, now_ms=True), dict(payload, stack=[1]),
                     dict(payload, stack=[0, 0]), dict(payload, held=[list(LB), list(LB)]),
                     dict(payload, held=["switch"]), dict(payload, extra=True),
                     dict(payload, analog_values=[[list(LB), "NaN"]]),
                     dict(payload, analog_values=[[list(LB), "32768"]]),
                     dict(payload, analog_values=[[list(LB), 10]]),
                     dict(payload, activations=[{"entry_id": "e", "deadline_ms": -1,
                                                "stage": "start", "fired": False}]),
                     dict(payload, activations=[{"entry_id": "e", "deadline_ms": None,
                                                "stage": "missing", "fired": False}])]
        for record in malformed:
            with self.subTest(record=record), self.assertRaises(ValueError):
                decode_state(record)


class TimedStoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.database = Path(self.temp.name) / "states.sqlite"
        self.model = TimedModel(Layout(build({
            "Base": {"switch": ("switches", {
                "left_bumper": act(add("A"), delay_start="2")})}, "A": {}})))
        self.identity = {"layout_sha256": "fixture-layout", "runtime": self.model.semantics,
                         "options": {"tick_ms": 1, "controls": [list(LB)]}}

    def store(self, resume=False, identity=None):
        store = TimedStore(self.database, self.model,
                           self.identity if identity is None else identity, resume=resume)
        self.addCleanup(store.close)
        return store

    def test_empty_is_incomplete_until_initial_states_are_seeded(self):
        store = self.store()
        self.assertFalse(store.seeded)
        self.assertFalse(store.complete)
        self.assertIsNone(store.pending())
        self.assertEqual((store.count, store.expanded_count), (0, 0))
        store.mark_seeded()
        self.assertTrue(store.seeded)
        self.assertTrue(store.complete)

    def test_seeding_and_deduplication_keep_first_witness(self):
        store = self.store()
        root = TimedState()
        root_id, = store.seed([root])
        self.assertEqual(store.add(root), (root_id, False))
        self.assertFalse(store.complete)
        next_state = replace(root, held=frozenset({LB}))
        event = {"press": list(LB)}
        state_id, created = store.add(next_state, root_id, event)
        self.assertTrue(created)
        self.assertEqual(store.add(next_state, root_id, {"other_event": True}), (state_id, False))
        self.assertEqual(store.trace(state_id), [event])
        self.assertEqual(list(store.iter_states()), [(root_id, root), (state_id, next_state)])

    def test_root_seeding_deduplicates_and_commits_initialization_together(self):
        store = self.store()
        roots = [TimedState(), TimedState(stack=(0, 1)), TimedState()]
        ids = store.seed(roots)
        self.assertEqual(ids[0], ids[2])
        self.assertEqual(store.count, 2)
        self.assertTrue(store.seeded)
        with self.assertRaisesRegex(ValueError, "already been seeded"):
            store.seed([])

    def test_failed_seed_generator_leaves_initialization_unfinished(self):
        store = self.store()

        def broken():
            yield TimedState()
            raise RuntimeError("interrupted initial states")

        with self.assertRaisesRegex(RuntimeError, "interrupted"):
            store.seed(broken())
        self.assertFalse(store.seeded)
        self.assertEqual(store.count, 0)
        self.assertFalse(store.complete)

    def test_expansion_budget_counts_distinct_new_states_and_is_atomic(self):
        store = self.store()
        root = TimedState()
        root_id, = store.seed([root])
        first = replace(root, held=frozenset({LB}))
        second = replace(root, held=frozenset({RB}))
        successors = [(first, {"press": list(LB)}), (second, {"press": list(RB)}),
                      (first, {"duplicate": True}), (root, {"self_loop": True})]
        self.assertFalse(store.commit_expansion(root_id, successors, max_states=2))
        self.assertEqual((store.count, store.expanded_count), (1, 0))
        self.assertEqual(store.pending(), (root_id, root))
        self.assertTrue(store.commit_expansion(root_id, successors, max_states=3))
        self.assertEqual((store.count, store.expanded_count), (3, 1))
        first_id, pending = store.pending()
        self.assertEqual(pending, first)
        self.assertEqual(store.trace(first_id), [{"press": list(LB)}])
        self.assertTrue(store.commit_expansion(first_id, [], max_states=3))
        second_id, pending = store.pending()
        self.assertEqual(pending, second)
        self.assertTrue(store.commit_expansion(second_id, [(root, {"cycle": True})], max_states=3))
        self.assertEqual(store.expanded_count, 3)
        self.assertTrue(store.complete)

    def test_sql_failure_rolls_back_all_successors_and_parent_expansion(self):
        store = self.store()
        root_id, = store.seed([TimedState()])
        # Simulate a failure after the first successor has been inserted.
        store._connection.execute("""CREATE TRIGGER fail_second_insert BEFORE INSERT ON states
            WHEN (SELECT COUNT(*) FROM states) >= 2
            BEGIN SELECT RAISE(ABORT, 'simulated disk failure'); END""")
        successors = [(TimedState(stack=(0, 1)), {"first": True}),
                      (TimedState(stack=(0, 2)), {"second": True})]
        with self.assertRaisesRegex(sqlite3.IntegrityError, "simulated disk failure"):
            store.commit_expansion(root_id, successors)
        self.assertEqual((store.count, store.expanded_count), (1, 0))
        self.assertEqual(store.pending()[0], root_id)

    def test_transactional_counters_follow_changes_and_rollbacks(self):
        store = self.store()
        root_id, = store.seed([TimedState()])
        store.commit_expansion(root_id, [(TimedState(stack=(0, 1)), {"next": True})])
        child_id, _ = store.pending()
        store.commit_expansion(child_id, [])
        # Retrying an already committed expansion changes no counters.
        store.commit_expansion(child_id, [])
        self.assertEqual((store.count, store.expanded_count), (2, 2))
        with self.assertRaisesRegex(RuntimeError, "rollback"):
            with store._transaction():
                store._connection.execute("DELETE FROM states WHERE id = ?", (child_id,))
                self.assertEqual((store.count, store.expanded_count), (1, 1))
                raise RuntimeError("rollback")
        self.assertEqual((store.count, store.expanded_count), (2, 2))
        store._connection.execute("UPDATE states SET expanded = 0 WHERE id = ?", (child_id,))
        self.assertEqual((store.count, store.expanded_count), (2, 1))
        store._connection.execute("DELETE FROM states WHERE id = ?", (child_id,))
        self.assertEqual((store.count, store.expanded_count), (1, 1))
        store.close()
        self.assertEqual(self.store(resume=True).count, 1)

    def test_resume_validates_persisted_counts(self):
        store = self.store()
        store.seed([TimedState()])
        store._connection.execute("UPDATE metadata SET value = '999' WHERE key = 'count'")
        store.close()
        with self.assertRaisesRegex(ValueError, "counts do not match"):
            self.store(resume=True)

    def test_budget_stop_can_resume_and_finish_without_losing_successors(self):
        store = self.store()
        root_id, = store.seed([TimedState()])
        successors = [(TimedState(stack=(0, 1)), {"first": True}),
                      (TimedState(stack=(0, 2)), {"second": True})]
        self.assertFalse(store.commit_expansion(root_id, successors, max_states=2))
        store.close()
        resumed = self.store(resume=True)
        self.assertEqual(resumed.pending()[0], root_id)
        self.assertFalse(resumed.complete)
        self.assertTrue(resumed.commit_expansion(root_id, successors, max_states=3))
        while resumed.pending() is not None:
            self.assertTrue(resumed.commit_expansion(resumed.pending()[0], []))
        resumed.close()
        complete = self.store(resume=True)
        self.assertTrue(complete.complete)
        self.assertEqual((complete.count, complete.expanded_count), (3, 3))

    def test_new_store_never_overwrites_existing_database(self):
        store = self.store()
        store.seed([TimedState()])
        store.close()
        original = self.database.read_bytes()
        with self.assertRaisesRegex(ValueError, "already exists"):
            self.store()
        self.assertEqual(self.database.read_bytes(), original)
        self.assertEqual(self.store(resume=True).count, 1)

    def test_new_store_accepts_empty_file_but_resume_never_creates_one(self):
        with self.assertRaisesRegex(ValueError, "does not exist"):
            self.store(resume=True)
        self.assertFalse(self.database.exists())
        self.database.touch()
        with self.assertRaisesRegex(ValueError, "empty"):
            self.store(resume=True)
        self.assertEqual(self.store().count, 0)

    def test_resume_requires_exact_identity_but_ignores_dictionary_order(self):
        store = self.store()
        store.close()
        reordered = dict(reversed(list(self.identity.items())))
        self.store(resume=True, identity=reordered).close()
        for change in ({"layout_sha256": "changed"}, {"runtime": {"version": "changed"}},
                       {"options": {"tick_ms": 2, "controls": [list(LB)]}}):
            with self.subTest(change=change), self.assertRaisesRegex(ValueError, "identity mismatch"):
                self.store(resume=True, identity={**self.identity, **change})

    def test_resume_rejects_unrelated_database_and_wrong_format(self):
        with sqlite3.connect(self.database) as connection:
            connection.execute("CREATE TABLE unrelated (value TEXT)")
        with self.assertRaisesRegex(ValueError, "not a timed search"):
            self.store(resume=True)
        self.database.unlink()
        store = self.store()
        store._connection.execute("UPDATE metadata SET value = '999' WHERE key = 'format'")
        store.close()
        with self.assertRaisesRegex(ValueError, "incompatible"):
            self.store(resume=True)

    def test_witness_path_replays_actual_runtime_states_after_resume(self):
        store = self.store()
        root, = self.model.start()
        root_id, = store.seed([root])
        pressed, = self.model.press(root, LB)
        store.commit_expansion(root_id, [(pressed, {"press": list(LB)})])
        pressed_id, = [state_id for state_id, state in store.iter_states() if state == pressed]
        waited, = self.model.wait(pressed, 2)
        store.commit_expansion(pressed_id, [(waited, {"wait": 2})])
        waited_id, = [state_id for state_id, state in store.iter_states() if state == waited]
        store.close()
        resumed = self.store(resume=True)
        path = resumed.path(waited_id)
        self.assertEqual(path, [(root_id, root, None), (pressed_id, pressed, {"press": list(LB)}),
                                (waited_id, waited, {"wait": 2})])
        actual = {root}
        for event in resumed.trace(waited_id):
            if "press" in event:
                actual = {result for state in actual for result in self.model.press(state, event["press"])}
            else:
                actual = {result for state in actual for result in self.model.wait(state, event["wait"])}
        self.assertEqual(actual, {resumed.get(waited_id)})
        self.assertEqual(resumed.trace(root_id), [])

    def test_invalid_parent_or_event_never_inserts_a_state(self):
        store = self.store()
        root_id, = store.seed([TimedState()])
        next_state = TimedState(stack=(0, 1))
        for parent, event, exception in ((None, {}, ValueError), (root_id, None, ValueError),
                                         (999, {}, KeyError), (root_id, [], ValueError),
                                         (root_id, {"bad": float("nan")}, ValueError)):
            with self.subTest(parent=parent, event=event), self.assertRaises(exception):
                store.add(next_state, parent, event)
            self.assertEqual(store.count, 1)
        for operation in (store.get, store.trace, store.path):
            with self.assertRaises(KeyError):
                operation(999)
        with self.assertRaises(KeyError):
            store.commit_expansion(999, [(next_state, {})])
        self.assertEqual(store.expanded_count, 0)

    def test_context_manager_closes_on_exception_and_preserves_commits(self):
        with self.assertRaisesRegex(RuntimeError, "stop"):
            with TimedStore(self.database, self.model, self.identity) as store:
                store.seed([TimedState()])
                raise RuntimeError("stop")
        self.assertIsNone(store._connection)
        self.assertEqual(self.store(resume=True).count, 1)


if __name__ == "__main__":
    unittest.main()
