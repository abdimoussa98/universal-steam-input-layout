"""Small sampled between families remain hypotheses until induction."""
import contextlib
import io
import itertools
import json
from pathlib import Path
import tempfile
import unittest

from steam_layout.model import Layout
from steam_layout.timed_between import _first_cover, main, mine_between_families
from steam_layout.timed_discover import save_witnesses
from steam_layout.timed_facts import Fact, FactCatalogue, FactWitnesses
from steam_layout.timed_mine import _Budget
from steam_layout.timed_model import TimedModel
from steam_layout.timed_predicates import RequiresBetweenAny
from test_audit_inheritance import act, add, build


def fixture():
    data = build({
        "Base": {"switch": ("switches", {
            "left_bumper": act(add("A")), "right_bumper": act(add("B"))}),
            "button_diamond": ("four_buttons", {"button_a": act(add("X")),
                                                   "button_b": act("key_press Y, , ")})},
        "A": {"button_diamond": ("four_buttons", {"button_b": act("key_press A, , ")})},
        "B": {"button_diamond": ("four_buttons", {"button_b": act("key_press B, , ")})},
        "X": {}, "Never": {}})
    model = TimedModel(Layout(data))
    catalogue = FactCatalogue(model)
    witnesses = FactWitnesses(model, catalogue)
    for control in ("left_bumper", "right_bumper"):
        witnesses.add_trace([{"press": ["switch", control]},
                             {"press": ["button_diamond", "button_a"]}])
    j = catalogue.controls.index(("button_diamond", "button_b"))
    target = catalogue._lookup["inherit", 3, 0, j]
    return data, witnesses, target


class TimedBetweenTests(unittest.TestCase):
    def test_alternative_between_blockers_and_unwitnessed_pairs(self):
        _, witnesses, target = fixture()
        absent = witnesses.catalogue._lookup["inherit", 4, 0, target.j]
        result = mine_between_families(witnesses, (target, absent))
        self.assertEqual(result.candidates, (RequiresBetweenAny(3, 0, (1, 2)),))
        self.assertEqual([row["status"] for row in result.targets],
                         ["hypothesis_proposed", "ordered_pair_unwitnessed"])
        self.assertFalse(result.to_data()["complete_for_model"])
        self.assertEqual(result.to_data()["validation"], "unvalidated")
        for state in witnesses.node_states.values():
            ranks = tuple(state.stack.index(x) + 1 if x in state.stack else 0 for x in range(5))
            self.assertTrue(result.candidates[0].holds(ranks))

    def test_unseen_trace_can_disprove_suggestion(self):
        _, witnesses, target = fixture()
        self.assertTrue(mine_between_families(witnesses, (target,)).candidates)
        witnesses.add_trace([{"press": ["button_diamond", "button_a"]}])
        result = mine_between_families(witnesses, (target,))
        self.assertFalse(result.candidates)
        self.assertEqual(result.targets[0]["status"], "already_witnessed")

    def test_minimum_cover_matches_brute_force(self):
        for masks in itertools.combinations(range(1, 16), 3):
            for maximum in (1, 2, 3):
                valid = [cover for cover in range(1, 16) if bin(cover).count("1") <= maximum and
                         all(cover & mask for mask in masks)]
                cover = _first_cover(masks, maximum, _Budget(10000, None))
                if not valid:
                    self.assertIsNone(cover)
                else:
                    self.assertIn(cover, valid)
                    self.assertEqual(bin(cover).count("1"), min(bin(item).count("1") for item in valid))

    def test_budget_and_member_bound_never_create_exclusions(self):
        _, witnesses, target = fixture()
        result = mine_between_families(witnesses, (target,), max_members=1)
        self.assertEqual(result.targets[0]["status"], "no_cover_within_member_bound")
        result = mine_between_families(witnesses, (target,), max_search_nodes=1)
        self.assertEqual(result.targets[0]["status"], "budget_exhausted")
        self.assertFalse(result.candidates)
        self.assertFalse(result.to_data()["complete_for_model"])

    def test_canonical_targets_and_strict_types(self):
        _, witnesses, target = fixture()
        # Foreign context cannot smuggle a narrower set of raw-input definers.
        forged = Fact(target.kind, target.x, target.y, target.j, (0, 1))
        self.assertEqual(mine_between_families(witnesses, (forged, target)).candidates,
                         (RequiresBetweenAny(3, 0, (1, 2)),))
        for targets in (("bad",), (Fact("inherit", 100, 0, 0),)):
            with self.assertRaises(ValueError):
                mine_between_families(witnesses, targets)
        for kwargs in ({"max_members": True}, {"max_search_nodes": 0}, {"seconds": float("nan")}):
            with self.assertRaises(ValueError):
                mine_between_families(witnesses, (target,), **kwargs)
        with self.assertRaises(ValueError):
            mine_between_families([], ())

    def test_cli_replay_round_trip_and_output_alias_rejection(self):
        data, witnesses, target = fixture()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            layout, archive, targets, output = (root / name for name in
                                                ("layout.json", "archive.sqlite", "targets.json", "out.json"))
            layout.write_text(json.dumps(data))
            save_witnesses(witnesses, archive)
            targets.write_text(json.dumps([[target.kind, target.x, target.y, target.j]]))
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(main(list(map(str, (layout, archive, targets, output)))), 0)
            payload = json.loads(output.read_text())
            self.assertEqual([RequiresBetweenAny.from_data(row) for row in payload["candidates"]],
                             [RequiresBetweenAny(3, 0, (1, 2))])
            self.assertEqual(payload["validation"], "unvalidated")
            for forbidden in (layout, archive, targets):
                with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                    main(list(map(str, (layout, archive, targets, forbidden))))


if __name__ == "__main__":
    unittest.main()
